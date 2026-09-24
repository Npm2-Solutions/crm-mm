# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The overview screens of the booking system.

* **Chi fa cosa** — services by professionals in one grid: who delivers what,
  with each professional's own length, price and online flag for a service.
  No management software we studied has it; everybody edits the relation from
  one side at a time, which is exactly how "nobody can be booked for X" happens.
* **Turni del team** — every professional's week, caps and time off together.
* **Prenotazione online** — the page open, the services online and who clients
  can book for each, on one screen, each with the reason when it is closed.
* **Perché non è disponibile?** — pick a service and an instant, get, for every
  professional, the first reason that keeps the slot closed and where to fix it.
"""

from __future__ import annotations

import datetime

import frappe
from frappe import _
from frappe.utils import cint, flt

from crm.scheduling import booking_rules as rules_mod
from crm.scheduling import intervals as iv
from crm.scheduling.availability import (
	ACTIVE_STATUSES,
	WEEKDAYS,
	SlotFinder,
	holiday_dates,
	resource_usage,
	resource_working_hours,
	service_working_hours,
	settings,
	staff_busy,
	staff_profile,
	staff_working_hours,
)
from crm.scheduling.timeutils import UTC, parse_date, parse_utc, scheduling_tz, to_system_naive
from crm.utils import count_field

MANAGER_ROLES = {"System Manager", "Sales Manager"}


def _check_manager():
	if not MANAGER_ROLES & set(frappe.get_roles()):
		frappe.throw(_("Only sales managers can change the booking setup"), frappe.PermissionError)


def _people(users) -> dict[str, dict]:
	users = [u for u in users if u]
	if not users:
		return {}
	return {
		row.name: {"user": row.name, "full_name": row.full_name or row.name, "image": row.user_image}
		for row in frappe.get_all(
			"User", filters={"name": ["in", users]}, fields=["name", "full_name", "user_image"]
		)
	}


def _team() -> list[str]:
	"""Everybody who delivers a service or has a working schedule."""
	users = set(frappe.get_all("CRM Service Staff", filters={"parenttype": "CRM Service"}, pluck="user"))
	users |= set(frappe.get_all("CRM Staff Schedule", pluck="user"))
	return sorted(u for u in users if u)


# --------------------------------------------------------------------------
# Chi fa cosa
# --------------------------------------------------------------------------


@frappe.whitelist()
def get_matrix() -> dict:
	"""Services (by category) by professionals, with every cell's own settings."""
	_check_manager()
	services = frappe.get_all(
		"CRM Service",
		fields=[
			"name",
			"service_name",
			"category",
			"color",
			"enabled",
			"bookable_online",
			"duration",
			"default_price",
			"currency",
			"staff_selection",
			"max_participants",
		],
		order_by="category asc, service_name asc",
	)
	# the services page is this grid: it also says what is coming up
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
	rows = frappe.get_all(
		"CRM Service Staff",
		filters={"parenttype": "CRM Service"},
		fields=["parent", "user", "role", "priority", "duration", "custom_price", "price", "bookable_online"],
	)
	cells: dict[str, dict] = {}
	for row in rows:
		cells.setdefault(row.parent, {})[row.user] = {
			"role": row.role or "",
			"priority": cint(row.priority),
			"duration": cint(row.duration),
			"custom_price": cint(row.custom_price),
			"price": flt(row.price),
			"bookable_online": 1 if row.bookable_online is None else cint(row.bookable_online),
		}
	team = _team()
	people = _people(team)
	profiles = {u: staff_profile(u) for u in team}
	for service in services:
		service["cells"] = cells.get(service.name, {})
		service["upcoming_count"] = upcoming.get(service.name, 0)
		online = [
			u
			for u, c in service["cells"].items()
			if c["bookable_online"] and profiles.get(u, {}).get("online", True)
		]
		service["warnings"] = _service_warnings(service, online)
	return {
		"services": services,
		"staff": [
			{**people.get(u, {"user": u, "full_name": u}), "online": profiles[u]["online"]} for u in team
		],
	}


