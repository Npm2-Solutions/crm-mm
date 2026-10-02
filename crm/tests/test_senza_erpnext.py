# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""DottorCloud connects to no ERP (02/10/2026): the patch takes away what the
ERPNext integration had left on a site, and nothing of it is registered any more."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils.password import set_encrypted_password

from crm.patches.v1_0 import dottorcloud_does_not_connect_erpnext as patch
from crm.permissions import livelli

IMPOSTAZIONI = patch.IMPOSTAZIONI


class TestSenzaERPNext(IntegrationTestCase):
	def semina(self):
		"""What a site that used the integration has: its fields (only their rows, so
		no column is made here), its form script, its values and its secret."""
		for doctype, fieldname in patch.CAMPI:
			frappe.get_doc(
				{
					"doctype": "Custom Field",
					"name": f"{doctype}-{fieldname}",
					"dt": doctype,
					"fieldname": fieldname,
					"fieldtype": "Data",
					"label": fieldname,
				}
			).db_insert()
		frappe.get_doc(
			{
				"doctype": "CRM Form Script",
				"name": patch.SCRIPT,
				"dt": "CRM Deal",
				"view": "Form",
				"script": "class CRMDeal {}",
				"enabled": 1,
			}
		).insert(ignore_permissions=True)
		frappe.db.sql(
			"insert into `tabSingles` (doctype, field, value) values (%s, 'enabled', '1')",
			IMPOSTAZIONI,
		)
		set_encrypted_password(IMPOSTAZIONI, IMPOSTAZIONI, "segreto-del-sito-remoto", "api_secret")

	def assert_niente(self):
		for doctype, fieldname in patch.CAMPI:
			self.assertFalse(
				frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname}), fieldname
			)
		self.assertFalse(frappe.db.exists("CRM Form Script", patch.SCRIPT))
		self.assertFalse(frappe.db.count("Singles", {"doctype": IMPOSTAZIONI}))
		self.assertFalse(frappe.db.sql("select count(*) from `__Auth` where doctype=%s", IMPOSTAZIONI)[0][0])
		self.assertFalse(frappe.db.exists("DocType", IMPOSTAZIONI))
		self.assertFalse(frappe.db.exists("DocType", patch.PROBLEMI))

	def test_the_patch_takes_away_what_the_integration_left(self):
		self.semina()
		patch.execute()
		self.assert_niente()

	def test_a_second_run_finds_nothing(self):
		self.semina()
		patch.execute()
		patch.execute()
		self.assert_niente()

	def test_no_hook_reaches_erpnext(self):
		self.assertNotIn("Quotation", frappe.get_hooks("doctype_js"))
		self.assertNotIn("Sales Order", frappe.get_hooks("doctype_js"))
		self.assertNotIn(IMPOSTAZIONI, frappe.get_hooks("has_permission"))
		eventi = frappe.get_hooks("doc_events")
		for doctype in ("Sales Order", "Item", "User Permission", "DocShare"):
			self.assertNotIn(doctype, eventi)
		self.assertNotIn("erpnext", repr(eventi).lower())

	def test_no_capability_names_it(self):
		self.assertNotIn("tecnico.erpnext", livelli.capacita_registrate())
