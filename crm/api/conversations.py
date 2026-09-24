# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""What has been said to a person, and whether anybody has dealt with it.

The People list and the Inbox are the same list of people. The only difference
is the order and what each row shows: the Inbox puts whoever wrote last at the
top and says how many of their messages are still waiting.

That ordering cannot come from the messages themselves — they live in three
different doctypes, one of them optional — so the answer is written **onto the
person** as it happens, the way every CRM with an inbox does it. A list sorted
by `last_conversation_on` is then an ordinary sorted list: the saved views, the
filters and the columns all keep working, because it *is* the People list.

Read state is kept on the person too, and it is **shared**, not per user. A CRM
inbox is a shared desk: a message a colleague has already answered is not still
waiting for you, and a badge that says it is would be the second thing you learn
to ignore.
"""

import html
import re

import frappe
from frappe.utils import now

RECORDS = ("CRM Lead", "CRM Deal")

# The three places a message can be, and how each one words itself. WhatsApp is
# optional: `frappe_whatsapp` may not be installed.
CHANNELS = {
	"WhatsApp": {
		"doctype": "WhatsApp Message",
		"direction": "type",
		"incoming": "Incoming",
		"text": "message",
	},
	"SMS": {
		"doctype": "CRM SMS Message",
		"direction": "type",
		"incoming": "Incoming",
		"text": "message",
	},
	"Email": {
		"doctype": "Communication",
		"direction": "sent_or_received",
		"incoming": "Received",
		"text": "content",
	},
}

PREVIEW = 140


def scope(reference_doctype: str, reference_name: str) -> list[tuple[str, str]]:
	"""Every record whose messages belong to this person's conversation.

	An email or a WhatsApp during a negotiation belongs to whoever we were
	talking to, not to the negotiation — which is why the Activity tab of a
	person already gathers what was said on their deals. The Inbox has to agree
	with it, or a person would sit at the bottom of the list while the thread
	the CRM shows on their own page was answered this morning.
	"""
	where = [(reference_doctype, reference_name)]
	if reference_doctype == "CRM Lead":
		where += [
			("CRM Deal", deal)
			for deal in frappe.get_all(
				"CRM Deal", filters={"lead": reference_name}, pluck="name", limit_page_length=0
			)
		]
	return where


def person_of(reference_doctype: str, reference_name: str) -> tuple[str, str] | None:
	"""Whose conversation this record's messages count towards.

	The other direction of `scope`: a deal opened from a person is read as that
	person, so a message answered on the deal clears the person's badge.
	"""
	if reference_doctype == "CRM Deal":
		lead = frappe.db.get_value("CRM Deal", reference_name, "lead")
		if lead and frappe.db.exists("CRM Lead", lead):
			return ("CRM Lead", lead)
	return (reference_doctype, reference_name) if reference_doctype in RECORDS else None


def available_channels() -> dict:
	"""The channels this site actually has. WhatsApp is an optional app."""
	return {name: spec for name, spec in CHANNELS.items() if frappe.db.exists("DocType", spec["doctype"])}


def snippet(text: str) -> str:
	"""One line of a message, for the row in the list.

	Email arrives as HTML and WhatsApp with its own marks; neither reads as a
	preview. The tags come out, the entities are read back, the whitespace
	collapses, and what is left is the beginning of what was said.

	`html.unescape` from the standard library rather than a Frappe helper: this
	runs on the way in for every message, and reaching for an API that might not
	be there is how sending a WhatsApp message came to fail with a Python error
	about a preview string.
	"""
	plain = re.sub(r"<[^>]+>", " ", str(text or ""))
	plain = html.unescape(plain)
	plain = re.sub(r"\s+", " ", plain).strip()
	return plain[:PREVIEW]


def belongs_to(where: list[tuple[str, str]]) -> dict:
	"""Filters that match the messages of a whole scope at once."""
	return {
		"reference_doctype": ["in", sorted({doctype for doctype, _ in where})],
		"reference_name": ["in", sorted({name for _, name in where})],
	}


def last_message(where: list[tuple[str, str]]) -> dict | None:
	"""The most recent message in this scope, whatever channel it came by."""
	newest = None
	for channel, spec in available_channels().items():
		filters = belongs_to(where)
		if spec["doctype"] == "Communication":
			filters["communication_type"] = "Communication"
		rows = frappe.get_all(
			spec["doctype"],
			filters=filters,
			fields=["name", "creation", spec["direction"] + " as direction", spec["text"] + " as text"],
			order_by="creation desc",
			limit=1,
		)
		if not rows:
			continue
		row = rows[0]
		row.channel = channel
		row.incoming = row.direction == spec["incoming"]
		if not newest or row.creation > newest.creation:
			newest = row
	return newest


def last_answer(where: list[tuple[str, str]]) -> str | None:
	"""When somebody here last wrote back, across all channels."""
	answered = None
	for spec in available_channels().values():
		filters = belongs_to(where)
		filters[spec["direction"]] = ["!=", spec["incoming"]]
		if spec["doctype"] == "Communication":
			filters["communication_type"] = "Communication"
		rows = frappe.get_all(
			spec["doctype"], filters=filters, fields=["creation"], order_by="creation desc", limit=1
		)
		if rows and (not answered or rows[0].creation > answered):
			answered = rows[0].creation
	return answered


def remember(reference_doctype: str, reference_name: str) -> None:
	"""Write the last message onto the person it was with.

	Called whenever a message is stored. Cheap on purpose: two small queries per
	channel, and `update_modified=False` so a message arriving does not make the
	record look edited.
	"""
	if reference_doctype not in RECORDS or not reference_name:
		return
	if not frappe.db.exists(reference_doctype, reference_name):
		return

	where = scope(reference_doctype, reference_name)
	newest = last_message(where)
	values = {
		"last_conversation_on": newest.creation if newest else None,
		"last_conversation_channel": newest.channel if newest else None,
		"last_conversation_direction": ("Incoming" if newest.incoming else "Outgoing") if newest else None,
		"last_conversation_preview": snippet(newest.text) if newest else None,
		"last_answered_on": last_answer(where),
	}
	# the cutoff is not among the values being written, and «still waiting» is a
	# comparison against it: read it rather than let it come back as unset, which
	# would call every answered conversation waiting again
	cutoff = cutoff_field()
	if cutoff not in values:
		values_with_cutoff = dict(values)
		values_with_cutoff[cutoff] = frappe.db.get_value(reference_doctype, reference_name, cutoff)
	else:
		values_with_cutoff = values
	values["conversation_unread"] = (
		1 if is_waiting(reference_doctype, reference_name, values_with_cutoff) else 0
	)
	frappe.db.set_value(reference_doctype, reference_name, values, update_modified=False)

	# a message on a deal is a message with that person: the row they appear as
	# in the Inbox has to move too
	if reference_doctype == "CRM Deal":
		person = person_of(reference_doctype, reference_name)
		if person and person != (reference_doctype, reference_name):
			remember(*person)


# --- the hooks, one per place a message can arrive from ----------------------


def quiet(what, *args) -> None:
	"""Run it; a fault is a line in the log and nothing more.

	Everything this module does on the way in is bookkeeping, and the message it
	is bookkeeping about has already been sent. Not a precaution in the abstract:
	one wrong helper name in a preview once made sending a WhatsApp message fail
	with a Python error about a string nobody had asked for.
	"""
	try:
		what(*args)
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"Conversations: {what.__name__} did not run")


def quietly(reference_doctype: str, reference_name: str) -> None:
	"""`remember`, and it can never take a message down with it."""
	quiet(remember, reference_doctype, reference_name)


def they_wrote(doc) -> bool:
	"""Did this arrive from them, rather than leave from us?"""
	if doc.doctype == "Communication":
		return doc.get("sent_or_received") == "Received"
	return doc.get("type") == "Incoming"


def reopen(reference_doctype: str, reference_name: str) -> None:
	"""They wrote again: whatever we had decided about this, it is open now.

	Decided from the message that just arrived rather than from the recomputed
	«last message», because those are not the same question. A conversation is
	often marked handled while the last word is still theirs — «grazie» needs no
	answer — and reading the state off the last message would have reopened it
	the next time anything at all touched the record.
	"""
	for doctype, name in also_the_person(reference_doctype, reference_name):
		frappe.db.set_value(
			doctype,
			name,
			{"conversation_status": OPEN, "conversation_snoozed_until": None},
			update_modified=False,
		)


def on_message(doc, method: str | None = None) -> None:
	"""A WhatsApp or SMS message was written."""
	quietly(doc.get("reference_doctype"), doc.get("reference_name"))
	if they_wrote(doc) and doc.get("reference_doctype") in RECORDS:
		quiet(reopen, doc.reference_doctype, doc.reference_name)


def on_communication(doc, method: str | None = None) -> None:
	"""An email was written. Only real correspondence, not automated notices."""
	if doc.get("communication_type") != "Communication":
		return
	quietly(doc.get("reference_doctype"), doc.get("reference_name"))
	if they_wrote(doc) and doc.get("reference_doctype") in RECORDS:
		quiet(reopen, doc.reference_doctype, doc.reference_name)


# --- how many are still waiting ----------------------------------------------

SEEN = "When seen"
ANSWERED = "When answered"


def badge_clears() -> str:
	"""What makes the count go away: opening the conversation, or replying.

	Two defensible answers, so it is a setting rather than an argument. Opening
	is what a mailbox means by read; replying is what a customer means by it.
	"""
	chosen = frappe.db.get_single_value("FCRM Settings", "conversation_badge_clears")
	return ANSWERED if chosen == ANSWERED else SEEN


def cutoff_field() -> str:
	return "last_answered_on" if badge_clears() == ANSWERED else "conversation_seen_until"


def is_waiting(reference_doctype: str, reference_name: str, values: dict | None = None) -> bool:
	"""Is somebody still waiting on an answer from us?

	Kept as a stored flag rather than worked out when the list is drawn, because
	«show me the ones still waiting» has to be a filter the list can run — over
	every person, not over the twenty on screen. It is a comparison between two
	dates, so refreshing it for a whole site is one statement.
	"""
	values = dict(values or {})
	if not values:
		values = (
			frappe.db.get_value(
				reference_doctype,
				reference_name,
				[
					"last_conversation_direction",
					"last_conversation_on",
					"last_answered_on",
					"conversation_seen_until",
				],
				as_dict=True,
			)
			or {}
		)
	if values.get("last_conversation_direction") != "Incoming":
		return False
	said_on = values.get("last_conversation_on")
	if not said_on:
		return False
	cutoff = values.get(cutoff_field())
	return not cutoff or said_on > cutoff


def refresh_waiting_flags() -> None:
	"""Redo the flag on every person, after the setting that defines it changed.

	One statement per doctype: what counts as waiting is a comparison between
	two columns, so there is nothing to walk.
	"""
	cutoff = cutoff_field()
	for doctype in RECORDS:
		frappe.db.sql(  # nosemgrep: frappe-sql-format-injection — RECORDS is ours, nothing is interpolated from input
			f"""
			update `tab{doctype}`
			set conversation_unread = case
				when last_conversation_direction = 'Incoming'
					and last_conversation_on is not null
					and (`{cutoff}` is null or last_conversation_on > `{cutoff}`)
				then 1 else 0 end
			"""
		)
	frappe.db.commit()  # nosemgrep: frappe-manual-commit — enqueued job and patch: no request will commit this


@frappe.whitelist()
def unread(records: list | str | None = None) -> dict:
	"""How many messages each of these people is still waiting on.

	Keyed `"<doctype>:<name>"`, and only the ones with something waiting are in
	it — a row missing from the answer has nothing outstanding.

	Counted rather than stored, because the cutoff moves: the same conversation
	is unread or not depending on a setting, and a stored counter would have to
	be rewritten on every record the day somebody changes it.
	"""
	records = frappe.parse_json(records) if isinstance(records, str) else (records or [])
	wanted: set[tuple[str, str]] = set()
	for entry in records:
		doctype, name = (
			entry if isinstance(entry, list | tuple) else (entry.get("doctype"), entry.get("name"))
		)
		if doctype in RECORDS and name:
			wanted.add((doctype, name))
	if not wanted:
		return {}

	field = cutoff_field()
	cutoffs: dict[tuple[str, str], str | None] = {}
	by_doctype: dict[str, list[str]] = {}
	for doctype, name in wanted:
		by_doctype.setdefault(doctype, []).append(name)
	for doctype, names in by_doctype.items():
		if not frappe.has_permission(doctype, "read"):
			continue
		for row in frappe.get_all(
			doctype, filters={"name": ["in", names]}, fields=["name", field], limit_page_length=0
		):
			cutoffs[(doctype, row.name)] = row.get(field)
	if not cutoffs:
		return {}

	# every record whose messages count towards one of these people, and which
	# person each of them is. A deal's messages are the person's messages.
	counts_towards: dict[tuple[str, str], tuple[str, str]] = {}
	for person in cutoffs:
		for record in scope(*person):
			counts_towards[record] = person

	# one sweep per channel rather than one per person: the earliest cutoff on
	# the page bounds the query, and each message is then weighed against the
	# cutoff of the person it belongs to. A person never seen has no cutoff at
	# all, and then nothing can be left out.
	values = list(cutoffs.values())
	since = None if any(value is None for value in values) else min(values, default=None)

	tally: dict[str, int] = {}
	for spec in available_channels().values():
		filters = belongs_to(list(counts_towards))
		filters[spec["direction"]] = spec["incoming"]
		if spec["doctype"] == "Communication":
			filters["communication_type"] = "Communication"
		if since:
			filters["creation"] = [">", since]
		for row in frappe.get_all(
			spec["doctype"],
			filters=filters,
			fields=["reference_doctype", "reference_name", "creation"],
			limit_page_length=0,
		):
			person = counts_towards.get((row.reference_doctype, row.reference_name))
			if not person:
				continue
			mine = cutoffs[person]
			if mine and row.creation <= mine:
				continue
			key = f"{person[0]}:{person[1]}"
			tally[key] = tally.get(key, 0) + 1
	return tally


def also_the_person(reference_doctype: str, reference_name: str) -> set[tuple[str, str]]:
	"""This record, and the person it is a deal of — never `None`."""
	both = {(reference_doctype, reference_name)}
	person = person_of(reference_doctype, reference_name)
	if person:
		both.add(person)
	return both


# What a conversation row is made of. Fixed rather than configurable: these are
# not columns somebody chose to see, they are the row itself.
ROW = (
	"name",
	"lead_name",
	"first_name",
	"last_name",
	"image",
	"organization",
	"mobile_no",
	"last_conversation_on",
	"last_conversation_channel",
	"last_conversation_direction",
	"last_conversation_preview",
	"conversation_unread",
	"conversation_status",
	"conversation_snoozed_until",
	"conversation_assigned_to",
)


@frappe.whitelist()
def people(
	search: str = "",
	state: str = "all",
	waiting: bool | int | str = False,
	filters: dict | str | None = None,
	limit: int = 30,
) -> list[dict]:
	"""The column of people beside a record: a chat list, so it behaves like one.

	`get_data` cannot serve this. A search across a name, a company and a phone
	number is an OR across three columns, and that is not something a list of
	AND filters can say — so somebody typing a surname would be told there is
	nobody, because the surname is not in the field the filter happened to pick.

	The order is the other reason. Sorting by `last_conversation_on` alone leaves
	everybody who has never written in a heap, in whatever order the database
	feels like: the list looked shuffled, because for most of it it was. Whoever
	wrote last comes first; the rest fall back to when they were last touched,
	which is at least an order somebody can predict.
	"""
	frappe.has_permission("CRM Lead", "read", throw=True)

	conditions = frappe.parse_json(filters) if isinstance(filters, str) else dict(filters or {})
	conditions.update(STATES.get(state or "all", STATES["all"]))
	if waiting in (True, 1, "1", "true", "True"):
		conditions["conversation_unread"] = 1

	or_conditions = {}
	search = (search or "").strip()
	if search:
		like = f"%{search}%"
		or_conditions = {
			"lead_name": ["like", like],
			"organization": ["like", like],
			"mobile_no": ["like", like],
			"email": ["like", like],
		}

	return frappe.get_list(
		"CRM Lead",
		fields=list(ROW),
		filters=conditions,
		or_filters=or_conditions,
		order_by="last_conversation_on desc, modified desc",
		limit_page_length=min(int(limit), 200),
	)


OPEN = "Open"
HANDLED = "Handled"

# The four questions asked of a list of conversations, and the filter each one is.
# Kept here rather than in the browser so «open» means the same thing to the list,
# to the count above it and to anything that asks later.
STATES = {
	"open": {"conversation_status": OPEN, "conversation_snoozed_until": ["is", "not set"]},
	"handled": {"conversation_status": HANDLED},
	"snoozed": {"conversation_snoozed_until": ["is", "set"]},
	"all": {},
}


def wake_the_snoozed() -> int:
	"""Bring back the conversations whose moment has come.

	Cleared on a schedule rather than read as «snoozed until now is past»,
	because the second way makes every list ask two questions about two columns
	for every row. Emptied, the field says exactly what it means: this one is
	parked. What is not parked is simply not.
	"""
	woken = 0
	for doctype in RECORDS:
		woken += frappe.db.sql(  # nosemgrep: frappe-sql-format-injection — RECORDS is ours; the cutoff is bound with %s
			f"""
			update `tab{doctype}`
			set conversation_snoozed_until = null
			where conversation_snoozed_until is not null
			  and conversation_snoozed_until <= %s
			""",
			(now(),),
		)
	frappe.db.commit()  # nosemgrep: frappe-manual-commit — hourly scheduler job, no request to commit it
	return woken


@frappe.whitelist(methods=["POST"])
def set_state(
	reference_doctype: str,
	reference_name: str,
	state: str = OPEN,
	until: str | None = None,
	assign_to: str | None = None,
) -> dict:
	"""Dealt with, parked, or back on the pile.

	One endpoint for the three, because they are one decision — what happens to
	this conversation now — and three endpoints would let a conversation be
	handled *and* snoozed, which is two answers to a question with one.
	"""
	if reference_doctype not in RECORDS:
		frappe.throw(frappe._("Not a conversation"), frappe.ValidationError)
	frappe.has_permission(reference_doctype, "write", doc=reference_name, throw=True)

	values = {"conversation_status": OPEN, "conversation_snoozed_until": None}
	if state == HANDLED:
		values["conversation_status"] = HANDLED
		# handled means read: leaving a count on something somebody has just
		# closed would be the badge arguing with the person
		values["conversation_seen_until"] = now()
		values["conversation_seen_by"] = frappe.session.user
		values["conversation_unread"] = 0
	elif state == "Snoozed":
		if not until:
			frappe.throw(frappe._("Say until when."), frappe.ValidationError)
		values["conversation_snoozed_until"] = until

	if assign_to is not None:
		values["conversation_assigned_to"] = assign_to or None

	for doctype, name in also_the_person(reference_doctype, reference_name):
		frappe.db.set_value(doctype, name, values, update_modified=False)
	return {"state": values["conversation_status"], "until": values["conversation_snoozed_until"]}


@frappe.whitelist(methods=["POST"])
def mark_seen(reference_doctype: str, reference_name: str) -> dict:
	"""Somebody opened this conversation. Everything said until now is seen."""
	if reference_doctype not in RECORDS:
		frappe.throw(frappe._("Not a conversation"), frappe.ValidationError)
	frappe.has_permission(reference_doctype, "read", doc=reference_name, throw=True)
	seen = now()
	values = {"conversation_seen_until": seen, "conversation_seen_by": frappe.session.user}
	# under the other setting, opening a conversation is not what settles it:
	# the person is still waiting until somebody writes back
	if badge_clears() == SEEN:
		values["conversation_unread"] = 0
	# and on the person, when it was opened from one of their deals: the badge
	# that was showing is theirs
	for doctype, name in also_the_person(reference_doctype, reference_name):
		frappe.db.set_value(doctype, name, values, update_modified=False)
	return {"seen_until": seen}


@frappe.whitelist(methods=["POST"])
def mark_unread(reference_doctype: str, reference_name: str) -> dict:
	"""Put it back in the pile — the one way to undo the line above."""
	if reference_doctype not in RECORDS:
		frappe.throw(frappe._("Not a conversation"), frappe.ValidationError)
	frappe.has_permission(reference_doctype, "read", doc=reference_name, throw=True)
	for doctype, name in also_the_person(reference_doctype, reference_name):
		frappe.db.set_value(
			doctype,
			name,
			{"conversation_seen_until": None, "conversation_seen_by": None},
			update_modified=False,
		)
		frappe.db.set_value(
			doctype, name, "conversation_unread", 1 if is_waiting(doctype, name) else 0, update_modified=False
		)
	return {"seen_until": None}