def _service_warnings(service, online_staff) -> list[str]:
	count = len(service["cells"])
	warnings = []
	if cint(service.enabled) and not count:
		warnings.append(_("Nobody delivers it"))
	elif cint(service.enabled) and count == 1 and service.staff_selection == "Any one":
		warnings.append(_("Only one person delivers it"))
	if cint(service.bookable_online) and count and not online_staff:
		warnings.append(_("Online, but nobody takes it online"))
	return warnings


@frappe.whitelist(methods=["POST"])
def set_cell(service: str, user: str, enabled: int | str = 1, values: str | dict | None = None) -> dict:
	"""Switch one professional on/off for one service, or change their own settings."""
	_check_manager()
	doc = frappe.get_doc("CRM Service", service)
	values = frappe.parse_json(values) if isinstance(values, str) else (values or {})
	existing = next((row for row in doc.staff if row.user == user), None)
	if not cint(enabled):
		if existing:
			doc.remove(existing)
	else:
		row = existing or doc.append("staff", {"user": user, "bookable_online": 1})
		for key in ("role", "priority", "duration", "custom_price", "price", "bookable_online"):
			if key in values:
				row.set(key, values[key])
	doc.save()
	return get_matrix()


@frappe.whitelist(methods=["POST"])
def set_row(service: str, users: str | list, enabled: int | str = 1) -> dict:
	"""A whole row at once: these professionals deliver (or stop delivering) the service."""
	_check_manager()
	users = frappe.parse_json(users) if isinstance(users, str) else users
	doc = frappe.get_doc("CRM Service", service)
	present = {row.user for row in doc.staff}
	if cint(enabled):
		for user in users:
			if user not in present:
				doc.append("staff", {"user": user, "bookable_online": 1})
	else:
		for row in [row for row in doc.staff if row.user in set(users)]:
			doc.remove(row)
	doc.save()
	return get_matrix()


@frappe.whitelist(methods=["POST"])
def set_column(user: str, services: str | list, enabled: int | str = 1) -> dict:
	"""A whole column: this professional delivers (or stops delivering) these services."""
	_check_manager()
	services = frappe.parse_json(services) if isinstance(services, str) else services
	errors = []
	for service in services:
		doc = frappe.get_doc("CRM Service", service)
		existing = next((row for row in doc.staff if row.user == user), None)
		if cint(enabled) and not existing:
			doc.append("staff", {"user": user, "bookable_online": 1})
		elif not cint(enabled) and existing:
			doc.remove(existing)
		else:
			continue
		try:
			doc.save()
		except frappe.ValidationError as exc:
			# a service cannot lose its last professional: say which, keep the others
			frappe.clear_last_message()
			errors.append(f"{doc.service_name}: {frappe.utils.strip_html(str(exc))}")
	result = get_matrix()
	result["errors"] = errors
	return result


@frappe.whitelist(methods=["POST"])
def copy_column(source: str, target: str) -> dict:
	"""Give ``target`` the same services (and own settings) as ``source``."""
	_check_manager()
	for name in frappe.get_all(
		"CRM Service Staff", filters={"user": source, "parenttype": "CRM Service"}, pluck="parent"
	):
		doc = frappe.get_doc("CRM Service", name)
		if any(row.user == target for row in doc.staff):
			continue
		original = next(row for row in doc.staff if row.user == source)
		doc.append(
			"staff",
			{
				"user": target,
				"role": original.role,
				"priority": original.priority,
				"duration": original.get("duration"),
				"custom_price": original.get("custom_price"),
				"price": original.get("price"),
				"bookable_online": original.get("bookable_online", 1),
			},
		)
		doc.save()
	return get_matrix()


# --------------------------------------------------------------------------
# Turni del team
# --------------------------------------------------------------------------


