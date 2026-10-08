# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Online payments on a site, with a fake Stripe (`stripe_finto`): connecting, an
invoice paid from its link, a deposit at online booking, Stripe's events applied
once, a refund recorded and said, never un-collected in silence."""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.utils import add_to_date, now_datetime
from werkzeug.test import EnvironBuilder

from crm.api import service_booking as SB
from crm.pagamenti import collegamento, pagamenti, webhook
from crm.pagamenti.tests.stripe_finto import SEGRETO, StripeFinto, firmato
from crm.scheduling.availability import forget_settings
from crm.tests import test_service_booking as prenota
from crm.tests.test_invoicing import InvoicingBase
from crm.tests.test_scheduling import SchedulingCase

CHIAVE = "sk_test_51FintoFintoFintoFinto1234"


def collega(finto: StripeFinto) -> dict:
	frappe.set_user("Administrator")
	return collegamento.connect_stripe(CHIAVE)


def manda(corpo: bytes, firma: str | None):
	"""A POST of Stripe's to the webhook, as the request Frappe would hand it."""
	intestazioni = {"Content-Type": "application/json"}
	if firma:
		intestazioni["Stripe-Signature"] = firma
	prima = getattr(frappe.local, "request", None)
	frappe.local.request = EnvironBuilder(method="POST", data=corpo, headers=intestazioni).get_request()
	frappe.local.response = frappe._dict()
	try:
		risposta = webhook.stripe()
		return frappe.local.response.get("http_status_code") or 200, risposta
	finally:
		frappe.set_user("Administrator")
		if prima is None:
			del frappe.local.request
		else:
			frappe.local.request = prima


class TestCollegamento(InvoicingBase):
	def test_collega_controlla_scollega(self):
		with StripeFinto() as finto:
			stato = collega(finto)
			self.assertTrue(stato["connected"])
			self.assertEqual(stato["mode"], "test")
			self.assertEqual(stato["account_name"], "Centro Prova")
			self.assertEqual(stato["currency"], "EUR")
			self.assertEqual(stato["key"], "sk_test_…1234")
			# the secrets never reach the page
			self.assertNotIn(CHIAVE, frappe.as_json(stato))
			self.assertNotIn(SEGRETO, frappe.as_json(stato))
			# its endpoint on the account, with the four events, and the secret kept
			(endpoint,) = finto.endpoint.values()
			self.assertTrue(endpoint["url"].endswith("/api/method/crm.pagamenti.webhook.stripe"))
			self.assertEqual(len(endpoint["events"]), 4)
			self.assertEqual(collegamento.segreto_del_webhook(), SEGRETO)
			self.assertEqual(collegamento.chiave(), CHIAVE)

			# deleted in the dashboard: «Check» makes it again
			finto.endpoint.clear()
			controllo = collegamento.check_stripe()
			self.assertTrue(controllo["ok"])
			self.assertTrue(controllo["repaired"])
			self.assertEqual(len(finto.endpoint), 1)

			collegamento.disconnect_stripe()
			self.assertFalse(collegamento.collegato())
			self.assertEqual(finto.endpoint, {})
			self.assertEqual(collegamento.chiave(), "")

	def test_una_chiave_pubblicabile_o_rifiutata(self):
		with StripeFinto() as finto:
			with self.assertRaises(frappe.ValidationError):
				collegamento.connect_stripe("pk_test_51FintoFintoFintoFinto")
			finto.rifiuta = (401, {"error": {"type": "invalid_request_error"}})
			with self.assertRaises(frappe.ValidationError) as rifiuto:
				collegamento.connect_stripe(CHIAVE)
			self.assertIn("API keys", str(rifiuto.exception))
			self.assertFalse(collegamento.collegato())

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()


