# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What an incoming call hears — decided once, for every carrier.

This module holds the whole decision and none of the dialect. It asks the
settings what should happen, then asks the provider to say it. Swapping carrier
changes the second half only.
"""

from __future__ import annotations

import frappe
from frappe import _

from crm.marchio import con_nome
from crm.telephony import answering, callbacks, persa, routing
from crm.telephony.providers.base import (
	Announcement,
	CallInstruction,
	Message,
	ProviderNotSupported,
	Ring,
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
			con_nome(_("{0} does not let {brand} decide what an incoming call hears.")).format(provider.label)
		)

	config = answering.settings()

	if answering.takes_every_call(config):
		persa.chiamata_persa(call_log, from_number, persa.R.SEGRETERIA)
		return answer_with_service(provider, config, call_log)

	ringing = routing.find_ringing(provider, to_number, from_number)

	if not ringing:
		# nobody to ring: a missed call where the centre counts it as one
		persa.chiamata_persa(call_log, from_number, persa.R.NESSUNO_DA_FAR_SQUILLARE)
		# "Ring Agents First" means exactly that — the announcement is the
		# fallback, not the surprise
		if answering.rings_agents_first(config):
			return answer_with_service(provider, config, call_log)
		return provider.say(apology(config))

	# everyone at once: whoever picks up first takes it; nobody within the
	# seconds, and the carrier comes back to `nobody_answered`
	on_phone = [r for r in ringing if r.get("call_receiving_device") == "Phone" and r.get("mobile_no")]
	return provider.ring(
		Ring(
			agents=tuple(r["name"] for r in ringing if r not in on_phone),
			phones=tuple(r["mobile_no"] for r in on_phone),
			caller_id=from_number,
			seconds=answering.ring_seconds(config),
		)
	)


def nobody_answered(provider: TelephonyProvider, call_log=None) -> CallInstruction:
	"""Everyone rang and nobody picked up: the announcement and the callback when the
	answering service rings first, else the apology. The automations hear it, or a
	number nobody knows gets its SMS (`persa`)."""
	persa.chiamata_persa(call_log, call_log.get("from") if call_log else None, persa.R.NESSUNO_RISPONDE)
	config = answering.settings()
	if answering.rings_agents_first(config):
		return answer_with_service(provider, config, call_log)
	return provider.say(apology(config))


def apology(config) -> Announcement:
	return Announcement(
		text=_("Agent is unavailable to take the call, please call after some time."),
		language=config.language or "it-IT",
		voice=config.voice or "alice",
	)


def answer_with_service(provider: TelephonyProvider, config, call_log) -> CallInstruction:
	"""Queue the callback, then say so - and take a message, when the centre wants.

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

	annuncio = answering.build_announcement(config, due=due)
	if answering.takes_messages(config):
		return provider.take_message(
			annuncio,
			Message(
				prompt=answering.message_prompt(config),
				seconds=answering.message_seconds(config),
				language=annuncio.language,
				voice=annuncio.voice,
			),
		)
	return provider.say(annuncio)
