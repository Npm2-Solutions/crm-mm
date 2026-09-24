# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The limits a service puts on *online* self-booking.

The availability engine answers "who and what is free". An online client needs a
second, stricter filter on top of it: the practice may be free at 19:30 today,
but it does not want strangers booking the same evening, nor the same client
holding five future slots, nor a laser treatment repeated after three days.

Everything here is pure — plain values in, reasons out — so the rules can be
tested without a database and reused by the public page, the connectors that
receive bookings from external platforms, and the staff calendar preview.

Each check returns ``None`` when the booking is fine, or a short machine code
(``LIMIT_*``) the caller turns into a translated message. Codes, not strings,
because the same rule reads differently to a client on the booking page and to
a receptionist inspecting an imported booking.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field

LIMIT_TOO_SOON = "too_soon"
LIMIT_TOO_FAR = "too_far"
LIMIT_NOT_OPEN_YET = "not_open_yet"
LIMIT_CLOSED = "closed"
LIMIT_SAME_DAY_CUTOFF = "same_day_cutoff"
LIMIT_SERVICE_DAY_FULL = "service_day_full"
LIMIT_SERVICE_WEEK_FULL = "service_week_full"
LIMIT_CONCURRENT = "concurrent"
LIMIT_CLIENT_ACTIVE = "client_active"
LIMIT_CLIENT_DAY = "client_day"
LIMIT_CLIENT_SPACING = "client_spacing"
LIMIT_NEW_ONLY = "new_only"
LIMIT_RETURNING_ONLY = "returning_only"
LIMIT_CANCEL_DISABLED = "cancel_disabled"
LIMIT_CANCEL_NOTICE = "cancel_notice"
LIMIT_RESCHEDULE_DISABLED = "reschedule_disabled"
LIMIT_RESCHEDULE_NOTICE = "reschedule_notice"
LIMIT_RESCHEDULE_COUNT = "reschedule_count"
LIMIT_IN_PAST = "in_past"

Interval = tuple[datetime.datetime, datetime.datetime]


def _int(value) -> int:
	try:
		return max(int(value or 0), 0)
	except (TypeError, ValueError):
		return 0


def _date(value) -> datetime.date | None:
	if not value:
		return None
	if isinstance(value, datetime.datetime):
		return value.date()
	if isinstance(value, datetime.date):
		return value
	return datetime.date.fromisoformat(str(value)[:10])


