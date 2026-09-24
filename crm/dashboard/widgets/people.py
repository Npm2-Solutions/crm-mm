# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""People: who arrived, from where, and whether they became a deal.

A ``CRM Lead`` is a person (docs/progetto-ghl/21): permanent, one per human,
created by a form, an ad, a booking or an unknown number writing on WhatsApp.
So "new people" counts humans who reached you for the first time — not
requests, which are deals.
"""

from __future__ import annotations

import frappe
from frappe import _, _lt
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count, Sum

from crm.dashboard import charts
from crm.dashboard.context import Context, where
from crm.dashboard.queries import grouped, per_bucket, per_day, two_periods
from crm.dashboard.registry import Option, widget

Lead = DocType("CRM Lead")
Deal = DocType("CRM Deal")

PEOPLE_ROUTE = {"name": "Leads"}
ROWS = Option("limit", _lt("Rows"), type="int", default=6, min=3, max=20)

TOUCH = Option(
	"touch",
	_lt("Credit"),
	choices=(("first", _lt("First contact")), ("last", _lt("Last contact"))),
	default="first",
)


@widget(
	"total_leads",
	category="people",
	kind="number",
	title=_lt("New people"),
	description=_lt("People who reached you for the first time in the period"),
	keywords=("leads", "contacts"),
)
def total_leads(ctx: Context):
	now, before = two_periods(ctx, Lead, Lead.creation, ctx.owned(Lead.lead_owner))
	return charts.number(now, before, route=PEOPLE_ROUTE)


@widget(
	"people_with_deal",
	category="people",
	kind="number",
	title=_lt("People with a deal"),
	description=_lt("Of the people who arrived in the period, the share that has a deal"),
	keywords=("conversion", "qualified"),
)
def people_with_deal(ctx: Context):
	def rate(previous: bool):
		query = frappe.qb.from_(Lead).select(Count("*").as_("people"), Sum(Lead.converted).as_("with_deal"))
		row = where(query, ctx.within(Lead.creation, previous), ctx.owned(Lead.lead_owner)).run(as_dict=True)[
			0
		]
		return charts.ratio(row.with_deal, row.people)

	now = rate(False)
	return charts.number(now or 0, rate(True), format="percent", compare="points", progress=now or 0)


@widget(
	"people_trend",
	category="people",
	kind="axis",
	title=_lt("New people over time"),
	description=_lt("How many people reached you, day by day"),
	size=(10, 8),
)
def people_trend(ctx: Context):
	people = per_bucket(ctx, per_day(ctx, Lead, Lead.creation, ctx.owned(Lead.lead_owner)))
	return charts.trend(
		ctx.buckets,
		ctx.grain,
		[charts.series("people", _("New people"), charts.fill(ctx.buckets, people), type="bar")],
	)


@widget(
	"leads_by_source",
	category="people",
	kind="donut",
	title=_lt("People by source"),
	description=_lt("Where the people who arrived in the period came from"),
	size=(10, 8),
)
def leads_by_source(ctx: Context):
	rows = grouped(Lead, Lead.source, ctx.within(Lead.creation), ctx.owned(Lead.lead_owner))
	return charts.donut(rows, other_label=_("Other"), empty_label=_("Not set"))


@widget(
	"people_by_channel",
	category="people",
	kind="axis",
	title=_lt("People by channel"),
	description=_lt("New people by the kind of channel that brought them: ads, search, social, direct…"),
	size=(10, 8),
	options=(TOUCH,),
	keywords=("attribution", "utm", "marketing"),
)
def people_by_channel(ctx: Context):
	column = Lead.last_touch_category if ctx.option("touch") == "last" else Lead.first_touch_category
	rows = grouped(Lead, column, ctx.within(Lead.creation), ctx.owned(Lead.lead_owner), limit=12)
	return charts.bars(
		[{"channel": _(key) if key else _("Unknown"), "n": value} for key, value in rows],
		label_key="channel",
		lines=[("n", _("People"))],
	)


@widget(
	"people_recent",
	category="people",
	kind="list",
	title=_lt("Latest people"),
	description=_lt("The most recent people to reach you"),
	size=(10, 8),
	options=(ROWS,),
)
def people_recent(ctx: Context):
	query = frappe.qb.from_(Lead).select(
		Lead.name,
		Lead.lead_name,
		Lead.organization,
		Lead.source,
		Lead.lead_owner,
		Lead.creation,
		Lead.converted,
	)
	query = where(query, ctx.within(Lead.creation), ctx.owned(Lead.lead_owner))
	rows = query.orderby(Lead.creation, order=frappe.qb.desc).limit(ctx.option("limit", 6)).run(as_dict=True)
	items = []
	for row in rows:
		item = {
			"title": row.lead_name or row.name,
			"subtitle": row.organization or row.source,
			"time": str(row.creation),
			"route": {"name": "Lead", "params": {"leadId": row.name}},
		}
		if row.converted:
			item["badge"] = {"label": _("Has a deal"), "color": "green"}
		if row.lead_owner:
			item["user"] = row.lead_owner
		items.append(item)
	return charts.listing(
		items,
		empty=_("Nobody new in this period"),
		more={"label": _("All people"), "route": PEOPLE_ROUTE},
	)


def sla_rows(ctx: Context, previous: bool = False):
	"""First-response SLA outcomes on people and deals created in the period."""
	fulfilled = failed = 0
	seconds: list[float] = []
	for table, owner in ((Lead, Lead.lead_owner), (Deal, Deal.deal_owner)):
		query = frappe.qb.from_(table).select(table.sla_status, table.first_response_time)
		query = where(query, ctx.within(table.creation, previous), table.sla.isnotnull(), ctx.owned(owner))
		for row in query.run(as_dict=True):
			if row.sla_status == "Fulfilled":
				fulfilled += 1
			elif row.sla_status == "Failed":
				failed += 1
			if row.first_response_time:
				seconds.append(float(row.first_response_time))
	return fulfilled, failed, seconds


@widget(
	"sla_compliance",
	category="people",
	kind="number",
	title=_lt("Answered within SLA"),
	description=_lt("Share of first responses given within the service level agreement"),
	requires=("sla",),
)
def sla_compliance(ctx: Context):
	fulfilled, failed, _seconds = sla_rows(ctx)
	fulfilled_before, failed_before, _seconds_before = sla_rows(ctx, True)
	now = charts.ratio(fulfilled, fulfilled + failed)
	before = charts.ratio(fulfilled_before, fulfilled_before + failed_before)
	return charts.number(now or 0, before, format="percent", compare="points", progress=now or 0)


@widget(
	"sla_first_response",
	category="people",
	kind="number",
	title=_lt("First response time"),
	description=_lt("Average time to the first response, in working hours, as the SLA measures it"),
	requires=("sla",),
)
def sla_first_response(ctx: Context):
	def average(values):
		return sum(values) / len(values) if values else 0

	now = average(sla_rows(ctx)[2])
	before = average(sla_rows(ctx, True)[2])
	return charts.number(now, before or None, format="duration", negative_is_better=True)
