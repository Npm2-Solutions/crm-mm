# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""External bookings ⇄ CRM appointments.

Inbound: every ``ExternalBooking`` (from a poll, a webhook or an email) is
*upserted* on ``(booking_connection, external_id)``: created the first time,
moved/re-statused afterwards, cancelled when the platform cancels it. The
platform is the source of truth for its own bookings, so an imported booking is
never refused for a clash — the clash is written on the appointment
(``conflict_note``) for the receptionist to see and solve.

Outbound: when the CRM books (or frees) a professional who also works on a
platform with the *Block time* option, the same hours are blocked (or freed)
there; cancelling an imported appointment in the CRM cancels it on the platform
when *Cancel on the platform* is on. Both run in the background, after commit,
so a slow platform never slows the calendar down.
"""

from __future__ import annotations

import datetime

import frappe
from frappe import _
from frappe.utils import cint, now_datetime

from crm.booking_platforms import get_provider
from crm.booking_platforms.base import (
	APPOINTMENT_STATUS,
	STATUS_CANCELLED,
	STATUS_CONFIRMED,
	ExternalBooking,
	NotSupported,
	PlatformError,
)
from crm.scheduling.timeutils import UTC, from_system_naive, to_system_naive

ACTIVE = ("Scheduled", "Confirmed")


# --------------------------------------------------------------------------
# mapping
# --------------------------------------------------------------------------


def _mapped(conn, map_type: str, ref: str, name: str) -> str | None:
	"""The CRM record a platform id (or, failing that, its display name) maps to."""
	field = {"Service": "service", "Staff": "staff", "Resource": "resource"}[map_type]
	ref, name = (ref or "").strip(), (name or "").strip().lower()
	for row in conn.mappings:
		if row.map_type != map_type:
			continue
		if ref and row.external_id == ref:
			return row.get(field)
	for row in conn.mappings:
		if row.map_type == map_type and name and (row.external_name or "").strip().lower() == name:
			return row.get(field)
	return None


def resolve_service(conn, booking: ExternalBooking) -> str | None:
	service = _mapped(conn, "Service", booking.service_ref, booking.service_name)
	if not service and booking.service_name:
		# a platform service called exactly like a CRM service needs no mapping row
		service = frappe.db.get_value(
			"CRM Service", {"service_name": booking.service_name.strip(), "enabled": 1}
		)
	return service or conn.default_service


def resolve_staff(conn, booking: ExternalBooking, service: str | None) -> str | None:
	staff = _mapped(conn, "Staff", booking.staff_ref, booking.staff_name)
	if not staff and booking.staff_ref and frappe.db.exists("User", booking.staff_ref):
		staff = booking.staff_ref  # Cal.com/Calendly hosts come as e-mail addresses
	if not staff and booking.staff_name:
		staff = frappe.db.get_value("User", {"full_name": booking.staff_name.strip(), "enabled": 1})
	if not staff and conn.default_staff:
		staff = conn.default_staff
	if not staff and service:
		rows = frappe.get_cached_doc("CRM Service", service).staff
		staff = rows[0].user if rows else None
	return staff


# --------------------------------------------------------------------------
# upsert
# --------------------------------------------------------------------------


def find_existing(conn, booking: ExternalBooking) -> str | None:
	name = frappe.db.get_value(
		"CRM Appointment", {"booking_connection": conn.name, "external_id": booking.external_id}
	)
	if name or not booking.raw.get("match_by_customer"):
		return name
	if booking.status != STATUS_CANCELLED and not booking.raw.get("moved"):
		return None  # a new booking by a returning client is a new appointment
	# an email without a booking reference: find the client's upcoming appointment
	# from this connection (the one being cancelled or moved)
	participant = frappe.qb.DocType("CRM Appointment Participant")
	appointment = frappe.qb.DocType("CRM Appointment")
	query = (
		frappe.qb.from_(appointment)
		.join(participant)
		.on(participant.parent == appointment.name)
		.select(appointment.name)
		.where(appointment.booking_connection == conn.name)
		.where(appointment.status.isin(ACTIVE))
		.where(appointment.ends_on >= now_datetime())
		.orderby(appointment.starts_on)
		.limit(1)
	)
	if booking.email:
		query = query.where(participant.email == booking.email)
	elif booking.phone:
		query = query.where(participant.phone.like(f"%{booking.phone[-8:]}"))
	elif booking.customer_name:
		query = query.where(participant.participant_name == booking.customer_name)
	else:
		return None
	rows = query.run(pluck=True)
	return rows[0] if rows else None


def upsert(conn, booking: ExternalBooking) -> tuple[str, str | None]:
	"""Create, update or cancel the appointment behind one external booking.

	Returns ``(action, appointment)`` with action in created, updated, cancelled,
	unchanged, skipped.
	"""
	existing = find_existing(conn, booking)
	target_status = APPOINTMENT_STATUS[booking.status]
	if booking.status == STATUS_CONFIRMED:
		target_status = conn.imported_status or "Confirmed"

	frappe.flags.in_platform_sync = True
	try:
		if existing:
			return _update(conn, existing, booking, target_status)
		if booking.status == STATUS_CANCELLED:
			return "skipped", None
		return _create(conn, booking, target_status)
	finally:
		frappe.flags.in_platform_sync = False


def _participant(conn, booking: ExternalBooking) -> dict | None:
	if not (booking.customer_name or booking.email or booking.phone):
		return None
	lead = None
	if cint(conn.create_leads) and (booking.email or booking.phone):
		from crm.api.booking import find_or_create_person

		lead = find_or_create_person(
			booking.customer_name,
			booking.email,
			booking.phone,
			source=conn.platform,
			medium="booking_platform",
			source_dimension=get_provider(conn).key,
		)
	return {
		"party_type": "CRM Lead",
		"party": lead,
		"participant_name": booking.customer_name or booking.email or booking.phone,
		"email": booking.email,
		"phone": booking.phone,
		"status": "Booked",
		"amount": booking.price or 0,
	}


def _create(conn, booking: ExternalBooking, status: str):
	service = resolve_service(conn, booking)
	if not service:
		raise PlatformError(
			_("{0}: service '{1}' is not mapped and the connection has no default service").format(
				conn.name, booking.service_name or booking.service_ref or "?"
			)
		)
	staff = resolve_staff(conn, booking, service)
	resource = _mapped(conn, "Resource", booking.resource_ref, "")
	participant = _participant(conn, booking)
	doc = frappe.get_doc(
		{
			"doctype": "CRM Appointment",
			"service": service,
			"status": status,
			"starts_on": to_system_naive(booking.start),
			"ends_on": to_system_naive(booking.end),
			"staff": [{"user": staff, "required": 1}] if staff else [],
			"resources": [{"resource": resource, "quantity": 1}] if resource else [],
			"participants": [participant] if participant else [],
			"location": booking.location or None,
			"source": "External",
			"booking_connection": conn.name,
			"external_platform": conn.platform,
			"external_id": booking.external_id,
			"external_url": (booking.url or "")[:140] or None,
			"customer_notes": booking.notes or None,
		}
	)
	doc.flags.external_booking = True
	doc.insert(ignore_permissions=True)
	if booking.price:
		doc.db_set("total_amount", booking.price, update_modified=False)
	frappe.db.set_value(
		"CRM Booking Connection",
		conn.name,
		"imported_count",
		cint(frappe.db.get_value("CRM Booking Connection", conn.name, "imported_count")) + 1,
		update_modified=False,
	)
	return "created", doc.name


def _update(conn, name: str, booking: ExternalBooking, status: str):
	doc = frappe.get_doc("CRM Appointment", name)
	doc.flags.external_booking = True
	if booking.status == STATUS_CANCELLED:
		if doc.status == "Cancelled":
			return "unchanged", name
		doc.status = "Cancelled"
		doc.cancellation_reason = _("Cancelled on {0}").format(conn.platform)
		for row in doc.participants:
			row.status = "Cancelled"
		doc.save(ignore_permissions=True)
		return "cancelled", name

	changed = False
	start, end = to_system_naive(booking.start), to_system_naive(booking.end)
	if from_system_naive(doc.starts_on) != booking.start or from_system_naive(doc.ends_on) != booking.end:
		doc.starts_on, doc.ends_on = start, end
		changed = True
	# the CRM may have completed or no-showed it; a platform "confirmed" does not undo that
	if doc.status in (*ACTIVE, "Cancelled") and doc.status != status:
		doc.status = status
		changed = True
	if booking.notes and booking.notes != doc.customer_notes:
		doc.customer_notes = booking.notes
		changed = True
	if not changed:
		return "unchanged", name
	doc.save(ignore_permissions=True)
	return "updated", name


def apply(conn, bookings: list[ExternalBooking]) -> dict:
	"""Upsert a batch; one bad booking never stops the others."""
	counts = {"created": 0, "updated": 0, "cancelled": 0, "unchanged": 0, "skipped": 0, "failed": 0}
	errors = []
	for booking in bookings:
		try:
			frappe.db.savepoint("platform_booking")
			action, _name = upsert(conn, booking)
			counts[action] += 1
		except Exception as exc:
			frappe.db.rollback(save_point="platform_booking")
			counts["failed"] += 1
			errors.append(f"{booking.external_id}: {frappe.utils.strip_html(str(exc))[:200]}")
	if errors:
		frappe.log_error("\n".join(errors[:50]), f"Booking platform {conn.name}: some bookings failed")
	counts["errors"] = errors[:5]
	return counts


# --------------------------------------------------------------------------
# polling
# --------------------------------------------------------------------------


def _mark(conn_name: str, **values):
	frappe.db.set_value("CRM Booking Connection", conn_name, values, update_modified=False)


def sync_connection(name: str) -> dict:
	conn = frappe.get_doc("CRM Booking Connection", name)
	provider = get_provider(conn)
	if not cint(conn.enabled) or not cint(conn.import_bookings):
		return {"skipped": True}
	if "pull" not in provider.capabilities:
		return {"skipped": True, "reason": "no pull"}
	missing = provider.missing_fields()
	if missing:
		_mark(name, status="Not configured", last_error=_("Missing: {0}").format(", ".join(missing)))
		return {"skipped": True, "missing": missing}

	now = datetime.datetime.now(UTC)
	since = now - datetime.timedelta(days=cint(conn.lookback_days) if conn.lookback_days is not None else 1)
	until = now + datetime.timedelta(days=cint(conn.sync_window_days) or 60)
	try:
		bookings = provider.fetch_bookings(since, until)
		if hasattr(provider, "pull_notifications"):
			try:
				bookings += provider.pull_notifications()
			except NotSupported:
				pass
	except Exception as exc:
		frappe.db.rollback()
		_mark(name, status="Error", last_error=str(exc)[:1000], last_sync=now_datetime())
		frappe.db.commit()
		frappe.log_error(frappe.get_traceback(), f"Booking platform {name}: sync failed")
		return {"error": str(exc)}

	counts = apply(conn, bookings)
	if getattr(provider, "authoritative_window", False):
		counts["cancelled"] += _cancel_missing(conn, bookings, since, until)
	_mark(name, status="Connected", last_error=None, last_sync=now_datetime())
	return counts


def _cancel_missing(conn, bookings, since, until) -> int:
	"""A feed that no longer lists a future booking means the platform deleted it."""
	seen = {b.external_id for b in bookings}
	stale = frappe.get_all(
		"CRM Appointment",
		filters={
			"booking_connection": conn.name,
			"status": ["in", ACTIVE],
			"starts_on": [">=", to_system_naive(max(since, datetime.datetime.now(UTC)))],
			"ends_on": ["<=", to_system_naive(until)],
		},
		fields=["name", "external_id", "starts_on", "ends_on"],
	)
	cancelled = 0
	for row in stale:
		if row.external_id in seen:
			continue
		ghost = ExternalBooking(
			external_id=row.external_id,
			start=from_system_naive(row.starts_on),
			end=from_system_naive(row.ends_on),
			status=STATUS_CANCELLED,
		)
		action, _name = upsert(conn, ghost)
		cancelled += action == "cancelled"
	return cancelled


def sync_all():
	"""Scheduler: enqueue a poll per enabled connection that can be polled."""
	for name in frappe.get_all(
		"CRM Booking Connection", filters={"enabled": 1, "import_bookings": 1}, pluck="name"
	):
		frappe.enqueue(
			"crm.booking_platforms.sync.sync_connection",
			name=name,
			queue="long",
			job_id=f"crm_booking_sync::{name}",
			deduplicate=True,
		)


# --------------------------------------------------------------------------
# webhooks and emails
# --------------------------------------------------------------------------


def handle_webhook(token: str, headers: dict, body: bytes, url: str = "") -> dict:
	name = (
		frappe.db.get_value("CRM Booking Connection", {"webhook_token": token, "enabled": 1})
		if token
		else None
	)
	if not name:
		raise frappe.PermissionError
	conn = frappe.get_doc("CRM Booking Connection", name)
	bookings = get_provider(conn).parse_webhook(headers, body, url)
	counts = apply(conn, bookings) if cint(conn.import_bookings) else {"skipped": len(bookings)}
	_mark(name, last_webhook=now_datetime(), status="Connected")
	return counts


def on_communication(doc, method=None):
	"""``Communication`` after_insert: a received email on a notification mailbox."""
	if doc.get("sent_or_received") != "Received" or doc.get("communication_medium") != "Email":
		return
	if not doc.get("email_account"):
		return
	names = frappe.get_all(
		"CRM Booking Connection",
		filters={"enabled": 1, "import_bookings": 1, "inbound_email_account": doc.email_account},
		pluck="name",
	)
	for name in names:
		frappe.enqueue(
			"crm.booking_platforms.sync.import_email",
			connection=name,
			communication=doc.name,
			enqueue_after_commit=True,
		)


def import_email(connection: str, communication: str) -> dict:
	conn = frappe.get_doc("CRM Booking Connection", connection)
	provider = get_provider(conn)
	if not hasattr(provider, "parse_email"):
		return {"skipped": True}
	mail = frappe.db.get_value("Communication", communication, ["subject", "content", "sender"], as_dict=True)
	if not mail:
		return {"skipped": True}
	bookings = provider.parse_email(mail.subject or "", mail.content or "", mail.sender or "")
	counts = apply(conn, bookings)
	_mark(connection, last_webhook=now_datetime(), status="Connected")
	return counts


# --------------------------------------------------------------------------
# outbound: blocks and cancellations
# --------------------------------------------------------------------------


def on_appointment_change(doc, method=None):
	"""``CRM Appointment`` on_update / on_trash: queue the platform side effects."""
	if frappe.flags.in_platform_sync or frappe.flags.in_install or frappe.flags.in_migrate:
		return
	if not frappe.db.exists("CRM Booking Connection", {"enabled": 1}):
		return
	frappe.enqueue(
		"crm.booking_platforms.sync.push_appointment",
		appointment=doc.name,
		deleted=method == "on_trash",
		enqueue_after_commit=True,
	)


def push_appointment(appointment: str, deleted: bool = False):
	doc = (
		None
		if deleted
		else frappe.db.get_value(
			"CRM Appointment",
			appointment,
			[
				"name",
				"status",
				"starts_on",
				"ends_on",
				"booking_connection",
				"external_id",
				"service",
				"cancellation_reason",
			],
			as_dict=True,
		)
	)
	if doc and doc.booking_connection and doc.status == "Cancelled":
		_cancel_on_platform(doc)
	_sync_blocks(appointment, doc)


def _cancel_on_platform(doc):
	conn = frappe.get_doc("CRM Booking Connection", doc.booking_connection)
	if not cint(conn.push_cancellations) or not cint(conn.enabled):
		return
	reason = doc.cancellation_reason or ""
	if reason.startswith(_("Cancelled on {0}").format(conn.platform)):
		return  # it came from the platform: nothing to send back
	try:
		get_provider(conn).cancel_booking(doc.external_id, reason)
	except NotSupported:
		pass
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"Booking platform {conn.name}: cancel failed")


def _sync_blocks(appointment: str, doc):
	"""Keep one platform block per (connection, professional) in step with the appointment."""
	blocks = frappe.get_all(
		"CRM Booking Platform Block",
		filters={"appointment": appointment, "status": "Active"},
		fields=["name", "connection", "staff", "external_block_id", "starts_on", "ends_on"],
	)
	wanted: dict[tuple[str, str], str] = {}
	if doc and doc.status in ACTIVE:
		staff = frappe.get_all("CRM Appointment Staff", filters={"parent": appointment}, pluck="user")
		for conn_name in frappe.get_all(
			"CRM Booking Connection", filters={"enabled": 1, "push_blocks": 1}, pluck="name"
		):
			if conn_name == doc.booking_connection:
				continue  # the platform already knows its own booking
			conn = frappe.get_cached_doc("CRM Booking Connection", conn_name)
			for row in conn.mappings:
				if row.map_type == "Staff" and row.staff in staff:
					wanted[(conn_name, row.staff)] = row.external_id

	for block in blocks:
		key = (block.connection, block.staff)
		same_time = (
			doc and str(block.starts_on) == str(doc.starts_on) and str(block.ends_on) == str(doc.ends_on)
		)
		if key in wanted and same_time:
			wanted.pop(key)
			continue
		_remove_block(block)

	for (conn_name, user), ref in wanted.items():
		_add_block(conn_name, user, ref, appointment, doc)


def _add_block(conn_name, user, ref, appointment, doc):
	conn = frappe.get_doc("CRM Booking Connection", conn_name)
	provider = get_provider(conn)
	if "block" not in provider.capabilities:
		return
	row = frappe.get_doc(
		{
			"doctype": "CRM Booking Platform Block",
			"connection": conn_name,
			"appointment": appointment,
			"staff": user,
			"starts_on": doc.starts_on,
			"ends_on": doc.ends_on,
		}
	)
	try:
		row.external_block_id = provider.block_time(
			ref, from_system_naive(doc.starts_on), from_system_naive(doc.ends_on), _("Busy (CRM)")
		)
		row.status = "Active"
	except Exception as exc:
		row.status = "Failed"
		row.error = str(exc)[:500]
	row.insert(ignore_permissions=True)


def _remove_block(block):
	conn = frappe.get_doc("CRM Booking Connection", block.connection)
	ref = next((r.external_id for r in conn.mappings if r.map_type == "Staff" and r.staff == block.staff), "")
	try:
		if block.external_block_id:
			get_provider(conn).unblock_time(block.external_block_id, ref)
		frappe.db.set_value("CRM Booking Platform Block", block.name, "status", "Removed")
	except Exception as exc:
		frappe.db.set_value(
			"CRM Booking Platform Block", block.name, {"status": "Failed", "error": str(exc)[:500]}
		)
