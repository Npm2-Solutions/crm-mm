# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""General-purpose schedulers with a public API.

Each connector is small on purpose: authenticate, list bookings in a window,
turn a webhook into bookings, and — where the platform allows — cancel a
booking, block a professional's time and list services/staff for mapping.

The ``*_to_booking`` functions are pure (a platform JSON object in, an
``ExternalBooking`` out) and carry the whole platform-specific knowledge, so
they are what the tests exercise.
"""

from __future__ import annotations

import datetime
import time
from urllib.parse import parse_qs

from crm.booking_platforms.base import (
	STATUS_CANCELLED,
	STATUS_COMPLETED,
	STATUS_CONFIRMED,
	STATUS_NO_SHOW,
	STATUS_PENDING,
	UTC,
	BookingPlatform,
	CatalogItem,
	ExternalBooking,
	InvalidSignature,
	PlatformError,
	as_utc,
	header,
	hmac_b64,
	hmac_hex,
	join_name,
	load_json,
	local_to_utc,
	safe_equal,
)


def _uuid(uri: str) -> str:
	"""Calendly ids are URIs; the uuid is the last path segment."""
	return str(uri or "").rstrip("/").rsplit("/", 1)[-1]


def _items(data) -> list:
	"""Lists come bare, or wrapped as ``data``/``collection``/``value``/``results``."""
	if isinstance(data, list):
		return data
	if isinstance(data, dict):
		for key in ("data", "collection", "value", "results", "appointments", "items", "_items"):
			value = data.get(key)
			if isinstance(value, list):
				return value
			if isinstance(value, dict):
				nested = _items(value)
				if nested:
					return nested
	return []


def _scheduling_tz() -> str:
	try:
		from crm.scheduling.timeutils import scheduling_tz

		return str(scheduling_tz())
	except Exception:
		return "Europe/Rome"


# ==========================================================================
# Cal.com (API v2)
# ==========================================================================

CAL_STATUS = {
	"accepted": STATUS_CONFIRMED,
	"pending": STATUS_PENDING,
	"cancelled": STATUS_CANCELLED,
	"rejected": STATUS_CANCELLED,
}
CAL_TRIGGER_STATUS = {
	"BOOKING_CANCELLED": STATUS_CANCELLED,
	"BOOKING_REJECTED": STATUS_CANCELLED,
	"BOOKING_REQUESTED": STATUS_PENDING,
	"BOOKING_NO_SHOW_UPDATED": STATUS_NO_SHOW,
}


def cal_to_booking(item: dict, trigger: str = "") -> ExternalBooking:
	attendee = (item.get("attendees") or [{}])[0] or {}
	host = (item.get("hosts") or [None])[0] or item.get("organizer") or {}
	event_type = item.get("eventType") or {}
	status = CAL_TRIGGER_STATUS.get(trigger) or CAL_STATUS.get(
		str(item.get("status") or "").lower(), STATUS_CONFIRMED
	)
	responses = item.get("bookingFieldsResponses") or item.get("responses") or {}
	phone = attendee.get("phoneNumber") or (
		responses.get("attendeePhoneNumber") if isinstance(responses, dict) else ""
	)
	return ExternalBooking(
		external_id=item.get("uid") or item.get("id"),
		start=item.get("start") or item.get("startTime"),
		end=item.get("end") or item.get("endTime"),
		status=status,
		service_ref=str(item.get("eventTypeId") or event_type.get("id") or ""),
		service_name=event_type.get("slug") or item.get("type") or item.get("title") or "",
		staff_ref=str(host.get("email") or host.get("id") or ""),
		staff_name=host.get("name") or "",
		customer_name=attendee.get("name") or "",
		email=attendee.get("email") or "",
		phone=phone if isinstance(phone, str) else "",
		notes=item.get("description") or item.get("additionalNotes") or "",
		location=item.get("location") or "",
		url=item.get("meetingUrl") or "",
		raw=item,
	)


class CalCom(BookingPlatform):
	key = "calcom"
	label = "Cal.com"
	sector = "general"
	website = "https://cal.com"
	docs_url = "https://cal.com/docs/api-reference/v2/introduction"
	capabilities = frozenset({"pull", "webhook", "catalog", "cancel", "busy_feed"})
	required_fields = ("api_key",)
	fields = ("api_base_url", "api_key", "webhook_secret")
	default_base_url = "https://api.cal.com"
	setup_help = (
		"Create an API key in Cal.com → Settings → Developer → API keys (cal_live_…). "
		"Add a webhook (Settings → Developer → Webhooks) to the address below with the "
		"triggers Booking created/rescheduled/cancelled/requested/rejected and a secret, and "
		"paste the same secret here. 'Block time' registers the CRM busy feed as a read-only "
		"calendar in Cal.com, so CRM appointments block Cal.com slots."
	)

	def auth_headers(self):
		return {"Authorization": f"Bearer {self.secret('api_key')}", "cal-api-version": "2024-08-13"}

	def fetch_bookings(self, since, until):
		out, skip = [], 0
		while True:
			data = self.request(
				"GET",
				"/v2/bookings",
				params={
					"afterStart": since.isoformat(),
					"beforeEnd": until.isoformat(),
					"take": 100,
					"skip": skip,
				},
			)
			page = _items(data)
			out.extend(cal_to_booking(item) for item in page)
			pagination = (data or {}).get("pagination") or {}
			if not page or not pagination.get("hasNextPage"):
				break
			skip += len(page)
		return out

	def parse_webhook(self, headers, body, url=""):
		secret = self.secret("webhook_secret")
		if secret and not safe_equal(header(headers, "x-cal-signature-256"), hmac_hex(secret, body)):
			raise InvalidSignature("Cal.com signature does not match")
		payload = load_json(body)
		trigger = payload.get("triggerEvent") or ""
		data = payload.get("payload") or {}
		if not trigger.startswith("BOOKING_") or not (
			data.get("uid") and (data.get("startTime") or data.get("start"))
		):
			return []
		return [cal_to_booking(data, trigger)]

	def fetch_catalog(self):
		items = [
			CatalogItem(str(e["id"]), e.get("title") or e.get("slug") or "", "Service")
			for e in _items(self.request("GET", "/v2/event-types", headers={"cal-api-version": "2024-06-14"}))
		]
		return items

	def cancel_booking(self, external_id, reason=""):
		self.request(
			"POST",
			f"/v2/bookings/{external_id}/cancel",
			json={"cancellationReason": reason or "Cancelled in the CRM"},
		)

	def register_busy_feed(self, url: str) -> None:
		"""Let Cal.com read the CRM's busy feed as a calendar, so CRM appointments block slots."""
		self.request("POST", "/v2/calendars/ics-feed/save", json={"urls": [url], "readOnly": True})


