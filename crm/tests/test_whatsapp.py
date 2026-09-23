# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from crm.api.whatsapp import notify_agent, validate


class TestWhatsAppHooks(FrappeTestCase):
	def tearDown(self):
		frappe.db.rollback()

	# --- validate() ---

	def test_validate_sets_reference_when_contact_found(self):
		"""validate() links the doc when a matching Contact/Lead is found"""
		doc = MagicMock()
		doc.type = "Incoming"
		doc.get.return_value = "+15551234567"

		with patch(
			"crm.api.whatsapp.get_contact_lead_or_deal_from_number",
			return_value=("LEAD-0001", "CRM Lead"),
		):
			validate(doc, None)

		self.assertEqual(doc.reference_doctype, "CRM Lead")
		self.assertEqual(doc.reference_name, "LEAD-0001")

	def test_validate_adopts_unknown_number_on_incoming(self):
		"""An incoming message from a stranger gets a lead, or it lands nowhere"""
		doc = MagicMock()
		doc.type = "Incoming"
		doc.get.return_value = "+15559999999"

		with (
			patch(
				"crm.api.whatsapp.get_contact_lead_or_deal_from_number",
				return_value=(None, None),
			),
			patch(
				"crm.api.whatsapp.adopt_unknown_number",
				return_value=("LEAD-0002", "CRM Lead"),
			) as adopt,
		):
			validate(doc, None)

		adopt.assert_called_once()
		self.assertEqual(doc.reference_doctype, "CRM Lead")
		self.assertEqual(doc.reference_name, "LEAD-0002")

	def test_validate_does_not_adopt_on_outgoing(self):
		"""Writing to an unknown number must not invent a lead for it"""
		doc = MagicMock()
		doc.type = "Outgoing"
		doc.get.return_value = "+15559999999"
		doc.reference_doctype = None
		doc.reference_name = None

		with (
			patch(
				"crm.api.whatsapp.get_contact_lead_or_deal_from_number",
				return_value=(None, None),
			),
			patch("crm.api.whatsapp.adopt_unknown_number") as adopt,
		):
			validate(doc, None)

		adopt.assert_not_called()
		self.assertIsNone(doc.reference_doctype)
		self.assertIsNone(doc.reference_name)

	def test_validate_logs_error_on_exception(self):
		"""validate() catches lookup exceptions and logs them instead of raising"""
		doc = MagicMock()
		doc.type = "Incoming"
		doc.get.return_value = "invalid-number"

		with (
			patch(
				"crm.api.whatsapp.get_contact_lead_or_deal_from_number",
				side_effect=Exception("parse error"),
			),
			patch("frappe.log_error") as mock_log,
		):
			validate(doc, None)  # must not raise

		mock_log.assert_called_once()

	# --- notify_agent() ---

	def test_notify_agent_returns_early_when_no_reference(self):
		"""notify_agent() skips notification when reference_doctype and reference_name are absent"""
		doc = MagicMock()
		doc.type = "Incoming"
		doc.reference_doctype = None
		doc.reference_name = None

		with patch("crm.api.whatsapp.get_assigned_users") as mock_users:
			notify_agent(doc)  # must not raise

		mock_users.assert_not_called()

	def test_notify_agent_returns_early_when_reference_doctype_missing(self):
		"""notify_agent() skips notification when only reference_doctype is absent"""
		doc = MagicMock()
		doc.type = "Incoming"
		doc.reference_doctype = ""
		doc.reference_name = "LEAD-0001"

		with patch("crm.api.whatsapp.get_assigned_users") as mock_users:
			notify_agent(doc)

		mock_users.assert_not_called()


class TestOutgoingMediaMetaCanRead(FrappeTestCase):
	"""Meta does not look inside the file. It reads the Content-Type header the
	web server sends, and refuses anything that does not match the kind of
	message it was asked to send.

	A voice note recorded in the browser is saved as `voice-….mp4`, and nginx
	serves every `.mp4` as `video/mp4`. Meta accepted the send — it answered with
	a message id — then fetched `video/mp4` for an `audio` message and marked it
	failed, in a status webhook that arrived long after the send had returned
	successfully. Nothing on screen ever said why.
	"""

	def tearDown(self):
		frappe.db.rollback()

	def test_an_mp4_voice_note_is_offered_as_audio(self):
		from crm.api.whatsapp import media_content_type

		self.assertEqual(media_content_type("/files/voice-1.mp4", "audio"), "audio/mp4")
		# and the same name, as a video message, is still a video
		self.assertEqual(media_content_type("/files/clip.mp4", "video"), "video/mp4")

	def test_the_audio_types_are_the_ones_meta_lists(self):
		from crm.api.whatsapp import media_content_type

		self.assertEqual(media_content_type("/files/a.ogg", "audio"), "audio/ogg")
		self.assertEqual(media_content_type("/files/a.mp3", "audio"), "audio/mpeg")
		self.assertEqual(media_content_type("/files/a.m4a", "audio"), "audio/mp4")

	def test_an_unknown_extension_still_gets_a_type_of_the_right_kind(self):
		"""Better a type Meta accepts for that kind than one it refuses outright."""
		from crm.api.whatsapp import media_content_type

		self.assertTrue(media_content_type("/files/mystery", "audio").startswith("audio/"))
		self.assertTrue(media_content_type("/files/mystery", "image").startswith("image/"))

	def test_a_document_keeps_whatever_it_is(self):
		from crm.api.whatsapp import media_content_type

		self.assertEqual(media_content_type("/files/offer.pdf", "document"), "application/pdf")

	def test_the_link_is_signed_and_the_signature_is_checked(self):
		from crm.api.whatsapp import media, media_signature, media_url

		url = media_url("/files/voice-1.mp4", "audio")
		self.assertIn("crm.api.whatsapp.media", url)
		self.assertIn(media_signature("/files/voice-1.mp4", "audio"), url)
		# the same file, claimed as another kind, is a different signature
		self.assertNotEqual(
			media_signature("/files/voice-1.mp4", "audio"),
			media_signature("/files/voice-1.mp4", "video"),
		)
		with self.assertRaises(frappe.PermissionError):
			media(file="/files/voice-1.mp4", kind="audio", s="not-the-signature")

	def test_it_will_not_hand_out_a_private_file(self):
		"""It serves what was already being served from /files, and nothing more."""
		from crm.api.whatsapp import media, media_signature

		private = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "segreto.ogg",
				"is_private": 1,
				"content": "not yours",
			}
		).insert(ignore_permissions=True)
		with self.assertRaises(frappe.DoesNotExistError):
			media(
				file=private.file_url,
				kind="audio",
				s=media_signature(private.file_url, "audio"),
			)
