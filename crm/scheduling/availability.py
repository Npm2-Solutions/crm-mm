# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Availability engine: who and what is free, and when.

Everything the calendar asks — "show me the free slots for a 60' physio session
with two therapists in room B", "is this drag-and-drop legal?" — reduces to the
same three questions:

1. **Windows**  — when is each professional / resource / service *supposed* to be
   available (weekly hours, date overrides, holidays)?
2. **Busy**     — what already occupies them (appointments, calendar events,
   public bookings, Google Calendar), padded by buffers?
3. **Fit**      — does the staffing model and the resource capacity leave room
   for one more appointment at that instant?

Staffing models (borrowed from the vocabulary Cal.com established, adapted to a
service business):

* ``Any one``       — round robin: pick ``staff_count`` free professionals out of
  the eligible list, least-busy first. One professional, many clients over the day.
* ``All required``  — collective: *every* listed professional must be free and all
  of them are booked together. Two professionals following one client.
* ``One per role``  — one free professional per declared role (therapist +
  assistant), each role filled independently.

Group services (``max_participants > 1``) additionally expose *joinable* slots:
an existing appointment with seats left, so several clients share one
professional in the same slot.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

import frappe
from frappe import _
from frappe.query_builder.functions import Count
from frappe.utils import cint, now_datetime

from crm.scheduling import intervals as iv
from crm.scheduling.timeutils import (
	UTC,
	as_time,
	day_bounds,
	from_system_naive,
	parse_date,
	scheduling_tz,
	to_system_naive,
)
from crm.utils import count_field

ACTIVE_STATUSES = ("Scheduled", "Confirmed", "Completed", "No Show")
"""Statuses that still occupy the diary. Only ``Cancelled`` frees the slot —
a no-show consumed the time as surely as an attended appointment did."""

WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


# --------------------------------------------------------------------------
# settings
# --------------------------------------------------------------------------


def settings():
	"""Cached singleton — the engine reads it many times per request."""
	if not hasattr(frappe.local, "crm_scheduling_settings"):
		frappe.local.crm_scheduling_settings = frappe.get_cached_doc("CRM Scheduling Settings")
	return frappe.local.crm_scheduling_settings


# --------------------------------------------------------------------------
# working windows
# --------------------------------------------------------------------------


def rows_to_intervals(rows, day: datetime.date, tz: ZoneInfo) -> list[iv.Interval]:
	"""``CRM Service Day`` rows → aware-UTC intervals for one calendar day."""
	weekday = WEEKDAYS[day.weekday()]
	out = []
	for row in rows or []:
		if row.workday != weekday:
			continue
		start = datetime.datetime.combine(day, as_time(row.start_time), tzinfo=tz).astimezone(UTC)
		end = datetime.datetime.combine(day, as_time(row.end_time), tzinfo=tz).astimezone(UTC)
		if start < end:
			out.append((start, end))
	return iv.merge(out)


def holiday_dates(holiday_list: str | None) -> set[datetime.date]:
	if not holiday_list:
		return set()
	return set(frappe.get_all("CRM Holiday", filters={"parent": holiday_list}, pluck="date"))


@dataclass
class WorkingHours:
	"""Weekly hours + holidays + one-off date overrides for a single actor."""

	rows: list = field(default_factory=list)
	holidays: set = field(default_factory=set)
	exceptions: list = field(default_factory=list)
	always: bool = False

	def for_day(self, day: datetime.date, tz: ZoneInfo) -> list[iv.Interval]:
		overrides = [e for e in self.exceptions if parse_date(e.date) == day]
		if overrides:
			# a date override replaces the weekly pattern for that day entirely
			if any(cint(e.unavailable) for e in overrides):
				return []
			start, end = day_bounds(day, tz)
			out = []
			for override in overrides:
				if not override.start_time or not override.end_time:
					out.append((start, end))
					continue
				out.append(
					(
						datetime.datetime.combine(day, as_time(override.start_time), tzinfo=tz).astimezone(
							UTC
						),
						datetime.datetime.combine(day, as_time(override.end_time), tzinfo=tz).astimezone(UTC),
					)
				)
			return iv.merge(out)
		if day in self.holidays:
			return []
		if self.always and not self.rows:
			return [day_bounds(day, tz)]
		return rows_to_intervals(self.rows, day, tz)

	def for_span(self, day: datetime.date, days: int, tz: ZoneInfo) -> list[iv.Interval]:
		"""Windows across consecutive days, merged.

		A slot may run past midnight, so coverage has to be asked over the span it
		touches. Consecutive all-day windows touch at midnight and ``merge``
		collapses them into one continuous interval, which is exactly right.
		"""
		out: list[iv.Interval] = []
		for offset in range(days):
			out.extend(self.for_day(day + datetime.timedelta(days=offset), tz))
		return iv.merge(out)


