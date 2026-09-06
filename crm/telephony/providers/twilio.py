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

	def _client(self):
		from crm.integrations.twilio.twilio_handler import Twilio

		twilio = Twilio.connect()
		if not twilio:
			frappe.throw(frappe._("Twilio is not configured."))
		return twilio
