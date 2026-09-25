# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""Connecting Google Calendar: the record behind the popup, on a site's first day too."""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.integrations.google import api as google_api
from crm.integrations.google import oauth


class TestGoogleConnection(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		# a site nobody has set Google up on: the credentials live in the bench config
		settings = frappe.get_doc("Google Settings")
		settings.enable = 0
		settings.client_id = ""
		settings.client_secret = ""
		settings.save(ignore_permissions=True)
		self._conf = patch.dict(
			frappe.conf,
			{"google_client_id": "bench.apps.googleusercontent.com", "google_client_secret": "bench-secret"},
		)
		self._conf.start()

	def tearDown(self):
		self._conf.stop()
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def make_user(self, email, first_name):
		if not frappe.db.exists("User", email):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": first_name,
					"send_welcome_email": 0,
					"roles": [{"role": "Sales User"}],
				}
			).insert(ignore_permissions=True)
		return email

	def test_the_first_connection_of_a_site_opens_the_google_window(self):
		"""The framework refuses a `Google Calendar` while `Google Settings` is off: the
		bench credentials have to be there before the record, or the button fails."""
		user = self.make_user("giulia.first@example.com", "Giulia")
		frappe.set_user(user)
		login = oauth.get_login_url()
		self.assertIn("accounts.google.com", login["login_url"])
		self.assertEqual(frappe.db.get_value("Google Calendar", login["calendar"], "user"), user)
		settings = frappe.get_doc("Google Settings")
		self.assertEqual((settings.enable, settings.client_id), (1, "bench.apps.googleusercontent.com"))

	def test_two_people_with_the_same_name_each_get_their_record(self):
		first = self.make_user("giulia.one@example.com", "Giulia Same")
		second = self.make_user("giulia.two@example.com", "Giulia Same")
		names = set()
		for user in (first, second):
			frappe.set_user(user)
			names.add(oauth.ensure_calendar_record())
		self.assertEqual(len(names), 2)

	def test_disconnecting_switches_the_record_off(self):
		user = self.make_user("giulia.off@example.com", "Giulia Off")
		frappe.set_user(user)
		name = oauth.ensure_calendar_record()
		oauth.store_tokens(name, {"refresh_token": "refresh-giulia"})
		self.assertTrue(google_api.get_status()["connected"])
		self.assertEqual(frappe.db.get_value("Google Calendar", name, "enable"), 1)

		status = google_api.disconnect()
		self.assertFalse(status["connected"])
		self.assertEqual(frappe.db.get_value("Google Calendar", name, "enable"), 0)
