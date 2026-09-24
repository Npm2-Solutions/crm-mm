# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""What every booking platform connector speaks.

A connector turns one platform's idea of a booking — MioDottore's *booking*,
Calendly's *scheduled event + invitee*, Square's *booking* — into one
:class:`ExternalBooking`. Everything downstream (the appointment, the lead, the
conflict note, the calendar) only ever sees that one shape, so adding a platform
is one module and one registry line.

A connector declares what it can do through ``capabilities``:

* ``pull``      — list bookings in a window (polled by the scheduler)
* ``webhook``   — receive pushes from the platform (near real time)
* ``catalog``   — list the platform's services and staff, for the mapping screen
* ``cancel``    — cancel a booking on the platform
* ``block``     — mark a professional busy on the platform (two-way availability)
"""

from __future__ import annotations

import base64
import datetime
import hashlib
import hmac
import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any, ClassVar

UTC = datetime.timezone.utc

STATUS_CONFIRMED = "confirmed"
STATUS_PENDING = "pending"
STATUS_CANCELLED = "cancelled"
STATUS_COMPLETED = "completed"
STATUS_NO_SHOW = "no_show"

#: how an external status lands on ``CRM Appointment.status``
APPOINTMENT_STATUS = {
	STATUS_CONFIRMED: "Confirmed",
	STATUS_PENDING: "Scheduled",
	STATUS_CANCELLED: "Cancelled",
	STATUS_COMPLETED: "Completed",
	STATUS_NO_SHOW: "No Show",
}


class PlatformError(Exception):
	"""A platform refused or failed a call. The message is safe to show an admin."""


class NotSupported(PlatformError):
	"""The platform has no API for this operation."""


class InvalidSignature(PlatformError):
	"""A webhook that does not prove it comes from the platform."""


@dataclass
class ExternalBooking:
	"""One booking as the CRM understands it, whatever platform it came from."""

	external_id: str
	start: datetime.datetime
	end: datetime.datetime
	status: str = STATUS_CONFIRMED
	service_ref: str = ""
	service_name: str = ""
	staff_ref: str = ""
	staff_name: str = ""
	resource_ref: str = ""
	customer_name: str = ""
	email: str = ""
	phone: str = ""
	notes: str = ""
	location: str = ""
	price: float = 0.0
	currency: str = ""
	url: str = ""
	raw: dict = field(default_factory=dict)

	def __post_init__(self):
		self.external_id = str(self.external_id or "").strip()
		self.start = as_utc(self.start)
		self.end = as_utc(self.end) if self.end else self.start
		if self.end <= self.start:
			self.end = self.start + datetime.timedelta(minutes=30)
		self.email = (self.email or "").strip().lower()
		self.phone = (self.phone or "").strip()
		self.customer_name = " ".join((self.customer_name or "").split())
		if self.status not in APPOINTMENT_STATUS:
			self.status = STATUS_CONFIRMED

	def as_dict(self) -> dict:
		data = asdict(self)
		data["start"] = self.start.isoformat()
		data["end"] = self.end.isoformat()
		return data


@dataclass
class CatalogItem:
	id: str
	name: str
	kind: str = "Service"  # Service | Staff | Resource
	extra: dict = field(default_factory=dict)


# --------------------------------------------------------------------------
# helpers shared by connectors (pure)
# --------------------------------------------------------------------------


def as_utc(value) -> datetime.datetime:
	"""ISO strings (with offset or Z), epoch seconds or datetimes → aware UTC.

	A naive value is taken as UTC: every platform we talk to documents UTC or
	sends an explicit offset, so a naive value is a platform bug, and UTC is the
	least surprising guess.
	"""
	if isinstance(value, datetime.datetime):
		return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
	if isinstance(value, int | float):
		return datetime.datetime.fromtimestamp(value, UTC)
	text = str(value or "").strip()
	if not text:
		raise PlatformError("Booking without a start time")
	if text.isdigit():
		return datetime.datetime.fromtimestamp(int(text), UTC)
	text = text.replace("Z", "+00:00")
	# Microsoft Graph sends 7 fractional digits; Python takes at most 6
	text = re.sub(r"(\.\d{6})\d+", r"\1", text)
	# "2026-09-25 10:00:00+0200" → isoformat wants a colon in the offset
	if len(text) > 5 and text[-5] in "+-" and text[-4:].isdigit() and ":" not in text[-5:]:
		text = text[:-2] + ":" + text[-2:]
	parsed = datetime.datetime.fromisoformat(text.replace(" ", "T", 1) if "T" not in text else text)
	return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def local_to_utc(value, tz_name: str) -> datetime.datetime:
	"""A naive local time ("2026-09-25 10:00:00", "2026-09-25T10:00") in ``tz_name`` → UTC.

	Several platforms (SimplyBook, Booksy, Easy!Appointments) answer in the
	business's wall-clock time without an offset.
	"""
	from zoneinfo import ZoneInfo

	if isinstance(value, datetime.datetime) and value.tzinfo:
		return value.astimezone(UTC)
	text = str(value or "").strip().replace("T", " ")
	if not text:
		raise PlatformError("Booking without a start time")
	if "+" in text[10:] or text.endswith("Z") or (len(text) > 19 and text[19] == "-"):
		return as_utc(text)
	parsed = datetime.datetime.fromisoformat(text[:19])
	try:
		tz = ZoneInfo(tz_name or "Europe/Rome")
	except Exception:
		tz = ZoneInfo("Europe/Rome")
	return parsed.replace(tzinfo=tz).astimezone(UTC)


def dig(data: Any, path: str, default: Any = None) -> Any:
	"""``dig(payload, "invitee.name")`` — dotted path into nested dicts/lists."""
	current = data
	for part in (path or "").split("."):
		if part == "":
			continue
		if isinstance(current, dict):
			current = current.get(part)
		elif isinstance(current, list) and part.lstrip("-").isdigit():
			index = int(part)
			current = current[index] if -len(current) <= index < len(current) else None
		else:
			return default
		if current is None:
			return default
	return current


def join_name(*parts) -> str:
	return " ".join(str(p).strip() for p in parts if p and str(p).strip())


def hmac_hex(secret: str, message: bytes, algo=hashlib.sha256) -> str:
	return hmac.new((secret or "").encode(), message, algo).hexdigest()


def hmac_b64(secret: str, message: bytes, algo=hashlib.sha256) -> str:
	return base64.b64encode(hmac.new((secret or "").encode(), message, algo).digest()).decode()


def safe_equal(a: str, b: str) -> bool:
	return hmac.compare_digest((a or "").strip(), (b or "").strip())


def header(headers: dict, name: str) -> str:
	"""Case-insensitive header lookup over a plain dict."""
	lowered = name.lower()
	for key, value in (headers or {}).items():
		if key.lower() == lowered:
			return value or ""
	return ""


def load_json(body: bytes | str) -> Any:
	if isinstance(body, bytes):
		body = body.decode("utf-8", errors="replace")
	try:
		return json.loads(body or "null")
	except ValueError:
		raise PlatformError("The webhook body is not JSON")


# --------------------------------------------------------------------------
# the connector contract
# --------------------------------------------------------------------------


class BookingPlatform:
	"""Base connector. Subclasses override what their platform supports.

	``conn`` is anything with ``get(field)`` and ``get_password(field)`` — the
	``CRM Booking Connection`` document in production, a stub in tests.
	"""

	key: ClassVar[str] = ""
	label: ClassVar[str] = ""
	sector: ClassVar[str] = "general"  # medical | beauty | wellness | general
	website: ClassVar[str] = ""
	docs_url: ClassVar[str] = ""
	api_access: ClassVar[str] = "public"  # public | partner | none
	capabilities: ClassVar[frozenset] = frozenset()
	#: connection fields the admin must fill, in the order the form asks for them
	required_fields: ClassVar[tuple] = ()
	#: fields the form shows at all (required ones included)
	fields: ClassVar[tuple] = ()
	default_base_url: ClassVar[str] = ""
	#: one paragraph for the admin: how to obtain credentials, what works
	setup_help: ClassVar[str] = ""
	timeout: ClassVar[int] = 20

	def __init__(self, conn):
		self.conn = conn

	# -- config ---------------------------------------------------------------

	def value(self, fieldname: str) -> str:
		return (self.conn.get(fieldname) or "").strip() if hasattr(self.conn, "get") else ""

	def secret(self, fieldname: str) -> str:
		try:
			return self.conn.get_password(fieldname, raise_exception=False) or ""
		except Exception:
			return ""

	@property
	def base_url(self) -> str:
		return (self.value("api_base_url") or self.default_base_url).rstrip("/")

	def missing_fields(self) -> list[str]:
		missing = []
		for fieldname in self.required_fields:
			is_secret = fieldname in ("client_secret", "api_key", "refresh_token", "webhook_secret")
			if not (self.secret(fieldname) if is_secret else self.value(fieldname)):
				missing.append(fieldname)
		return missing

	@classmethod
	def describe(cls) -> dict:
		return {
			"key": cls.key,
			"label": cls.label,
			"sector": cls.sector,
			"website": cls.website,
			"docs_url": cls.docs_url,
			"api_access": cls.api_access,
			"capabilities": sorted(cls.capabilities),
			"required_fields": list(cls.required_fields),
			"fields": list(cls.fields or cls.required_fields),
			"setup_help": cls.setup_help,
		}

	# -- tokens -----------------------------------------------------------------

	def cached_token(self, fetch) -> str:
		"""An access token reused until a minute before it expires.

		``fetch()`` returns ``(token, lifetime_seconds)``. The token is kept on the
		connection (encrypted), so a scheduler run does not log in every time.
		"""
		now = datetime.datetime.now(UTC)
		expires = self.conn.get("token_expires_on")
		token = self.secret("access_token")
		if token and expires:
			expires_at = as_utc(expires) if not isinstance(expires, datetime.datetime) else expires
			if expires_at.tzinfo is None:
				from crm.scheduling.timeutils import from_system_naive

				expires_at = from_system_naive(expires_at)
			if expires_at - now > datetime.timedelta(seconds=60):
				return token
		token, lifetime = fetch()
		self.store_token(token, now + datetime.timedelta(seconds=int(lifetime or 3600)))
		return token

	def store_token(self, token: str, expires_at: datetime.datetime) -> None:
		setter = getattr(self.conn, "store_token", None)
		if setter:
			setter(token, expires_at)
		else:  # a stub in tests
			self.conn["access_token"] = token
			self.conn["token_expires_on"] = expires_at

	# -- HTTP -------------------------------------------------------------------

	def auth_headers(self) -> dict:
		return {}

	def request(self, method: str, path: str, **kwargs) -> Any:
		"""One authenticated call; JSON in and out, errors as ``PlatformError``."""
		import requests

		url = path if path.startswith("http") else f"{self.base_url}/{path.lstrip('/')}"
		headers = {"Accept": "application/json", **self.auth_headers(), **kwargs.pop("headers", {})}
		try:
			response = requests.request(method, url, headers=headers, timeout=self.timeout, **kwargs)
		except requests.RequestException as exc:
			raise PlatformError(f"{self.label}: {exc.__class__.__name__}") from exc
		if response.status_code == 204 or not response.content:
			if response.ok:
				return None
		if not response.ok:
			detail = response.text[:300]
			raise PlatformError(f"{self.label} HTTP {response.status_code}: {detail}")
		try:
			return response.json()
		except ValueError:
			return response.text

	# -- operations (override) --------------------------------------------------

	def test(self) -> str:
		"""Prove the credentials work. Returns a one-line human summary."""
		if "pull" in self.capabilities:
			now = datetime.datetime.now(UTC)
			found = self.fetch_bookings(now, now + datetime.timedelta(days=7))
			return f"{len(found)} bookings in the next 7 days"
		return "Configuration saved"

	def fetch_bookings(self, since: datetime.datetime, until: datetime.datetime) -> list[ExternalBooking]:
		raise NotSupported(f"{self.label} cannot list bookings")

	def parse_webhook(self, headers: dict, body: bytes, url: str = "") -> list[ExternalBooking]:
		raise NotSupported(f"{self.label} does not send webhooks")

	def fetch_catalog(self) -> list[CatalogItem]:
		raise NotSupported(f"{self.label} does not expose its services")

	def cancel_booking(self, external_id: str, reason: str = "") -> None:
		raise NotSupported(f"{self.label} cannot cancel bookings through its API")

	def block_time(
		self, staff_ref: str, start: datetime.datetime, end: datetime.datetime, reason: str = ""
	) -> str:
		raise NotSupported(f"{self.label} cannot block time through its API")

	def unblock_time(self, block_id: str, staff_ref: str = "") -> None:
		raise NotSupported(f"{self.label} cannot remove blocked time through its API")