# ==========================================================================
# Calendly (API v2)
# ==========================================================================


def calendly_to_booking(invitee: dict, event: dict, canceled: bool = False) -> ExternalBooking:
	membership = (event.get("event_memberships") or [{}])[0] or {}
	location = event.get("location") or {}
	answers = invitee.get("questions_and_answers") or []
	phone = invitee.get("text_reminder_number") or next(
		(
			a.get("answer")
			for a in answers
			if "phone" in str(a.get("question", "")).lower()
			or "telefono" in str(a.get("question", "")).lower()
		),
		"",
	)
	status = (
		STATUS_CANCELLED
		if canceled or invitee.get("status") == "canceled" or event.get("status") == "canceled"
		else STATUS_CONFIRMED
	)
	if (invitee.get("no_show") or {}).get("uri"):
		status = STATUS_NO_SHOW
	return ExternalBooking(
		# event/invitee: cancelling needs the event, a group event has many invitees
		external_id=f"{_uuid(event.get('uri'))}/{_uuid(invitee.get('uri'))}",
		start=event.get("start_time"),
		end=event.get("end_time"),
		status=status,
		service_ref=_uuid(event.get("event_type")),
		service_name=event.get("name") or "",
		staff_ref=membership.get("user_email") or _uuid(membership.get("user")),
		staff_name=membership.get("user_name") or "",
		customer_name=invitee.get("name") or join_name(invitee.get("first_name"), invitee.get("last_name")),
		email=invitee.get("email") or "",
		phone=phone or "",
		notes="\n".join(f"{a.get('question')}: {a.get('answer')}" for a in answers if a.get("answer")),
		location=location.get("location") or location.get("join_url") or "",
		url=invitee.get("reschedule_url") or "",
		raw={"invitee": invitee, "event": event},
	)


def verify_calendly(
	signing_key: str, headers: dict, body: bytes, now: float | None = None, tolerance: int = 180
):
	value = header(headers, "Calendly-Webhook-Signature")
	parts = dict(p.split("=", 1) for p in value.split(",") if "=" in p)
	if not parts.get("t") or not parts.get("v1"):
		raise InvalidSignature("Calendly webhook without a signature")
	expected = hmac_hex(signing_key, f"{parts['t']}.".encode() + body)
	if not safe_equal(parts["v1"], expected):
		raise InvalidSignature("Calendly signature does not match")
	if abs((now or time.time()) - int(parts["t"])) > tolerance:
		raise InvalidSignature("Calendly webhook is too old")


class Calendly(BookingPlatform):
	key = "calendly"
	label = "Calendly"
	sector = "general"
	website = "https://calendly.com"
	docs_url = "https://developer.calendly.com"
	capabilities = frozenset({"pull", "webhook", "catalog", "cancel"})
	required_fields = ("api_key",)
	fields = ("api_key", "webhook_secret")
	default_base_url = "https://api.calendly.com"
	setup_help = (
		"Create a Personal Access Token in Calendly → Integrations → API & Webhooks. "
		"Webhooks need a paid plan: create a subscription to the address below for "
		"invitee.created, invitee.canceled and invitee_no_show.created with a signing key, "
		"and paste the key here. Calendly has no API to block time: connect the same Google "
		"Calendar the CRM syncs to, and Calendly will see CRM appointments as busy."
	)

	def auth_headers(self):
		return {"Authorization": f"Bearer {self.secret('api_key')}"}

	def organization(self) -> str:
		me = self.request("GET", "/users/me") or {}
		return (me.get("resource") or {}).get("current_organization") or ""

	def fetch_bookings(self, since, until):
		org = self.organization()
		out, token = [], None
		while True:
			params = {
				"organization": org,
				"min_start_time": since.astimezone(UTC).isoformat().replace("+00:00", "Z"),
				"max_start_time": until.astimezone(UTC).isoformat().replace("+00:00", "Z"),
				"count": 100,
				"sort": "start_time:asc",
			}
			if token:
				params["page_token"] = token
			data = self.request("GET", "/scheduled_events", params=params) or {}
			for event in data.get("collection") or []:
				invitees = (
					self.request(
						"GET", f"/scheduled_events/{_uuid(event['uri'])}/invitees", params={"count": 100}
					)
					or {}
				)
				for invitee in invitees.get("collection") or []:
					out.append(calendly_to_booking(invitee, event))
			token = (data.get("pagination") or {}).get("next_page_token")
			if not token:
				break
		return out

	def parse_webhook(self, headers, body, url=""):
		key = self.secret("webhook_secret")
		if key:
			verify_calendly(key, headers, body)
		payload = load_json(body)
		kind = payload.get("event") or ""
		data = payload.get("payload") or {}
		event = data.get("scheduled_event") or {}
		if not kind.startswith("invitee") or not event:
			return []
		# a reschedule arrives as cancel(old) + create(new): both are handled as they come
		return [calendly_to_booking(data, event, canceled=kind == "invitee.canceled")]

	def fetch_catalog(self):
		org = self.organization()
		items = [
			CatalogItem(_uuid(e["uri"]), e.get("name") or "", "Service")
			for e in (
				self.request("GET", "/event_types", params={"organization": org, "count": 100}) or {}
			).get("collection")
			or []
		]
		for member in (
			self.request("GET", "/organization_memberships", params={"organization": org, "count": 100}) or {}
		).get("collection") or []:
			user = member.get("user") or {}
			items.append(
				CatalogItem(user.get("email") or _uuid(user.get("uri")), user.get("name") or "", "Staff")
			)
		return items

	def cancel_booking(self, external_id, reason=""):
		event = external_id.split("/", 1)[0]
		self.request(
			"POST", f"/scheduled_events/{event}/cancellation", json={"reason": reason or "Cancelled"}
		)


