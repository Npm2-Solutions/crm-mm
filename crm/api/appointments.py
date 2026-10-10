# Copyright (c) 2026, NPM2 Solutions Srl and contributors
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
from frappe.query_builder.functions import Min
from frappe.utils import cint, flt, sbool

from crm.permissions.livelli import CENTRO, ambito, puo, verifica
from crm.scheduling import abbonamenti, cicli, pricing, sedi, visite_online, visite_online_regole
from crm.scheduling import intervals as iv
from crm.scheduling.availability import (
	ACTIVE_STATUSES,
	find_conflicts,
	get_slots,
	resource_working_hours,
	settings,
	staff_working_hours,
)
from crm.scheduling.timeutils import (
	from_system_naive,
	hhmm,
	parse_date,
	parse_utc,
	scheduling_tz,
	to_system_naive,
)
from crm.utils import count_field

MAX_RANGE_DAYS = 92


def _check(capacita: str) -> None:
	"""Services, prices and the studio's rules are the Manager's; rota, rooms and
	equipment the front desk's too (doc 30)."""
	verifica(
		capacita,
		messaggio=_("Only sales managers can change the scheduling setup"),
		ambito_minimo=CENTRO,
	)


def turni(user: str | None = None) -> str | None:
	"""Whose shifts the session reads and changes: the whole team's for the front
	desk and the manager (None), only their own for a practitioner - the scope the
	capability gives them (doc 30), as their schedule's own permission does
	(`documenti.DI_CHI`). Their one entry of the settings opened on a refusal."""
	verifica("agenda.turni", messaggio=_("Only sales managers can change the scheduling setup"))
	if ambito("agenda.turni") == CENTRO:
		return None
	if user and user != frappe.session.user:
		frappe.throw(_("You can change only your own shifts"), frappe.PermissionError)
	return frappe.session.user


def _check_reader():
	"""The editor's helpers answer questions about everyone's day: who is busy
	when, which room is taken, whether a person already has an appointment. The
	calendar says the same to whoever may read it, and only to them; the public
	booking page has endpoints of its own."""
	frappe.has_permission("CRM Appointment", "read", throw=True)


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
	sources: str | list | None = None,
	with_hours: bool = False,
	location: str | None = None,
) -> dict:
	"""Appointments (and optionally plain calendar events) in a date window.

	One call feeds every view — month, week, day and the resource grid — because
	they only differ in how the same rows are laid out. With `with_hours`, for a
	day or a week, when each professional and each room works on those days and
	the professionals' own engagements: the grid greys out the rest. With
	`location`, where the centre has more than one (docs/crm/62), that location's
	appointments and the ones that name none.
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
	# "Internal", "Online", or a connected platform's name (e.g. "Treatwell / Uala")
	wanted_sources = _as_list(sources)
	if wanted_sources:
		kinds = [s for s in wanted_sources if s in ("Internal", "Online", "External")]
		platforms = [s for s in wanted_sources if s not in kinds]
		or_filters = []
		if kinds:
			or_filters.append(["source", "in", kinds])
		if platforms:
			or_filters.append(["external_platform", "in", platforms])
		if len(or_filters) == 1:
			filters[or_filters[0][0]] = or_filters[0][1:]
		else:
			filters["name"] = [
				"in",
				frappe.get_list("CRM Appointment", or_filters=or_filters, pluck="name", limit_page_length=0)
				or [""],
			]

	sede = sedi.valida(location)
	rows = frappe.get_list(
		"CRM Appointment",
		filters=filters,
		or_filters=[["centre_location", "=", sede], ["centre_location", "is", "not set"]] if sede else None,
		fields=[
			"name",
			"title",
			"service",
			"status",
			"starts_on",
			"ends_on",
			"color",
			"location",
			"centre_location",
			"total_amount",
			"currency",
			"price_source",
			"notes",
			"conflict_note",
			"series",
			"source",
			"external_platform",
			"external_url",
			"customer_notes",
			# an online visit's room: whoever reads the appointment starts it
			"video_link",
		],
		order_by="starts_on asc",
		limit_page_length=0,
	)
	appointments = _decorate(rows)
	_first_visits(appointments)
	# each person's reminder: sent, answered (docs/crm/59)
	from crm.scheduling.promemoria import nelle_righe

	nelle_righe(appointments)

	wanted_staff = set(_as_list(staff))
	wanted_resources = set(_as_list(resources))
	if wanted_staff:
		appointments = [a for a in appointments if wanted_staff & {s["user"] for s in a["staff"]}]
	if wanted_resources:
		appointments = [a for a in appointments if wanted_resources & {r["resource"] for r in a["resources"]}]

	events = _plain_events(from_dt, to_dt) if sbool(include_events) else []
	from crm.permissions.seguono import shows_busy_time

	busy = (
		_busy_time(from_dt, to_dt, {row["name"] for row in rows}, wanted_staff, wanted_resources, sede)
		if shows_busy_time()
		else []
	)
	feed = {"appointments": appointments, "events": events, "busy": busy}
	# the grid's days: a day or a week, never a month's worth of shifts
	if sbool(with_hours) and (window_end - window_start).days < 7:
		feed.update(_giornate(window_start, window_end, appointments, busy, from_dt, to_dt))
	return feed


def _giornate(first, last, appointments, busy, from_dt, to_dt) -> dict:
	"""When each professional and each room works on the days the grid draws -
	their shifts, date overrides and holidays, as the engine books on them - and
	the professionals' own events as busy time."""
	days = [first + datetime.timedelta(days=offset) for offset in range((last - first).days + 1)]
	shown = appointments + busy
	users = sorted(_professionisti() | {row["user"] for a in shown for row in a["staff"]})
	rooms = set(frappe.get_all("CRM Resource", filters={"enabled": 1}, pluck="name")) | {
		row["resource"] for a in shown for row in a["resources"]
	}
	tz = scheduling_tz()
	return {
		"hours": {
			"staff": {
				user: orari_di(staff_working_hours(user), days, tz, con_le_sedi=sedi.piu_sedi())
				for user in users
			},
			"resources": {
				room: orari_di(resource_working_hours(frappe.get_cached_doc("CRM Resource", room)), days, tz)
				for room in sorted(rooms)
				# a room an old appointment names, gone since
				if frappe.db.exists("CRM Resource", room)
			},
		},
		"engaged": _impegni(from_dt, to_dt, users),
	}


