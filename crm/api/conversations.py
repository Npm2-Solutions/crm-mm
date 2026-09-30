# Copyright (c) 2026, NPM2 Solutions Srl and contributors
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

And read is one moment, with everything that depends on it happening in it. A
conversation becomes read when somebody here says so — the button, a reply
written from the composer, marking it handled — and never because it was
opened. Then, and only then, the badge goes for everybody, who read it and when
is written down, and, where the site has asked for it, WhatsApp is told: the blue
ticks on the customer's phone. Looking is not reading, on either side of the chat.
"""

import html
import re
from datetime import date, datetime

import frappe
from frappe.utils import add_to_date, cint, get_datetime, now, now_datetime

from crm.scheduling.timeutils import to_system_naive

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
		# the title of the line is the one part of this handler that depends on what
		# was passed in, and not every callable carries a `__name__`: a `partial`, a
		# callable object, a mock standing in for one of ours. Asking for it plainly
		# made the handler raise while it was handling — which is the single thing
		# this function exists not to do, and it would have taken the message down
		# after all, in production as readily as in a test
		called = getattr(what, "__name__", None) or type(what).__name__
		frappe.log_error(frappe.get_traceback(), f"Conversations: {called} did not run")


def quietly(reference_doctype: str, reference_name: str) -> None:
	"""`remember`, and it can never take a message down with it."""
	quiet(remember, reference_doctype, reference_name)


def they_wrote(doc) -> bool:
	"""Did this arrive from them, rather than leave from us?"""
	if doc.doctype == "Communication":
		return doc.get("sent_or_received") == "Received"
	return doc.get("type") == "Incoming"


def on_the_pile(reference_doctype: str, reference_name: str) -> None:
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
			{
				"conversation_status": OPEN,
				"conversation_snoozed_until": None,
				# and unread, which is now a fact rather than a calculation: it
				# goes only when somebody says they have read it
				"conversation_unread": 1,
			},
			update_modified=False,
		)


def on_message(doc, method: str | None = None) -> None:
	"""A WhatsApp or SMS message was written."""
	quietly(doc.get("reference_doctype"), doc.get("reference_name"))
	if they_wrote(doc) and doc.get("reference_doctype") in RECORDS:
		quiet(on_the_pile, doc.reference_doctype, doc.reference_name)


def on_communication(doc, method: str | None = None) -> None:
	"""An email was written. Only real correspondence, not automated notices."""
	if doc.get("communication_type") != "Communication":
		return
	quietly(doc.get("reference_doctype"), doc.get("reference_name"))
	if they_wrote(doc) and doc.get("reference_doctype") in RECORDS:
		quiet(on_the_pile, doc.reference_doctype, doc.reference_name)


# --- how many are still waiting ----------------------------------------------


@frappe.whitelist()
def unread(records: list | str | None = None) -> dict:
	"""How many messages each of these people is still waiting on.

	Keyed `"<doctype>:<name>"`, and only the ones with something waiting are in
	it — a row missing from the answer has nothing outstanding.

	Counted rather than stored, because the cutoff moves: the same conversation
	is unread or not depending on a setting, and a stored counter would have to
	be rewritten on every record the day somebody changes it.

	Only for the ones marked unread. The flag is the fact — a message arriving
	sets it, somebody reading clears it — and the number is how many arrived
	since anybody last read it. Counting past the flag put a number on rows the
	header called read. And one marked unread again with nothing new since has
	the flag and no number: a dot on the row, not a count of everything they
	ever wrote.
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

	field = "conversation_seen_until"
	cutoffs: dict[tuple[str, str], str | None] = {}
	by_doctype: dict[str, list[str]] = {}
	for doctype, name in wanted:
		by_doctype.setdefault(doctype, []).append(name)
	for doctype, names in by_doctype.items():
		if not frappe.has_permission(doctype, "read"):
			continue
		for row in frappe.get_all(
			doctype,
			filters={"name": ["in", names], "conversation_unread": 1},
			fields=["name", field],
			limit_page_length=0,
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
	"email",
	"last_conversation_on",
	"last_conversation_channel",
	"last_conversation_direction",
	"last_conversation_preview",
	"conversation_unread",
	# who read it and when: the header says so, rather than a bare «read»
	"conversation_seen_until",
	"conversation_seen_by",
	"conversation_status",
	"conversation_snoozed_until",
	"conversation_assigned_to",
)


