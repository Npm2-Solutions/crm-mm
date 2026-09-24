# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The stretch of time a widget measures, and the one it is compared with.

Pure date arithmetic, no database: runs with plain ``unittest`` too.

A period is a pair of calendar days, both included — 1 to 30 September is thirty
days. The comparison period is the same number of days immediately before it,
so "this month so far" on the 24th is compared with the 24 days that precede
it, not with the whole of last month: a half-finished month against a full one
would read as a collapse every morning.
"""

from __future__ import annotations

import datetime

DateLike = datetime.date | datetime.datetime | str | None


def to_date(value: DateLike) -> datetime.date | None:
	"""A date out of whatever the request carried: a date, a datetime or ISO text."""
	if value is None or value == "":
		return None
	if isinstance(value, datetime.datetime):
		return value.date()
	if isinstance(value, datetime.date):
		return value
	try:
		return datetime.date.fromisoformat(str(value).strip()[:10])
	except ValueError:
		return None


def normalize(
	from_date: DateLike, to_date_: DateLike, today: datetime.date
) -> tuple[datetime.date, datetime.date]:
	"""A usable (from, to): missing ends fall back to this month, reversed ends are swapped."""
	start = to_date(from_date)
	end = to_date(to_date_)
	if not start and not end:
		start = today.replace(day=1)
		end = last_day_of_month(today)
	elif not start:
		start = end.replace(day=1)
	elif not end:
		end = max(start, today)
	if start > end:
		start, end = end, start
	return start, end


def last_day_of_month(day: datetime.date) -> datetime.date:
	following = (day.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
	return following - datetime.timedelta(days=1)


def length(start: datetime.date, end: datetime.date) -> int:
	"""Days in the period, both ends included."""
	return (end - start).days + 1


def previous(start: datetime.date, end: datetime.date) -> tuple[datetime.date, datetime.date]:
	"""The period of the same length that ends the day before this one starts."""
	days = length(start, end)
	prev_end = start - datetime.timedelta(days=1)
	return prev_end - datetime.timedelta(days=days - 1), prev_end


def bounds(start: datetime.date, end: datetime.date) -> tuple[datetime.datetime, datetime.datetime]:
	"""Datetimes for a half-open range: midnight of the first day, midnight after the last.

	Comparing a datetime column with ``<= '2026-09-30'`` drops everything that
	happened on the 30th after midnight; ``< '2026-10-01 00:00'`` does not.
	"""
	return (
		datetime.datetime.combine(start, datetime.time.min),
		datetime.datetime.combine(end + datetime.timedelta(days=1), datetime.time.min),
	)


def days(start: datetime.date, end: datetime.date) -> list[datetime.date]:
	"""Every day of the period, in order — the x axis of a daily chart."""
	return [start + datetime.timedelta(days=offset) for offset in range(length(start, end))]


def grain(start: datetime.date, end: datetime.date) -> str:
	"""How finely a trend over this period should be cut: by day, week or month.

	Ninety bars are still readable; a year of days is a barcode.
	"""
	span = length(start, end)
	if span <= 62:
		return "day"
	if span <= 190:
		return "week"
	return "month"


def bucket(day: datetime.date, grain_: str) -> datetime.date:
	"""The first day of the bucket ``day`` falls into, for the given grain."""
	if grain_ == "week":
		return day - datetime.timedelta(days=day.weekday())
	if grain_ == "month":
		return day.replace(day=1)
	return day


def buckets(start: datetime.date, end: datetime.date, grain_: str) -> list[datetime.date]:
	"""Every bucket start covering the period, so empty stretches show as zero, not as a gap."""
	seen: list[datetime.date] = []
	for day in days(start, end):
		key = bucket(day, grain_)
		if not seen or seen[-1] != key:
			seen.append(key)
	return seen


def delta_percent(current: float | None, before: float | None) -> float | None:
	"""Change against the previous period, in percent; ``None`` when there is nothing to compare with.

	From zero to anything is not an infinite rise, it is no comparison at all.
	"""
	if before in (None, 0) or current is None:
		return None
	return (current - before) / abs(before) * 100
