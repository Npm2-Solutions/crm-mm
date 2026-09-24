# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Calls: how many, how many missed, how long, and who still needs a call back.

Offered when a telephony provider (Twilio, Exotel) is on. A call belongs to the
agent who made it (``caller``) or took it (``receiver``). "Missed" is an incoming
call nobody picked up — no answer, declined, or hung up before anyone did; the
same reading as the call log in the app (``utils/callLog.js``).

Call-backs live on the missed call itself (``crm.telephony.callbacks``), and the
power dialer records an outcome for every number it rings.
"""

from __future__ import annotations

from collections import defaultdict

import frappe
from frappe import _, _lt
from frappe.query_builder import DocType
from frappe.query_builder.functions import Avg, Count

from crm.dashboard import charts
from crm.dashboard.context import Context, where
from crm.dashboard.queries import per_bucket, per_day, total, two_periods, weekday_hour
from crm.dashboard.registry import Option, widget
from crm.dashboard.widgets.conversations import full_names, hour_labels, weekday_labels

Call = DocType("CRM Call Log")
Session = DocType("CRM Dial Session")
Entry = DocType("CRM Dial Session Entry")

CALLS = ("calls",)
MISSED = ("No Answer", "Busy", "Canceled", "Failed")
ROWS = Option("limit", _lt("Rows"), type="int", default=6, min=3, max=20)
CALL_LOGS = {"name": "Call Logs"}
DIALER = {"name": "Dialer"}


def handled_by(ctx: Context):
	"""The call was made or taken by one of the people counted.

	An incoming call nobody picked up has no receiver: it belongs to the whole
	team, so it shows up for everyone — a missed call is everybody's problem.
	"""
	if ctx.everyone:
		return None
	owners = ctx.owners or ["<nobody>"]
	return ((Call.type == "Outgoing") & Call.caller.isin(owners)) | (
		(Call.type == "Incoming") & (Call.receiver.isin(owners) | Call.receiver.isnull())
	)


def missed():
	return (Call.type == "Incoming") & Call.status.isin(MISSED)


@widget(
	"calls_total",
	category="calls",
	kind="number",
	title=_lt("Calls"),
	description=_lt("Calls made and received in the period"),
	requires=CALLS,
)
def calls_total(ctx: Context):
	return charts.number(*two_periods(ctx, Call, Call.creation, handled_by(ctx)), route=CALL_LOGS)


@widget(
	"calls_incoming",
	category="calls",
	kind="number",
	title=_lt("Incoming calls"),
	description=_lt("Calls people made to you"),
	requires=CALLS,
)
def calls_incoming(ctx: Context):
	return charts.number(
		*two_periods(ctx, Call, Call.creation, Call.type == "Incoming", handled_by(ctx)), route=CALL_LOGS
	)


@widget(
	"calls_outgoing",
	category="calls",
	kind="number",
	title=_lt("Outgoing calls"),
	description=_lt("Calls the team made"),
	requires=CALLS,
)
def calls_outgoing(ctx: Context):
	return charts.number(
		*two_periods(ctx, Call, Call.creation, Call.type == "Outgoing", handled_by(ctx)), route=CALL_LOGS
	)


@widget(
	"calls_missed",
	category="calls",
	kind="number",
	title=_lt("Missed calls"),
	description=_lt("Incoming calls nobody answered"),
	requires=CALLS,
)
def calls_missed(ctx: Context):
	return charts.number(
		*two_periods(ctx, Call, Call.creation, missed(), handled_by(ctx)),
		negative_is_better=True,
		route=CALL_LOGS,
	)


@widget(
	"calls_answer_rate",
	category="calls",
	kind="number",
	title=_lt("Answer rate"),
	description=_lt("Share of incoming calls somebody answered"),
	requires=CALLS,
)
def calls_answer_rate(ctx: Context):
	def rate(previous: bool):
		incoming = total(Call, Call.type == "Incoming", ctx.within(Call.creation, previous), handled_by(ctx))
		answered = total(
			Call,
			Call.type == "Incoming",
			Call.status == "Completed",
			ctx.within(Call.creation, previous),
			handled_by(ctx),
		)
		return charts.ratio(answered, incoming)

	now = rate(False)
	return charts.number(now or 0, rate(True), format="percent", compare="points", progress=now or 0)


@widget(
	"calls_average_duration",
	category="calls",
	kind="number",
	title=_lt("Average call"),
	description=_lt("Average length of the calls that connected"),
	requires=CALLS,
)
def calls_average_duration(ctx: Context):
	def average(previous: bool):
		query = frappe.qb.from_(Call).select(Avg(Call.duration))
		query = where(
			query,
			Call.status == "Completed",
			Call.duration > 0,
			ctx.within(Call.creation, previous),
			handled_by(ctx),
		)
		return float(query.run()[0][0] or 0)

	return charts.number(average(False), average(True) or None, format="duration")


@widget(
	"calls_talk_time",
	category="calls",
	kind="number",
	title=_lt("Time on the phone"),
	description=_lt("Total length of the calls that connected"),
	requires=CALLS,
)
def calls_talk_time(ctx: Context):
	return charts.number(
		*two_periods(
			ctx, Call, Call.creation, Call.status == "Completed", handled_by(ctx), value=Call.duration
		),
		format="duration",
	)


@widget(
	"calls_trend",
	category="calls",
	kind="axis",
	title=_lt("Calls over time"),
	description=_lt("Incoming, outgoing and missed calls"),
	size=(10, 8),
	requires=CALLS,
)
def calls_trend(ctx: Context):
	scope = handled_by(ctx)
	incoming = per_bucket(ctx, per_day(ctx, Call, Call.creation, Call.type == "Incoming", scope))
	outgoing = per_bucket(ctx, per_day(ctx, Call, Call.creation, Call.type == "Outgoing", scope))
	lost = per_bucket(ctx, per_day(ctx, Call, Call.creation, missed(), scope))
	return charts.trend(
		ctx.buckets,
		ctx.grain,
		[
			charts.series("incoming", _("Incoming"), charts.fill(ctx.buckets, incoming), color="blue"),
			charts.series("outgoing", _("Outgoing"), charts.fill(ctx.buckets, outgoing), color="darkgreen"),
			charts.series("missed", _("Missed"), charts.fill(ctx.buckets, lost), color="red", dashed=True),
		],
	)


@widget(
	"calls_by_agent",
	category="calls",
	kind="axis",
	title=_lt("Calls per person"),
	description=_lt("Calls made and taken by each member of the team"),
	size=(10, 8),
	requires=CALLS,
	managers_only=True,
)
def calls_by_agent(ctx: Context):
	counts: dict[str, dict[str, float]] = defaultdict(lambda: {"outgoing": 0, "incoming": 0})
	for kind, column in (("outgoing", Call.caller), ("incoming", Call.receiver)):
		query = frappe.qb.from_(Call).select(column.as_("user"), Count("*").as_("n"))
		query = where(
			query,
			Call.type == kind.capitalize(),
			column.isnotnull(),
			ctx.within(Call.creation),
			ctx.owned(column),
		).groupby(column)
		for row in query.run(as_dict=True):
			counts[row.user][kind] += float(row.n or 0)
	names = full_names(list(counts))
	rows = sorted(
		({"user": names.get(user) or user, **values} for user, values in counts.items()),
		key=lambda row: row["outgoing"] + row["incoming"],
		reverse=True,
	)[:12]
	# the same colours as "Calls over time"
	return charts.bars(
		rows,
		label_key="user",
		lines=[("incoming", _("Incoming"), "blue"), ("outgoing", _("Outgoing"), "darkgreen")],
		stacked=True,
	)


@widget(
	"calls_heatmap",
	category="calls",
	kind="heatmap",
	title=_lt("When people call"),
	description=_lt("Incoming calls by day of the week and hour"),
	size=(20, 7),
	requires=CALLS,
)
def calls_heatmap(ctx: Context):
	counts = weekday_hour(ctx, Call, Call.creation, Call.type == "Incoming", handled_by(ctx))
	return charts.heatmap(counts, x_labels=hour_labels(), y_labels=weekday_labels())


# -- call-backs and missed calls -----------------------------------------------


def callbacks_scope(ctx: Context):
	if ctx.everyone:
		return None
	owners = ctx.owners or ["<nobody>"]
	return Call.callback_by.isin(owners) | Call.callback_by.isnull()


@widget(
	"callbacks_pending",
	category="calls",
	kind="number",
	title=_lt("Calls to return"),
	description=_lt("Missed calls waiting for a call back"),
	live=True,
	requires=CALLS,
)
def callbacks_pending(ctx: Context):
	return charts.number(total(Call, Call.callback_status == "Pending", callbacks_scope(ctx)), route=DIALER)


def callback_list(ctx: Context):
	Lead = DocType("CRM Lead")
	query = (
		frappe.qb.from_(Call)
		.left_join(Lead)
		.on((Call.reference_doctype == "CRM Lead") & (Call.reference_docname == Lead.name))
		.select(
			Call.name,
			Call["from"].as_("number"),
			Call.callback_due,
			Call.callback_attempts,
			Call.creation,
			Lead.name.as_("person"),
			Lead.lead_name,
		)
	)
	query = where(query, Call.callback_status == "Pending", callbacks_scope(ctx))
	rows = (
		query.orderby(Call.callback_due, order=frappe.qb.asc).limit(ctx.option("limit", 6)).run(as_dict=True)
	)
	items = []
	for row in rows:
		overdue = row.callback_due and row.callback_due < ctx.now
		item = {
			"title": row.lead_name or row.number,
			"subtitle": row.number if row.lead_name else None,
			"time": str(row.callback_due or row.creation),
			"icon": "phone",
			"route": {"name": "Lead", "params": {"leadId": row.person}} if row.person else DIALER,
		}
		if overdue:
			item["badge"] = {"label": _("Late"), "color": "red"}
		elif row.callback_attempts:
			item["badge"] = {"label": _("Attempt {0}").format(row.callback_attempts + 1), "color": "orange"}
		items.append(item)
	return charts.listing(
		items,
		empty=_("Nobody is waiting for a call back"),
		more={"label": _("Open the dialer"), "route": DIALER},
		total=int(total(Call, Call.callback_status == "Pending", callbacks_scope(ctx))),
	)


@widget(
	"callbacks_list",
	category="calls",
	kind="list",
	title=_lt("Call backs due"),
	description=_lt("Missed calls to return, the most urgent first"),
	size=(10, 8),
	live=True,
	requires=CALLS,
	options=(ROWS,),
)
def callbacks_list(ctx: Context):
	return callback_list(ctx)


widget(
	"my_callbacks",
	category="calls",
	kind="list",
	title=_lt("My call backs"),
	description=_lt("The calls you have to return"),
	size=(10, 8),
	live=True,
	scope="me",
	requires=CALLS,
	options=(ROWS,),
)(callback_list)


# -- power dialer --------------------------------------------------------------


def dispositions(ctx: Context) -> dict[str, float]:
	query = (
		frappe.qb.from_(Entry)
		.join(Session)
		.on(Entry.parent == Session.name)
		.select(Entry.disposition, Count("*").as_("n"))
		.where(Entry.parenttype == "CRM Dial Session")
		.where(Entry.status == "Done")
	)
	query = where(query, ctx.within(Session.creation), ctx.owned(Session.agent)).groupby(Entry.disposition)
	return {row.disposition or "": float(row.n or 0) for row in query.run(as_dict=True)}


@widget(
	"dialer_outcomes",
	category="calls",
	kind="donut",
	title=_lt("Dialer outcomes"),
	description=_lt("What happened to the numbers rung in dialer sessions"),
	size=(10, 8),
	requires=CALLS,
)
def dialer_outcomes(ctx: Context):
	return charts.donut(
		[(_(key) if key else _("No outcome"), value) for key, value in dispositions(ctx).items()],
		other_label=_("Other"),
	)


@widget(
	"dialer_calls",
	category="calls",
	kind="number",
	title=_lt("Numbers dialed"),
	description=_lt("Numbers worked through in dialer sessions"),
	requires=CALLS,
)
def dialer_calls(ctx: Context):
	def done(previous: bool):
		query = (
			frappe.qb.from_(Entry)
			.join(Session)
			.on(Entry.parent == Session.name)
			.select(Count("*"))
			.where(Entry.parenttype == "CRM Dial Session")
			.where(Entry.status == "Done")
		)
		query = where(query, ctx.within(Session.creation, previous), ctx.owned(Session.agent))
		return float(query.run()[0][0] or 0)

	return charts.number(done(False), done(True), route=DIALER)


@widget(
	"dialer_reached_rate",
	category="calls",
	kind="number",
	title=_lt("Reached in the dialer"),
	description=_lt("Share of dialed numbers where somebody answered"),
	requires=CALLS,
)
def dialer_reached_rate(ctx: Context):
	counts = dispositions(ctx)
	dialed = sum(counts.values())
	unreached = sum(counts.get(key, 0) for key in ("No Answer", "Voicemail", "Wrong Number"))
	rate = charts.ratio(dialed - unreached, dialed)
	return charts.number(rate or 0, format="percent", progress=rate or 0)
