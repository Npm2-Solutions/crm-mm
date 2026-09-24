# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Public self-booking of services: the service menu, the professional, the slot.

The Calendly-style pages in ``crm.api.booking`` book a *person's time*. This
module books a *service* through the full scheduling engine — the staffing
model, the rooms and equipment it needs, group seats, the price list — so what
a client books online is exactly what the receptionist would have booked on the
calendar, with the same conflict rules behind it.

On top of the engine sit the online limits of each service
(:mod:`crm.scheduling.booking_rules`): notice, horizon, seasonal window,
same-day cutoff, daily/weekly/concurrent caps, per-client caps and spacing,
who may book, and how late a client may cancel or move.

Clients manage their booking through a token stored on *their* participant row,
so a client of a group class can cancel their seat without touching the others.
"""

from __future__ import annotations

import datetime
import hashlib
from zoneinfo import ZoneInfo

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import cint, flt, get_url

from crm.scheduling import booking_rules as rules_mod
from crm.scheduling.availability import ACTIVE_STATUSES, get_slots, settings
from crm.scheduling.timeutils import (
	UTC,
	from_system_naive,
	parse_date,
	parse_utc,
	scheduling_tz,
	to_system_naive,
)

MAX_RANGE_DAYS = 31
ONLINE_SOURCE = "Online booking"


# --------------------------------------------------------------------------
# messages
# --------------------------------------------------------------------------


def limit_message(code: str) -> str:
	"""The client-facing sentence for a ``booking_rules`` code."""
	return {
		rules_mod.LIMIT_IN_PAST: _("This time is in the past."),
		rules_mod.LIMIT_TOO_SOON: _("This time is too close: it can no longer be booked online."),
		rules_mod.LIMIT_TOO_FAR: _("This date is too far ahead to be booked yet."),
		rules_mod.LIMIT_NOT_OPEN_YET: _("Online booking for this service is not open yet for this date."),
		rules_mod.LIMIT_CLOSED: _("Online booking for this service is closed for this date."),
		rules_mod.LIMIT_SAME_DAY_CUTOFF: _("Same-day bookings are closed for today."),
		rules_mod.LIMIT_SERVICE_DAY_FULL: _("This day is fully booked for this service."),
		rules_mod.LIMIT_SERVICE_WEEK_FULL: _("This week is fully booked for this service."),
		rules_mod.LIMIT_CONCURRENT: _("This time is fully booked for this service."),
		rules_mod.LIMIT_CLIENT_ACTIVE: _(
			"You already have the maximum number of upcoming bookings. Cancel one or contact us."
		),
		rules_mod.LIMIT_CLIENT_DAY: _("You already have the maximum number of bookings for that day."),
		rules_mod.LIMIT_CLIENT_SPACING: _("This service needs more time between two of your bookings."),
		rules_mod.LIMIT_NEW_ONLY: _("This service can be booked online by new clients only."),
		rules_mod.LIMIT_RETURNING_ONLY: _(
			"This service can be booked online by existing clients only. Please contact us."
		),
		rules_mod.LIMIT_CANCEL_DISABLED: _("This booking cannot be cancelled online. Please contact us."),
		rules_mod.LIMIT_CANCEL_NOTICE: _("It is too late to cancel online. Please contact us."),
		rules_mod.LIMIT_RESCHEDULE_DISABLED: _("This booking cannot be moved online. Please contact us."),
		rules_mod.LIMIT_RESCHEDULE_NOTICE: _(
			"It is too late to move this booking online. Please contact us."
		),
		rules_mod.LIMIT_RESCHEDULE_COUNT: _(
			"This booking has already been moved the maximum number of times."
		),
	}.get(code, _("This time cannot be booked."))


# --------------------------------------------------------------------------
# lookup helpers
# --------------------------------------------------------------------------


def _flag(doc, key: str, default: int = 1) -> int:
	"""A Check that may not exist yet on a site that has not migrated."""
	value = doc.get(key)
	return default if value is None else cint(value)


def _config():
	config = settings()
	if not _flag(config, "online_booking_enabled"):
		frappe.throw(_("Online booking is currently closed"), frappe.PermissionError)
	return config


def _online_service(name: str):
	if not name or not frappe.db.get_value("CRM Service", {"name": name, "enabled": 1, "bookable_online": 1}):
		frappe.throw(_("Service not found"), frappe.DoesNotExistError)
	return frappe.get_cached_doc("CRM Service", name)


def _resolve_service(key: str):
	"""A service by name or by its website slug — the slug is what links carry."""
	name = frappe.db.get_value("CRM Service", {"website_slug": key}) if key else None
	return _online_service(name or key)


def _rules(service) -> rules_mod.OnlineRules:
	config = settings()
	return rules_mod.OnlineRules.from_service(
		service, global_max_active=config.get("max_active_per_customer"), defaults=_defaults(config)
	)


def _defaults(config):
	"""The booking-page defaults, or ``None`` on a site that has not migrated yet."""
	return config if config.get("default_max_horizon_days") is not None else None


def _effective(service) -> dict:
	"""The inheritable online rules in force for this service (own or default)."""
	values, _sources = rules_mod.effective_rules(service, _defaults(settings()))
	return values


def _online_staff(service) -> list[str]:
	"""Professionals of the service who take it through the booking page."""
	from crm.scheduling.availability import staff_profile

	return [
		row.user
		for row in service.staff
		if (row.get("bookable_online") is None or cint(row.get("bookable_online")))
		and staff_profile(row.user)["online"]
	]


def public_staff_id(user: str) -> str:
	"""Opaque id for a professional: user ids are e-mail addresses, and those
	have no business in a public page's source."""
	return hashlib.sha256(f"{frappe.local.site}:{user}".encode()).hexdigest()[:12]


