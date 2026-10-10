# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The reminders of what a person still owes, on a real site (`crm.invoicing.solleciti`).

An invoice issued to a person and still to collect, past the days the centre chose,
gets its reminder once per turn: written on its log before it leaves, by email with
a button to the area where the person has one. Never with the switch off, never a
collected, test or credit note invoice, never an amount under the threshold.
"""

from __future__ import annotations

import frappe
from frappe.utils import add_days, getdate, nowdate

from crm.invoicing import solleciti
from crm.invoicing import solleciti_regole as R
from crm.tests.test_invoicing import InvoicingBase

IMPOSTAZIONI = "CRM Payment Reminder Settings"


class SollecitiTest(InvoicingBase):
	def setUp(self):
		super().setUp()
		frappe.db.set_single_value(
			IMPOSTAZIONI,
			{
				"enabled": 1,
				"first_after_days": 7,
				"every_days": 14,
				"max_reminders": 2,
				"minimum_amount": 10,
				"use_email": 1,
				"use_sms": 0,
				"how_to_pay": "IBAN IT60X0542811101000000123456",
			},
		)
		self.persona = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Mario",
				"last_name": "Solleciti",
				"email": "mario.solleciti@example.com",
			}
		).insert(ignore_permissions=True)

	def emessa(self, giorni_fa: int = 10, **kwargs):
		"""An invoice to the person, issued ``giorni_fa`` days ago, still to collect."""
		documento = self.fattura(
			self.consulenza.name,
			self.consulente.name,
			party_type="CRM Lead",
			party=self.persona.name,
			**kwargs,
		)
		documento.submit()
		frappe.db.set_value(
			"CRM Invoice",
			documento.name,
			{"posting_date": add_days(nowdate(), -giorni_fa), "collected_on": None, "test_document": 0},
		)
		return documento.name

	def dovute(self, oggi=None) -> list[str]:
		return [riga.name for riga in solleciti.dovute(oggi=oggi)]

	def test_dopo_i_giorni_scelti_un_sollecito_poi_l_intervallo(self):
		nome = self.emessa(giorni_fa=10)
		recente = self.emessa(giorni_fa=3)
		dovute = self.dovute()
		self.assertIn(nome, dovute)
		self.assertNotIn(recente, dovute)

		fattura = next(riga for riga in solleciti.dovute() if riga.name == nome)
		self.assertEqual(solleciti.manda(fattura), R.INVIATO)
		self.assertTrue(
			frappe.db.exists("Email Queue", {"reference_doctype": "CRM Invoice", "reference_name": nome})
		)
		self.assertEqual(solleciti.di_fatture([nome])[nome], {"count": 1, "last": str(getdate())})
		# the next one waits for the interval
		self.assertNotIn(nome, self.dovute())
		self.assertIn(nome, self.dovute(oggi=add_days(nowdate(), 14)))

	def test_l_email_ha_il_bottone_dell_area_solo_per_chi_ce_l_ha(self):
		from crm.area import accesso

		nome = self.emessa()
		fattura = next(riga for riga in solleciti.dovute() if riga.name == nome)
		solleciti.manda(fattura)
		messaggio = frappe.get_last_doc(
			"Email Queue", filters={"reference_doctype": "CRM Invoice", "reference_name": nome}
		).message
		self.assertNotIn("/area/login?link=", messaggio)
		self.assertIn("IT60X0542811101000000123456", messaggio)

		accesso.apri(self.persona.name, accesso.SE_STESSO, self.persona.email, invito=False)
		altra = self.emessa()
		fattura = next(riga for riga in solleciti.dovute() if riga.name == altra)
		solleciti.manda(fattura)
		messaggio = frappe.get_last_doc(
			"Email Queue", filters={"reference_doctype": "CRM Invoice", "reference_name": altra}
		).message
		self.assertIn("/area/login?link=", messaggio)

	def test_mai_incassata_di_prova_nota_di_credito_o_sotto_la_soglia(self):
		nome = self.emessa()
		frappe.db.set_value("CRM Invoice", nome, "collected_on", nowdate())
		self.assertNotIn(nome, self.dovute())
		frappe.db.set_value("CRM Invoice", nome, {"collected_on": None, "test_document": 1})
		self.assertNotIn(nome, self.dovute())
		frappe.db.set_value("CRM Invoice", nome, {"test_document": 0, "document_type": "TD04"})
		self.assertNotIn(nome, self.dovute())
		frappe.db.set_value("CRM Invoice", nome, "document_type", "TD01")
		self.assertIn(nome, self.dovute())
		frappe.db.set_single_value(IMPOSTAZIONI, "minimum_amount", 100000)
		self.assertNotIn(nome, self.dovute())

	def test_la_fattura_all_azienda_non_si_sollecita_alla_persona(self):
		# Federica's visit, made out to the company that pays for it: the company's
		# to pay, never reminded to her
		nome = self.emessa(
			recipient_type="soggetto_iva",
			billing_name="Tecnoservizi S.r.l.",
			tax_id="IT12345678903",
			recipient_code="0000000",
		)
		self.assertNotIn(nome, self.dovute())

	def test_spento_non_parte_nulla(self):
		nome = self.emessa()
		frappe.db.set_single_value(IMPOSTAZIONI, "enabled", 0)
		solleciti.ogni_giorno()
		self.assertEqual(solleciti.di_fatture([nome])[nome]["count"], 0)
		frappe.db.set_single_value(IMPOSTAZIONI, "enabled", 1)
		solleciti.ogni_giorno()
		self.assertEqual(solleciti.di_fatture([nome])[nome]["count"], 1)

	def test_chi_non_si_raggiunge_resta_scritto_e_non_conta(self):
		frappe.db.set_value("CRM Lead", self.persona.name, "email", None)
		nome = self.emessa()
		fattura = next(riga for riga in solleciti.dovute() if riga.name == nome)
		self.assertEqual(solleciti.manda(fattura), R.NON_INVIATO)
		self.assertEqual(solleciti.di_fatture([nome])[nome]["count"], 0)
		# but it waits for the next turn, as any other
		self.assertNotIn(nome, self.dovute())

	def test_il_figlio_prenotato_dalla_mamma_lo_sa_la_mamma(self):
		# a child booked online by his mother, with no email of his own: the
		# appointment's reminders reached her, the payment's said «call them»
		from crm.persone import collegate, legami

		mamma = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Elena",
				"last_name": "Solleciti",
				"email": "elena.solleciti@example.com",
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value("CRM Lead", self.persona.name, "email", None)
		collegate.assicura_legame(self.persona.name, mamma.name, legami.GENITORE, books=1)
		nome = self.emessa()
		fattura = next(riga for riga in solleciti.dovute() if riga.name == nome)
		prima = frappe.db.count("Email Queue")
		self.assertEqual(solleciti.manda(fattura), R.INVIATO)
		self.assertEqual(frappe.db.count("Email Queue"), prima + 1)
		posta = frappe.get_last_doc("Email Queue")
		self.assertEqual([r.recipient for r in posta.recipients], ["elena.solleciti@example.com"])

	def test_la_data_si_legge_come_in_una_frase(self):
		from types import SimpleNamespace

		nome = self.emessa()
		frappe.db.set_value("CRM Invoice", nome, "posting_date", "2026-09-01")
		fattura = frappe.get_doc("CRM Invoice", nome)
		dove = SimpleNamespace(nome="Mario", email=self.persona.email, numero=None, lead=self.persona.name)
		lingua = frappe.local.lang
		try:
			frappe.local.lang = "it"
			frase = solleciti._testo(fattura, dove, SimpleNamespace(come_pagare=""))["frase"]
		finally:
			frappe.local.lang = lingua
		# the day in words, its article elided before the 1, never «dell'01/09/2026»
		self.assertIn("dell'1 settembre 2026", frase)
		self.assertNotIn("01/09", frase)