class TestFatturaPagataOnline(InvoicingBase):
	def setUp(self):
		super().setUp()
		self.persona = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Paola",
				"last_name": "Online",
				"email": "paola.online@example.com",
			}
		).insert(ignore_permissions=True)
		self.finto = StripeFinto().__enter__()
		collega(self.finto)

	def tearDown(self):
		self.finto.__exit__()
		frappe.set_user("Administrator")
		super().tearDown()

	def emessa(self, **kwargs) -> str:
		documento = self.fattura(
			self.consulenza.name,
			self.consulente.name,
			party_type="CRM Lead",
			party=self.persona.name,
			**kwargs,
		)
		documento.submit()
		frappe.db.set_value("CRM Invoice", documento.name, {"collected_on": None, "test_document": 0})
		return documento.name

	def test_il_link_poi_pagata_una_volta_sola(self):
		nome = self.emessa()
		link = pagamenti.payment_link(nome)
		self.assertTrue(link["url"].startswith("https://checkout.stripe.com/"))
		sessione = self.finto.sessioni[link["url"].rsplit("/", 1)[1]]
		da_pagare = frappe.db.get_value("CRM Invoice", nome, "net_payable") or frappe.db.get_value(
			"CRM Invoice", nome, "grand_total"
		)
		self.assertEqual(sessione["amount_total"], round(da_pagare * 100))
		self.assertEqual(sessione["metadata"]["invoice"], nome)
		self.assertEqual(sessione["metadata"]["site"], frappe.local.site)
		# asked again: the same link, no second session
		self.assertEqual(pagamenti.payment_link(nome)["url"], link["url"])
		self.assertEqual(len(self.finto.sessioni), 1)

		evento = self.finto.paga(sessione["id"])
		corpo, firma = firmato(evento)
		self.assertEqual(manda(corpo, firma)[0], 200)
		self.assertEqual(
			str(frappe.db.get_value("CRM Invoice", nome, "collected_on")), str(now_datetime().date())
		)
		pagamento = frappe.get_doc("CRM Online Payment", link["payment"])
		self.assertEqual(pagamento.status, "Paid")
		self.assertEqual(pagamento.payment_intent, f"pi_{sessione['id']}")
		log = frappe.get_all(
			"CRM Invoice Log", filters={"invoice": nome, "event": "collected"}, fields=["message", "payload"]
		)
		self.assertEqual(len(log), 1)
		self.assertIn("Stripe", log[0].message)
		self.assertIn("MP08", log[0].payload)

		# Stripe sends it again: applied once
		self.assertEqual(manda(corpo, firma)[0], 200)
		self.assertEqual(frappe.db.count("CRM Invoice Log", {"invoice": nome, "event": "collected"}), 1)
		self.assertEqual(frappe.db.count("CRM Stripe Event", {"event_id": evento["id"], "done": 1}), 1)
		# the area says when
		self.assertEqual(pagamenti.pagate_online([nome]), {nome: str(now_datetime().date())})
		# and a collected invoice has no link any more
		with self.assertRaises(frappe.ValidationError):
			pagamenti.payment_link(nome)

	def test_una_firma_sbagliata_o_vecchia_e_400(self):
		nome = self.emessa()
		link = pagamenti.payment_link(nome)
		evento = self.finto.paga(link["url"].rsplit("/", 1)[1])
		corpo, _firma = firmato(evento, segreto="whsec_altro")
		self.assertEqual(manda(corpo, _firma)[0], 400)
		self.assertEqual(manda(corpo, None)[0], 400)
		corpo, vecchia = firmato(evento, momento=1_000_000_000)
		self.assertEqual(manda(corpo, vecchia)[0], 400)
		self.assertFalse(frappe.db.get_value("CRM Invoice", nome, "collected_on"))
		self.assertFalse(frappe.db.exists("CRM Stripe Event", evento["id"]))

	def test_un_rimborso_si_scrive_e_si_dice_non_si_toglie_l_incasso(self):
		nome = self.emessa()
		link = pagamenti.payment_link(nome)
		sessione = link["url"].rsplit("/", 1)[1]
		manda(*firmato(self.finto.paga(sessione)))
		manda(*firmato(self.finto.rimborsato(sessione, 1500)))
		pagamento = frappe.get_doc("CRM Online Payment", link["payment"])
		self.assertEqual(pagamento.status, "Partly refunded")
		self.assertEqual(pagamento.refunded_amount, 15)
		self.assertTrue(frappe.db.get_value("CRM Invoice", nome, "collected_on"))
		self.assertTrue(frappe.db.exists("CRM Invoice Log", {"invoice": nome, "event": "refunded"}))

	def test_mai_una_fattura_di_prova_o_una_nota_di_credito(self):
		nome = self.emessa()
		frappe.db.set_value("CRM Invoice", nome, "test_document", 1)
		with self.assertRaises(frappe.ValidationError):
			pagamenti.payment_link(nome)
		frappe.db.set_value("CRM Invoice", nome, {"test_document": 0, "document_type": "TD04"})
		with self.assertRaises(frappe.ValidationError):
			pagamenti.payment_link(nome)
		self.assertEqual(self.finto.sessioni, {})

	def test_scollegato_niente_link(self):
		nome = self.emessa()
		collegamento.disconnect_stripe()
		with self.assertRaises(frappe.ValidationError):
			pagamenti.payment_link(nome)


