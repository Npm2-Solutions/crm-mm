# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A quote paid in instalments, on a site (`crm.preventivi.rate`).

Anna's treatments, 240 € in all, are paid with a deposit of a tenth and seven
monthly instalments: the schedule is written with the draft, to the cent, and
frozen when it is proposed. Accepted, the deposit falls due that day: the daily
round invoices it, once; collected, it is paid. The laser's appointment is paid by
the instalments and is never invoiced again. Paid off early, one invoice takes the
rest. Declined or closed, what was not invoiced is cancelled; a new version
accepted closes the old one. Where the centre invoices by itself, the desk marks
them. The demo's quotes never reach the daily round. A reminder names the
instalment.
"""

from unittest import mock

import frappe
from frappe.utils import add_days, add_months, getdate

from crm.area.tests.test_area import DESK, MANAGER, OPERATORE
from crm.invoicing import api as fatture
from crm.invoicing import incassi, solleciti
from crm.invoicing.install import semina_qualifiche
from crm.persone import riepilogo
from crm.preventivi import api as preventivi
from crm.preventivi import area, documento, rate
from crm.preventivi import rate_regole as RR
from crm.preventivi import regole as R

# modules, not classes: a TestCase imported here would run here too
from crm.preventivi.tests import test_preventivi as quote_base
from crm.tests import test_invoicing as fatturazione

IMPOSTAZIONI = "CRM Quote Settings"


class RateCase(quote_base.PreventiviCase):
	def setUp(self):
		super().setUp()
		semina_qualifiche()
		fatturazione.InvoicingBase.crea_azienda()
		erogatore = fatturazione.InvoicingBase.crea_erogatore("Estetista Rate", "psicologo")
		for servizio in (self.viso, self.laser):
			frappe.get_doc(
				{
					"doctype": "CRM Billable Service",
					"service_name": f"{servizio.service_name} (fattura)",
					"fiscal_description": servizio.service_name,
					"crm_service": servizio.name,
					"is_healthcare": 0,
					"vat_rate": 22,
					"default_rate": 100,
					"default_provider": erogatore.name,
					"enabled": 1,
				}
			).insert()
		frappe.db.set_single_value(
			IMPOSTAZIONI, {"instalment_invoicing": RR.OGNI_RATA, "issue_instalment_invoices": 0}
		)

	def a_rate(self, **altro):
		termini = {
			"payment": RR.A_RATE,
			"deposit_type": RR.PERCENTUALE,
			"deposit_value": 10,
			"instalments_count": 7,
			"every_months": 1,
			"first_due_on": str(add_days(getdate(), 20)),
		}
		return self.scrive(**{**termini, **altro})

	def accettato(self, **altro):
		fatto = self.a_rate(**altro)
		self.proponi(fatto["name"])
		self.come(DESK)
		return preventivi.accept_quote(fatto["name"])

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()


class IlPiano(RateCase):
	def test_scritto_con_la_bozza_al_centesimo(self):
		fatto = self.a_rate()
		righe = fatto["instalments"]
		self.assertEqual(len(righe), 8)
		self.assertEqual((righe[0]["kind"], righe[0]["amount"], righe[0]["due_on"]), (RR.ACCONTO, 24, None))
		# 216 € in seven: 30,85 each, the cents left on the last
		self.assertEqual([r["amount"] for r in righe[1:]], [30.85] * 6 + [30.9])
		primo = add_days(getdate(), 20)
		self.assertEqual(righe[1]["due_on"], str(primo))
		self.assertEqual(righe[3]["due_on"], str(add_months(primo, 2)))
		self.assertEqual(round(sum(r["amount"] for r in righe), 2), 240)
		# a draft follows its terms; at once, it has no plan
		di_nuovo = self.scrive(payment=RR.UNICA)
		self.assertEqual(di_nuovo["instalments"], [])

	def test_cosa_non_va(self):
		with self.assertRaises(frappe.ValidationError):
			self.a_rate(instalments_count=40)
		# a draft may wait for the first day; proposed, it needs it, not in the past
		fatto = self.a_rate(first_due_on=None)
		self.assertEqual(fatto["instalments"], [])
		with self.assertRaises(frappe.ValidationError):
			self.proponi(fatto["name"])
		passato = self.a_rate(first_due_on=str(add_days(getdate(), -1)))
		with self.assertRaises(frappe.ValidationError):
			self.proponi(passato["name"])

	def test_nel_pdf_e_nell_area_prima_di_firmare(self):
		fatto = self.a_rate()
		self.proponi(fatto["name"])
		html = documento.html(frappe.get_doc(preventivi.DOCTYPE, fatto["name"]))
		self.assertIn("30,90", html.replace("30.90", "30,90"))
		self.assertIn("Deposit", frappe.get_doc(preventivi.DOCTYPE, fatto["name"]).instalments[0].kind)
		self.invita()
		self.entra()
		[nell_area] = area.area_quotes(self.anna.name)["quotes"]
		self.assertEqual(len(nell_area["payment"]["rows"]), 8)
		self.assertEqual(nell_area["payment"]["count"], 7)


class LaFattura(RateCase):
	def test_l_acconto_si_fattura_una_volta_e_incassato_e_pagato(self):
		fatto = self.accettato()
		self.assertEqual(fatto["instalments_invoiced"], 1)
		self.assertEqual(fatto["instalments"][0]["due_on"], str(getdate()))
		frappe.set_user("Administrator")
		rate.ogni_giorno()
		rate.ogni_giorno()
		fatture_fatte = frappe.get_all("CRM Invoice", filters={"quote": fatto["name"]}, pluck="name")
		self.assertEqual(len(fatture_fatte), 1)
		fattura = frappe.get_doc("CRM Invoice", fatture_fatte[0])
		self.assertEqual((fattura.party, fattura.docstatus, fattura.items[0].rate), (self.anna.name, 0, 24))
		self.assertIn("Trattamenti di ottobre", fattura.items[0].description)
		# issued and collected: paid
		fattura.update(
			{
				"fiscal_code": "RSSMRA80A01H501U",
				"address_line": "Via Verdi 3",
				"postal_code": "00100",
				"city": "Roma",
				"province": "RM",
				"payment_method": "MP08",
			}
		)
		fattura.save()
		fattura.submit()
		self.assertEqual(frappe.db.get_value(rate.RIGA, {"invoice": fattura.name}, "status"), RR.FATTURATA)
		incassi.segna(fattura, getdate())
		self.come(OPERATORE)
		letto = preventivi.get_quote(fatto["name"])
		self.assertEqual(letto["instalments"][0]["status"], RR.PAGATA)
		self.assertEqual(letto["instalments_summary"]["paid"], 0)
		self.assertEqual(letto["instalments_summary"]["next"]["due_on"], str(add_days(getdate(), 20)))
		# deleted, a row is to pay again
		frappe.set_user("Administrator")
		fattura.cancel()
		self.assertEqual(
			frappe.db.get_value(rate.RIGA, letto["instalments"][0]["name"], "status"), RR.DA_PAGARE
		)

	def test_gli_appuntamenti_li_pagano_le_rate(self):
		fatto = self.accettato()
		laser = quote_base.LeSedute.appuntamento(self, self.laser, self.tomorrow(11))
		self.assertIn(laser.name, rate.pagati_a_rate([laser.name]))
		with self.assertRaises(frappe.ValidationError):
			fatture.issue_from_appointment(laser.name)
		self.assertTrue(fatto["name"])

	def test_salda_il_resto(self):
		fatto = self.accettato()
		self.come(DESK)
		saldo = rate.settle_quote(fatto["name"])
		self.assertTrue(saldo["invoice"])
		self.assertEqual(frappe.db.get_value("CRM Invoice", saldo["invoice"], "grand_total") > 0, True)
		self.assertEqual({r["invoice"] for r in saldo["instalments"]}, {saldo["invoice"]})
		self.assertEqual(
			frappe.get_doc("CRM Invoice", saldo["invoice"]).items[0].rate,
			240,
		)
		self.assertFalse(saldo["can_settle"])
		with self.assertRaises(frappe.ValidationError):
			rate.settle_quote(fatto["name"])

	def test_il_sollecito_dice_quale_rata(self):
		fatto = self.accettato()
		self.come(DESK)
		riga = fatto["instalments"][3]
		fatta = rate.invoice_instalment(fatto["name"], riga["name"])
		self.assertEqual(
			solleciti._la_rata(frappe._dict(name=fatta["invoice"], quote=fatto["name"])), ("Instalment", 3, 7)
		)
		testo = solleciti._testo(
			frappe.get_doc("CRM Invoice", fatta["invoice"]),
			frappe._dict(nome="Anna"),
			solleciti.impostazioni(),
		)
		self.assertIn("3", testo["frase"])

	def test_mai_quelli_della_demo(self):
		fatto = self.accettato()
		frappe.set_user("Administrator")
		with mock.patch("crm.demo.registro.nomi_di_prova", return_value={fatto["name"]}):
			rate.ogni_giorno()
		self.assertFalse(frappe.db.exists("CRM Invoice", {"quote": fatto["name"]}))


class LaFine(RateCase):
	def test_rifiutato_si_annulla_tutto(self):
		fatto = self.a_rate()
		self.proponi(fatto["name"])
		self.come(DESK)
		letto = preventivi.decline_quote(fatto["name"])
		self.assertEqual({r["status"] for r in letto["instalments"]}, {RR.ANNULLATA})

	def test_chiuso_restano_le_fatturate(self):
		fatto = self.accettato()
		frappe.set_user("Administrator")
		rate.ogni_giorno()
		self.come(DESK)
		chiuso = preventivi.close_quote(fatto["name"])
		self.assertEqual(chiuso["cancelled_instalments"], 7)
		self.assertEqual([r["status"] for r in chiuso["instalments"]], [RR.FATTURATA] + [RR.ANNULLATA] * 7)

	def test_una_nuova_versione_accettata_chiude_la_vecchia(self):
		fatto = self.accettato()
		self.come(OPERATORE)
		nuova = preventivi.copy_quote(fatto["name"])
		self.assertEqual(nuova["payment"], RR.A_RATE)
		self.proponi(nuova["name"])
		self.come(DESK)
		preventivi.accept_quote(nuova["name"])
		vecchio = preventivi.get_quote(fatto["name"])
		self.assertEqual(vecchio["status"], R.CHIUSO)
		self.assertEqual({r["status"] for r in vecchio["instalments"]}, {RR.ANNULLATA})


class SoloSeguite(RateCase):
	def test_il_centro_fattura_da_se_e_le_segna(self):
		frappe.db.set_single_value(IMPOSTAZIONI, "instalment_invoicing", RR.SOLO_SEGUITE)
		fatto = self.accettato()
		self.assertEqual(fatto["instalments_invoiced"], 0)
		frappe.set_user("Administrator")
		rate.ogni_giorno()
		self.assertFalse(frappe.db.exists("CRM Invoice", {"quote": fatto["name"]}))
		laser = quote_base.LeSedute.appuntamento(self, self.laser, self.tomorrow(11))
		self.assertFalse(rate.pagati_a_rate([laser.name]))
		self.come(MANAGER)
		segnato = rate.mark_instalment(fatto["name"], fatto["instalments"][0]["name"])
		self.assertEqual(segnato["instalments"][0]["status"], RR.PAGATA)
		# the person's summary says how it goes
		[riga] = riepilogo.get_summary(self.anna.name)["quotes"]["quotes"]
		self.assertEqual(riga["instalments"]["count"], 7)
		saldato = rate.settle_quote(fatto["name"])
		self.assertEqual({r["status"] for r in saldato["instalments"]}, {RR.PAGATA})

	def test_le_impostazioni(self):
		from crm.preventivi import pipeline

		self.come(MANAGER)
		fatto = pipeline.save_settings(
			pipeline.quale(), 30, instalment_invoicing=RR.SOLO_SEGUITE, issue_instalment_invoices=1
		)
		self.assertEqual(
			(fatto["instalment_invoicing"], fatto["issue_instalment_invoices"]), (RR.SOLO_SEGUITE, 1)
		)
		with self.assertRaises(frappe.PermissionError):
			self.come(OPERATORE)
			pipeline.save_settings(pipeline.quale(), 30)
