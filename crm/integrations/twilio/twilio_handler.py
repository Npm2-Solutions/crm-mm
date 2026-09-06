import frappe
from frappe import _
from frappe.utils.password import get_decrypted_password
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VoiceGrant
from twilio.rest import Client as TwilioClient
from twilio.twiml.voice_response import Dial, VoiceResponse

from crm.telephony import answering, routing
from crm.telephony.providers import get as get_provider

from .utils import get_public_url


class Twilio:
	"""Twilio connector over TwilioClient."""

	def __init__(self, settings):
		"""
		:param settings: `CRM Twilio Settings` doctype
		"""
		self.settings = settings
		self.account_sid = settings.account_sid
		self.application_sid = settings.twiml_sid
		self.api_key = settings.api_key
		self.api_secret = settings.get_password("api_secret")
		self.auth_token = settings.get_password("auth_token", raise_exception=False)
		self.twilio_client = self.get_twilio_client()

	@classmethod
	def connect(cls):
		"""Read CRM Twilio Settings and return a configured Twilio instance, or None if not enabled."""
		settings = frappe.get_doc("CRM Twilio Settings")
		if not (settings and settings.enabled):
			return
		return Twilio(settings=settings)

	def get_phone_numbers(self):
		"""Get account's twilio phone numbers."""
		numbers = self.twilio_client.incoming_phone_numbers.list()
		return [n.phone_number for n in numbers]

	def generate_voice_access_token(self, identity: str, ttl=60 * 60):
		"""Generates a token required to make voice calls from the browser."""
		# identity is used by twilio to identify the user uniqueness at browser(or any endpoints).
		identity = self.safe_identity(identity)

		# Create access token with credentials
		token = AccessToken(self.account_sid, self.api_key, self.api_secret, identity=identity, ttl=ttl)

		# Create a Voice grant and add to token
		voice_grant = VoiceGrant(
			outgoing_application_sid=self.application_sid,
			incoming_allow=True,  # Allow incoming calls
		)
		token.add_grant(voice_grant)
		return token.to_jwt()

	@classmethod
	def safe_identity(cls, identity: str):
		"""Create a safe identity by replacing unsupported special charaters `@` with (at)).
		Twilio Client JS fails to make a call connection if identity has special characters like @, [, / etc)
		https://www.twilio.com/docs/voice/client/errors (#31105)
		"""
		return identity.replace("@", "(at)")

	@classmethod
	def emailid_from_identity(cls, identity: str):
		"""Convert safe identity string into emailID."""
		return identity.replace("(at)", "@")

	def get_recording_status_callback_url(self):
		url_path = "/api/method/crm.integrations.twilio.api.update_recording_info"
		return get_public_url(url_path)

	def get_update_call_status_callback_url(self):
		url_path = "/api/method/crm.integrations.twilio.api.update_call_status_info"
		return get_public_url(url_path)

	def recording_notice(self) -> str | None:
		"""What to say before connecting, when the call is being recorded."""
		if not self.settings.record_calls:
			return None
		return (self.settings.recording_notice or "").strip() or None

	def get_recording_notice_url(self):
		url_path = "/api/method/crm.integrations.twilio.api.recording_notice"
		return get_public_url(url_path)

	def say_notice(self, resp: VoiceResponse) -> None:
		"""Speak the recording notice into an existing response, if there is one."""
		if notice := self.recording_notice():
			voice, language = notice_voice()
			resp.say(notice, language=language, voice=voice)

	def generate_twilio_dial_response(self, from_number: str, to_number: str, notify_callee=False):
		"""Voice instructions to forward the call to a phone.

		``notify_callee`` decides which side hears the recording notice. On an
		incoming call the person to tell is the one already on the line, so it is
		spoken before dialling. On an outgoing one it is the person about to be
		rung, so it rides on their leg via the number's own TwiML — telling the
		agent that their own call is recorded discloses nothing to anybody.
		"""
		resp = VoiceResponse()
		if not notify_callee:
			self.say_notice(resp)

		dial = Dial(
			caller_id=from_number,
			record=self.settings.record_calls,
			recording_status_callback=self.get_recording_status_callback_url(),
			recording_status_callback_event="completed",
		)
		dial.number(
			to_number,
			url=self.get_recording_notice_url() if (notify_callee and self.recording_notice()) else None,
			status_callback_event="initiated ringing answered completed",
			status_callback=self.get_update_call_status_callback_url(),
			status_callback_method="POST",
		)
		resp.append(dial)
		return resp

	def get_call_info(self, call_sid):
		return self.twilio_client.calls(call_sid).fetch()

	def generate_twilio_client_response(self, client, ring_tone="at"):
		"""Generates voice call instructions to forward the call to agents computer."""
		resp = VoiceResponse()
		# the caller is already on the line, so they are the one to tell
		self.say_notice(resp)
		dial = Dial(
			ring_tone=ring_tone,
			record=self.settings.record_calls,
			recording_status_callback=self.get_recording_status_callback_url(),
			recording_status_callback_event="completed",
		)
		dial.client(
			client,
			status_callback_event="initiated ringing answered completed",
			status_callback=self.get_update_call_status_callback_url(),
			status_callback_method="POST",
		)
		resp.append(dial)
		return resp

	@classmethod
	def get_twilio_client(self):
		twilio_settings = frappe.get_doc("CRM Twilio Settings")
		if not twilio_settings.enabled:
			frappe.throw(_("Please enable twilio settings before making a call."))

		auth_token = get_decrypted_password("CRM Twilio Settings", "CRM Twilio Settings", "auth_token")
		client = TwilioClient(twilio_settings.account_sid, auth_token)

		return client