class TestAcconto(SchedulingCase):
	# the booking page's own helpers (`crm/tests/test_service_booking.py`)
	online_service = prenota.TestServiceBooking.online_service
	book = prenota.TestServiceBooking.book

	def setUp(self):
		super().setUp()
		impostazioni = frappe.get_doc("CRM Scheduling Settings")
		impostazioni.update(
			{
				"online_booking_enabled": 1,
				"require_privacy_consent": 0,
				"max_active_per_customer": 0,
				"no_show_limit": 0,
				"default_min_notice_hours": 0,
				"default_max_horizon_days": 30,
				"default_require_phone": 0,
				"default_cancel_notice_hours": 0,
				"default_reschedule_notice_hours": 0,
				"default_max_reschedules": 0,
				"default_online_confirmation": "Automatic",
			}
		)
		impostazioni.save()
		forget_settings()
		self.anna = self.make_user("anna.acconto@example.com")
		self.bruno = self.make_user("bruno.acconto@example.com")
		self._posta = patch("frappe.sendmail")
		self._posta.start()
		self.finto = StripeFinto().__enter__()
		collega(self.finto)

	def tearDown(self):
		self.finto.__exit__()
		self._posta.stop()
		frappe.set_user("Administrator")
		super().tearDown()

	def prenota(self, ora=10):
		servizio = self.online_service(
			"Deposit Physio", staff=[self.anna], default_price=80, online_payment="Deposit", online_deposit=30
		)
		return servizio, self.book(servizio, self.tomorrow(ora))

	def appuntamento(self, token):
		return frappe.get_doc(
			"CRM Appointment",
			frappe.db.get_value("CRM Appointment Participant", {"access_token": token}, "parent"),
		)

	def test_il_catalogo_dice_l_acconto(self):
		servizio, _risultato = self.prenota()
		scheda = next(s for s in SB.get_catalog()["services"] if s["name"] == "Deposit Physio")
		self.assertEqual(scheda["deposit"]["amount"], 30)

	def test_tenuto_poi_confermato_quando_pagato(self):
		_servizio, risultato = self.prenota()
		self.assertTrue(risultato["checkout_url"])
		self.assertEqual(risultato["payment"]["state"], "waiting")
		self.assertFalse(risultato["pending_approval"])
		appuntamento = self.appuntamento(risultato["token"])
		self.assertEqual(appuntamento.status, "Scheduled")
		sessione = risultato["checkout_url"].rsplit("/", 1)[1]
		self.assertEqual(self.finto.sessioni[sessione]["amount_total"], 3000)
		self.assertIn(f"token={risultato['token']}", self.finto.sessioni[sessione]["success_url"])

		manda(*firmato(self.finto.paga(sessione)))
		appuntamento.reload()
		self.assertEqual(appuntamento.status, "Confirmed")
		vista = SB.get_booking(risultato["token"])
		self.assertEqual(vista["payment"]["state"], "paid")
		# the desk's invoice says it
		bozza = frappe.new_doc("CRM Invoice")
		bozza.appointment = appuntamento.name
		self.assertEqual(pagamenti.per_la_fattura(bozza)["deposit"]["amount"], 30)

	def test_scaduto_libera_il_posto(self):
		servizio, risultato = self.prenota()
		sessione = risultato["checkout_url"].rsplit("/", 1)[1]
		manda(*firmato(self.finto.scade(sessione)))
		self.assertEqual(self.appuntamento(risultato["token"]).status, "Cancelled")
		self.assertEqual(SB.get_booking(risultato["token"])["payment"]["state"], "expired")
		# the same time can be booked again
		altro = self.book(servizio, self.tomorrow(10), email="altro@example.com")
		self.assertTrue(altro["checkout_url"])

	def test_il_giro_dei_dieci_minuti_libera_chi_non_ha_pagato(self):
		_servizio, risultato = self.prenota()
		nome = frappe.db.get_value("CRM Online Payment", {"access_token": risultato["token"]}, "name")
		frappe.db.set_value(
			"CRM Online Payment", nome, "expires_at", add_to_date(now_datetime(), minutes=-10)
		)
		pagamenti.ogni_dieci_minuti()
		self.assertEqual(frappe.db.get_value("CRM Online Payment", nome, "status"), "Expired")
		self.assertEqual(self.appuntamento(risultato["token"]).status, "Cancelled")
		self.assertEqual(
			self.finto.sessioni[risultato["checkout_url"].rsplit("/", 1)[1]]["status"], "expired"
		)

	def test_pagato_mentre_scadeva_resta_prenotato(self):
		_servizio, risultato = self.prenota()
		sessione = risultato["checkout_url"].rsplit("/", 1)[1]
		self.finto.paga(sessione)  # paid on Stripe, its event lost
		nome = frappe.db.get_value("CRM Online Payment", {"access_token": risultato["token"]}, "name")
		frappe.db.set_value(
			"CRM Online Payment", nome, "expires_at", add_to_date(now_datetime(), minutes=-10)
		)
		pagamenti.ogni_dieci_minuti()
		self.assertEqual(frappe.db.get_value("CRM Online Payment", nome, "status"), "Paid")
		self.assertEqual(self.appuntamento(risultato["token"]).status, "Confirmed")

	def test_disdetto_in_tempo_l_acconto_torna(self):
		# tomorrow's appointment: two hours before is in time
		frappe.db.set_single_value("CRM Stripe Settings", "refund_hours", 2)
		_servizio, risultato = self.prenota()
		manda(*firmato(self.finto.paga(risultato["checkout_url"].rsplit("/", 1)[1])))
		frappe.set_user("Guest")
		SB.cancel(token=risultato["token"])
		frappe.set_user("Administrator")
		self.assertEqual(len(self.finto.rimborsi), 1)
		self.assertEqual(self.finto.rimborsi[0]["amount"], "3000")
		nome = frappe.db.get_value("CRM Online Payment", {"access_token": risultato["token"]}, "name")
		self.assertEqual(frappe.db.get_value("CRM Online Payment", nome, "status"), "Refunded")

	def test_disdetto_tardi_o_regola_spenta_l_acconto_resta(self):
		frappe.db.set_single_value("CRM Stripe Settings", "refund_hours", 72)
		_servizio, risultato = self.prenota()
		manda(*firmato(self.finto.paga(risultato["checkout_url"].rsplit("/", 1)[1])))
		frappe.set_user("Guest")
		SB.cancel(token=risultato["token"])
		frappe.set_user("Administrator")
		self.assertEqual(self.finto.rimborsi, [])

	def test_disdetto_mentre_aspetta_il_link_si_chiude(self):
		_servizio, risultato = self.prenota()
		sessione = risultato["checkout_url"].rsplit("/", 1)[1]
		frappe.set_user("Guest")
		SB.cancel(token=risultato["token"])
		frappe.set_user("Administrator")
		nome = frappe.db.get_value("CRM Online Payment", {"access_token": risultato["token"]}, "name")
		self.assertEqual(frappe.db.get_value("CRM Online Payment", nome, "status"), "Cancelled")
		self.assertEqual(self.finto.sessioni[sessione]["status"], "expired")
		# paid all the same, a moment before Stripe closed it: given back at once
		manda(*firmato(self.finto.paga(sessione)))
		self.assertEqual(len(self.finto.rimborsi), 1)
		self.assertEqual(frappe.db.get_value("CRM Online Payment", nome, "status"), "Refunded")

	def test_senza_stripe_si_prenota_come_sempre(self):
		collegamento.disconnect_stripe()
		_servizio, risultato = self.prenota()
		self.assertNotIn("checkout_url", risultato)
		self.assertEqual(risultato["status"], "Confirmed")
		self.assertIsNone(risultato["payment"])

	def test_stripe_che_rifiuta_non_prenota(self):
		self.finto.rifiuta = None
		servizio = self.online_service(
			"Deposit Physio", staff=[self.anna], default_price=80, online_payment="Deposit", online_deposit=30
		)
		with patch.object(self.finto, "rifiuta", (500, {"error": {"type": "api_error"}})):
			with self.assertRaises(frappe.ValidationError):
				self.book(servizio, self.tomorrow(10))