def _staff_from_public_id(service, public_id: str | None) -> str | None:
	if not public_id:
		return None
	for row in service.staff:
		if public_staff_id(row.user) == public_id:
			return row.user
	frappe.throw(_("Professional not found"))


def _staff_card(user: str) -> dict:
	# a month of slots names the same few people hundreds of times: ask once per request
	if not hasattr(frappe.local, "crm_booking_staff_cards"):
		frappe.local.crm_booking_staff_cards = {}
	cache = frappe.local.crm_booking_staff_cards
	if user not in cache:
		info = frappe.db.get_value("User", user, ["full_name", "user_image"], as_dict=True) or {}
		profile = (
			frappe.db.get_value(
				"CRM Staff Schedule", {"user": user}, ["public_title", "public_bio"], as_dict=True
			)
			or {}
		)
		cache[user] = {**info, **profile}
	info = cache[user]
	return {
		"id": public_staff_id(user),
		"name": info.get("full_name") or _("Professional"),
		"image": info.get("user_image") or "",
		"title": info.get("public_title") or "",
		"bio": info.get("public_bio") or "",
	}


def _money(amount, currency) -> str:
	return frappe.utils.fmt_money(flt(amount), currency=currency or "EUR") if flt(amount) else ""


def _tz_or(value: str | None, fallback: ZoneInfo) -> ZoneInfo:
	if value:
		try:
			return ZoneInfo(value)
		except Exception:
			pass
	return fallback


# --------------------------------------------------------------------------
# catalogue
# --------------------------------------------------------------------------


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_catalog() -> dict:
	"""The service menu: categories, services, professionals, page settings."""
	config = _config()
	names = frappe.get_all(
		"CRM Service",
		filters={"enabled": 1, "bookable_online": 1},
		pluck="name",
		order_by="website_order asc, service_name asc",
	)
	services = []
	for name in names:
		service = frappe.get_cached_doc("CRM Service", name)
		services.append(_service_card(service))
	services = [card for card in services if card["bookable"]]
	categories = []
	for service in services:
		if service["category"] and service["category"] not in categories:
			categories.append(service["category"])
	# the team, for staff pages (/prenota?professionista=…): who they are, what they do
	people: dict[str, dict] = {}
	for name in names:
		service = frappe.get_cached_doc("CRM Service", name)
		card_id = service.website_slug or service.name
		for user in _online_staff(service):
			person = people.setdefault(user, {**_staff_card(user), "services": []})
			person["services"].append(card_id)
	return {
		"title": config.get("booking_page_title")
		or frappe.db.get_single_value("Website Settings", "app_name")
		or _("Book an appointment"),
		"intro": config.get("booking_page_intro") or "",
		"privacy_policy_url": config.get("privacy_policy_url") or "",
		"require_consent": cint(config.get("require_privacy_consent")),
		"timezone": str(scheduling_tz()),
		"categories": categories,
		"services": services,
		"people": sorted(people.values(), key=lambda p: p["name"]),
	}