def notice_voice() -> tuple[str, str]:
	"""Voice and language for spoken notices, borrowed from the answering service.

	One place to configure how the CRM sounds on the phone; a second pair of
	fields would only ever be set to the same values.
	"""
	config = answering.settings()
	return (config.voice or "alice", config.language or "it-IT")


class TwilioCallDetails:
	def __init__(self, call_info, call_from=None, call_to=None):
		self.call_info = call_info
		self.account_sid = call_info.get("AccountSid")
		self.application_sid = call_info.get("ApplicationSid")
		self.call_sid = call_info.get("CallSid")
		self.call_status = self.get_call_status(call_info.get("CallStatus"))
		self._call_from = call_from or call_info.get("From")
		self._call_to = call_to or call_info.get("To")

	def get_direction(self):
		# Caller is absent on some callbacks; a missing one is not an outgoing call
		caller = self.call_info.get("Caller") or ""
		return "Outgoing" if caller.lower().startswith("client") else "Incoming"

	def get_from_number(self):
		return self._call_from or self.call_info.get("From")

	def get_to_number(self):
		return self._call_to or self.call_info.get("To")

	@classmethod
	def get_call_status(cls, twilio_status):
		"""Convert Twilio given status into system status."""
		twilio_status = twilio_status or ""
		return " ".join(twilio_status.split("-")).title()

	def to_dict(self):
		"""Convert call details into dict."""
		direction = self.get_direction()
		from_number = self.get_from_number()
		to_number = self.get_to_number()
		caller = ""
		receiver = ""

		if direction == "Outgoing":
			identity = (self.call_info.get("Caller") or "").replace("client:", "").strip()
			caller = Twilio.emailid_from_identity(identity) if identity else ""
		elif not answering.takes_every_call():
			# with the announcement answering every call there is no attender to
			# find, and guessing one would credit an agent with a call they never took
			attender = routing.find_attender(get_provider("twilio"), to_number, from_number)
			receiver = attender["name"] if attender else ""

		return {
			"type": direction,
			"status": self.call_status,
			"id": self.call_sid,
			"from": from_number,
			"to": to_number,
			"receiver": receiver,
			"caller": caller,
		}
