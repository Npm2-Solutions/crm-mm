# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""What the CRM needs from a telephony provider, and nothing more.

The decisions — whether the answering service takes the call, what it says, by
when the callback falls due, who would otherwise be rung — are made once, in
provider-agnostic code. A provider only *renders* those decisions into whatever
call-control language it speaks: TwiML for Twilio, JSON actions for 46elks,
SVAML for Sinch, a dialplan for an Asterisk you host yourself.

That split matters more than it looks. Which carrier a practice can use is
decided by regulators and by where its data may be processed, and both change
without asking. Keeping the decisions out of the carrier's dialect means that
answering the door differently costs one new file, not a rewrite.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import frappe
from frappe import _


@dataclass(frozen=True)
class Announcement:
	"""What a caller hears. Either a recording to play or words to speak."""

	text: str | None = None
	audio_url: str | None = None
	language: str = "it-IT"
	voice: str = "alice"


@dataclass(frozen=True)
class CallInstruction:
	"""A provider's answer to "what should this call do now", ready to return.

	The body is already in the provider's own language; the webhook that returns
	it does not need to know which one that is.
	"""

	body: str
	mimetype: str = "text/xml"


class ProviderNotSupported(frappe.ValidationError):
	"""Raised when a provider is asked for something it cannot do."""


class TelephonyProvider(ABC):
	"""One carrier's dialect.

	Subclasses are cheap on purpose: state lives in the provider's settings
	doctype, and an instance is built per request.
	"""

	name: str = ""
	"""Stable identifier used in settings and APIs, e.g. ``twilio``."""

	label: str = ""
	"""What a person sees, and the value stored in ``CRM Call Log.telephony_medium``."""

	agent_number_field: str = ""
	"""Field on ``CRM Telephony Agent`` holding this provider's number for an agent."""

	controls_call_flow: bool = False
	"""Whether the CRM decides what an incoming call hears.

	False for providers whose call flow is configured in their own dashboard and
	who only notify the CRM afterwards — the answering service cannot run on those.
	"""

	rings_browser: bool = False
	"""Whether an agent can take a call in the browser rather than on a phone."""

	places_calls_server_side: bool = False
	"""Whether the server can start an outgoing call.

	False for providers that dial from the agent's browser, where the server never
	originates anything.
	"""

	# ------------------------------------------------------------------
	# configuration
	# ------------------------------------------------------------------

	@abstractmethod
	def is_enabled(self) -> bool:
		"""Is this provider configured and switched on for this site?"""

	def caller_id_for(self, user: str) -> str | None:
		"""The number this agent's outgoing calls present."""
		if not self.agent_number_field:
			return None
		return frappe.db.get_value("CRM Telephony Agent", user, self.agent_number_field)

	def recording_credentials(self) -> tuple | None:
		"""``(user, secret)`` for fetching a recording, or ``None`` when it needs no auth."""
		return None

	# ------------------------------------------------------------------
	# what an incoming call hears
	# ------------------------------------------------------------------

	def say(self, announcement: Announcement, hang_up: bool = True) -> CallInstruction:
		raise ProviderNotSupported(
			_("{0} does not let the CRM control what a call hears.").format(self.label)
		)

	def dial_phone(self, caller_id: str, to_number: str) -> CallInstruction:
		raise ProviderNotSupported(_("{0} cannot forward a call to a phone.").format(self.label))

	def dial_agent(self, agent: str) -> CallInstruction:
		raise ProviderNotSupported(_("{0} cannot ring an agent in the browser.").format(self.label))

	# ------------------------------------------------------------------
	# outgoing
	# ------------------------------------------------------------------

	def place_call(self, to_number: str, from_number: str | None = None) -> dict:
		"""Start an outgoing call. Returns whatever the provider reports about it."""
		raise ProviderNotSupported(
			_("{0} starts outgoing calls from the browser, not from the server.").format(self.label)
		)

	# ------------------------------------------------------------------

	def as_dict(self) -> dict:
		"""The shape the settings UI and the call button read."""
		return {
			"name": self.name,
			"label": self.label,
			"enabled": self.is_enabled(),
			"controls_call_flow": self.controls_call_flow,
			"rings_browser": self.rings_browser,
			"places_calls_server_side": self.places_calls_server_side,
			"agent_number_field": self.agent_number_field,
		}

	def __repr__(self) -> str:
		return f"<{type(self).__name__} {self.name}>"