def _service_card(service) -> dict:
	show_price = _flag(service, "show_price_online")
	staff_choice = _flag(service, "allow_staff_choice")
	online_staff = _online_staff(service)
	rules = _effective(service)
	# picking a professional only makes sense when the engine picks one of several
	can_pick = staff_choice and service.staff_selection == "Any one" and len(online_staff) > 1
	prices, durations = _price_and_duration_range(service, online_staff)
	return {
		"id": service.website_slug or service.name,
		"name": service.service_name,
		"category": service.category or "",
		"color": service.color or "",
		"description": service.short_description or service.description or "",
		"image": service.website_image or "",
		"duration": durations[0],
		"duration_max": durations[1],
		"price": prices[0] if show_price else 0,
		"formatted_price": _money(prices[0], service.currency) if show_price else "",
		# "from € 40" when professionals charge differently
		"price_from": bool(show_price and prices[1] > prices[0]),
		"per_participant": cint(service.price_per_participant),
		"max_seats": max(cint(service.get("online_max_participants")) or 1, 1)
		if cint(service.max_participants) > 1
		else 1,
		"group": cint(service.max_participants) > 1,
		"can_pick_staff": bool(can_pick),
		"staff": [_staff_card(user) for user in online_staff] if can_pick else [],
		"staff_ids": [public_staff_id(user) for user in online_staff],
		"require_phone": cint(rules.get("require_phone") if rules.get("require_phone") is not None else 1),
		"require_notes": cint(service.get("require_notes")),
		"question": service.get("online_question") or "",
		"min_notice_hours": cint(rules.get("min_notice_hours")),
		"max_horizon_days": cint(rules.get("max_horizon_days")),
		"manual_approval": rules.get("online_confirmation") == "Manual approval",
		"bookable": bool(online_staff),
	}


def _price_and_duration_range(service, users: list[str]) -> tuple[tuple[float, float], tuple[int, int]]:
	"""Lowest/highest price and length across the professionals who take it online."""
	base_price, base_minutes = flt(service.default_price), cint(service.duration)
	prices, minutes = [], []
	for row in service.staff:
		if row.user not in users:
			continue
		prices.append(flt(row.get("price")) if cint(row.get("custom_price")) else base_price)
		minutes.append(cint(row.get("duration")) or base_minutes)
	prices = prices or [base_price]
	minutes = minutes or [base_minutes]
	return (min(prices), max(prices)), (min(minutes), max(minutes))


# --------------------------------------------------------------------------
# slots
# --------------------------------------------------------------------------


def _service_booked(service_name: str, start, end, exclude: str | None = None) -> list[tuple]:
	"""Active appointments of the service overlapping a padded window.

	Padded by a week each side, so the weekly cap sees the whole ISO week.
	"""
	pad = datetime.timedelta(days=7)
	filters = {
		"service": service_name,
		"status": ["in", ACTIVE_STATUSES],
		"starts_on": ["<", to_system_naive(end + pad)],
		"ends_on": [">", to_system_naive(start - pad)],
	}
	if exclude:
		filters["name"] = ["!=", exclude]
	return [
		(from_system_naive(r.starts_on), from_system_naive(r.ends_on))
		for r in frappe.get_all("CRM Appointment", filters=filters, fields=["starts_on", "ends_on"])
	]


def online_slots(
	service,
	first: datetime.date,
	last: datetime.date,
	staff_user: str | None = None,
	participants: int = 1,
	exclude_appointment: str | None = None,
) -> list:
	"""Engine slots narrowed by the service's online rules."""
	rules = _rules(service)
	now = datetime.datetime.now(UTC)
	earliest, latest = rules.window(now)
	slots = get_slots(
		service.name,
		first,
		last,
		staff=[staff_user] if staff_user else None,
		participants=participants,
		exclude_appointment=exclude_appointment,
		online=True,
		# the online notice/horizon (own or inherited) decide, not the internal ones
		window=(earliest, latest or now + datetime.timedelta(days=3650)),
	)
	tz = scheduling_tz()
	window_start = datetime.datetime.combine(first, datetime.time.min, tzinfo=tz)
	window_end = datetime.datetime.combine(last + datetime.timedelta(days=1), datetime.time.min, tzinfo=tz)
	booked = _service_booked(service.name, window_start, window_end, exclude=exclude_appointment)
	slots = rules_mod.thin_grid(slots, cint(_effective(service).get("online_slot_interval")), tz)
	slots = rules_mod.filter_slots(rules, slots, now, tz, booked)
	if staff_user:
		slots = [s for s in slots if staff_user in s.staff]
	# a group slot needs room for everybody this client is bringing
	return [s for s in slots if cint(s.seats_left) >= participants]