# ==========================================================================
# SimplyBook.me (REST v2 admin API)
# ==========================================================================

SIMPLYBOOK_STATUS = {
	"confirmed": STATUS_CONFIRMED,
	"confirmed_pending": STATUS_PENDING,
	"pending": STATUS_PENDING,
	"canceled": STATUS_CANCELLED,
	"cancelled": STATUS_CANCELLED,
}


def simplybook_to_booking(item: dict, tz: str) -> ExternalBooking:
	client = item.get("client") or {}
	service = item.get("service") or {}
	provider = item.get("provider") or {}
	start = item.get("start_datetime") or item.get("from")
	end = item.get("end_datetime") or item.get("to")
	return ExternalBooking(
		external_id=item.get("id"),
		start=local_to_utc(start, tz),
		end=local_to_utc(end, tz) if end else None,
		status=SIMPLYBOOK_STATUS.get(str(item.get("status") or "").lower(), STATUS_CONFIRMED),
		service_ref=str(item.get("service_id") or service.get("id") or ""),
		service_name=service.get("name") or item.get("service_name") or "",
		staff_ref=str(item.get("provider_id") or provider.get("id") or ""),
		staff_name=provider.get("name") or item.get("provider_name") or "",
		customer_name=client.get("name") or item.get("client_name") or "",
		email=client.get("email") or item.get("client_email") or "",
		phone=client.get("phone") or item.get("client_phone") or "",
		notes=item.get("comment") or "",
		price=float(service.get("price") or 0),
		currency=service.get("currency") or "",
		raw=item,
	)


class SimplyBook(BookingPlatform):
	key = "simplybook"
	label = "SimplyBook.me"
	sector = "general"
	website = "https://simplybook.me"
	docs_url = "https://simplybook.me/api/swagger-admin"
	capabilities = frozenset({"pull", "webhook", "catalog", "cancel", "block"})
	required_fields = ("account_id", "client_id", "client_secret")
	fields = ("api_base_url", "account_id", "client_id", "client_secret")
	default_base_url = "https://user-api-v2.simplybook.it"
	setup_help = (
		"Account ID is your company login (the xxx in xxx.simplybook.it); Client ID and "
		"Client Secret are an admin user's login and password (use a dedicated user without "
		"2FA). Enable the API Custom Feature in SimplyBook. The CRM registers the webhook for "
		"new/changed/cancelled bookings on 'Test connection'; SimplyBook webhooks are unsigned, "
		"so every notification is re-read from the API before it is trusted."
	)

	def _login(self):
		import requests

		try:
			response = requests.post(
				f"{self.base_url}/admin/auth",
				json={
					"company": self.value("account_id"),
					"login": self.value("client_id"),
					"password": self.secret("client_secret"),
				},
				timeout=self.timeout,
			)
		except requests.RequestException as exc:
			raise PlatformError(f"SimplyBook: {exc.__class__.__name__}") from exc
		if not response.ok:
			raise PlatformError(f"SimplyBook login refused (HTTP {response.status_code})")
		data = response.json()
		if data.get("require2fa"):
			raise PlatformError(
				"SimplyBook asks for 2FA: use an admin user without two-factor authentication"
			)
		return data["token"], 50 * 60

	def auth_headers(self):
		return {"X-Company-Login": self.value("account_id"), "X-Token": self.cached_token(self._login)}

	def fetch_bookings(self, since, until):
		tz = _scheduling_tz()
		out, page = [], 1
		while True:
			data = self.request(
				"GET",
				"/admin/bookings",
				params={
					"page": page,
					"on_page": 100,
					"filter[date_from]": since.date().isoformat(),
					"filter[date_to]": until.date().isoformat(),
				},
			)
			items = _items(data)
			out.extend(simplybook_to_booking(item, tz) for item in items)
			meta = (data or {}).get("metadata") if isinstance(data, dict) else None
			if not items or not meta or page >= int(meta.get("pages_count") or 1):
				break
			page += 1
		return out

	def parse_webhook(self, headers, body, url=""):
		payload = load_json(body)
		booking_id = payload.get("booking_id") if isinstance(payload, dict) else None
		if not booking_id or str(payload.get("company") or "") not in ("", self.value("account_id")):
			return []
		# unsigned: the notification is only a hint, the API is the truth
		item = self.request("GET", f"/admin/bookings/{booking_id}")
		booking = simplybook_to_booking(item or {}, _scheduling_tz())
		if payload.get("notification_type") == "cancel":
			booking.status = STATUS_CANCELLED
		return [booking]

	def ensure_webhooks(self, url: str) -> None:
		existing = {(w.get("url"), w.get("event")) for w in _items(self.request("GET", "/admin/webhooks"))}
		for event in ("new_booking", "change_booking", "cancel_booking"):
			if (url, event) not in existing:
				self.request("POST", "/admin/webhooks", json={"url": url, "event": event})

	def fetch_catalog(self):
		items = [
			CatalogItem(str(s["id"]), s.get("name") or "", "Service")
			for s in _items(self.request("GET", "/admin/services"))
		]
		items += [
			CatalogItem(str(p["id"]), p.get("name") or "", "Staff")
			for p in _items(self.request("GET", "/admin/providers"))
		]
		return items

	def cancel_booking(self, external_id, reason=""):
		self.request("DELETE", f"/admin/bookings/{external_id}")

	def block_time(self, staff_ref, start, end, reason=""):
		from zoneinfo import ZoneInfo

		tz = ZoneInfo(_scheduling_tz())
		fmt = "%Y-%m-%d %H:%M:%S"
		data = self.request(
			"POST",
			"/admin/calendar-notes",
			json={
				"provider_id": int(staff_ref) if str(staff_ref).isdigit() else staff_ref,
				"start_date_time": start.astimezone(tz).strftime(fmt),
				"end_date_time": end.astimezone(tz).strftime(fmt),
				"note": reason or "CRM",
				"time_blocked": True,
				"mode": "provider",
			},
		)
		return str((data or {}).get("id") or "")

	def unblock_time(self, block_id, staff_ref=""):
		self.request("DELETE", f"/admin/calendar-notes/{block_id}")


