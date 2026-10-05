# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The choices the screens get, on a real site.

The settings draw invoicing's DocTypes from their own layout (`crm.api.doc.get_fields`)
and the Desk's invoice form asks `get_options`: in both, a code select offers names,
in the healthcare profile only the healthcare ones, and a value stored before stays.
The pairs field -> vocabulary are the ones the pure test checks against the
DocTypes' options (`test_voci.CAMPI_DEL_MOTORE`): here the two lists are held equal.
"""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.doc import get_fields
from crm.invoicing import scelte
from crm.invoicing.engine import voci
from crm.invoicing.tests.test_voci import CAMPI_DEL_MOTORE


def _sanitario():
	return patch.object(scelte, "profilo", return_value=voci.SANITARIO)


def _generale():
	return patch.object(scelte, "profilo", return_value=voci.GENERALE)


def _campo(campi, fieldname):
	return next(campo for campo in campi if campo.get("fieldname") == fieldname)


class LeScelteInParole(IntegrationTestCase):
	def test_le_coppie_sono_quelle_del_test_puro(self):
		nostre = {
			(frappe.scrub(doctype), fieldname): famiglia
			for (doctype, fieldname), famiglia in scelte.CAMPI.items()
			if (frappe.scrub(doctype), fieldname) in CAMPI_DEL_MOTORE
		}
		self.assertEqual(nostre, CAMPI_DEL_MOTORE)
		for (doctype, fieldname), famiglia in scelte.CAMPI.items():
			self.assertTrue(frappe.get_meta(doctype).get_field(fieldname), f"{doctype}.{fieldname}")
			self.assertTrue(voci.tutte(famiglia), f"{famiglia} has no words")

	def test_un_select_offre_nomi_e_spiegazioni(self):
		with _generale():
			regime = _campo(get_fields("CRM Invoicing Company"), "tax_regime")
		self.assertEqual(regime["options"][0]["value"], "RF01")
		self.assertTrue(all(scelta["label"] != scelta["value"] for scelta in regime["options"]))
		self.assertEqual(len(regime["options"]), len(voci.tutte("regime_fiscale")))

	def test_il_profilo_sanitario_toglie_quello_che_non_serve(self):
		with _sanitario():
			regime = _campo(get_fields("CRM Invoicing Company"), "tax_regime")
			natura = _campo(get_fields("CRM Billable Service"), "vat_nature")
		self.assertEqual([s["value"] for s in regime["options"]], ["RF01", "RF19", "RF02"])
		# not required: the empty choice first, then the three a practice meets
		self.assertEqual([s["value"] for s in natura["options"]], ["", "N4", "N2.2", "N1"])

	def test_la_causale_diventa_un_elenco(self):
		with _sanitario():
			causale = _campo(get_fields("CRM Professional Qualification"), "payment_reason")
		self.assertEqual(causale["fieldtype"], "Select")
		# it starts with a value: nothing to leave empty
		self.assertEqual([s["value"] for s in causale["options"]], ["A", "M", "M2"])

	def test_il_paese_per_nome(self):
		paese = _campo(get_fields("CRM Invoicing Company"), "country")
		self.assertEqual(paese["fieldtype"], "Select")
		valori = {scelta["value"] for scelta in paese["options"]}
		self.assertIn("IT", valori)
		# no grouping nor reserved code is a country to issue from
		self.assertFalse(valori & scelte.NON_PAESI)
		italiani = {scelta["value"]: scelta["label"] for scelta in scelte.paesi("it")}
		self.assertEqual(italiani["IT"], "Italia")
		self.assertEqual(italiani["DE"], "Germania")
		# in the order of the names, an accent where it falls
		nomi = [scelta["label"] for scelta in scelte.paesi("it")]
		self.assertLess(nomi.index("Austria"), nomi.index("Italia"))

	def test_le_qualifiche_di_un_centro_medico_sono_sanitarie(self):
		with _sanitario():
			qualifica = _campo(get_fields("CRM Service Provider"), "qualification")
		# health professions only, and never who issues (a facility, a pharmacy)
		filtro = frappe.parse_json(qualifica.get("link_filters"))
		self.assertEqual(filtro["category"], "sanitaria")
		self.assertEqual(filtro["sender_category"][0], "not in")
		self.assertIn("farmacia", filtro["sender_category"][1])
		with _generale():
			qualifica = _campo(get_fields("CRM Service Provider"), "qualification")
		filtro = frappe.parse_json(qualifica.get("link_filters"))
		self.assertNotIn("category", filtro)
		self.assertIn("struttura_autorizzata", filtro["sender_category"][1])

	def test_gli_altri_doctype_non_cambiano(self):
		with _sanitario():
			campi = get_fields("CRM Lead")
		self.assertTrue(all(not isinstance(campo, dict) for campo in campi))

	def test_il_modulo_della_fattura_tiene_quello_che_c_e(self):
		fattura = {
			"company": "",
			"payment_method": "MP12",
			"items": [{"vat_nature": "N4"}, {"vat_nature": "N6.3"}],
			"payments": [],
		}
		with _sanitario():
			risposta = scelte.get_options("CRM Invoice", fattura)
		pagamenti = [s["value"] for s in risposta["fields"]["payment_method"]]
		# the payment method starts with one: no empty choice
		self.assertEqual(pagamenti[:3], ["MP08", "MP01", "MP05"])
		# a RIBA chosen before stays, named, at the end
		self.assertEqual(pagamenti[-1], "MP12")
		self.assertEqual(risposta["fields"]["payment_method"][-1]["label"], frappe._("RIBA"))
		nature = [s["value"] for s in risposta["tables"]["items"]["vat_nature"]]
		self.assertEqual(nature, ["", "N4", "N2.2", "N1", "N6.3"])
		self.assertIn("payment_method", risposta["tables"]["payments"])
		# what is read only is named too
		self.assertIn("channel", risposta["fields"])


class IProfessionistiInParole(IntegrationTestCase):
	"""A professional's qualification is stored by its code: the search for one shows
	the qualification's name, and finds by it."""

	def test_la_qualifica_per_nome_non_per_codice(self):
		from frappe.desk.search import search_link

		from crm.invoicing.install import semina_qualifiche
		from crm.tests.test_invoicing import InvoicingBase

		semina_qualifiche()
		InvoicingBase.crea_erogatore("Studio Ricerca Parole", "societa_servizi")
		nome = frappe.db.get_value("CRM Professional Qualification", "societa_servizi", "qualification_name")
		(trovato,) = [
			r
			for r in search_link("CRM Service Provider", "Ricerca Parole")
			if r["value"] == "Studio Ricerca Parole"
		]
		self.assertEqual(trovato["description"], nome)
		self.assertNotIn("societa_servizi", trovato["description"])
		# by the qualification's own words too
		per_qualifica = search_link("CRM Service Provider", nome.split()[0])
		self.assertIn("Studio Ricerca Parole", [r["value"] for r in per_qualifica])
