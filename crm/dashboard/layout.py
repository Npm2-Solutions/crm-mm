# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Where widgets sit on the grid — pure, no database: runs with plain ``unittest`` too.

A layout is the list the grid in the browser works with, one entry per widget::

        {
            "name": "whatsapp_received",
            "type": "number",
            "layout": {"x": 0, "y": 0, "w": 4, "h": 3, "i": "whatsapp_received"},
            "config": {"title": "WhatsApp in", "period": "today"},
        }

``name`` is the widget, ``layout`` its place on a 20-column grid of 42px rows,
``config`` what the person changed about it. The same shape the dashboard has
always saved, so layouts saved before the builder existed still load.

Two jobs live here. ``pack`` turns a template's rows into positions, sharing each
row between whatever widgets the site can show — three KPIs out of five get a
third of the row each, not a gap where WhatsApp would have been. ``sanitize``
cleans a layout coming back from the browser before it is stored: it is the
only part of the dashboard a person writes directly.
"""

from __future__ import annotations

import re
from typing import Any

GRID_COLUMNS = 20
MAX_ITEMS = 80
MAX_HEIGHT = 40
MAX_CONFIG_KEYS = 20
MAX_TEXT = 140

# the widgets that are layout, not data: nothing to ask the server for
SPACER = "spacer"
HEADING = "heading"
STRUCTURAL = (SPACER, HEADING)


def split(total: int, parts: int) -> list[int]:
	"""``total`` columns shared as evenly as whole columns allow, wider ones first."""
	if parts <= 0:
		return []
	base, extra = divmod(total, parts)
	return [base + (1 if index < extra else 0) for index in range(parts)]


def slug(value: str) -> str:
	cleaned = re.sub(r"[^a-z0-9_]+", "_", str(value or "").lower()).strip("_")
	return cleaned[:40] or "widget"


def new_key(name: str, taken: set[str]) -> str:
	"""A grid key for ``name`` that nothing else on the layout uses; remembered in ``taken``.

	Deterministic on purpose: a template rebuilt on every visit gives every widget
	the same key each time, so the browser does not redraw what did not change.
	"""
	base = slug(name)
	key = base
	counter = 2
	while key in taken:
		key = f"{base}_{counter}"
		counter += 1
	taken.add(key)
	return key


def pack(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
	"""Positions for a template, one grid row per line (or more, if a line is crowded).

	Each line is ``{"items": [{"name", "type", "config"?}], "h": rows, "min_w": columns}``.
	A line never leaves a hole: its widgets share the full width. When a line holds
	more widgets than fit at ``min_w`` columns each, it wraps onto a second row.
	"""
	items: list[dict[str, Any]] = []
	taken: set[str] = set()
	y = 0
	for line in lines:
		entries = [entry for entry in line.get("items") or [] if entry and entry.get("name")]
		if not entries:
			continue
		height = _clamp(line.get("h"), 1, MAX_HEIGHT, 3)
		min_width = _clamp(line.get("min_w"), 1, GRID_COLUMNS, 4)
		per_row = max(1, GRID_COLUMNS // min_width)
		for start in range(0, len(entries), per_row):
			chunk = entries[start : start + per_row]
			x = 0
			for entry, width in zip(chunk, split(GRID_COLUMNS, len(chunk)), strict=True):
				item = {
					"name": entry["name"],
					"type": entry.get("type") or "",
					"layout": {"x": x, "y": y, "w": width, "h": height, "i": new_key(entry["name"], taken)},
				}
				if entry.get("config"):
					item["config"] = dict(entry["config"])
				items.append(item)
				x += width
			y += height
	return items


def bottom(items: list[dict[str, Any]]) -> int:
	"""The first free row under everything on the layout."""
	return max((_int(item["layout"].get("y")) + _int(item["layout"].get("h")) for item in items), default=0)


def sanitize(raw: Any, allowed_config: dict[str, set[str]] | None = None) -> list[dict[str, Any]]:
	"""A layout safe to store, built from whatever the browser sent.

	Keeps only well-formed entries, pulls every widget back inside the grid, gives
	duplicate or missing keys fresh ones and drops anything that is not layout —
	chart data the browser was holding included. ``allowed_config`` maps a widget
	name to the config keys it accepts; widgets not in it keep only the common
	ones (``title``, ``period``).
	"""
	if not isinstance(raw, list):
		return []
	cleaned: list[dict[str, Any]] = []
	taken: set[str] = set()
	for entry in raw[:MAX_ITEMS]:
		if not isinstance(entry, dict):
			continue
		name = entry.get("name")
		if not isinstance(name, str) or not name.strip():
			continue
		name = name.strip()[:60]
		position = entry.get("layout") if isinstance(entry.get("layout"), dict) else {}
		width = _clamp(position.get("w"), 1, GRID_COLUMNS, 4)
		x = _clamp(position.get("x"), 0, GRID_COLUMNS - 1, 0)
		if x + width > GRID_COLUMNS:
			x = GRID_COLUMNS - width
		key = position.get("i")
		key = str(key)[:80] if isinstance(key, (str, int)) and str(key).strip() else ""
		if not key or key in taken:
			key = new_key(name, taken)
		else:
			taken.add(key)
		item: dict[str, Any] = {
			"name": name,
			"type": str(entry.get("type") or "")[:30],
			"layout": {
				"x": x,
				"y": _clamp(position.get("y"), 0, 10_000, 0),
				"w": width,
				"h": _clamp(position.get("h"), 1, MAX_HEIGHT, 3),
				"i": key,
			},
		}
		config = _config(entry.get("config"), (allowed_config or {}).get(name))
		if config:
			item["config"] = config
		cleaned.append(item)
	return cleaned


COMMON_CONFIG = {"title", "period"}


def _config(raw: Any, allowed: set[str] | None) -> dict[str, Any]:
	if not isinstance(raw, dict):
		return {}
	keys = COMMON_CONFIG | (allowed or set())
	config: dict[str, Any] = {}
	for key, value in list(raw.items())[: MAX_CONFIG_KEYS * 2]:
		if key not in keys or len(config) >= MAX_CONFIG_KEYS:
			continue
		if isinstance(value, bool) or value is None:
			config[key] = value
		elif isinstance(value, (int, float)):
			config[key] = value
		elif isinstance(value, str):
			value = value.strip()[:MAX_TEXT]
			if value:
				config[key] = value
	return config


def _int(value: Any, default: int = 0) -> int:
	try:
		return int(value)
	except (TypeError, ValueError):
		return default


def _clamp(value: Any, low: int, high: int, default: int) -> int:
	number = _int(value, default)
	return max(low, min(high, number))