@frappe.whitelist()
def people(
	search: str = "",
	view: str = "open",
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
	search = (search or "").strip()
	# A name somebody types is a person they want, not a person filed where they
	# happen to be standing. Searching inside the current view is how you look
	# for a customer, find nothing, and conclude the CRM has lost them — when
	# they were simply marked as dealt with last week.
	if not search:
		conditions.update(conditions_for(view or "open"))
		# and «only unread» narrows a view, not a search, for the same reason: a
		# name typed is somebody wanted, read or not
		if waiting in (True, 1, "1", "true", "True"):
			conditions["conversation_unread"] = 1

	or_conditions = {}
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
		order_by=NEWEST_FIRST,
		limit_page_length=min(int(limit), 200),
	)


@frappe.whitelist()
def person(name: str) -> dict:
	"""One row of the list, for a conversation opened from a link.

	The list holds the forty people at the top of the view that is open, and a
	link — from the dashboard, a notification, a colleague — can name anybody.
	Looking them up only among the rows on screen is how the header came to say
	«CRM-LEAD-2026-00128» where a name goes, over a conversation with somebody
	whose name the CRM knows perfectly well.
	"""
	if not frappe.db.exists("CRM Lead", name):
		frappe.throw(frappe._("This conversation no longer exists"), frappe.DoesNotExistError)
	frappe.has_permission("CRM Lead", "read", doc=name, throw=True)
	return frappe.db.get_value("CRM Lead", name, list(ROW), as_dict=True) or {}


OPEN = "Open"
HANDLED = "Handled"

# Whoever spoke last first — and «spoke» counts both sides, because a
# conversation you answered five minutes ago is more alive than one nobody has
# touched since April.
#
# And nothing ahead of that. Unread used to come first, which made reading a
# thing that moved rows: you marked a conversation read and it dropped below
# everything still unread — out of sight, and the row you were on was no longer
# where you had left it. A row moves when somebody says something, the way it
# does in every messenger, and never because of a button somebody here pressed.
# What is unread is marked on the row, and has a filter of its own.
NEWEST_FIRST = "last_conversation_on desc, modified desc"

# The views. Four, because a fifth would be a way of asking something these
# four already answer — and a menu you have to read is a menu that slows you
# down every morning.
#
# They are all the same list under the same order. The base one is what a chat
# app shows: everything still going on, whoever spoke last at the top. The other
# three exist because without them a button leads nowhere — «gestita» and
# «rimanda» would make a conversation vanish with no way back to it.
VIEWS = ("open", "unanswered", "snoozed", "handled")

LIVE = {"conversation_status": OPEN, "conversation_snoozed_until": ["is", "not set"]}


def conditions_for(view: str) -> dict:
	"""The filter one view is.

	An unrecognised name is an error rather than the base list. Falling back to
	«open» is how a renamed view passes unnoticed: the caller asks for a pile,
	silently gets everything still going on, and nothing says so — the failure
	develop had already paid for once, when a stale `open` was answered with the
	whole address book. Wrong name, loud answer.
	"""
	if view == "unanswered":
		# they spoke last and nobody answered. Not «unread»: you can have read
		# something this morning and still owe the answer, and that one is the
		# one that costs money. Unread is not a view but a filter over any of
		# them — the unread among the open, among the parked, among the settled.
		return {**LIVE, "last_conversation_direction": "Incoming"}
	if view == "snoozed":
		return {"conversation_snoozed_until": ["is", "set"]}
	if view == "handled":
		return {"conversation_status": HANDLED}
	if view != "open":
		frappe.throw(frappe._("Unknown conversation view {0}. Known: {1}").format(view, ", ".join(VIEWS)))
	return dict(LIVE)


