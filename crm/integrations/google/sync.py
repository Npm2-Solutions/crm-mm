# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The CRM's appointments, copied one way into each professional's Google Calendar.

Who: every user who connected Google from Settings → Google Calendar sees, in their
own Google account, the appointments they are on. Nothing comes back: an event
changed or deleted in Google is put back as the CRM has it.

Where: a calendar of its own in that Google account ("<brand> (CRM)"), made by the
first sync. The professional can colour it, hide it or share it, and their own
events never mix with the CRM's.

When: saving or deleting an appointment queues a push for the people on it, after
the transaction commits. Connecting Google queues a full sync, and every hour each
calendar is reconciled with the CRM, which catches what a failed push, a worker
restart or an edit made in Google left behind.

Why not the framework's own sync (``Event`` ↔ ``Google Calendar``): it sends the
Event's participants, the clients, as Google attendees with ``sendUpdates="all"``
(an invitation e-mail from Google for every appointment), and it reads Google back
into the CRM. Neither is wanted here.

The pure half (event shape, who gets a copy, the reconcile, the REST client) is in
``calendar_mirror``; this module is the Frappe side: accounts, tokens, jobs.
"""

from __future__ import annotations

import datetime
from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import cint, get_fullname, get_url, now_datetime
from frappe.utils.password import get_decrypted_password

from crm.integrations.google import calendar_mirror as M
from crm.scheduling.availability import ACTIVE_STATUSES
from crm.scheduling.timeutils import UTC, from_system_naive, scheduling_tz, to_system_naive

#: the stretch of time a full sync makes identical to the CRM. Older events stay in
#: Google as they are; later ones are still copied, one by one, when they are saved.
DAYS_BACK = 14
DAYS_AHEAD = 180

FIELDS = (
	"name",
	"title",
	"service",
	"status",
	"starts_on",
	"ends_on",
	"location",
	"notes",
	"customer_notes",
	"owner",
)


def is_ready() -> bool:
	"""The copy remembers each user's Google calendar in the CRM's fields on the
	framework's ``Google Calendar``. Until a migrate adds them, it stays off: without
	them every sync would make a new calendar."""
	return frappe.get_meta("Google Calendar").has_field("crm_calendar_id")


def account_of(user: str) -> str | None:
	"""The user's ``Google Calendar`` record, while it is switched on for the copy."""
	return frappe.db.get_value("Google Calendar", {"user": user, "enable": 1, "push_to_google_calendar": 1})


def calendar_title() -> str:
	brand = (frappe.db.get_single_value("FCRM Settings", "brand_name") or "").strip()
	return f"{brand} (CRM)" if brand and brand.upper() != "CRM" else "CRM"


# --------------------------------------------------------------------------
# when an appointment changes
# --------------------------------------------------------------------------


def on_appointment_change(doc, method=None):
	"""Queue a push for everybody who has, or just lost, a copy of this appointment."""
	if frappe.flags.in_import or frappe.flags.in_migrate or frappe.flags.in_install:
		# the hourly reconcile brings a bulk load across in one pass
		return
	users = set(M.mirror_users(_staff(doc), doc.owner))
	previous = doc.get_doc_before_save() if method == "on_update" else None
	if previous:
		users.update(M.mirror_users(_staff(previous), previous.owner))
	if not users or not is_ready():
		return
	connected = frappe.get_all(
		"Google Calendar",
		filters={"user": ["in", sorted(users)], "enable": 1, "push_to_google_calendar": 1},
		pluck="user",
	)
	if connected:
		frappe.enqueue(
			"crm.integrations.google.sync.push_appointment",
			queue="short",
			enqueue_after_commit=True,
			appointment=doc.name,
			users=sorted(connected),
		)


def _staff(doc) -> list[dict]:
	return [{"user": row.user, "status": row.status} for row in doc.get("staff") or []]


def push_appointment(appointment: str, users: list[str]) -> None:
	"""Bring these users' copies of one appointment in line with the CRM: written while
	it stands and they are on it, removed once it is cancelled, deleted or not theirs."""
	if not is_ready():
		return
	rows = _load([appointment])
	row = rows[0] if rows else None
	context = _context()
	for user in users:
		account = account_of(user)
		if not account:
			continue
		calendar_id = frappe.db.get_value("Google Calendar", account, "crm_calendar_id")
		if not calendar_id:
			# the first sync makes the calendar and copies this appointment with the rest
			queue_sync(user)
			continue
		client = _client(account)
		try:
			if (
				row
				and row["status"] in ACTIVE_STATUSES
				and user in M.mirror_users(row["staff"], row["owner"])
			):
				client.save(calendar_id, appointment, _event(row, user, context))
			else:
				client.remove(calendar_id, appointment)
		except M.CalendarMissing:
			# deleted in Google: the next sync makes a new one and fills it
			frappe.db.set_value("Google Calendar", account, "crm_calendar_id", None, update_modified=False)
			queue_sync(user)
			continue
		except M.GoogleError as exc:
			_failed(account, exc)
			continue
		_record(account)