@frappe.whitelist(allow_guest=True, methods=["GET"])
@rate_limit(limit=300, seconds=60 * 60)
def get_slots_public(
	service: str,
	start_date: str,
	end_date: str,
	staff: str | None = None,
	participants: int = 1,
	timezone: str | None = None,
) -> dict:
	"""Free start times for a service between two dates.

	Answers per day, in the client's timezone, so the page can grey out full
	days on the month grid without a second round trip.
	"""
	_config()
	doc = _resolve_service(service)
	first, last = parse_date(start_date), parse_date(end_date)
	if last < first:
		frappe.throw(_("End date must be on or after start date"))
	if (last - first).days > MAX_RANGE_DAYS:
		frappe.throw(_("Date range too large"))
	seats = _seats(doc, participants)
	user = _staff_from_public_id(doc, staff)
	client_tz = _tz_or(timezone, scheduling_tz())

	days: dict[str, list[dict]] = {}
	seen = set()
	for slot in online_slots(doc, first, last, user, seats):
		key = (slot.start, slot.join_appointment)
		if key in seen:
			continue
		seen.add(key)
		local = slot.start.astimezone(client_tz)
		days.setdefault(local.date().isoformat(), []).append(
			{
				"start": slot.start.isoformat(),
				"time": local.strftime("%H:%M"),
				"seats_left": cint(slot.seats_left),
				"group": bool(slot.join_appointment),
				"staff": [_staff_card(u)["name"] for u in slot.staff]
				if doc.staff_selection != "All required"
				else [],
			}
		)
	earliest, latest = _rules(doc).window(datetime.datetime.now(UTC))
	return {
		"days": days,
		"min_date": earliest.astimezone(client_tz).date().isoformat(),
		"max_date": latest.astimezone(client_tz).date().isoformat() if latest else None,
	}


def _seats(service, requested) -> int:
	if cint(service.max_participants) <= 1:
		return 1
	cap = max(cint(service.get("online_max_participants")) or 1, 1)
	return min(max(cint(requested) or 1, 1), cap)


# --------------------------------------------------------------------------
# booking
# --------------------------------------------------------------------------


def _client_history(service_name: str, email: str, phone: str, lead: str | None) -> rules_mod.ClientHistory:
	"""The client's own non-cancelled appointments, matched by any identity."""
	appointment = frappe.qb.DocType("CRM Appointment")
	participant = frappe.qb.DocType("CRM Appointment Participant")
	matches = []
	if email:
		matches.append(participant.email == email)
	if phone:
		matches.append(participant.phone == phone)
	if lead:
		matches.append((participant.party_type == "CRM Lead") & (participant.party == lead))
	if not matches:
		return rules_mod.ClientHistory()
	condition = matches[0]
	for extra in matches[1:]:
		condition = condition | extra
	rows = (
		frappe.qb.from_(participant)
		.join(appointment)
		.on(participant.parent == appointment.name)
		.select(appointment.name, appointment.service, appointment.starts_on)
		.where(condition)
		.where(participant.status != "Cancelled")
		.where(appointment.status.isin(ACTIVE_STATUSES))
		.run(as_dict=True)
	)
	now = datetime.datetime.now(UTC)
	unique = {row.name: row for row in rows}.values()
	starts = [(row.service, from_system_naive(row.starts_on)) for row in unique]
	return rules_mod.ClientHistory(
		service_starts=[s for svc, s in starts if svc == service_name],
		all_starts=[s for _svc, s in starts],
		is_returning=any(s < now for _svc, s in starts),
	)


def _clean_email(value: str | None) -> str:
	value = (value or "").strip().lower()
	if value and not frappe.utils.validate_email_address(value):
		frappe.throw(_("Please enter a valid email address"))
	return value


def _clean_phone(value: str | None) -> str:
	from crm.utils import to_e164

	value = (value or "").strip()
	if not value:
		return ""
	return to_e164(value) or value