# The same four in SQL, so the numbers above the list can be counted in one pass
# over the table instead of one query per view.
COUNTABLE = {
	"open": "conversation_status = 'Open' and conversation_snoozed_until is null",
	"unanswered": (
		"conversation_status = 'Open' and conversation_snoozed_until is null "
		"and last_conversation_direction = 'Incoming'"
	),
	"snoozed": "conversation_snoozed_until is not null",
	"handled": "conversation_status = 'Handled'",
}


@frappe.whitelist()
def counts() -> dict:
	"""How many are in each view, and how many of those are unread, in one sweep.

	One query with a sum per question rather than one query per view: they are
	eight questions about the same rows, and asking the table eight times to draw
	one menu is seven times too many. The unread ones are `<view>_unread`, for the
	number on the filter that narrows the open view to them.
	"""
	if not frappe.has_permission("CRM Lead", "read"):
		return {}
	sums = []
	for view, clause in COUNTABLE.items():
		sums.append(f"sum(case when {clause} then 1 else 0 end) as `{view}`")
		sums.append(
			f"sum(case when ({clause}) and conversation_unread = 1 then 1 else 0 end) as `{view}_unread`"
		)
	row = frappe.db.sql(f"select {', '.join(sums)} from `tabCRM Lead`", as_dict=True)  # nosemgrep
	return {key: int(value or 0) for key, value in (row[0] if row else {}).items()}


def wake_the_snoozed() -> int:
	"""Bring back the conversations whose moment has come.

	Cleared on a schedule rather than read as «snoozed until now is past»,
	because the second way makes every list ask two questions about two columns
	for every row. Emptied, the field says exactly what it means: this one is
	parked. What is not parked is simply not.
	"""
	cutoff = now()
	woken = 0
	for doctype in RECORDS:
		# a null moment never satisfies `<=`, so the ones that were never parked
		# are already out; asking for the names first is what makes the count true
		due = frappe.get_all(
			doctype,
			filters={"conversation_snoozed_until": ["<=", cutoff]},
			pluck="name",
		)
		for name in due:
			# one row at a time, by name: a filter dict with an `in` reached nothing,
			# and a count that says it woke them while they stay parked is worse than
			# slow. There are only ever the ones whose hour has just come.
			frappe.db.set_value(doctype, name, "conversation_snoozed_until", None, update_modified=False)
		woken += len(due)
	frappe.db.commit()  # nosemgrep: frappe-manual-commit — hourly scheduler job, no request to commit it
	return woken


def _a_moment(until) -> datetime:
	"""Read `until` as a moment this site can store, or refuse it.

	The column is a naive Datetime, so anything carrying an offset has to be
	brought into the site's own clock first: a browser sending an ISO string
	ending in Z means a real instant, and storing its digits unchanged would park
	the conversation at an hour nobody asked for. Whatever we cannot read at all
	is refused in the same words as naming no moment — better a plain no than a
	conversation left on the pile while the answer says it was parked.
	"""
	try:
		moment = get_datetime(until) if until else None
	except Exception:
		moment = None
	if not moment:
		frappe.throw(frappe._("Say until when."), frappe.ValidationError)
	if moment.tzinfo is not None:
		moment = to_system_naive(moment)
	return moment


