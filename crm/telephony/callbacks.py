# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The callback queue: who the answering service promised a call to, and by when.

A callback lives on the ``CRM Call Log`` row of the incoming call that created
it, rather than in a table of its own. The call already carries everything a
callback needs — the number, the moment, and the lead or deal it was matched to
— so a separate document would only be a second copy of the same facts, kept in
step by hand.
"""

from __future__ import annotations

import frappe
from frappe.utils import add_to_date, cint, now_datetime

from crm.telephony import answering

PENDING = "Pending"
DONE = "Done"
CANCELLED = "Cancelled"

_MATCH_DIGITS = 9
"""How many trailing digits decide that two numbers are the same caller.

Enough to be the whole national number in most plans, so ``+39 333 1234567`` and
``333 1234567`` merge while two different callers do not. Deliberately blunter
than a full ``phonenumbers`` parse: the caller ID a provider hands us is not
always parseable, and the cost of being wrong here is one merged callback inside
a few-hour window, not a lost call.
"""


def _match_key(number: str | None) -> str:
	digits = "".join(c for c in (number or "") if c.isdigit())
	return digits[-_MATCH_DIGITS:] if len(digits) >= _MATCH_DIGITS else digits


def _emit(event: str, call_log, payload: dict | None = None) -> None:
	"""Fire an automation event, never at the cost of the call itself."""
	try:
		from crm.automation.engine import process_event

		process_event(event, call_log, payload or {})
	except Exception:
		frappe.log_error(frappe.get_traceback(), "CRM Telephony: automation event failed")


# --------------------------------------------------------------------------
# queueing
# --------------------------------------------------------------------------


def find_pending_for_number(number: str | None, within_hours: int) -> str | None:
	"""An open callback already owed to this caller, if there is one.

	Someone who hears the announcement often rings straight back. Without this
	the front desk would find the same person three times in one round.
	"""
	key = _match_key(number)
	if not key or within_hours <= 0:
		return None

	since = add_to_date(now_datetime(), hours=-within_hours)
	rows = frappe.get_all(
		"CRM Call Log",
		filters={"callback_status": PENDING, "creation": [">=", since]},
		fields=["name", "from"],
		order_by="creation asc",
	)
	for row in rows:
		if _match_key(row.get("from")) == key:
			return row.name
	return None


def queue_callback(call_log, config=None) -> str:
	"""Record that this caller is owed a call back.

	Returns the call log carrying the callback, which is an *earlier* one when the
	caller has rung again inside the merge window. The repeat call is still logged
	— the history is worth keeping — it just doesn't queue a second callback.
	"""
	config = config if config is not None else answering.settings()

	existing = find_pending_for_number(call_log.get("from"), cint(config.dedupe_window_hours))
	if existing and existing != call_log.name:
		return existing

	call_log.callback_status = PENDING
	call_log.callback_due = answering.callback_due(config)
	call_log.callback_attempts = 0
	call_log.save(ignore_permissions=True)

	_emit("callback_requested", call_log, {"number": call_log.get("from")})
	return call_log.name


# --------------------------------------------------------------------------
# working the queue
# --------------------------------------------------------------------------


def resolve_callback(name: str, user: str | None = None):
	"""The caller was reached — the promise is kept."""
	log = frappe.get_doc("CRM Call Log", name)
	if log.callback_status != PENDING:
		return log
	log.callback_status = DONE
	log.callback_by = user or frappe.session.user
	log.callback_completed_on = now_datetime()
	log.save(ignore_permissions=True)
	_emit("callback_completed", log)
	return log


def record_attempt(name: str, user: str | None = None, config=None):
	"""An attempt that didn't reach the caller.

	Comes back around after the retry delay until the attempt cap is spent, at
	which point it closes as unreachable rather than circling forever.
	"""
	config = config if config is not None else answering.settings()
	log = frappe.get_doc("CRM Call Log", name)
	if log.callback_status != PENDING:
		return log

	log.callback_attempts = cint(log.callback_attempts) + 1
	cap = cint(config.max_callback_attempts)
	exhausted = bool(cap) and log.callback_attempts >= cap

	if exhausted:
		log.callback_status = CANCELLED
		log.callback_by = user or frappe.session.user
		log.callback_completed_on = now_datetime()
	else:
		log.callback_due = answering.retry_due(config)

	log.save(ignore_permissions=True)
	_emit(
		"callback_attempt_failed",
		log,
		{"attempts": log.callback_attempts, "exhausted": exhausted},
	)
	return log


def reschedule_callback(name: str, at=None, config=None):
	"""The caller asked to be rung at another time."""
	config = config if config is not None else answering.settings()
	log = frappe.get_doc("CRM Call Log", name)
	if log.callback_status != PENDING:
		return log
	log.callback_due = at or answering.retry_due(config)
	log.save(ignore_permissions=True)
	return log


def cancel_callback(name: str, user: str | None = None):
	"""Close a callback nobody owes any more."""
	log = frappe.get_doc("CRM Call Log", name)
	if log.callback_status != PENDING:
		return log
	log.callback_status = CANCELLED
	log.callback_by = user or frappe.session.user
	log.callback_completed_on = now_datetime()
	log.save(ignore_permissions=True)
	return log


# --------------------------------------------------------------------------
# reading the queue
# --------------------------------------------------------------------------

QUEUE_FIELDS = (
	"name",
	"from",
	"to",
	"callback_due",
	"callback_attempts",
	"reference_doctype",
	"reference_docname",
	"creation",
)


def pending_callbacks(only_due: bool = True, limit: int = 100) -> list[dict]:
	"""The queue, oldest promise first.

	Permission-aware on purpose — this feeds the dialer, so an agent only ever
	builds a round out of call logs they are allowed to see.
	"""
	filters = {"callback_status": PENDING}
	if only_due:
		filters["callback_due"] = ["<=", now_datetime()]
	return frappe.get_list(
		"CRM Call Log",
		filters=filters,
		fields=list(QUEUE_FIELDS),
		order_by="callback_due asc, creation asc",
		page_length=max(cint(limit), 1),
	)


def pending_summary() -> dict:
	"""Counts the front desk actually acts on: what is owed, and what is late."""
	now = now_datetime()
	total = frappe.db.count("CRM Call Log", {"callback_status": PENDING})
	due = frappe.db.count("CRM Call Log", {"callback_status": PENDING, "callback_due": ["<=", now]})
	oldest = frappe.get_all(
		"CRM Call Log",
		filters={"callback_status": PENDING},
		fields=["callback_due"],
		order_by="callback_due asc",
		limit=1,
	)
	return {
		"pending": total,
		"due": due,
		"upcoming": max(total - due, 0),
		"oldest_due": oldest[0].callback_due if oldest else None,
	}