def staff_working_hours(user: str) -> WorkingHours:
	"""A professional's own schedule, falling back to the site-wide default hours."""
	name = frappe.db.get_value("CRM Staff Schedule", {"user": user, "enabled": 1})
	if name:
		doc = frappe.get_cached_doc("CRM Staff Schedule", name)
		return WorkingHours(
			rows=doc.availability,
			holidays=holiday_dates(doc.holiday_list),
			exceptions=doc.exceptions,
			always=not doc.availability,
		)
	config = settings()
	return WorkingHours(
		rows=config.default_availability,
		holidays=holiday_dates(config.default_holiday_list),
		always=not config.default_availability,
	)


def staff_daily_cap(user: str) -> int:
	name = frappe.db.get_value("CRM Staff Schedule", {"user": user, "enabled": 1})
	return cint(frappe.db.get_value("CRM Staff Schedule", name, "max_daily_appointments")) if name else 0


def resource_working_hours(resource) -> WorkingHours:
	return WorkingHours(
		rows=resource.availability,
		holidays=holiday_dates(resource.holiday_list),
		always=not resource.availability,
	)


def service_working_hours(service) -> WorkingHours:
	return WorkingHours(
		rows=service.availability,
		holidays=holiday_dates(service.holiday_list),
		always=not service.availability,
	)


# --------------------------------------------------------------------------
# busy time
# --------------------------------------------------------------------------


def _service_buffers() -> dict[str, tuple[int, int]]:
	"""Buffers of every service, cached per request — the busy padding needs them
	for each occupying appointment, and the table is small."""
	if not hasattr(frappe.local, "crm_service_buffers"):
		rows = frappe.get_all("CRM Service", fields=["name", "buffer_before", "buffer_after"])
		frappe.local.crm_service_buffers = {
			r.name: (cint(r.buffer_before), cint(r.buffer_after)) for r in rows
		}
	return frappe.local.crm_service_buffers


def _appointment_rows(
	child_doctype: str,
	link_field: str,
	values: list[str],
	start: datetime.datetime,
	end: datetime.datetime,
	extra_fields: list[str] | None = None,
	exclude: str | None = None,
):
	"""Overlapping non-cancelled appointments joined to one of their child tables."""
	if not values:
		return []
	appointment = frappe.qb.DocType("CRM Appointment")
	child = frappe.qb.DocType(child_doctype)
	query = (
		frappe.qb.from_(child)
		.join(appointment)
		.on(child.parent == appointment.name)
		.select(
			child[link_field].as_("link"),
			appointment.name.as_("appointment"),
			appointment.service.as_("service"),
			appointment.starts_on.as_("starts_on"),
			appointment.ends_on.as_("ends_on"),
		)
		.where(child[link_field].isin(values))
		.where(appointment.status.isin(ACTIVE_STATUSES))
		.where(appointment.starts_on < to_system_naive(end))
		.where(appointment.ends_on > to_system_naive(start))
	)
	for extra in extra_fields or []:
		query = query.select(child[extra].as_(extra))
	if exclude:
		query = query.where(appointment.name != exclude)
	return query.run(as_dict=True)


def _pad(start: datetime.datetime, end: datetime.datetime, before: int, after: int) -> iv.Interval:
	return (start - datetime.timedelta(minutes=before), end + datetime.timedelta(minutes=after))


