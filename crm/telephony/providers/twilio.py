# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Twilio, speaking TwiML.

The twilio SDK is imported inside the methods rather than at module level, so a
site that has moved to another carrier can drop the dependency without this
module failing to import and taking the registry down with it.
"""

from __future__ import annotations

import frappe

from crm.telephony.providers.base import Announcement, CallInstruction, TelephonyProvider


class TwilioProvider(TelephonyProvider):
	name = "twilio"
	label = "Twilio"
	agent_number_field = "twilio_number"
	controls_call_flow = True
	rings_browser = True

	def is_enabled(self) -> bool:
		return bool(frappe.db.get_single_value("CRM Twilio Settings", "enabled"))

	def recording_credentials(self) -> tuple | None:
		settings = frappe.get_single("CRM Twilio Settings")
		secret = settings.get_password("api_secret", raise_exception=False)
		return (settings.api_key, secret) if settings.api_key and secret else None

	# ------------------------------------------------------------------
	# call control
	# ------------------------------------------------------------------

	def say(self, announcement: Announcement, hang_up: bool = True) -> CallInstruction:
		from twilio.twiml.voice_response import VoiceResponse

		response = VoiceResponse()
		if announcement.audio_url:
			response.play(announcement.audio_url)
		elif announcement.text:
			response.say(
				announcement.text,
				language=announcement.language or "it-IT",
				voice=announcement.voice or "alice",
			)
		if hang_up:
			response.hangup()
		return CallInstruction(response.to_xml())

	def dial_phone(self, caller_id: str, to_number: str) -> CallInstruction:
		client = self._client()
		return CallInstruction(client.generate_twilio_dial_response(caller_id, to_number).to_xml())

	def dial_agent(self, agent: str) -> CallInstruction:
		client = self._client()
		return CallInstruction(client.generate_twilio_client_response(client.safe_identity(agent)).to_xml())

	# ------------------------------------------------------------------
	# what this account can present, and how each number is routed
	# ------------------------------------------------------------------

	def list_caller_ids(self) -> list[dict]:
		"""Every number the account owns or has verified, with its routing.

		Two sources, because they mean different things. An *incoming phone number*
		is owned outright: it can be presented outbound and can receive calls. An
		*outgoing caller ID* was proven by a verification call: it can be presented,
		but incoming calls to it belong to whoever really owns the line.
		"""
		client = self._rest()
		inbound_url = self.inbound_webhook_url()
		trunk_names = self._trunk_names(client)
		rows = []

		for number in client.incoming_phone_numbers.list():
			capabilities = number.capabilities or {}
			rows.append(
				{
					"phone_number": number.phone_number,
					"label": number.friendly_name,
					"source": "Account Number",
					"voice_capable": bool(capabilities.get("voice", True)),
					"sms_capable": bool(capabilities.get("sms")),
					"voice_url": number.voice_url,
					"voice_application_sid": number.voice_application_sid,
					"sip_trunk_sid": number.trunk_sid,
					"sip_trunk": trunk_names.get(number.trunk_sid),
					"points_at_crm": self._points_at(number.voice_url, inbound_url),
					"uses_crm_app": bool(
						number.voice_application_sid
						and number.voice_application_sid == self.settings().twiml_sid
					),
				}
			)

		for verified in client.outgoing_caller_ids.list():
			rows.append(
				{
					"phone_number": verified.phone_number,
					"label": verified.friendly_name,
					"source": "Verified Caller ID",
					"voice_capable": True,
					"sms_capable": False,
				}
			)

		return rows

	def inbound_webhook_url(self) -> str:
		from crm.integrations.twilio.utils import get_public_url

		return get_public_url("/api/method/crm.integrations.twilio.api.twilio_incoming_call_handler")

	@staticmethod
	def _points_at(voice_url: str | None, expected: str) -> bool:
		"""Whether a number's voice webhook is our incoming handler.

		Compared on the path rather than the whole URL: the host can legitimately
		differ from the one this app knows itself by, which is the same reason the
		callback base is configurable in the first place.
		"""
		if not voice_url:
			return False
		return voice_url.split("?")[0].endswith(expected.split("?")[0].rsplit("/", 1)[-1])

	# ------------------------------------------------------------------
	# SIP trunking
	# ------------------------------------------------------------------

	def list_sip_trunks(self) -> list[dict]:
		"""The account's Elastic SIP trunks, with what each one does to a number.

		Read-only on purpose. Creating and authenticating a trunk belongs in Twilio's
		console, next to the IP allow-lists and credentials it needs; what the CRM
		needs to know is which of its numbers have been handed to one, because those
		numbers stop reaching it.
		"""
		client = self._rest()
		trunks = []

		for trunk in client.trunking.v1.trunks.list():
			scoped = client.trunking.v1.trunks(trunk.sid)
			trunks.append(
				{
					"sid": trunk.sid,
					"friendly_name": trunk.friendly_name,
					"termination_uri": f"{trunk.domain_name}" if trunk.domain_name else None,
					"secure": bool(trunk.secure),
					"cnam_lookup_enabled": bool(trunk.cnam_lookup_enabled),
					"transfer_mode": trunk.transfer_mode,
					"auth_type": trunk.auth_type,
					"origination_urls": [
						{
							"friendly_name": url.friendly_name,
							"sip_url": url.sip_url,
							"priority": url.priority,
							"weight": url.weight,
							"enabled": bool(url.enabled),
						}
						for url in scoped.origination_urls.list()
					],
					"phone_numbers": [n.phone_number for n in scoped.phone_numbers.list()],
				}
			)
		return trunks

	def _trunk_names(self, client) -> dict[str, str]:
		"""Trunk SID to friendly name, so a number can say which trunk took it."""
		try:
			return {t.sid: t.friendly_name for t in client.trunking.v1.trunks.list()}
		except Exception:
			# trunking may not be enabled on the account; a missing name is not worth
			# failing the whole number sync over
			frappe.log_error(frappe.get_traceback(), "CRM Telephony: could not list SIP trunks")
			return {}

	# ------------------------------------------------------------------
	# verifying a number the practice owns
	# ------------------------------------------------------------------

	def start_caller_id_verification(self, phone_number: str, label: str | None = None) -> dict:
		"""Ask Twilio to ring a number and hand back the code to type on it.

		This is the legitimate way to present a number you own but did not buy here:
		answering the call and entering the code proves you control the line.
		"""
		request = self._rest().validation_requests.create(
			phone_number=phone_number, friendly_name=label or phone_number
		)
		return {
			"phone_number": request.phone_number,
			"validation_code": request.validation_code,
			"call_sid": request.call_sid,
		}

	def settings(self):
		return frappe.get_cached_doc("CRM Twilio Settings")

	def _rest(self):
		"""The plain REST client, for the resources that are not call control."""
		from crm.integrations.twilio.twilio_handler import Twilio

		return Twilio.get_twilio_client()

	def _client(self):
		from crm.integrations.twilio.twilio_handler import Twilio

		twilio = Twilio.connect()
		if not twilio:
			frappe.throw(frappe._("Twilio is not configured."))
		return twilio
