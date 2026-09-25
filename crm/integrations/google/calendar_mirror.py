# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The CRM's appointments, copied one way into each professional's Google Calendar.

The copy only goes out. Google is where the professional *looks*; the CRM stays
the one place where an appointment is made, moved or cancelled. An event edited or
deleted in Google is put back the next time the CRM writes it.

Everything here is pure (no Frappe, no database), so the rules are tested without
a site and without Google:

* who gets a copy of an appointment;
* what the copy looks like, and the fingerprint that tells whether it changed;
* which events a reconcile writes or removes, the upcoming ones first;
* a small REST client that is given its transport and its token.

Event ids are chosen by the CRM (Google allows it): the same appointment always
lands on the same event, so a retry or two jobs racing can never make a duplicate,
and no table has to remember which event belongs to which appointment.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import time
from collections.abc import Callable, Iterable
from urllib.parse import quote

API = "https://www.googleapis.com/calendar/v3"
TIMEOUT = 30

#: private extended properties the CRM stamps on its events. Only events carrying
#: MARKER are ever listed, rewritten or removed: anything the professional adds to
#: the calendar by hand is left alone.
MARKER = "crm_mirror"
APPOINTMENT_KEY = "crm_appointment"
HASH_KEY = "crm_hash"

#: bump when the shape of the event changes: every event is then written again once
FORMAT_VERSION = 1

UTC = datetime.timezone.utc


class GoogleError(Exception):
	"""Google said no. ``status`` is the HTTP status, 0 when Google was not reached."""

	def __init__(self, message: str, status: int = 0, reason: str = ""):
		super().__init__(message)
		self.status = status
		self.reason = reason


class NotConnected(GoogleError):
	"""The authorisation is gone: revoked by the user, expired, or never finished."""


class CalendarMissing(GoogleError):
	"""The CRM's calendar is no longer in the user's Google account."""


# --------------------------------------------------------------------------
# what goes to Google
# --------------------------------------------------------------------------


def event_id(appointment: str) -> str:
	"""Google lets the writer pick an event id: 5 to 1024 characters of base32hex
	(0-9 and a-v). Hex digits are base32hex too, so a digest of the name is one."""
	return "crm" + hashlib.sha256(appointment.encode()).hexdigest()


def mirror_users(staff: Iterable[dict], owner: str | None) -> list[str]:
	"""Who gets a copy: every professional on the appointment who has not declined it.

	An appointment with nobody on it belongs to whoever booked it, as its calendar
	``Event`` already does.
	"""
	staff = list(staff or [])
	if any(row.get("user") for row in staff):
		users = [row["user"] for row in staff if row.get("user") and row.get("status") != "Declined"]
	else:
		users = [owner] if owner and owner != "Guest" else []
	return list(dict.fromkeys(users))