def staff_busy(
	users: list[str],
	start: datetime.datetime,
	end: datetime.datetime,
	buffer_before: int = 0,
	buffer_after: int = 0,
	exclude_appointment: str | None = None,
	include_google: bool = False,
) -> dict[str, list[iv.Interval]]:
	"""Everything that occupies these professionals in ``[start, end)``.

	Buffers are the *larger* of the asking service's and the occupying service's,
	so a 15' clean-up after a treatment protects the next slot no matter which
	side of the boundary declared it.
	"""
	busy: dict[str, list[iv.Interval]] = {u: [] for u in users}
	if not users:
		return busy

	buffers = _service_buffers()
	pad = datetime.timedelta(minutes=max(buffer_before, buffer_after))
	window_start, window_end = start - pad, end + pad

	for row in _appointment_rows(
		"CRM Appointment Staff", "user", users, window_start, window_end, exclude=exclude_appointment
	):
		other_before, other_after = buffers.get(row.service, (0, 0))
		busy[row.link].append(
			_pad(
				from_system_naive(row.starts_on),
				from_system_naive(row.ends_on),
				max(buffer_before, other_before),
				max(buffer_after, other_after),
			)
		)

	# public Calendly-style bookings share the same people
	for row in frappe.get_all(
		"CRM Booking",
		filters={
			"agent": ["in", users],
			"status": "Confirmed",
			"starts_on": ["<", to_system_naive(window_end)],
			"ends_on": [">", to_system_naive(window_start)],
		},
		fields=["agent", "starts_on", "ends_on"],
	):
		busy[row.agent].append(
			_pad(
				from_system_naive(row.starts_on),
				from_system_naive(row.ends_on),
				buffer_before,
				buffer_after,
			)
		)

	for user, entries in _event_busy(users, window_start, window_end).items():
		for entry in entries:
			busy[user].append(_pad(entry[0], entry[1], buffer_before, buffer_after))

	if include_google:
		from crm.fcrm.doctype.crm_booking_calendar.crm_booking_calendar import (
			get_google_busy_intervals,
		)

		for user in users:
			for entry in get_google_busy_intervals(user, window_start, window_end):
				busy[user].append(_pad(entry[0], entry[1], buffer_before, buffer_after))

	return {user: iv.merge(entries) for user, entries in busy.items()}


def _event_busy(
	users: list[str], start: datetime.datetime, end: datetime.datetime
) -> dict[str, list[iv.Interval]]:
	"""Framework ``Event`` records owned by or involving these users.

	Appointments mirrored into Event are skipped — they are already counted, and
	double counting would make every appointment collide with its own shadow.
	"""
	busy: dict[str, list[iv.Interval]] = {u: [] for u in users}
	rows = frappe.get_all(
		"Event",
		filters={
			"status": "Open",
			"starts_on": ["<", to_system_naive(end)],
			"ends_on": [">", to_system_naive(start)],
		},
		fields=["name", "owner", "starts_on", "ends_on", "reference_doctype"],
		limit_page_length=0,
	)
	rows = [r for r in rows if r.reference_doctype != "CRM Appointment"]
	if not rows:
		return busy

	by_name = {r.name: r for r in rows}
	for row in rows:
		if row.owner in busy:
			busy[row.owner].append((from_system_naive(row.starts_on), from_system_naive(row.ends_on)))
	for row in frappe.get_all(
		"Event Participants",
		filters={"parent": ["in", list(by_name)], "email": ["in", users]},
		fields=["parent", "email"],
	):
		event = by_name.get(row.parent)
		if event and row.email in busy:
			busy[row.email].append((from_system_naive(event.starts_on), from_system_naive(event.ends_on)))
	return busy


def resource_usage(
	resources: list[str],
	start: datetime.datetime,
	end: datetime.datetime,
	exclude_appointment: str | None = None,
) -> dict[str, list[tuple[datetime.datetime, datetime.datetime, int]]]:
	"""Booked quantity per resource, so capacity can be checked with a sweep."""
	usage: dict[str, list] = {r: [] for r in resources}
	for row in _appointment_rows(
		"CRM Appointment Resource",
		"resource",
		resources,
		start,
		end,
		extra_fields=["quantity"],
		exclude=exclude_appointment,
	):
		usage[row.link].append(
			(
				from_system_naive(row.starts_on),
				from_system_naive(row.ends_on),
				max(cint(row.quantity), 1),
			)
		)
	return usage


def party_busy(
	parties: list[tuple[str, str]],
	start: datetime.datetime,
	end: datetime.datetime,
	exclude_appointment: str | None = None,
) -> dict[tuple[str, str], list[iv.Interval]]:
	"""When each client is already booked, keyed by ``(party_type, party)``."""
	busy: dict[tuple[str, str], list[iv.Interval]] = {p: [] for p in parties}
	names = [p[1] for p in parties if p[1]]
	if not names:
		return busy
	for row in _appointment_rows(
		"CRM Appointment Participant",
		"party",
		names,
		start,
		end,
		extra_fields=["party_type", "status"],
		exclude=exclude_appointment,
	):
		if row.status == "Cancelled":
			continue
		key = (row.party_type, row.link)
		if key in busy:
			busy[key].append((from_system_naive(row.starts_on), from_system_naive(row.ends_on)))
	return {key: iv.merge(entries) for key, entries in busy.items()}


