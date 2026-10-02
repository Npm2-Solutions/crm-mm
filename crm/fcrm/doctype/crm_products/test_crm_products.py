# Modifications copyright (c) 2026, NPM2 Solutions Srl

import unittest

import frappe
from frappe.tests import IntegrationTestCase

from crm.fcrm.doctype.crm_products.crm_products import get_product_rate_details


class TestGetProductRateDetails(IntegrationTestCase):
	def test_a_line_takes_the_products_own_price(self):
		product = frappe.get_doc(
			{"doctype": "CRM Product", "product_code": "LINE-PRICE", "standard_rate": 90}
		).insert(ignore_permissions=True)

		out = get_product_rate_details(product.name)

		self.assertEqual(out, {"product_name": "LINE-PRICE", "rate": 90})

	def test_an_unknown_product_has_no_price(self):
		self.assertEqual(get_product_rate_details("NOT-A-PRODUCT"), {"product_name": None, "rate": None})


class TestProductDetailsScript(unittest.TestCase):
	def test_product_change_replaces_existing_rate(self):
		from crm.fcrm.doctype.crm_products.crm_products import get_product_details_script

		script = get_product_details_script("CRM Deal")

		self.assertIn("row.rate = a.rate ?? 0", script)
		self.assertNotIn("!row.rate", script)
		self.assertIn("row.product_code !== productCode", script)