@frappe.whitelist(methods=["POST"])
def set_state(
	reference_doctype: str,
	reference_name: str,
	state: str = OPEN,
	until: str | datetime | date | None = None,
	assign_to: str | None = None,
) -> dict:
	"""Dealt with, parked, or back on the pile.

	One endpoint for the three, because they are one decision — what happens to
	this conversation now — and three endpoints would let a conversation be
	handled *and* snoozed, which is two answers to a question with one.

	`until` is a moment, and a moment arrives here in more than one shape: a
	string from the browser, a `datetime` from `add_to_date`, a `date` from
	`getdate`. Frappe enforces these annotations on the function itself whenever
	it runs inside a request or under test, so naming only the browser's shape
	did not document a contract — it made an ordinary Python call to a function
	of ours illegal, and left every caller to remember to stringify a date first.

	Handled means read, too: a count left on something somebody has just closed
	would be the badge arguing with the person — so it is one of the moments the
	blue ticks can go. Only the move *into* handled reads it. Handing a settled
	conversation to a colleague comes through here as well, and giving something
	away is not reading it.
	"""
	if reference_doctype not in RECORDS:
		frappe.throw(frappe._("Not a conversation"), frappe.ValidationError)
	frappe.has_permission(reference_doctype, "write", doc=reference_name, throw=True)

	settled = frappe.db.get_value(reference_doctype, reference_name, "conversation_status") == HANDLED

	values = {"conversation_status": OPEN, "conversation_snoozed_until": None}
	if state == HANDLED:
		values["conversation_status"] = HANDLED
	elif state == "Snoozed":
		# settled into one shape here rather than stored as it came, so what is parked
		# — and what comes back in the answer — does not depend on who did the asking
		values["conversation_snoozed_until"] = _a_moment(until)

	if assign_to is not None:
		values["conversation_assigned_to"] = assign_to or None

	for doctype, name in also_the_person(reference_doctype, reference_name):
		frappe.db.set_value(doctype, name, values, update_modified=False)

	answer = {"state": values["conversation_status"], "until": values["conversation_snoozed_until"]}
	if state == HANDLED and not settled and is_unread(reference_doctype, reference_name):
		answer.update(read_now(reference_doctype, reference_name))
	return answer


# --- read ----------------------------------------------------------------------


def is_unread(reference_doctype: str, reference_name: str) -> bool:
	"""Is anything here still unread — on this record, or on the person it is a deal of?"""
	return any(
		cint(frappe.db.get_value(doctype, name, "conversation_unread"))
		for doctype, name in also_the_person(reference_doctype, reference_name)
	)


def read_now(reference_doctype: str, reference_name: str) -> dict:
	"""Read, now, by whoever is asking — and WhatsApp told, where that is wanted.

	On the record and on its person, when it is one of their deals: the badge
	that was showing is theirs.
	"""
	seen = now()
	who = frappe.session.user
	values = {"conversation_seen_until": seen, "conversation_seen_by": who, "conversation_unread": 0}
	for doctype, name in also_the_person(reference_doctype, reference_name):
		frappe.db.set_value(doctype, name, values, update_modified=False)
	return {"seen_until": seen, "seen_by": who, "receipts": tell_whatsapp(reference_doctype, reference_name)}


@frappe.whitelist(methods=["POST"])
def mark_read(reference_doctype: str, reference_name: str) -> dict:
	"""Read, and off the pile. Only ever because somebody said so.

	It used to happen by itself, the moment a conversation was opened — and that
	is how a badge becomes noise: you glance at a chat to see who it was, the
	count goes, and the thing you had not dealt with is indistinguishable from
	the thing you had. Looking is not dealing with it.

	Said by the button, by marking it handled, and by answering from the
	composer — nobody replies to what they have not read. Not by a message an
	automation sends: nobody read anything for that one.

	With nothing new since it was last read, nothing happens: the second reply in
	a row does not make its writer the one who read the conversation, and does
	not tell WhatsApp twice.
	"""
	if reference_doctype not in RECORDS:
		frappe.throw(frappe._("Not a conversation"), frappe.ValidationError)
	frappe.has_permission(reference_doctype, "read", doc=reference_name, throw=True)
	if not is_unread(reference_doctype, reference_name):
		seen = (
			frappe.db.get_value(
				reference_doctype,
				reference_name,
				["conversation_seen_until", "conversation_seen_by"],
				as_dict=True,
			)
			or {}
		)
		return {
			"seen_until": seen.get("conversation_seen_until"),
			"seen_by": seen.get("conversation_seen_by"),
			"receipts": 0,
		}
	return read_now(reference_doctype, reference_name)


