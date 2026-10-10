# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Subscriptions bought from the area and charged on the saved card, with a fake
Stripe (`stripe_finto`).

Anna buys a quarter of pilates paid at once: Stripe's page for the whole price,
then - paid - the subscription is hers from today and its invoice issued and
collected by card; told twice, sold once. She buys one paid by the month: the first
instalment, and the card kept for the next ones with the mandate's words on Stripe's
page. On the next instalment's day the card is charged first and the instalment
invoiced only then, once however often the round runs. A card declined: no invoice,
Anna told with the way to pay from her area, tried again 3 and 7 days later, then
the instalment is invoiced as any other. She stops the charges from her area; she
cannot buy for somebody who is not hers, nor the centre from its preview."""

from __future__ import annotations

import json
from unittest.mock import patch

import frappe
from frappe.utils import add_days, flt, getdate

from crm.area import anteprima
from crm.area import api as area_api
from crm.area.tests import test_area as area
from crm.invoicing.install import semina_qualifiche
from crm.pagamenti import addebiti
from crm.pagamenti.tests.stripe_finto import StripeFinto, firmato
from crm.pagamenti.tests.test_pagamenti import collega, manda
from crm.scheduling import abbonamenti as A
from crm.scheduling import abbonamenti_regole as AR

# modules, not classes: a TestCase imported here would run here too
from crm.tests import test_invoicing as fatturazione


class AddebitiCase(area.AreaCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		semina_qualifiche()
		fatturazione.InvoicingBase.crea_azienda()
		erogatore = fatturazione.InvoicingBase.crea_erogatore("Istruttrice Online", "psicologo")
		self.scheda = frappe.get_doc(
			{
				"doctype": "CRM Billable Service",
				"service_name": "Abbonamento online (fattura)",
				"fiscal_description": "Abbonamento ai corsi",
				"is_healthcare": 0,
				"vat_rate": 22,
				"default_rate": 40,
				"default_provider": erogatore.name,
				"enabled": 1,
			}
		).insert()
		pilates = self.make_service("Pilates online", [area.OPERATORE], default_price=20, currency="EUR")
		self.subito = self.tipo("Trimestre online", AR.SUBITO, 150, pilates.name)
		self.mensile = self.tipo("Mensile online", AR.MENSILE, 120, pilates.name)
		frappe.get_doc(
			{
				"doctype": "CRM Billing Profile",
				"party_type": "CRM Lead",
				"party": self.anna.name,
				"fiscal_code": fatturazione.CF_PAZIENTE,
				"address_line": "Via Verdi 3",
				"postal_code": "20100",
				"city": "Milano",
				"province": "MI",
				"country": "IT",
			}
		).insert(ignore_permissions=True)
		self.posta = patch("frappe.sendmail")
		self.mandate = self.posta.start()
		self.finto = StripeFinto().__enter__()
		collega(self.finto)
		frappe.db.set_single_value("CRM Stripe Settings", {"sell_in_area": 1, "card_charges": 1})
		self.invita()
		self.entra()

	def tearDown(self):
		self.finto.__exit__()
		self.posta.stop()
		frappe.cache.delete_value(anteprima._chiave())
		frappe.set_user("Administrator")
		super().tearDown()

	def tipo(self, nome, pagamento, prezzo, servizio):
		frappe.set_user("Administrator")
		return A.save_type(
			json.dumps(
				{
					"type_name": nome,
					"months": 3,
					"price": prezzo,
					"currency": "EUR",
					"payment": pagamento,
					"services": [servizio],
					"entries": AR.ILLIMITATI,
					"billable_service": self.scheda.name,
					"sold_online": 1,
				}
			)
		)["name"]

	def compra(self, tipo):
		link = area_api.buy_subscription(self.anna.name, tipo)
		return self.finto.sessioni[link["url"].rsplit("/", 1)[1]], link

	def paga(self, sessione):
		frappe.set_user("Administrator")
		corpo, firma = firmato(self.finto.paga(sessione["id"]))
		self.assertEqual(manda(corpo, firma)[0], 200)
		return corpo, firma

	def abbonamento(self, tipo):
		return frappe.get_doc("CRM Subscription", {"lead": self.anna.name, "subscription_type": tipo})

	def compra_al_mese(self):
		sessione, _link = self.compra(self.mensile)
		self.paga(sessione)
		return self.abbonamento(self.mensile)

	def dovuta(self, doc, indice, giorni=0, **altro):
		"""The instalment ``indice`` due ``giorni`` from today."""
		riga = doc.instalments[indice]
		frappe.db.set_value(
			"CRM Subscription Instalment",
			riga.name,
			{"due_on": add_days(getdate(), giorni), **altro},
			update_modified=False,
		)
		return riga.name

	def addebiti(self):
		return [c for c in self.finto.chiamate if c == ("POST", "payment_intents")]


class IlNegozio(AddebitiCase):
	def test_quello_che_si_vende_e_quanto_si_paga(self):
		voci = {v["name"]: v for v in area_api.get_shop(self.anna.name)["items"]}
		self.assertEqual(set(voci), {self.subito, self.mensile})
		# what the invoice adds up to: the fund (2%) and the VAT on top
		self.assertEqual(voci[self.subito]["first"], 186.66)
		self.assertFalse(voci[self.subito]["monthly"])
		self.assertEqual((voci[self.mensile]["first"], voci[self.mensile]["instalments"]), (49.78, 3))
		# without the monthly charge, only what is paid at once
		frappe.db.set_single_value("CRM Stripe Settings", "card_charges", 0)
		self.assertEqual([v["name"] for v in area_api.get_shop(self.anna.name)["items"]], [self.subito])
		frappe.db.set_single_value("CRM Stripe Settings", "sell_in_area", 0)
		self.assertEqual(area_api.get_shop(self.anna.name)["items"], [])

	def test_un_tipo_venduto_online_vuole_la_scheda_fiscale(self):
		frappe.set_user("Administrator")
		dati = A._tipo(frappe.get_doc(A.TIPO, self.subito))
		with self.assertRaises(frappe.ValidationError):
			A.save_type(json.dumps({**dati, "billable_service": None}), name=self.subito)


class IlCodiceFiscale(AddebitiCase):
	"""«Buy» asks the codice fiscale where the billing details lack it: the
	instalment's invoice is issued the day it is paid."""

	def voce(self):
		return {v["name"]: v for v in area_api.get_shop(self.anna.name)["items"]}[self.subito]

	def test_per_una_fattura_sanitaria_si_chiede_e_si_scrive(self):
		frappe.db.set_value("CRM Billable Service", self.scheda.name, "is_healthcare", 1)
		frappe.db.set_value("CRM Billing Profile", {"party": self.anna.name}, "fiscal_code", None)
		self.assertEqual(self.voce()["fiscal_code"], "required")
		with self.assertRaises(frappe.ValidationError):
			area_api.buy_subscription(self.anna.name, self.subito)
		with self.assertRaises(frappe.ValidationError):
			area_api.buy_subscription(self.anna.name, self.subito, fiscal_code="RSSMRA80A01H501X")
		link = area_api.buy_subscription(self.anna.name, self.subito, fiscal_code=fatturazione.CF_PAZIENTE)
		self.assertTrue(link["url"])
		self.assertEqual(
			frappe.db.get_value("CRM Billing Profile", {"party": self.anna.name}, "fiscal_code"),
			fatturazione.CF_PAZIENTE,
		)
		self.assertEqual(self.voce()["fiscal_code"], "")

	def test_altrimenti_facoltativo(self):
		frappe.db.set_value("CRM Billing Profile", {"party": self.anna.name}, "fiscal_code", None)
		self.assertEqual(self.voce()["fiscal_code"], "optional")
		self.assertTrue(area_api.buy_subscription(self.anna.name, self.subito)["url"])