def _professionisti() -> set[str]:
	"""Whoever works a service the centre offers: the agenda's columns."""
	services = frappe.get_all("CRM Service", filters={"enabled": 1}, pluck="name")
	if not services:
		return set()
	return set(
		frappe.get_all(
			"CRM Service Staff",
			filters={"parent": ["in", services], "parenttype": "CRM Service"},
			pluck="user",
		)
	)


def orari_di(hours, days: list[datetime.date], tz, con_le_sedi: bool = False) -> dict | None:
	"""A professional's or a room's open hours on each day, in minutes of the
	centre's clock - {"2026-10-06": {"open": [[480, 780], [840, 1140]], "note": ""}},
	the note a date override's reason («Ferie»). None where no hours were ever set:
	open whenever, and the agenda greys nothing out. `con_le_sedi`: the locations
	the day's lines name too (`sedi`, '' for a line good anywhere: docs/crm/62)."""
	if hours.always and not hours.rows and not hours.exceptions and not hours.holidays:
		return None
	out = {}
	for day in days:
		midnight = datetime.datetime.combine(day, datetime.time.min)

		def minute(moment, midnight=midnight):
			seconds = (to_system_naive(moment) - midnight).total_seconds()
			return max(0, min(24 * 60, round(seconds / 60)))

		# the shifts are kept on the scheduling clock and the grid draws the
		# centre's: the day's hours may come from the days either side of it
		windows = iv.clamp(
			hours.for_span(day - datetime.timedelta(days=1), 3, tz),
			from_system_naive(midnight),
			from_system_naive(midnight + datetime.timedelta(days=1)),
		)
		note = next(
			(
				row.reason
				for row in hours.exceptions
				if parse_date(row.date) == day and cint(row.unavailable) and row.reason
			),
			"",
		)
		out[day.isoformat()] = {
			"open": [[minute(start), minute(end)] for start, end in windows if minute(start) < minute(end)],
			"note": note,
		}
		if con_le_sedi:
			out[day.isoformat()]["sedi"] = hours.sedi_del_giorno(day, tz)
	return out


def _impegni(from_dt, to_dt, users: list[str]) -> list[dict]:
	"""The professionals' own events (a meeting, a training day) as busy time in
	their columns: when, never what - as the engine counts them when it books.
	An appointment's mirror is left out: it is drawn as itself."""
	if not users:
		return []
	rows = [
		row
		for row in frappe.get_all(
			"Event",
			filters={"status": "Open", "starts_on": ["<", to_dt], "ends_on": [">", from_dt]},
			fields=["name", "owner", "starts_on", "ends_on", "all_day", "reference_doctype"],
			limit_page_length=0,
		)
		if row.reference_doctype != "CRM Appointment"
	]
	if not rows:
		return []
	wanted = set(users)
	whose = {row.name: {row.owner} & wanted for row in rows}
	for entry in frappe.get_all(
		"Event Participants",
		filters={"parent": ["in", list(whose)], "parenttype": "Event", "email": ["in", users]},
		fields=["parent", "email"],
		limit_page_length=0,
	):
		whose[entry.parent].add(entry.email)
	return [
		{
			"name": row.name,
			"users": sorted(whose[row.name]),
			"starts_on": str(row.starts_on),
			"ends_on": str(row.ends_on),
			"all_day": cint(row.all_day),
		}
		for row in rows
		if whose[row.name]
	]