# --------------------------------------------------------------------------
# a full sync
# --------------------------------------------------------------------------


def queue_sync(user: str) -> None:
	"""One full sync per user at a time: a second request while one is queued or
	running is dropped, the running one already brings everything."""
	frappe.enqueue(
		"crm.integrations.google.sync.sync_user",
		queue="long",
		timeout=3600,
		job_id=f"crm-google-calendar-sync::{user}",
		deduplicate=True,
		user=user,
	)


def sync_all() -> None:
	"""Hourly: every connected calendar is reconciled with the CRM."""
	if not is_ready():
		return
	for user in frappe.get_all(
		"Google Calendar", filters={"enable": 1, "push_to_google_calendar": 1}, pluck="user"
	):
		queue_sync(user)


def sync_user(user: str) -> dict | None:
	"""Make the user's CRM calendar in Google hold exactly their appointments, over the
	window. Returns what was done, or None when there was nothing to sync with."""
	if not is_ready():
		return None
	account = account_of(user)
	if not account:
		return None
	now = datetime.datetime.now(UTC)
	start = now - datetime.timedelta(days=DAYS_BACK)
	end = now + datetime.timedelta(days=DAYS_AHEAD)
	context = _context()
	desired = {row["name"]: _event(row, user, context) for row in appointments_of(user, start, end)}
	client = _client(account)
	try:
		calendar_id = ensure_calendar(client, account)
		try:
			stats = M.reconcile(client, calendar_id, desired, start, end, now)
		except M.CalendarMissing:
			frappe.db.set_value("Google Calendar", account, "crm_calendar_id", None, update_modified=False)
			calendar_id = ensure_calendar(client, account)
			stats = M.reconcile(client, calendar_id, desired, start, end, now)
	except M.GoogleError as exc:
		_failed(account, exc)
		return None
	_record(account, events=stats["events"])
	return stats


def ensure_calendar(client: M.CalendarClient, account: str) -> str:
	"""The id of the CRM's calendar in the user's Google account, made when missing."""
	calendar_id = frappe.db.get_value("Google Calendar", account, "crm_calendar_id")
	if calendar_id and client.get_calendar(calendar_id) is not None:
		return calendar_id
	calendar_id = client.create_calendar(
		calendar_title(),
		str(scheduling_tz()),
		_("Appointments from the CRM. Change them in the CRM: edits made here are overwritten."),
	)
	frappe.db.set_value("Google Calendar", account, "crm_calendar_id", calendar_id, update_modified=False)
	if not frappe.flags.in_test:
		# a push running meanwhile has to find this calendar, not wait for the first copy to end
		frappe.db.commit()  # nosemgrep: frappe-manual-commit — background job, see above
	return calendar_id


def appointments_of(user: str, start: datetime.datetime, end: datetime.datetime) -> list[dict]:
	"""The user's appointments that stand and overlap the window, ready for ``event_body``."""
	low, high = to_system_naive(start), to_system_naive(end)
	appointment = frappe.qb.DocType("CRM Appointment")
	staff = frappe.qb.DocType("CRM Appointment Staff")
	on_it = (
		frappe.qb.from_(appointment)
		.join(staff)
		.on(staff.parent == appointment.name)
		.select(appointment.name)
		.distinct()
		.where(staff.parenttype == "CRM Appointment")
		.where(staff.user == user)
		.where(appointment.status.isin(ACTIVE_STATUSES))
		.where(appointment.starts_on < high)
		.where(appointment.ends_on > low)
	).run(pluck=True)
	# with nobody on it, an appointment is its author's: mirror_users decides below
	booked = frappe.get_all(
		"CRM Appointment",
		filters={
			"owner": user,
			"status": ["in", ACTIVE_STATUSES],
			"starts_on": ["<", high],
			"ends_on": [">", low],
		},
		pluck="name",
		limit_page_length=0,
	)
	rows = _load(sorted(set(on_it) | set(booked)))
	return [row for row in rows if user in M.mirror_users(row["staff"], row["owner"])]


