# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Deals: what came in, what was won and lost, what is on the table now.

The deal is where the sale lives (docs/progetto-ghl/26): stage, value, owner,
outcome. Amounts are converted to the dashboard currency with the deal's own
exchange rate, as the original dashboard did.

Several ids here (``won_deals``, ``sales_trend``, ``funnel_conversion``…) are the
names the first dashboard saved in its layouts. They keep their name and get the
new answer, so a dashboard saved a year ago opens with the current numbers.
"""

from __future__ import annotations

import datetime
from collections import defaultdict

import frappe
from frappe import _, _lt
from frappe.query_builder import Case, DocType
from frappe.query_builder.functions import Avg, Count, Date, IfNull, Sum
from frappe.utils import add_days, add_months, get_first_day, getdate

from crm.dashboard import charts, periods
from crm.dashboard.context import Context, where
from crm.dashboard.queries import DaysBetween, grouped, per_bucket, per_day, total, two_periods
from crm.dashboard.registry import Option, widget

Deal = DocType("CRM Deal")
Status = DocType("CRM Deal Status")
Lead = DocType("CRM Lead")
Log = DocType("CRM Status Change Log")

CLOSED = ("Won", "Lost")

PIPELINE = Option("pipeline", _lt("Pipeline"), type="pipeline", default="")
MEASURE = Option(
	"measure",
	_lt("Show"),
	choices=(("count", _lt("Number of deals")), ("value", _lt("Value"))),
	default="count",
)
ROWS = Option("limit", _lt("Rows"), type="int", default=6, min=3, max=20)

DEALS_ROUTE = {"name": "Deals"}


def amount(field: str = "deal_value"):
	"""A deal amount in the dashboard currency."""
	rate = Case().when(Deal.exchange_rate > 0, Deal.exchange_rate).else_(1)
	return IfNull(Deal[field], 0) * rate


def open_amount():
	"""What an open deal is worth: its expected value when there is one, else its value."""
	value = (
		Case().when(Deal.expected_deal_value > 0, Deal.expected_deal_value).else_(IfNull(Deal.deal_value, 0))
	)
	return value * Case().when(Deal.exchange_rate > 0, Deal.exchange_rate).else_(1)


def in_pipeline(ctx: Context):
	pipeline = ctx.option("pipeline")
	return (Deal.pipeline == pipeline) if pipeline else None


def with_status(query):
	return query.join(Status).on(Deal.status == Status.name)


def lost_between(low: datetime.datetime, high: datetime.datetime):
	"""Deals that are lost now and got there inside [low, high).

	The moment is the status log's row for entering a Lost stage. Deals moved in
	bulk leave no log, so for those the last change stands in for it.
	"""
	entered = (
		frappe.qb.from_(Log)
		.select(Log.parent)
		.where((Log.parenttype == "CRM Deal") & (Log.from_type == "Lost"))
		.where((Log.from_date >= low) & (Log.from_date < high))
	)
	any_entry = (
		frappe.qb.from_(Log)
		.select(Log.parent)
		.where((Log.parenttype == "CRM Deal") & (Log.from_type == "Lost"))
	)
	return (Status.type == "Lost") & (
		Deal.name.isin(entered)
		| (Deal.name.notin(any_entry) & (Deal.modified >= low) & (Deal.modified < high))
	)


def won_count(ctx: Context, previous: bool = False) -> int:
	query = with_status(frappe.qb.from_(Deal)).select(Count("*"))
	query = where(
		query,
		Status.type == "Won",
		ctx.within_days(Deal.closed_date, previous),
		ctx.owned(Deal.deal_owner),
		in_pipeline(ctx),
	)
	return int(query.run()[0][0] or 0)


def lost_count(ctx: Context, previous: bool = False) -> int:
	query = with_status(frappe.qb.from_(Deal)).select(Count("*"))
	query = where(query, lost_between(*ctx.span(previous)), ctx.owned(Deal.deal_owner), in_pipeline(ctx))
	return int(query.run()[0][0] or 0)


def stage_name(name: str | None) -> str:
	return name or _("No stage")


# -- KPIs -------------------------------------------------------------------


@widget(
	"deals_new",
	category="sales",
	kind="number",
	title=_lt("New deals"),
	description=_lt("Deals opened in the period"),
	options=(PIPELINE,),
	keywords=("opportunities", "created"),
)
def deals_new(ctx: Context):
	now, before = two_periods(ctx, Deal, Deal.creation, ctx.owned(Deal.deal_owner), in_pipeline(ctx))
	return charts.number(now, before, route=DEALS_ROUTE)


@widget(
	"deals_open",
	category="sales",
	kind="number",
	title=_lt("Open deals"),
	description=_lt("Deals not yet won or lost, right now"),
	live=True,
	options=(PIPELINE,),
)
def deals_open(ctx: Context):
	value = total(
		Deal,
		Status.type.notin(CLOSED),
		ctx.owned(Deal.deal_owner),
		in_pipeline(ctx),
		joins=((Status, Deal.status == Status.name),),
	)
	return charts.number(value, route=DEALS_ROUTE)


@widget(
	"won_deals",
	category="sales",
	kind="number",
	title=_lt("Won deals"),
	description=_lt("Deals closed as won in the period"),
	options=(PIPELINE,),
)
def won_deals(ctx: Context):
	return charts.number(won_count(ctx), won_count(ctx, previous=True), route=DEALS_ROUTE)


@widget(
	"deals_lost",
	category="sales",
	kind="number",
	title=_lt("Lost deals"),
	description=_lt("Deals closed as lost in the period"),
	options=(PIPELINE,),
)
def deals_lost(ctx: Context):
	return charts.number(
		lost_count(ctx), lost_count(ctx, previous=True), negative_is_better=True, route=DEALS_ROUTE
	)


@widget(
	"win_rate",
	category="sales",
	kind="number",
	title=_lt("Win rate"),
	description=_lt("Of the deals closed in the period, the share that was won"),
	options=(PIPELINE,),
	keywords=("conversion", "close rate"),
)
def win_rate(ctx: Context):
	won, lost = won_count(ctx), lost_count(ctx)
	won_before, lost_before = won_count(ctx, True), lost_count(ctx, True)
	rate = charts.ratio(won, won + lost)
	before = charts.ratio(won_before, won_before + lost_before)
	return charts.number(rate or 0, before, format="percent", compare="points", progress=rate or 0)


def won_amount(ctx: Context, previous: bool = False, average: bool = False) -> float:
	measure = Avg(amount()) if average else Sum(amount())
	query = with_status(frappe.qb.from_(Deal)).select(measure)
	query = where(
		query,
		Status.type == "Won",
		ctx.within_days(Deal.closed_date, previous),
		ctx.owned(Deal.deal_owner),
		in_pipeline(ctx),
	)
	return float(query.run()[0][0] or 0)


@widget(
	"won_value",
	category="sales",
	kind="number",
	title=_lt("Won revenue"),
	description=_lt("Total value of the deals won in the period"),
	options=(PIPELINE,),
	keywords=("revenue", "sales", "turnover"),
)
def won_value(ctx: Context):
	return charts.number(won_amount(ctx), won_amount(ctx, True), format="currency", route=DEALS_ROUTE)


@widget(
	"average_won_deal_value",
	category="sales",
	kind="number",
	title=_lt("Average won deal"),
	description=_lt("Average value of the deals won in the period"),
	options=(PIPELINE,),
)
def average_won_deal_value(ctx: Context):
	return charts.number(
		won_amount(ctx, average=True), won_amount(ctx, True, average=True), format="currency"
	)


@widget(
	"pipeline_value",
	category="sales",
	kind="number",
	title=_lt("Pipeline value"),
	description=_lt("What the open deals are worth, right now"),
	live=True,
	options=(PIPELINE,),
)
def pipeline_value(ctx: Context):
	value = total(
		Deal,
		Status.type.notin(CLOSED),
		ctx.owned(Deal.deal_owner),
		in_pipeline(ctx),
		value=open_amount(),
		joins=((Status, Deal.status == Status.name),),
	)
	return charts.number(value, format="currency", route=DEALS_ROUTE)


@widget(
	"weighted_pipeline",
	category="sales",
	kind="number",
	title=_lt("Weighted pipeline"),
	description=_lt("Open deals weighted by their probability of closing"),
	live=True,
	options=(PIPELINE,),
	keywords=("forecast", "probability"),
)
def weighted_pipeline(ctx: Context):
	probability = IfNull(Deal.probability, IfNull(Status.probability, 0))
	value = total(
		Deal,
		Status.type.notin(CLOSED),
		ctx.owned(Deal.deal_owner),
		in_pipeline(ctx),
		value=open_amount() * probability / 100,
		joins=((Status, Deal.status == Status.name),),
	)
	return charts.number(value, format="currency", route=DEALS_ROUTE)


def days_to_win(ctx: Context, previous: bool = False, from_person: bool = False) -> float:
	start = IfNull(Lead.creation, Deal.creation) if from_person else Deal.creation
	query = with_status(frappe.qb.from_(Deal)).left_join(Lead).on(Deal.lead == Lead.name)
	query = query.select(Avg(DaysBetween(Deal.closed_date, Date(start))))
	query = where(
		query,
		Status.type == "Won",
		ctx.within_days(Deal.closed_date, previous),
		ctx.owned(Deal.deal_owner),
		in_pipeline(ctx),
	)
	return round(float(query.run()[0][0] or 0), 1)


@widget(
	"average_time_to_close_a_deal",
	category="sales",
	kind="number",
	title=_lt("Days to win"),
	description=_lt("Average days from opening a deal to winning it, for deals won in the period"),
	options=(PIPELINE,),
	keywords=("sales cycle", "velocity"),
)
def average_time_to_close_a_deal(ctx: Context):
	return charts.number(days_to_win(ctx), days_to_win(ctx, True), format="days", negative_is_better=True)


@widget(
	"average_time_to_close_a_lead",
	category="sales",
	kind="number",
	title=_lt("Days from first contact to win"),
	description=_lt("Average days from a person's arrival to winning their deal"),
	options=(PIPELINE,),
	retired=True,
)
def average_time_to_close_a_lead(ctx: Context):
	return charts.number(
		days_to_win(ctx, from_person=True),
		days_to_win(ctx, True, from_person=True),
		format="days",
		negative_is_better=True,
	)


def created_deals_average(ctx: Context, previous: bool, types) -> float:
	query = with_status(frappe.qb.from_(Deal)).select(Avg(amount()))
	query = where(
		query, ctx.within(Deal.creation, previous), types, ctx.owned(Deal.deal_owner), in_pipeline(ctx)
	)
	return float(query.run()[0][0] or 0)


@widget(
	"average_deal_value",
	category="sales",
	kind="number",
	title=_lt("Average deal value"),
	description=_lt("Average value of the open and won deals opened in the period"),
	retired=True,
)
def average_deal_value(ctx: Context):
	types = Status.type != "Lost"
	return charts.number(
		created_deals_average(ctx, False, types), created_deals_average(ctx, True, types), format="currency"
	)


@widget(
	"average_ongoing_deal_value",
	category="sales",
	kind="number",
	title=_lt("Average open deal value"),
	description=_lt("Average value of the deals opened in the period that are still open"),
	retired=True,
)
def average_ongoing_deal_value(ctx: Context):
	types = Status.type.notin(CLOSED)
	return charts.number(
		created_deals_average(ctx, False, types), created_deals_average(ctx, True, types), format="currency"
	)


@widget(
	"ongoing_deals",
	category="sales",
	kind="number",
	title=_lt("Open deals opened in the period"),
	description=_lt("Deals opened in the period that are not yet won or lost"),
	retired=True,
)
def ongoing_deals(ctx: Context):
	now, before = two_periods(
		ctx,
		Deal,
		Deal.creation,
		Deal.status.isin(frappe.qb.from_(Status).select(Status.name).where(Status.type.notin(CLOSED))),
		ctx.owned(Deal.deal_owner),
	)
	return charts.number(now, before, route=DEALS_ROUTE)


# -- charts -----------------------------------------------------------------


@widget(
	"sales_trend",
	category="sales",
	kind="axis",
	title=_lt("Sales trend"),
	description=_lt("New people, new deals and won deals over the period"),
	size=(10, 8),
)
def sales_trend(ctx: Context):
	people = per_bucket(ctx, per_day(ctx, Lead, Lead.creation, ctx.owned(Lead.lead_owner)))
	deals = per_bucket(ctx, per_day(ctx, Deal, Deal.creation, ctx.owned(Deal.deal_owner)))
	won_query = with_status(frappe.qb.from_(Deal)).select(Deal.closed_date.as_("day"), Count("*").as_("n"))
	won_query = where(
		won_query, Status.type == "Won", ctx.within_days(Deal.closed_date), ctx.owned(Deal.deal_owner)
	).groupby(Deal.closed_date)
	won = per_bucket(ctx, {getdate(row.day): float(row.n) for row in won_query.run(as_dict=True)})
	return charts.trend(
		ctx.buckets,
		ctx.grain,
		[
			charts.series("people", _("New people"), charts.fill(ctx.buckets, people)),
			charts.series("deals", _("New deals"), charts.fill(ctx.buckets, deals)),
			charts.series("won", _("Won deals"), charts.fill(ctx.buckets, won)),
		],
	)


@widget(
	"won_value_trend",
	category="sales",
	kind="axis",
	title=_lt("Won revenue over time"),
	description=_lt("Value of the deals won, day by day or month by month"),
	size=(10, 8),
	options=(PIPELINE,),
)
def won_value_trend(ctx: Context):
	query = with_status(frappe.qb.from_(Deal)).select(Deal.closed_date.as_("day"), Sum(amount()).as_("n"))
	query = where(
		query,
		Status.type == "Won",
		ctx.within_days(Deal.closed_date),
		ctx.owned(Deal.deal_owner),
		in_pipeline(ctx),
	).groupby(Deal.closed_date)
	won = per_bucket(ctx, {getdate(row.day): float(row.n or 0) for row in query.run(as_dict=True)})
	return charts.trend(
		ctx.buckets,
		ctx.grain,
		[charts.series("won", _("Won revenue"), charts.fill(ctx.buckets, won), type="bar")],
		format="currency",
	)


@widget(
	"forecasted_revenue",
	category="sales",
	kind="axis",
	title=_lt("Revenue forecast"),
	description=_lt(
		"Won revenue of the last months, and open deals weighted by probability by expected close month"
	),
	size=(10, 8),
	live=True,
	options=(PIPELINE,),
)
def forecasted_revenue(ctx: Context):
	first = getdate(get_first_day(add_months(ctx.today, -5)))
	last = getdate(add_days(get_first_day(add_months(ctx.today, 7)), -1))
	months = periods.buckets(first, last, "month")

	won_query = with_status(frappe.qb.from_(Deal)).select(Deal.closed_date.as_("day"), Sum(amount()).as_("n"))
	won_query = where(
		won_query,
		Status.type == "Won",
		(Deal.closed_date >= first) & (Deal.closed_date <= ctx.today),
		ctx.owned(Deal.deal_owner),
		in_pipeline(ctx),
	).groupby(Deal.closed_date)
	won: dict = defaultdict(float)
	for row in won_query.run(as_dict=True):
		won[periods.bucket(getdate(row.day), "month")] += float(row.n or 0)

	probability = IfNull(Deal.probability, IfNull(Status.probability, 0))
	open_query = with_status(frappe.qb.from_(Deal)).select(
		Deal.expected_closure_date.as_("day"), Sum(open_amount() * probability / 100).as_("n")
	)
	open_query = where(
		open_query,
		Status.type.notin(CLOSED),
		Deal.expected_closure_date <= last,
		ctx.owned(Deal.deal_owner),
		in_pipeline(ctx),
	).groupby(Deal.expected_closure_date)
	this_month = getdate(get_first_day(ctx.today))
	forecast: dict = defaultdict(float)
	for row in open_query.run(as_dict=True):
		# a deal whose expected month has passed is still open: it is expected now, not never
		month = max(periods.bucket(getdate(row.day), "month"), this_month)
		forecast[month] += float(row.n or 0)

	return charts.trend(
		months,
		"month",
		[
			charts.series("won", _("Won"), charts.fill(months, won), type="bar"),
			charts.series("forecast", _("Weighted forecast"), charts.fill(months, forecast), type="bar"),
		],
		format="currency",
		stacked=True,
	)


def furthest_positions(ctx: Context, pipeline: str) -> tuple[list[dict], dict[str, float]]:
	"""The pipeline's stages, and for each deal opened in the period the furthest stage it reached."""
	stages = frappe.get_all(
		"CRM Deal Status",
		filters={"pipeline": pipeline},
		fields=["name", "type", "position"],
		order_by="position asc, name asc",
	)
	position = {stage.name: index for index, stage in enumerate(stages)}
	lost = {stage.name for stage in stages if stage.type == "Lost"}

	query = frappe.qb.from_(Deal).select(Deal.name, Deal.status)
	query = where(query, ctx.within(Deal.creation), Deal.pipeline == pipeline, ctx.owned(Deal.deal_owner))
	deals = {row.name: row.status for row in query.run(as_dict=True)}
	if not deals:
		return stages, {}

	reached: dict[str, float] = {}
	for name, status in deals.items():
		if status in position and status not in lost:
			reached[name] = position[status]
	for chunk in _chunks(list(deals), 500):
		logs = (
			frappe.qb.from_(Log)
			.select(Log.parent, Log["from"].as_("stage"))
			.where((Log.parenttype == "CRM Deal") & Log.parent.isin(chunk))
			.run(as_dict=True)
		)
		for row in logs:
			if row.stage in position and row.stage not in lost:
				reached[row.parent] = max(reached.get(row.parent, -1), position[row.stage])
	# a deal lost at its very first stage still entered the funnel
	for name in deals:
		reached.setdefault(name, -1)
	return stages, reached


