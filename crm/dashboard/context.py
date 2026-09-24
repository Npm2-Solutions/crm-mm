# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""What a widget is asked: which days, whose work, and with which settings.

Every widget function receives one ``Context``. It carries the period and the
one before it, the people whose records count, and the widget's own options,
plus the small helpers every query needs — so the rule "a sales user sees their
own numbers" is written once, here, instead of in eighty queries.

Whose work counts is decided by who is looking, never by the request alone:

- a sales user always sees their own records, whatever the filter says;
- a manager inside the sales hierarchy sees their part of the tree, and can
  narrow it to one person of that part;
- a system manager, or a sales manager outside the tree, sees everyone and can
  narrow it to anyone.

That is the rule the lists already follow (``crm.permissions.org_hierarchy``);
before this module, the dashboard showed a manager in the tree the whole company.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any

import frappe
from frappe.query_builder import Criterion
from frappe.utils import getdate, now_datetime, nowdate

from crm.dashboard import periods

MANAGER_ROLES = {"System Manager", "Sales Manager"}


def is_manager(user: str | None = None) -> bool:
	user = user or frappe.session.user
	return user == "Administrator" or bool(MANAGER_ROLES & set(frappe.get_roles(user)))


def team_of(user: str) -> list[str] | None:
	"""The people whose records ``user`` may count on the dashboard; ``None`` for everyone."""
	from crm.permissions.org_hierarchy import visible_owners

	return visible_owners(user)


def owners_for(requested: str | None, viewer: str) -> list[str] | None:
	"""Whose work to count: the requested person when the viewer may see them, else the viewer's team."""
	team = team_of(viewer)
	if requested and (team is None or requested in team):
		return [requested]
	return team


@dataclass
class Context:
	start: datetime.date
	end: datetime.date
	viewer: str
	owners: list[str] | None = None
	config: dict[str, Any] = field(default_factory=dict)
	today: datetime.date = field(default_factory=lambda: getdate(nowdate()))
	now: datetime.datetime = field(default_factory=now_datetime)

	@classmethod
	def build(
		cls,
		from_date: Any,
		to_date: Any,
		*,
		viewer: str | None = None,
		requested_user: str | None = None,
		scope: str = "team",
		config: dict | None = None,
	) -> Context:
		viewer = viewer or frappe.session.user
		today = getdate(nowdate())
		start, end = periods.normalize(from_date, to_date, today)
		if scope == "me":
			owners: list[str] | None = [viewer]
		elif scope == "site":
			owners = None
		else:
			owners = owners_for(requested_user, viewer)
		return cls(start=start, end=end, viewer=viewer, owners=owners, config=config or {}, today=today)

	# -- the period ---------------------------------------------------------

	@cached_property
	def previous(self) -> tuple[datetime.date, datetime.date]:
		return periods.previous(self.start, self.end)

	def dates(self, previous: bool = False) -> tuple[datetime.date, datetime.date]:
		return self.previous if previous else (self.start, self.end)

	def span(self, previous: bool = False) -> tuple[datetime.datetime, datetime.datetime]:
		"""The period as a half-open datetime range, [first midnight, midnight after the last day)."""
		return periods.bounds(*self.dates(previous))

	def within(self, column, previous: bool = False) -> Criterion:
		"""``column`` (a Datetime) falls inside the period."""
		low, high = self.span(previous)
		return (column >= low) & (column < high)

	def within_days(self, column, previous: bool = False) -> Criterion:
		"""``column`` (a Date) falls inside the period."""
		start, end = self.dates(previous)
		return (column >= start) & (column <= end)

	@cached_property
	def grain(self) -> str:
		return periods.grain(self.start, self.end)

	@cached_property
	def buckets(self) -> list[datetime.date]:
		return periods.buckets(self.start, self.end, self.grain)

	def bucket(self, value: Any) -> datetime.date | None:
		day = periods.to_date(value)
		return periods.bucket(day, self.grain) if day else None

	# -- whose work ---------------------------------------------------------

	def owned(self, column) -> Criterion | None:
		"""``column`` holds one of the people being counted; ``None`` when everyone counts."""
		if self.owners is None:
			return None
		return column.isin(self.owners or ["<nobody>"])

	@property
	def everyone(self) -> bool:
		return self.owners is None

	# -- the widget's settings -----------------------------------------------

	def option(self, key: str, default: Any = None) -> Any:
		value = self.config.get(key)
		return default if value is None or value == "" else value

	@cached_property
	def currency(self) -> str:
		"""The currency every amount on the dashboard is converted to."""
		return frappe.db.get_single_value("FCRM Settings", "currency") or "USD"


def where(query, *criteria):
	"""``query`` with every criterion that is not ``None`` added."""
	for criterion in criteria:
		if criterion is not None:
			query = query.where(criterion)
	return query
