# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""The whitelisted methods of the settings documents.

Frappe runs a document's whitelisted method for anyone who can read the document:
`run_doc_method` (/api/method/run_doc_method, and frappe-ui's document resources)
loads it with a read check and nothing more. A Sales User can read FCRM Settings
and ERPNext CRM Settings, so the methods that change something check the role
themselves. The calls here go through run_doc_method, as a browser's would.
"""

import json
from unittest.mock import MagicMock, patch

import frappe
from frappe.handler import run_doc_method
from frappe.tests import IntegrationTestCase
from frappe.utils import set_request

from crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings import get_crm_form_script

MANAGER = "settings.methods.manager@example.com"
SALES_USER = "settings.methods.user@example.com"

FCRM_SETTINGS = "crm.fcrm.doctype.fcrm_settings.fcrm_settings"
ERPNEXT_SETTINGS = "crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings"
QUOTATION_SCRIPT = "Create Quotation from CRM Deal"


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

	def assert_refused(self, method: str, **kwargs):
		# the precondition that made this reachable at all
		self.assertTrue(frappe.has_permission(self.settings_doctype, "read", user=SALES_USER))
		with self.assertRaises(frappe.PermissionError):
			self.call(SALES_USER, method, **kwargs)


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


class TestERPNextSettingsMethods(SettingsMethodTestCase):
	settings_doctype = "ERPNext CRM Settings"

	def stale_quotation_script(self):
		if not frappe.db.exists("CRM Form Script", QUOTATION_SCRIPT):
			frappe.get_doc(
				{
					"doctype": "CRM Form Script",
					"name": QUOTATION_SCRIPT,
					"dt": "CRM Deal",
					"view": "Form",
					"script": "class CRMDeal {}",
					"enabled": 1,
					"is_standard": 1,
				}
			).insert(ignore_permissions=True)
		frappe.db.set_value("CRM Form Script", QUOTATION_SCRIPT, "script", "class CRMDeal {}")

	def quotation_script(self) -> str:
		return frappe.db.get_value("CRM Form Script", QUOTATION_SCRIPT, "script")

	def connect_remote_site(self):
		frappe.db.set_single_value(
			self.settings_doctype,
			{
				"erpnext_site_url": "https://erp.example.com",
				"api_key": "remote-api-key",
				"api_secret": "remote-api-secret",
			},
		)

	def test_a_sales_user_cannot_reset_the_quotation_script(self):
		self.stale_quotation_script()
		self.assert_refused("reset_erpnext_form_script")
		self.assertEqual(self.quotation_script(), "class CRMDeal {}")

	def test_a_sales_user_cannot_call_the_remote_site(self):
		self.connect_remote_site()
		with patch(f"{ERPNEXT_SETTINGS}.get_erpnext_site_client") as client:
			self.assert_refused("get_external_companies")
		client.assert_not_called()

	def test_a_sales_user_cannot_start_a_product_sync(self):
		frappe.db.set_single_value(self.settings_doctype, {"enabled": 1, "is_erpnext_in_different_site": 0})
		with patch("crm.fcrm.doctype.crm_product.reconcile_job.enqueue_reconciliation") as enqueue:
			self.assert_refused("run_product_sync")
		enqueue.assert_not_called()

	def test_a_manager_resets_the_quotation_script(self):
		self.stale_quotation_script()
		self.assertTrue(self.call(MANAGER, "reset_erpnext_form_script"))
		self.assertEqual(self.quotation_script(), get_crm_form_script())

	def test_a_manager_lists_the_remote_companies(self):
		self.connect_remote_site()
		remote = MagicMock()
		remote.get_list.return_value = [{"company_name": "Rossi S.r.l."}]
		with patch(f"{ERPNEXT_SETTINGS}.get_erpnext_site_client", return_value=remote):
			companies = self.call(MANAGER, "get_external_companies")
		self.assertEqual(companies, [{"company_name": "Rossi S.r.l."}])

	def test_a_manager_starts_a_product_sync(self):
		frappe.db.set_single_value(self.settings_doctype, {"enabled": 1, "is_erpnext_in_different_site": 0})
		with patch("crm.fcrm.doctype.crm_product.reconcile_job.enqueue_reconciliation") as enqueue:
			self.assertTrue(self.call(MANAGER, "run_product_sync"))
		enqueue.assert_called_once_with()

	def test_whether_erpnext_is_installed_stays_open_to_readers(self):
		"""A boolean about the site, left readable on purpose: the settings page asks it."""
		self.call(SALES_USER, "is_erpnext_installed")
		self.assertIn(frappe.response.get("message"), (True, False))