@widget(
	"funnel_conversion",
	category="sales",
	kind="funnel",
	title=_lt("Pipeline funnel"),
	description=_lt("How far the deals opened in the period got, stage by stage"),
	size=(10, 8),
	options=(PIPELINE,),
	keywords=("conversion", "stages"),
)
def funnel_conversion(ctx: Context):
	from crm.fcrm.doctype.crm_pipeline.crm_pipeline import get_default_pipeline

	pipeline = ctx.option("pipeline") or get_default_pipeline()
	if not pipeline:
		return charts.funnel([])
	stages, reached = furthest_positions(ctx, pipeline)
	steps = [(_("Opened"), len(reached))]
	for index, stage in enumerate(stages):
		if stage.type == "Lost":
			continue
		steps.append((stage.name, sum(1 for value in reached.values() if value >= index)))
	return charts.funnel(steps)


@widget(
	"deals_by_stage",
	category="sales",
	kind="axis",
	title=_lt("Open deals by stage"),
	description=_lt("Where the open deals are, right now"),
	size=(10, 8),
	live=True,
	options=(PIPELINE, MEASURE),
)
def deals_by_stage(ctx: Context):
	from crm.fcrm.doctype.crm_pipeline.crm_pipeline import get_default_pipeline

	pipeline = ctx.option("pipeline") or get_default_pipeline()
	by_value = ctx.option("measure") == "value"
	query = with_status(frappe.qb.from_(Deal)).select(
		Deal.status.as_("stage"),
		(Sum(open_amount()) if by_value else Count("*")).as_("n"),
		Status.position.as_("position"),
	)
	query = where(
		query,
		Status.type.notin(CLOSED),
		(Deal.pipeline == pipeline) if pipeline else None,
		ctx.owned(Deal.deal_owner),
	).groupby(Deal.status, Status.position)
	rows = sorted(query.run(as_dict=True), key=lambda row: (row.position or 0, row.stage or ""))
	return charts.bars(
		[{"stage": stage_name(row.stage), "n": row.n} for row in rows],
		label_key="stage",
		lines=[("n", _("Value") if by_value else _("Deals"))],
		format="currency" if by_value else "number",
	)


