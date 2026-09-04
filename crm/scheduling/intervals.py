# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Interval algebra for the scheduling engine.

Pure functions on ``(start, end)`` tuples of timezone-aware datetimes. No Frappe
imports on purpose: this is the piece every availability question reduces to, so
it stays trivially testable and reusable.

Convention everywhere: intervals are half-open, ``start <= t < end``. Two
intervals that merely touch (``a.end == b.start``) do NOT overlap — that is what
makes back-to-back appointments legal.
"""

from __future__ import annotations

import datetime

Interval = tuple[datetime.datetime, datetime.datetime]


def normalize(intervals: list[Interval]) -> list[Interval]:
	"""Drop empty intervals and sort by start."""
	return sorted((s, e) for s, e in intervals if s < e)


def merge(intervals: list[Interval]) -> list[Interval]:
	"""Union: overlapping and touching intervals collapse into one."""
	out: list[Interval] = []
	for start, end in normalize(intervals):
		if out and start <= out[-1][1]:
			if end > out[-1][1]:
				out[-1] = (out[-1][0], end)
		else:
			out.append((start, end))
	return out


def intersect(a: list[Interval], b: list[Interval]) -> list[Interval]:
	"""Intervals covered by both sets."""
	a, b = merge(a), merge(b)
	out: list[Interval] = []
	i = j = 0
	while i < len(a) and j < len(b):
		start = max(a[i][0], b[j][0])
		end = min(a[i][1], b[j][1])
		if start < end:
			out.append((start, end))
		# advance whichever interval ends first
		if a[i][1] < b[j][1]:
			i += 1
		else:
			j += 1
	return out


def intersect_all(sets: list[list[Interval]]) -> list[Interval]:
	"""Intervals covered by every set. An empty list of sets means 'no constraint'
	and yields an empty result — callers decide what that means."""
	if not sets:
		return []
	out = merge(sets[0])
	for other in sets[1:]:
		out = intersect(out, other)
		if not out:
			break
	return out


def subtract(base: list[Interval], holes: list[Interval]) -> list[Interval]:
	"""``base`` minus every part covered by ``holes``."""
	holes = merge(holes)
	out: list[Interval] = []
	for start, end in merge(base):
		cursor = start
		for hole_start, hole_end in holes:
			if hole_end <= cursor:
				continue
			if hole_start >= end:
				break
			if hole_start > cursor:
				out.append((cursor, min(hole_start, end)))
			cursor = max(cursor, hole_end)
			if cursor >= end:
				break
		if cursor < end:
			out.append((cursor, end))
	return out


def clamp(intervals: list[Interval], start: datetime.datetime, end: datetime.datetime) -> list[Interval]:
	"""Restrict every interval to the ``[start, end)`` window."""
	return intersect(intervals, [(start, end)])


def overlaps(intervals: list[Interval], start: datetime.datetime, end: datetime.datetime) -> bool:
	"""True when any interval overlaps ``[start, end)``."""
	return any(s < end and e > start for s, e in intervals)


def covers(intervals: list[Interval], start: datetime.datetime, end: datetime.datetime) -> bool:
	"""True when ``[start, end)`` sits entirely inside the union of the set."""
	for s, e in merge(intervals):
		if s <= start and e >= end:
			return True
	return False


def peak_usage(
	usage: list[tuple[datetime.datetime, datetime.datetime, int]],
	start: datetime.datetime,
	end: datetime.datetime,
) -> int:
	"""Highest simultaneous load inside ``[start, end)``.

	``usage`` carries a quantity per interval (one room booked twice, two units of
	the same equipment, …). Sweep line over the boundary events: the maximum the
	running total reaches while inside the window is what a capacity check needs.
	"""
	events: list[tuple[datetime.datetime, int]] = []
	for s, e, qty in usage:
		s, e = max(s, start), min(e, end)
		if s < e:
			events.append((s, qty))
			events.append((e, -qty))
	if not events:
		return 0
	events.sort(key=lambda x: (x[0], x[1]))
	running = peak = 0
	for _, delta in events:
		running += delta
		peak = max(peak, running)
	return peak


def slots_in(
	windows: list[Interval], duration: datetime.timedelta, step: datetime.timedelta
) -> list[datetime.datetime]:
	"""Every slot start of ``duration`` that fits in ``windows``, walked in ``step``.

	Each window is walked from its own start, so a 09:00-12:00 + 14:00-18:00 day
	produces slots aligned to 09:00 and to 14:00 rather than to one global grid.
	"""
	if duration <= datetime.timedelta(0) or step <= datetime.timedelta(0):
		return []
	starts: list[datetime.datetime] = []
	for window_start, window_end in merge(windows):
		cursor = window_start
		while cursor + duration <= window_end:
			starts.append(cursor)
			cursor += step
	return sorted(set(starts))
