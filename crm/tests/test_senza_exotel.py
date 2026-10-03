# Copyright (c) 2026, NPM2 Solutions Srl and Contributors
# See license.txt

"""DottorCloud no longer offers Exotel (03/10/2026): the patch takes away what
it left, and nothing in the app names it any more."""

import frappe
from frappe.tests import IntegrationTestCase

from crm.patches.v1_0 import dottorcloud_does_not_use_exotel as patch
from crm.telephony import providers


class SenzaExotel(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_a_default_and_a_call_that_named_it_name_nothing(self):
		utente = "Administrator"
		if not frappe.db.exists("CRM Telephony Agent", utente):
			frappe.get_doc({"doctype": "CRM Telephony Agent", "user": utente}).insert(ignore_permissions=True)
		# as a site before this release has them: the option is gone from the form
		frappe.db.set_value("CRM Telephony Agent", utente, "default_medium", "Exotel")
		chiamata = frappe.get_doc(
			{
				"doctype": "CRM Call Log",
				"id": frappe.generate_hash(length=12),
				"type": "Incoming",
				"status": "Completed",
				"from": "+390212345678",
				"to": "+390298765432",
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value("CRM Call Log", chiamata.name, "telephony_medium", "Exotel")

		patch.execute()
		patch.execute()

		self.assertEqual(frappe.db.get_value("CRM Telephony Agent", utente, "default_medium"), "")
		self.assertEqual(frappe.db.get_value("CRM Call Log", chiamata.name, "telephony_medium"), "")
		self.assertTrue(frappe.db.exists("CRM Call Log", chiamata.name))

	def test_its_settings_are_gone(self):
		patch.execute()
		self.assertFalse(frappe.db.exists("DocType", "CRM Exotel Settings"))
		self.assertFalse(
			frappe.db.sql("select 1 from `tabSingles` where doctype = %s", "CRM Exotel Settings")
		)
		self.assertNotIn("exotel", providers.REGISTRY)