def _busy_time(
	from_dt, to_dt, seen: set[str], wanted_staff: set, wanted_resources: set, sede: str | None = None
) -> list[dict]:
	"""The rest of the agenda as busy time: when, who works it, which room - never who
	comes or why. For whoever sees only part of the agenda in full: sales book for
	their people into everybody's day."""
	rows = [
		row
		for row in frappe.get_all(
			"CRM Appointment",
			filters={"starts_on": ["<", to_dt], "ends_on": [">", from_dt], "status": ["!=", "Cancelled"]},
			fields=["name", "starts_on", "ends_on", "centre_location"],
			limit_page_length=0,
		)
		if row.name not in seen and (not sede or row.centre_location in (sede, None, ""))
	]
	if not rows:
		return []
	names = [row.name for row in rows]
	staff: dict[str, list[str]] = {}
	for entry in frappe.get_all(
		"CRM Appointment Staff",
		filters={"parent": ["in", names], "parenttype": "CRM Appointment"},
		fields=["parent", "user"],
		limit_page_length=0,
	):
		staff.setdefault(entry.parent, []).append(entry.user)
	resources: dict[str, list[str]] = {}
	for entry in frappe.get_all(
		"CRM Appointment Resource",
		filters={"parent": ["in", names], "parenttype": "CRM Appointment"},
		fields=["parent", "resource"],
		limit_page_length=0,
	):
		resources.setdefault(entry.parent, []).append(entry.resource)
	busy = []
	for row in rows:
		who = staff.get(row.name, [])
		where = resources.get(row.name, [])
		if wanted_staff and not wanted_staff & set(who):
			continue
		if wanted_resources and not wanted_resources & set(where):
			continue
		busy.append(
			{
				"starts_on": str(row.starts_on),
				"ends_on": str(row.ends_on),
				"start_utc": from_system_naive(str(row.starts_on)).isoformat(),
				"end_utc": from_system_naive(str(row.ends_on)).isoformat(),
				"staff": [{"user": user} for user in who],
				"resources": [{"resource": resource} for resource in where],
			}
		)
	return busy


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
			["party_type", "party", "participant_name", "booked_by", "email", "phone", "status", "amount"],
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
			if entry.get("booked_by"):
				# a child booked by their mother: the panel says so, and why the contact is hers
				entry["booked_by_name"] = frappe.db.get_value("CRM Lead", entry["booked_by"], "lead_name")
			by_name[parent][key].append(entry)
	return rows


def _first_visits(appointments: list[dict]) -> None:
	"""Mark `first_visit` on the appointments that are a person's first: their
	earliest appointment not cancelled, unless the centre counted them a client
	before it (history from before the agenda). The agenda draws them as the
	brand's full block, the design system's AgendaEvent."""
	leads = {
		participant["party"]
		for appointment in appointments
		for participant in appointment["participants"]
		if participant.get("party_type") == "CRM Lead" and participant.get("party")
	}
	for appointment in appointments:
		appointment["first_visit"] = False
	if not leads:
		return
	appointment_ = frappe.qb.DocType("CRM Appointment")
	participant_ = frappe.qb.DocType("CRM Appointment Participant")
	first = {
		row.party: row.first
		for row in (
			frappe.qb.from_(participant_)
			.join(appointment_)
			.on(appointment_.name == participant_.parent)
			.select(participant_.party, Min(appointment_.starts_on).as_("first"))
			.where(
				(participant_.parenttype == "CRM Appointment")
				& (participant_.party_type == "CRM Lead")
				& participant_.party.isin(list(leads))
				& (appointment_.status != "Cancelled")
			)
			.groupby(participant_.party)
		).run(as_dict=True)
	}
	clients_since = dict(
		frappe.get_all(
			"CRM Lead",
			filters={"name": ["in", list(leads)], "client_since": ["is", "set"]},
			fields=["name", "client_since"],
			as_list=True,
		)
	)
	for appointment in appointments:
		appointment["first_visit"] = is_first_visit(appointment, first, clients_since)


