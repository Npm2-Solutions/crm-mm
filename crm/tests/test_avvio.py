# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What the page says at the start, so that the first page waits on no call in a
row: whether the session opens DottorCloud, whether the first-run questions are
to be asked (crm.www.crm)."""

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from crm.www.crm import ask_persona, get_boot, session_opens_the_crm


class TestAvvio(FrappeTestCase):
	def setUp(self):
		from crm.registrazione import carica

		carica()
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_the_page_says_the_session_opens_dottorcloud(self):
		boot = get_boot()
		self.assertIs(boot.crm_user, True)
		self.assertIn("ask_persona", boot)

	def test_a_guest_does_not(self):
		frappe.set_user("Guest")
		self.assertFalse(session_opens_the_crm())

	def test_the_questions_only_where_telemetry_reads_them(self):
		with patch("frappe.utils.telemetry.pulse.client.is_enabled", return_value=False):
			self.assertFalse(ask_persona())
		with (
			patch("frappe.utils.telemetry.pulse.client.is_enabled", return_value=True),
			patch("frappe.db.get_single_value", return_value=0),
		):
			self.assertTrue(ask_persona())
		# answered once: not asked again
		with (
			patch("frappe.utils.telemetry.pulse.client.is_enabled", return_value=True),
			patch("frappe.db.get_single_value", return_value=1),
		):
			self.assertFalse(ask_persona())