# ==========================================================================
# Acuity Scheduling
# ==========================================================================


def acuity_to_booking(item: dict) -> ExternalBooking:
	start = as_utc(item.get("datetime"))
	minutes = int(float(item.get("duration") or 30))
	status = STATUS_CANCELLED if item.get("canceled") in (True, "true", 1) else STATUS_CONFIRMED
	return ExternalBooking(
		external_id=item.get("id"),
		start=start,
		end=start + datetime.timedelta(minutes=minutes),
		status=status,
		service_ref=str(item.get("appointmentTypeID") or ""),
		service_name=item.get("type") or "",
		staff_ref=str(item.get("calendarID") or ""),
		staff_name=item.get("calendar") or "",
		customer_name=join_name(item.get("firstName"), item.get("lastName")),
		email=item.get("email") or "",
		phone=item.get("phone") or "",
		notes=item.get("notes") or "",
		location=item.get("location") or "",
		price=float(item.get("price") or 0),
		url=item.get("confirmationPage") or "",
		raw=item,
	)


class Acuity(BookingPlatform):
	key = "acuity"
	label = "Acuity Scheduling"
	sector = "wellness"
	website = "https://acuityscheduling.com"
	docs_url = "https://developers.acuityscheduling.com"
	capabilities = frozenset({"pull", "webhook", "catalog", "cancel", "block"})
	required_fields = ("client_id", "api_key")
	fields = ("client_id", "api_key")
	default_base_url = "https://acuityscheduling.com/api/v1"
	setup_help = (
		"In Acuity → Integrations → API copy the User ID (Client ID here) and the API key. "
		"The CRM registers its webhooks (scheduled, rescheduled, canceled, changed) on 'Test "
		"connection'; they are verified with your API key. Map each Acuity calendar to a "
		"professional (Staff) and each appointment type to a service."
	)

	def auth_headers(self):
		import base64

		token = base64.b64encode(f"{self.value('client_id')}:{self.secret('api_key')}".encode()).decode()
		return {"Authorization": f"Basic {token}"}

	def fetch_bookings(self, since, until):
		out = []
		for canceled in ("false", "true"):
			items = self.request(
				"GET",
				"/appointments",
				params={
					"minDate": since.date().isoformat(),
					"maxDate": until.date().isoformat(),
					"max": 2000,
					"canceled": canceled,
				},
			)
			out.extend(acuity_to_booking(item) for item in _items(items))
		return out

	def parse_webhook(self, headers, body, url=""):
		expected = hmac_b64(self.secret("api_key"), body)
		if not safe_equal(header(headers, "X-Acuity-Signature"), expected):
			raise InvalidSignature("Acuity signature does not match")
		form = {k: v[0] for k, v in parse_qs(body.decode("utf-8", errors="replace")).items()}
		if not form.get("id") or not str(form.get("action", "")).startswith("appointment"):
			return []
		booking = acuity_to_booking(self.request("GET", f"/appointments/{form['id']}") or {})
		if form.get("action") == "appointment.canceled":
			booking.status = STATUS_CANCELLED
		return [booking]

	def ensure_webhooks(self, url: str) -> None:
		existing = {(w.get("event"), w.get("target")) for w in _items(self.request("GET", "/webhooks"))}
		for event in (
			"appointment.scheduled",
			"appointment.rescheduled",
			"appointment.canceled",
			"appointment.changed",
		):
			if (event, url) not in existing:
				self.request("POST", "/webhooks", json={"event": event, "target": url})

	def fetch_catalog(self):
		items = [
			CatalogItem(str(t["id"]), t.get("name") or "", "Service")
			for t in _items(self.request("GET", "/appointment-types"))
		]
		items += [
			CatalogItem(str(c["id"]), c.get("name") or "", "Staff")
			for c in _items(self.request("GET", "/calendars"))
		]
		return items

	def cancel_booking(self, external_id, reason=""):
		self.request(
			"PUT",
			f"/appointments/{external_id}/cancel",
			json={"cancelNote": reason or "Cancelled in the CRM"},
		)

	def block_time(self, staff_ref, start, end, reason=""):
		data = self.request(
			"POST",
			"/blocks",
			json={
				"start": start.isoformat(),
				"end": end.isoformat(),
				"calendarID": int(staff_ref) if str(staff_ref).isdigit() else staff_ref,
				"notes": reason or "CRM",
			},
		)
		return str((data or {}).get("id") or "")

	def unblock_time(self, block_id, staff_ref=""):
		self.request("DELETE", f"/blocks/{block_id}")