# the first dashboard had the stages twice, as bars and as a donut
widget(
	"deals_by_stage_axis",
	category="sales",
	kind="axis",
	title=_lt("Open deals by stage"),
	size=(10, 8),
	live=True,
	options=(PIPELINE, MEASURE),
	retired=True,
)(deals_by_stage)
widget(
	"deals_by_stage_donut",
	category="sales",
	kind="axis",
	title=_lt("Open deals by stage"),
	size=(10, 8),
	live=True,
	options=(PIPELINE, MEASURE),
	retired=True,
)(deals_by_stage)


@widget(
	"lost_deal_reasons",
	category="sales",
	kind="axis",
	title=_lt("Why deals are lost"),
	description=_lt("Reasons given for the deals lost in the period"),
	size=(10, 8),
	options=(PIPELINE,),
)
def lost_deal_reasons(ctx: Context):
	rows = grouped(
		Deal,
		Deal.lost_reason,
		lost_between(*ctx.span()),
		ctx.owned(Deal.deal_owner),
		in_pipeline(ctx),
		joins=((Status, Deal.status == Status.name),),
		limit=10,
	)
	return charts.bars(
		[{"reason": reason or _("No reason given"), "n": count} for reason, count in rows],
		label_key="reason",
		lines=[("n", _("Deals"))],
	)


