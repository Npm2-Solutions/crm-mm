# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The shapes a widget answers in — pure, no database: runs with plain ``unittest`` too.

Widgets return data, never drawing instructions: numbers, series, slices, rows.
How it looks — colours, fonts, number formats in the reader's locale — is the
browser's job, the same for every widget. So a widget never says "blue" or
"€ 1.234,00"; it says ``format="currency"`` and hands over 1234.

Formats: ``number``, ``currency`` (in the dashboard currency, unless the payload
names another), ``percent`` (0 to 100), ``duration`` (seconds), ``days``,
``ratio`` (a multiple: return on ad spend is "3.2 times").
"""

from __future__ import annotations

import datetime
from collections.abc import Iterable
from typing import Any

from crm.dashboard.periods import delta_percent

FORMATS = ("number", "currency", "percent", "duration", "days", "ratio")

# a donut past six slices stops being part-to-whole and becomes a colour quiz
MAX_SLICES = 6


def number(
	value: float | None,
	previous: float | None = None,
	*,
	format: str = "number",
	negative_is_better: bool = False,
	compare: str = "percent",
	route: dict | None = None,
	hint: str | None = None,
	progress: float | None = None,
	currency: str | None = None,
) -> dict[str, Any]:
	"""A KPI: one value, and how it moved against the previous period.

	``compare="percent"`` reports the change as a percentage of the previous value
	(counts, amounts); ``compare="points"`` as a plain difference (rates already
	in percent, where "+5%" of 40% would be ambiguous). ``progress`` (0 to 100)
	draws a meter under the value — occupancy, share reported.
	"""
	value = _num(value)
	payload: dict[str, Any] = {"kind": "number", "value": value, "format": _format(format)}
	if previous is not None:
		previous = _num(previous)
		payload["previous"] = previous
		if compare == "points":
			payload["delta"] = round(value - previous, 2)
			payload["deltaUnit"] = "points"
		else:
			change = delta_percent(value, previous)
			if change is not None:
				payload["delta"] = round(change, 1)
				payload["deltaUnit"] = "percent"
	if negative_is_better:
		payload["negativeIsBetter"] = True
	if route:
		payload["route"] = route
	if hint:
		payload["hint"] = hint
	if progress is not None:
		payload["progress"] = max(0.0, min(100.0, round(_num(progress), 1)))
	if currency:
		payload["currency"] = currency
	return payload


def series(name: str, label: str, values: list[float], type: str = "line") -> dict[str, Any]:
	return {"name": name, "label": label, "type": type, "values": [_num(value) for value in values]}


def trend(
	buckets: list[datetime.date],
	grain: str,
	lines: list[dict[str, Any]],
	*,
	format: str = "number",
	stacked: bool = False,
) -> dict[str, Any]:
	"""A chart over time: one point per bucket (day, week or month) for every series.

	``lines`` are ``series(...)`` built against the same buckets, so every series
	has a value — zero included — at every point of the axis.
	"""
	return {
		"kind": "axis",
		"x": {"type": "time", "grain": grain, "values": [day.isoformat() for day in buckets]},
		"series": lines,
		"stacked": stacked,
		"format": _format(format),
	}


def bars(
	rows: list[dict[str, Any]],
	*,
	label_key: str,
	lines: list[tuple[str, str]],
	format: str = "number",
	horizontal: bool = True,
	stacked: bool = False,
) -> dict[str, Any]:
	"""A bar chart over categories — a ranking when ``horizontal`` (long names read sideways).

	``lines`` are ``(key in each row, label)``; one line is a plain ranking, more
	than one a grouped (or ``stacked``) comparison. One scale for all of them: two
	measures of different size belong in two widgets, not on a second axis.
	"""
	return {
		"kind": "axis",
		"x": {"type": "category", "values": [_label(row.get(label_key)) for row in rows]},
		"series": [series(key, label, [row.get(key) for row in rows], type="bar") for key, label in lines],
		"horizontal": horizontal,
		"stacked": stacked,
		"format": _format(format),
	}


def donut(
	rows: Iterable[tuple[Any, float]],
	*,
	format: str = "number",
	other_label: str = "Other",
	empty_label: str = "Not set",
) -> dict[str, Any]:
	"""Part-to-whole. The biggest five slices stay, the rest fold into one "Other"."""
	slices = [(_label(label, empty_label), _num(value)) for label, value in rows]
	slices = [entry for entry in slices if entry[1] > 0]
	slices.sort(key=lambda entry: entry[1], reverse=True)
	if len(slices) > MAX_SLICES:
		kept = slices[: MAX_SLICES - 1]
		rest = sum(value for _label_, value in slices[MAX_SLICES - 1 :])
		slices = [*kept, (other_label, rest)]
	return {
		"kind": "donut",
		"slices": [{"label": label, "value": value} for label, value in slices],
		"total": sum(value for _label_, value in slices),
		"format": _format(format),
	}


def funnel(steps: list[tuple[str, float]], *, format: str = "number") -> dict[str, Any]:
	"""Ordered stages, each with the share of the first one it kept."""
	first = _num(steps[0][1]) if steps else 0
	out = []
	for index, (label, value) in enumerate(steps):
		value = _num(value)
		before = _num(steps[index - 1][1]) if index else None
		out.append(
			{
				"label": _label(label),
				"value": value,
				"ofFirst": round(value / first * 100, 1) if first else None,
				"ofPrevious": round(value / before * 100, 1) if before else None,
			}
		)
	return {"kind": "funnel", "steps": out, "format": _format(format)}


def listing(
	items: list[dict[str, Any]],
	*,
	empty: str | None = None,
	more: dict | None = None,
	total: int | None = None,
) -> dict[str, Any]:
	"""Records to act on. Each item: ``title``, and optionally ``subtitle``, ``time``
	(ISO, shown relative or as a clock), ``badge`` (``{label, color}``), ``user``
	(an avatar), ``icon``, ``value`` + ``format``, ``route`` (where a click goes)."""
	payload: dict[str, Any] = {"kind": "list", "items": items}
	if empty:
		payload["empty"] = empty
	if more:
		payload["more"] = more
	if total is not None:
		payload["total"] = total
	return payload


def table(
	columns: list[dict[str, Any]],
	rows: list[dict[str, Any]],
	*,
	empty: str | None = None,
) -> dict[str, Any]:
	"""Columns ``{key, label, format?}`` over rows of plain values; ``format`` as for numbers,
	plus ``text`` and ``user`` (an avatar and a name)."""
	payload: dict[str, Any] = {"kind": "table", "columns": columns, "rows": rows}
	if empty:
		payload["empty"] = empty
	return payload


def heatmap(
	counts: dict[tuple[int, int], float],
	*,
	x_labels: list[str],
	y_labels: list[str],
	format: str = "number",
) -> dict[str, Any]:
	"""Values on a grid — hours across, weekdays down. ``counts`` is ``{(x, y): value}``."""
	cells = [[x, y, _num(value)] for (x, y), value in sorted(counts.items()) if _num(value)]
	return {
		"kind": "heatmap",
		"x": x_labels,
		"y": y_labels,
		"cells": cells,
		"max": max((cell[2] for cell in cells), default=0),
		"format": _format(format),
	}


def fill(buckets: list[datetime.date], values: dict[datetime.date, float]) -> list[float]:
	"""Values aligned with the buckets, zero where nothing happened."""
	return [_num(values.get(bucket_)) for bucket_ in buckets]


def ratio(part: float | None, whole: float | None) -> float | None:
	"""``part`` as a percentage of ``whole``; ``None`` when there is no whole to divide by."""
	whole = _num(whole)
	if not whole:
		return None
	return round(_num(part) / whole * 100, 1)


def _num(value: Any) -> float:
	if value is None or value == "":
		return 0
	try:
		number_ = float(value)
	except (TypeError, ValueError):
		return 0
	return int(number_) if number_.is_integer() else round(number_, 2)


def _label(value: Any, empty: str = "Not set") -> str:
	text = "" if value is None else str(value).strip()
	return text[:120] or empty


def _format(value: str) -> str:
	return value if value in FORMATS else "number"