def daily_counts(
	users: list[str], start: datetime.datetime, end: datetime.datetime
) -> dict[tuple[str, datetime.date], int]:
	"""Appointments per professional per day, for the daily cap."""
	counts: dict[tuple[str, datetime.date], int] = {}
	tz = scheduling_tz()
	for row in _appointment_rows("CRM Appointment Staff", "user", users, start, end):
		day = from_system_naive(row.starts_on).astimezone(tz).date()
		counts[(row.link, day)] = counts.get((row.link, day), 0) + 1
	return counts


# --------------------------------------------------------------------------
# slot finding
# --------------------------------------------------------------------------


@dataclass
class Slot:
	start: datetime.datetime
	end: datetime.datetime
	staff: list[str]
	resources: list[dict]
	seats_left: int = 1
	join_appointment: str | None = None

	def as_dict(self) -> dict:
		return {
			"start": self.start.isoformat(),
			"end": self.end.isoformat(),
			"staff": self.staff,
			"resources": self.resources,
			"seats_left": self.seats_left,
			"join_appointment": self.join_appointment,
		}


class SlotFinder:
	"""Free slots for one service over a date range.

	Loads every window and every busy interval for the whole range up front, then
	walks the candidate grid in memory — one query per source rather than one per
	slot.
	"""

	def __init__(
		self,
		service: str,
		from_date: datetime.date | str,
		to_date: datetime.date | str,
		staff: list[str] | None = None,
		resources: list[str] | None = None,
		participants: int = 1,
		exclude_appointment: str | None = None,
	):
		self.service = frappe.get_cached_doc("CRM Service", service)
		self.from_date = parse_date(from_date)
		self.to_date = parse_date(to_date)
		self.participants = max(cint(participants), 1)
		self.exclude = exclude_appointment
		self.tz = scheduling_tz()
		self.settings = settings()

		self.duration = datetime.timedelta(minutes=cint(self.service.duration))
		self.step = datetime.timedelta(
			minutes=cint(self.service.slot_interval) or cint(self.service.duration)
		)
		self.buffer_before = cint(self.service.buffer_before)
		self.buffer_after = cint(self.service.buffer_after)

		self.eligible = [row.user for row in self.service.staff]
		# a collective service always books its whole roster, so a staff filter can
		# only say "show me slots this person is in" — never shrink the team
		if staff and self.service.staff_selection != "All required":
			self.eligible = [u for u in self.eligible if u in set(staff)]
		self.roles = {}
		for row in self.service.staff:
			self.roles.setdefault(row.role or "", []).append(row.user)
		self.priority = {row.user: cint(row.priority) for row in self.service.staff}
		self.resource_filter = set(resources or [])
		self._loads: dict[str, int] = {}

	# -- window ------------------------------------------------------------

	def window(self) -> tuple[datetime.datetime, datetime.datetime]:
		start, _ = day_bounds(self.from_date, self.tz)
		_, end = day_bounds(self.to_date, self.tz)
		return start, end

	def bookable_window(self) -> tuple[datetime.datetime, datetime.datetime]:
		"""Notice period and horizon, as an absolute UTC window."""
		now = datetime.datetime.now(UTC)
		earliest = now + datetime.timedelta(hours=cint(self.service.min_notice_hours))
		horizon = cint(self.service.max_horizon_days) or 3650
		return earliest, now + datetime.timedelta(days=horizon)

	# -- resources ---------------------------------------------------------

	def _resource_candidates(self) -> list[dict]:
		"""One entry per requirement: the resources that could satisfy it."""
		requirements = []
		for row in self.service.resources:
			filters = {"enabled": 1}
			if row.resource:
				filters["name"] = row.resource
			elif row.resource_type:
				filters["resource_type"] = row.resource_type
			names = frappe.get_all("CRM Resource", filters=filters, pluck="name")
			if self.resource_filter:
				# a caller's resource picks narrow a requirement only where they can:
				# asking for "Room A" must not starve the requirement for a treadmill
				preferred = [n for n in names if n in self.resource_filter]
				names = preferred or names
			requirements.append(
				{
					"quantity": max(cint(row.quantity), 1),
					"required": bool(cint(row.required)),
					"label": row.resource or row.resource_type or _("Resource"),
					"candidates": names,
				}
			)
		return requirements

	# -- main --------------------------------------------------------------

	def run(self) -> list[Slot]:
		if not self.eligible or not cint(self.service.duration):
			return []

		start, end = self.window()
		earliest, latest = self.bookable_window()

		staff_hours = {u: staff_working_hours(u) for u in self.eligible}
		caps = {u: staff_daily_cap(u) for u in self.eligible}
		# ranking is the same for every candidate slot of this run: query it once
		self._loads = self.upcoming_load(self.eligible)
		counts = daily_counts(self.eligible, start, end)
		busy = staff_busy(
			self.eligible,
			start,
			end,
			self.buffer_before,
			self.buffer_after,
			exclude_appointment=self.exclude,
			include_google=bool(cint(self.settings.check_google_busy)),
		)
		service_hours = service_working_hours(self.service)

		requirements = self._resource_candidates()
		resource_names = sorted({n for req in requirements for n in req["candidates"]})
		resources = {n: frappe.get_cached_doc("CRM Resource", n) for n in resource_names}
		resource_hours = {n: resource_working_hours(doc) for n, doc in resources.items()}
		usage = resource_usage(resource_names, start, end, exclude_appointment=self.exclude)

		joinable = self._joinable_appointments(start, end) if self.is_group_service else {}

		slots: list[Slot] = []
		day = self.from_date
		while day <= self.to_date:
			# two days of windows: a late slot may run past midnight, and only a
			# slot that *starts* today belongs to today
			day_start, day_end = day_bounds(day, self.tz)
			service_windows = service_hours.for_span(day, 2, self.tz)
			free_by_user = {}
			for user in self.eligible:
				windows = staff_hours[user].for_span(day, 2, self.tz)
				if service_windows:
					windows = iv.intersect(windows, service_windows)
				free_by_user[user] = iv.subtract(windows, busy[user])

			candidates = iv.slots_in(
				iv.merge([w for windows in free_by_user.values() for w in windows]),
				self.duration,
				self.step,
			)
			for slot_start in candidates:
				slot_end = slot_start + self.duration
				if not (day_start <= slot_start < day_end):
					continue
				if not (earliest <= slot_start <= latest):
					continue
				free_now = [
					u
					for u in self.eligible
					if iv.covers(free_by_user[u], slot_start, slot_end)
					and not self._over_cap(u, day, caps, counts)
				]
				assigned = self.assign_staff(free_now)
				if not assigned:
					continue
				booked = self._assign_resources(
					requirements, resources, resource_hours, usage, slot_start, slot_end
				)
				if booked is None:
					continue
				slots.append(
					Slot(
						start=slot_start,
						end=slot_end,
						staff=assigned,
						resources=booked,
						seats_left=self.seats_for(booked),
					)
				)
			day += datetime.timedelta(days=1)

		slots.extend(joinable.values())
		slots.sort(key=lambda s: (s.start, s.join_appointment or ""))
		return slots

	def _over_cap(self, user, day, caps, counts) -> bool:
		cap = caps.get(user) or 0
		return bool(cap) and counts.get((user, day), 0) >= cap

	# -- staffing models ---------------------------------------------------

	@property
	def is_group_service(self) -> bool:
		return cint(self.service.max_participants) > 1

	def assign_staff(self, free: list[str]) -> list[str]:
		"""Turn the set of free professionals into a concrete assignment."""
		mode = self.service.staff_selection or "Any one"
		if mode == "All required":
			return list(self.eligible) if len(free) == len(self.eligible) else []
		if mode == "One per role":
			assigned = []
			for role in self.service.roles:
				pool = [u for u in self.roles.get(role.role or "", []) if u in free and u not in assigned]
				needed = max(cint(role.staff_count), 1)
				if len(pool) < needed:
					return []
				assigned.extend(self._rank(pool)[:needed])
			return assigned
		needed = max(cint(self.service.staff_count), 1)
		if len(free) < needed:
			return []
		return self._rank(free)[:needed]

	def _rank(self, users: list[str]) -> list[str]:
		"""Lowest priority number first, then the least-booked professional."""
		loads = self._loads or self.upcoming_load(users)
		return sorted(users, key=lambda u: (self.priority.get(u, 0), loads.get(u, 0), u))

	@staticmethod
	def upcoming_load(users: list[str]) -> dict[str, int]:
		if not users:
			return {}
		appointment = frappe.qb.DocType("CRM Appointment")
		staff = frappe.qb.DocType("CRM Appointment Staff")
		rows = (
			frappe.qb.from_(staff)
			.join(appointment)
			.on(staff.parent == appointment.name)
			.select(staff.user, Count(staff.name).as_("total"))
			.where(staff.user.isin(users))
			.where(appointment.status.isin(("Scheduled", "Confirmed")))
			.where(appointment.starts_on >= now_datetime())
			.groupby(staff.user)
			.run(as_dict=True)
		)
		return {row.user: cint(row.total) for row in rows}

	# -- resource assignment ----------------------------------------------

	def _assign_resources(
		self, requirements, resources, resource_hours, usage, slot_start, slot_end
	) -> list[dict] | None:
		"""Pick concrete resources for every requirement, or ``None`` if impossible.

		Greedy by remaining headroom: the least contended resource is taken first,
		which keeps a busy shared room free for the requirements that have no
		alternative.
		"""
		booked: list[dict] = []
		taken: dict[str, int] = {}
		for req in requirements:
			remaining = req["quantity"]
			options = []
			for name in req["candidates"]:
				doc = resources[name]
				day = slot_start.astimezone(self.tz).date()
				windows = resource_hours[name].for_span(day, 2, self.tz)
				if not iv.covers(windows, slot_start, slot_end):
					continue
				capacity = max(cint(doc.capacity), 1)
				used = iv.peak_usage(usage.get(name, []), slot_start, slot_end) + taken.get(name, 0)
				headroom = capacity - used
				if headroom > 0:
					options.append((headroom, name))
			options.sort(key=lambda x: (x[0], x[1]))
			for headroom, name in options:
				if remaining <= 0:
					break
				take = min(headroom, remaining)
				booked.append({"resource": name, "quantity": take})
				taken[name] = taken.get(name, 0) + take
				remaining -= take
			if remaining > 0 and req["required"]:
				return None
		return booked

	def seats_for(self, booked: list[dict]) -> int:
		"""Seats a slot offers: the service cap, narrowed by any room's own seats."""
		seats = max(cint(self.service.max_participants), 1)
		for row in booked:
			resource_seats = cint(frappe.get_cached_doc("CRM Resource", row["resource"]).seats)
			if resource_seats:
				seats = min(seats, resource_seats)
		return seats

	# -- group sessions ----------------------------------------------------

	def _joinable_appointments(self, start, end) -> dict[str, Slot]:
		"""Existing group sessions of this service that still have seats left."""
		out: dict[str, Slot] = {}
		rows = frappe.get_all(
			"CRM Appointment",
			filters={
				"service": self.service.name,
				"status": ["in", ("Scheduled", "Confirmed")],
				"starts_on": ["<", to_system_naive(end)],
				"ends_on": [">", to_system_naive(start)],
			},
			fields=["name", "starts_on", "ends_on"],
		)
		if not rows:
			return out
		names = [r.name for r in rows]
		booked: dict[str, int] = {}
		for row in frappe.get_all(
			"CRM Appointment Participant",
			filters={"parent": ["in", names], "status": ["!=", "Cancelled"]},
			fields=["parent", count_field()],
			group_by="parent",
		):
			booked[row.parent] = cint(row.total)
		staff_rows = frappe.get_all(
			"CRM Appointment Staff", filters={"parent": ["in", names]}, fields=["parent", "user"]
		)
		staff_by_appointment: dict[str, list[str]] = {}
		for row in staff_rows:
			staff_by_appointment.setdefault(row.parent, []).append(row.user)
		resource_rows = frappe.get_all(
			"CRM Appointment Resource",
			filters={"parent": ["in", names]},
			fields=["parent", "resource", "quantity"],
		)
		resources_by_appointment: dict[str, list[dict]] = {}
		for row in resource_rows:
			resources_by_appointment.setdefault(row.parent, []).append(
				{"resource": row.resource, "quantity": max(cint(row.quantity), 1)}
			)

		earliest, latest = self.bookable_window()
		for row in rows:
			slot_start = from_system_naive(row.starts_on)
			if not (earliest <= slot_start <= latest):
				continue
			assigned_resources = resources_by_appointment.get(row.name, [])
			seats = self.seats_for(assigned_resources)
			left = seats - booked.get(row.name, 0)
			if left < self.participants:
				continue
			out[row.name] = Slot(
				start=slot_start,
				end=from_system_naive(row.ends_on),
				staff=staff_by_appointment.get(row.name, []),
				resources=assigned_resources,
				seats_left=left,
				join_appointment=row.name,
			)
		return out