def by_dimension(ctx: Context, key):
	by_value = ctx.option("measure") == "value"
	criteria = [ctx.owned(Deal.deal_owner), in_pipeline(ctx)]
	if by_value:
		criteria += [Status.type == "Won", ctx.within_days(Deal.closed_date)]
	else:
		criteria.append(ctx.within(Deal.creation))
	rows = grouped(
		Deal,
		key,
		*criteria,
		value=amount() if by_value else None,
		joins=((Status, Deal.status == Status.name),),
		limit=12,
	)
	return rows, by_value


@widget(
	"deals_by_source",
	category="sales",
	kind="donut",
	title=_lt("Deals by source"),
	description=_lt("Where the deals opened in the period came from"),
	size=(10, 8),
	options=(PIPELINE, MEASURE),
)
def deals_by_source(ctx: Context):
	rows, by_value = by_dimension(ctx, Deal.source)
	return charts.donut(
		rows, format="currency" if by_value else "number", other_label=_("Other"), empty_label=_("Not set")
	)


@widget(
	"deals_by_territory",
	category="sales",
	kind="axis",
	title=_lt("Deals by territory"),
	description=_lt("Deals opened in the period, or revenue won, by territory"),
	size=(10, 8),
	options=(PIPELINE, MEASURE),
)
def deals_by_territory(ctx: Context):
	rows, by_value = by_dimension(ctx, Deal.territory)
	return charts.bars(
		[{"territory": key or _("Not set"), "n": value} for key, value in rows],
		label_key="territory",
		lines=[("n", _("Won revenue") if by_value else _("Deals"))],
		format="currency" if by_value else "number",
	)


