# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The deposit's invoice, with a fake Stripe (`stripe_finto`): paid at /prenota, an
advance invoice issued and collected by itself, once however often Stripe tells;
the desk's invoice of the appointment is its balance, and nothing when the whole
price was paid; a deposit given back is a credit note on its advance."""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.utils import flt

from crm.api import service_booking as SB
from crm.invoicing import api as fatture_api
from crm.invoicing.install import semina_qualifiche
from crm.notifiche import regole as NR
from crm.pagamenti import pagamenti
from crm.pagamenti.tests.stripe_finto import StripeFinto, firmato
from crm.pagamenti.tests.test_pagamenti import collega, manda
from crm.scheduling.availability import forget_settings

# modules, not classes: a TestCase imported here would run here too
from crm.tests import test_invoicing as fatturazione
from crm.tests import test_service_booking as prenota
from crm.tests.test_scheduling import SchedulingCase

GESTORE = "gestione.fatture.acconto@example.com"


class AccontoCase(SchedulingCase):
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
		semina_qualifiche()
		fatturazione.InvoicingBase.crea_azienda()
		self.erogatore = fatturazione.InvoicingBase.crea_erogatore("Dott.ssa Bianchi", "psicologo")
		self.anna = self.bruno = self.make_user("anna.fattura.acconto@example.com")
		self.make_user(GESTORE)
		frappe.get_doc("User", GESTORE).add_roles("Invoicing Manager")
		self._posta = patch("frappe.sendmail")
		self._posta.start()
		self.finto = StripeFinto().__enter__()
		collega(self.finto)

	def tearDown(self):
		self.finto.__exit__()
		self._posta.stop()
		frappe.set_user("Administrator")
		super().tearDown()

	def prenota(self, modo="Deposit", acconto=30, prezzo=80, nome="Seduta con acconto"):
		servizio = self.online_service(
			nome, staff=[self.anna], default_price=prezzo, online_payment=modo, online_deposit=acconto
		)
		frappe.get_doc(
			{
				"doctype": "CRM Billable Service",
				"service_name": f"{nome} (scheda)",
				"fiscal_description": nome,
				"crm_service": servizio.name,
				"is_healthcare": 1,
				"vat_exempt": 1,
				"exemption_reference": "art. 10, n. 18, DPR 633/72",
				"ts_expense_type": "SP",
				"default_rate": prezzo,
				"default_provider": self.erogatore.name,
				"enabled": 1,
			}
		).insert()
		risultato = self.book(servizio, self.tomorrow(10), email="acconto.fattura@example.com")
		persona = frappe.db.get_value(
			"CRM Appointment Participant", {"access_token": risultato["token"]}, "party"
		)
		self.profilo(persona)
		return risultato

	def profilo(self, persona):
		if frappe.db.exists("CRM Billing Profile", {"party": persona}):
			return
		frappe.get_doc(
			{
				"doctype": "CRM Billing Profile",
				"party_type": "CRM Lead",
				"party": persona,
				"fiscal_code": fatturazione.CF_PAZIENTE,
				"address_line": "Via Verdi 3",
				"postal_code": "20100",
				"city": "Milano",
				"province": "MI",
				"country": "IT",
			}
		).insert(ignore_permissions=True)

	def paga(self, risultato):
		sessione = risultato["checkout_url"].rsplit("/", 1)[1]
		corpo, firma = firmato(self.finto.paga(sessione))
		self.assertEqual(manda(corpo, firma)[0], 200)
		return sessione, corpo, firma

	def pagamento(self, risultato):
		return frappe.get_doc(
			"CRM Online Payment", {"access_token": risultato["token"], "purpose": "Deposit"}
		)

	def appuntamento(self, risultato):
		return frappe.db.get_value(
			"CRM Appointment Participant", {"access_token": risultato["token"]}, "parent"
		)


class TestFatturaDAcconto(AccontoCase):
	def test_pagato_la_fattura_d_acconto_una_volta(self):
		risultato = self.prenota()
		_sessione, corpo, firma = self.paga(risultato)
		pagamento = self.pagamento(risultato)
		self.assertTrue(pagamento.invoice)
		fattura = frappe.get_doc("CRM Invoice", pagamento.invoice)
		# issued, by card, collected, adding up to the 30 paid; its appointment named
		# as an advance, never as the appointment it closes
		self.assertEqual(fattura.docstatus, 1, fattura.warnings)
		self.assertEqual(fattura.payment_method, "MP08")
		self.assertTrue(fattura.collected_on)
		self.assertEqual(round(flt(fattura.net_payable) or flt(fattura.grand_total), 2), 30)
		self.assertEqual(fattura.advance_for, self.appuntamento(risultato))
		self.assertFalse(fattura.appointment)
		# in the centre's language, whoever's request Stripe's is
		self.assertRegex(fattura.items[0].description, r"^(Advance for|Acconto per) Seduta con acconto")
		# Stripe tells again: one invoice
		self.assertEqual(manda(corpo, firma)[0], 200)
		self.assertEqual(frappe.db.count("CRM Invoice", {"advance_for": fattura.advance_for}), 1)
		# the appointment is not closed as attended by it
		stato = frappe.db.get_value(
			"CRM Appointment Participant", {"access_token": risultato["token"]}, "status"
		)
		self.assertNotEqual(stato, "Attended")

	def test_la_reception_fattura_il_saldo(self):
		risultato = self.prenota()
		self.paga(risultato)
		acconto = frappe.get_doc("CRM Invoice", self.pagamento(risultato).invoice)
		proposta = fatture_api.appointment_invoice_proposal(self.appuntamento(risultato))
		self.assertEqual(round(proposta["items"][0]["rate"], 2), round(80 - flt(acconto.net_total), 2))
		self.assertIn(acconto.document_number, proposta["causale"])
		# the dialog names the advance it settles
		bozza = frappe.new_doc("CRM Invoice")
		bozza.appointment = self.appuntamento(risultato)
		[riga] = pagamenti.per_la_fattura(bozza)["advances"]
		self.assertEqual(riga["number"], acconto.document_number)
		self.assertIsNone(pagamenti.per_la_fattura(bozza)["deposit"])

	def test_pagato_tutto_niente_da_fatturare(self):
		# the whole price is what the invoice adds up to: the fund and the stamp duty too
		risultato = self.prenota(modo="Full price", prezzo=80, nome="Seduta pagata tutta")
		self.paga(risultato)
		appuntamento = self.appuntamento(risultato)
		with self.assertRaises(frappe.ValidationError) as gia:
			fatture_api.appointment_invoice_proposal(appuntamento)
		self.assertIn("invoiced already", str(gia.exception))

	def test_senza_codice_fiscale_resta_bozza_e_si_dice(self):
		risultato = self.prenota()
		persona = frappe.db.get_value(
			"CRM Appointment Participant", {"access_token": risultato["token"]}, "party"
		)
		frappe.db.set_value("CRM Billing Profile", {"party": persona}, "fiscal_code", None)
		self.paga(risultato)
		pagamento = self.pagamento(risultato)
		self.assertEqual(frappe.db.get_value("CRM Invoice", pagamento.invoice, "docstatus"), 0)
		# the booking is confirmed whatever the invoice does
		self.assertEqual(
			frappe.db.get_value("CRM Appointment", self.appuntamento(risultato), "status"), "Confirmed"
		)
		self.assertTrue(
			frappe.db.exists(
				"CRM Notification",
				{
					"to_user": GESTORE,
					"sentence": NR.PAGATA_ONLINE_IN_BOZZA,
					"notification_type_doc": pagamento.invoice,
				},
			)
		)

	def test_rimborsato_alla_disdetta_la_nota_di_credito(self):
		frappe.db.set_single_value("CRM Stripe Settings", "refund_on_cancel", 1)
		frappe.db.set_single_value("CRM Stripe Settings", "refund_hours", 2)
		risultato = self.prenota()
		self.paga(risultato)
		acconto = self.pagamento(risultato).invoice
		frappe.set_user("Guest")
		SB.cancel(token=risultato["token"])
		frappe.set_user("Administrator")
		self.assertEqual(len(self.finto.rimborsi), 1)
		[nota] = frappe.get_all(
			"CRM Invoice",
			filters={"reference_invoice": acconto, "document_type": "TD04"},
			fields=["name", "docstatus", "net_total"],
		)
		self.assertEqual(nota.docstatus, 1)
		self.assertEqual(flt(nota.net_total), flt(frappe.db.get_value("CRM Invoice", acconto, "net_total")))
		self.assertEqual(self.pagamento(risultato).credit_note, nota.name)

	def test_un_rimborso_su_stripe_in_parte(self):
		risultato = self.prenota()
		sessione, _corpo, _firma = self.paga(risultato)
		acconto = self.pagamento(risultato).invoice
		manda(*firmato(self.finto.rimborsato(sessione, 1500)))
		[nota] = frappe.get_all(
			"CRM Invoice", filters={"reference_invoice": acconto}, fields=["net_total", "docstatus"]
		)
		imponibile = flt(frappe.db.get_value("CRM Invoice", acconto, "net_total"))
		self.assertAlmostEqual(flt(nota.net_total), round(imponibile / 2, 2), delta=0.01)
		# the same refund told again: no second note
		manda(*firmato(self.finto.rimborsato(sessione, 1500)))
		self.assertEqual(frappe.db.count("CRM Invoice", {"reference_invoice": acconto}), 1)

	def test_un_acconto_di_prima_senza_fattura_si_dice_ancora(self):
		risultato = self.prenota()
		self.paga(risultato)
		pagamento = self.pagamento(risultato)
		# a deposit paid before the advance invoice was: the old line
		frappe.db.set_value("CRM Online Payment", pagamento.name, "invoice", None)
		bozza = frappe.new_doc("CRM Invoice")
		bozza.appointment = self.appuntamento(risultato)
		self.assertEqual(pagamenti.per_la_fattura(bozza)["deposit"]["amount"], 30)
