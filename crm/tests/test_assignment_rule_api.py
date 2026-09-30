# Copyright (c) 2026, NPM2 Solutions Srl and Contributors
# See license.txt

"""The assignment rules list reads past permissions, so it checks who is asking."""

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.assignment_rule import get_assignment_rules_list

MANAGER = "assignment.rules.manager@example.com"
SALES_USER = "assignment.rules.user@example.com"
RULE = "Leads to the Milan team"


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


class TestAssignmentRulesList(IntegrationTestCase):
	def setUp(self):
		make_user(MANAGER, "Sales Manager")
		make_user(SALES_USER, "Sales User")
		if not frappe.db.exists("Assignment Rule", RULE):
			frappe.get_doc(
				{
					"doctype": "Assignment Rule",
					"name": RULE,
					"document_type": "CRM Lead",
					"description": "Milan leads",
					"assign_condition": "status == 'New'",
					"rule": "Round Robin",
					"priority": 1,
					"users": [{"user": MANAGER}],
					"assignment_days": [{"day": "Monday"}],
				}
			).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_a_manager_sees_the_rules(self):
		frappe.set_user(MANAGER)
		rules = {rule["name"]: rule for rule in get_assignment_rules_list()}
		self.assertIn(RULE, rules)
		self.assertEqual(rules[RULE]["description"], "Milan leads")
		self.assertTrue(rules[RULE]["users_exists"])

	def test_a_sales_user_does_not(self):
		frappe.set_user(SALES_USER)
		with self.assertRaises(frappe.PermissionError):
			get_assignment_rules_list()