@frappe.whitelist()
def get_team_rota(start: str | None = None) -> dict:
	"""Every professional's week (from ``start``'s Monday) with hours, time off and load."""
	_check_manager()
	tz = scheduling_tz()
	first = parse_date(start) if start else datetime.datetime.now(tz).date()
	first -= datetime.timedelta(days=first.weekday())
	days = [first + datetime.timedelta(days=i) for i in range(7)]
	team = _team()
	people = _people(team)
	week_start = datetime.datetime.combine(first, datetime.time.min, tzinfo=tz).astimezone(UTC)
	week_end = week_start + datetime.timedelta(days=7)

	booked = {}
	for row in frappe.get_all(
		"CRM Appointment Staff",
		filters={"parenttype": "CRM Appointment", "user": ["in", team or [""]]},
		fields=["user", "parent"],
		limit_page_length=0,
	):
		booked.setdefault(row.parent, []).append(row.user)
	minutes: dict[tuple[str, datetime.date], float] = {}
	if booked:
		for appt in frappe.get_all(
			"CRM Appointment",
			filters={
				"name": ["in", list(booked)],
				"status": ["in", ACTIVE_STATUSES],
				"starts_on": ["<", to_system_naive(week_end)],
				"ends_on": [">", to_system_naive(week_start)],
			},
			fields=["name", "starts_on", "ends_on"],
			limit_page_length=0,
		):
			from crm.scheduling.timeutils import from_system_naive

			start_utc, end_utc = from_system_naive(appt.starts_on), from_system_naive(appt.ends_on)
			day = start_utc.astimezone(tz).date()
			for user in booked[appt.name]:
				minutes[(user, day)] = (
					minutes.get((user, day), 0) + (end_utc - start_utc).total_seconds() / 60
				)

	rows = []
	for user in team:
		hours = staff_working_hours(user)
		profile = staff_profile(user)
		has_schedule = bool(frappe.db.exists("CRM Staff Schedule", {"user": user, "enabled": 1}))
		cells = []
		for day in days:
			windows = hours.for_day(day, tz)
			exception = next((e for e in hours.exceptions if parse_date(e.date) == day), None)
			open_minutes = sum((b - a).total_seconds() / 60 for a, b in windows)
			cells.append(
				{
					"date": day.isoformat(),
					"windows": [
						[a.astimezone(tz).strftime("%H:%M"), b.astimezone(tz).strftime("%H:%M")]
						for a, b in windows
					],
					"state": (
						"holiday"
						if day in hours.holidays and not exception
						else "off"
						if exception and cint(exception.unavailable)
						else "extra"
						if exception
						else "open"
						if windows
						else "closed"
					),
					"reason": (exception.reason if exception else "") or "",
					"open_minutes": open_minutes,
					"booked_minutes": minutes.get((user, day), 0),
				}
			)
		rows.append(
			{
				**people.get(user, {"user": user, "full_name": user}),
				"own_schedule": has_schedule,
				"daily_cap": profile["daily"],
				"weekly_cap": profile["weekly"],
				"online": profile["online"],
				"days": cells,
			}
		)
	return {"days": [d.isoformat() for d in days], "weekdays": list(WEEKDAYS), "team": rows}


# --------------------------------------------------------------------------
# Perché non è disponibile?
# --------------------------------------------------------------------------


def _reason(code: str, text: str, fix: str = "") -> dict:
	return {"code": code, "text": text, "fix": fix}


