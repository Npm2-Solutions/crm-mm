# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A medical centre's invoicing in three questions, on a real site.

A physiotherapist on the flat-rate regime answers who issues, the regime and the
profession: the company reports to the Sistema TS as a health professional, with
the INPS fund of the profession and no withholding by default. A facility cannot
be on the flat-rate regime. The agenda's services become cards that are healthcare
services, exempt with the annotation the invoices carry, with the only expense type
a health professional has - once, and a card of the same name is tied, not doubled.
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from crm.invoicing.install import semina_qualifiche
from crm.tessera_sanitaria import preimpostazione
from crm.tests.test_invoicing import InvoicingBase

AZIENDA = "Studio Test Fatturazione"


def _servizio(nome: str, prezzo: float = 80, chi: str = "Administrator") -> str:
	if not frappe.db.exists("CRM Service", nome):
		frappe.get_doc(
			{
				"doctype": "CRM Service",
				"service_name": nome,
				"enabled": 1,
				"default_price": prezzo,
				"staff": [{"user": chi}],
			}
		).insert(ignore_permissions=True)
	return nome


class LeTreDomande(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		semina_qualifiche()
		InvoicingBase.crea_azienda()

	def setUp(self):
		frappe.set_user("Administrator")

	def test_le_domande_hanno_le_scelte_di_un_centro_medico(self):
		dati = preimpostazione.get_setup(AZIENDA)
		self.assertEqual(
			[s["value"] for s in dati["issuers"]],
			[
				"struttura_autorizzata",
				"medico_odontoiatra",
				"professionista_sanitario",
				"struttura_accreditata",
			],
		)
		self.assertEqual([s["value"] for s in dati["regimes"]], ["RF01", "RF19", "RF02"])
		professioni = {p["value"] for p in dati["professions"]["professionista_sanitario"]}
		self.assertIn("fisioterapista", professioni)
		self.assertNotIn("medico_chirurgo", professioni)
		self.assertIn("medico_chirurgo", {p["value"] for p in dati["professions"]["medico_odontoiatra"]})
		# a name, never a code
		self.assertTrue(all(s["label"] != s["value"] for s in dati["issuers"]))

	def test_un_fisioterapista_nel_forfettario(self):
		frappe.db.set_value("CRM Invoicing Company", AZIENDA, "apply_withholding_by_default", 1)
		dati = preimpostazione.apply_setup(AZIENDA, "professionista_sanitario", "RF19", "fisioterapista")
		azienda = frappe.get_doc("CRM Invoicing Company", AZIENDA)
		self.assertEqual(azienda.sender_category, "professionista_sanitario")
		self.assertEqual(azienda.tax_regime, "RF19")
		qualifica = frappe.get_doc("CRM Professional Qualification", "fisioterapista")
		self.assertEqual(azienda.fund_type, qualifica.fund_type)
		self.assertEqual(azienda.fund_rate, qualifica.fund_rate)
		self.assertFalse(azienda.apply_withholding_by_default)
		self.assertTrue(dati["done"])
		self.assertEqual(dati["expense_type"]["value"], "SP")
		self.assertEqual(dati["card_defaults"]["ts_expense_type"], "SP")
		self.assertIn("art. 10, n. 18", dati["card_defaults"]["exemption_reference"])

	def test_una_struttura_e_nel_regime_ordinario(self):
		with self.assertRaises(frappe.ValidationError):
			preimpostazione.apply_setup(AZIENDA, "struttura_autorizzata", "RF19")
		# and it reports with the Region's codes, all three
		frappe.db.set_value(
			"CRM Invoicing Company", AZIENDA, {"region_code": "", "asl_code": "", "ssa_code": ""}
		)
		with self.assertRaises(frappe.ValidationError):
			preimpostazione.apply_setup(AZIENDA, "struttura_autorizzata", "RF01", region_code="120")
		dati = preimpostazione.apply_setup(
			AZIENDA, "struttura_autorizzata", "RF01", region_code="120", asl_code="201", ssa_code="ab12"
		)
		azienda = frappe.get_doc("CRM Invoicing Company", AZIENDA)
		self.assertEqual((azienda.region_code, azienda.asl_code, azienda.ssa_code), ("120", "201", "AB12"))
		self.assertFalse(azienda.fund_type)
		self.assertEqual(dati["expense_type"]["value"], "SR")
		self.assertIn("art. 10, n. 19", dati["card_defaults"]["exemption_reference"])

		# the same centre answers again, as a professional: the facility's codes go
		preimpostazione.apply_setup(AZIENDA, "professionista_sanitario", "RF01", "psicologo")
		azienda = frappe.get_doc("CRM Invoicing Company", AZIENDA)
		self.assertEqual((azienda.region_code, azienda.asl_code, azienda.ssa_code), ("", "", ""))
		self.assertEqual(azienda.fund_type, "TC21")

	def test_la_professione_e_di_chi_emette(self):
		# a doctor's qualification for a physiotherapist invoicing in their own name
		with self.assertRaises(frappe.ValidationError):
			preimpostazione.apply_setup(AZIENDA, "professionista_sanitario", "RF01", "medico_chirurgo")
		with self.assertRaises(frappe.ValidationError):
			preimpostazione.apply_setup(AZIENDA, "non_sanitario", "RF01")

	def test_le_schede_dai_servizi_dell_agenda(self):
		preimpostazione.apply_setup(AZIENDA, "professionista_sanitario", "RF01", "fisioterapista")
		# who performs it: the agenda says one person, and that person is a provider
		frappe.db.delete("CRM Service Provider", {"user": "Administrator"})
		erogatore = (
			frappe.get_doc(
				{
					"doctype": "CRM Service Provider",
					"provider_name": "Fisioterapista di prova",
					"qualification": "fisioterapista",
					"user": "Administrator",
					"enabled": 1,
				}
			)
			.insert(ignore_permissions=True)
			.name
		)
		nuovo = _servizio("Rieducazione posturale di prova", 65)
		omonimo = _servizio("Linfodrenaggio di prova")
		if not frappe.db.exists("CRM Billable Service", omonimo):
			frappe.get_doc(
				{
					"doctype": "CRM Billable Service",
					"service_name": omonimo,
					"fiscal_description": omonimo,
					"vat_rate": 22,
				}
			).insert(ignore_permissions=True)
		frappe.db.set_value("CRM Billable Service", omonimo, "crm_service", None)

		esito = preimpostazione.cards_from_services(AZIENDA)
		self.assertIn(nuovo, esito["created"])
		self.assertIn(omonimo, esito["linked"])
		scheda = frappe.get_doc("CRM Billable Service", nuovo)
		self.assertEqual(scheda.crm_service, nuovo)
		self.assertTrue(scheda.is_healthcare)
		self.assertTrue(scheda.vat_exempt)
		self.assertEqual(scheda.vat_nature, "N4")
		self.assertEqual(scheda.ts_expense_type, "SP")
		self.assertEqual(scheda.default_rate, 65)
		self.assertEqual(scheda.default_provider, erogatore)
		self.assertIn("art. 10", scheda.exemption_reference)
		self.assertFalse(scheda.verified_by_accountant)
		# the card of the same name keeps what somebody wrote on it
		self.assertEqual(frappe.db.get_value("CRM Billable Service", omonimo, "vat_rate"), 22)

		# once
		self.assertEqual(preimpostazione.cards_from_services(AZIENDA), {"created": [], "linked": []})

	def test_la_scheda_di_chi_non_e_esente_ha_l_iva(self):
		"""Pilates with the kinesiologist: no health profession (Ris. AdE 9/2026),
		taxed at its rate; an exempt card would be refused at the first invoice."""
		preimpostazione.apply_setup(AZIENDA, "professionista_sanitario", "RF01", "fisioterapista")
		chinesiologo = "kinesiologist.cards@example.com"
		if not frappe.db.exists("User", chinesiologo):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": chinesiologo,
					"first_name": "Kinesiologist",
					"send_welcome_email": 0,
				}
			).insert(ignore_permissions=True)
		frappe.db.delete("CRM Service Provider", {"user": chinesiologo})
		frappe.get_doc(
			{
				"doctype": "CRM Service Provider",
				"provider_name": "Chinesiologo di prova",
				"qualification": "chinesiologo",
				"user": chinesiologo,
				"enabled": 1,
			}
		).insert(ignore_permissions=True)
		pilates = _servizio("Pilates di prova delle schede", 20, chi=chinesiologo)
		self.assertIn(pilates, preimpostazione.cards_from_services(AZIENDA)["created"])
		scheda = frappe.get_doc("CRM Billable Service", pilates)
		self.assertFalse(scheda.vat_exempt)
		self.assertFalse(scheda.is_healthcare)
		self.assertEqual(scheda.vat_rate, 22)
		self.assertFalse(scheda.ts_expense_type)
		self.assertFalse(scheda.exemption_reference)
