# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase
from twilio.request_validator import RequestValidator
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request

from crm.integrations.twilio import api
from crm.integrations.twilio.twilio_handler import Twilio, TwilioCallDetails
from crm.integrations.twilio.utils import get_public_url

BASE_URL = "https://crm.studio.it"
VOICE_PATH = "/api/method/crm.integrations.twilio.api.voice"
AUTH_TOKEN = "a-secret-auth-token"
ACCOUNT_SID = "AC00000000000000000000000000000001"


def build_request(url: str, params: dict, signature: str | None = None) -> Request:
	"""A werkzeug request shaped like the one Twilio would send."""
	builder = EnvironBuilder(method="POST", data=params)
	environ = builder.get_environ()

	scheme, _, rest = url.partition("://")
	host, _, path = rest.partition("/")
	environ["wsgi.url_scheme"] = scheme
	environ["HTTP_HOST"] = host
	environ["PATH_INFO"] = "/" + path
	if signature is not None:
		environ["HTTP_X_TWILIO_SIGNATURE"] = signature
	return Request(environ)


class TwilioRequestCase(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self._original_request = getattr(frappe.local, "request", None)

	def tearDown(self):
		frappe.local.request = self._original_request
		frappe.db.rollback()

	def as_twilio(self, url: str, params: dict, token: str = AUTH_TOKEN, tamper: bool = False):
		signature = RequestValidator(token).compute_signature(url, params)
		if tamper:
			signature = "x" + signature[1:]
		frappe.local.request = build_request(url, params, signature)


# ---------------------------------------------------------------------------
# webhook authenticity
# ---------------------------------------------------------------------------


PARAMS = {"AccountSid": ACCOUNT_SID, "CallSid": "CA123", "From": "+393331234567"}


class TestSignatureValidation(TwilioRequestCase):
	def test_a_properly_signed_request_is_accepted(self):
		self.as_twilio(BASE_URL + VOICE_PATH, PARAMS)
		self.assertTrue(api._signature_is_valid(AUTH_TOKEN))

	def test_a_tampered_signature_is_refused(self):
		self.as_twilio(BASE_URL + VOICE_PATH, PARAMS, tamper=True)
		self.assertFalse(api._signature_is_valid(AUTH_TOKEN))

	def test_a_signature_from_another_account_is_refused(self):
		self.as_twilio(BASE_URL + VOICE_PATH, PARAMS, token="somebody-elses-token")
		self.assertFalse(api._signature_is_valid(AUTH_TOKEN))

	def test_an_unsigned_request_is_refused(self):
		frappe.local.request = build_request(BASE_URL + VOICE_PATH, PARAMS)
		self.assertFalse(api._signature_is_valid(AUTH_TOKEN))

	def test_changed_parameters_break_the_signature(self):
		signature = RequestValidator(AUTH_TOKEN).compute_signature(BASE_URL + VOICE_PATH, PARAMS)
		# the body an attacker would want to change: a recording url of their choosing
		forged = {**PARAMS, "RecordingUrl": "https://attacker.example/evil.mp3"}
		frappe.local.request = build_request(BASE_URL + VOICE_PATH, forged, signature)
		self.assertFalse(api._signature_is_valid(AUTH_TOKEN))

	def test_without_a_token_nothing_validates(self):
		self.as_twilio(BASE_URL + VOICE_PATH, PARAMS)
		self.assertFalse(api._signature_is_valid(None))
		self.assertFalse(api._signature_is_valid(""))

	def test_a_tls_terminating_proxy_still_validates(self):
		"""Twilio signed https; the app behind the proxy sees http."""
		signature = RequestValidator(AUTH_TOKEN).compute_signature(BASE_URL + VOICE_PATH, PARAMS)
		frappe.local.request = build_request("http://crm.studio.it" + VOICE_PATH, PARAMS, signature)
		self.assertTrue(api._signature_is_valid(AUTH_TOKEN))


class TestSignatureSwitch(IntegrationTestCase):
	def test_nothing_stored_still_means_on(self):
		# an installation predating the field must not silently stop checking
		self.assertTrue(api._signature_check_enabled(frappe._dict()))
		self.assertTrue(api._signature_check_enabled(frappe._dict(verify_webhook_signature=None)))

	def test_it_can_be_switched_off_on_purpose(self):
		self.assertFalse(api._signature_check_enabled(frappe._dict(verify_webhook_signature=0)))

	def test_it_is_on_when_set(self):
		self.assertTrue(api._signature_check_enabled(frappe._dict(verify_webhook_signature=1)))


# ---------------------------------------------------------------------------
# callback address
# ---------------------------------------------------------------------------


class TestCallbackUrl(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_the_configured_base_wins(self):
		frappe.db.set_single_value("CRM Twilio Settings", "webhook_base_url", "https://tunnel.test")
		self.assertEqual(get_public_url(VOICE_PATH), "https://tunnel.test" + VOICE_PATH)

	def test_a_trailing_slash_does_not_double_up(self):
		frappe.db.set_single_value("CRM Twilio Settings", "webhook_base_url", "https://tunnel.test/")
		self.assertEqual(get_public_url(VOICE_PATH), "https://tunnel.test" + VOICE_PATH)

	def test_the_site_url_is_the_fallback(self):
		frappe.db.set_single_value("CRM Twilio Settings", "webhook_base_url", "")
		self.assertTrue(get_public_url(VOICE_PATH).endswith(VOICE_PATH))

	def test_no_path_returns_the_bare_base(self):
		frappe.db.set_single_value("CRM Twilio Settings", "webhook_base_url", "https://tunnel.test")
		self.assertEqual(get_public_url(), "https://tunnel.test")


# ---------------------------------------------------------------------------
# reading what Twilio sent
# ---------------------------------------------------------------------------


class TestCallDetails(IntegrationTestCase):
	def test_a_missing_caller_is_an_incoming_call(self):
		# some callbacks carry no Caller at all; that used to crash the webhook
		details = TwilioCallDetails(frappe._dict({"CallSid": "CA1", "CallStatus": "completed"}))
		self.assertEqual(details.get_direction(), "Incoming")

	def test_a_browser_leg_is_an_outgoing_call(self):
		details = TwilioCallDetails(frappe._dict({"Caller": "client:agent(at)studio.it"}))
		self.assertEqual(details.get_direction(), "Outgoing")
		self.assertEqual(details.to_dict()["caller"], "agent@studio.it")

	def test_statuses_are_normalised(self):
		self.assertEqual(TwilioCallDetails.get_call_status("in-progress"), "In Progress")
		self.assertEqual(TwilioCallDetails.get_call_status("no-answer"), "No Answer")
		self.assertEqual(TwilioCallDetails.get_call_status(None), "")


# ---------------------------------------------------------------------------
# telling people they are being recorded
# ---------------------------------------------------------------------------


NOTICE = "Questa chiamata potrebbe essere registrata."


class TestRecordingNotice(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()
		if hasattr(frappe.local, "crm_answering_settings"):
			del frappe.local.crm_answering_settings

	def connector(self, record_calls=1, notice=NOTICE):
		settings = frappe._dict(
			{
				"account_sid": ACCOUNT_SID,
				"twiml_sid": "AP1",
				"api_key": "SK1",
				"record_calls": record_calls,
				"recording_notice": notice,
				"get_password": lambda *args, **kwargs: "secret",
			}
		)
		with patch.object(Twilio, "get_twilio_client", return_value=MagicMock()):
			return Twilio(settings=settings)

	def test_no_notice_when_calls_are_not_recorded(self):
		self.assertIsNone(self.connector(record_calls=0).recording_notice())

	def test_no_notice_when_the_text_is_blank(self):
		self.assertIsNone(self.connector(notice="   ").recording_notice())

	def test_an_incoming_caller_is_told_before_being_connected(self):
		xml = self.connector().generate_twilio_dial_response("+390212345678", "+393480000000").to_xml()
		self.assertIn("<Say", xml)
		self.assertIn("registrata", xml)
		# spoken to whoever is already on the line, before the dial
		self.assertLess(xml.index("<Say"), xml.index("<Dial"))

	def test_an_outgoing_callee_is_told_on_their_own_leg(self):
		xml = (
			self.connector()
			.generate_twilio_dial_response("+390212345678", "+393480000000", notify_callee=True)
			.to_xml()
		)
		# nothing spoken to the agent; the notice rides on the number being rung
		self.assertNotIn("<Say", xml)
		self.assertIn("crm.integrations.twilio.api.recording_notice", xml)

	def test_a_browser_agent_call_still_tells_the_caller(self):
		xml = self.connector().generate_twilio_client_response("agent(at)studio.it").to_xml()
		self.assertIn("registrata", xml)

	def test_nothing_is_announced_when_recording_is_off(self):
		twilio = self.connector(record_calls=0)
		outgoing = twilio.generate_twilio_dial_response("+39021", "+39348", notify_callee=True).to_xml()
		incoming = twilio.generate_twilio_dial_response("+39021", "+39348").to_xml()
		self.assertNotIn("recording_notice", outgoing)
		self.assertNotIn("<Say", incoming)