def iso_utc(moment: datetime.datetime) -> str:
	return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def body_hash(body: dict) -> str:
	"""A fingerprint of everything the CRM writes, its own stamp excluded."""
	private = dict((body.get("extendedProperties") or {}).get("private") or {})
	private.pop(HASH_KEY, None)
	content = {**body, "extendedProperties": {"private": private}, "_v": FORMAT_VERSION}
	canonical = json.dumps(content, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
	return hashlib.sha256(canonical.encode()).hexdigest()[:20]


def describe(
	appointment: dict,
	user: str,
	names: dict[str, str] | None = None,
	labels: dict[str, str] | None = None,
	link: str = "",
) -> str:
	"""The event's notes: the clients and how to reach them, colleagues, notes, the link.

	Written for a phone screen: no field names where the value speaks for itself.
	"""
	names = names or {}
	labels = {"with": "With", "client_notes": "Client notes", **(labels or {})}
	blocks = []
	clients = []
	for person in appointment.get("participants") or []:
		if person.get("status") == "Cancelled":
			continue
		parts = [person.get(key) for key in ("participant_name", "phone", "email")]
		line = " · ".join(str(p).strip() for p in parts if p and str(p).strip())
		if line:
			clients.append(line)
	colleagues = [
		names.get(u) or u
		for u in mirror_users(appointment.get("staff") or [], appointment.get("owner"))
		if u != user
	]
	if colleagues:
		clients.append(f"{labels['with']}: {', '.join(colleagues)}")
	if clients:
		blocks.append("\n".join(clients))
	if (appointment.get("notes") or "").strip():
		blocks.append(appointment["notes"].strip())
	if (appointment.get("customer_notes") or "").strip():
		blocks.append(f"{labels['client_notes']}: {appointment['customer_notes'].strip()}")
	if link:
		blocks.append(link)
	return "\n\n".join(blocks)


def event_body(
	appointment: dict,
	*,
	user: str,
	timezone: str,
	link: str = "",
	source: str = "CRM",
	names: dict[str, str] | None = None,
	labels: dict[str, str] | None = None,
) -> dict:
	"""The Google event for ``user``'s copy of ``appointment``.

	``appointment`` carries aware ``starts_on``/``ends_on``. No attendees: an attendee
	is a person Google would e-mail, and the clients must hear nothing from here.
	"""
	body = {
		"summary": appointment.get("title") or appointment.get("service") or appointment["name"],
		"description": describe(appointment, user, names, labels, link),
		"location": appointment.get("location") or "",
		"start": {"dateTime": iso_utc(appointment["starts_on"]), "timeZone": timezone},
		"end": {"dateTime": iso_utc(appointment["ends_on"]), "timeZone": timezone},
		"status": "confirmed",
		"transparency": "opaque",
		"extendedProperties": {"private": {MARKER: "1", APPOINTMENT_KEY: appointment["name"]}},
	}
	if link.startswith(("https://", "http://")):
		body["source"] = {"title": source, "url": link}
	body["extendedProperties"]["private"][HASH_KEY] = body_hash(body)
	return body


# --------------------------------------------------------------------------
# what a reconcile does
# --------------------------------------------------------------------------


def stamp(body: dict) -> str:
	"""The fingerprint an event body was stamped with by ``event_body``."""
	private = (body.get("extendedProperties") or {}).get("private") or {}
	return private.get(HASH_KEY) or body_hash(body)


def _starts(body: dict) -> datetime.datetime:
	return datetime.datetime.fromisoformat(body["start"]["dateTime"].replace("Z", "+00:00"))


def plan(
	desired: dict[str, dict], found: dict[str, dict], now: datetime.datetime
) -> tuple[list[tuple[str, str | None]], list[str]]:
	"""What to write and what to remove to make Google match the CRM.

	``desired`` maps an appointment to the body the CRM wants; ``found`` maps the ids
	of the CRM's events in Google to the appointment and fingerprint they carry.

	Events are matched to appointments by the appointment they carry, not by their
	id: an event normally has the id the CRM chose, but not when Google would not
	take that id back (see ``CalendarClient.save``). One event per appointment is
	kept, the one with the chosen id first; a second one is removed.

	Returns ``[(appointment, id of its event or None)]`` to write, unchanged ones
	left out, upcoming first and nearest first, then the past, latest first (if
	Google stops a long first sync halfway, what is missing is what matters least);
	and the ids to remove.
	"""
	owned: dict[str, list[str]] = {}
	for eid, info in sorted(found.items()):
		owned.setdefault(info.get("appointment") or "", []).append(eid)
	to_write, to_remove = [], []
	for appointment, body in desired.items():
		ids = owned.pop(appointment, [])
		chosen = event_id(appointment)
		keep = chosen if chosen in ids else (ids[0] if ids else None)
		to_remove += [eid for eid in ids if eid != keep]
		if keep is None or found[keep].get("hash") != stamp(body):
			to_write.append((appointment, keep))
	for ids in owned.values():
		to_remove += ids
	to_write.sort(key=lambda item: _order(_starts(desired[item[0]]), now))
	return to_write, sorted(to_remove)


def _order(start: datetime.datetime, now: datetime.datetime) -> tuple[int, float]:
	distance = (start - now).total_seconds()
	return (0, distance) if distance >= 0 else (1, -distance)


def reconcile(
	client: CalendarClient,
	calendar_id: str,
	desired: dict[str, dict],
	time_min: datetime.datetime,
	time_max: datetime.datetime,
	now: datetime.datetime,
) -> dict:
	"""Make the window of the calendar hold exactly ``desired`` (appointment → body).
	Removals first: an appointment still showing after it was cancelled misleads
	more than one that shows up late."""
	found = client.list_mirrored(calendar_id, time_min, time_max)
	to_write, to_remove = plan(desired, found, now)
	for eid in to_remove:
		client.delete(calendar_id, eid)
	for appointment, eid in to_write:
		client.save(calendar_id, appointment, desired[appointment], eid)
	return {"events": len(desired), "written": len(to_write), "removed": len(to_remove)}


# --------------------------------------------------------------------------
# the REST client
# --------------------------------------------------------------------------


def http(method: str, url: str, **kwargs) -> tuple[int, dict]:
	"""One HTTP call: (status, JSON body). Status 0 when the network failed."""
	import requests

	try:
		response = requests.request(method, url, timeout=TIMEOUT, **kwargs)
	except requests.RequestException as exc:
		return 0, {"error": {"message": exc.__class__.__name__}}
	try:
		data = response.json() if response.content else {}
	except ValueError:
		data = {}
	return response.status_code, data if isinstance(data, dict) else {}


def error_reason(data: dict) -> str:
	error = data.get("error")
	if isinstance(error, dict):
		errors = error.get("errors") or [{}]
		return errors[0].get("reason") or error.get("status") or ""
	return str(error or "")


def error_message(data: dict, status: int) -> str:
	error = data.get("error")
	detail = error.get("message") if isinstance(error, dict) else data.get("error_description") or error
	if not status:
		return f"Google could not be reached ({detail})" if detail else "Google could not be reached"
	return f"Google {status}: {detail}" if detail else f"Google {status}"


def retryable(status: int, data: dict) -> bool:
	if status in (0, 429, 500, 502, 503, 504):
		return True
	return status == 403 and error_reason(data) in ("rateLimitExceeded", "userRateLimitExceeded")


class CalendarClient:
	"""Just the calls the mirror makes, on Google Calendar API v3.

	``token(refresh)`` returns an access token; with ``refresh=True`` a fresh one,
	for when Google turned the current one down early.
	"""

	def __init__(
		self,
		token: Callable[..., str],
		transport: Callable[..., tuple[int, dict]] | None = None,
		sleep: Callable[[float], None] = time.sleep,
		retries: int = 3,
	):
		self.token = token
		self.transport = transport or http
		self.sleep = sleep
		self.retries = retries

	def call(self, method, path, *, params=None, body=None, ok=(200,), missing=()) -> dict | None:
		"""The JSON Google answered, or ``None`` for a status in ``missing``."""
		fresh_token = False
		attempt = 0
		while True:
			status, data = self.transport(
				method,
				API + path,
				params=params,
				json=body,
				headers={"Authorization": f"Bearer {self.token(refresh=fresh_token)}"},
			)
			if status in ok:
				return data or {}
			if status in missing:
				return None
			if status == 401 and not fresh_token:
				fresh_token = True
				continue
			if retryable(status, data) and attempt < self.retries:
				self.sleep(2**attempt)
				attempt += 1
				continue
			raise GoogleError(error_message(data, status), status, error_reason(data))

	def create_calendar(self, summary: str, timezone: str, description: str = "") -> str:
		created = self.call(
			"POST", "/calendars", body={"summary": summary, "description": description, "timeZone": timezone}
		)
		return created["id"]

	def get_calendar(self, calendar_id: str) -> dict | None:
		return self.call("GET", f"/calendars/{quote(calendar_id, safe='')}", missing=(404,))

	def _events(self, calendar_id: str) -> str:
		return f"/calendars/{quote(calendar_id, safe='')}/events"

	def _list(self, calendar_id: str, params: dict) -> dict[str, dict]:
		"""Event id → the appointment and fingerprint the CRM stamped on it, all pages."""
		found: dict[str, dict] = {}
		page = None
		while True:
			query = {
				**params,
				"maxResults": 2500,
				"fields": "items(id,extendedProperties/private),nextPageToken",
			}
			if page:
				query["pageToken"] = page
			data = self.call("GET", self._events(calendar_id), params=query, missing=(404,))
			if data is None:
				raise CalendarMissing("The CRM calendar is no longer in this Google account", 404)
			for item in data.get("items") or []:
				private = (item.get("extendedProperties") or {}).get("private") or {}
				found[item["id"]] = {
					"appointment": private.get(APPOINTMENT_KEY, ""),
					"hash": private.get(HASH_KEY, ""),
				}
			page = data.get("nextPageToken")
			if not page:
				return found

	def list_mirrored(
		self, calendar_id: str, time_min: datetime.datetime, time_max: datetime.datetime
	) -> dict[str, dict]:
		"""The CRM's events that overlap the window: id → appointment and fingerprint."""
		return self._list(
			calendar_id,
			{
				"timeMin": iso_utc(time_min),
				"timeMax": iso_utc(time_max),
				"privateExtendedProperty": f"{MARKER}=1",
			},
		)

	def find(self, calendar_id: str, appointment: str) -> list[str]:
		"""The ids of the live events of one appointment, whenever they are."""
		constraints = [f"{MARKER}=1", f"{APPOINTMENT_KEY}={appointment}"]
		return sorted(self._list(calendar_id, {"privateExtendedProperty": constraints}))

	def save(self, calendar_id: str, appointment: str, body: dict, eid: str | None = None) -> str:
		"""Write the appointment's event, whether or not Google has it yet. Returns its id.

		The event gets the id the CRM chose (``event_id``), so a retry or two jobs racing
		cannot make two. An update with ``status: confirmed`` also brings an event back
		from Google's bin. Should Google keep that id and refuse to update it, the event
		lives on under an id of Google's, found again by the appointment it carries.
		"""
		events = self._events(calendar_id)
		params = {"sendUpdates": "none"}
		chosen = event_id(appointment)
		for candidate in dict.fromkeys(i for i in (eid, chosen) if i):
			written = self.call("PUT", f"{events}/{candidate}", params=params, body=body, missing=(404, 410))
			if written is not None:
				return candidate
		try:
			created = self.call("POST", events, params=params, body={"id": chosen, **body}, missing=(404,))
		except GoogleError as exc:
			if exc.status != 409:
				raise
			# the id is taken: written by another job meanwhile, or sitting in Google's bin
			try:
				self.call("PUT", f"{events}/{chosen}", params=params, body=body)
				return chosen
			except GoogleError as again:
				if again.status not in (403, 404, 410):
					raise
			for other in self.find(calendar_id, appointment):
				written = self.call("PUT", f"{events}/{other}", params=params, body=body, missing=(404, 410))
				if written is not None:
					return other
			created = self.call("POST", events, params=params, body=body, missing=(404,))
		if created is None:
			raise CalendarMissing("The CRM calendar is no longer in this Google account", 404)
		return created.get("id") or chosen

	def delete(self, calendar_id: str, eid: str) -> bool:
		"""False when there was nothing to delete."""
		deleted = self.call(
			"DELETE",
			f"{self._events(calendar_id)}/{eid}",
			params={"sendUpdates": "none"},
			ok=(200, 204),
			missing=(404, 410),
		)
		return deleted is not None

	def remove(self, calendar_id: str, appointment: str) -> int:
		"""Delete every event of one appointment: the one under the chosen id, and any
		it had to live under instead. Returns how many there were."""
		removed = int(self.delete(calendar_id, event_id(appointment)))
		for other in self.find(calendar_id, appointment):
			removed += int(self.delete(calendar_id, other))
		return removed
