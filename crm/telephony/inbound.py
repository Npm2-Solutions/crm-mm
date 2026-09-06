# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""What an incoming call hears — decided once, for every carrier.

This module holds the whole decision and none of the dialect. It asks the
settings what should happen, then asks the provider to say it. Swapping carrier
changes the second half only.
"""

from __future__ import annotations

import frappe
from frappe import _

from crm.telephony import answering, callbacks, routing
from crm.telephony.providers.base import (
	Announcement,
	CallInstruction,
	ProviderNotSupported,
	TelephonyProvider,
)


def handle_incoming_call(
	provider: TelephonyProvider,
	from_number: str,
	to_number: str,
	call_log=None,
) -> CallInstruction:
	"""Answer, ring somebody, or apologise.

	Whether the answering service takes the call is read off ``answer_mode``,
	never inferred from who happens to be logged in. A practice needs the same
	number to behave the same way at 9am and at 9pm, and "somebody left a tab
	open" is not an explanation it can give its patients.
	"""
	if not provider.controls_call_flow:
		# a carrier whose flow is built in its own dashboard has nothing to be told;
		# reaching here means a webhook was wired to the wrong provider
		raise ProviderNotSupported(
			_("{0} does not let the CRM decide what an incoming call hears.").format(provider.label)
		)

	config = answering.settings()

	if answering.takes_every_call(config):
		return answer_with_service(provider, config, call_log)

	attender = routing.find_attender(provider, to_number, from_number)

	if not attender:
		# "Ring Agents First" means exactly that — the announcement is the
		# fallback, not the surprise
		if answering.rings_agents_first(config):
			return answer_with_service(provider, config, call_log)
		return provider.say(
			Announcement(
				text=_("Agent is unavailable to take the call, please call after some time."),
				language=config.language or "it-IT",
				voice=config.voice or "alice",
			)
		)

	if attender.get("call_receiving_device") == "Phone" and attender.get("mobile_no"):
		return provider.dial_phone(caller_id=from_number, to_number=attender["mobile_no"])
	return provider.dial_agent(attender["name"])


def answer_with_service(provider: TelephonyProvider, config, call_log) -> CallInstruction:
	"""Queue the callback, then say so.

	A failure to queue must not cost the caller the announcement: they would hear
	dead air and ring again, which is the one outcome worse than losing the queue
	entry.
	"""
	due = None
	if call_log:
		try:
			carrier = callbacks.queue_callback(call_log, config)
			due = frappe.db.get_value("CRM Call Log", carrier, "callback_due")
		except Exception:
			# the call log itself is already committed, so this only discards the
			# half-written callback — and leaves the session clean enough to log
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), "CRM Answering Service: failed to queue callback")
			due = answering.callback_due(config)
	else:
		due = answering.callback_due(config)

	return provider.say(answering.build_announcement(config, due=due))