@widget(
	"deals_by_salesperson",
	category="sales",
	kind="axis",
	title=_lt("Deals by salesperson"),
	description=_lt("Deals opened in the period, or revenue won, per salesperson"),
	size=(10, 8),
	managers_only=True,
	options=(PIPELINE, MEASURE),
)
def deals_by_salesperson(ctx: Context):
	rows, by_value = by_dimension(ctx, Deal.deal_owner)
	names = _full_names([key for key, _value in rows])
	return charts.bars(
		[{"owner": names.get(key) or key or _("Unassigned"), "n": value} for key, value in rows],
		label_key="owner",
		lines=[("n", _("Won revenue") if by_value else _("Deals"))],
		format="currency" if by_value else "number",
	)


# -- lists ------------------------------------------------------------------


def deal_item(row, *, value=None, time=None, badge=None) -> dict:
	title = row.get("organization") or row.get("lead_name") or row.get("name")
	item = {
		"title": title,
		"subtitle": row.get("lead_name") if row.get("organization") else None,
		"route": {"name": "Deal", "params": {"dealId": row.name}},
	}
	if value is not None:
		item["value"] = value
		item["format"] = "currency"
	if time:
		item["time"] = str(time)
	if badge:
		item["badge"] = badge
	if row.get("deal_owner"):
		item["user"] = row.deal_owner
	return item


