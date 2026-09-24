# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Conversations: who is waiting for an answer, and how fast answers come.

Two kinds of numbers. The inbox state — waiting, snoozed, handled — is stored on
the person (``crm.api.conversations``) and describes the present, so those
widgets are live. The traffic — messages in and out, per channel, per hour —
comes from the messages themselves and follows the period.

Every channel counts: WhatsApp (when its app is installed), SMS and email filed
on a person or a deal. Reactions are not messages.
"""

from __future__ import annotations

import datetime
import statistics
from collections import defaultdict

import frappe
from frappe import _, _lt
from frappe.query_builder import DocType
from frappe.query_builder.functions import Coalesce, Count

from crm.dashboard import charts
from crm.dashboard.context import Context, where
from crm.dashboard.queries import (
	channels,
	owned_records,
	people_owned,
	per_bucket,
	per_day,
	total,
	two_periods,
	weekday_hour,
)
from crm.dashboard.registry import Option, widget

Lead = DocType("CRM Lead")
Deal = DocType("CRM Deal")

INBOX = {"name": "Conversations"}
ROWS = Option("limit", _lt("Rows"), type="int", default=6, min=3, max=20)
CHANNEL_LABELS = {"whatsapp": "WhatsApp", "sms": "SMS", "email": "Email"}


def open_now():
	return (Lead.conversation_status == "Open") & Lead.conversation_snoozed_until.isnull()


def waiting_now():
	return open_now() & (Lead.conversation_unread == 1)


@widget(
	"conversations_waiting",
	category="conversations",
	kind="number",
	title=_lt("Waiting for an answer"),
	description=_lt("People whose last message nobody has answered yet"),
	live=True,
	keywords=("inbox", "unread", "unanswered"),
)
def conversations_waiting(ctx: Context):
	return charts.number(total(Lead, waiting_now(), people_owned(ctx, Lead)), route=INBOX)


@widget(
	"conversations_open",
	category="conversations",
	kind="number",
	title=_lt("Open conversations"),
	description=_lt("Conversations not yet marked as handled, snoozed ones aside"),
	live=True,
)
def conversations_open(ctx: Context):
	return charts.number(
		total(Lead, open_now(), Lead.last_conversation_on.isnotnull(), people_owned(ctx, Lead)), route=INBOX
	)


@widget(
	"conversations_unassigned",
	category="conversations",
	kind="number",
	title=_lt("Waiting, unassigned"),
	description=_lt("People waiting for an answer that nobody has taken on"),
	live=True,
	managers_only=True,
)
def conversations_unassigned(ctx: Context):
	return charts.number(
		total(Lead, waiting_now(), Lead.conversation_assigned_to.isnull(), people_owned(ctx, Lead)),
		route=INBOX,
	)


@widget(
	"conversations_snoozed",
	category="conversations",
	kind="number",
	title=_lt("Snoozed"),
	description=_lt("Conversations put off until later"),
	live=True,
)
def conversations_snoozed(ctx: Context):
	return charts.number(
		total(Lead, Lead.conversation_snoozed_until.isnotnull(), people_owned(ctx, Lead)), route=INBOX
	)


def waiting_list(ctx: Context):
	limit = ctx.option("limit", 6)
	query = frappe.qb.from_(Lead).select(
		Lead.name,
		Lead.lead_name,
		Lead.last_conversation_on,
		Lead.last_conversation_channel,
		Lead.last_conversation_preview,
		Lead.conversation_assigned_to,
		Lead.lead_owner,
	)
	query = where(query, waiting_now(), people_owned(ctx, Lead))
	rows = query.orderby(Lead.last_conversation_on, order=frappe.qb.asc).limit(limit).run(as_dict=True)
	items = []
	for row in rows:
		channel = (row.last_conversation_channel or "").lower()
		item = {
			"title": row.lead_name or row.name,
			"subtitle": row.last_conversation_preview,
			"time": str(row.last_conversation_on) if row.last_conversation_on else None,
			"icon": channel or "message",
			"route": {"name": "Conversations", "query": {"person": row.name}},
		}
		if row.conversation_assigned_to or row.lead_owner:
			item["user"] = row.conversation_assigned_to or row.lead_owner
		items.append(item)
	return charts.listing(
		items,
		empty=_("Nobody is waiting for an answer"),
		more={"label": _("Open the inbox"), "route": INBOX},
		total=int(total(Lead, waiting_now(), people_owned(ctx, Lead))),
	)


@widget(
	"conversations_waiting_list",
	category="conversations",
	kind="list",
	title=_lt("Longest waiting"),
	description=_lt("People waiting for an answer, the longest wait first"),
	size=(10, 8),
	live=True,
	options=(ROWS,),
)
def conversations_waiting_list(ctx: Context):
	return waiting_list(ctx)


widget(
	"my_conversations",
	category="conversations",
	kind="list",
	title=_lt("My conversations waiting"),
	description=_lt("Your people waiting for an answer"),
	size=(10, 8),
	live=True,
	scope="me",
	options=(ROWS,),
)(waiting_list)


@widget(
	"conversations_by_assignee",
	category="conversations",
	kind="axis",
	title=_lt("Open conversations per person"),
	description=_lt("Who is handling the open conversations, right now"),
	size=(10, 8),
	live=True,
	managers_only=True,
	keywords=("workload",),
)
def conversations_by_assignee(ctx: Context):
	owner = Coalesce(Lead.conversation_assigned_to, Lead.lead_owner)
	query = frappe.qb.from_(Lead).select(owner.as_("user"), Count("*").as_("n"))
	query = where(query, open_now(), Lead.last_conversation_on.isnotnull(), people_owned(ctx, Lead))
	rows = query.groupby(owner).orderby(Count("*"), order=frappe.qb.desc).limit(12).run(as_dict=True)
	names = full_names([row.user for row in rows])
	return charts.bars(
		[{"user": names.get(row.user) or row.user or _("Unassigned"), "n": row.n} for row in rows],
		label_key="user",
		lines=[("n", _("Conversations"))],
	)


# -- traffic ------------------------------------------------------------------


def traffic(ctx: Context, direction: str, previous_too: bool = True) -> tuple[float, float]:
	now = before = 0.0
	for channel in channels():
		table = channel.table
		criteria = [
			*channel.base(),
			channel.is_incoming() if direction == "in" else channel.is_outgoing(),
			owned_records(ctx, table.reference_doctype, table.reference_name),
		]
		a, b = two_periods(ctx, table, table.creation, *criteria)
		now += a
		before += b
	return now, before


@widget(
	"messages_received",
	category="conversations",
	kind="number",
	title=_lt("Messages received"),
	description=_lt("Messages people sent you on every channel"),
)
def messages_received(ctx: Context):
	return charts.number(*traffic(ctx, "in"), route=INBOX)


@widget(
	"messages_sent",
	category="conversations",
	kind="number",
	title=_lt("Messages sent"),
	description=_lt("Messages the team sent on every channel"),
)
def messages_sent(ctx: Context):
	return charts.number(*traffic(ctx, "out"), route=INBOX)


@widget(
	"messages_by_channel",
	category="conversations",
	kind="donut",
	title=_lt("Messages by channel"),
	description=_lt("WhatsApp, SMS and email, sent and received"),
	size=(10, 8),
)
def messages_by_channel(ctx: Context):
	rows = []
	for channel in channels():
		table = channel.table
		count = total(
			table,
			*channel.base(),
			ctx.within(table.creation),
			owned_records(ctx, table.reference_doctype, table.reference_name),
		)
		rows.append((CHANNEL_LABELS[channel.key], count))
	return charts.donut(rows)


@widget(
	"messages_trend",
	category="conversations",
	kind="axis",
	title=_lt("Messages over time"),
	description=_lt("Messages received and sent, on every channel"),
	size=(10, 8),
)
def messages_trend(ctx: Context):
	received: dict = defaultdict(float)
	sent: dict = defaultdict(float)
	for channel in channels():
		table = channel.table
		owned = owned_records(ctx, table.reference_doctype, table.reference_name)
		for day, count in per_day(
			ctx, table, table.creation, *channel.base(), channel.is_incoming(), owned
		).items():
			received[day] += count
		for day, count in per_day(
			ctx, table, table.creation, *channel.base(), channel.is_outgoing(), owned
		).items():
			sent[day] += count
	received, sent = per_bucket(ctx, received), per_bucket(ctx, sent)
	return charts.trend(
		ctx.buckets,
		ctx.grain,
		[
			charts.series("received", _("Received"), charts.fill(ctx.buckets, received)),
			charts.series("sent", _("Sent"), charts.fill(ctx.buckets, sent)),
		],
	)


def weekday_labels() -> list[str]:
	return [_("Mon"), _("Tue"), _("Wed"), _("Thu"), _("Fri"), _("Sat"), _("Sun")]


def hour_labels() -> list[str]:
	return [f"{hour:02d}" for hour in range(24)]


@widget(
	"messages_heatmap",
	category="conversations",
	kind="heatmap",
	title=_lt("When people write to you"),
	description=_lt("Messages received by day of the week and hour"),
	size=(20, 7),
	keywords=("busiest", "hours", "staffing"),
)
def messages_heatmap(ctx: Context):
	counts: dict = defaultdict(float)
	for channel in channels():
		table = channel.table
		owned = owned_records(ctx, table.reference_doctype, table.reference_name)
		for cell, count in weekday_hour(
			ctx, table, table.creation, *channel.base(), channel.is_incoming(), owned
		).items():
			counts[cell] += count
	return charts.heatmap(counts, x_labels=hour_labels(), y_labels=weekday_labels())


# -- how fast answers come ----------------------------------------------------

# looking a little before the period tells whether its first message opened a
# new wait or continued one; looking after it finds the answers that came late
LOOKBACK = datetime.timedelta(days=3)
MAX_MESSAGES = 100_000


def reply_waits(ctx: Context, previous: bool = False) -> tuple[list[float], int]:
	"""Seconds from each wait's first message to the answer, and how many waits got none.

	A wait opens with a message from the person when nothing was pending, and
	closes with the first message back — from the CRM or from the phone. Waits are
	per person: a message filed on one of their deals belongs to the same thread.
	"""
	low, high = ctx.span(previous)
	fetch_high = min(high + LOOKBACK, ctx.now)
	events: list[tuple] = []
	for channel in channels():
		table = channel.table
		query = frappe.qb.from_(table).select(
			table.reference_doctype,
			table.reference_name,
			table.creation,
			channel.is_incoming().as_("incoming"),
		)
		query = where(
			query,
			*channel.base(),
			(table.creation >= low - LOOKBACK) & (table.creation < fetch_high),
			owned_records(ctx, table.reference_doctype, table.reference_name),
		)
		events += query.limit(MAX_MESSAGES).run()

	deal_names = {name for doctype, name, *_rest in events if doctype == "CRM Deal"}
	person_of_deal = {}
	if deal_names:
		person_of_deal = dict(
			frappe.qb.from_(Deal).select(Deal.name, Deal.lead).where(Deal.name.isin(list(deal_names))).run()
		)

	threads: dict[str, list[tuple]] = defaultdict(list)
	for doctype, name, created, incoming in events:
		person = person_of_deal.get(name) if doctype == "CRM Deal" else name
		threads[person or f"{doctype}:{name}"].append((created, bool(incoming)))

	waits: list[float] = []
	unanswered = 0
	for messages in threads.values():
		messages.sort(key=lambda message: message[0])
		waiting_since = None
		for created, incoming in messages:
			if incoming:
				waiting_since = waiting_since or created
			elif waiting_since is not None:
				if low <= waiting_since < high:
					waits.append((created - waiting_since).total_seconds())
				waiting_since = None
		if waiting_since is not None and low <= waiting_since < high:
			unanswered += 1
	return waits, unanswered


@widget(
	"reply_time",
	category="conversations",
	kind="number",
	title=_lt("Reply time"),
	description=_lt("Typical time to answer a person who writes, on every channel (median)"),
	keywords=("response time", "speed"),
)
def reply_time(ctx: Context):
	now, _unanswered = reply_waits(ctx)
	before, _unanswered_before = reply_waits(ctx, True)
	return charts.number(
		statistics.median(now) if now else 0,
		statistics.median(before) if before else None,
		format="duration",
		negative_is_better=True,
	)


REPLY_BUCKETS = (
	(5 * 60, _lt("Under 5 min")),
	(30 * 60, _lt("5–30 min")),
	(60 * 60, _lt("30–60 min")),
	(4 * 3600, _lt("1–4 hours")),
	(24 * 3600, _lt("4–24 hours")),
	(None, _lt("Over a day")),
)


@widget(
	"reply_time_distribution",
	category="conversations",
	kind="axis",
	title=_lt("How fast people get an answer"),
	description=_lt("Waits of the period by how long the answer took, and the ones still unanswered"),
	size=(10, 8),
)
def reply_time_distribution(ctx: Context):
	waits, unanswered = reply_waits(ctx)
	counts = [0] * len(REPLY_BUCKETS)
	for seconds in waits:
		for index, (limit, _label) in enumerate(REPLY_BUCKETS):
			if limit is None or seconds < limit:
				counts[index] += 1
				break
	rows = [
		{"bucket": str(label), "n": count}
		for (_limit, label), count in zip(REPLY_BUCKETS, counts, strict=True)
	]
	rows.append({"bucket": _("No answer yet"), "n": unanswered})
	return charts.bars(rows, label_key="bucket", lines=[("n", _("Conversations"))], horizontal=False)


def full_names(users) -> dict:
	users = [user for user in set(users) if user]
	if not users:
		return {}
	return dict(
		frappe.get_all("User", filters={"name": ("in", users)}, fields=["name", "full_name"], as_list=True)
	)
