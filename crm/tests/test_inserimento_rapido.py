# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A new person reads by rows on a phone: the shipped quick entries hold each of
the person's rows as a section of its own, and the patch splits a section still as
it was shipped, never one the centre changed."""

import json

import frappe
from frappe.tests import IntegrationTestCase

from crm.install import DEAL_QUICK_ENTRY, LEAD_QUICK_ENTRY
from crm.patches.v1_0 import the_quick_entry_reads_by_rows as patch

PERSONA = "CRM Lead-Quick Entry"
TRATTATIVA = "CRM Deal-Quick Entry"


def come_prima(spedito, sezione, seconda):
	"""A shipped layout as it was before: the two rows one section of three columns."""
	sezioni = json.loads(spedito)
	i = next(n for n, s in enumerate(sezioni) if s["name"] == sezione)
	unita = {
		**sezioni[i],
		"columns": [
			{"name": colonna["name"], "fields": list(campi)}
			for colonna, campi in zip(sezioni[i]["columns"], patch.PRIMA, strict=True)
		],
	}
	return [*sezioni[:i], unita, *[s for s in sezioni[i + 1 :] if s["name"] != seconda]]


def al_telefono(sezioni):
	"""The fields in the order a phone draws them: section by section, column by column."""
	return [campo for s in sezioni for colonna in s.get("columns", []) for campo in colonna.get("fields", [])]


class TestInserimentoRapido(IntegrationTestCase):
	def setUp(self):
		for nome in (PERSONA, TRATTATIVA):
			if frappe.db.exists("CRM Fields Layout", nome):
				prima = frappe.db.get_value("CRM Fields Layout", nome, "layout")
				self.addCleanup(frappe.db.set_value, "CRM Fields Layout", nome, "layout", prima)

	def metti(self, nome, sezioni):
		if not frappe.db.exists("CRM Fields Layout", nome):
			doc = frappe.new_doc("CRM Fields Layout")
			doc.dt = "CRM Lead" if nome == PERSONA else "CRM Deal"
			doc.type = "Quick Entry"
			doc.layout = json.dumps(sezioni)
			doc.insert(ignore_permissions=True)
			self.addCleanup(frappe.delete_doc, "CRM Fields Layout", nome, force=True)
		else:
			frappe.db.set_value("CRM Fields Layout", nome, "layout", json.dumps(sezioni))

	def leggi(self, nome):
		return json.loads(frappe.db.get_value("CRM Fields Layout", nome, "layout"))

	def test_a_new_person_reads_name_first_on_a_phone(self):
		campi = al_telefono(json.loads(LEAD_QUICK_ENTRY))
		self.assertEqual(campi[:6], ["salutation", "first_name", "last_name", "mobile_no", "email", "gender"])
		# the deal's person, after the company it may be at
		campi = al_telefono(json.loads(DEAL_QUICK_ENTRY))
		inizio = campi.index("salutation")
		self.assertEqual(
			campi[inizio : inizio + 6],
			["salutation", "first_name", "last_name", "mobile_no", "email", "gender"],
		)

	def test_the_shipped_person_is_split_into_rows(self):
		self.metti(PERSONA, come_prima(LEAD_QUICK_ENTRY, "person_section", "person_contacts_section"))
		patch.execute()
		self.assertEqual(self.leggi(PERSONA), json.loads(LEAD_QUICK_ENTRY))

	def test_the_deals_person_keeps_its_fixed_rows(self):
		self.metti(
			TRATTATIVA,
			come_prima(DEAL_QUICK_ENTRY, "contact_details_section", "contact_details_more_section"),
		)
		patch.execute()
		sezioni = self.leggi(TRATTATIVA)
		self.assertEqual(sezioni, json.loads(DEAL_QUICK_ENTRY))
		righe = [s for s in sezioni if s["name"].startswith("contact_details")]
		self.assertEqual([s.get("editable") for s in righe], [False, False])

	def test_a_section_the_centre_changed_stays(self):
		sezioni = come_prima(LEAD_QUICK_ENTRY, "person_section", "person_contacts_section")
		sezioni[0]["columns"][1]["fields"].append("phone")
		self.metti(PERSONA, sezioni)
		patch.execute()
		self.assertEqual(self.leggi(PERSONA), sezioni)

	def test_a_layout_in_tabs_is_split_inside_its_tab(self):
		sezioni = come_prima(LEAD_QUICK_ENTRY, "person_section", "person_contacts_section")
		self.metti(PERSONA, [{"name": "first_tab", "sections": sezioni}])
		patch.execute()
		self.assertEqual(
			self.leggi(PERSONA), [{"name": "first_tab", "sections": json.loads(LEAD_QUICK_ENTRY)}]
		)

	def test_a_second_run_changes_nothing(self):
		self.metti(PERSONA, come_prima(LEAD_QUICK_ENTRY, "person_section", "person_contacts_section"))
		patch.execute()
		dopo = self.leggi(PERSONA)
		patch.execute()
		self.assertEqual(self.leggi(PERSONA), dopo)

	def test_every_field_exists(self):
		for doctype, spedito in (("CRM Lead", LEAD_QUICK_ENTRY), ("CRM Deal", DEAL_QUICK_ENTRY)):
			meta = frappe.get_meta(doctype)
			for campo in al_telefono(json.loads(spedito)):
				self.assertTrue(meta.has_field(campo), f"{doctype}.{campo}")