def is_first_visit(appointment: dict, first: dict, clients_since: dict) -> bool:
	"""A person's first visit: not cancelled, the earliest of one of its people,
	who was not a client before its day."""
	if appointment.get("status") == "Cancelled":
		return False
	day = str(appointment["starts_on"])[:10]
	for participant in appointment.get("participants") or []:
		party = participant.get("party")
		if participant.get("party_type") != "CRM Lead" or not party or party not in first:
			continue
		if str(first[party]) != str(appointment["starts_on"]):
			continue
		since = clients_since.get(party)
		if since and str(since)[:10] < day:
			continue
		return True
	return False


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
	# each person's reminder, read on the rows as they are stored (docs/crm/59)
	from crm.scheduling.promemoria import nelle_righe

	nelle_righe([data])
	# the editor searches people only: show older contact/deal rows as their person
	from crm.fcrm.doctype.crm_appointment.crm_appointment import person_of

	for row in data.get("participants") or []:
		person = person_of(row.get("party_type"), row.get("party"))
		if person:
			row["party_type"], row["party"] = "CRM Lead", person
	# each person's deposit paid online, kept or given back, on their row (doc 60)
	from crm.pagamenti import pagamenti

	pagamenti.del_appuntamento(doc, data.get("participants") or [])
	data["start_utc"] = from_system_naive(doc.starts_on).isoformat()
	data["end_utc"] = from_system_naive(doc.ends_on).isoformat()
	# where the price came from, in the reader's language: it is stored in the
	# language of whoever saved the appointment
	data["price_source"] = pricing.in_parole(doc.price_source)
	# which session of its cycle it is, and the cycles it could join; the same for
	# the subscriptions an entry is used of
	data["cycle"] = cicli.della_seduta(doc)
	data["subscription"] = abbonamenti.del_appuntamento(doc)
	# under a convention: which, the two shares, the authorisation (doc 61)
	from crm.convenzioni import convenzioni

	data["convention_info"] = convenzioni.del_appuntamento(doc)
	# what the panel offers: who reads the agenda without booking (the medical
	# director, the read-only level) sees the appointment, not the controls the
	# server would refuse
	data["can_write"] = bool(doc.has_permission("write"))
	data["can_delete"] = bool(doc.has_permission("delete"))
	# held by video: the panel starts it, or says it has no link yet
	data["online_visit"] = visite_online.del_servizio(doc.service)
	return data


@frappe.whitelist()
def get_person_appointments(doctype: str, name: str) -> list[dict]:
	"""The appointments of the person a record is about, newest first.

	A person's page showed their events and not their appointments, so what a
	client had booked could only be found on the calendar. A deal answers for
	the person behind it: that is who the appointments were made for.
	"""
	if doctype not in ("CRM Lead", "CRM Deal"):
		return []
	frappe.has_permission(doctype, "read", name, throw=True)
	person = name if doctype == "CRM Lead" else frappe.db.get_value("CRM Deal", name, "lead")
	if not person:
		return []
	posti = posti_della_persona("CRM Lead", person)
	if not posti:
		return []
	rows = frappe.get_list(
		"CRM Appointment",
		filters={"name": ["in", list(posti)]},
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
			"source",
			"external_platform",
		],
		order_by="starts_on desc",
		limit_page_length=100,
	)
	sedute = cicli.numero_della_seduta([row.name for row in rows])
	for row in rows:
		row["starts_on"] = str(row["starts_on"])
		row["ends_on"] = str(row["ends_on"])
		row["cycle"] = sedute.get(row.name)
		row["status"] = per_la_persona(row["status"], posti.get(row.name))
	return rows


#: How somebody's own place reads on their page, whatever the appointment says: in a
#: class one gives up one's place or does not come while the others have the lesson,
#: or came while the class is still open at the desk.
DEL_POSTO = {"Cancelled": "Cancelled", "No Show": "No Show", "Attended": "Completed"}
#: A place that is no appointment of theirs any more.
POSTO_LASCIATO = ("Cancelled", "No Show")


def posti_della_persona(party_type: str, party: str) -> dict[str, str | None]:
	"""The appointments somebody has a place in, each with how their place is."""
	return {
		riga.parent: riga.status
		for riga in frappe.get_all(
			"CRM Appointment Participant",
			filters={"parenttype": "CRM Appointment", "party_type": party_type, "party": party},
			fields=["parent", "status"],
			limit_page_length=0,
		)
	}


def per_la_persona(stato: str | None, posto: str | None) -> str | None:
	"""An appointment as it is for one of its people: how their own place went says
	it, whatever the class does. Their page said they were coming to a class they had
	cancelled, and that they had done one they never came to - the area already said
	it as it was."""
	return DEL_POSTO.get(posto or "") or stato