def _find_slot(service, start_utc, staff_user, seats, exclude_appointment=None):
	tz = scheduling_tz()
	day = start_utc.astimezone(tz).date()
	for slot in online_slots(service, day, day, staff_user, seats, exclude_appointment):
		if slot.start == start_utc:
			return slot
	return None


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=10, seconds=60 * 60)
def book(
	service: str,
	start: str,
	full_name: str,
	email: str,
	phone: str | None = None,
	notes: str | None = None,
	staff: str | None = None,
	participants: int = 1,
	consent: int | str | None = None,
	timezone: str | None = None,
	crm_vid: str | None = None,
	crm_sid: str | None = None,
) -> dict:
	"""Book a service on a free slot; returns what the confirmation page shows."""
	config = _config()
	frappe.flags.in_service_booking_api = True
	doc = _resolve_service(service)
	# serialise bookings of the same service: the re-check below must not race
	frappe.db.get_value("CRM Service", doc.name, "name", for_update=True)

	full_name = (full_name or "").strip()
	email = _clean_email(email)
	phone = _clean_phone(phone)
	notes = (notes or "").strip()
	if not full_name or not email:
		frappe.throw(_("Name and email are required"))
	require_phone = _effective(doc).get("require_phone")
	if (require_phone is None or cint(require_phone)) and not phone:
		frappe.throw(_("A phone number is required"))
	if cint(doc.get("require_notes")) and not notes:
		frappe.throw(_("Please answer the question: {0}").format(doc.get("online_question") or _("Notes")))
	if cint(config.get("require_privacy_consent")) and not cint(consent):
		frappe.throw(_("Please accept the privacy policy to book"))

	start_utc = parse_utc(start)
	seats = _seats(doc, participants)
	rules = _rules(doc)
	now = datetime.datetime.now(UTC)
	tz = scheduling_tz()
	if code := rules.check_time(start_utc, now, tz):
		frappe.throw(limit_message(code))

	from crm.api.lead import find_person

	existing = find_person(email=email, phone=phone)
	history = _client_history(doc.name, email, phone, existing)
	if code := rules.check_client(start_utc, now, tz, history):
		frappe.throw(limit_message(code))

	staff_user = _staff_from_public_id(doc, staff) if staff and _flag(doc, "allow_staff_choice") else None
	slot = _find_slot(doc, start_utc, staff_user, seats)
	if not slot:
		frappe.throw(_("This slot is no longer available. Please pick another one."))

	from crm.api.booking import find_or_create_person

	lead = find_or_create_person(
		full_name,
		email,
		phone,
		crm_vid=crm_vid,
		crm_sid=crm_sid,
		source=ONLINE_SOURCE,
		medium="booking",
		source_dimension="service_booking",
	)
	token = frappe.generate_hash(length=32)
	rows = _participant_rows(full_name, email, phone, lead, token, seats, _valid_tz_name(timezone))
	status = "Scheduled" if _effective(doc).get("online_confirmation") == "Manual approval" else "Confirmed"

	if slot.join_appointment:
		appointment = frappe.get_doc("CRM Appointment", slot.join_appointment)
		for row in rows:
			appointment.append("participants", row)
		if notes:
			appointment.customer_notes = "\n".join(
				filter(None, [appointment.customer_notes, f"{full_name}: {notes}"])
			)
		appointment.flags.ignore_permissions = True
		appointment.save(ignore_permissions=True)
	else:
		appointment = frappe.get_doc(
			{
				"doctype": "CRM Appointment",
				"service": doc.name,
				"status": status,
				"starts_on": to_system_naive(slot.start),
				"ends_on": to_system_naive(slot.end),
				"staff": [{"user": user, "required": 1} for user in slot.staff],
				"resources": slot.resources,
				"participants": rows,
				"source": "Online",
				"customer_notes": notes,
			}
		)
		appointment.insert(ignore_permissions=True)

	send_client_email(appointment, token, "booked")
	notify_staff(appointment, _("New online booking"))
	return public_view(appointment, token)


def _participant_rows(full_name, email, phone, lead, token, seats, timezone=None) -> list[dict]:
	rows = [
		{
			"party_type": "CRM Lead",
			"party": lead,
			"participant_name": full_name,
			"email": email,
			"phone": phone,
			"status": "Booked",
			"access_token": token,
			"booked_online": 1,
			"timezone": timezone,
		}
	]
	# extra seats: the people a client brings along are guests, not records
	for index in range(2, seats + 1):
		rows.append(
			{
				"party_type": "CRM Lead",
				"participant_name": _("{0} — guest {1}").format(full_name, index - 1),
				"status": "Booked",
				"access_token": token,
				"booked_online": 1,
			}
		)
	return rows


def _valid_tz_name(value: str | None) -> str | None:
	if not value:
		return None
	try:
		ZoneInfo(value)
	except Exception:
		return None
	return value


# --------------------------------------------------------------------------
# manage: view, cancel, reschedule
# --------------------------------------------------------------------------