def get_slots(
	service: str,
	from_date,
	to_date,
	staff: list[str] | None = None,
	resources: list[str] | None = None,
	participants: int = 1,
	exclude_appointment: str | None = None,
) -> list[Slot]:
	return SlotFinder(
		service,
		from_date,
		to_date,
		staff=staff,
		resources=resources,
		participants=participants,
		exclude_appointment=exclude_appointment,
	).run()


# --------------------------------------------------------------------------
# conflict detection
# --------------------------------------------------------------------------


def find_conflicts(doc) -> list[str]:
	"""Human-readable reasons this appointment cannot be booked as it stands.

	Used both by the controller (to block a save) and by the UI (to warn while the
	user is still editing), so the two can never disagree.
	"""
	config = settings()
	if doc.status == "Cancelled":
		return []

	start = from_system_naive(doc.starts_on)
	end = from_system_naive(doc.ends_on)
	if end <= start:
		return [_("End time must be after start time")]

	service = frappe.get_cached_doc("CRM Service", doc.service) if doc.service else None
	buffer_before = cint(service.buffer_before) if service else 0
	buffer_after = cint(service.buffer_after) if service else 0
	conflicts: list[str] = []

	users = [row.user for row in doc.staff if row.user]
	if users and cint(config.enforce_staff_conflicts):
		busy = staff_busy(users, start, end, buffer_before, buffer_after, exclude_appointment=doc.name)
		for user in users:
			if iv.overlaps(busy[user], start, end):
				conflicts.append(_("{0} is already booked in this time slot").format(_user_label(user)))

	if users and cint(config.enforce_working_hours):
		tz = scheduling_tz()
		day = start.astimezone(tz).date()
		for user in users:
			if not iv.covers(staff_working_hours(user).for_span(day, 2, tz), start, end):
				conflicts.append(_("{0} does not work in this time slot").format(_user_label(user)))

	if cint(config.enforce_resource_conflicts):
		wanted: dict[str, int] = {}
		for row in doc.resources:
			if row.resource:
				wanted[row.resource] = wanted.get(row.resource, 0) + max(cint(row.quantity), 1)
		if wanted:
			usage = resource_usage(list(wanted), start, end, exclude_appointment=doc.name)
			tz = scheduling_tz()
			day = start.astimezone(tz).date()
			for name, quantity in wanted.items():
				resource = frappe.get_cached_doc("CRM Resource", name)
				capacity = max(cint(resource.capacity), 1)
				used = iv.peak_usage(usage.get(name, []), start, end)
				if used + quantity > capacity:
					conflicts.append(
						_("{0} is fully booked in this time slot ({1} of {2} in use)").format(
							resource.resource_name, used, capacity
						)
					)
				if not iv.covers(resource_working_hours(resource).for_span(day, 2, tz), start, end):
					conflicts.append(
						_("{0} is not available in this time slot").format(resource.resource_name)
					)

	if cint(config.enforce_participant_conflicts):
		parties = [
			(row.party_type, row.party) for row in doc.participants if row.party and row.status != "Cancelled"
		]
		if parties:
			busy = party_busy(parties, start, end, exclude_appointment=doc.name)
			for row in doc.participants:
				key = (row.party_type, row.party)
				if key in busy and iv.overlaps(busy[key], start, end):
					conflicts.append(
						_("{0} already has another appointment in this time slot").format(
							row.participant_name or row.party
						)
					)

	seats = cint(service.max_participants) if service else 1
	active = [row for row in doc.participants if row.status != "Cancelled"]
	if seats and len(active) > seats:
		conflicts.append(
			_("This service takes at most {0} participants, {1} listed").format(seats, len(active))
		)
	for row in doc.resources:
		resource_seats = cint(frappe.db.get_value("CRM Resource", row.resource, "seats"))
		if resource_seats and len(active) > resource_seats:
			conflicts.append(
				_("{0} seats {1} people, {2} listed").format(row.resource, resource_seats, len(active))
			)

	return conflicts


def _user_label(user: str) -> str:
	return frappe.db.get_value("User", user, "full_name") or user