# --------------------------------------------------------------------------
# meta for the pickers
# --------------------------------------------------------------------------


@frappe.whitelist()
def get_scheduler_meta() -> dict:
	"""Everything the calendar toolbar and the appointment editor need at once."""
	config = settings()
	services = frappe.get_list(
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
			"online_visit",
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
	# names and pictures of the staff, and which platforms are connected: a Sales
	# User reads neither User nor CRM Booking Connection, and the calendar needs both
	people = frappe.get_all(
		"User",
		filters={"name": ["in", list(users)]} if users else {"name": ["in", [""]]},
		fields=["name", "full_name", "user_image"],
		order_by="full_name asc",
	)

	# where each works, where the centre has more than one location (docs/crm/62)
	if sedi.piu_sedi():
		for persona in people:
			persona["sedi"] = sorted(
				{
					riga.centre_location or ""
					for riga in staff_working_hours(persona.name).rows
					if riga.get("workday")
				}
			)
	return {
		"services": services,
		"resources": frappe.get_list(
			"CRM Resource",
			filters={"enabled": 1},
			fields=[
				"name",
				"resource_name",
				"resource_type",
				"capacity",
				"seats",
				"color",
				"location",
				"centre_location",
			],
			order_by="resource_type asc, resource_name asc",
		),
		"locations": sedi.per_il_boot(),
		"staff": people,
		"price_lists": frappe.get_list(
			"CRM Price List",
			filters={"enabled": 1},
			fields=["name", "price_list_name", "currency", "is_default"],
			order_by="price_list_name asc",
		),
		"statuses": ["Scheduled", "Confirmed", "Completed", "Cancelled", "No Show"],
		# where appointments come from: the calendar can be filtered by it
		"platforms": sorted(
			set(
				frappe.get_all("CRM Booking Connection", filters={"enabled": 1}, pluck="platform")
				if frappe.db.table_exists("CRM Booking Connection")
				else []
			)
		),
		"settings": {
			"timezone": config.timezone or str(scheduling_tz()),
			"default_price_list": pricing.default_price_list(),
			"default_duration": cint(config.default_duration) or 30,
			"allow_override": cint(config.allow_override),
			"can_override": puo("agenda.sovrapponi"),
			# an online visit's room is made by itself on the agency's server
			"video_server": bool(visite_online.server()),
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
	location: str | None = None,
) -> list[dict]:
	"""Free slots for a service, as ISO-8601 UTC, with the assignment behind each;
	at one location where asked (docs/crm/62)."""
	_check_reader()
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
		location=sedi.valida(location),
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
	convention: str | None = None,
	convention_form: str | None = None,
) -> dict:
	"""Live price preview while the appointment is still being edited; under a
	convention, its price and the two shares (doc 61)."""
	_check_reader()
	if convention:
		from crm.convenzioni import convenzioni

		price_list = convenzioni.listino_di(convention) or price_list
	price = pricing.resolve_price(
		service,
		parse_utc(when),
		price_list=price_list,
		staff=_as_list(staff),
		resources=_as_list(resources),
		participants=cint(participants) or 1,
	)
	risposta = price.as_dict(cint(participants) or 1)
	if convention:
		risposta.update(convenzioni.anteprima(convention, convention_form, risposta["total"], service))
	return risposta


@frappe.whitelist()
def check_conflicts(appointment: str | dict) -> list[str]:
	"""Dry-run the conflict rules against an unsaved appointment."""
	_check_reader()
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
			# what the client uses to manage an online booking must survive a staff edit
			"access_token": row.get("access_token"),
			"booked_online": cint(row.get("booked_online")),
			"timezone": row.get("timezone"),
			"booked_by": row.get("booked_by"),
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


def _persona_scritta(nome: str | None, email: str | None, telefono: str | None) -> str | None:
	"""Somebody the desk typed by hand, with a contact: their record, found by the
	contact and the name the way a booking finds it (a family shares an email), or
	made. Left as a name, they had no record: no forms, no invoice, no clinical
	record. A name alone stays a name - two Maria Rossi are not one - and so does
	somebody whose record the user may not make."""
	if not nome or not (email or telefono):
		return None
	from crm.persone.collegate import persona_per_conto, trova_per_nome

	esistente, titolare = trova_per_nome(nome, email=email, telefono=telefono)
	if titolare:
		return esistente or persona_per_conto(titolare, nome)
	if not frappe.has_permission("CRM Lead", "create"):
		return None
	from crm.api.lead import default_status
	from crm.persone import legami

	nome_proprio, cognome = legami.dividi(nome)
	persona = frappe.get_doc(
		{
			"doctype": "CRM Lead",
			"first_name": nome_proprio,
			"last_name": cognome,
			"email": email or "",
			"mobile_no": telefono or "",
			"status": default_status("CRM Lead"),
		}
	)
	persona.insert()
	return persona.name


@frappe.whitelist(methods=["POST"])
def save_appointment(appointment: str | dict, name: str | None = None) -> dict:
	"""Create or update an appointment. Conflicts are enforced by the controller."""
	payload = _loads(appointment)
	values = _normalize(payload)
	for row in values["participants"]:
		if not row["party"]:
			row["party"] = _persona_scritta(row["participant_name"], row["email"], row["phone"])
	if name:
		doc = frappe.get_doc("CRM Appointment", name)
		doc.check_permission("write")
		kept = {
			(row.party_type, row.party or row.participant_name): row
			for row in doc.participants
			if row.get("access_token") or row.get("booked_by")
		}
		# child tables must be replaced wholesale, not merged
		for table in ("staff", "participants", "resources"):
			doc.set(table, [])
		doc.update(values)
		# an editor that never saw the online token, or who booked for whom, must
		# not wipe them
		for row in doc.participants:
			old = kept.get((row.party_type, row.party or row.participant_name))
			if not old:
				continue
			if not row.get("access_token"):
				row.access_token = old.access_token
				row.booked_online = old.booked_online
				row.timezone = old.get("timezone")
			if not row.get("booked_by"):
				row.booked_by = old.get("booked_by")
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
	from crm.permissions.seguono import shows_busy_time

	first, last = parse_date(start), parse_date(end)
	from_dt = datetime.datetime.combine(first, datetime.time.min)
	to_dt = datetime.datetime.combine(last + datetime.timedelta(days=1), datetime.time.min)
	# minutes per person and room say no more than the busy time: whoever is shown
	# the rest of the agenda as busy gets the load of all of it
	rows = (frappe.get_all if shows_busy_time() else frappe.get_list)(
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
	_check("agenda.configura")
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
			"online_visit",
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
	_check("agenda.configura")
	doc = frappe.get_doc("CRM Service", name)
	data = doc.as_dict()
	data.update(online_rule_state(doc))
	data["availability"] = [
		{"workday": row.workday, "start_time": hhmm(row.start_time), "end_time": hhmm(row.end_time)}
		for row in doc.availability
	]
	# whether an online visit gets its room by itself, for the editor to say so
	data["video_server"] = bool(visite_online.server())
	return data


def online_rule_state(service) -> dict:
	"""Which online rules the service customises, and every rule's value in force
	with where it comes from — what the editor shows as "inherited" or "own"."""
	from crm.scheduling.booking_rules import INHERITED, effective_rules, overridden_keys

	def plain(value):
		# Time fields load as timedelta: the editor wants "HH:MM:SS"
		return str(value) if hasattr(value, "total_seconds") else value

	config = settings()
	defaults = config if config.get("default_max_horizon_days") is not None else None
	values, sources = effective_rules(service, defaults)
	return {
		"online_overrides": sorted(overridden_keys(service)),
		"online_effective": {
			key: {"value": plain(value), "source": sources[key]} for key, value in values.items()
		},
		"online_defaults": {key: plain(config.get(default_key)) for key, default_key in INHERITED.items()},
	}


@frappe.whitelist(methods=["POST"])
def save_service(service: str | dict, name: str | None = None) -> dict:
	_check("agenda.configura")
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
			"location",
			# online booking
			"online_confirmation",
			"online_slot_interval",
			"online_max_participants",
			"booking_opens_on",
			"booking_closes_on",
			"same_day_cutoff",
			"online_question",
			"booking_instructions",
			"max_bookings_per_day",
			"max_bookings_per_week",
			"max_concurrent",
			"customer_eligibility",
			"max_active_per_customer",
			"max_per_customer_per_day",
			"min_days_between",
			"cancel_notice_hours",
			"reschedule_notice_hours",
			"max_reschedules",
			# paid online when booking (`crm.pagamenti`)
			"online_payment",
			"online_deposit",
		)
		if key in payload
	}
	for key in ("booking_opens_on", "booking_closes_on", "same_day_cutoff"):
		# an emptied date/time picker sends "", which a Date/Time column refuses
		if key in values and not values[key]:
			values[key] = None
	for key in (
		"allow_staff_choice",
		"show_price_online",
		"require_phone",
		"require_notes",
		"allow_online_cancel",
		"allow_online_reschedule",
		"hide_from_menu",
		"online_visit",
	):
		if key in payload:
			values[key] = cint(payload.get(key))
	if "online_overrides" in payload:
		from crm.scheduling.booking_rules import INHERITED

		keys = _loads(payload.get("online_overrides")) or []
		values["online_overrides"] = json.dumps(sorted(k for k in keys if k in INHERITED))
	values.update(
		{
			"enabled": cint(payload.get("enabled", 1)),
			"bookable_online": cint(payload.get("bookable_online")),
			"price_per_participant": cint(payload.get("price_per_participant")),
			"staff": [_staff_row(row) for row in payload.get("staff") or [] if row.get("user")],
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


def _staff_row(row: dict) -> dict:
	"""A professional on a service, with their optional own length/price/online flag."""
	return {
		"user": row.get("user"),
		"role": row.get("role"),
		"priority": cint(row.get("priority")),
		"duration": cint(row.get("duration")),
		"custom_price": cint(row.get("custom_price")),
		"price": flt(row.get("price")),
		"bookable_online": cint(row.get("bookable_online", 1)),
	}


@frappe.whitelist(methods=["POST"])
def delete_service(name: str) -> None:
	_check("agenda.configura")
	frappe.delete_doc("CRM Service", name)


@frappe.whitelist()
def list_resources() -> list[dict]:
	_check("agenda.turni")
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
			"centre_location",
			"color",
			"hourly_rate",
			"currency",
		],
		order_by="resource_type asc, resource_name asc",
	)


