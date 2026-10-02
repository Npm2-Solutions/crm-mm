# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The issuing company, only with what somebody has to set (02/10/2026).

The invoices leave through Itala on the agency's account and come back the same way,
in both directions, paid in the plan's SdI credits; the Agenzia's free service keeps
the SdI documents. Nobody chooses any of it: whatever a request says, the company
saves it so, and the screen does not draw it. The numbering is never empty, and the
format is picked among examples. The tab of the Sistema TS asks how the expenses get
there before asking for the credentials that way needs.
"""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.doc import get_fields
from crm.invoicing import scelte
from crm.invoicing.engine import voci
from crm.invoicing.engine.numerazione import FORMATO_DEFAULT, valida_formato

AZIENDA = "CRM Invoicing Company"


class SoloQuelloCheServe(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def nuova(self, **valori):
		return frappe.get_doc(
			{
				"doctype": AZIENDA,
				"company_name": f"Studio Essenziale {frappe.generate_hash(length=6)}",
				"tax_id": "00743110157",
				"address_line": "Via Roma 1",
				"postal_code": "20100",
				"city": "Milano",
				"tax_regime": "RF01",
				**valori,
			}
		).insert(ignore_permissions=True)

	def test_niente_da_scegliere(self):
		azienda = self.nuova(
			sdi_mode="export",
			sdi_flow="uscita",
			conservation_service="altro",
			document_mode="elettronica_extra_sdi",
		)
		self.assertEqual(
			(azienda.sdi_mode, azienda.sdi_flow, azienda.conservation_service, azienda.document_mode),
			("provider", "entrambi", "agenzia_entrate", "analogico_con_copia"),
		)

	def test_la_numerazione_non_e_mai_vuota(self):
		azienda = self.nuova(series_electronic="", series_healthcare="  ", number_format="")
		self.assertEqual(
			(azienda.series_electronic, azienda.series_healthcare, azienda.number_format),
			("E", "S", FORMATO_DEFAULT),
		)
		# a series somebody wrote stays as written
		azienda.series_healthcare = "SAN"
		azienda.save(ignore_permissions=True)
		self.assertEqual(azienda.series_healthcare, "SAN")

	def test_il_formato_si_sceglie_tra_esempi(self):
		esempi = [voce.valore for voce in voci.tutte("formato_numero")]
		self.assertEqual(esempi[0], FORMATO_DEFAULT)
		# every example passes the Sistema TS, the test series too
		for formato in esempi:
			for serie in ("E", "S", "PROVA-S"):
				valida_formato(formato, serie, 2026)
		with patch.object(scelte, "profilo", return_value=voci.SANITARIO):
			campo = next(c for c in get_fields(AZIENDA, True) if c.get("fieldname") == "number_format")
		self.assertEqual(campo["fieldtype"], "Select")
		self.assertEqual([scelta["value"] for scelta in campo["options"]], esempi)
		self.assertEqual(campo["options"][0]["label"], "2026/S/15")

	def test_la_pagina_non_disegna_quello_che_non_si_sceglie(self):
		campi = {c.fieldname: c for c in get_fields(AZIENDA, True)}
		for nascosto in (
			"sdi_mode",
			"sdi_flow",
			"provider_environment",
			"sdi_username",
			"sdi_password",
			"conservation_service",
			"conservation_local",
			"document_mode",
		):
			self.assertTrue(campi[nascosto].hidden, nascosto)
		self.assertFalse(campi["conservation_joined"].hidden)
		self.assertEqual(campi["tab_healthcare"].label, "Sistema TS")
		# how the expenses get there, before the credentials that way needs
		ordine = [c.fieldname for c in get_fields(AZIENDA, True)]
		self.assertLess(ordine.index("ts_mode"), ordine.index("ts_username"))

	def test_chi_emette_tra_quelli_di_un_centro_medico(self):
		with patch.object(scelte, "profilo", return_value=voci.SANITARIO):
			campo = next(c for c in get_fields(AZIENDA, True) if c.get("fieldname") == "sender_category")
		offerti = [scelta["value"] for scelta in campo["options"]]
		for sanitario in (
			"medico_odontoiatra",
			"professionista_sanitario",
			"struttura_autorizzata",
			"struttura_accreditata",
		):
			self.assertIn(sanitario, offerti)
		for altro in ("veterinario", "farmacia", "parafarmacia", "ottico"):
			self.assertNotIn(altro, offerti)