def _deals_list(ctx: Context, *criteria, order, limit: int, value=None):
	query = with_status(frappe.qb.from_(Deal)).select(
		Deal.name,
		Deal.organization,
		Deal.lead_name,
		Deal.deal_owner,
		Deal.status,
		Deal.expected_closure_date,
		Deal.closed_date,
		Deal.modified,
		Status.color.as_("color"),
		(value if value is not None else open_amount()).as_("amount"),
	)
	query = where(query, *criteria, ctx.owned(Deal.deal_owner), in_pipeline(ctx))
	for column, direction in order:
		query = query.orderby(column, order=direction)
	return query.limit(limit).run(as_dict=True)


def _count_deals(ctx: Context, *criteria) -> int:
	query = where(
		with_status(frappe.qb.from_(Deal)).select(Count("*")),
		*criteria,
		ctx.owned(Deal.deal_owner),
		in_pipeline(ctx),
	)
	return int(query.run()[0][0] or 0)


def closing_soon(ctx: Context):
	limit = ctx.option("limit", 6)
	horizon = add_days(ctx.today, 14)
	criteria = (
		Status.type.notin(CLOSED),
		Deal.expected_closure_date.isnotnull(),
		Deal.expected_closure_date <= horizon,
	)
	rows = _deals_list(ctx, *criteria, order=((Deal.expected_closure_date, frappe.qb.asc),), limit=limit)
	items = [
		deal_item(
			row,
			value=row.amount,
			time=row.expected_closure_date,
			badge={"label": row.status, "color": row.color or "gray"},
		)
		for row in rows
	]
	return charts.listing(
		items,
		empty=_("No deal is expected to close in the next two weeks"),
		more={"label": _("All deals"), "route": DEALS_ROUTE},
		total=_count_deals(ctx, *criteria),
	)


