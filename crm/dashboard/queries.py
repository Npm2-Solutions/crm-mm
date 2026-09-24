# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The handful of query shapes almost every widget is made of.

Counting "how many in the period, and how many in the one before" is the same
question over twenty tables, so it is written once: one query, both periods, via
``CASE`` — the pattern the original dashboard used, kept because it halves the
round trips. Everything here takes a ``Context`` and plain query-builder terms,
and returns plain Python values.

The raw SQL goes through the query builder, not ``frappe.get_list``: the
dashboard counts, it does not list, and whose records count is decided by
``Context`` (which follows the same hierarchy as the list permissions).
"""

from __future__ import annotations

import datetime
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

import frappe
from frappe.query_builder import Case, DocType
from frappe.query_builder.functions import Count, Date, DateFormat, Sum
from pypika.functions import Function
from pypika.terms import LiteralValue

from crm.dashboard.context import Context, where


class DaysBetween(Function):
	"""Whole days from ``earlier`` to ``later`` (MariaDB ``DATEDIFF``; pypika's own takes an interval)."""

	def __init__(self, later, earlier, alias=None):
		super().__init__("DATEDIFF", later, earlier, alias=alias)


class SecondsBetween(Function):
	"""Seconds from ``earlier`` to ``later`` (``TIMESTAMPDIFF``)."""

	def __init__(self, earlier, later, alias=None):
		super().__init__("TIMESTAMPDIFF", LiteralValue("SECOND"), earlier, later, alias=alias)


def two_periods(ctx: Context, table, column, *criteria, value=None, distinct=None) -> tuple[float, float]:
	"""(this period, previous period) for rows of ``table`` whose ``column`` falls in each.

	Counts rows, or sums ``value``, or counts distinct ``distinct``. ``column``
	is a Datetime; for a Date column use ``two_periods_by_day``.
	"""
	return _two(ctx, table, ctx.within(column), ctx.within(column, previous=True), criteria, value, distinct)


def two_periods_by_day(
	ctx: Context, table, column, *criteria, value=None, distinct=None
) -> tuple[float, float]:
	"""``two_periods`` for a Date column."""
	return _two(
		ctx,
		table,
		ctx.within_days(column),
		ctx.within_days(column, previous=True),
		criteria,
		value,
		distinct,
	)


def _two(ctx, table, current, previous, criteria, value, distinct) -> tuple[float, float]:
	if distinct is not None:
		now_ = Count(Case().when(current, distinct).else_(None)).distinct()
		before = Count(Case().when(previous, distinct).else_(None)).distinct()
	elif value is not None:
		now_ = Sum(Case().when(current, value).else_(0))
		before = Sum(Case().when(previous, value).else_(0))
	else:
		now_ = Sum(Case().when(current, 1).else_(0))
		before = Sum(Case().when(previous, 1).else_(0))
	query = frappe.qb.from_(table).select(now_.as_("now"), before.as_("before"))
	query = where(query, current | previous, *criteria)
	row = query.run(as_dict=True)
	row = row[0] if row else {}
	return float(row.get("now") or 0), float(row.get("before") or 0)


def total(table, *criteria, value=None, distinct=None, joins=()) -> float:
	"""A single count (or sum) with no period — for widgets about the present."""
	if distinct is not None:
		measure = Count(distinct).distinct()
	elif value is not None:
		measure = Sum(value)
	else:
		measure = Count("*")
	query = frappe.qb.from_(table)
	for other, on in joins:
		query = query.join(other).on(on)
	query = where(query.select(measure.as_("n")), *criteria)
	row = query.run()
	return float(row[0][0] or 0) if row else 0


def per_day(ctx: Context, table, column, *criteria, value=None) -> dict[datetime.date, float]:
	"""Rows (or ``value`` summed) per calendar day of the period."""
	day = Date(column)
	measure = Sum(value) if value is not None else Count("*")
	query = frappe.qb.from_(table).select(day.as_("day"), measure.as_("n")).groupby(day)
	query = where(query, ctx.within(column), *criteria)
	return {_as_date(row.day): float(row.n or 0) for row in query.run(as_dict=True) if row.day}


def per_bucket(ctx: Context, daily: dict[datetime.date, float]) -> dict[datetime.date, float]:
	"""Daily values folded into the context's buckets (days, weeks or months)."""
	folded: dict[datetime.date, float] = defaultdict(float)
	for day, value in daily.items():
		bucket = ctx.bucket(day)
		if bucket:
			folded[bucket] += value
	return folded


def grouped(table, key, *criteria, value=None, joins=(), limit: int | None = None) -> list[tuple[Any, float]]:
	"""(key, count or sum of ``value``) pairs, largest first."""
	measure = Sum(value) if value is not None else Count("*")
	query = frappe.qb.from_(table)
	for other, on in joins:
		query = query.left_join(other).on(on)
	query = where(query.select(key.as_("key"), measure.as_("n")), *criteria).groupby(key)
	query = query.orderby(measure, order=frappe.qb.desc)
	if limit:
		query = query.limit(limit)
	return [(row.key, float(row.n or 0)) for row in query.run(as_dict=True)]


def weekday_hour(ctx: Context, table, column, *criteria) -> dict[tuple[int, int], float]:
	"""Counts per (hour, weekday) over the period; weekday 0 is Monday."""
	weekday = DateFormat(column, "%w")  # 0 = Sunday
	hour = DateFormat(column, "%H")
	query = (
		frappe.qb.from_(table)
		.select(weekday.as_("weekday"), hour.as_("hour"), Count("*").as_("n"))
		.groupby(weekday, hour)
	)
	query = where(query, ctx.within(column), *criteria)
	counts: dict[tuple[int, int], float] = {}
	for row in query.run(as_dict=True):
		monday_first = (int(row.weekday) + 6) % 7
		counts[(int(row.hour), monday_first)] = float(row.n or 0)
	return counts


def _as_date(value) -> datetime.date | None:
	if isinstance(value, datetime.datetime):
		return value.date()
	if isinstance(value, datetime.date):
		return value
	try:
		return datetime.date.fromisoformat(str(value)[:10])
	except ValueError:
		return None


# -- messages across channels -------------------------------------------------


@dataclass(frozen=True)
class Channel:
	"""Where one channel keeps its messages, and how to tell in from out."""

	key: str
	doctype: str
	direction: str
	incoming: str
	outgoing: str

	@property
	def table(self):
		return DocType(self.doctype)

	def exists(self) -> bool:
		return bool(frappe.db.exists("DocType", self.doctype))

	def base(self) -> list:
		"""What makes a row a real message on a person or a deal."""
		table = self.table
		criteria = [table.reference_doctype.isin(["CRM Lead", "CRM Deal"])]
		if self.key == "whatsapp":
			# reactions are rows too, in both directions; they are not messages
			criteria.append((table.content_type.isnull()) | (table.content_type != "reaction"))
		if self.key == "email":
			criteria.append(table.communication_type == "Communication")
			criteria.append(table.communication_medium == "Email")
		return criteria

	def is_incoming(self):
		return self.table[self.direction] == self.incoming

	def is_outgoing(self):
		return self.table[self.direction] == self.outgoing


CHANNELS = (
	Channel("whatsapp", "WhatsApp Message", "type", "Incoming", "Outgoing"),
	Channel("sms", "CRM SMS Message", "type", "Incoming", "Outgoing"),
	Channel("email", "Communication", "sent_or_received", "Received", "Sent"),
)


def channel(key: str) -> Channel:
	return next(item for item in CHANNELS if item.key == key)


def channels() -> list[Channel]:
	"""The channels whose messages this site can store (the WhatsApp app may be missing)."""
	return [item for item in CHANNELS if item.exists()]


def owned_records(ctx: Context, reference_doctype, reference_name):
	"""Messages filed on a person or deal that belongs to the people being counted."""
	if ctx.everyone:
		return None
	Lead = DocType("CRM Lead")
	Deal = DocType("CRM Deal")
	leads = frappe.qb.from_(Lead).select(Lead.name).where(Lead.lead_owner.isin(ctx.owners or ["<nobody>"]))
	deals = frappe.qb.from_(Deal).select(Deal.name).where(Deal.deal_owner.isin(ctx.owners or ["<nobody>"]))
	return ((reference_doctype == "CRM Lead") & reference_name.isin(leads)) | (
		(reference_doctype == "CRM Deal") & reference_name.isin(deals)
	)


def people_owned(ctx: Context, lead_table):
	"""A person counts when they belong to, or their conversation is handled by, someone counted."""
	if ctx.everyone:
		return None
	owners = ctx.owners or ["<nobody>"]
	return lead_table.lead_owner.isin(owners) | lead_table.conversation_assigned_to.isin(owners)
