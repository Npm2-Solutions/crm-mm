# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""SMS and email: the two other channels a conversation runs on.

SMS is offered when Twilio is on. Email is always there: every site sends and
receives it, filed on a person or a deal (automated messages are not counted —
they are the system talking, not the team).
"""

from __future__ import annotations

from frappe import _, _lt

from crm.dashboard import charts
from crm.dashboard.context import Context
from crm.dashboard.queries import channel, owned_records, per_bucket, per_day, two_periods
from crm.dashboard.registry import widget

INBOX = {"name": "Conversations"}


def traffic(ctx: Context, key: str, direction: str, *criteria) -> tuple[float, float]:
	chan = channel(key)
	table = chan.table
	return two_periods(
		ctx,
		table,
		table.creation,
		*chan.base(),
		chan.is_incoming() if direction == "in" else chan.is_outgoing(),
		owned_records(ctx, table.reference_doctype, table.reference_name),
		*criteria,
	)


def trend(ctx: Context, key: str):
	chan = channel(key)
	table = chan.table
	owned = owned_records(ctx, table.reference_doctype, table.reference_name)
	received = per_bucket(ctx, per_day(ctx, table, table.creation, *chan.base(), chan.is_incoming(), owned))
	sent = per_bucket(ctx, per_day(ctx, table, table.creation, *chan.base(), chan.is_outgoing(), owned))
	return charts.trend(
		ctx.buckets,
		ctx.grain,
		[
			charts.series("received", _("Received"), charts.fill(ctx.buckets, received)),
			charts.series("sent", _("Sent"), charts.fill(ctx.buckets, sent)),
		],
	)


# -- SMS -----------------------------------------------------------------------


@widget(
	"sms_received",
	category="sms",
	kind="number",
	title=_lt("SMS received"),
	description=_lt("Text messages people sent you"),
	requires=("sms",),
)
def sms_received(ctx: Context):
	return charts.number(*traffic(ctx, "sms", "in"), route=INBOX)


@widget(
	"sms_sent",
	category="sms",
	kind="number",
	title=_lt("SMS sent"),
	description=_lt("Text messages the team and the automations sent"),
	requires=("sms",),
)
def sms_sent(ctx: Context):
	return charts.number(*traffic(ctx, "sms", "out"), route=INBOX)


@widget(
	"sms_failed",
	category="sms",
	kind="number",
	title=_lt("SMS not delivered"),
	description=_lt("Text messages that failed or were not delivered"),
	requires=("sms",),
)
def sms_failed(ctx: Context):
	table = channel("sms").table
	return charts.number(
		*traffic(ctx, "sms", "out", table.status.isin(["Failed", "Undelivered"])), negative_is_better=True
	)


@widget(
	"sms_trend",
	category="sms",
	kind="axis",
	title=_lt("SMS over time"),
	description=_lt("Text messages received and sent"),
	size=(10, 8),
	requires=("sms",),
)
def sms_trend(ctx: Context):
	return trend(ctx, "sms")


# -- email ---------------------------------------------------------------------


@widget(
	"emails_received",
	category="email",
	kind="number",
	title=_lt("Emails received"),
	description=_lt("Emails from people and deals that landed in the CRM"),
)
def emails_received(ctx: Context):
	return charts.number(*traffic(ctx, "email", "in"), route=INBOX)


@widget(
	"emails_sent",
	category="email",
	kind="number",
	title=_lt("Emails sent"),
	description=_lt("Emails the team sent to people and deals"),
)
def emails_sent(ctx: Context):
	return charts.number(*traffic(ctx, "email", "out"), route=INBOX)


@widget(
	"emails_trend",
	category="email",
	kind="axis",
	title=_lt("Email over time"),
	description=_lt("Emails received and sent"),
	size=(10, 8),
)
def emails_trend(ctx: Context):
	return trend(ctx, "email")
