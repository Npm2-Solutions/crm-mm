# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The agenda: how full the days are, who shows up, what it is worth.

Offered once the site has services or appointments (``features``). An
appointment belongs to the professionals on it (``CRM Appointment Staff``), so a
professional's dashboard shows their diary and a manager's the whole studio.

Statuses as the scheduler reads them (``crm.scheduling.availability``): only a
cancellation frees the slot — a no-show still took the time. "Upcoming" is
scheduled or confirmed, from now on. Amounts are the appointment's own
``total_amount`` in its currency, which for a studio is the dashboard's.
"""

from __future__ import annotations

import datetime
from collections import defaultdict

import frappe
from frappe import _, _lt
from frappe.query_builder import Case, DocType
from frappe.query_builder.functions import Count, IfNull, Sum

from crm.dashboard import charts
from crm.dashboard.context import Context, where
from crm.dashboard.queries import grouped, per_bucket, per_day, total, two_periods, weekday_hour
from crm.dashboard.registry import Option, widget
from crm.dashboard.widgets.conversations import full_names, hour_labels, weekday_labels

Appt = DocType("CRM Appointment")
Staff = DocType("CRM Appointment Staff")
Participant = DocType("CRM Appointment Participant")
Connection = DocType("CRM Booking Connection")

AGENDA = ("agenda",)
CALENDAR = {"name": "Calendar"}
TAKEN = ("Scheduled", "Confirmed", "Completed", "No Show")
UPCOMING = ("Scheduled", "Confirmed")
BOOKED = ("Scheduled", "Confirmed", "Completed")
ROWS = Option("limit", _lt("Rows"), type="int", default=6, min=3, max=20)
MEASURE = Option(
	"measure",
	_lt("Show"),
	choices=(("count", _lt("Number of appointments")), ("value", _lt("Value"))),
	default="count",
)


def staffed_by(ctx: Context):
	"""The appointment has one of the people counted among its professionals."""
	if ctx.everyone:
		return None
	return Appt.name.isin(
		frappe.qb.from_(Staff)
		.select(Staff.parent)
		.where((Staff.parenttype == "CRM Appointment") & Staff.user.isin(ctx.owners or ["<nobody>"]))
	)


def status_labels() -> dict[str, str]:
	return {
		"Scheduled": _("To confirm"),
		"Confirmed": _("Confirmed"),
		"Completed": _("Completed"),
		"Cancelled": _("Cancelled"),
		"No Show": _("No show"),
	}


STATUS_COLORS = {
	"Scheduled": "orange",
	"Confirmed": "blue",
	"Completed": "green",
	"Cancelled": "gray",
	"No Show": "red",
}


def today_bounds(ctx: Context) -> tuple[datetime.datetime, datetime.datetime]:
	start = datetime.datetime.combine(ctx.today, datetime.time.min)
	return start, start + datetime.timedelta(days=1)


# -- KPIs ---------------------------------------------------------------------


@widget(
	"appointments_today",
	category="agenda",
	kind="number",
	title=_lt("Appointments today"),
	description=_lt("Appointments on today's agenda"),
	live=True,
	requires=AGENDA,
)
def appointments_today(ctx: Context):
	low, high = today_bounds(ctx)
	value = total(
		Appt, Appt.status.isin(TAKEN), (Appt.starts_on >= low) & (Appt.starts_on < high), staffed_by(ctx)
	)
	return charts.number(value, route=CALENDAR)


@widget(
	"appointments_count",
	category="agenda",
	kind="number",
	title=_lt("Appointments"),
	description=_lt("Appointments in the period, cancelled ones aside"),
	requires=AGENDA,
)
def appointments_count(ctx: Context):
	return charts.number(
		*two_periods(ctx, Appt, Appt.starts_on, Appt.status.isin(TAKEN), staffed_by(ctx)), route=CALENDAR
	)


@widget(
	"appointments_to_confirm",
	category="agenda",
	kind="number",
	title=_lt("To confirm"),
	description=_lt("Upcoming appointments still waiting for a confirmation"),
	live=True,
	requires=AGENDA,
)
def appointments_to_confirm(ctx: Context):
	return charts.number(
		total(Appt, Appt.status == "Scheduled", Appt.starts_on >= ctx.now, staffed_by(ctx)), route=CALENDAR
	)


def share(ctx: Context, part, whole, previous: bool) -> float | None:
	counts = frappe.qb.from_(Appt).select(
		Sum(Case().when(part, 1).else_(0)).as_("part"), Sum(Case().when(whole, 1).else_(0)).as_("whole")
	)
	row = where(counts, ctx.within(Appt.starts_on, previous), staffed_by(ctx)).run(as_dict=True)[0]
	return charts.ratio(row.part, row.whole)


@widget(
	"appointments_no_show_rate",
	category="agenda",
	kind="number",
	title=_lt("No-show rate"),
	description=_lt("Of the appointments that were due, the share where the client did not come"),
	requires=AGENDA,
)
def appointments_no_show_rate(ctx: Context):
	part, whole = Appt.status == "No Show", Appt.status.isin(("Completed", "No Show"))
	now = share(ctx, part, whole, False)
	return charts.number(
		now or 0, share(ctx, part, whole, True), format="percent", compare="points", negative_is_better=True
	)


@widget(
	"appointments_cancellation_rate",
	category="agenda",
	kind="number",
	title=_lt("Cancellation rate"),
	description=_lt("Share of the period's appointments that were cancelled"),
	requires=AGENDA,
)
def appointments_cancellation_rate(ctx: Context):
	part, whole = Appt.status == "Cancelled", Appt.status.isnotnull()
	now = share(ctx, part, whole, False)
	return charts.number(
		now or 0, share(ctx, part, whole, True), format="percent", compare="points", negative_is_better=True
	)


@widget(
	"appointments_revenue",
	category="agenda",
	kind="number",
	title=_lt("Appointments value"),
	description=_lt("What the period's appointments are worth, done and still to do"),
	requires=AGENDA,
	keywords=("revenue", "takings", "income"),
)
def appointments_revenue(ctx: Context):
	return charts.number(
		*two_periods(
			ctx,
			Appt,
			Appt.starts_on,
			Appt.status.isin(BOOKED),
			staffed_by(ctx),
			value=IfNull(Appt.total_amount, 0),
		),
		format="currency",
		route=CALENDAR,
	)


@widget(
	"appointments_no_show_value",
	category="agenda",
	kind="number",
	title=_lt("Lost to no-shows"),
	description=_lt("Value of the appointments the client did not turn up to"),
	requires=AGENDA,
)
def appointments_no_show_value(ctx: Context):
	return charts.number(
		*two_periods(
			ctx,
			Appt,
			Appt.starts_on,
			Appt.status == "No Show",
			staffed_by(ctx),
			value=IfNull(Appt.total_amount, 0),
		),
		format="currency",
		negative_is_better=True,
	)


def first_visits(ctx: Context, previous: bool) -> int:
	"""People whose first appointment ever falls in the period."""
	low, high = ctx.span(previous)
	earlier = Participant.as_("earlier")
	earlier_appt = Appt.as_("earlier_appt")
	before = (
		frappe.qb.from_(earlier)
		.join(earlier_appt)
		.on(earlier.parent == earlier_appt.name)
		.select(earlier.party)
		.where(earlier.parenttype == "CRM Appointment")
		.where(earlier_appt.status.isin(TAKEN))
		.where(earlier_appt.starts_on < low)
		.where(earlier.party.isnotnull())
	)
	query = (
		frappe.qb.from_(Participant)
		.join(Appt)
		.on(Participant.parent == Appt.name)
		.select(Count(Participant.party).distinct())
		.where(Participant.parenttype == "CRM Appointment")
		.where(Participant.party.isnotnull())
		.where(Participant.party.notin(before))
	)
	query = where(
		query, Appt.status.isin(TAKEN), (Appt.starts_on >= low) & (Appt.starts_on < high), staffed_by(ctx)
	)
	return int(query.run()[0][0] or 0)


@widget(
	"new_clients",
	category="agenda",
	kind="number",
	title=_lt("New clients"),
	description=_lt("People who came for the first time in the period"),
	requires=AGENDA,
	keywords=("first visit",),
)
def new_clients(ctx: Context):
	return charts.number(first_visits(ctx, False), first_visits(ctx, True))


def workload(ctx: Context) -> tuple[dict[str, float], dict[str, float], int]:
	"""Booked and available minutes per professional over the period."""
	from crm.api.appointments import get_workload

	data = get_workload(str(ctx.start), str(ctx.end))
	booked = data.get("staff") or {}
	capacity = data.get("staff_capacity") or {}
	if not ctx.everyone:
		owners = set(ctx.owners or [])
		booked = {user: value for user, value in booked.items() if user in owners}
		capacity = {user: value for user, value in capacity.items() if user in owners}
	return booked, capacity, int(data.get("appointments") or 0)


@widget(
	"agenda_occupancy",
	category="agenda",
	kind="number",
	title=_lt("Agenda occupancy"),
	description=_lt("Booked hours against the working hours of the professionals"),
	requires=AGENDA,
	keywords=("utilisation", "utilization", "saturation"),
)
def agenda_occupancy(ctx: Context):
	booked, capacity, _count = workload(ctx)
	rate = charts.ratio(sum(booked.values()), sum(capacity.values()))
	return charts.number(rate or 0, format="percent", progress=rate or 0, route=CALENDAR)


# -- charts -------------------------------------------------------------------


@widget(
	"appointments_trend",
	category="agenda",
	kind="axis",
	title=_lt("Appointments over time"),
	description=_lt("Appointments by outcome: done, still to come, no-shows and cancellations"),
	size=(10, 8),
	requires=AGENDA,
)
def appointments_trend(ctx: Context):
	scope = staffed_by(ctx)
	lines = []
	# stacked from what went well to what went wrong; each outcome keeps its colour
	for key, statuses, label, color in (
		("completed", ("Completed",), _("Completed"), "green"),
		("upcoming", UPCOMING, _("Scheduled"), "blue"),
		("cancelled", ("Cancelled",), _("Cancelled"), "amber"),
		("no_show", ("No Show",), _("No show"), "pink"),
	):
		values = per_bucket(ctx, per_day(ctx, Appt, Appt.starts_on, Appt.status.isin(statuses), scope))
		lines.append(charts.series(key, label, charts.fill(ctx.buckets, values), type="bar", color=color))
	return charts.trend(ctx.buckets, ctx.grain, lines, stacked=True)


@widget(
	"appointments_by_service",
	category="agenda",
	kind="axis",
	title=_lt("Appointments by service"),
	description=_lt("Which services fill the agenda, by number or by value"),
	size=(10, 8),
	requires=AGENDA,
	options=(MEASURE,),
)
def appointments_by_service(ctx: Context):
	by_value = ctx.option("measure") == "value"
	rows = grouped(
		Appt,
		Appt.service,
		Appt.status.isin(BOOKED if by_value else TAKEN),
		ctx.within(Appt.starts_on),
		staffed_by(ctx),
		value=IfNull(Appt.total_amount, 0) if by_value else None,
		limit=12,
	)
	return charts.bars(
		[{"service": key or _("Not set"), "n": value} for key, value in rows],
		label_key="service",
		lines=[("n", _("Value") if by_value else _("Appointments"))],
		format="currency" if by_value else "number",
	)


@widget(
	"appointments_by_staff",
	category="agenda",
	kind="axis",
	title=_lt("Appointments per professional"),
	description=_lt("How the period's appointments are shared across the team"),
	size=(10, 8),
	requires=AGENDA,
	managers_only=True,
)
def appointments_by_staff(ctx: Context):
	query = (
		frappe.qb.from_(Staff)
		.join(Appt)
		.on(Staff.parent == Appt.name)
		.select(Staff.user, Count(Appt.name).distinct().as_("n"))
		.where(Staff.parenttype == "CRM Appointment")
	)
	query = where(query, Appt.status.isin(TAKEN), ctx.within(Appt.starts_on), ctx.owned(Staff.user))
	rows = (
		query.groupby(Staff.user)
		.orderby(Count(Appt.name).distinct(), order=frappe.qb.desc)
		.limit(12)
		.run(as_dict=True)
	)
	names = full_names([row.user for row in rows])
	return charts.bars(
		[{"user": names.get(row.user) or row.user, "n": row.n} for row in rows],
		label_key="user",
		lines=[("n", _("Appointments"))],
	)


def source_label(source: str | None, platform: str | None) -> str:
	if source == "Online":
		return _("Online booking")
	if source == "External":
		return platform or _("Booking platform")
	return _("Booked by the team")


@widget(
	"appointments_by_source",
	category="agenda",
	kind="donut",
	title=_lt("How appointments are booked"),
	description=_lt("By the team, online booking, or an external platform"),
	size=(10, 8),
	requires=AGENDA,
)
def appointments_by_source(ctx: Context):
	query = frappe.qb.from_(Appt).select(Appt.source, Appt.external_platform, Count("*").as_("n"))
	query = where(query, Appt.status.isin(TAKEN), ctx.within(Appt.creation), staffed_by(ctx)).groupby(
		Appt.source, Appt.external_platform
	)
	totals: dict[str, float] = defaultdict(float)
	for row in query.run(as_dict=True):
		totals[source_label(row.source, row.external_platform)] += float(row.n or 0)
	return charts.donut(list(totals.items()), other_label=_("Other"))


@widget(
	"appointments_heatmap",
	category="agenda",
	kind="heatmap",
	title=_lt("Busiest hours"),
	description=_lt("Appointments by day of the week and starting hour"),
	size=(20, 7),
	requires=AGENDA,
)
def appointments_heatmap(ctx: Context):
	counts = weekday_hour(ctx, Appt, Appt.starts_on, Appt.status.isin(TAKEN), staffed_by(ctx))
	return charts.heatmap(counts, x_labels=hour_labels(), y_labels=weekday_labels())


@widget(
	"staff_occupancy",
	category="agenda",
	kind="table",
	title=_lt("Team occupancy"),
	description=_lt("Booked hours and occupancy of each professional in the period"),
	size=(10, 8),
	requires=AGENDA,
	managers_only=True,
)
def staff_occupancy(ctx: Context):
	booked, capacity, _count = workload(ctx)
	names = full_names(list(booked))
	rows = [
		{
			"user": user,
			"name": names.get(user) or user,
			"hours": round(minutes / 60, 1),
			"occupancy": charts.ratio(minutes, capacity.get(user)),
		}
		for user, minutes in booked.items()
	]
	rows.sort(key=lambda row: row["hours"], reverse=True)
	return charts.table(
		[
			{"key": "user", "label": _("Professional"), "format": "user"},
			{"key": "hours", "label": _("Booked hours"), "format": "number"},
			{"key": "occupancy", "label": _("Occupancy"), "format": "percent"},
		],
		rows,
		empty=_("No appointment in this period"),
	)


# -- lists --------------------------------------------------------------------


def appointment_items(rows) -> list[dict]:
	labels = status_labels()
	staff: dict[str, str] = {}
	names = [row.name for row in rows]
	if names:
		for row in (
			frappe.qb.from_(Staff)
			.select(Staff.parent, Staff.user)
			.where((Staff.parenttype == "CRM Appointment") & Staff.parent.isin(names))
			.orderby(Staff.idx)
			.run(as_dict=True)
		):
			staff.setdefault(row.parent, row.user)
	items = []
	for row in rows:
		people = (row.title or "").split(" — ", 1)
		item = {
			"title": people[1] if len(people) > 1 and people[1] else row.title or row.service,
			"subtitle": row.service,
			"time": str(row.starts_on),
			"clock": True,
			"badge": {
				"label": labels.get(row.status, row.status),
				"color": STATUS_COLORS.get(row.status, "gray"),
			},
			"route": {"name": "Calendar", "query": {"appointment": row.name}},
		}
		if staff.get(row.name):
			item["user"] = staff[row.name]
		items.append(item)
	return items


def upcoming(ctx: Context, *criteria, empty: str):
	query = frappe.qb.from_(Appt).select(Appt.name, Appt.title, Appt.service, Appt.status, Appt.starts_on)
	query = where(query, *criteria, staffed_by(ctx))
	rows = query.orderby(Appt.starts_on, order=frappe.qb.asc).limit(ctx.option("limit", 6)).run(as_dict=True)
	return charts.listing(
		appointment_items(rows),
		empty=empty,
		more={"label": _("Open the agenda"), "route": CALENDAR},
		total=int(total(Appt, *criteria, staffed_by(ctx))),
	)


def next_appointments(ctx: Context):
	return upcoming(
		ctx,
		Appt.status.isin(UPCOMING),
		Appt.starts_on >= ctx.now,
		empty=_("Nothing on the agenda"),
	)


@widget(
	"appointments_upcoming",
	category="agenda",
	kind="list",
	title=_lt("Next appointments"),
	description=_lt("The next appointments on the agenda"),
	size=(10, 8),
	live=True,
	requires=AGENDA,
	options=(ROWS,),
)
def appointments_upcoming(ctx: Context):
	return next_appointments(ctx)


def todays_appointments(ctx: Context):
	low, high = today_bounds(ctx)
	return upcoming(
		ctx,
		Appt.status.isin(TAKEN),
		(Appt.starts_on >= low) & (Appt.starts_on < high),
		empty=_("No appointment today"),
	)


widget(
	"my_appointments_today",
	category="agenda",
	kind="list",
	title=_lt("My appointments today"),
	description=_lt("Your agenda for today"),
	size=(10, 8),
	live=True,
	scope="me",
	requires=AGENDA,
	options=(ROWS,),
)(todays_appointments)


@widget(
	"appointments_to_confirm_list",
	category="agenda",
	kind="list",
	title=_lt("Waiting for confirmation"),
	description=_lt("Upcoming appointments nobody has confirmed yet"),
	size=(10, 8),
	live=True,
	requires=AGENDA,
	options=(ROWS,),
)
def appointments_to_confirm_list(ctx: Context):
	return upcoming(
		ctx,
		Appt.status == "Scheduled",
		Appt.starts_on >= ctx.now,
		empty=_("Every upcoming appointment is confirmed"),
	)


# -- online booking -------------------------------------------------------------


@widget(
	"online_bookings",
	category="booking",
	kind="number",
	title=_lt("Online bookings"),
	description=_lt("Appointments clients booked themselves on the booking page"),
	requires=("online_booking",),
)
def online_bookings(ctx: Context):
	return charts.number(
		*two_periods(ctx, Appt, Appt.creation, Appt.source == "Online", staffed_by(ctx)), route=CALENDAR
	)


@widget(
	"online_booking_share",
	category="booking",
	kind="number",
	title=_lt("Booked online"),
	description=_lt("Share of the period's new appointments booked by the clients themselves"),
	requires=("online_booking",),
)
def online_booking_share(ctx: Context):
	def rate(previous: bool):
		query = frappe.qb.from_(Appt).select(
			Sum(Case().when(Appt.source == "Online", 1).else_(0)).as_("online"), Count("*").as_("all")
		)
		row = where(query, ctx.within(Appt.creation, previous), staffed_by(ctx)).run(as_dict=True)[0]
		return charts.ratio(row.online, row.all)

	now = rate(False)
	return charts.number(now or 0, rate(True), format="percent", compare="points", progress=now or 0)


@widget(
	"online_bookings_trend",
	category="booking",
	kind="axis",
	title=_lt("Online bookings over time"),
	description=_lt("When clients book online"),
	size=(10, 8),
	requires=("online_booking",),
)
def online_bookings_trend(ctx: Context):
	values = per_bucket(ctx, per_day(ctx, Appt, Appt.creation, Appt.source == "Online", staffed_by(ctx)))
	return charts.trend(
		ctx.buckets,
		ctx.grain,
		[charts.series("online", _("Online bookings"), charts.fill(ctx.buckets, values), type="bar")],
	)


# -- booking platforms ----------------------------------------------------------


@widget(
	"platform_bookings",
	category="booking",
	kind="donut",
	title=_lt("Bookings from platforms"),
	description=_lt("Appointments that arrived from MioDottore, Treatwell and the other platforms"),
	size=(10, 8),
	requires=("booking_platforms",),
)
def platform_bookings(ctx: Context):
	rows = grouped(
		Appt,
		Appt.external_platform,
		Appt.source == "External",
		ctx.within(Appt.creation),
		staffed_by(ctx),
	)
	return charts.donut(rows, other_label=_("Other"), empty_label=_("Booking platform"))


@widget(
	"platform_connections",
	category="booking",
	kind="list",
	title=_lt("Platform connections"),
	description=_lt("Whether each booking platform is syncing, and when it last did"),
	size=(10, 8),
	live=True,
	requires=("booking_platforms",),
	managers_only=True,
)
def platform_connections(ctx: Context):
	rows = (
		frappe.qb.from_(Connection)
		.select(
			Connection.name,
			Connection.platform,
			Connection.status,
			Connection.last_sync,
			Connection.last_webhook,
			Connection.last_error,
			Connection.imported_count,
		)
		.where(Connection.enabled == 1)
		.orderby(Connection.name)
		.run(as_dict=True)
	)
	colors = {"Connected": "green", "Error": "red"}
	labels = {"Connected": _("Connected"), "Error": _("Error"), "Not configured": _("Not configured")}
	items = []
	for row in rows:
		seen = max(filter(None, (row.last_sync, row.last_webhook)), default=None)
		items.append(
			{
				"title": row.name,
				"subtitle": row.last_error if row.status == "Error" else row.platform,
				"time": str(seen) if seen else None,
				"badge": {
					"label": labels.get(row.status, row.status),
					"color": colors.get(row.status, "gray"),
				},
				"value": row.imported_count or 0,
				"format": "number",
				"settings": "Booking platforms",
			}
		)
	return charts.listing(items, empty=_("No booking platform connected"))