# ==========================================================================
# Microsoft Bookings (Graph)
# ==========================================================================


def graph_time(value: dict) -> datetime.datetime:
	value = value or {}
	zone = value.get("timeZone") or "UTC"
	text = str(value.get("dateTime") or "")
	if zone.upper() in ("UTC", "Z"):
		return as_utc(text if text.endswith("Z") or "+" in text[10:] else text + "Z")
	return local_to_utc(text, zone)


def msbookings_to_booking(item: dict) -> ExternalBooking:
	customer = (item.get("customers") or [{}])[0] or {}
	return ExternalBooking(
		external_id=item.get("id"),
		start=graph_time(item.get("startDateTime") or item.get("start")),
		end=graph_time(item.get("endDateTime") or item.get("end")),
		status=STATUS_CONFIRMED,
		service_ref=item.get("serviceId") or "",
		service_name=item.get("serviceName") or "",
		staff_ref=(item.get("staffMemberIds") or [""])[0],
		customer_name=customer.get("name") or item.get("customerName") or "",
		email=customer.get("emailAddress") or item.get("customerEmailAddress") or "",
		phone=customer.get("phone") or item.get("customerPhone") or "",
		notes=customer.get("notes") or item.get("customerNotes") or item.get("serviceNotes") or "",
		price=float(item.get("price") or 0),
		url=item.get("joinWebUrl") or "",
		raw=item,
	)


class MicrosoftBookings(BookingPlatform):
	key = "msbookings"
	label = "Microsoft Bookings"
	sector = "general"
	website = "https://www.microsoft.com/microsoft-365/business/scheduling-and-booking-app"
	docs_url = "https://learn.microsoft.com/graph/api/resources/booking-api-overview"
	capabilities = frozenset({"pull", "catalog", "cancel"})
	required_fields = ("tenant_id", "client_id", "client_secret", "account_id")
	fields = ("tenant_id", "client_id", "client_secret", "account_id")
	default_base_url = "https://graph.microsoft.com/v1.0"
	#: cancelled appointments vanish from calendarView instead of changing status
	authoritative_window = True
	setup_help = (
		"Register an app in Microsoft Entra ID with the application permission "
		"BookingsAppointment.ReadWrite.All (admin consent), create a client secret, and enter "
		"Tenant ID, Client ID and secret. Account ID is the booking business id (its e-mail "
		"address, e.g. studio@contoso.onmicrosoft.com). Graph has no webhooks for Bookings: "
		"the CRM polls every 15 minutes."
	)

	def _login(self):
		import requests

		try:
			response = requests.post(
				f"https://login.microsoftonline.com/{self.value('tenant_id')}/oauth2/v2.0/token",
				data={
					"grant_type": "client_credentials",
					"client_id": self.value("client_id"),
					"client_secret": self.secret("client_secret"),
					"scope": "https://graph.microsoft.com/.default",
				},
				timeout=self.timeout,
			)
		except requests.RequestException as exc:
			raise PlatformError(f"Microsoft: {exc.__class__.__name__}") from exc
		if not response.ok:
			raise PlatformError(f"Microsoft login refused (HTTP {response.status_code})")
		data = response.json()
		return data["access_token"], data.get("expires_in") or 3600

	def auth_headers(self):
		return {"Authorization": f"Bearer {self.cached_token(self._login)}"}

	@property
	def business(self) -> str:
		return f"/solutions/bookingBusinesses/{self.value('account_id')}"

	def fetch_bookings(self, since, until):
		out = []
		url = f"{self.business}/calendarView"
		params = {
			"start": since.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
			"end": until.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
		}
		while url:
			data = self.request("GET", url, params=params) or {}
			out.extend(msbookings_to_booking(item) for item in data.get("value") or [])
			url, params = data.get("@odata.nextLink"), None
		return out

	def fetch_catalog(self):
		items = [
			CatalogItem(s["id"], s.get("displayName") or "", "Service")
			for s in (self.request("GET", f"{self.business}/services") or {}).get("value") or []
		]
		items += [
			CatalogItem(s["id"], s.get("displayName") or "", "Staff")
			for s in (self.request("GET", f"{self.business}/staffMembers") or {}).get("value") or []
		]
		return items

	def cancel_booking(self, external_id, reason=""):
		self.request(
			"POST",
			f"{self.business}/appointments/{external_id}/cancel",
			json={"cancellationMessage": reason or "Cancelled"},
		)


# ==========================================================================
# TIMIFY
# ==========================================================================


def timify_to_booking(item: dict) -> ExternalBooking:
	customer = (item.get("customers") or [{}])[0] or {}
	start = item.get("from") or item.get("datetime") or item.get("date")
	start_utc = as_utc(start)
	end = item.get("until") or item.get("to")
	minutes = int(float(item.get("duration") or 30))
	resources = item.get("resources") or item.get("resourceIds") or [item.get("resourceId")]
	first_resource = resources[0] if resources else ""
	if isinstance(first_resource, dict):
		first_resource = first_resource.get("id") or ""
	deleted = (
		item.get("isDeleted")
		or item.get("deleted")
		or str(item.get("status", "")).lower() in ("deleted", "cancelled", "canceled")
	)
	return ExternalBooking(
		external_id=item.get("id"),
		start=start_utc,
		end=as_utc(end) if end else start_utc + datetime.timedelta(minutes=minutes),
		status=STATUS_CANCELLED if deleted else STATUS_CONFIRMED,
		service_ref=str(item.get("serviceId") or ""),
		service_name=item.get("title") or "",
		staff_ref=str(first_resource or ""),
		customer_name=customer.get("fullName")
		or join_name(customer.get("firstName"), customer.get("lastName"))
		or customer.get("name")
		or "",
		email=customer.get("email") or "",
		phone=customer.get("phone") or customer.get("mobilePhone") or "",
		notes=item.get("notes") or "",
		price=float(item.get("price") or 0),
		currency=item.get("currency") or "",
		raw=item,
	)


