# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A person's gender and title have something to choose from, wizard or not."""

import frappe
from frappe.tests import IntegrationTestCase

from crm.install import TITOLI, add_genders_and_titles


class GeneriETitoli(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_ci_sono_anche_senza_la_procedura_guidata(self):
		frappe.db.delete("Gender", {"name": ("in", ["Male", "Female"])})
		add_genders_and_titles()
		self.assertTrue(frappe.db.exists("Gender", "Female"))
		self.assertTrue(frappe.db.exists("Gender", "Prefer not to say"))
		for titolo in TITOLI:
			self.assertTrue(frappe.db.exists("Salutation", titolo))

	def test_due_volte_non_raddoppia(self):
		add_genders_and_titles()
		add_genders_and_titles()
		self.assertEqual(frappe.db.count("Gender", {"name": "Male"}), 1)
		self.assertEqual(frappe.db.count("Salutation", {"name": "Dr"}), 1)