class SubitoECarta(AddebitiCase):
	def test_pagato_subito_venduto_e_fatturato_una_volta(self):
		sessione, _link = self.compra(self.subito)
		self.assertEqual(sessione["amount_total"], 18666)
		self.assertFalse(sessione["setup_future_usage"])
		# nothing sold before the money
		self.assertFalse(frappe.db.exists("CRM Subscription", {"lead": self.anna.name}))
		corpo, firma = self.paga(sessione)
		doc = self.abbonamento(self.subito)
		self.assertEqual(getdate(doc.starts_on), getdate())
		fattura = frappe.get_doc("CRM Invoice", doc.instalments[0].invoice)
		self.assertEqual((fattura.docstatus, fattura.payment_method), (1, "MP08"))
		self.assertTrue(fattura.collected_on)
		self.assertEqual(flt(fattura.grand_total), 186.66)
		self.assertFalse(doc.card_charges)
		# Stripe tells again: sold once
		self.assertEqual(manda(corpo, firma)[0], 200)
		self.assertEqual(frappe.db.count("CRM Subscription", {"lead": self.anna.name}), 1)

	def test_mai_pagato_niente_venduto(self):
		sessione, _link = self.compra(self.subito)
		frappe.set_user("Administrator")
		manda(*firmato(self.finto.scade(sessione["id"])))
		self.assertFalse(frappe.db.exists("CRM Subscription", {"lead": self.anna.name}))

	def test_al_mese_la_carta_tenuta_e_il_mandato(self):
		sessione, _link = self.compra(self.mensile)
		self.assertEqual(sessione["amount_total"], 4978)
		self.assertEqual(sessione["setup_future_usage"], "off_session")
		self.assertTrue(sessione["customer"].startswith("cus_"))
		self.assertIn("every month", sessione["custom_text"])
		self.paga(sessione)
		doc = self.abbonamento(self.mensile)
		self.assertEqual(
			(doc.card_charges, doc.card_brand, doc.card_last4, doc.card_expiry),
			(1, "Visa", "4242", "12/2034"),
		)
		self.assertTrue(doc.stripe_payment_method.startswith("pm_"))
		self.assertTrue(frappe.db.get_value("CRM Invoice", doc.instalments[0].invoice, "collected_on"))
		self.assertFalse(doc.instalments[1].invoice)
		# the customer is kept, with the person
		self.assertEqual(
			frappe.db.get_value("CRM Stripe Customer", {"party": self.anna.name}, "customer_id"),
			doc.stripe_customer,
		)
		# the area says the next charge
		self.entra()
		[mio] = area_api.get_appointments(self.anna.name)["subscriptions"]
		self.assertEqual(mio["card"]["last4"], "4242")
		self.assertEqual(mio["card"]["next_on"], str(doc.instalments[1].due_on))
		self.assertTrue(mio["card"]["next_amount"])


