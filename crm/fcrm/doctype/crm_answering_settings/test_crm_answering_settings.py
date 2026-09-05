# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


class TestCRMAnsweringSettings(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_audio_source_requires_a_file(self):
		settings = frappe.get_single("CRM Answering Settings")
		settings.enabled = 1
		settings.callback_hours = 3
		settings.greeting_source = "Audio File"
		settings.greeting_audio = ""
		with self.assertRaises(frappe.ValidationError):
			settings.save()

	def test_enabled_requires_a_callback_window(self):
		settings = frappe.get_single("CRM Answering Settings")
		settings.enabled = 1
		settings.greeting_source = "Text to Speech"
		settings.callback_hours = 0
		with self.assertRaises(frappe.ValidationError):
			settings.save()

	def test_negative_values_are_clamped(self):
		settings = frappe.get_single("CRM Answering Settings")
		settings.enabled = 0
		settings.callback_hours = 3
		settings.retry_after_hours = -5
		settings.save()
		self.assertEqual(settings.retry_after_hours, 0)