@widget(
	"deals_closing_soon",
	category="sales",
	kind="list",
	title=_lt("Closing soon"),
	description=_lt("Open deals expected to close in the next two weeks, or already late"),
	size=(10, 8),
	live=True,
	options=(PIPELINE, ROWS),
)
def deals_closing_soon(ctx: Context):
	return closing_soon(ctx)


widget(
	"my_deals_closing_soon",
	category="sales",
	kind="list",
	title=_lt("My deals closing soon"),
	description=_lt("Your open deals expected to close in the next two weeks"),
	size=(10, 8),
	live=True,
	scope="me",
	options=(PIPELINE, ROWS),
)(closing_soon)


STALE_DAYS = Option(
	"days",
	_lt("Untouched for"),
	choices=(("7", _lt("7 days")), ("14", _lt("14 days")), ("30", _lt("30 days"))),
	default="14",
)


@widget(
	"deals_stale",
	category="sales",
	kind="list",
	title=_lt("Deals going cold"),
	description=_lt("Open deals nobody has touched for a while"),
	size=(10, 8),
	live=True,
	options=(PIPELINE, STALE_DAYS, ROWS),
	keywords=("stuck", "idle", "rotting"),
)
def deals_stale(ctx: Context):
	days = int(ctx.option("days", "14"))
	cutoff = add_days(ctx.now, -days)
	criteria = (Status.type.notin(CLOSED), Deal.modified < cutoff)
	rows = _deals_list(ctx, *criteria, order=((Deal.modified, frappe.qb.asc),), limit=ctx.option("limit", 6))
	items = [
		deal_item(
			row,
			value=row.amount,
			time=row.modified,
			badge={"label": row.status, "color": row.color or "gray"},
		)
		for row in rows
	]
	return charts.listing(
		items,
		empty=_("Every open deal was touched in the last {0} days").format(days),
		more={"label": _("All deals"), "route": DEALS_ROUTE},
		total=_count_deals(ctx, *criteria),
	)


@widget(
	"deals_recently_won",
	category="sales",
	kind="list",
	title=_lt("Recently won"),
	description=_lt("The deals won in the period, latest first"),
	size=(10, 8),
	options=(PIPELINE, ROWS),
)
def deals_recently_won(ctx: Context):
	criteria = (Status.type == "Won", ctx.within_days(Deal.closed_date))
	rows = _deals_list(
		ctx,
		*criteria,
		order=((Deal.closed_date, frappe.qb.desc), (Deal.modified, frappe.qb.desc)),
		limit=ctx.option("limit", 6),
		value=amount(),
	)
	items = [deal_item(row, value=row.amount, time=row.closed_date) for row in rows]
	return charts.listing(
		items, empty=_("No deal won in this period yet"), total=_count_deals(ctx, *criteria)
	)


def _full_names(users: list[str | None]) -> dict[str, str]:
	users = [user for user in users if user]
	if not users:
		return {}
	return dict(
		frappe.get_all("User", filters={"name": ("in", users)}, fields=["name", "full_name"], as_list=True)
	)


def _chunks(items: list, size: int):
	for start in range(0, len(items), size):
		yield items[start : start + size]