class IlMese(AddebitiCase):
	def test_addebitata_poi_fatturata_una_volta(self):
		doc = self.compra_al_mese()
		riga = self.dovuta(doc, 1)
		frappe.set_user("Administrator")
		A.ogni_giorno()
		A.ogni_giorno()
		self.assertEqual(len(self.addebiti()), 1)
		fattura = frappe.db.get_value("CRM Subscription Instalment", riga, ["invoice"], as_dict=True).invoice
		self.assertTrue(fattura)
		self.assertEqual(frappe.db.get_value("CRM Invoice", fattura, "payment_method"), "MP08")
		self.assertTrue(frappe.db.get_value("CRM Invoice", fattura, "collected_on"))
		self.assertEqual(frappe.db.count("CRM Invoice", {"subscription": doc.name}), 2)
		# the webhook's own word, after: nothing more
		pagamento = frappe.get_doc("CRM Online Payment", {"instalment": riga, "status": "Paid"})
		manda(*firmato(self.finto.intento(pagamento.payment_intent)))
		self.assertEqual(frappe.db.count("CRM Invoice", {"subscription": doc.name}), 2)

	def test_rifiutata_niente_fattura_poi_tre_volte_poi_come_sempre(self):
		doc = self.compra_al_mese()
		self.finto.rifiuti = ["insufficient_funds", "insufficient_funds", "expired_card"]
		riga = self.dovuta(doc, 1)
		frappe.set_user("Administrator")
		self.mandate.reset_mock()
		A.ogni_giorno()
		stato = frappe.db.get_value(
			"CRM Subscription Instalment",
			riga,
			["invoice", "charge_attempts", "charge_problem"],
			as_dict=True,
		)
		self.assertFalse(stato.invoice)
		self.assertEqual(stato.charge_attempts, 1)
		self.assertEqual(stato.charge_problem, "There is not enough money on the card.")
		# Anna is told, with the day it is tried again
		self.assertEqual(self.mandate.call_count, 1)
		self.assertIn(str(getdate().year), self.mandate.call_args.kwargs["message"])
		# the same day again: no second try
		A.ogni_giorno()
		self.assertEqual(len(self.addebiti()), 1)
		# three days on, again; seven days on, the last
		self.dovuta(doc, 1, -3, last_charge_on=add_days(getdate(), -3))
		A.ogni_giorno()
		self.dovuta(doc, 1, -7, last_charge_on=add_days(getdate(), -4))
		A.ogni_giorno()
		self.assertEqual(len(self.addebiti()), 3)
		# then the instalment is invoiced as any other, and the card left alone
		A.ogni_giorno()
		self.assertEqual(len(self.addebiti()), 3)
		self.assertTrue(frappe.db.get_value("CRM Subscription Instalment", riga, "invoice"))

	def test_pagata_dall_area_dopo_il_rifiuto(self):
		doc = self.compra_al_mese()
		self.finto.rifiuti = ["card_declined"]
		riga = self.dovuta(doc, 1)
		frappe.set_user("Administrator")
		A.ogni_giorno()
		self.entra()
		[mio] = area_api.get_appointments(self.anna.name)["subscriptions"]
		self.assertEqual(mio["card"]["failed"]["instalment"], riga)
		link = area_api.pay_instalment(self.anna.name, doc.name, riga)
		sessione = self.finto.sessioni[link["url"].rsplit("/", 1)[1]]
		self.paga(sessione)
		fattura = frappe.db.get_value("CRM Subscription Instalment", riga, "invoice")
		self.assertTrue(frappe.db.get_value("CRM Invoice", fattura, "collected_on"))
		# paid: the card is not tried again
		self.dovuta(doc, 1, -3, last_charge_on=add_days(getdate(), -3))
		A.ogni_giorno()
		self.assertEqual(len(self.addebiti()), 1)

	def test_interrotti_dall_area(self):
		doc = self.compra_al_mese()
		self.entra()
		fatto = area_api.stop_card_charges(self.anna.name, doc.name)
		self.assertFalse(fatto["card"]["active"])
		self.assertEqual(self.finto.staccate, [doc.stripe_payment_method])
		riga = self.dovuta(doc, 1)
		frappe.set_user("Administrator")
		A.ogni_giorno()
		# no charge: the instalment follows the subscription's own rule
		self.assertEqual(self.addebiti(), [])
		self.assertTrue(frappe.db.get_value("CRM Subscription Instalment", riga, "invoice"))


class ChiCompra(AddebitiCase):
	def test_non_per_chi_non_e_suo(self):
		altra = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Altra", "last_name": "Persona"}).insert(
			ignore_permissions=True
		)
		self.entra()
		with self.assertRaises(frappe.PermissionError):
			area_api.buy_subscription(altra.name, self.subito)
		with self.assertRaises(frappe.PermissionError):
			area_api.get_shop(altra.name)

	def test_non_dall_anteprima(self):
		self.come(area.DESK)
		anteprima.start(self.anna.name)
		self.assertEqual(area_api.get_shop(self.anna.name)["items"], [])
		with self.assertRaises(frappe.PermissionError):
			area_api.buy_subscription(self.anna.name, self.subito)

	def test_il_desk_interrompe(self):
		doc = self.compra_al_mese()
		self.come(area.DESK)
		letto = addebiti.stop_card_charges(doc.name)
		self.assertFalse(letto["card"]["active"])
		self.assertTrue(letto["card"]["stopped_by"])
		frappe.set_user("Administrator")
		# whoever sells keeps the instalments: nothing else changed
		self.assertEqual(frappe.db.get_value("CRM Subscription", doc.name, "status"), AR.ATTIVO)
