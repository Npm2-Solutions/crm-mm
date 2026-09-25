# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The widget catalogue: what exists, what it needs, and who may see it.

A widget is registered by decorating the function that answers it::

        @widget(
            "whatsapp_received",
            category="whatsapp",
            kind="number",
            title=_lt("WhatsApp received"),
            description=_lt("Messages people sent you on WhatsApp"),
            requires=("whatsapp",),
        )
        def whatsapp_received(ctx): ...

Titles are lazy (``_lt``): the module is imported once per worker and serves
every site and every language that passes through it, so a title translated at
import time would stay in whichever language came first.

``kind`` is how the browser draws the answer: ``number`` (a KPI card), ``axis``,
``donut`` and ``funnel`` (charts), ``list`` (records to act on), ``table``,
``heatmap``. ``live`` widgets describe the present — who is waiting right now —
and ignore the period. ``scope`` says whose work is counted: ``team`` follows
the dashboard's person filter, ``me`` is always the person looking, ``site`` is
the whole business (ad spend has no owner).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

KINDS = ("number", "axis", "donut", "funnel", "list", "table", "heatmap")
SCOPES = ("team", "me", "site")

# Order of the library's sections. The browser owns the icons and the labels.
CATEGORIES = (
	"sales",
	"invoicing",
	"people",
	"conversations",
	"whatsapp",
	"sms",
	"email",
	"calls",
	"agenda",
	"booking",
	"marketing",
	"meta",
	"automations",
	"social",
	"tasks",
	"team",
)


@dataclass(frozen=True)
class Option:
	"""A setting a person can change on one widget, shown in its configuration dialog."""

	key: str
	label: Any
	type: str = "select"  # select | int | pipeline
	choices: tuple[tuple[str, Any], ...] = ()
	default: Any = None
	min: int | None = None
	max: int | None = None

	def clean(self, value: Any) -> Any:
		"""The value to use: the stored one when it is valid, the default otherwise."""
		if value is None or value == "":
			return self.default
		if self.type == "int":
			try:
				number = int(value)
			except (TypeError, ValueError):
				return self.default
			if self.min is not None:
				number = max(self.min, number)
			if self.max is not None:
				number = min(self.max, number)
			return number
		if self.type == "select":
			return value if value in {choice for choice, _label in self.choices} else self.default
		return str(value)[:140]

	def describe(self) -> dict[str, Any]:
		return {
			"key": self.key,
			"label": str(self.label),
			"type": self.type,
			"choices": [{"value": value, "label": str(label)} for value, label in self.choices],
			"default": self.default,
			"min": self.min,
			"max": self.max,
		}


@dataclass(frozen=True)
class Widget:
	id: str
	fn: Callable[..., dict]
	category: str
	kind: str
	title: Any
	description: Any = ""
	size: tuple[int, int] = (4, 3)
	requires: tuple[str, ...] = ()
	managers_only: bool = False
	live: bool = False
	scope: str = "team"
	options: tuple[Option, ...] = ()
	# kept so layouts saved with it still load, but no longer offered in the library
	retired: bool = False
	keywords: tuple[str, ...] = field(default=())

	def option(self, key: str) -> Option | None:
		return next((option for option in self.options if option.key == key), None)

	def clean_config(self, config: dict | None) -> dict[str, Any]:
		"""Every option with a usable value, whatever the stored config holds."""
		config = config or {}
		return {option.key: option.clean(config.get(option.key)) for option in self.options}


_REGISTRY: dict[str, Widget] = {}
_loaded = False


def widget(id: str, **meta: Any) -> Callable[[Callable[..., dict]], Callable[..., dict]]:
	"""Register the decorated function as the widget ``id``."""
	if meta.get("kind") not in KINDS:
		raise ValueError(f"Dashboard widget {id}: unknown kind {meta.get('kind')!r}")
	if meta.get("category") not in CATEGORIES:
		raise ValueError(f"Dashboard widget {id}: unknown category {meta.get('category')!r}")
	if meta.get("scope", "team") not in SCOPES:
		raise ValueError(f"Dashboard widget {id}: unknown scope {meta.get('scope')!r}")

	def register(fn: Callable[..., dict]) -> Callable[..., dict]:
		if id in _REGISTRY and _REGISTRY[id].fn is not fn:
			raise ValueError(f"Dashboard widget {id} is registered twice")
		_REGISTRY[id] = Widget(id=id, fn=fn, **meta)
		return fn

	return register


def load() -> dict[str, Widget]:
	"""Every registered widget, importing the widget modules the first time."""
	global _loaded
	if not _loaded:
		import crm.dashboard.widgets  # registers every widget as a side effect

		_loaded = True
	return _REGISTRY


def get(id: str | None) -> Widget | None:
	if not id:
		return None
	return load().get(id)


def all_widgets() -> list[Widget]:
	return list(load().values())