class Timify(BookingPlatform):
	key = "timify"
	label = "TIMIFY"
	sector = "general"
	website = "https://www.timify.com/it"
	docs_url = "https://docs.timify.dev"
	capabilities = frozenset({"pull", "webhook", "cancel"})
	required_fields = ("client_id", "client_secret", "account_id")
	fields = ("client_id", "client_secret", "account_id", "webhook_secret")
	default_base_url = "https://api.timify.com"
	setup_help = (
		"Create an app in the TIMIFY Developer Platform: App ID and App Secret go in Client "
		"ID/Secret, the company id in Account ID. Configure the appointment webhooks to the "
		"address below, adding a custom header X-Webhook-Secret with a value of your choice "
		"and paste the same value in the signing secret."
	)

	def _login(self):
		import requests

		try:
			response = requests.post(
				f"{self.base_url}/v1/auth/token",
				json={"appid": self.value("client_id"), "appsecret": self.secret("client_secret")},
				timeout=self.timeout,
			)
		except requests.RequestException as exc:
			raise PlatformError(f"TIMIFY: {exc.__class__.__name__}") from exc
		if not response.ok:
			raise PlatformError(f"TIMIFY login refused (HTTP {response.status_code})")
		data = response.json()
		token = data.get("accessToken") or data.get("access_token") or data.get("token")
		return token, data.get("expires") or data.get("expiresIn") or 3600

	def auth_headers(self):
		return {"authorization": self.cached_token(self._login), "company-id": self.value("account_id")}

	def fetch_bookings(self, since, until):
		out = []
		cursor = since
		while cursor < until:
			# TIMIFY serves at most 31 days per call
			chunk_end = min(cursor + datetime.timedelta(days=30), until)
			data = self.request(
				"GET",
				"/v1/appointments",
				params={
					"from_date": cursor.date().isoformat(),
					"to_date": chunk_end.date().isoformat(),
					"timezone": "UTC",
				},
			)
			out.extend(
				timify_to_booking(item) for item in _items(data) if isinstance(item, dict) and item.get("id")
			)
			cursor = chunk_end + datetime.timedelta(days=1)
		return out

	def parse_webhook(self, headers, body, url=""):
		secret = self.secret("webhook_secret")
		if secret and not safe_equal(header(headers, "X-Webhook-Secret"), secret):
			raise InvalidSignature("TIMIFY webhook without the agreed secret header")
		payload = load_json(body)
		event = str((payload or {}).get("event") or (payload or {}).get("type") or "").lower()
		items = _items(payload) or [(payload or {}).get("data") or payload]
		out = []
		for item in items:
			if (
				isinstance(item, dict)
				and item.get("id")
				and (item.get("from") or item.get("datetime") or item.get("date"))
			):
				booking = timify_to_booking(item)
				if "delete" in event or "cancel" in event:
					booking.status = STATUS_CANCELLED
				out.append(booking)
		return out

	def cancel_booking(self, external_id, reason=""):
		self.request("DELETE", f"/v1/appointments/{external_id}")


# ==========================================================================
# Setmore
# ==========================================================================


def setmore_to_booking(item: dict) -> ExternalBooking:
	customer = item.get("customer") or {}
	label = str(item.get("label") or "").lower()
	status = (
		STATUS_CANCELLED
		if "cancel" in label
		else STATUS_NO_SHOW
		if "no" in label and "show" in label
		else STATUS_CONFIRMED
	)
	return ExternalBooking(
		external_id=item.get("key"),
		start=item.get("start_time"),
		end=item.get("end_time"),
		status=status,
		service_ref=item.get("service_key") or "",
		staff_ref=item.get("staff_key") or "",
		customer_name=join_name(customer.get("first_name"), customer.get("last_name")),
		email=customer.get("email_id") or "",
		phone=customer.get("cell_phone") or "",
		notes=item.get("comment") or "",
		price=float(item.get("cost") or 0),
		currency=item.get("currency") or "",
		raw=item,
	)


