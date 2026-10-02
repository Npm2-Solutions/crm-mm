# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A person's page starts with the person: the shipped layouts move the person's
own fields first, a centre's own layout stays as the centre left it."""

import json

import frappe
from frappe.tests import IntegrationTestCase

from crm.install import LEAD_DATA_FIELDS, LEAD_SIDE_PANEL
from crm.patches.v1_0 import the_person_first_on_their_page as patch

ATTRIBUZIONE = {
	"label": "First Touch",
	"name": "first_touch_data_section",
	"opened": False,
	"columns": [{"name": "column_first_touch_1", "fields": ["first_touch_category"]}],
}


class TestSchedaPersona(IntegrationTestCase):
	def metti(self, nome, sezioni):
		if not frappe.db.exists("CRM Fields Layout", nome):
			doc = frappe.new_doc("CRM Fields Layout")
			doc.dt = "CRM Lead"
			doc.type = "Side Panel" if nome == patch.PANNELLO else "Data Fields"
			doc.layout = json.dumps(sezioni)
			doc.insert(ignore_permissions=True)
		else:
			frappe.db.set_value("CRM Fields Layout", nome, "layout", json.dumps(sezioni))

	def leggi(self, nome):
		return json.loads(frappe.db.get_value("CRM Fields Layout", nome, "layout"))

	def test_the_shipped_panel_starts_with_the_person(self):
		self.metti(patch.PANNELLO, patch.PRIMA_PANNELLO)
		patch.execute()
		sezioni = self.leggi(patch.PANNELLO)
		self.assertEqual(sezioni, json.loads(LEAD_SIDE_PANEL))
		self.assertEqual(sezioni[0]["name"], "person_section")
		self.assertEqual(sezioni[0]["columns"][0]["fields"][:3], ["first_name", "last_name", "mobile_no"])
		# the company, closed at the end
		self.assertFalse(sezioni[-1]["opened"])
		self.assertIn("organization", sezioni[-1]["columns"][0]["fields"])

	def test_no_field_is_lost(self):
		self.metti(patch.PANNELLO, patch.PRIMA_PANNELLO)
		patch.execute()
		prima = set(patch._campi(patch.PRIMA_PANNELLO))
		self.assertLessEqual(prima, set(patch._campi(self.leggi(patch.PANNELLO))))

	def test_the_enrichment_fields_in_another_order_are_still_shipped(self):
		sezioni = json.loads(json.dumps(patch.PRIMA_PANNELLO))
		campi = sezioni[0]["columns"][0]["fields"]
		campi.reverse()
		self.metti(patch.PANNELLO, sezioni)
		patch.execute()
		self.assertEqual(self.leggi(patch.PANNELLO)[0]["name"], "person_section")

	def test_a_layout_the_centre_changed_stays(self):
		sezioni = json.loads(json.dumps(patch.PRIMA_PANNELLO))
		sezioni[1]["columns"][0]["fields"].append("territory")
		sezioni[0]["columns"][0]["fields"].remove("territory")
		sezioni[0]["columns"][0]["fields"].remove("industry")
		self.metti(patch.PANNELLO, sezioni)
		patch.execute()
		self.assertEqual(self.leggi(patch.PANNELLO), sezioni)

	def test_the_data_tab_keeps_its_attribution(self):
		self.metti(patch.DATI, [*patch.PRIMA_DATI, ATTRIBUZIONE])
		patch.execute()
		sezioni = self.leggi(patch.DATI)
		self.assertEqual(sezioni[:-1], json.loads(LEAD_DATA_FIELDS))
		self.assertEqual(sezioni[-1], ATTRIBUZIONE)
		self.assertEqual(sezioni[0]["name"], "person_section")

	def test_a_second_run_changes_nothing(self):
		self.metti(patch.PANNELLO, patch.PRIMA_PANNELLO)
		self.metti(patch.DATI, [*patch.PRIMA_DATI, ATTRIBUZIONE])
		patch.execute()
		pannello, dati = self.leggi(patch.PANNELLO), self.leggi(patch.DATI)
		patch.execute()
		self.assertEqual(self.leggi(patch.PANNELLO), pannello)
		self.assertEqual(self.leggi(patch.DATI), dati)

	def test_every_field_of_the_new_layouts_exists(self):
		meta = frappe.get_meta("CRM Lead")
		for layout in (LEAD_SIDE_PANEL, LEAD_DATA_FIELDS):
			for campo in patch._campi(json.loads(layout)):
				self.assertTrue(meta.has_field(campo), campo)
