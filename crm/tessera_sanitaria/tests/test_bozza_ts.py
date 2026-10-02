# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The Sistema TS's report checked on the draft, on a real site.

An issued document is frozen, and a report the Sistema TS refuses in January is a
credit note and a phone call. So what it would refuse is said while the invoice is
being written: what belongs to the document stops the issue, what belongs to the
company is said and does not stop the invoice the patient is waiting for, and what
invoicing already says about the patient is not said twice.
"""

from __future__ import annotations

import frappe
from frappe.utils import add_days, getdate

from crm.invoicing import documento, emissione
from crm.tessera_sanitaria import documento as ts
from crm.tests.test_invoicing import CF_PAZIENTE, InvoicingBase


class IlSistemaTSPrimaDiEmettere(InvoicingBase):
	def dati(self, rate=100, **altro):
		return {
			"billing_name": "Mario Rossi",
			"first_name": "Mario",
			"last_name": "Rossi",
			"fiscal_code": CF_PAZIENTE,
			"recipient_type": "persona_fisica",
			"payment_method": "MP08",
			"items": [
				{
					"billable_service": self.seduta.name,
					"service_provider": self.psicologo.name,
					"qty": 1,
					"rate": rate,
				}
			],
			**altro,
		}

	def test_quello_che_rifiuterebbe_ferma_l_emissione(self):
		vista = emissione.preview(self.dati(rate=100000))
		self.assertTrue(any("above what the Sistema TS takes" in errore for errore in vista["errors"]))
		with self.assertRaises(frappe.ValidationError):
			emissione.issue(self.dati(rate=100000))

	def test_quello_dell_azienda_si_dice_e_non_ferma(self):
		frappe.db.set_value("CRM Invoicing Company", self.azienda.name, "fiscal_code", "XXX")
		frappe.clear_document_cache("CRM Invoicing Company", self.azienda.name)
		self.addCleanup(frappe.clear_document_cache, "CRM Invoicing Company", self.azienda.name)

		vista = emissione.preview(self.dati())
		self.assertFalse(any("whoever issues" in errore for errore in vista["errors"]))
		self.assertTrue(
			any(
				"until the issuing company is complete: the codice fiscale of whoever issues is not valid: XXX"
				in avviso
				for avviso in vista["warnings"]
			)
		)
		self.assertEqual(emissione.issue(self.dati())["docstatus"], 1)

	def test_il_codice_fiscale_del_paziente_si_dice_una_volta(self):
		vista = emissione.preview(self.dati(fiscal_code=""))
		detti = [errore for errore in vista["errors"] if "odice fiscale" in errore]
		self.assertEqual(len(detti), 1, detti)

	def test_una_fattura_fuori_dal_sistema_ts_non_si_controlla(self):
		fattura = self.fattura(self.consulenza.name, self.consulente.name)
		preparato = documento.prepara(fattura)
		self.assertFalse(preparato["classificazione"].ts_richiesto)
		from crm.tessera_sanitaria import controlla_bozza

		self.assertEqual(controlla_bozza(fattura, preparato), ([], []))

	def test_il_rimborso_si_paga_il_giorno_della_nota(self):
		emessa = emissione.issue(self.dati())
		nota = frappe.get_doc("CRM Invoice", emissione.credit_note(emessa["name"])["name"])
		nota.payment_date = add_days(nota.posting_date, -3)
		spesa = ts.documento_spesa(nota, documento.azienda(nota))
		self.assertEqual(spesa.data_pagamento, getdate(nota.posting_date))