def _by_token(token: str):
	if not token or len(token) < 16:
		frappe.throw(_("Invalid booking link"), frappe.PermissionError)
	parent = frappe.db.get_value("CRM Appointment Participant", {"access_token": token}, "parent")
	if not parent:
		frappe.throw(_("Booking not found"), frappe.DoesNotExistError)
	return frappe.get_doc("CRM Appointment", parent)


def _my_rows(appointment, token: str) -> list:
	return [row for row in appointment.participants if row.access_token == token]


def public_view(appointment, token: str) -> dict:
	service = frappe.get_cached_doc("CRM Service", appointment.service)
	rules = _rules(service)
	start = from_system_naive(appointment.starts_on)
	end = from_system_naive(appointment.ends_on)
	now = datetime.datetime.now(UTC)
	mine = _my_rows(appointment, token)
	cancelled = appointment.status == "Cancelled" or all(r.status == "Cancelled" for r in mine)
	status = "Cancelled" if cancelled else appointment.status
	active = status in ("Scheduled", "Confirmed") and start > now
	cancel_block = rules.check_cancel(start, now) if active else "inactive"
	move_block = rules.check_reschedule(start, now, appointment.reschedule_count) if active else "inactive"
	client_tz = next((r.timezone for r in mine if r.get("timezone")), None) or str(scheduling_tz())
	amount = (
		sum(flt(r.amount) for r in mine)
		if cint(appointment.per_participant)
		else flt(appointment.total_amount)
	)
	show_price = _flag(service, "show_price_online")
	return {
		"token": token,
		"service": service.service_name,
		"service_id": service.website_slug or service.name,
		"status": status,
		"pending_approval": status == "Scheduled",
		"start": start.isoformat(),
		"end": end.isoformat(),
		"timezone": client_tz,
		"duration": int((end - start).total_seconds() // 60),
		"staff": [_staff_card(row.user)["name"] for row in appointment.staff],
		"location": appointment.location or "",
		"seats": len([r for r in mine if r.status != "Cancelled"]) or len(mine),
		"client_name": mine[0].participant_name if mine else "",
		"formatted_price": _money(amount, appointment.currency) if show_price else "",
		"instructions": service.get("booking_instructions") or "",
		"can_cancel": not cancel_block,
		"cancel_block": limit_message(cancel_block) if cancel_block and cancel_block != "inactive" else "",
		"can_reschedule": not move_block,
		"reschedule_block": limit_message(move_block) if move_block and move_block != "inactive" else "",
		"calendar_links": _calendar_links(service.service_name, start, end, appointment.location),
	}


@frappe.whitelist(allow_guest=True, methods=["GET"])
def get_booking(token: str) -> dict:
	return public_view(_by_token(token), token)


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=20, seconds=60 * 60)
def cancel(token: str, reason: str | None = None) -> dict:
	frappe.flags.in_service_booking_api = True
	appointment = _by_token(token)
	service = frappe.get_cached_doc("CRM Service", appointment.service)
	start = from_system_naive(appointment.starts_on)
	if appointment.status == "Cancelled":
		return public_view(appointment, token)
	if code := _rules(service).check_cancel(start, datetime.datetime.now(UTC)):
		frappe.throw(limit_message(code))
	_cancel_rows(appointment, token, reason)
	send_client_email(appointment, token, "cancelled")
	notify_staff(appointment, _("Online booking cancelled"))
	return public_view(appointment, token)


