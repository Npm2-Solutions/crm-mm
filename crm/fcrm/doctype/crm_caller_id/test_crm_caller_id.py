# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


class TestCRMCallerID(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def make(self, number: str, **values):
		return frappe.get_doc({"doctype": "CRM Caller ID", "phone_number": number, **values}).insert(
			ignore_permissions=True
		)

	def test_a_number_is_stored_in_one_canonical_form(self):
		doc = self.make("+39 02 1234 5678")
		self.assertEqual(doc.phone_number, "+390212345678")
		self.assertEqual(doc.name, "+390212345678")

	def test_the_type_is_read_from_the_number(self):
		self.assertEqual(self.make("+390212345678").number_type, "Geographic")
		self.assertEqual(self.make("+393331234567").number_type, "Mobile")

	def test_the_country_is_read_from_the_number(self):
		self.assertEqual(self.make("+390212345678").country, "IT")

	def test_an_empty_number_is_refused(self):
		with self.assertRaises(frappe.ValidationError):
			self.make("   ")

	def test_something_that_is_not_a_number_is_refused(self):
		with self.assertRaises(frappe.ValidationError):
			self.make("chiamare la reception")

	def test_the_same_number_cannot_be_listed_twice(self):
		self.make("+390212345678")
		with self.assertRaises(Exception):
			self.make("02 1234 5678")