@frappe.whitelist()
def explain_slot(service: str, start: str, online: int | str = 1) -> dict:
	"""Why a service can (or cannot) be booked at ``start``, professional by professional."""
	_check_manager()
	from crm.api.service_booking import _online_staff, _rules, _service_booked, limit_message

	doc = frappe.get_cached_doc("CRM Service", service)
	online = bool(cint(online))
	tz = scheduling_tz()
	start_utc = parse_utc(start)
	now = datetime.datetime.now(UTC)
	day = start_utc.astimezone(tz).date()
	finder = SlotFinder(service, day, day, online=False)
	service_level: list[dict] = []

	if not cint(doc.enabled):
		service_level.append(_reason("SERVICE_OFF", _("The service is disabled"), "service"))
	if online and not cint(doc.bookable_online):
		service_level.append(_reason("NOT_ONLINE", _("The service is not bookable online"), "service"))
	if online:
		rules = _rules(doc)
		if code := rules.check_time(start_utc, now, tz):
			service_level.append(_reason(code.upper(), limit_message(code), "online_rules"))
		booked = _service_booked(
			doc.name, start_utc - datetime.timedelta(days=1), start_utc + datetime.timedelta(days=1)
		)
		end_guess = start_utc + finder.duration
		if code := rules.check_capacity(start_utc, end_guess, booked, tz):
			service_level.append(_reason(code.upper(), limit_message(code), "online_rules"))

	service_windows = service_working_hours(doc).for_span(day, 2, tz)
	online_staff = set(_online_staff(doc)) if online else None
	holidays_service = holiday_dates(doc.holiday_list)

	staff_reports = []
	for row in doc.staff:
		user = row.user
		end_utc = start_utc + finder.duration_for(user)
		reasons: list[dict] = []
		if online_staff is not None and user not in online_staff:
			if not (row.get("bookable_online") is None or cint(row.get("bookable_online"))):
				reasons.append(
					_reason(
						"STAFF_SERVICE_OFFLINE",
						_("Does this service only when booked by the practice"),
						"matrix",
					)
				)
			else:
				reasons.append(
					_reason("STAFF_OFFLINE", _("Not bookable online (working hours → booking page)"), "rota")
				)
		if service_windows and not iv.covers(service_windows, start_utc, end_utc):
			reasons.append(
				_reason("SERVICE_HOURS", _("Outside the hours this service can be delivered"), "service")
			)
		if day in holidays_service:
			reasons.append(
				_reason("SERVICE_HOLIDAY", _("The service's holiday list closes this day"), "service")
			)
		hours = staff_working_hours(user)
		if not iv.covers(hours.for_span(day, 2, tz), start_utc, end_utc):
			exception = next((e for e in hours.exceptions if parse_date(e.date) == day), None)
			if exception and cint(exception.unavailable):
				reasons.append(
					_reason("TIME_OFF", _("Day off: {0}").format(exception.reason or _("time off")), "rota")
				)
			elif day in hours.holidays:
				reasons.append(_reason("HOLIDAY", _("Holiday"), "rota"))
			else:
				reasons.append(_reason("OUTSIDE_HOURS", _("Outside working hours"), "rota"))
		busy = staff_busy(
			[user],
			start_utc,
			end_utc,
			finder.buffer_before,
			finder.buffer_after,
			include_google=bool(cint(settings().check_google_busy)),
		)[user]
		if iv.overlaps(busy, start_utc, end_utc):
			reasons.append(_reason("BUSY", _busy_text(user, start_utc, end_utc), "calendar"))
		profile = staff_profile(user)
		if profile["daily"] or profile["weekly"]:
			from crm.scheduling.availability import daily_counts, weekly_counts

			day_start = datetime.datetime.combine(day, datetime.time.min, tzinfo=tz).astimezone(UTC)
			if profile["daily"]:
				count = daily_counts([user], day_start, day_start + datetime.timedelta(days=1)).get(
					(user, day), 0
				)
				if count >= profile["daily"]:
					reasons.append(
						_reason("DAILY_CAP", _("Daily limit reached ({0})").format(profile["daily"]), "rota")
					)
			if profile["weekly"]:
				week_start = day_start - datetime.timedelta(days=day.weekday())
				week = start_utc.astimezone(tz).isocalendar()[:2]
				count = weekly_counts([user], week_start, week_start + datetime.timedelta(days=7)).get(
					(user, week), 0
				)
				if count >= profile["weekly"]:
					reasons.append(
						_reason(
							"WEEKLY_CAP", _("Weekly limit reached ({0})").format(profile["weekly"]), "rota"
						)
					)
		staff_reports.append(
			{
				"user": user,
				"full_name": frappe.db.get_value("User", user, "full_name") or user,
				"duration": int(finder.duration_for(user).total_seconds() // 60),
				"free": not reasons,
				"reasons": reasons,
			}
		)

	resource_reasons = _resource_reasons(finder, start_utc, start_utc + finder.duration, tz)
	offered = any(slot.start == start_utc for slot in _offered(doc, day, online))
	return {
		"service": doc.service_name,
		"start": start_utc.isoformat(),
		"offered": offered,
		"service_reasons": service_level,
		"resource_reasons": resource_reasons,
		"staff": staff_reports,
		"staffing": doc.staff_selection,
	}


def _offered(doc, day, online):
	if online:
		from crm.api.service_booking import online_slots

		return online_slots(doc, day, day)
	return SlotFinder(doc.name, day, day).run()


def _busy_text(user: str, start, end) -> str:
	"""Name what occupies the professional, not just that something does."""
	appointment = frappe.qb.DocType("CRM Appointment")
	child = frappe.qb.DocType("CRM Appointment Staff")
	rows = (
		frappe.qb.from_(child)
		.join(appointment)
		.on(child.parent == appointment.name)
		.select(appointment.name, appointment.title)
		.where(child.user == user)
		.where(appointment.status.isin(ACTIVE_STATUSES))
		.where(appointment.starts_on < to_system_naive(end + datetime.timedelta(hours=2)))
		.where(appointment.ends_on > to_system_naive(start - datetime.timedelta(hours=2)))
		.limit(3)
		.run(as_dict=True)
	)
	if rows:
		return _("Busy (or inside a buffer) with: {0}").format(", ".join(r.title or r.name for r in rows))
	return _("Busy: calendar event or Google Calendar")


def _resource_reasons(finder, start, end, tz) -> list[dict]:
	reasons = []
	for requirement in finder._resource_candidates():
		if not requirement["candidates"]:
			reasons.append(
				_reason(
					"NO_RESOURCE", _("No {0} exists or is enabled").format(requirement["label"]), "resources"
				)
			)
			continue
		free = []
		usage = resource_usage(requirement["candidates"], start, end)
		for name in requirement["candidates"]:
			resource = frappe.get_cached_doc("CRM Resource", name)
			day = start.astimezone(tz).date()
			if not iv.covers(resource_working_hours(resource).for_span(day, 2, tz), start, end):
				continue
			used = iv.peak_usage(usage.get(name, []), start, end)
			if used < max(cint(resource.capacity), 1):
				free.append(name)
		if len(free) < requirement["quantity"] and requirement["required"]:
			reasons.append(
				_reason(
					"RESOURCE_FULL",
					_("{0}: none free at this time").format(requirement["label"]),
					"resources",
				)
			)
	return reasons


# --------------------------------------------------------------------------
# Prenotazione online — who clients can book, on one screen
# --------------------------------------------------------------------------

TEAM_ROLES = ("Sales User", "Sales Manager", "System Manager")


def _bookable_people() -> list[str]:
	"""The team plus every CRM user, so someone new can be switched on here too."""
	users = set(_team())
	users |= set(
		frappe.get_all(
			"Has Role",
			filters={"role": ["in", TEAM_ROLES], "parenttype": "User"},
			pluck="parent",
		)
	)
	users -= {"Administrator", "Guest"}
	enabled = set(
		frappe.get_all(
			"User",
			filters={"name": ["in", list(users) or [""]], "enabled": 1, "user_type": "System User"},
			pluck="name",
		)
	)
	return sorted(enabled)


def _why_not_online(is_open: bool, online: bool, delivers: int, bookable: list) -> str:
	if not is_open:
		return _("Online booking is closed")
	if not online:
		return _("Switched off")
	if not delivers:
		return _("Pick the services clients can book them for")
	if not bookable:
		return _("None of their services is online")
	return ""


@frappe.whitelist()
def get_online_setup() -> dict:
	"""Everything that decides whether a client can book someone, together:
	the page open, which services are online, who takes each of them online."""
	_check_manager()
	is_open = bool(cint(settings().get("online_booking_enabled")))
	services = frappe.get_all(
		"CRM Service",
		filters={"enabled": 1},
		fields=["name", "service_name", "category", "color", "bookable_online"],
		order_by="category asc, service_name asc",
	)
	rows = frappe.get_all(
		"CRM Service Staff",
		filters={"parenttype": "CRM Service", "parent": ["in", [s.name for s in services] or [""]]},
		fields=["parent", "user", "bookable_online"],
	)
	cells: dict[str, dict[str, bool]] = {}
	for row in rows:
		cells.setdefault(row.user, {})[row.parent] = row.bookable_online is None or bool(
			cint(row.bookable_online)
		)
	online_services = {s.name for s in services if cint(s.bookable_online)}
	users = _bookable_people()
	people = _people(users)
	profiles = {
		row.user: row
		for row in frappe.get_all(
			"CRM Staff Schedule",
			filters={"user": ["in", users or [""]]},
			fields=["user", "public_title", "public_bio"],
		)
	}
	team = []
	for user in users:
		online = staff_profile(user)["online"]
		mine = cells.get(user, {})
		bookable = [name for name, flag in mine.items() if flag and name in online_services]
		team.append(
			{
				**people.get(user, {"user": user, "full_name": user}),
				"online": online,
				"public_title": (profiles.get(user) or {}).get("public_title") or "",
				"public_bio": (profiles.get(user) or {}).get("public_bio") or "",
				"services": {name: flag for name, flag in mine.items()},
				"bookable": bookable if online and is_open else [],
				"reason": _why_not_online(is_open, online, len(mine), bookable),
			}
		)
	for service in services:
		service["online_staff"] = sum(
			1 for p in team if p["online"] and p["services"].get(service.name) and service.bookable_online
		)
	# people who can be booked first, then those who could, then the rest
	team.sort(key=lambda p: (not p["bookable"], not p["services"], p["full_name"].lower()))
	return {"open": is_open, "link": "/prenota", "services": services, "team": team}


@frappe.whitelist(methods=["POST"])
def set_booking_open(enabled: int | str) -> dict:
	_check_manager()
	frappe.db.set_single_value("CRM Scheduling Settings", "online_booking_enabled", cint(enabled))
	if hasattr(frappe.local, "crm_scheduling_settings"):
		del frappe.local.crm_scheduling_settings
	return get_online_setup()


@frappe.whitelist(methods=["POST"])
def set_person_online(user: str, online: int | str) -> dict:
	"""Clients can (or cannot) book this professional at all."""
	_check_manager()
	name = frappe.db.get_value("CRM Staff Schedule", {"user": user})
	if name:
		frappe.db.set_value("CRM Staff Schedule", name, "bookable_online", cint(online))
	elif not cint(online):
		# no schedule yet: a switched-off one keeps the default hours and only
		# records the choice
		frappe.get_doc(
			{"doctype": "CRM Staff Schedule", "user": user, "enabled": 0, "bookable_online": 0}
		).insert()
	return get_online_setup()


@frappe.whitelist(methods=["POST"])
def set_person_profile(user: str, public_title: str | None = None, public_bio: str | None = None) -> dict:
	"""What the booking page says about a professional."""
	_check_manager()
	values = {
		"public_title": (public_title or "").strip() or None,
		"public_bio": (public_bio or "").strip() or None,
	}
	name = frappe.db.get_value("CRM Staff Schedule", {"user": user})
	if name:
		frappe.db.set_value("CRM Staff Schedule", name, values)
	else:
		# no schedule yet: a switched-off one keeps the studio hours
		frappe.get_doc({"doctype": "CRM Staff Schedule", "user": user, "enabled": 0, **values}).insert()
	return get_online_setup()


@frappe.whitelist(methods=["POST"])
def set_service_online(service: str, online: int | str) -> dict:
	_check_manager()
	doc = frappe.get_doc("CRM Service", service)
	doc.bookable_online = cint(online)
	doc.save()
	return get_online_setup()


@frappe.whitelist(methods=["POST"])
def set_person_service_online(user: str, service: str, online: int | str) -> dict:
	"""Clients can book this professional for this service. Switching it on adds
	them to the service when they do not deliver it yet; switching it off keeps
	them on it for bookings made by the practice."""
	_check_manager()
	doc = frappe.get_doc("CRM Service", service)
	row = next((r for r in doc.staff if r.user == user), None)
	if row:
		row.bookable_online = cint(online)
	elif cint(online):
		doc.append("staff", {"user": user, "bookable_online": 1})
	else:
		return get_online_setup()
	doc.save()
	return get_online_setup()


# --------------------------------------------------------------------------
# booking page defaults with what inherits them
# --------------------------------------------------------------------------


@frappe.whitelist()
def get_inheritance_summary() -> dict:
	"""For each inheritable rule: how many online services follow the default,
	and which ones set their own value — shown next to the default before saving."""
	_check_manager()
	summary = {key: {"inherit": 0, "own": []} for key in rules_mod.INHERITED}
	for name in frappe.get_all("CRM Service", filters={"bookable_online": 1}, pluck="name"):
		doc = frappe.get_cached_doc("CRM Service", name)
		own = rules_mod.overridden_keys(doc)
		for key in rules_mod.INHERITED:
			if key in own:
				summary[key]["own"].append(doc.service_name)
			else:
				summary[key]["inherit"] += 1
	return summary
