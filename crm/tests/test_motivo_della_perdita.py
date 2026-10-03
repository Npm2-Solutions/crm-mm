# Copyright (c) 2026, NPM2 Solutions Srl and Contributors
# See license.txt

"""The lost reason in the deals' side panel: kept once in the layout, shown by a
deal's page while that deal is lost; a deal changing stage rewrites nothing."""

import json

import frappe
from frappe.tests import IntegrationTestCase

from crm.fcrm.doctype.utils import LOST_REASON_SECTION, with_lost_reason_section
from crm.patches.v1_0 import the_lost_reason_shows_on_the_lost_deal as patch

LAYOUT = "CRM Deal-Side Panel"


def _nomi(sezioni):
	return [s.get("name") for s in sezioni]


class LaSezione(IntegrationTestCase):
	def test_once_after_the_contacts(self):
		sezioni = [{"name": "contacts_section"}, {"name": "organization_section"}]
		con = with_lost_reason_section(sezioni)
		self.assertEqual(_nomi(con), ["contacts_section", LOST_REASON_SECTION, "organization_section"])
		self.assertIs(with_lost_reason_section(con), con)

	def test_first_without_the_contacts(self):
		self.assertEqual(_nomi(with_lost_reason_section([{"name": "x"}])), [LOST_REASON_SECTION, "x"])


class IlLayout(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _layout(self):
		return json.loads(frappe.db.get_value("CRM Fields Layout", LAYOUT, "layout") or "[]")

	def _trattativa(self):
		organizzazione = frappe.get_doc(
			{"doctype": "CRM Organization", "organization_name": f"Persa {frappe.generate_hash(length=6)}"}
		).insert(ignore_permissions=True)
		persona = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Persa"}).insert()
		return frappe.get_doc(
			{"doctype": "CRM Deal", "lead": persona.name, "organization": organizzazione.name}
		).insert()

	def test_the_patch_puts_it_back_once(self):
		if not frappe.db.exists("CRM Fields Layout", LAYOUT):
			self.skipTest("no deal side panel on this site")
		senza = [s for s in self._layout() if s.get("name") != LOST_REASON_SECTION]
		frappe.db.set_value("CRM Fields Layout", LAYOUT, "layout", json.dumps(senza))
		patch.execute()
		patch.execute()
		self.assertEqual(_nomi(self._layout()).count(LOST_REASON_SECTION), 1)

	def test_a_deal_changing_stage_rewrites_nothing(self):
		if not frappe.db.exists("CRM Fields Layout", LAYOUT):
			self.skipTest("no deal side panel on this site")
		patch.execute()
		prima = frappe.db.get_value("CRM Fields Layout", LAYOUT, ["layout", "modified"], as_dict=True)
		trattativa = self._trattativa()
		persa = frappe.db.get_value("CRM Deal Status", {"type": "Lost"}, "name")
		motivo = frappe.db.get_value("CRM Lost Reason", {}, "name")
		if not (persa and motivo):
			self.skipTest("no lost stage or reason on this site")
		trattativa.status = persa
		trattativa.lost_reason = motivo
		trattativa.lost_notes = "Prezzo"
		trattativa.save()
		aperta = frappe.db.get_value("CRM Deal Status", {"type": "Open"}, "name")
		trattativa.status = aperta
		trattativa.save()
		dopo = frappe.db.get_value("CRM Fields Layout", LAYOUT, ["layout", "modified"], as_dict=True)
		self.assertEqual(dopo.layout, prima.layout)
		self.assertEqual(dopo.modified, prima.modified)