def _cancel_rows(appointment, token: str, reason: str | None):
	mine = _my_rows(appointment, token)
	others = [r for r in appointment.participants if r.status != "Cancelled" and r.access_token != token]
	reason = (reason or "").strip() or _("Cancelled online by the client")
	if others:
		# a seat in a group session: free the seat, the session goes on
		for row in mine:
			row.status = "Cancelled"
	else:
		appointment.status = "Cancelled"
		appointment.cancellation_reason = reason
		for row in appointment.participants:
			row.status = "Cancelled"
	appointment.save(ignore_permissions=True)


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=20, seconds=60 * 60)
def reschedule(token: str, start: str) -> dict:
	frappe.flags.in_service_booking_api = True
	appointment = _by_token(token)
	service = _online_service(appointment.service)
	now = datetime.datetime.now(UTC)
	current = from_system_naive(appointment.starts_on)
	rules = _rules(service)
	if appointment.status not in ("Scheduled", "Confirmed"):
		frappe.throw(_("Only active bookings can be moved"))
	if code := rules.check_reschedule(current, now, appointment.reschedule_count):
		frappe.throw(limit_message(code))

	frappe.db.get_value("CRM Service", service.name, "name", for_update=True)
	new_start = parse_utc(start)
	if code := rules.check_time(new_start, now, scheduling_tz()):
		frappe.throw(limit_message(code))

	mine = _my_rows(appointment, token)
	others = [r for r in appointment.participants if r.status != "Cancelled" and r.access_token != token]
	seats = len([r for r in mine if r.status != "Cancelled"]) or 1

	if not others:
		# the whole appointment is this client's: move it, keeping the professional if possible
		current_staff = [row.user for row in appointment.staff]
		slot = None
		if len(current_staff) == 1:
			slot = _find_slot(service, new_start, current_staff[0], seats, appointment.name)
		slot = slot or _find_slot(service, new_start, None, seats, appointment.name)
		if not slot or slot.join_appointment:
			frappe.throw(_("This slot is no longer available. Please pick another one."))
		appointment.starts_on = to_system_naive(slot.start)
		appointment.ends_on = to_system_naive(slot.end)
		appointment.set("staff", [{"user": u, "required": 1} for u in slot.staff])
		appointment.set("resources", slot.resources)
		appointment.reschedule_count = cint(appointment.reschedule_count) + 1
		appointment.save(ignore_permissions=True)
		target = appointment
	else:
		# a seat in a group: leave this session, take a seat in (or open) another
		slot = _find_slot(service, new_start, None, seats)
		if not slot:
			frappe.throw(_("This slot is no longer available. Please pick another one."))
		carried = [
			{
				k: row.get(k)
				for k in (
					"party_type",
					"party",
					"participant_name",
					"email",
					"phone",
					"access_token",
					"timezone",
				)
			}
			| {"status": "Booked", "booked_online": 1}
			for row in mine
			if row.status != "Cancelled"
		]
		for row in mine:
			row.status = "Cancelled"
			row.access_token = None
		appointment.save(ignore_permissions=True)
		if slot.join_appointment:
			target = frappe.get_doc("CRM Appointment", slot.join_appointment)
			for row in carried:
				target.append("participants", row)
			target.reschedule_count = cint(target.reschedule_count)
			target.save(ignore_permissions=True)
		else:
			target = frappe.get_doc(
				{
					"doctype": "CRM Appointment",
					"service": service.name,
					"status": appointment.status,
					"starts_on": to_system_naive(slot.start),
					"ends_on": to_system_naive(slot.end),
					"staff": [{"user": u, "required": 1} for u in slot.staff],
					"resources": slot.resources,
					"participants": carried,
					"source": "Online",
					"reschedule_count": 1,
				}
			)
			target.insert(ignore_permissions=True)

	send_client_email(target, token, "rescheduled")
	notify_staff(target, _("Online booking moved"))
	return public_view(target, token)


# --------------------------------------------------------------------------
# notifications
# --------------------------------------------------------------------------


def manage_url(token: str) -> str:
	return get_url(f"/prenota?token={token}")


def _calendar_links(title: str, start, end, location: str | None) -> dict:
	from urllib.parse import urlencode

	fmt = "%Y%m%dT%H%M%SZ"
	google = "https://calendar.google.com/calendar/render?" + urlencode(
		{
			"action": "TEMPLATE",
			"text": title,
			"dates": f"{start.strftime(fmt)}/{end.strftime(fmt)}",
			"location": location or "",
		}
	)
	outlook = "https://outlook.live.com/calendar/0/deeplink/compose?" + urlencode(
		{
			"subject": title,
			"startdt": start.isoformat(),
			"enddt": end.isoformat(),
			"location": location or "",
			"path": "/calendar/action/compose",
			"rru": "addevent",
		}
	)
	return {"google": google, "outlook": outlook}