@frappe.whitelist(methods=["POST"])
def mark_unread(reference_doctype: str, reference_name: str) -> dict:
	"""Back on the pile: a flag for the team, not a rewind.

	Only the flag. The moment it was read stays where it was, so the number on
	the row is still what arrived since then — nothing, until they write again —
	instead of every message they ever sent, which is what forgetting the moment
	used to count. And the blue ticks, if they went, stay: a receipt cannot be
	taken back from somebody's phone.
	"""
	if reference_doctype not in RECORDS:
		frappe.throw(frappe._("Not a conversation"), frappe.ValidationError)
	frappe.has_permission(reference_doctype, "read", doc=reference_name, throw=True)
	for doctype, name in also_the_person(reference_doctype, reference_name):
		frappe.db.set_value(doctype, name, "conversation_unread", 1, update_modified=False)
	return {"unread": 1}


@frappe.whitelist(methods=["POST"])
def restore(reference_doctype: str, reference_name: str, was: dict | str) -> dict:
	"""Undo: the conversation as it was before the last decision about it.

	«Handled» and «later» take a row out of the list, and a button that makes
	something leave needs a way back that is not a hunt through another view.
	`was` is the row as the screen had it before — its decision, whether it was
	read and by whom, and when anything was last said. That last one is the
	guard: if they wrote in the meantime, the conversation is open and unread
	because of it, and putting the old state back would bury their message under
	«handled». Then nothing is undone, and the answer says why.

	What it cannot put back are the blue ticks: they are on the customer's phone.
	"""
	if reference_doctype not in RECORDS:
		frappe.throw(frappe._("Not a conversation"), frappe.ValidationError)
	frappe.has_permission(reference_doctype, "write", doc=reference_name, throw=True)
	was = frappe.parse_json(was) if isinstance(was, str) else dict(was or {})

	heard = frappe.db.get_value(reference_doctype, reference_name, "last_conversation_on")
	before = was.get("last_conversation_on")
	if heard and (not before or get_datetime(heard) > get_datetime(before)):
		frappe.throw(
			frappe._("Something new was said in the meantime, so it stays as it is now."),
			frappe.ValidationError,
		)

	status = was.get("conversation_status") or OPEN
	if status not in (OPEN, HANDLED):
		frappe.throw(frappe._("Not a conversation state: {0}").format(status), frappe.ValidationError)
	parked = was.get("conversation_snoozed_until")
	seen = get_datetime(was["conversation_seen_until"]) if was.get("conversation_seen_until") else None
	who = was.get("conversation_seen_by")
	values = {
		"conversation_status": status,
		"conversation_snoozed_until": _a_moment(parked) if parked else None,
		"conversation_unread": 1 if cint(was.get("conversation_unread")) else 0,
		# never ahead of now: a moment in the future would hide what has not arrived yet
		"conversation_seen_until": min(seen, now_datetime()) if seen else None,
		"conversation_seen_by": who if who and frappe.db.exists("User", who) else None,
	}
	for doctype, name in also_the_person(reference_doctype, reference_name):
		frappe.db.set_value(doctype, name, values, update_modified=False)
	return {"state": status, "until": values["conversation_snoozed_until"]}


# --- the blue ticks ------------------------------------------------------------
#
# What the customer sees on their own phone, so it goes at the moment the CRM
# says the conversation was read, and at no other. It used to go when a chat was
# *opened*, while the badge stayed — opening is not reading — so the customer
# was told somebody had read them while the CRM said nobody had: two answers to
# one question, given to two people, at two different moments.

# How frappe_whatsapp writes it down on a message, so a receipt it sent and one
# sent from here read the same.
READ_BY_US = "marked as read"

# Meta takes a receipt for a message up to thirty days old, and asking about
# older ones only fills the error log with its refusals.
RECEIPTS_REACH_DAYS = 30

RECEIPT_TIMEOUT = 15


def receipts_wanted() -> bool:
	"""Has this site asked for the blue ticks, and can it send them?"""
	return bool(frappe.db.get_single_value("FCRM Settings", "whatsapp_read_receipts")) and bool(
		frappe.db.exists("DocType", "WhatsApp Message")
	)