@frappe.whitelist()
def get_resource(name: str) -> dict:
	_check("agenda.turni")
	doc = frappe.get_doc("CRM Resource", name)
	data = doc.as_dict()
	data["availability"] = [
		{"workday": row.workday, "start_time": hhmm(row.start_time), "end_time": hhmm(row.end_time)}
		for row in doc.availability
	]
	return data


@frappe.whitelist(methods=["POST"])
def save_resource(resource: str | dict, name: str | None = None) -> dict:
	_check("agenda.turni")
	payload = _loads(resource)
	values = {
		"resource_name": (payload.get("resource_name") or "").strip(),
		"resource_type": payload.get("resource_type") or "Room",
		"enabled": cint(payload.get("enabled", 1)),
		"capacity": cint(payload.get("capacity")) or 1,
		"seats": cint(payload.get("seats")),
		"location": payload.get("location"),
		"centre_location": sedi.esistente(payload.get("centre_location")),
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
	_check("agenda.turni")
	frappe.delete_doc("CRM Resource", name)


@frappe.whitelist()
def list_price_lists() -> list[dict]:
	_check("agenda.configura")
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
	_check("agenda.configura")
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
	_check("agenda.configura")
	frappe.delete_doc("CRM Price List", name)


@frappe.whitelist()
def list_prices(price_list: str, service: str | None = None) -> list[dict]:
	_check("agenda.configura")
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
	_check("agenda.configura")
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
	_check("agenda.configura")
	frappe.delete_doc("CRM Service Price", name)


@frappe.whitelist()
def list_schedules() -> list[dict]:
	_check("agenda.turni")
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
def get_schedule(user: str = "") -> dict:
	user = turni(user) or user
	config = frappe.get_cached_doc("CRM Scheduling Settings")
	studio = {
		"default_availability": [
			{"workday": row.workday, "start_time": hhmm(row.start_time), "end_time": hhmm(row.end_time)}
			for row in config.default_availability
		],
		"default_holiday_list": config.default_holiday_list,
		"full_name": (frappe.db.get_value("User", user, "full_name") if user else "") or user,
	}
	name = frappe.db.get_value("CRM Staff Schedule", {"user": user}) if user else None
	if not name:
		return {
			**studio,
			"user": user,
			# no schedule yet: they work the studio hours
			"enabled": 0,
			"max_daily_appointments": 0,
			"max_weekly_appointments": 0,
			"bookable_online": 1,
			"public_title": "",
			"public_bio": "",
			"video_link": "",
			"holiday_list": None,
			"availability": [],
			"exceptions": [],
		}
	doc = frappe.get_doc("CRM Staff Schedule", name)
	return {
		**studio,
		"name": doc.name,
		"user": doc.user,
		"enabled": doc.enabled,
		"max_daily_appointments": doc.max_daily_appointments,
		"max_weekly_appointments": doc.get("max_weekly_appointments") or 0,
		"bookable_online": 1 if doc.get("bookable_online") is None else cint(doc.bookable_online),
		"public_title": doc.get("public_title") or "",
		"public_bio": doc.get("public_bio") or "",
		"video_link": doc.get("video_link") or "",
		"holiday_list": doc.holiday_list,
		"availability": [
			{
				"workday": row.workday,
				"start_time": hhmm(row.start_time),
				"end_time": hhmm(row.end_time),
				"centre_location": row.get("centre_location") or "",
			}
			for row in doc.availability
		],
		"exceptions": [
			{
				"date": str(row.date),
				"unavailable": row.unavailable,
				"start_time": hhmm(row.start_time),
				"end_time": hhmm(row.end_time),
				"reason": row.reason,
				"centre_location": row.get("centre_location") or "",
			}
			for row in doc.exceptions
		],
	}


@frappe.whitelist(methods=["POST"])
def save_schedule(schedule: str | dict) -> dict:
	payload = _loads(schedule)
	proprio = turni(payload.get("user"))
	user = proprio or payload.get("user")
	if not user:
		frappe.throw(_("Pick a professional"))
	values = {
		"user": user,
		"enabled": cint(payload.get("enabled", 1)),
		"max_daily_appointments": cint(payload.get("max_daily_appointments")),
		"max_weekly_appointments": cint(payload.get("max_weekly_appointments")),
		"holiday_list": payload.get("holiday_list") or None,
		"availability": [
			{
				"workday": row.get("workday"),
				"start_time": row.get("start_time"),
				"end_time": row.get("end_time"),
				# where these hours are worked (docs/crm/62): empty, anywhere
				"centre_location": sedi.esistente(row.get("centre_location")),
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
				"centre_location": sedi.esistente(row.get("centre_location")),
			}
			for row in payload.get("exceptions") or []
			if row.get("date")
		],
	}
	# the online side (bookable, title, bio) lives in Online booking: a rota save
	# that does not carry it leaves it alone
	if "bookable_online" in payload and not proprio:
		values["bookable_online"] = cint(payload.get("bookable_online"))
	for key in ("public_title", "public_bio"):
		# a practitioner's own hours, not how the booking page shows them
		if key in payload and not proprio:
			values[key] = payload.get(key) or None
	# their own online visit room: a practitioner sets theirs too
	if "video_link" in payload:
		link = (payload.get("video_link") or "").strip()
		if link and not visite_online_regole.link_valido(link):
			frappe.throw(_("The online visit's link must be an address starting with https://"))
		values["video_link"] = link or None
	if values["enabled"] and not values["availability"]:
		frappe.throw(_("Add at least one time slot, or use the studio hours"))
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
	_check("agenda.configura")
	doc = frappe.get_doc("CRM Scheduling Settings")
	data = doc.as_dict()
	data["default_availability"] = [
		{"workday": row.workday, "start_time": hhmm(row.start_time), "end_time": hhmm(row.end_time)}
		for row in doc.default_availability
	]
	# a field never saved reads its default, never 0: the months the misses count over
	data["no_show_months"] = data.get("no_show_months") or 12
	# what an empty time zone means, for the settings page to say it
	data["site_timezone"] = frappe.utils.get_system_timezone()
	# what the booking page falls back to, for the settings to show it. One field
	# per read: `get_single_value` takes a single fieldname, and handed a list and
	# `as_dict` it raised, so this whole settings page failed to load
	data["brand"] = {
		"name": frappe.db.get_single_value("FCRM Settings", "brand_name") or "",
		"logo": frappe.db.get_single_value("FCRM Settings", "brand_logo") or "",
	}
	return data


@frappe.whitelist(methods=["POST"])
def save_scheduling_settings(scheduling_settings: str | dict) -> dict:
	_check("agenda.configura")
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
		# the public /prenota page
		"online_booking_enabled",
		"booking_page_title",
		"booking_page_logo",
		"booking_page_intro",
		"privacy_policy_url",
		"require_privacy_consent",
		"ask_marketing_consent",
		"notify_staff_on_booking",
		"send_client_confirmation",
		"max_active_per_customer",
		"no_show_limit",
		"no_show_months",
		"no_show_action",
		# online defaults every service inherits
		"default_min_notice_hours",
		"default_max_horizon_days",
		"default_online_slot_interval",
		"default_online_confirmation",
		"default_same_day_cutoff",
		"default_allow_online_cancel",
		"default_cancel_notice_hours",
		"default_allow_online_reschedule",
		"default_reschedule_notice_hours",
		"default_max_reschedules",
		"default_require_phone",
		"default_max_per_customer_per_day",
	):
		if key in payload:
			value = payload[key]
			# an emptied time picker sends "", which a Time column refuses
			doc.set(key, None if value == "" and key.endswith("cutoff") else value)
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