class Setmore(BookingPlatform):
	key = "setmore"
	label = "Setmore"
	sector = "general"
	website = "https://www.setmore.com"
	docs_url = "https://setmore.docs.apiary.io"
	capabilities = frozenset({"pull", "catalog"})
	required_fields = ("refresh_token",)
	fields = ("refresh_token",)
	default_base_url = "https://developer.setmore.com/api/v1"
	setup_help = (
		"Setmore's API is a limited beta for Pro accounts: write to api@setmore.com to "
		"receive a refresh token and paste it here. Setmore has no webhooks nor a cancel "
		"endpoint: the CRM polls every 15 minutes."
	)

	def _login(self):
		data = self.request("GET", "/o/oauth2/token", params={"refreshToken": self.secret("refresh_token")})
		token = ((data or {}).get("data") or {}).get("token") or {}
		if not token.get("access_token"):
			raise PlatformError("Setmore refused the refresh token")
		return token["access_token"], token.get("expires_in") or 3600

	def auth_headers(self):
		return {"Authorization": f"Bearer {self.cached_token(self._login)}"}

	def request(self, method, path, **kwargs):
		# the login call must not recurse into auth_headers
		if path.startswith("/o/oauth2"):
			import requests

			response = requests.request(
				method, f"{self.base_url}{path}", timeout=self.timeout, params=kwargs.get("params")
			)
			if not response.ok:
				raise PlatformError(f"Setmore HTTP {response.status_code}")
			return response.json()
		return super().request(method, path, **kwargs)

	def fetch_bookings(self, since, until):
		out, cursor = [], None
		while True:
			params = {
				"startDate": since.strftime("%d-%m-%Y"),
				"endDate": until.strftime("%d-%m-%Y"),
				"customerDetails": "true",
			}
			if cursor:
				params["cursor"] = cursor
			data = (self.request("GET", "/bookingapi/appointments", params=params) or {}).get("data") or {}
			out.extend(setmore_to_booking(item) for item in data.get("appointments") or [])
			cursor = data.get("cursor")
			if not cursor or not data.get("appointments"):
				break
		return out

	def fetch_catalog(self):
		services = ((self.request("GET", "/bookingapi/services") or {}).get("data") or {}).get(
			"services"
		) or []
		staff = ((self.request("GET", "/bookingapi/staffs") or {}).get("data") or {}).get("staffs") or []
		return [CatalogItem(s["key"], s.get("service_name") or "", "Service") for s in services] + [
			CatalogItem(s["key"], join_name(s.get("first_name"), s.get("last_name")), "Staff") for s in staff
		]


# ==========================================================================
# Easy!Appointments (self-hosted, open source)
# ==========================================================================


def easyappointments_to_booking(item: dict, tz: str) -> ExternalBooking:
	customer = item.get("customer") or {}
	return ExternalBooking(
		external_id=item.get("id"),
		start=local_to_utc(item.get("start"), tz),
		end=local_to_utc(item.get("end"), tz) if item.get("end") else None,
		status=STATUS_CONFIRMED,
		service_ref=str(item.get("serviceId") or ""),
		staff_ref=str(item.get("providerId") or ""),
		customer_name=join_name(customer.get("firstName"), customer.get("lastName")),
		email=customer.get("email") or "",
		phone=customer.get("phone") or "",
		notes=item.get("notes") or "",
		location=item.get("location") or "",
		raw=item,
	)


class EasyAppointments(BookingPlatform):
	key = "easyappointments"
	label = "Easy!Appointments"
	sector = "general"
	website = "https://easyappointments.org"
	docs_url = "https://easyappointments.org/docs/rest-api/"
	capabilities = frozenset({"pull", "webhook", "catalog", "cancel", "block"})
	required_fields = ("api_base_url", "api_key")
	fields = ("api_base_url", "api_key", "webhook_secret")
	#: an appointment deleted in Easy!Appointments simply stops being listed
	authoritative_window = True
	setup_help = (
		"API Base URL is https://<your-host>/index.php/api/v1 and the API key is the token set "
		"in Settings → Integrations → API. For webhooks, point them to the address below and "
		"use the same token in X-EA-Token (signing secret here)."
	)

	def auth_headers(self):
		return {"Authorization": f"Bearer {self.secret('api_key')}"}

	def fetch_bookings(self, since, until):
		tz = _scheduling_tz()
		out = []
		for page in range(1, 51):
			items = _items(
				self.request(
					"GET",
					"/appointments",
					params={"page": page, "length": 100, "sort": "-start", "with": "customer"},
				)
			)
			if not items:
				break
			for item in items:
				booking = easyappointments_to_booking(item, tz)
				if booking.end >= since and booking.start <= until:
					out.append(booking)
			if all(local_to_utc(i.get("start"), tz) < since for i in items):
				break
		return out

	def parse_webhook(self, headers, body, url=""):
		secret = self.secret("webhook_secret")
		if secret and not safe_equal(header(headers, "X-EA-Token"), secret):
			raise InvalidSignature("Easy!Appointments webhook without the agreed token")
		payload = load_json(body)
		action = (
			str(payload.get("action") or payload.get("event") or "").lower()
			if isinstance(payload, dict)
			else ""
		)
		item = (payload.get("payload") or payload.get("data") or payload) if isinstance(payload, dict) else {}
		if not isinstance(item, dict) or not item.get("id") or not item.get("start"):
			return []
		booking = easyappointments_to_booking(item, _scheduling_tz())
		if "delete" in action:
			booking.status = STATUS_CANCELLED
		return [booking]

	def fetch_catalog(self):
		items = [
			CatalogItem(str(s["id"]), s.get("name") or "", "Service")
			for s in _items(self.request("GET", "/services"))
		]
		items += [
			CatalogItem(str(p["id"]), join_name(p.get("firstName"), p.get("lastName")), "Staff")
			for p in _items(self.request("GET", "/providers"))
		]
		return items

	def cancel_booking(self, external_id, reason=""):
		self.request("DELETE", f"/appointments/{external_id}")

	def block_time(self, staff_ref, start, end, reason=""):
		from zoneinfo import ZoneInfo

		tz = ZoneInfo(_scheduling_tz())
		fmt = "%Y-%m-%d %H:%M:%S"
		data = self.request(
			"POST",
			"/unavailabilities",
			json={
				"start": start.astimezone(tz).strftime(fmt),
				"end": end.astimezone(tz).strftime(fmt),
				"providerId": int(staff_ref) if str(staff_ref).isdigit() else staff_ref,
				"notes": reason or "CRM",
			},
		)
		return str((data or {}).get("id") or "")

	def unblock_time(self, block_id, staff_ref=""):
		self.request("DELETE", f"/unavailabilities/{block_id}")


# ==========================================================================
# Booksy (partner API)
# ==========================================================================

