# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""The ERPNext endpoints that take a deal name answer only about deals the caller can read.

A Sales User sees their own and assigned deals; naming someone else's deal used to be
enough to read its products and prices, its customer, or to send its contacts to
ERPNext as a Prospect. Nothing of ERPNext is installed on a test bench: the remote
site is a stand-in, and so is the item code the integration keeps on CRM Product.
"""

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.fcrm.doctype.erpnext_crm_settings import erpnext_crm_settings as E

OWNER = "erpnext.deal.owner@example.com"
STRANGER = "erpnext.deal.stranger@example.com"


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


class TestERPNextDealAccess(IntegrationTestCase):
	def setUp(self):
		make_user(OWNER, "Sales User")
		make_user(STRANGER, "Sales User")
		self.organization = frappe.get_doc(
			{"doctype": "CRM Organization", "organization_name": "Rossi Arredamenti"}
		).insert(ignore_permissions=True)
		if not frappe.db.exists("CRM Product", "SEDIA-01"):
			product = frappe.get_doc(
				{"doctype": "CRM Product", "product_code": "SEDIA-01", "product_name": "Sedia"}
			)
			product.flags.ignore_erpnext_sync = True
			product.insert(ignore_permissions=True)
		self.deal = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"deal_owner": OWNER,
				"organization": self.organization.name,
				"products": [
					{
						"product_code": "SEDIA-01",
						"product_name": "Sedia",
						"qty": 2,
						"rate": 120,
						"discount_percentage": 10,
					}
				],
			}
		).insert(ignore_permissions=True)

		frappe.db.set_single_value(
			"ERPNext CRM Settings",
			{
				"enabled": 1,
				"is_erpnext_in_different_site": 1,
				"erpnext_site_url": "https://erp.example.com",
				"erpnext_company": "Rossi",
			},
		)
		self.remote = MagicMock()
		self.remote.get_list.return_value = [{"name": "CUST-0001"}]
		self.remote.post_api.return_value = "PROSPECT-0001"
		self._client = patch.object(E, "get_erpnext_site_client", return_value=self.remote)
		self._client.start()

	def tearDown(self):
		self._client.stop()
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def prefill(self, user: str):
		real_get_value = frappe.db.get_value

		def item_code(doctype, *args, **kwargs):
			# the custom field the integration adds to CRM Product
			if doctype == "CRM Product" and args[1:2] == ("erpnext_item_code",):
				return "ITEM-SEDIA"
			return real_get_value(doctype, *args, **kwargs)

		frappe.set_user(user)
		with patch.object(frappe.db, "get_value", side_effect=item_code):
			return E.prefill_quotation_items(self.deal.name)

	def test_the_owner_gets_the_items_to_quote(self):
		self.assertEqual(
			self.prefill(OWNER),
			[{"item_code": "ITEM-SEDIA", "qty": 2, "price_list_rate": 120, "discount_percentage": 10}],
		)

	def test_someone_elses_deal_gives_no_items(self):
		with self.assertRaises(frappe.PermissionError):
			self.prefill(STRANGER)

	def test_the_owner_gets_the_customer_link(self):
		frappe.set_user(OWNER)
		self.assertEqual(
			E.get_customer_link(self.deal.name), "https://erp.example.com/app/customer/CUST-0001"
		)

	def test_someone_elses_deal_gives_no_customer_link(self):
		frappe.set_user(STRANGER)
		with self.assertRaises(frappe.PermissionError):
			E.get_customer_link(self.deal.name)
		self.remote.get_list.assert_not_called()

	def test_the_owner_quotes_the_deal(self):
		frappe.set_user(OWNER)
		url = E.get_quotation_url(self.deal.name, self.organization.name)
		self.assertTrue(url.startswith("https://erp.example.com/app/quotation/new?"), url)
		self.assertIn("party_name=PROSPECT-0001", url)
		self.remote.post_api.assert_called_once()
		self.assertEqual(self.remote.post_api.call_args.args[1]["crm_deal"], self.deal.name)

	def test_someone_elses_deal_is_not_sent_to_erpnext(self):
		frappe.set_user(STRANGER)
		with self.assertRaises(frappe.PermissionError):
			E.get_quotation_url(self.deal.name, self.organization.name)
		# no Prospect with the deal's contacts and address was created
		self.remote.post_api.assert_not_called()


class TestCustomerForQuotation(IntegrationTestCase):
	"""Called from ERPNext's Sales Order form: whoever calls it must be able to read the
	quotation and make a Sales Order. ERPNext is not on a test bench, so its doctypes'
	answers are stood in for; the rule under test is what the code does with them."""

	def setUp(self):
		self._patches = [
			patch.object(E, "_is_erpnext_installed", return_value=True),
			patch.object(E, "check_customer_for_deal", return_value="CUST-0001"),
		]
		self.check_customer_for_deal = self._patches[1].start()
		self._patches[0].start()

	def tearDown(self):
		for p in self._patches:
			p.stop()

	def call(self, can_read_quotation: bool, can_make_sales_order: bool):
		real_has_permission = frappe.has_permission
		real_get_value = frappe.db.get_value

		def has_permission(doctype=None, ptype="read", doc=None, *args, **kwargs):
			if doctype == "Quotation":
				return can_read_quotation
			if doctype == "Sales Order":
				return can_make_sales_order and ptype == "create"
			return real_has_permission(doctype, ptype, doc, *args, **kwargs)

		def get_value(doctype, *args, **kwargs):
			if doctype == "Quotation":
				return "CRM-DEAL-2026-00001"
			return real_get_value(doctype, *args, **kwargs)

		with (
			patch.object(frappe, "has_permission", side_effect=has_permission),
			patch.object(frappe.db, "get_value", side_effect=get_value),
		):
			return E.check_customer_for_quotation("SAL-QTN-2026-00001")

	def test_whoever_makes_the_sales_order_gets_the_customer(self):
		self.assertEqual(self.call(True, True), "CUST-0001")
		self.check_customer_for_deal.assert_called_once_with("CRM-DEAL-2026-00001")

	def test_without_the_quotation_nothing_is_created(self):
		with self.assertRaises(frappe.PermissionError):
			self.call(False, True)
		self.check_customer_for_deal.assert_not_called()

	def test_without_sales_orders_nothing_is_created(self):
		with self.assertRaises(frappe.PermissionError):
			self.call(True, False)
		self.check_customer_for_deal.assert_not_called()

	def test_without_erpnext_on_this_site_there_is_nothing_to_do(self):
		with patch.object(E, "_is_erpnext_installed", return_value=False):
			self.assertIsNone(E.check_customer_for_quotation("SAL-QTN-2026-00001"))
		self.check_customer_for_deal.assert_not_called()
