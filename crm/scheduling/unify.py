# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""One booking system: the Calendly-style calendars become services.

A ``CRM Booking Calendar`` was a person's-time page (duration, members, hours,
price) living beside the service catalogue with its own engine, pages and rules.
Every one of those notions exists on ``CRM Service``, so each calendar is turned
into a service bookable online with the same values, and its old address keeps
working by redirecting to the service's link on ``/prenota``.

Nothing is deleted: the calendar keeps its record (``migrated_service`` says
where it went), past ``CRM Booking`` rows stay as history and still occupy the
diary, and a booking made before the move is still managed on its old page.
"""

from __future__ import annotations

import json

import frappe
from frappe.utils import cint, flt

from crm.api.site_routes import route_conflict, slugify


def migrate_all() -> list[str]:
	"""Move every calendar not yet moved; returns the services created."""
	created = []
	for name in frappe.get_all(
		"CRM Booking Calendar", filters={"migrated_service": ["is", "not set"]}, pluck="name"
	):
		service = migrate_calendar(name)
		if service:
			created.append(service)
	if frappe.get_all("CRM Booking Calendar", filters={"check_google_busy": 1}, limit=1):
		# one calendar asked to respect Google busy time: the whole engine does now
		frappe.db.set_single_value("CRM Scheduling Settings", "check_google_busy", 1)
	return created


def migrate_calendar(name: str) -> str | None:
	cal = frappe.get_doc("CRM Booking Calendar", name)
	members = [row.user for row in cal.members if row.user]
	if not members:
		frappe.log_error(f"Booking calendar {name} has no members: not moved", "Unify booking")
		return None

	service_name = _free_name(cal.calendar_name)
	doc = frappe.get_doc(
		{
			"doctype": "CRM Service",
			"service_name": service_name,
			"enabled": cint(cal.enabled),
			"bookable_online": cint(cal.enabled),
			# a calendar that was not in the /book directory was reachable only by its link
			"hide_from_menu": 0 if cint(cal.show_in_menu) else 1,
			"description": cal.description,
			"short_description": cal.description,
			"location": cal.location,
			"duration": cint(cal.duration) or 30,
			"slot_interval": cint(cal.slot_interval),
			"buffer_before": cint(cal.buffer_before),
			"buffer_after": cint(cal.buffer_after),
			"min_notice_hours": cint(cal.min_notice_hours),
			"max_horizon_days": cint(cal.max_horizon_days) or 30,
			# the calendar's own notice and horizon were explicit choices: keep them its own
			"online_overrides": json.dumps(["max_horizon_days", "min_notice_hours"]),
			"default_price": flt(cal.price),
			"currency": cal.currency or "EUR",
			"staff_selection": "Any one",
			"staff_count": 1,
			"staff": [{"user": user, "bookable_online": 1} for user in members],
			"availability": [
				{"workday": row.workday, "start_time": row.start_time, "end_time": row.end_time}
				for row in cal.availability
			],
			"holiday_list": cal.holiday_list,
			"website_slug": _free_slug(cal.route),
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	cal.db_set("migrated_service", doc.name, update_modified=False)
	# a service published on the site with "Book" pointing at this calendar keeps working
	for service in frappe.get_all("CRM Service", filters={"booking_calendar": name}, pluck="name"):
		frappe.db.set_value("CRM Service", service, "bookable_online", 1, update_modified=False)
	return doc.name


def _free_name(base: str) -> str:
	name = (base or "Servizio").strip()
	if not frappe.db.exists("CRM Service", name):
		return name
	for n in range(2, 100):
		candidate = f"{name} ({n})"
		if not frappe.db.exists("CRM Service", candidate):
			return candidate
	return f"{name} ({frappe.generate_hash(length=5)})"


def _free_slug(route: str | None) -> str | None:
	slug = slugify(route or "")
	if not slug:
		return None
	if frappe.db.exists("CRM Service", {"website_slug": slug}) or route_conflict(slug):
		slug = f"{slug}-online"
		if frappe.db.exists("CRM Service", {"website_slug": slug}):
			return None
	return slug


def service_for_route(route: str) -> str | None:
	"""The service an old /book/<route> now lives as, if it was moved."""
	return frappe.db.get_value("CRM Booking Calendar", {"route": route}, "migrated_service")


def booking_url(service: str | None) -> str:
	"""The service's own address on the booking page."""
	if not service:
		return "/prenota"
	slug = frappe.db.get_value("CRM Service", service, "website_slug")
	from urllib.parse import quote

	return f"/prenota?servizio={quote(slug or service)}"
