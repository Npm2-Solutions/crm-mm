# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Whitelisted endpoints for the scheduling calendar.

Everything the SPA calendar and its Settings pages need. The engine itself lives
in ``crm.scheduling``; this module only marshals arguments, checks permissions
and shapes JSON.
"""

from __future__ import annotations

import calendar
import datetime
import json

import frappe
from frappe import _
from frappe.utils import cint, flt, sbool

from crm.scheduling import pricing
from crm.scheduling.availability import (
	ACTIVE_STATUSES,
	find_conflicts,
	get_slots,
	settings,
	staff_working_hours,
)
from crm.scheduling.timeutils import (
	from_system_naive,
	parse_date,
	parse_utc,
	scheduling_tz,
	to_system_naive,
)
from crm.utils import count_field

MANAGER_ROLES = {"System Manager", "Sales Manager"}
MAX_RANGE_DAYS = 92


def _check_manager():
	if not MANAGER_ROLES & set(frappe.get_roles()):
		frappe.throw(_("Only sales managers can change the scheduling setup"), frappe.PermissionError)


def _loads(value):
	"""Query strings arrive as JSON text; POST bodies arrive already decoded."""
	if not isinstance(value, str):
		return value
	try:
		return json.loads(value)
	except ValueError:
		return value


def _as_list(value) -> list[str]:
	value = _loads(value)
	if not value:
		return []
	return [v for v in (value if isinstance(value, list) else [value]) if v]


# --------------------------------------------------------------------------
# calendar feed
# --------------------------------------------------------------------------


@frappe.whitelist()
def get_calendar(
	start: str,
	end: str,
	staff: str | list | None = None,
	resources: str | list | None = None,
	services: str | list | None = None,
	statuses: str | list | None = None,
	include_events: bool = True,
) -> dict:
	"""Appointments (and optionally plain calendar events) in a date window.

	One call feeds every view — month, week, day and the resource grid — because
	they only differ in how the same rows are laid out.
	"""
	window_start = parse_date(start)
	window_end = parse_date(end)
	if (window_end - window_start).days > MAX_RANGE_DAYS:
		frappe.throw(_("Date range too large"))

	from_dt = datetime.datetime.combine(window_start, datetime.time.min)
	to_dt = datetime.datetime.combine(window_end + datetime.timedelta(days=1), datetime.time.min)

	filters = {"starts_on": ["<", to_dt], "ends_on": [">", from_dt]}
	wanted_statuses = _as_list(statuses)
	if wanted_statuses:
		filters["status"] = ["in", wanted_statuses]
	wanted_services = _as_list(services)
	if wanted_services:
		filters["service"] = ["in", wanted_services]

	rows = frappe.get_all(
		"CRM Appointment",
		filters=filters,
		fields=[
			"name",
			"title",
			"service",
			"status",
			"starts_on",
			"ends_on",
			"color",
			"location",
			"total_amount",
			"currency",
			"price_source",
			"notes",
			"conflict_note",
			"series",
		],
		order_by="starts_on asc",
		limit_page_length=0,
	)
	appointments = _decorate(rows)

	wanted_staff = set(_as_list(staff))
	wanted_resources = set(_as_list(resources))
	if wanted_staff:
		appointments = [a for a in appointments if wanted_staff & {s["user"] for s in a["staff"]}]
	if wanted_resources:
		appointments = [a for a in appointments if wanted_resources & {r["resource"] for r in a["resources"]}]

	events = _plain_events(from_dt, to_dt) if sbool(include_events) else []
	return {"appointments": appointments, "events": events}


def _decorate(rows: list[dict]) -> list[dict]:
	"""Attach staff, participants and resources to the appointment rows."""
	if not rows:
		return []
	names = [row["name"] for row in rows]
	by_name = {row["name"]: row for row in rows}
	for row in rows:
		row["staff"] = []
		row["participants"] = []
		row["resources"] = []
		row["starts_on"] = str(row["starts_on"])
		row["ends_on"] = str(row["ends_on"])
		row["start_utc"] = from_system_naive(row["starts_on"]).isoformat()
		row["end_utc"] = from_system_naive(row["ends_on"]).isoformat()

	for child, key, fields in (
		("CRM Appointment Staff", "staff", ["user", "role", "status", "required"]),
		(
			"CRM Appointment Participant",
			"participants",
			["party_type", "party", "participant_name", "email", "phone", "status", "amount"],
		),
		("CRM Appointment Resource", "resources", ["resource", "resource_type", "quantity"]),
	):
		for entry in frappe.get_all(
			child,
			filters={"parent": ["in", names]},
			fields=["parent", "idx", *fields],
			order_by="idx asc",
			limit_page_length=0,
		):
			parent = entry.pop("parent")
			entry.pop("idx", None)
			by_name[parent][key].append(entry)
	return rows


def _plain_events(from_dt, to_dt) -> list[dict]:
	"""Framework events of the current user that are not appointment mirrors."""
	user = frappe.session.user
	rows = frappe.get_all(
		"Event",
		filters={"status": "Open", "starts_on": ["<", to_dt], "ends_on": [">", from_dt]},
		or_filters=[["owner", "=", user], ["Event Participants", "email", "=", user]],
		fields=["name", "subject", "starts_on", "ends_on", "all_day", "color", "reference_doctype"],
		limit_page_length=0,
	)
	seen = set()
	events = []
	for row in rows:
		if row.reference_doctype == "CRM Appointment" or row.name in seen:
			continue
		seen.add(row.name)
		events.append(
			{
				"name": row.name,
				"title": row.subject,
				"starts_on": str(row.starts_on),
				"ends_on": str(row.ends_on),
				"all_day": cint(row.all_day),
				"color": row.color,
			}
		)
	return events


@frappe.whitelist()
def get_appointment(name: str) -> dict:
	doc = frappe.get_doc("CRM Appointment", name)
	doc.check_permission("read")
	data = doc.as_dict()
	data["start_utc"] = from_system_naive(doc.starts_on).isoformat()
	data["end_utc"] = from_system_naive(doc.ends_on).isoformat()
	return data


# --------------------------------------------------------------------------
# meta for the pickers
# --------------------------------------------------------------------------


@frappe.whitelist()
def get_scheduler_meta() -> dict:
	"""Everything the calendar toolbar and the appointment editor need at once."""
	config = settings()
	services = frappe.get_all(
		"CRM Service",
		filters={"enabled": 1},
		fields=[
			"name",
			"service_name",
			"category",
			"color",
			"duration",
			"buffer_before",
			"buffer_after",
			"staff_selection",
			"staff_count",
			"min_participants",
			"max_participants",
			"default_price",
			"currency",
			"price_per_participant",
			"description",
		],
		order_by="service_name asc",
	)
	service_names = [s.name for s in services] or [""]
	staff_by_service: dict[str, list[dict]] = {}
	for row in frappe.get_all(
		"CRM Service Staff",
		filters={"parent": ["in", service_names]},
		fields=["parent", "user", "role", "priority"],
		order_by="idx asc",
	):
		staff_by_service.setdefault(row.parent, []).append(
			{"user": row.user, "role": row.role, "priority": row.priority}
		)
	resources_by_service: dict[str, list[dict]] = {}
	for row in frappe.get_all(
		"CRM Service Resource",
		filters={"parent": ["in", service_names]},
		fields=["parent", "resource", "resource_type", "quantity", "required"],
		order_by="idx asc",
	):
		resources_by_service.setdefault(row.parent, []).append(
			{
				"resource": row.resource,
				"resource_type": row.resource_type,
				"quantity": row.quantity,
				"required": row.required,
			}
		)
	for service in services:
		service["staff"] = staff_by_service.get(service.name, [])
		service["resources"] = resources_by_service.get(service.name, [])

	users = {u for service in services for u in [row["user"] for row in service["staff"]]}
	people = frappe.get_all(
		"User",
		filters={"name": ["in", list(users)]} if users else {"name": ["in", [""]]},
		fields=["name", "full_name", "user_image"],
		order_by="full_name asc",
	)

	return {
		"services": services,
		"resources": frappe.get_all(
			"CRM Resource",
			filters={"enabled": 1},
			fields=["name", "resource_name", "resource_type", "capacity", "seats", "color", "location"],
			order_by="resource_type asc, resource_name asc",
		),
		"staff": people,
		"price_lists": frappe.get_all(
			"CRM Price List",
			filters={"enabled": 1},
			fields=["name", "price_list_name", "currency", "is_default"],
			order_by="price_list_name asc",
		),
		"statuses": ["Scheduled", "Confirmed", "Completed", "Cancelled", "No Show"],
		"settings": {
			"timezone": config.timezone or str(scheduling_tz()),
			"default_price_list": pricing.default_price_list(),
			"default_duration": cint(config.default_duration) or 30,
			"allow_override": cint(config.allow_override),
			"can_override": bool(MANAGER_ROLES & set(frappe.get_roles())),
		},
	}


# --------------------------------------------------------------------------
# slots and price preview
# --------------------------------------------------------------------------


@frappe.whitelist()
def get_available_slots(
	service: str,
	start_date: str,
	end_date: str,
	staff: str | list | None = None,
	resources: str | list | None = None,
	participants: int = 1,
	exclude_appointment: str | None = None,
) -> list[dict]:
	"""Free slots for a service, as ISO-8601 UTC, with the assignment behind each."""
	first, last = parse_date(start_date), parse_date(end_date)
	if last < first:
		frappe.throw(_("End date must be on or after start date"))
	if (last - first).days > 31:
		frappe.throw(_("Date range too large"))
	slots = get_slots(
		service,
		first,
		last,
		staff=_as_list(staff),
		resources=_as_list(resources),
		participants=cint(participants) or 1,
		exclude_appointment=exclude_appointment,
	)
	return [slot.as_dict() for slot in slots]


@frappe.whitelist()
def quote_price(
	service: str,
	when: str,
	price_list: str | None = None,
	staff: str | list | None = None,
	resources: str | list | None = None,
	participants: int = 1,
) -> dict:
	"""Live price preview while the appointment is still being edited."""
	price = pricing.resolve_price(
		service,
		parse_utc(when),
		price_list=price_list,
		staff=_as_list(staff),
		resources=_as_list(resources),
		participants=cint(participants) or 1,
	)
	return price.as_dict(cint(participants) or 1)


@frappe.whitelist()
def check_conflicts(appointment: str | dict) -> list[str]:
	"""Dry-run the conflict rules against an unsaved appointment."""
	payload = _loads(appointment)
	doc = frappe.get_doc({"doctype": "CRM Appointment", **_normalize(payload)})
	if payload.get("name"):
		doc.name = payload["name"]
	return find_conflicts(doc)


# --------------------------------------------------------------------------
# writes
# --------------------------------------------------------------------------


def _normalize(payload: dict) -> dict:
	"""Accept both UTC ISO strings and naive site-time strings from the client."""
	data = dict(payload)
	data.pop("doctype", None)
	data.pop("name", None)
	for field in ("starts_on", "ends_on"):
		if data.get(field):
			data[field] = to_system_naive(parse_utc(data[field]))
	data["staff"] = [
		{"user": row["user"], "role": row.get("role"), "required": cint(row.get("required", 1))}
		for row in data.get("staff") or []
		if row.get("user")
	]
	data["participants"] = [
		{
			"party_type": row.get("party_type") or "CRM Lead",
			"party": row.get("party"),
			"participant_name": row.get("participant_name") or row.get("party"),
			"email": row.get("email"),
			"phone": row.get("phone"),
			"status": row.get("status") or "Booked",
			"amount": flt(row.get("amount")),
		}
		for row in data.get("participants") or []
		if row.get("participant_name") or row.get("party")
	]
	data["resources"] = [
		{"resource": row["resource"], "quantity": cint(row.get("quantity")) or 1}
		for row in data.get("resources") or []
		if row.get("resource")
	]
	return data


@frappe.whitelist(methods=["POST"])
def save_appointment(appointment: str | dict, name: str | None = None) -> dict:
	"""Create or update an appointment. Conflicts are enforced by the controller."""
	payload = _loads(appointment)
	values = _normalize(payload)
	if name:
		doc = frappe.get_doc("CRM Appointment", name)
		doc.check_permission("write")
		# child tables must be replaced wholesale, not merged
		for table in ("staff", "participants", "resources"):
			doc.set(table, [])
		doc.update(values)
		doc.save()
	else:
		doc = frappe.get_doc({"doctype": "CRM Appointment", **values})
		doc.insert()
	return get_appointment(doc.name)


@frappe.whitelist(methods=["POST"])
def move_appointment(name: str, starts_on: str, ends_on: str | None = None) -> dict:
	"""Drag & drop on the calendar: reschedule keeping everything else."""
	doc = frappe.get_doc("CRM Appointment", name)
	doc.check_permission("write")
	start = parse_utc(starts_on)
	length = from_system_naive(doc.ends_on) - from_system_naive(doc.starts_on)
	end = parse_utc(ends_on) if ends_on else start + length
	doc.starts_on = to_system_naive(start)
	doc.ends_on = to_system_naive(end)
	doc.save()
	return get_appointment(doc.name)


@frappe.whitelist(methods=["POST"])
def set_status(name: str, status: str, reason: str | None = None) -> dict:
	doc = frappe.get_doc("CRM Appointment", name)
	doc.check_permission("write")
	if status not in ("Scheduled", "Confirmed", "Completed", "Cancelled", "No Show"):
		frappe.throw(_("Unknown status {0}").format(status))
	doc.status = status
	if status == "Cancelled":
		doc.cancellation_reason = reason
		for row in doc.participants:
			row.status = "Cancelled"
	doc.save()
	return get_appointment(doc.name)


@frappe.whitelist(methods=["POST"])
def set_participant_status(name: str, participant: str, status: str) -> dict:
	"""Mark one client as attended / no-show inside a group session."""
	doc = frappe.get_doc("CRM Appointment", name)
	doc.check_permission("write")
	for row in doc.participants:
		if row.name == participant:
			row.status = status
			break
	else:
		frappe.throw(_("Participant not found"))
	doc.save()
	return get_appointment(doc.name)


@frappe.whitelist(methods=["POST"])
def join_appointment(name: str, participant: str | dict) -> dict:
	"""Add a client to an existing group session, respecting the seat limit."""
	doc = frappe.get_doc("CRM Appointment", name)
	doc.check_permission("write")
	row = _loads(participant)
	doc.append(
		"participants",
		{
			"party_type": row.get("party_type") or "CRM Lead",
			"party": row.get("party"),
			"participant_name": row.get("participant_name") or row.get("party"),
			"email": row.get("email"),
			"phone": row.get("phone"),
			"status": "Booked",
		},
	)
	doc.save()
	return get_appointment(doc.name)


@frappe.whitelist(methods=["POST"])
def delete_appointment(name: str) -> None:
	doc = frappe.get_doc("CRM Appointment", name)
	doc.check_permission("delete")
	doc.delete()


@frappe.whitelist(methods=["POST"])
def create_series(
	name: str, repeat: str, occurrences: int, until: str | None = None, skip_conflicts: bool = True
) -> dict:
	"""Repeat an appointment weekly/biweekly/monthly — a course, a therapy cycle.

	Each occurrence is a real appointment validated on its own, so a clash on one
	date never silently corrupts the rest of the series. Dates that cannot be
	booked are reported back instead of being forced.
	"""
	source = frappe.get_doc("CRM Appointment", name)
	source.check_permission("write")
	steps = {
		"Daily": datetime.timedelta(days=1),
		"Weekly": datetime.timedelta(days=7),
		"Biweekly": datetime.timedelta(days=14),
	}
	if repeat not in steps and repeat != "Monthly":
		frappe.throw(_("Unknown repeat rule {0}").format(repeat))

	series = source.series or frappe.generate_hash(length=10)
	if not source.series:
		source.db_set("series", series, update_modified=False)

	limit = min(cint(occurrences) or 1, 52)
	last_date = parse_date(until) if until else None
	created, skipped = [], []
	start = from_system_naive(source.starts_on)
	end = from_system_naive(source.ends_on)

	for index in range(1, limit + 1):
		if repeat == "Monthly":
			next_start = _add_months(start, index)
			next_end = next_start + (end - start)
		else:
			next_start = start + steps[repeat] * index
			next_end = end + steps[repeat] * index
		if last_date and next_start.astimezone(scheduling_tz()).date() > last_date:
			break
		clone = frappe.copy_doc(source)
		clone.starts_on = to_system_naive(next_start)
		clone.ends_on = to_system_naive(next_end)
		clone.series = series
		clone.status = "Scheduled"
		clone.event = None
		clone.booking = None
		try:
			clone.insert()
			created.append(clone.name)
		except frappe.ValidationError as exc:
			if not skip_conflicts:
				raise
			skipped.append(
				{"start": next_start.isoformat(), "reason": frappe.utils.strip_html(str(exc))[:200]}
			)
	return {"series": series, "created": created, "skipped": skipped}


def _add_months(value: datetime.datetime, months: int) -> datetime.datetime:
	"""Same day-of-month N months on, clamped to the end of a shorter month."""
	month_index = value.month - 1 + months
	year = value.year + month_index // 12
	month = month_index % 12 + 1
	day = min(value.day, calendar.monthrange(year, month)[1])
	return value.replace(year=year, month=month, day=day)


@frappe.whitelist(methods=["POST"])
def cancel_series(series: str, reason: str | None = None) -> int:
	"""Cancel every future appointment of a series."""
	names = frappe.get_all(
		"CRM Appointment",
		filters={
			"series": series,
			"status": ["in", ("Scheduled", "Confirmed")],
			"starts_on": [">=", frappe.utils.now_datetime()],
		},
		pluck="name",
	)
	for name in names:
		set_status(name, "Cancelled", reason)
	return len(names)


# --------------------------------------------------------------------------
# workload / utilisation
# --------------------------------------------------------------------------


@frappe.whitelist()
def get_workload(start: str, end: str) -> dict:
	"""Booked minutes per professional and per resource over a window.

	Feeds the utilisation strip at the top of the resource view: the point of
	tracking rooms and equipment is knowing what is actually being used.
	"""
	first, last = parse_date(start), parse_date(end)
	from_dt = datetime.datetime.combine(first, datetime.time.min)
	to_dt = datetime.datetime.combine(last + datetime.timedelta(days=1), datetime.time.min)
	rows = frappe.get_all(
		"CRM Appointment",
		filters={
			"status": ["in", ACTIVE_STATUSES],
			"starts_on": ["<", to_dt],
			"ends_on": [">", from_dt],
		},
		fields=["name", "starts_on", "ends_on"],
		limit_page_length=0,
	)
	minutes = {
		row.name: (from_system_naive(row.ends_on) - from_system_naive(row.starts_on)).total_seconds() / 60
		for row in rows
	}
	names = list(minutes) or [""]

	def totals(child, field):
		out: dict[str, float] = {}
		for row in frappe.get_all(
			child, filters={"parent": ["in", names]}, fields=["parent", field], limit_page_length=0
		):
			out[row[field]] = out.get(row[field], 0) + minutes.get(row.parent, 0)
		return out

	tz = scheduling_tz()
	capacity: dict[str, float] = {}
	for user in totals("CRM Appointment Staff", "user"):
		hours = staff_working_hours(user)
		total = 0.0
		day = first
		while day <= last:
			for window_start, window_end in hours.for_day(day, tz):
				total += (window_end - window_start).total_seconds() / 60
			day += datetime.timedelta(days=1)
		capacity[user] = total

	return {
		"staff": totals("CRM Appointment Staff", "user"),
		"resources": totals("CRM Appointment Resource", "resource"),
		"staff_capacity": capacity,
		"appointments": len(rows),
	}


# --------------------------------------------------------------------------
# admin: services, resources, price lists, schedules, settings
# --------------------------------------------------------------------------


@frappe.whitelist()
def list_services() -> list[dict]:
	_check_manager()
	rows = frappe.get_all(
		"CRM Service",
		fields=[
			"name",
			"service_name",
			"category",
			"enabled",
			"duration",
			"staff_selection",
			"max_participants",
			"default_price",
			"currency",
			"color",
			"bookable_online",
		],
		order_by="service_name asc",
	)
	upcoming = dict(
		frappe.get_all(
			"CRM Appointment",
			filters={
				"status": ["in", ("Scheduled", "Confirmed")],
				"starts_on": [">=", frappe.utils.now_datetime()],
			},
			fields=["service", count_field()],
			group_by="service",
			as_list=True,
		)
	)
	for row in rows:
		row["upcoming_count"] = upcoming.get(row.name, 0)
	return rows


@frappe.whitelist()
def get_service(name: str) -> dict:
	_check_manager()
	doc = frappe.get_doc("CRM Service", name)
	data = doc.as_dict()
	data["availability"] = [
		{"workday": row.workday, "start_time": str(row.start_time), "end_time": str(row.end_time)}
		for row in doc.availability
	]
	return data


@frappe.whitelist(methods=["POST"])
def save_service(service: str | dict, name: str | None = None) -> dict:
	_check_manager()
	payload = _loads(service)
	values = {
		key: payload.get(key)
		for key in (
			"service_name",
			"category",
			"color",
			"description",
			"duration",
			"slot_interval",
			"buffer_before",
			"buffer_after",
			"min_notice_hours",
			"max_horizon_days",
			"staff_selection",
			"staff_count",
			"min_participants",
			"max_participants",
			"default_price",
			"currency",
			"holiday_list",
		)
		if key in payload
	}
	values.update(
		{
			"enabled": cint(payload.get("enabled", 1)),
			"bookable_online": cint(payload.get("bookable_online")),
			"price_per_participant": cint(payload.get("price_per_participant")),
			"staff": [
				{"user": row.get("user"), "role": row.get("role"), "priority": cint(row.get("priority"))}
				for row in payload.get("staff") or []
				if row.get("user")
			],
			"roles": [
				{"role": row.get("role"), "staff_count": cint(row.get("staff_count")) or 1}
				for row in payload.get("roles") or []
				if row.get("role")
			],
			"resources": [
				{
					"resource_type": row.get("resource_type"),
					"resource": row.get("resource"),
					"quantity": cint(row.get("quantity")) or 1,
					"required": cint(row.get("required", 1)),
				}
				for row in payload.get("resources") or []
				if row.get("resource") or row.get("resource_type")
			],
			"availability": [
				{
					"workday": row.get("workday"),
					"start_time": row.get("start_time"),
					"end_time": row.get("end_time"),
				}
				for row in payload.get("availability") or []
				if row.get("workday")
			],
		}
	)
	if name:
		doc = frappe.get_doc("CRM Service", name)
		for table in ("staff", "roles", "resources", "availability"):
			doc.set(table, [])
		doc.update(values)
		doc.save()
	else:
		doc = frappe.get_doc({"doctype": "CRM Service", **values})
		doc.insert()
	return get_service(doc.name)


@frappe.whitelist(methods=["POST"])
def delete_service(name: str) -> None:
	_check_manager()
	frappe.delete_doc("CRM Service", name)


@frappe.whitelist()
def list_resources() -> list[dict]:
	_check_manager()
	return frappe.get_all(
		"CRM Resource",
		fields=[
			"name",
			"resource_name",
			"resource_type",
			"enabled",
			"capacity",
			"seats",
			"location",
			"color",
			"hourly_rate",
			"currency",
		],
		order_by="resource_type asc, resource_name asc",
	)


@frappe.whitelist()
def get_resource(name: str) -> dict:
	_check_manager()
	doc = frappe.get_doc("CRM Resource", name)
	data = doc.as_dict()
	data["availability"] = [
		{"workday": row.workday, "start_time": str(row.start_time), "end_time": str(row.end_time)}
		for row in doc.availability
	]
	return data


@frappe.whitelist(methods=["POST"])
def save_resource(resource: str | dict, name: str | None = None) -> dict:
	_check_manager()
	payload = _loads(resource)
	values = {
		"resource_name": (payload.get("resource_name") or "").strip(),
		"resource_type": payload.get("resource_type") or "Room",
		"enabled": cint(payload.get("enabled", 1)),
		"capacity": cint(payload.get("capacity")) or 1,
		"seats": cint(payload.get("seats")),
		"location": payload.get("location"),
		"color": payload.get("color"),
		"hourly_rate": flt(payload.get("hourly_rate")),
		"currency": payload.get("currency") or "EUR",
		"description": payload.get("description"),
		"holiday_list": payload.get("holiday_list"),
		"availability": [
			{
				"workday": row.get("workday"),
				"start_time": row.get("start_time"),
				"end_time": row.get("end_time"),
			}
			for row in payload.get("availability") or []
			if row.get("workday")
		],
	}
	if not values["resource_name"]:
		frappe.throw(_("Name is required"))
	if name:
		doc = frappe.get_doc("CRM Resource", name)
		doc.set("availability", [])
		doc.update(values)
		doc.save()
	else:
		doc = frappe.get_doc({"doctype": "CRM Resource", **values})
		doc.insert()
	return get_resource(doc.name)


@frappe.whitelist(methods=["POST"])
def delete_resource(name: str) -> None:
	_check_manager()
	frappe.delete_doc("CRM Resource", name)


@frappe.whitelist()
def list_price_lists() -> list[dict]:
	_check_manager()
	rows = frappe.get_all(
		"CRM Price List",
		fields=["name", "price_list_name", "enabled", "is_default", "currency", "valid_from", "valid_upto"],
		order_by="price_list_name asc",
	)
	counts = dict(
		frappe.get_all(
			"CRM Service Price",
			fields=["price_list", count_field()],
			group_by="price_list",
			as_list=True,
		)
	)
	for row in rows:
		row["rule_count"] = counts.get(row.name, 0)
	return rows


@frappe.whitelist(methods=["POST"])
def save_price_list(price_list: str | dict, name: str | None = None) -> dict:
	_check_manager()
	payload = _loads(price_list)
	values = {
		"price_list_name": (payload.get("price_list_name") or "").strip(),
		"enabled": cint(payload.get("enabled", 1)),
		"is_default": cint(payload.get("is_default")),
		"currency": payload.get("currency") or "EUR",
		"valid_from": payload.get("valid_from") or None,
		"valid_upto": payload.get("valid_upto") or None,
		"description": payload.get("description"),
	}
	if not values["price_list_name"]:
		frappe.throw(_("Name is required"))
	if name:
		doc = frappe.get_doc("CRM Price List", name)
		doc.update(values)
		doc.save()
	else:
		doc = frappe.get_doc({"doctype": "CRM Price List", **values})
		doc.insert()
	return doc.as_dict()


@frappe.whitelist(methods=["POST"])
def delete_price_list(name: str) -> None:
	_check_manager()
	frappe.delete_doc("CRM Price List", name)


@frappe.whitelist()
def list_prices(price_list: str, service: str | None = None) -> list[dict]:
	_check_manager()
	filters = {"price_list": price_list}
	if service:
		filters["service"] = service
	return frappe.get_all(
		"CRM Service Price",
		filters=filters,
		fields=[
			"name",
			"service",
			"label",
			"price",
			"currency",
			"per_participant",
			"priority",
			"enabled",
			"staff",
			"resource",
			"weekday",
			"start_time",
			"end_time",
			"min_participants",
			"max_participants",
			"valid_from",
			"valid_upto",
		],
		order_by="service asc, priority desc",
	)


@frappe.whitelist(methods=["POST"])
def save_price(price: str | dict, name: str | None = None) -> dict:
	_check_manager()
	payload = _loads(price)
	values = {
		"price_list": payload.get("price_list"),
		"service": payload.get("service"),
		"label": payload.get("label"),
		"price": flt(payload.get("price")),
		"currency": payload.get("currency") or None,
		"per_participant": cint(payload.get("per_participant")),
		"priority": cint(payload.get("priority")),
		"enabled": cint(payload.get("enabled", 1)),
		"staff": payload.get("staff") or None,
		"resource": payload.get("resource") or None,
		"weekday": payload.get("weekday") or None,
		"start_time": payload.get("start_time") or None,
		"end_time": payload.get("end_time") or None,
		"min_participants": cint(payload.get("min_participants")),
		"max_participants": cint(payload.get("max_participants")),
		"valid_from": payload.get("valid_from") or None,
		"valid_upto": payload.get("valid_upto") or None,
	}
	if name:
		doc = frappe.get_doc("CRM Service Price", name)
		doc.update(values)
		doc.save()
	else:
		doc = frappe.get_doc({"doctype": "CRM Service Price", **values})
		doc.insert()
	return doc.as_dict()


@frappe.whitelist(methods=["POST"])
def delete_price(name: str) -> None:
	_check_manager()
	frappe.delete_doc("CRM Service Price", name)


@frappe.whitelist()
def list_schedules() -> list[dict]:
	_check_manager()
	rows = frappe.get_all(
		"CRM Staff Schedule",
		fields=["name", "user", "enabled", "max_daily_appointments", "holiday_list"],
		order_by="user asc",
	)
	counts = dict(
		frappe.get_all(
			"CRM Service Day",
			filters={"parenttype": "CRM Staff Schedule"},
			fields=["parent", count_field()],
			group_by="parent",
			as_list=True,
		)
	)
	for row in rows:
		row["day_count"] = counts.get(row.name, 0)
		row["full_name"] = frappe.db.get_value("User", row.user, "full_name") or row.user
	return rows


@frappe.whitelist()
def get_schedule(user: str) -> dict:
	_check_manager()
	name = frappe.db.get_value("CRM Staff Schedule", {"user": user})
	if not name:
		return {
			"user": user,
			"enabled": 1,
			"max_daily_appointments": 0,
			"holiday_list": None,
			"availability": [],
			"exceptions": [],
		}
	doc = frappe.get_doc("CRM Staff Schedule", name)
	return {
		"name": doc.name,
		"user": doc.user,
		"enabled": doc.enabled,
		"max_daily_appointments": doc.max_daily_appointments,
		"holiday_list": doc.holiday_list,
		"availability": [
			{"workday": row.workday, "start_time": str(row.start_time), "end_time": str(row.end_time)}
			for row in doc.availability
		],
		"exceptions": [
			{
				"date": str(row.date),
				"unavailable": row.unavailable,
				"start_time": str(row.start_time) if row.start_time else None,
				"end_time": str(row.end_time) if row.end_time else None,
				"reason": row.reason,
			}
			for row in doc.exceptions
		],
	}


@frappe.whitelist(methods=["POST"])
def save_schedule(schedule: str | dict) -> dict:
	_check_manager()
	payload = _loads(schedule)
	user = payload.get("user")
	if not user:
		frappe.throw(_("Pick a professional"))
	values = {
		"user": user,
		"enabled": cint(payload.get("enabled", 1)),
		"max_daily_appointments": cint(payload.get("max_daily_appointments")),
		"holiday_list": payload.get("holiday_list") or None,
		"availability": [
			{
				"workday": row.get("workday"),
				"start_time": row.get("start_time"),
				"end_time": row.get("end_time"),
			}
			for row in payload.get("availability") or []
			if row.get("workday")
		],
		"exceptions": [
			{
				"date": row.get("date"),
				"unavailable": cint(row.get("unavailable")),
				"start_time": row.get("start_time") or None,
				"end_time": row.get("end_time") or None,
				"reason": row.get("reason"),
			}
			for row in payload.get("exceptions") or []
			if row.get("date")
		],
	}
	name = frappe.db.get_value("CRM Staff Schedule", {"user": user})
	if name:
		doc = frappe.get_doc("CRM Staff Schedule", name)
		for table in ("availability", "exceptions"):
			doc.set(table, [])
		doc.update(values)
		doc.save()
	else:
		doc = frappe.get_doc({"doctype": "CRM Staff Schedule", **values})
		doc.insert()
	return get_schedule(user)


@frappe.whitelist()
def get_scheduling_settings() -> dict:
	_check_manager()
	doc = frappe.get_doc("CRM Scheduling Settings")
	data = doc.as_dict()
	data["default_availability"] = [
		{"workday": row.workday, "start_time": str(row.start_time), "end_time": str(row.end_time)}
		for row in doc.default_availability
	]
	return data


@frappe.whitelist(methods=["POST"])
def save_scheduling_settings(scheduling_settings: str | dict) -> dict:
	_check_manager()
	payload = _loads(scheduling_settings)
	doc = frappe.get_doc("CRM Scheduling Settings")
	for key in (
		"timezone",
		"default_price_list",
		"default_duration",
		"cancellation_notice_hours",
		"enforce_staff_conflicts",
		"enforce_resource_conflicts",
		"enforce_participant_conflicts",
		"enforce_working_hours",
		"allow_override",
		"sync_to_event",
		"check_google_busy",
		"default_holiday_list",
	):
		if key in payload:
			doc.set(key, payload[key])
	if "default_availability" in payload:
		doc.set("default_availability", [])
		for row in payload["default_availability"] or []:
			if row.get("workday"):
				doc.append("default_availability", row)
	doc.save()
	# the engine caches the singleton per request; drop it so the next read is fresh
	if hasattr(frappe.local, "crm_scheduling_settings"):
		del frappe.local.crm_scheduling_settings
	return get_scheduling_settings()
