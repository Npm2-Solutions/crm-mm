# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


class TestCRMTranscriptionSettings(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def settings(self, **values):
		doc = frappe.get_single("CRM Transcription Settings")
		doc.update({"enabled": 1, "base_url": "https://api.example.com/v1", "model": "whisper-1", **values})
		return doc

	def test_enabled_requires_an_endpoint(self):
		with self.assertRaises(frappe.ValidationError):
			self.settings(base_url="").save()

	def test_enabled_requires_a_model(self):
		with self.assertRaises(frappe.ValidationError):
			self.settings(model="").save()

	def test_remote_endpoints_must_be_encrypted(self):
		with self.assertRaises(frappe.ValidationError):
			self.settings(base_url="http://stt.example.com/v1").save()

	def test_a_local_endpoint_may_be_plain_http(self):
		doc = self.settings(base_url="http://localhost:8000/v1")
		doc.save()
		self.assertEqual(doc.base_url, "http://localhost:8000/v1")

	def test_a_disabled_service_needs_no_endpoint(self):
		doc = self.settings(enabled=0, base_url="", model="")
		doc.save()
		self.assertFalse(doc.enabled)

	def test_limits_are_clamped_to_something_usable(self):
		doc = self.settings(max_recording_mb=0, request_timeout=1, transcript_retention_days=-5)
		doc.save()
		self.assertEqual(doc.max_recording_mb, 1)
		self.assertEqual(doc.request_timeout, 10)
		self.assertEqual(doc.transcript_retention_days, 0)