def still_unacknowledged(where: list[tuple[str, str]]) -> list[str]:
	"""The newest thing they wrote on WhatsApp, per number of ours, not yet marked read.

	One per number, because WhatsApp marks everything before it in the same chat
	as read too. Twenty receipts for twenty messages say the same thing twenty
	times; the one for the last says it once — and the old way, twenty requests
	in a row inside somebody's click, was the click waiting on Meta twenty times.
	"""
	base = {
		**belongs_to(where),
		"type": "Incoming",
		"message_id": ["is", "set"],
		"creation": [">", add_to_date(now_datetime(), days=-RECEIPTS_REACH_DAYS)],
	}
	if frappe.get_meta("WhatsApp Message").has_field("whatsapp_account"):
		accounts = {
			account or ""
			for account in frappe.get_all("WhatsApp Message", filters=base, pluck="whatsapp_account")
		}
		per_number = [{**base, "whatsapp_account": account or ["is", "not set"]} for account in accounts]
	else:
		per_number = [base]

	latest = []
	for filters in per_number:
		rows = frappe.get_all(
			"WhatsApp Message",
			filters=filters,
			fields=["name", "status"],
			order_by="creation desc",
			limit=1,
		)
		if rows and rows[0].status != READ_BY_US and rows[0].name not in latest:
			latest.append(rows[0].name)
	return latest


def tell_whatsapp(reference_doctype: str, reference_name: str) -> int:
	"""Queue the blue ticks for this person, if the site wants them. How many.

	The person's whole conversation, their deals included, because that is the
	conversation that was just read.

	Queued, and after the commit: this runs inside somebody's click, and a round
	trip to Meta is not something a click should wait on — nor something to send
	for a read the database then rolled back.
	"""
	if not receipts_wanted():
		return 0
	person = person_of(reference_doctype, reference_name) or (reference_doctype, reference_name)
	latest = still_unacknowledged(scope(*person))
	for message in latest:
		frappe.enqueue(
			"crm.api.conversations.send_read_receipt",
			queue="short",
			message=message,
			enqueue_after_commit=True,
		)
	return len(latest)


def whatsapp_account(name: str | None):
	"""The account a message came in on, or the one incoming messages default to."""
	if not frappe.db.exists("DocType", "WhatsApp Account"):
		return None
	if not (name and frappe.db.exists("WhatsApp Account", name)):
		name = frappe.db.get_value("WhatsApp Account", {"is_default_incoming": 1}, "name")
	return frappe.get_cached_doc("WhatsApp Account", name) if name else None


def send_read_receipt(message: str) -> bool:
	"""Tell WhatsApp we have read up to this message. Runs in the background.

	Our own request rather than the method on the message: that one saves the
	message to write the answer down, and saving an incoming message runs what
	runs when one arrives — its number is looked up again, which can file it on
	another record than the chat it is shown in. Writing the status straight to
	the row says the same thing and nothing else.
	"""
	fields = ["type", "message_id", "status"]
	if frappe.get_meta("WhatsApp Message").has_field("whatsapp_account"):
		fields.append("whatsapp_account")
	row = frappe.db.get_value("WhatsApp Message", message, fields, as_dict=True)
	if not row or row.type != "Incoming" or not row.message_id or row.status == READ_BY_US:
		return False
	account = whatsapp_account(row.get("whatsapp_account"))
	if not account:
		return False

	import requests

	try:
		answer = requests.post(
			f"{account.url}/{account.version}/{account.phone_id}/messages",
			headers={"Authorization": f"Bearer {account.get_password('token')}"},
			json={"messaging_product": "whatsapp", "status": "read", "message_id": row.message_id},
			timeout=RECEIPT_TIMEOUT,
		)
		told = answer.status_code == 200 and bool((answer.json() or {}).get("success"))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "WhatsApp: read receipt not sent")
		return False
	if not told:
		frappe.log_error(
			f"{message}: {answer.status_code} {answer.text[:500]}", "WhatsApp: read receipt refused"
		)
		return False
	frappe.db.set_value("WhatsApp Message", message, "status", READ_BY_US, update_modified=False)
	return True
