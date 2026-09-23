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


class TestOpusInsideMp4IsNotAudioMp4(FrappeTestCase):
	"""`audio/mp4` means **AAC** in an MP4 container.

	Chrome's MediaRecorder, asked for `audio/mp4` with no codec named, records
	**Opus** in an MP4 container — which no messenger accepts. The file plays
	perfectly in the browser that made it, the Content-Type header is right, and
	Meta answers with a message id and then marks the message failed in a status
	webhook nobody sees. Said out loud at send time instead.
	"""

	def test_opus_in_mp4_is_refused_with_a_reason(self):
		from crm.api.whatsapp import audio_codec_problem

		# the boxes an Opus-in-MP4 recording carries
		opus_mp4 = b"\x00\x00\x00\x18ftypisom" + b"\x00" * 400 + b"Opus" + b"\x00" * 40 + b"dOps"
		problem = audio_codec_problem(opus_mp4, "/files/voice-1.mp4")
		self.assertIn("Opus", problem)
		self.assertIn("OGG", problem)

	def test_aac_in_mp4_is_exactly_what_it_should_be(self):
		from crm.api.whatsapp import audio_codec_problem

		aac_mp4 = b"\x00\x00\x00\x18ftypisom" + b"\x00" * 400 + b"mp4a" + b"\x00" * 40 + b"esds"
		self.assertEqual(audio_codec_problem(aac_mp4, "/files/voice-1.m4a"), "")

	def test_an_ogg_recording_is_left_alone(self):
		"""Opus belongs in OGG, and nothing here has an opinion about it."""
		from crm.api.whatsapp import audio_codec_problem

		self.assertEqual(audio_codec_problem(b"OggS" + b"\x00" * 100 + b"OpusHead", "/files/v.ogg"), "")


class TestRetryingAMessageThatFailed(FrappeTestCase):
	"""Meta's status webhook writes `failed`; the doctype's own option is
	`Failed`. The comparison was case-sensitive, so the retry button refused
	exactly the messages it exists for."""

	def tearDown(self):
		frappe.db.rollback()

	def test_lower_case_failed_is_still_failed(self):
		from crm.api.whatsapp import retry_whatsapp_message

		doc = MagicMock()
		doc.type = "Outgoing"
		doc.status = "failed"
		doc.reference_doctype = None
		doc.reference_name = None
		doc.message_id = "wamid.TEST"

		with (
			patch("crm.api.whatsapp.frappe.get_doc", return_value=doc),
			patch("crm.api.whatsapp.validate_access"),
		):
			retry_whatsapp_message("whatever")

		doc.send_outgoing.assert_called_once()

	def test_a_message_that_went_through_is_not_sent_twice(self):
		from crm.api.whatsapp import retry_whatsapp_message

		doc = MagicMock()
		doc.type = "Outgoing"
		doc.status = "sent"
		doc.reference_doctype = None
		doc.reference_name = None

		with (
			patch("crm.api.whatsapp.frappe.get_doc", return_value=doc),
			patch("crm.api.whatsapp.validate_access"),
			self.assertRaises(frappe.ValidationError),
		):
			retry_whatsapp_message("whatever")

		doc.send_outgoing.assert_not_called()


class TestATemplateBelongsToItsNumber(FrappeTestCase):
	"""A template is approved on one WhatsApp Business account and belongs to it.

	Sent from another number Meta refuses it, complaining about a template name
	that does not exist — true from where it is standing, useless to whoever
	pressed Send. The chooser was listing every approved template on the site,
	including the ones left behind by a number no longer in use, and offering
	Send on all of them.
	"""

	def tearDown(self):
		frappe.db.rollback()

	def test_a_template_of_another_account_is_refused_by_name(self):
		from crm.api.whatsapp import send_whatsapp_template

		with (
			patch("crm.api.whatsapp.frappe.db.get_value", return_value="Vecchio"),
			patch("crm.api.whatsapp.sending_account_name", return_value="Nuovo"),
			patch("crm.api.whatsapp.validate_access"),
		):
			with self.assertRaises(frappe.ValidationError) as caught:
				send_whatsapp_template("CRM Lead", "LEAD-0001", "promo-it", "+393330000000")

		message = str(caught.exception)
		# both numbers named, so the reader knows what to do about it
		self.assertIn("Vecchio", message)
		self.assertIn("Nuovo", message)
		self.assertIn("promo-it", message)

	def test_a_template_with_no_account_recorded_is_left_alone(self):
		"""Nobody wrote down where it came from; it goes out from whichever number
		is sending, exactly as it did before."""
		from crm.api.whatsapp import send_whatsapp_template

		with (
			patch("crm.api.whatsapp.frappe.db.get_value", return_value=None),
			patch("crm.api.whatsapp.sending_account_name", return_value="Nuovo"),
			patch("crm.api.whatsapp.validate_access"),
			patch("crm.api.whatsapp.frappe.new_doc"),
			patch("crm.api.whatsapp.whatsapp_recipient", return_value="+393330000000"),
			patch("crm.api.whatsapp.insert_and_send", return_value="MSG-1") as sent,
		):
			send_whatsapp_template("CRM Lead", "LEAD-0001", "promo-it", "+393330000000")

		sent.assert_called_once()

	def test_the_sending_account_is_the_one_frappe_whatsapp_uses(self):
		"""The flag on the account, not the link on Settings — they can disagree,
		and the flag is what sends."""
		from crm.api.whatsapp import sending_account_name

		with (
			patch("crm.api.whatsapp.frappe.db.exists", return_value=True),
			patch("crm.api.whatsapp.frappe.db.get_value", return_value="Mattia"),
		):
			self.assertEqual(sending_account_name(), "Mattia")