# --------------------------------------------------------------------------
# shaping and plumbing
# --------------------------------------------------------------------------


def _load(names: list[str]) -> list[dict]:
	"""Appointments with their staff and participants, times as aware UTC datetimes."""
	if not names:
		return []
	rows = frappe.get_all(
		"CRM Appointment", filters={"name": ["in", names]}, fields=list(FIELDS), limit_page_length=0
	)
	by_name = {}
	for row in rows:
		row["starts_on"] = from_system_naive(row["starts_on"])
		row["ends_on"] = from_system_naive(row["ends_on"])
		row["staff"], row["participants"] = [], []
		by_name[row["name"]] = row
	for child, key, fields in (
		("CRM Appointment Staff", "staff", ["user", "status"]),
		("CRM Appointment Participant", "participants", ["participant_name", "phone", "email", "status"]),
	):
		for entry in frappe.get_all(
			child,
			filters={"parent": ["in", list(by_name)], "parenttype": "CRM Appointment"},
			fields=["parent", *fields],
			order_by="idx asc",
			limit_page_length=0,
		):
			by_name[entry.pop("parent")][key].append(entry)
	return rows


def _context() -> dict:
	"""What every event of one run shares."""
	return {
		"timezone": str(scheduling_tz()),
		"source": calendar_title(),
		"labels": {"with": _("With"), "client_notes": _("Client notes")},
	}


def _event(row: dict, user: str, context: dict) -> dict:
	names = {entry["user"]: get_fullname(entry["user"]) for entry in row["staff"] if entry.get("user")}
	return M.event_body(
		row,
		user=user,
		timezone=context["timezone"],
		link=get_url(f"/crm/calendar?appointment={quote(row['name'])}"),
		source=context["source"],
		names=names,
		labels=context["labels"],
	)


def _client(account: str) -> M.CalendarClient:
	return M.CalendarClient(lambda refresh=False: access_token(account, refresh))


def _token_key(account: str) -> str:
	return f"crm_google_access_token|{account}"


def access_token(account: str, refresh: bool = False) -> str:
	"""A short-lived access token from the stored refresh token, kept until it expires."""
	if not refresh:
		cached = frappe.cache.get_value(_token_key(account))
		if cached:
			return cached
	refresh_token = get_decrypted_password("Google Calendar", account, "refresh_token", raise_exception=False)
	if not refresh_token:
		raise M.NotConnected(_("Google Calendar is not connected"))

	from crm.integrations.google.oauth import TOKEN_URL, client_id, client_secret

	status, data = M.http(
		"POST",
		TOKEN_URL,
		data={
			"client_id": client_id(),
			"client_secret": client_secret(),
			"refresh_token": refresh_token,
			"grant_type": "refresh_token",
		},
	)
	token = data.get("access_token") if status == 200 else None
	if token:
		lifetime = max(60, cint(data.get("expires_in") or 3600) - 300)
		frappe.cache.set_value(_token_key(account), token, expires_in_sec=lifetime)
		return token
	if data.get("error") == "invalid_grant":
		# revoked in Google, expired (a project still in Testing), or the password changed
		raise M.NotConnected(M.error_message(data, status), status, "invalid_grant")
	raise M.GoogleError(M.error_message(data, status), status, M.error_reason(data))


def forget_token(account: str) -> None:
	frappe.cache.delete_value(_token_key(account))


def _failed(account: str, exc: M.GoogleError) -> None:
	if isinstance(exc, M.NotConnected):
		# every save would try again and fail the same way: the copy stops until the
		# user connects again, which switches it back on
		frappe.db.set_value("Google Calendar", account, "push_to_google_calendar", 0, update_modified=False)
		forget_token(account)
		_record(
			account,
			error=_("Google no longer accepts this connection, connect the calendar again: {0}").format(exc),
		)
		return
	_record(account, error=str(exc))


def _record(account: str, error: str | None = None, events: int | None = None) -> None:
	"""How the last sync went, for the settings screen. An error is logged once, when it
	first shows up, not at every hourly pass."""
	values = {"crm_sync_error": error[:1000] if error else None}
	if not error:
		values["crm_last_sync"] = now_datetime()
	if events is not None:
		values["crm_synced_events"] = events
	if error and error[:1000] != frappe.db.get_value("Google Calendar", account, "crm_sync_error"):
		frappe.log_error(title="Google Calendar sync", message=f"{account}: {error}")
	frappe.db.set_value("Google Calendar", account, values, update_modified=False)