def _time(value) -> datetime.time | None:
	if value in (None, ""):
		return None
	if isinstance(value, datetime.time):
		return value
	if isinstance(value, datetime.timedelta):
		total = int(value.total_seconds())
		return datetime.time(total // 3600 % 24, total // 60 % 60, total % 60)
	return datetime.time.fromisoformat(str(value))


@dataclass
class OnlineRules:
	"""The online-booking knobs of one service, normalised.

	Built from a ``CRM Service`` document (or any mapping with the same field
	names) through :meth:`from_service`, so tests can build one from a dict.
	"""

	min_notice_hours: int = 0
	max_horizon_days: int = 0
	opens_on: datetime.date | None = None
	closes_on: datetime.date | None = None
	same_day_cutoff: datetime.time | None = None
	max_per_day: int = 0
	max_per_week: int = 0
	max_concurrent: int = 0
	max_active_per_customer: int = 0
	max_per_customer_per_day: int = 0
	min_days_between: int = 0
	eligibility: str = "Everyone"
	allow_cancel: bool = True
	cancel_notice_hours: int = 0
	allow_reschedule: bool = True
	reschedule_notice_hours: int = 0
	max_reschedules: int = 0
	global_max_active_per_customer: int = 0

	@classmethod
	def from_service(cls, service, global_max_active: int = 0) -> OnlineRules:
		get = service.get if hasattr(service, "get") else lambda k, d=None: getattr(service, k, d)

		def flag(key, default=1):
			value = get(key)
			return bool(default if value is None else int(value))

		return cls(
			min_notice_hours=_int(get("min_notice_hours")),
			max_horizon_days=_int(get("max_horizon_days")),
			opens_on=_date(get("booking_opens_on")),
			closes_on=_date(get("booking_closes_on")),
			same_day_cutoff=_time(get("same_day_cutoff")),
			max_per_day=_int(get("max_bookings_per_day")),
			max_per_week=_int(get("max_bookings_per_week")),
			max_concurrent=_int(get("max_concurrent")),
			max_active_per_customer=_int(get("max_active_per_customer")),
			max_per_customer_per_day=_int(get("max_per_customer_per_day")),
			min_days_between=_int(get("min_days_between")),
			eligibility=get("customer_eligibility") or "Everyone",
			allow_cancel=flag("allow_online_cancel"),
			cancel_notice_hours=_int(get("cancel_notice_hours")),
			allow_reschedule=flag("allow_online_reschedule"),
			reschedule_notice_hours=_int(get("reschedule_notice_hours")),
			max_reschedules=_int(get("max_reschedules")),
			global_max_active_per_customer=_int(global_max_active),
		)

	# -- window --------------------------------------------------------------

	def window(self, now: datetime.datetime) -> tuple[datetime.datetime, datetime.datetime | None]:
		"""Earliest and latest bookable instant (aware), from notice and horizon."""
		earliest = now + datetime.timedelta(hours=self.min_notice_hours)
		latest = now + datetime.timedelta(days=self.max_horizon_days) if self.max_horizon_days else None
		return earliest, latest

	def check_time(self, start: datetime.datetime, now: datetime.datetime, tz) -> str | None:
		"""Is ``start`` inside the bookable window at all?"""
		if start <= now:
			return LIMIT_IN_PAST
		earliest, latest = self.window(now)
		if start < earliest:
			return LIMIT_TOO_SOON
		if latest and start > latest:
			return LIMIT_TOO_FAR
		local_day = start.astimezone(tz).date()
		if self.opens_on and local_day < self.opens_on:
			return LIMIT_NOT_OPEN_YET
		if self.closes_on and local_day > self.closes_on:
			return LIMIT_CLOSED
		if self.same_day_cutoff:
			local_now = now.astimezone(tz)
			if local_day == local_now.date() and local_now.time() >= self.same_day_cutoff:
				return LIMIT_SAME_DAY_CUTOFF
		return None

	# -- service capacity -----------------------------------------------------

	def check_capacity(
		self,
		start: datetime.datetime,
		end: datetime.datetime,
		booked: list[Interval],
		tz,
	) -> str | None:
		"""Service-wide caps, against the service's other active appointments."""
		if self.max_per_day:
			day = start.astimezone(tz).date()
			if sum(1 for s, _e in booked if s.astimezone(tz).date() == day) >= self.max_per_day:
				return LIMIT_SERVICE_DAY_FULL
		if self.max_per_week:
			week = start.astimezone(tz).isocalendar()[:2]
			if sum(1 for s, _e in booked if s.astimezone(tz).isocalendar()[:2] == week) >= self.max_per_week:
				return LIMIT_SERVICE_WEEK_FULL
		if self.max_concurrent:
			if peak_overlap(booked, start, end) >= self.max_concurrent:
				return LIMIT_CONCURRENT
		return None

	# -- the client -------------------------------------------------------------

	def check_client(
		self,
		start: datetime.datetime,
		now: datetime.datetime,
		tz,
		history: ClientHistory,
	) -> str | None:
		"""Per-client limits. ``history`` holds the client's own appointments."""
		if self.eligibility == "New customers only" and history.is_returning:
			return LIMIT_NEW_ONLY
		if self.eligibility == "Returning customers only" and not history.is_returning:
			return LIMIT_RETURNING_ONLY

		upcoming_service = [s for s in history.service_starts if s > now]
		if self.max_active_per_customer and len(upcoming_service) >= self.max_active_per_customer:
			return LIMIT_CLIENT_ACTIVE
		upcoming_all = [s for s in history.all_starts if s > now]
		if self.global_max_active_per_customer and len(upcoming_all) >= self.global_max_active_per_customer:
			return LIMIT_CLIENT_ACTIVE
		if self.max_per_customer_per_day:
			day = start.astimezone(tz).date()
			if (
				sum(1 for s in history.all_starts if s.astimezone(tz).date() == day)
				>= self.max_per_customer_per_day
			):
				return LIMIT_CLIENT_DAY
		if self.min_days_between:
			gap = datetime.timedelta(days=self.min_days_between)
			for other in history.service_starts:
				if abs(other - start) < gap:
					return LIMIT_CLIENT_SPACING
		return None

	# -- after booking --------------------------------------------------------

	def check_cancel(self, start: datetime.datetime, now: datetime.datetime) -> str | None:
		if not self.allow_cancel:
			return LIMIT_CANCEL_DISABLED
		if start - now < datetime.timedelta(hours=self.cancel_notice_hours):
			return LIMIT_CANCEL_NOTICE
		return None

	def check_reschedule(self, start: datetime.datetime, now: datetime.datetime, done: int = 0) -> str | None:
		if not self.allow_reschedule:
			return LIMIT_RESCHEDULE_DISABLED
		if self.max_reschedules and _int(done) >= self.max_reschedules:
			return LIMIT_RESCHEDULE_COUNT
		if start - now < datetime.timedelta(hours=self.reschedule_notice_hours):
			return LIMIT_RESCHEDULE_NOTICE
		return None


@dataclass
class ClientHistory:
	"""A client's active appointments, as aware start instants."""

	service_starts: list[datetime.datetime] = field(default_factory=list)
	all_starts: list[datetime.datetime] = field(default_factory=list)
	#: has the client ever been seen before (any past appointment or record)
	is_returning: bool = False


def peak_overlap(booked: list[Interval], start: datetime.datetime, end: datetime.datetime) -> int:
	"""Most appointments running at the same instant inside ``[start, end)``."""
	events = []
	for s, e in booked:
		s, e = max(s, start), min(e, end)
		if s < e:
			events.append((s, 1))
			events.append((e, -1))
	peak = current = 0
	# ends sort before starts at the same instant: back-to-back is not overlap
	for _moment, delta in sorted(events, key=lambda x: (x[0], x[1])):
		current += delta
		peak = max(peak, current)
	return peak


def filter_slots(
	rules: OnlineRules,
	slots: list,
	now: datetime.datetime,
	tz,
	booked: list[Interval],
) -> list:
	"""Drop the slots an online client may not take.

	``slots`` are objects with aware ``start``/``end`` (the engine's ``Slot``);
	client-specific rules are left to booking time, since the page does not know
	who the client is until the form is filled in.
	"""
	out = []
	for slot in slots:
		if rules.check_time(slot.start, now, tz):
			continue
		# a joinable group slot adds a participant, not an appointment
		if not getattr(slot, "join_appointment", None) and rules.check_capacity(
			slot.start, slot.end, booked, tz
		):
			continue
		out.append(slot)
	return out


def thin_grid(slots: list, interval_minutes: int, tz) -> list:
	"""Keep only the start times aligned to a coarser online grid.

	Staff may book at any 5' step, while the public page offers :00 and :30 only.
	Alignment is measured from local midnight so the grid reads naturally.
	"""
	if not interval_minutes:
		return slots
	out = []
	for slot in slots:
		local = slot.start.astimezone(tz)
		if (local.hour * 60 + local.minute) % interval_minutes == 0 or getattr(
			slot, "join_appointment", None
		):
			out.append(slot)
	return out
