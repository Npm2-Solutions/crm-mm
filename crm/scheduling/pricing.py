# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Variable price lists for services.

A price is not a property of a service — it is the answer to "what does *this*
service cost, on *this* price list, delivered by *this* professional, in *this*
room, at *this* hour, to *this many* people, on *this* date?".

``CRM Service Price`` rows carry that question's conditions. Every row whose
conditions all match is a candidate; the winner is decided by, in order:

1. explicit ``priority`` (highest wins — the manager's override lever),
2. **specificity**: a row that pins the professional, the room, the weekday, a
   time band or a participant threshold beats a blanket rate,
3. the most recently modified row, so the newest correction wins a genuine tie.

Nothing matched? Fall back to the service's own ``default_price``. There is
always an answer, and ``price_source`` says where it came from — the number on
an appointment is never unexplainable.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate

from crm.scheduling.timeutils import as_time, parse_utc, scheduling_tz

WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


@dataclass
class Price:
	rate: float
	currency: str
	per_participant: bool
	source: str
	rule: str | None = None

	def total(self, participants: int) -> float:
		return flt(self.rate) * max(cint(participants), 1) if self.per_participant else flt(self.rate)

	def as_dict(self, participants: int = 1) -> dict:
		return {
			"rate": flt(self.rate),
			"currency": self.currency,
			"per_participant": self.per_participant,
			"source": self.source,
			"rule": self.rule,
			"total": flt(self.total(participants)),
		}


def default_price_list() -> str | None:
	configured = frappe.db.get_single_value("CRM Scheduling Settings", "default_price_list")
	if configured and frappe.db.get_value("CRM Price List", configured, "enabled"):
		return configured
	return frappe.db.get_value("CRM Price List", {"enabled": 1, "is_default": 1})


def _price_list_is_valid(price_list: str, on: datetime.date) -> bool:
	row = frappe.db.get_value(
		"CRM Price List", price_list, ["enabled", "valid_from", "valid_upto"], as_dict=True
	)
	if not row or not cint(row.enabled):
		return False
	if row.valid_from and getdate(row.valid_from) > on:
		return False
	if row.valid_upto and getdate(row.valid_upto) < on:
		return False
	return True


def _matches(row, when: datetime.datetime, staff: list[str], resources: list[str], participants: int) -> bool:
	"""All conditions on a price row must hold. Empty condition = 'any'."""
	day = when.date()
	if row.valid_from and getdate(row.valid_from) > day:
		return False
	if row.valid_upto and getdate(row.valid_upto) < day:
		return False
	if row.staff and row.staff not in staff:
		return False
	if row.resource and row.resource not in resources:
		return False
	if row.weekday and row.weekday != WEEKDAYS[day.weekday()]:
		return False
	if row.start_time and when.time() < as_time(row.start_time):
		return False
	if row.end_time and when.time() >= as_time(row.end_time):
		return False
	if cint(row.min_participants) and participants < cint(row.min_participants):
		return False
	if cint(row.max_participants) and participants > cint(row.max_participants):
		return False
	return True


def _specificity(row) -> int:
	"""How many conditions the row pins down. More conditions = more specific."""
	return sum(
		1
		for value in (
			row.staff,
			row.resource,
			row.weekday,
			row.start_time,
			row.end_time,
			cint(row.min_participants) or None,
			cint(row.max_participants) or None,
			row.valid_from,
			row.valid_upto,
		)
		if value
	)


def resolve_price(
	service: str,
	when,
	price_list: str | None = None,
	staff: list[str] | None = None,
	resources: list[str] | None = None,
	participants: int = 1,
) -> Price:
	"""The rate that applies to one appointment. Never raises: always answers."""
	service_doc = frappe.get_cached_doc("CRM Service", service)
	fallback = Price(
		rate=flt(service_doc.default_price),
		currency=service_doc.currency or "EUR",
		per_participant=bool(cint(service_doc.price_per_participant)),
		source=_("Service default"),
	)

	price_list = price_list or default_price_list()
	if not price_list:
		return fallback

	local = parse_utc(when).astimezone(scheduling_tz())
	if not _price_list_is_valid(price_list, local.date()):
		return fallback

	rows = frappe.get_all(
		"CRM Service Price",
		filters={"service": service, "price_list": price_list, "enabled": 1},
		fields=[
			"name",
			"label",
			"price",
			"currency",
			"per_participant",
			"priority",
			"staff",
			"resource",
			"weekday",
			"start_time",
			"end_time",
			"min_participants",
			"max_participants",
			"valid_from",
			"valid_upto",
			"modified",
		],
	)
	matching = [row for row in rows if _matches(row, local, staff or [], resources or [], participants)]
	if not matching:
		list_currency = frappe.db.get_value("CRM Price List", price_list, "currency")
		return Price(
			rate=fallback.rate,
			currency=list_currency or fallback.currency,
			per_participant=fallback.per_participant,
			source=_("Service default"),
		)

	winner = max(matching, key=lambda row: (cint(row.priority), _specificity(row), row.modified))
	label = winner.label or price_list
	return Price(
		rate=flt(winner.price),
		currency=winner.currency
		or frappe.db.get_value("CRM Price List", price_list, "currency")
		or fallback.currency,
		per_participant=bool(cint(winner.per_participant)),
		source=f"{price_list} · {label}" if winner.label else price_list,
		rule=winner.name,
	)


def apply_to(doc) -> None:
	"""Stamp the resolved rate onto an appointment.

	The appointment keeps the *number*, not a pointer to the rule: a price list
	edited next month must not silently restate what a client was quoted today.
	Participants without their own amount inherit the resolved rate.
	"""
	if not doc.service or not doc.starts_on:
		return
	active = [row for row in doc.participants if row.status != "Cancelled"]
	price = resolve_price(
		doc.service,
		doc.starts_on,
		price_list=doc.price_list,
		staff=[row.user for row in doc.staff if row.user],
		resources=[row.resource for row in doc.resources if row.resource],
		participants=len(active) or 1,
	)
	doc.unit_price = price.rate
	doc.currency = price.currency
	doc.per_participant = 1 if price.per_participant else 0
	doc.price_source = price.source

	if price.per_participant:
		for row in active:
			if not flt(row.amount):
				row.amount = price.rate
		doc.total_amount = sum(flt(row.amount) for row in active)
	else:
		doc.total_amount = flt(price.rate)
		if len(active) == 1 and not flt(active[0].amount):
			active[0].amount = flt(price.rate)