def ics_file(uid: str, title: str, start, end, location: str | None, cancelled: bool = False) -> dict:
	fmt = "%Y%m%dT%H%M%SZ"

	def esc(value: str) -> str:
		return (
			(value or "").replace("\\", "\\\\").replace(",", r"\,").replace(";", r"\;").replace("\n", r"\n")
		)

	lines = [
		"BEGIN:VCALENDAR",
		"VERSION:2.0",
		"PRODID:-//CRM//Service Booking//EN",
		f"METHOD:{'CANCEL' if cancelled else 'PUBLISH'}",
		"BEGIN:VEVENT",
		f"UID:{uid}@crm-service-booking",
		f"DTSTAMP:{datetime.datetime.now(UTC).strftime(fmt)}",
		f"DTSTART:{start.astimezone(UTC).strftime(fmt)}",
		f"DTEND:{end.astimezone(UTC).strftime(fmt)}",
		f"SUMMARY:{esc(title)}",
		f"LOCATION:{esc(location or '')}",
		f"STATUS:{'CANCELLED' if cancelled else 'CONFIRMED'}",
		"END:VEVENT",
		"END:VCALENDAR",
		"",
	]
	return {"fname": "appuntamento.ics", "fcontent": "\r\n".join(lines)}


def send_client_email(appointment, token: str, kind: str) -> None:
	"""Tell the client what just happened to their booking. Never blocks a booking."""
	if not _flag(settings(), "send_client_confirmation"):
		return
	mine = [r for r in appointment.participants if r.access_token == token and r.email]
	if not mine:
		return
	try:
		view = public_view(appointment, token)
		tz = _tz_or(view["timezone"], scheduling_tz())
		start = from_system_naive(appointment.starts_on)
		end = from_system_naive(appointment.ends_on)
		when = start.astimezone(tz).strftime("%d/%m/%Y %H:%M")
		heading = {
			"booked": _("Your booking request has been received")
			if view["pending_approval"]
			else _("Your booking is confirmed"),
			"confirmed": _("Your booking is confirmed"),
			"rescheduled": _("Your booking has been moved"),
			"cancelled": _("Your booking has been cancelled"),
		}.get(kind, _("Booking update"))
		esc = frappe.utils.escape_html
		lines = [
			f"<p>{_('Hi {0},').format(esc(mine[0].participant_name or ''))}</p>",
			f"<p><b>{esc(heading)}</b></p>",
			f"<p>{esc(view['service'])}<br>{when} ({esc(str(tz))})</p>",
		]
		if view["staff"]:
			lines.append(f"<p>{_('With')}: {esc(', '.join(view['staff']))}</p>")
		if view["location"]:
			lines.append(f"<p>{esc(view['location'])}</p>")
		if view["formatted_price"]:
			lines.append(f"<p>{_('Price')}: <b>{view['formatted_price']}</b></p>")
		if view["pending_approval"] and kind == "booked":
			lines.append(f"<p>{_('We will confirm it shortly.')}</p>")
		if view["instructions"] and kind != "cancelled":
			lines.append(f"<p>{esc(view['instructions'])}</p>")
		if kind != "cancelled":
			lines.append(f'<p><a href="{manage_url(token)}">{_("Manage your booking")}</a></p>')
		frappe.sendmail(
			recipients=[mine[0].email],
			subject=f"{heading} — {view['service']}, {when}",
			message="".join(lines),
			attachments=[
				ics_file(token, view["service"], start, end, view["location"], cancelled=kind == "cancelled")
			],
			reference_doctype="CRM Appointment",
			reference_name=appointment.name,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"Service booking: {kind} email failed")


def notify_staff(appointment, subject: str) -> None:
	if not _flag(settings(), "notify_staff_on_booking"):
		return
	try:
		emails = [
			email
			for email in (frappe.db.get_value("User", row.user, "email") for row in appointment.staff)
			if email
		]
		if not emails:
			return
		start = from_system_naive(appointment.starts_on).astimezone(scheduling_tz())
		frappe.sendmail(
			recipients=emails,
			subject=f"[{appointment.name}] {subject}: {appointment.title or appointment.service}",
			message=_("{0} on {1}. Open the CRM calendar for details.").format(
				frappe.utils.escape_html(appointment.title or appointment.service),
				start.strftime("%d/%m/%Y %H:%M"),
			),
			reference_doctype="CRM Appointment",
			reference_name=appointment.name,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Service booking: staff notification failed")


def on_appointment_status_change(doc) -> None:
	"""Called by the appointment controller: tell online clients when the practice
	approves or cancels their booking from the calendar."""
	if frappe.flags.in_service_booking_api or doc.get("source") != "Online":
		return
	previous = doc.get_doc_before_save()
	if not previous or previous.status == doc.status:
		return
	kind = {"Confirmed": "confirmed", "Cancelled": "cancelled"}.get(doc.status)
	if not kind or (kind == "confirmed" and previous.status != "Scheduled"):
		return
	for token in {r.access_token for r in doc.participants if r.access_token}:
		send_client_email(doc, token, kind)
