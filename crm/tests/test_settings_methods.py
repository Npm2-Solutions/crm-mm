# Copyright (c) 2026, NPM2 Solutions Srl and Contributors
# See license.txt

"""The whitelisted methods of the settings documents.

Frappe runs a document's whitelisted method for anyone who can read the document:
`run_doc_method` (/api/method/run_doc_method, and frappe-ui's document resources)
loads it with a read check and nothing more. A Sales User can read FCRM Settings,
so the methods that change something ask for the capability themselves. The calls
here go through run_doc_method, as a browser's would.
"""

import json
from unittest.mock import patch

import frappe
from frappe.handler import run_doc_method
from frappe.tests import IntegrationTestCase
from frappe.utils import set_request

MANAGER = "settings.methods.manager@example.com"
SALES_USER = "settings.methods.user@example.com"

FCRM_SETTINGS = "crm.fcrm.doctype.fcrm_settings.fcrm_settings"


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


class SettingsMethodTestCase(IntegrationTestCase):
	settings_doctype = None

	def setUp(self):
		make_user(MANAGER, "Sales Manager")
		make_user(SALES_USER, "Sales User")
		# run_doc_method checks the HTTP verb of the request it is serving
		self._request = getattr(frappe.local, "request", None)
		set_request(method="POST", path="/api/method/run_doc_method")

	def tearDown(self):
		frappe.local.request = self._request
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def call(self, user: str, method: str, **kwargs):
		frappe.set_user(user)
		frappe.local.response = frappe._dict({"docs": []})
		run_doc_method(
			method,
			dt=self.settings_doctype,
			dn=self.settings_doctype,
			args=json.dumps(kwargs) if kwargs else None,
		)
		return frappe.response.get("message")

	def assert_refused(self, method: str, user: str = SALES_USER, **kwargs):
		# the precondition that made this reachable at all
		self.assertTrue(frappe.has_permission(self.settings_doctype, "read", user=user))
		with self.assertRaises(frappe.PermissionError):
			self.call(user, method, **kwargs)


class TestFCRMSettingsMethods(SettingsMethodTestCase):
	settings_doctype = "FCRM Settings"

	def test_a_sales_user_cannot_restore_the_defaults(self):
		with patch(f"{FCRM_SETTINGS}.after_install") as after_install:
			self.assert_refused("restore_defaults", force=True)
		after_install.assert_not_called()

	def test_a_sales_user_cannot_restore_the_demo_data(self):
		with patch(f"{FCRM_SETTINGS}.create_demo_data") as create_demo_data:
			self.assert_refused("restore_demo_data")
		create_demo_data.assert_not_called()

	def test_a_manager_restores_the_defaults(self):
		with patch(f"{FCRM_SETTINGS}.after_install") as after_install:
			self.call(MANAGER, "restore_defaults", force=True)
		after_install.assert_called_once_with(True)

	def test_a_manager_restores_the_demo_data(self):
		with patch(f"{FCRM_SETTINGS}.create_demo_data") as create_demo_data:
			self.call(MANAGER, "restore_demo_data")
		create_demo_data.assert_called_once_with()