BOOKSY_STATUS = {
	"A": STATUS_CONFIRMED,
	"M": STATUS_CONFIRMED,
	"C": STATUS_CANCELLED,
	"D": STATUS_CANCELLED,
	"F": STATUS_COMPLETED,
	"N": STATUS_NO_SHOW,
	"P": STATUS_PENDING,
	"W": STATUS_PENDING,
}


def booksy_to_booking(item: dict) -> ExternalBooking | None:
	if item.get("type") == "R":
		return None  # a time reservation (block), not a client booking
	tz = item.get("business_timezone") or _scheduling_tz()
	sub = (item.get("subbookings") or [{}])[0] or {}
	return ExternalBooking(
		external_id=item.get("id"),
		start=local_to_utc(item.get("booked_from") or sub.get("booked_from"), tz),
		end=local_to_utc(item.get("booked_till") or sub.get("booked_till"), tz),
		status=BOOKSY_STATUS.get(str(item.get("status") or "A"), STATUS_CONFIRMED),
		service_ref=str(sub.get("service_variant_id") or ""),
		service_name=sub.get("service_name") or "",
		staff_ref=str(sub.get("staffer_id") or ""),
		customer_name=item.get("customer_name") or "",
		email=item.get("customer_email") or "",
		phone=item.get("customer_phone") or "",
		notes=item.get("customer_note") or "",
		raw=item,
	)


class Booksy(BookingPlatform):
	key = "booksy"
	label = "Booksy"
	sector = "beauty"
	website = "https://booksy.com"
	docs_url = "https://docs.booksy.com"
	api_access = "partner"
	capabilities = frozenset({"pull", "webhook", "catalog", "cancel", "block"})
	required_fields = ("client_id", "client_secret", "account_id", "tenant_id", "extra_param")
	fields = ("api_base_url", "client_id", "client_secret", "account_id", "tenant_id", "extra_param")
	setup_help = (
		"Booksy's Public API is for approved partners. Client ID = partner UUID, Client "
		"Secret = the partner RSA private key (PEM), Account ID = business id, Tenant = "
		"country code (it, pl, us…), Additional parameter = partner name. Booksy sends "
		"webhooks unsigned to the address agreed at onboarding: the URL token authenticates them."
	)

	@property
	def base_url(self) -> str:
		cc = self.value("tenant_id") or "us"
		return (self.value("api_base_url") or f"https://{cc}.booksy.com/public-api/{cc}").rstrip("/")

	def _login(self):
		import jwt
		import requests

		now = int(time.time())
		assertion = jwt.encode(
			{
				"iss": "https://public-api.booksy.com",
				"iat": now,
				"exp": now + 180,
				"aud": self.value("client_id"),
			},
			self.secret("client_secret"),
			algorithm="RS256",
		)
		try:
			response = requests.post(
				f"{self.base_url}/token/",
				data={"partner_name": self.value("extra_param"), "token": assertion},
				headers={"Accept": "application/json; version=0.3"},
				timeout=self.timeout,
			)
		except requests.RequestException as exc:
			raise PlatformError(f"Booksy: {exc.__class__.__name__}") from exc
		if not response.ok:
			raise PlatformError(f"Booksy login refused (HTTP {response.status_code})")
		return response.json()["access"], 4 * 60

	def auth_headers(self):
		return {
			"Authorization": f"Bearer {self.cached_token(self._login)}",
			"Accept": "application/json; version=0.3",
		}

	@property
	def business(self) -> str:
		return f"/business/{self.value('account_id')}"

	def fetch_bookings(self, since, until):
		from zoneinfo import ZoneInfo

		tz = ZoneInfo(_scheduling_tz())
		fmt = "%Y-%m-%dT%H:%M"
		out = []
		url = f"{self.business}/appointment/"
		params = {
			"booked_from": since.astimezone(tz).strftime(fmt),
			"booked_till": until.astimezone(tz).strftime(fmt),
		}
		while url:
			data = self.request("GET", url, params=params) or {}
			for item in data.get("results") or []:
				booking = booksy_to_booking(item)
				if booking:
					out.append(booking)
			url, params = data.get("next"), None
		return out

	def parse_webhook(self, headers, body, url=""):
		payload = load_json(body)
		item = (payload or {}).get("appointment") or {}
		if not item.get("id"):
			return []
		booking = booksy_to_booking(item)
		if booking and payload.get("action") == "CANCELLED":
			booking.status = STATUS_CANCELLED
		return [booking] if booking else []

	def fetch_catalog(self):
		items = [
			CatalogItem(str(s["id"]), s.get("name") or "", "Service")
			for s in _items(self.request("GET", f"{self.business}/service/"))
		]
		items += [
			CatalogItem(str(r["id"]), r.get("name") or "", "Staff")
			for r in _items(self.request("GET", f"{self.business}/resource/"))
		]
		return items

	def cancel_booking(self, external_id, reason=""):
		self.request("PATCH", f"{self.business}/appointment/{external_id}/status/cancel/")

	def block_time(self, staff_ref, start, end, reason=""):
		from zoneinfo import ZoneInfo

		tz = ZoneInfo(_scheduling_tz())
		local_start, local_end = start.astimezone(tz), end.astimezone(tz)
		data = self.request(
			"POST",
			f"{self.business}/schedule/resource/{staff_ref}/time_off/",
			json={
				"date_from": local_start.date().isoformat(),
				"date_till": local_end.date().isoformat(),
				"hour_from": local_start.strftime("%H:%M"),
				"hour_till": local_end.strftime("%H:%M"),
				"reason_code": "other",
				"reason": reason or "CRM",
				"approved": True,
			},
		)
		return str((data or {}).get("id") or "")

	def unblock_time(self, block_id, staff_ref=""):
		self.request("DELETE", f"{self.business}/schedule/resource/{staff_ref}/time_off/{block_id}/")
