# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.doc import get_data


class TestListColumns(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def keys(self, doctype):
		data = get_data(doctype=doctype, filters={}, order_by="modified desc", view={"view_type": "list"})
		return [c.get("key") for c in data["columns"]]

	def test_the_contact_list_has_its_name_column(self):
		# Frappe core hides Contact.full_name; the CRM declares it as the first
		# column, and a list of contacts without names is a list of emails
		self.assertTrue(frappe.get_meta("Contact").get_field("full_name").hidden)
		self.assertIn("full_name", self.keys("Contact"))

	def test_a_column_nobody_declared_still_goes_when_its_field_is_hidden(self):
		# `image` is hidden in core and not one of the CRM's contact columns: a
		# view that names it keeps losing it, as before
		self.assertTrue(frappe.get_meta("Contact").get_field("image").hidden)
		data = get_data(
			doctype="Contact",
			filters={},
			order_by="modified desc",
			columns=[{"label": "Name", "key": "full_name"}, {"label": "Image", "key": "image"}],
			rows=["name"],
			view={"view_type": "list"},
		)
		keys = [c.get("key") for c in data["columns"]]
		self.assertIn("full_name", keys)
		self.assertNotIn("image", keys)
