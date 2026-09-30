# Copyright (c) 2026, NPM2 Solutions Srl and Contributors
# See license.txt

"""Quick filters are the team's: who may change them, and on which lists."""

import json

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.doc import update_quick_filters

MANAGER = "quick.filters.manager@example.com"
SALES_USER = "quick.filters.user@example.com"


def make_user(email: str, role: str):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"send_welcome_email": 0,
				"roles": [{"role": role}],
			}
		).insert(ignore_permissions=True)


def in_standard_filter(doctype: str, fieldname: str):
	return frappe.db.get_value(
		"Property Setter",
		{"doc_type": doctype, "field_name": fieldname, "property": "in_standard_filter"},
		"value",
	)


def stored_quick_filters(doctype: str):
	value = frappe.db.get_value("CRM Global Settings", {"dt": doctype, "type": "Quick Filters"}, "json")
	return json.loads(value) if value else None


class TestQuickFilters(IntegrationTestCase):
	def setUp(self):
		make_user(MANAGER, "Sales Manager")
		make_user(SALES_USER, "Sales User")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def change(self, doctype: str, new: list, old: list):
		update_quick_filters(json.dumps(new), json.dumps(old), doctype)

	def test_a_manager_changes_the_quick_filters_of_a_list(self):
		frappe.set_user(MANAGER)
		self.change("CRM Lead", ["lead_name", "territory"], ["lead_name", "industry"])
		frappe.set_user("Administrator")

		self.assertEqual(stored_quick_filters("CRM Lead"), ["lead_name", "territory"])
		self.assertEqual(str(in_standard_filter("CRM Lead", "territory")), "1")
		self.assertEqual(str(in_standard_filter("CRM Lead", "industry")), "0")

	def test_a_manager_can_set_them_on_a_list_that_never_had_any(self):
		# notes are not seeded at install: the first change creates the settings row
		frappe.set_user(MANAGER)
		self.change("FCRM Note", ["title"], [])
		frappe.set_user("Administrator")
		self.assertEqual(stored_quick_filters("FCRM Note"), ["title"])

	def test_a_sales_user_cannot_change_them(self):
		before = (stored_quick_filters("CRM Lead"), in_standard_filter("CRM Lead", "territory"))

		frappe.set_user(SALES_USER)
		with self.assertRaises(frappe.PermissionError):
			self.change("CRM Lead", ["territory"], [])
		frappe.set_user("Administrator")

		after = (stored_quick_filters("CRM Lead"), in_standard_filter("CRM Lead", "territory"))
		self.assertEqual(before, after)

	def test_they_reach_only_the_lists_that_have_quick_filters(self):
		"""The endpoint wrote a Property Setter on whatever doctype it was handed."""
		for doctype in ("User", "DocType", "Role", "CRM Global Settings"):
			written = {"doc_type": doctype, "property": "in_standard_filter"}
			before = frappe.db.count("Property Setter", written)

			frappe.set_user(MANAGER)
			with self.assertRaises(frappe.PermissionError):
				self.change(doctype, ["enabled"], [])
			frappe.set_user("Administrator")

			self.assertEqual(frappe.db.count("Property Setter", written), before, doctype)
			self.assertIsNone(stored_quick_filters(doctype), doctype)

	def test_the_stored_quick_filters_are_not_writable_by_a_sales_user(self):
		"""Otherwise the endpoint's check is one REST call away from not mattering."""
		self.assertTrue(frappe.has_permission("CRM Global Settings", "read", user=SALES_USER))
		self.assertFalse(frappe.has_permission("CRM Global Settings", "write", user=SALES_USER))
		self.assertFalse(frappe.has_permission("CRM Global Settings", "create", user=SALES_USER))
		self.assertTrue(frappe.has_permission("CRM Global Settings", "write", user=MANAGER))