class TestAClientSiteDoesNotSeeTheAgencysPlumbing(FrappeTestCase):
	"""The Meta app id, the Embedded Signup configuration and the button that
	changes it belong to the provider. On a client's site the app is somebody
	else's: the id means nothing they can act on, and the field is the one thing
	that would stop their own connection working."""

	def test_the_status_says_whether_this_is_the_provider(self):
		from crm.integrations.whatsapp.api import get_status

		status = get_status()
		if status.get("installed"):
			self.assertIn("is_hub", status)
			self.assertIsInstance(status["is_hub"], bool)


class TestMetaErrorsSayWhatToDo(FrappeTestCase):
	"""Meta answers a refusal with a number and a sentence written for whoever
	wrote the integration. Neither half says whose problem it is, so every error
	gets a second sentence that does."""

	def test_the_24_hour_window_is_named_for_what_it_is(self):
		from crm.integrations.meta.errors import advice

		said = advice(131047)
		self.assertIn("24 hours", said)
		self.assertIn("template", said)

	def test_a_dead_token_says_reconnect(self):
		from crm.integrations.meta.errors import advice

		self.assertIn("reconnect", advice(190).lower())

	def test_a_subcode_is_more_specific_than_its_code(self):
		"""190 on its own is «log in again»; 190/460 is «the password changed»."""
		from crm.integrations.meta.errors import advice

		self.assertIn("password", advice(190, 460).lower())
		self.assertNotEqual(advice(190), advice(190, 460))

	def test_the_media_codes_are_the_two_we_lost_a_day_to(self):
		from crm.integrations.meta.errors import advice

		self.assertIn("Content-Type", advice(131052))
		self.assertIn("Opus", advice(131053))

	def test_a_template_on_the_wrong_account_is_explained(self):
		from crm.integrations.meta.errors import advice

		self.assertIn("approved on", advice(132001))

	def test_an_unknown_code_adds_nothing_rather_than_guessing(self):
		from crm.integrations.meta.errors import advice

		self.assertEqual(advice(999999), "")
		self.assertEqual(advice(None), "")
		self.assertEqual(advice("not a number"), "")

	def test_a_code_is_read_out_of_metas_own_sentence(self):
		"""A WhatsApp send never touches our Graph client: what comes back is
		Meta's text with the code in brackets."""
		from crm.integrations.meta.errors import explain_text

		explained = explain_text("(#131047) Re-engagement message")
		self.assertIn("Re-engagement message", explained)
		self.assertIn("24 hours", explained)

	def test_text_with_no_code_is_returned_untouched(self):
		from crm.integrations.meta.errors import explain_text

		self.assertEqual(explain_text("something broke"), "something broke")
		self.assertEqual(explain_text(""), "")

	def test_the_exception_carries_the_explanation(self):
		from crm.integrations.meta.client import MetaAPIError

		error = MetaAPIError("Invalid parameter", code=190)
		self.assertEqual(error.raw, "Invalid parameter")
		self.assertIn("Invalid parameter", str(error))
		self.assertIn("reconnect", str(error).lower())


class TestANumberIsRetiredNotDeleted(FrappeTestCase):
	"""Eight doctypes point at a WhatsApp Account — every message most of all —
	so deleting one barely worked, and it should not: the chat history belongs to
	that number. It is switched off instead, and the other way is closed."""

	def test_deleting_from_the_desk_is_refused_and_says_where_to_go(self):
		from crm.integrations.whatsapp.api import refuse_account_deletion

		with self.assertRaises(frappe.ValidationError) as caught:
			refuse_account_deletion(MagicMock())
		self.assertIn("Settings", str(caught.exception))
