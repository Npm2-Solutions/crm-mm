# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A person reads in order on a phone: the shipped quick entries hold each of the
person's rows as a section of its own, the Data tab a column per kind, and the patches
change a section still as it was shipped, never one the centre changed. A person is
added without a company: name and surname, how to reach them, the rest, the company
only by its name."""

import json

import frappe
from frappe.tests import IntegrationTestCase

from crm.install import DEAL_QUICK_ENTRY, LEAD_DATA_FIELDS, LEAD_QUICK_ENTRY
from crm.patches.v1_0 import a_person_is_added_without_a_company as senza_azienda
from crm.patches.v1_0 import the_person_reads_in_order_on_a_phone as patch

PERSONA = "CRM Lead-Quick Entry"
TRATTATIVA = "CRM Deal-Quick Entry"
DATI = "CRM Lead-Data Fields"


def come_prima(spedito, sezione, seconda):
	"""A shipped layout as it was before: the two rows one section of three columns."""
	sezioni = json.loads(spedito) if isinstance(spedito, str) else json.loads(json.dumps(spedito))
	i = next(n for n, s in enumerate(sezioni) if s["name"] == sezione)
	unita = {
		**sezioni[i],
		"columns": [
			{"name": colonna["name"], "fields": list(campi)}
			for colonna, campi in zip(sezioni[i]["columns"], patch.PRIMA, strict=True)
		],
	}
	return [*sezioni[:i], unita, *[s for s in sezioni[i + 1 :] if s["name"] != seconda]]


def del_04_10():
	"""«Aggiungi una persona» as the first patch left it: the person in two rows, the
	company in three columns of its fields."""
	persona = json.loads(patch.PERSONA_DEL_04_10)
	azienda = {
		"name": "organization_section",
		"columns": [
			{"name": n, "fields": list(campi)}
			for n, campi in zip(
				("column_GHfX", "column_hXjS", "column_RDNA"), senza_azienda.AZIENDA_PRIMA, strict=True
			)
		],
	}
	resto = [s for s in json.loads(LEAD_QUICK_ENTRY) if s["name"] == "lead_section"]
	return [*persona, azienda, *resto]


def al_telefono(sezioni):
	"""The fields in the order a phone draws them: section by section, column by column."""
	return [campo for s in sezioni for colonna in s.get("columns", []) for campo in colonna.get("fields", [])]


class TestInserimentoRapido(IntegrationTestCase):
	def setUp(self):
		for nome in (PERSONA, TRATTATIVA, DATI):
			if frappe.db.exists("CRM Fields Layout", nome):
				prima = frappe.db.get_value("CRM Fields Layout", nome, "layout")
				self.addCleanup(frappe.db.set_value, "CRM Fields Layout", nome, "layout", prima)

	def metti(self, nome, sezioni):
		if not frappe.db.exists("CRM Fields Layout", nome):
			doc = frappe.new_doc("CRM Fields Layout")
			doc.dt = "CRM Deal" if nome == TRATTATIVA else "CRM Lead"
			doc.type = "Data Fields" if nome == DATI else "Quick Entry"
			doc.layout = json.dumps(sezioni)
			doc.insert(ignore_permissions=True)
			self.addCleanup(frappe.delete_doc, "CRM Fields Layout", nome, force=True)
		else:
			frappe.db.set_value("CRM Fields Layout", nome, "layout", json.dumps(sezioni))

	def leggi(self, nome):
		return json.loads(frappe.db.get_value("CRM Fields Layout", nome, "layout"))

	def test_a_new_person_reads_name_first_on_a_phone(self):
		campi = al_telefono(json.loads(LEAD_QUICK_ENTRY))
		self.assertEqual(campi[:6], ["first_name", "last_name", "mobile_no", "email", "gender", "salutation"])
		# the company only by its name, the owner after it
		self.assertEqual(campi[6:], ["organization", "lead_owner"])
		# the deal's person, after the company it may be at
		campi = al_telefono(json.loads(DEAL_QUICK_ENTRY))
		inizio = campi.index("salutation")
		self.assertEqual(
			campi[inizio : inizio + 6],
			["salutation", "first_name", "last_name", "mobile_no", "email", "gender"],
		)

	def test_the_shipped_person_is_split_into_rows(self):
		self.metti(PERSONA, come_prima(del_04_10(), "person_section", "person_contacts_section"))
		patch.execute()
		self.assertEqual(self.leggi(PERSONA), del_04_10())

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
		sezioni = come_prima(del_04_10(), "person_section", "person_contacts_section")
		sezioni[0]["columns"][1]["fields"].append("phone")
		self.metti(PERSONA, sezioni)
		patch.execute()
		self.assertEqual(self.leggi(PERSONA), sezioni)

	def test_a_layout_in_tabs_is_split_inside_its_tab(self):
		sezioni = come_prima(del_04_10(), "person_section", "person_contacts_section")
		self.metti(PERSONA, [{"name": "first_tab", "sections": sezioni}])
		patch.execute()
		self.assertEqual(self.leggi(PERSONA), [{"name": "first_tab", "sections": del_04_10()}])

	def test_a_second_run_changes_nothing(self):
		self.metti(PERSONA, come_prima(del_04_10(), "person_section", "person_contacts_section"))
		patch.execute()
		dopo = self.leggi(PERSONA)
		patch.execute()
		self.assertEqual(self.leggi(PERSONA), dopo)

	def test_every_field_exists(self):
		for doctype, spedito in (("CRM Lead", LEAD_QUICK_ENTRY), ("CRM Deal", DEAL_QUICK_ENTRY)):
			meta = frappe.get_meta(doctype)
			for campo in al_telefono(json.loads(spedito)):
				self.assertTrue(meta.has_field(campo), f"{doctype}.{campo}")

	def test_the_data_tab_reads_like_the_panel(self):
		campi = al_telefono([s for s in json.loads(LEAD_DATA_FIELDS) if s["name"] == "person_section"])
		self.assertEqual(
			campi, ["first_name", "last_name", "mobile_no", "phone", "email", "gender", "salutation"]
		)

	def test_the_shipped_data_tab_gets_a_column_per_kind(self):
		spedite = json.loads(LEAD_DATA_FIELDS)
		prima = json.loads(LEAD_DATA_FIELDS)
		prima[0]["columns"] = [
			{"name": f"column_{i}", "fields": list(campi)} for i, campi in enumerate(patch.PRIMA_DATI)
		]
		attribuzione = {"label": "First Touch", "name": "first_touch_data_section", "columns": []}
		self.metti(DATI, [*prima, attribuzione])
		patch.execute()
		dopo = self.leggi(DATI)
		self.assertEqual(dopo[0]["columns"], spedite[0]["columns"])
		# its label and its state stay, and so does everything after it
		self.assertEqual((dopo[0]["label"], dopo[0]["opened"]), ("Person", True))
		self.assertEqual(dopo[1:], [*spedite[1:], attribuzione])

	def test_a_data_tab_the_centre_changed_stays(self):
		sezioni = json.loads(LEAD_DATA_FIELDS)
		sezioni[0]["columns"] = [{"name": "c", "fields": ["email", "first_name"]}]
		self.metti(DATI, sezioni)
		patch.execute()
		self.assertEqual(self.leggi(DATI), sezioni)

	def test_a_person_is_added_without_a_company(self):
		self.metti(PERSONA, del_04_10())
		senza_azienda.execute()
		self.assertEqual(self.leggi(PERSONA), json.loads(LEAD_QUICK_ENTRY))

	def test_a_site_that_never_ran_either_patch_keeps_gender_and_title(self):
		self.metti(PERSONA, come_prima(del_04_10(), "person_section", "person_contacts_section"))
		patch.execute()
		senza_azienda.execute()
		self.assertEqual(self.leggi(PERSONA), json.loads(LEAD_QUICK_ENTRY))

	def test_a_company_the_centre_changed_stays(self):
		sezioni = del_04_10()
		sezioni[2]["columns"][1]["fields"].remove("annual_revenue")
		self.metti(PERSONA, sezioni)
		senza_azienda.execute()
		dopo = self.leggi(PERSONA)
		# the person is the new one, the company the centre's
		self.assertEqual(dopo[:3], json.loads(LEAD_QUICK_ENTRY)[:3])
		self.assertEqual(dopo[3], sezioni[2])

	def test_a_person_the_centre_changed_stays(self):
		sezioni = del_04_10()
		sezioni[1]["columns"][2]["fields"].append("phone")
		self.metti(PERSONA, sezioni)
		senza_azienda.execute()
		dopo = self.leggi(PERSONA)
		self.assertEqual(dopo[:2], sezioni[:2])
		self.assertEqual(dopo[2]["columns"], json.loads(LEAD_QUICK_ENTRY)[3]["columns"])

	def test_without_a_company_in_tabs_and_twice(self):
		self.metti(PERSONA, [{"name": "first_tab", "sections": del_04_10()}])
		senza_azienda.execute()
		senza_azienda.execute()
		self.assertEqual(
			self.leggi(PERSONA), [{"name": "first_tab", "sections": json.loads(LEAD_QUICK_ENTRY)}]
		)
