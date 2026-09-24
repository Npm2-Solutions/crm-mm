# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""WhatsApp: traffic, delivery, templates and what the team answers from the phone.

Only offered when a WhatsApp number is connected (``features``). Messages live in
the WhatsApp app's ``WhatsApp Message``; its ``status`` is free text written by
three different writers — "Success", "sent", "delivered", "read", "Failed"… — so
it is always read case-insensitively and folded into five states.

``written_on_the_phone`` marks the messages the team typed in the WhatsApp
Business app (coexistence). A site that installed WhatsApp after that column was
introduced may not have it yet: those widgets then say so instead of guessing.
"""

from __future__ import annotations

from collections import defaultdict

import frappe
from frappe import _, _lt
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count, Lower, Min

from crm.dashboard import charts
from crm.dashboard.context import Context, where
from crm.dashboard.queries import channel, owned_records, per_bucket, per_day, total, two_periods
from crm.dashboard.registry import Option, widget

WHATSAPP = ("whatsapp",)
ROWS = Option("limit", _lt("Rows"), type="int", default=6, min=3, max=20)
INBOX = {"name": "Conversations"}

READ, DELIVERED, SENT, FAILED, PENDING = "read", "delivered", "sent", "failed", "pending"


def status_key(value: str | None) -> str:
	value = (value or "").strip().lower()
	if value == "read":
		return READ
	if value == "delivered":
		return DELIVERED
	if value in ("sent", "success"):
		return SENT
	if value == "failed":
		return FAILED
	return PENDING


def status_labels() -> dict[str, str]:
	return {
		READ: _("Read"),
		DELIVERED: _("Delivered"),
		SENT: _("Sent"),
		FAILED: _("Not delivered"),
		PENDING: _("Waiting for Meta"),
	}


def messages():
	return channel("whatsapp").table


def base(ctx: Context) -> list:
	table = messages()
	return [*channel("whatsapp").base(), owned_records(ctx, table.reference_doctype, table.reference_name)]


def has_phone_flag() -> bool:
	return frappe.get_meta("WhatsApp Message").has_field("written_on_the_phone")


def from_the_crm():
	"""Outgoing messages sent by the CRM, not typed on the phone."""
	table = messages()
	if not has_phone_flag():
		return None
	return (table.written_on_the_phone == 0) | table.written_on_the_phone.isnull()


@widget(
	"whatsapp_received",
	category="whatsapp",
	kind="number",
	title=_lt("WhatsApp received"),
	description=_lt("Messages people sent you on WhatsApp"),
	requires=WHATSAPP,
)
def whatsapp_received(ctx: Context):
	table = messages()
	return charts.number(
		*two_periods(ctx, table, table.creation, *base(ctx), table.type == "Incoming"), route=INBOX
	)


@widget(
	"whatsapp_sent",
	category="whatsapp",
	kind="number",
	title=_lt("WhatsApp sent"),
	description=_lt("Messages the team sent on WhatsApp, from the CRM or the phone"),
	requires=WHATSAPP,
)
def whatsapp_sent(ctx: Context):
	table = messages()
	return charts.number(
		*two_periods(ctx, table, table.creation, *base(ctx), table.type == "Outgoing"), route=INBOX
	)


def first_contacts(ctx: Context, previous: bool) -> int:
	"""People whose first WhatsApp message ever arrived in the period."""
	table = messages()
	low, high = ctx.span(previous)
	wrote = frappe.qb.from_(table).select(table.reference_name)
	wrote = where(
		wrote, *base(ctx), table.type == "Incoming", (table.creation >= low) & (table.creation < high)
	)
	first = Min(table.creation)
	query = (
		frappe.qb.from_(table)
		.select(table.reference_doctype, table.reference_name, first.as_("first_at"))
		.where(table.type == "Incoming")
		.where(table.reference_name.isin(wrote))
		.groupby(table.reference_doctype, table.reference_name)
		.having((first >= low) & (first < high))
	)
	query = where(query, *base(ctx))
	return len(query.run())


@widget(
	"whatsapp_new_conversations",
	category="whatsapp",
	kind="number",
	title=_lt("New on WhatsApp"),
	description=_lt("People who wrote to you on WhatsApp for the first time"),
	requires=WHATSAPP,
)
def whatsapp_new_conversations(ctx: Context):
	return charts.number(first_contacts(ctx, False), first_contacts(ctx, True), route=INBOX)


def outgoing_by_status(ctx: Context, previous: bool = False, *criteria) -> dict[str, float]:
	table = messages()
	status = Lower(table.status)
	query = frappe.qb.from_(table).select(status.as_("status"), Count("*").as_("n")).groupby(status)
	query = where(
		query,
		*base(ctx),
		table.type == "Outgoing",
		ctx.within(table.creation, previous),
		from_the_crm(),
		*criteria,
	)
	counts: dict[str, float] = defaultdict(float)
	for row in query.run(as_dict=True):
		counts[status_key(row.status)] += float(row.n or 0)
	return counts


def read_rate(counts: dict[str, float]) -> float | None:
	return charts.ratio(counts.get(READ, 0), sum(counts.values()))


@widget(
	"whatsapp_read_rate",
	category="whatsapp",
	kind="number",
	title=_lt("WhatsApp read rate"),
	description=_lt("Share of the messages sent from the CRM that were read"),
	requires=WHATSAPP,
)
def whatsapp_read_rate(ctx: Context):
	now = read_rate(outgoing_by_status(ctx))
	return charts.number(
		now or 0,
		read_rate(outgoing_by_status(ctx, True)),
		format="percent",
		compare="points",
		progress=now or 0,
	)


@widget(
	"whatsapp_failed",
	category="whatsapp",
	kind="number",
	title=_lt("WhatsApp not delivered"),
	description=_lt("Messages Meta refused or could not deliver"),
	requires=WHATSAPP,
)
def whatsapp_failed(ctx: Context):
	now = outgoing_by_status(ctx).get(FAILED, 0)
	before = outgoing_by_status(ctx, True).get(FAILED, 0)
	return charts.number(now, before, negative_is_better=True, route=INBOX)


@widget(
	"whatsapp_status",
	category="whatsapp",
	kind="donut",
	title=_lt("What happened to the messages sent"),
	description=_lt("Messages sent from the CRM: read, delivered, sent, not delivered"),
	size=(10, 8),
	requires=WHATSAPP,
)
def whatsapp_status(ctx: Context):
	labels = status_labels()
	counts = outgoing_by_status(ctx)
	# still on its way, whether Meta has it yet or not
	on_the_way = counts.get(SENT, 0) + counts.get(PENDING, 0)
	return charts.donut(
		[
			(labels[READ], counts.get(READ, 0), "darkgreen"),
			(labels[DELIVERED], counts.get(DELIVERED, 0), "blue"),
			(labels[SENT], on_the_way, "amber"),
			(labels[FAILED], counts.get(FAILED, 0), "pink"),
		]
	)


@widget(
	"whatsapp_trend",
	category="whatsapp",
	kind="axis",
	title=_lt("WhatsApp over time"),
	description=_lt("WhatsApp messages received and sent"),
	size=(10, 8),
	requires=WHATSAPP,
)
def whatsapp_trend(ctx: Context):
	table = messages()
	received = per_bucket(ctx, per_day(ctx, table, table.creation, *base(ctx), table.type == "Incoming"))
	sent = per_bucket(ctx, per_day(ctx, table, table.creation, *base(ctx), table.type == "Outgoing"))
	return charts.trend(
		ctx.buckets,
		ctx.grain,
		[
			charts.series("received", _("Received"), charts.fill(ctx.buckets, received)),
			charts.series("sent", _("Sent"), charts.fill(ctx.buckets, sent)),
		],
	)


@widget(
	"whatsapp_templates",
	category="whatsapp",
	kind="table",
	title=_lt("Templates sent"),
	description=_lt("Each approved template: how often it went out and how often it was read"),
	size=(10, 8),
	requires=WHATSAPP,
	options=(ROWS,),
)
def whatsapp_templates(ctx: Context):
	table = messages()
	status = Lower(table.status)
	query = frappe.qb.from_(table).select(table.template, status.as_("status"), Count("*").as_("n"))
	query = where(
		query,
		*base(ctx),
		table.type == "Outgoing",
		table.template.isnotnull(),
		table.template != "",
		ctx.within(table.creation),
	).groupby(table.template, status)
	by_template: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
	for row in query.run(as_dict=True):
		by_template[row.template][status_key(row.status)] += float(row.n or 0)
	rows = []
	for template, counts in by_template.items():
		sent = sum(counts.values())
		rows.append(
			{
				"template": template,
				"sent": sent,
				"delivered": charts.ratio(counts[READ] + counts[DELIVERED], sent),
				"read": charts.ratio(counts[READ], sent),
			}
		)
	rows.sort(key=lambda row: row["sent"], reverse=True)
	return charts.table(
		[
			{"key": "template", "label": _("Template"), "format": "text"},
			{"key": "sent", "label": _("Sent"), "format": "number"},
			{"key": "delivered", "label": _("Delivered"), "format": "percent"},
			{"key": "read", "label": _("Read"), "format": "percent"},
		],
		rows[: ctx.option("limit", 6)],
		empty=_("No template sent in this period"),
	)


@widget(
	"whatsapp_from_phone",
	category="whatsapp",
	kind="number",
	title=_lt("Answered from the phone"),
	description=_lt("Share of WhatsApp replies typed in the WhatsApp Business app instead of the CRM"),
	requires=WHATSAPP,
	keywords=("coexistence", "business app"),
)
def whatsapp_from_phone(ctx: Context):
	if not has_phone_flag():
		return charts.number(0, hint=_("This site does not record it yet"))
	table = messages()

	def share(previous: bool):
		outgoing = total(table, *base(ctx), table.type == "Outgoing", ctx.within(table.creation, previous))
		phone = total(
			table,
			*base(ctx),
			table.type == "Outgoing",
			table.written_on_the_phone == 1,
			ctx.within(table.creation, previous),
		)
		return charts.ratio(phone, outgoing)

	now = share(False)
	return charts.number(now or 0, share(True), format="percent", compare="points", progress=now or 0)


@widget(
	"whatsapp_failed_list",
	category="whatsapp",
	kind="list",
	title=_lt("WhatsApp to resend"),
	description=_lt("The latest messages that did not reach the person"),
	size=(10, 8),
	requires=WHATSAPP,
	options=(ROWS,),
)
def whatsapp_failed_list(ctx: Context):
	table = messages()
	Lead = DocType("CRM Lead")
	Deal = DocType("CRM Deal")
	query = (
		frappe.qb.from_(table)
		.left_join(Deal)
		.on((table.reference_doctype == "CRM Deal") & (table.reference_name == Deal.name))
		.left_join(Lead)
		.on(
			((table.reference_doctype == "CRM Lead") & (table.reference_name == Lead.name))
			| ((table.reference_doctype == "CRM Deal") & (Deal.lead == Lead.name))
		)
		.select(table.name, table.message, table.creation, table.to, Lead.name.as_("person"), Lead.lead_name)
	)
	query = where(
		query,
		*base(ctx),
		table.type == "Outgoing",
		Lower(table.status) == "failed",
		ctx.within(table.creation),
	)
	rows = query.orderby(table.creation, order=frappe.qb.desc).limit(ctx.option("limit", 6)).run(as_dict=True)
	items = []
	for row in rows:
		item = {
			"title": row.lead_name or row.to or _("Unknown"),
			"subtitle": frappe.utils.strip_html(row.message or "")[:120],
			"time": str(row.creation),
			"icon": "whatsapp",
			"badge": {"label": _("Not delivered"), "color": "red"},
		}
		if row.person:
			item["route"] = {"name": "Conversations", "query": {"person": row.person}}
		items.append(item)
	return charts.listing(items, empty=_("Every message was delivered"))
