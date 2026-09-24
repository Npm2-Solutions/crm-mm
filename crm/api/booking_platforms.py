# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Endpoints of the booking-platform connectors.

Guest:
* ``webhook`` — where platforms (and Zapier/Make/email routes) push bookings.
  The unguessable token in the URL names the connection; each connector then
  verifies the platform's own signature when it has one.
* ``busy_feed`` — the CRM's agenda as an iCalendar of anonymous busy blocks,
  per connection and per professional, for platforms that import a calendar
  (Treatwell "Calendario esterno", Fresha, Cal.com, Google…).

Managers: the Settings screen — list/save/test/sync connections and read the
platform's services and staff for the mapping table.
"""

from __future__ import annotations

import datetime
import hashlib
import hmac

import frappe
from frappe import _
from frappe.utils import cint, get_url

from crm.booking_platforms import catalog, get_provider, provider_class
from crm.booking_platforms.base import InvalidSignature, NotSupported, PlatformError
from crm.scheduling.timeutils import UTC, from_system_naive, to_system_naive
from crm.utils import count_field

MANAGER_ROLES = {"System Manager", "Sales Manager"}
SECRET_FIELDS = ("client_secret", "api_key", "refresh_token", "webhook_secret")
PLAIN_FIELDS = (
	"connection_name",
	"platform",
	"api_base_url",
	"account_id",
	"client_id",
	"tenant_id",
	"extra_param",
	"ical_url",
	"inbound_email_account",
	"sender_filter",
	"field_map",
	"default_service",
	"default_staff",
	"imported_status",
)
FLAG_FIELDS = ("enabled", "import_bookings", "push_blocks", "push_cancellations", "create_leads")
INT_FIELDS = ("sync_window_days", "lookback_days")


def _is_admin() -> bool:
	return "System Manager" in frappe.get_roles()


def _check_platform(platform: str | None):
	"""Beta connectors are for administrators only — server side too, not just hidden."""
	from crm.booking_platforms import is_stable

	if platform and not is_stable(platform) and not _is_admin():
		frappe.throw(
			_("This connection is still in testing: only an administrator can use it"), frappe.PermissionError
		)


def _check_connection(name: str):
	_check_platform(frappe.db.get_value("CRM Booking Connection", name, "platform"))


def _check_manager():
	if not MANAGER_ROLES & set(frappe.get_roles()):
		frappe.throw(_("Only sales managers can manage booking platforms"), frappe.PermissionError)


# --------------------------------------------------------------------------
# guest: webhook in, busy feed out
# --------------------------------------------------------------------------


@frappe.whitelist(allow_guest=True, methods=["POST"])
def webhook(token: str | None = None, **kwargs):
	"""Bookings pushed by a platform. Answers fast: platforms retry on slowness."""
	from crm.booking_platforms.sync import handle_webhook

	request = frappe.request
	token = token or frappe.form_dict.get("token")
	body = request.get_data(cache=True) or b""
	headers = {key: value for key, value in request.headers.items()}
	try:
		counts = handle_webhook(token, headers, body, request.url)
	except frappe.PermissionError:
		frappe.local.response.http_status_code = 404
		return {"ok": False}
	except InvalidSignature:
		frappe.local.response.http_status_code = 401
		return {"ok": False, "error": "invalid signature"}
	except (PlatformError, NotSupported) as exc:
		# answer 200: a payload we cannot use will not become usable on retry
		frappe.log_error(str(exc), "Booking platform webhook")
		return {"ok": False, "error": str(exc)[:200]}
	return {"ok": True, **{k: v for k, v in counts.items() if k != "errors"}}


def feed_key(conn, user: str | None) -> str:
	"""Per-professional key: knowing one professional's feed reveals nobody else's."""
	return hashlib.sha256(f"{conn.webhook_token}:{user or '*'}".encode()).hexdigest()[:20]


def busy_feed_url(conn, user: str | None = None) -> str:
	query = f"token={conn.webhook_token}&key={feed_key(conn, user)}"
	if user:
		query += f"&staff={frappe.utils.quote(user)}"
	return get_url(f"/api/method/crm.api.booking_platforms.busy_feed?{query}")


@frappe.whitelist(allow_guest=True, methods=["GET"])
def busy_feed(token: str, key: str, staff: str | None = None):
	"""The professional's (or the whole team's) agenda as anonymous busy blocks.

	No names, services or clients: platforms only need *when*, and a medical or
	beauty agenda is personal data that must not leave the CRM.
	"""
	from werkzeug.wrappers import Response

	name = (
		frappe.db.get_value("CRM Booking Connection", {"webhook_token": token, "enabled": 1})
		if token
		else None
	)
	if not name:
		raise frappe.PermissionError
	conn = frappe.get_doc("CRM Booking Connection", name)
	if not hmac.compare_digest(key or "", feed_key(conn, staff)):
		raise frappe.PermissionError

	users = [staff] if staff else [r.staff for r in conn.mappings if r.map_type == "Staff" and r.staff]
	now = datetime.datetime.now(UTC)
	start, end = now - datetime.timedelta(days=1), now + datetime.timedelta(days=180)
	rows = []
	if users:
		appointment = frappe.qb.DocType("CRM Appointment")
		child = frappe.qb.DocType("CRM Appointment Staff")
		query = (
			frappe.qb.from_(appointment)
			.join(child)
			.on(child.parent == appointment.name)
			.select(appointment.name, appointment.starts_on, appointment.ends_on, appointment.modified)
			.distinct()
			.where(child.user.isin(users))
			.where(appointment.status.isin(("Scheduled", "Confirmed")))
			.where(appointment.starts_on < to_system_naive(end))
			.where(appointment.ends_on > to_system_naive(start))
		)
		# the platform already has its own bookings: echoing them back would double them
		query = query.where(
			(appointment.booking_connection.isnull()) | (appointment.booking_connection != conn.name)
		)
		rows = query.run(as_dict=True)
	return Response(
		render_busy_ics(rows, conn.connection_name),
		content_type="text/calendar; charset=utf-8",
		headers={"Cache-Control": "no-cache, max-age=0"},
	)


def render_busy_ics(rows: list[dict], calendar_name: str) -> str:
	fmt = "%Y%m%dT%H%M%SZ"
	stamp = datetime.datetime.now(UTC).strftime(fmt)
	lines = [
		"BEGIN:VCALENDAR",
		"VERSION:2.0",
		"PRODID:-//CRM//Busy Feed//IT",
		"CALSCALE:GREGORIAN",
		"METHOD:PUBLISH",
		f"X-WR-CALNAME:{calendar_name} (CRM)",
		"X-PUBLISHED-TTL:PT15M",
	]
	for row in rows:
		lines += [
			"BEGIN:VEVENT",
			f"UID:{row['name']}@crm-busy",
			f"DTSTAMP:{stamp}",
			f"DTSTART:{from_system_naive(row['starts_on']).strftime(fmt)}",
			f"DTEND:{from_system_naive(row['ends_on']).strftime(fmt)}",
			"SUMMARY:Occupato",
			"TRANSP:OPAQUE",
			"CLASS:PRIVATE",
			"END:VEVENT",
		]
	lines += ["END:VCALENDAR", ""]
	return "\r\n".join(lines)


# --------------------------------------------------------------------------
# manager: settings screen
# --------------------------------------------------------------------------


@frappe.whitelist()
def list_platforms() -> list[dict]:
	_check_manager()
	return catalog(include_beta=_is_admin())


@frappe.whitelist()
def list_connections() -> list[dict]:
	_check_manager()
	rows = frappe.get_all(
		"CRM Booking Connection",
		fields=[
			"name",
			"connection_name",
			"platform",
			"enabled",
			"status",
			"last_sync",
			"last_webhook",
			"last_error",
			"imported_count",
		],
		order_by="connection_name asc",
	)
	upcoming = dict(
		frappe.get_all(
			"CRM Appointment",
			filters={
				"booking_connection": ["is", "set"],
				"status": ["in", ("Scheduled", "Confirmed")],
				"starts_on": [">=", frappe.utils.now_datetime()],
			},
			fields=["booking_connection", count_field()],
			group_by="booking_connection",
			as_list=True,
		)
	)
	if not _is_admin():
		from crm.booking_platforms import is_stable

		rows = [row for row in rows if is_stable(row.platform)]
	for row in rows:
		row["upcoming"] = upcoming.get(row.name, 0)
		try:
			row["platform_info"] = provider_class(row.platform).describe()
		except KeyError:
			row["platform_info"] = {}
	return rows


@frappe.whitelist()
def get_connection(name: str) -> dict:
	_check_manager()
	_check_connection(name)
	conn = frappe.get_doc("CRM Booking Connection", name)
	data = {field: conn.get(field) for field in PLAIN_FIELDS + FLAG_FIELDS + INT_FIELDS}
	data.update(
		{
			"name": conn.name,
			"status": conn.status,
			"last_sync": conn.last_sync,
			"last_webhook": conn.last_webhook,
			"last_error": conn.last_error,
			"imported_count": conn.imported_count,
			"webhook_url": conn.webhook_url(),
			"busy_feed_url": busy_feed_url(conn),
			"has_secret": {
				field: bool(conn.get_password(field, raise_exception=False)) for field in SECRET_FIELDS
			},
			"mappings": [
				{
					"map_type": row.map_type,
					"external_id": row.external_id,
					"external_name": row.external_name,
					"service": row.service,
					"staff": row.staff,
					"resource": row.resource,
					"busy_feed_url": busy_feed_url(conn, row.staff)
					if row.map_type == "Staff" and row.staff
					else "",
				}
				for row in conn.mappings
			],
			"platform_info": provider_class(conn.platform).describe(),
			"recent": frappe.get_all(
				"CRM Appointment",
				filters={"booking_connection": conn.name},
				fields=["name", "title", "status", "starts_on", "conflict_note", "creation"],
				order_by="creation desc",
				limit=10,
			),
		}
	)
	return data


@frappe.whitelist(methods=["POST"])
def save_connection(connection: str | dict, name: str | None = None) -> dict:
	_check_manager()
	payload = frappe.parse_json(connection) if isinstance(connection, str) else connection
	if name:
		_check_connection(name)
	_check_platform(payload.get("platform"))
	doc = frappe.get_doc("CRM Booking Connection", name) if name else frappe.new_doc("CRM Booking Connection")
	for field in PLAIN_FIELDS:
		if field in payload:
			doc.set(field, payload.get(field) or None)
	for field in FLAG_FIELDS:
		if field in payload:
			doc.set(field, cint(payload.get(field)))
	for field in INT_FIELDS:
		if field in payload:
			doc.set(field, cint(payload.get(field)))
	for field in SECRET_FIELDS:
		value = payload.get(field)
		# an untouched secret comes back empty: keep what is stored
		if value:
			doc.set(field, value)
	if "mappings" in payload:
		doc.set(
			"mappings",
			[
				{
					"map_type": row.get("map_type") or "Service",
					"external_id": str(row.get("external_id") or "").strip(),
					"external_name": row.get("external_name"),
					"service": row.get("service") or None,
					"staff": row.get("staff") or None,
					"resource": row.get("resource") or None,
				}
				for row in payload.get("mappings") or []
				if row.get("external_id")
			],
		)
	doc.save() if name else doc.insert()
	return get_connection(doc.name)


@frappe.whitelist(methods=["POST"])
def delete_connection(name: str) -> None:
	_check_manager()
	_check_connection(name)
	frappe.delete_doc("CRM Booking Connection", name)


@frappe.whitelist(methods=["POST"])
def test_connection(name: str) -> dict:
	"""Prove the credentials, and set up what the platform lets us set up from here."""
	_check_manager()
	_check_connection(name)
	conn = frappe.get_doc("CRM Booking Connection", name)
	provider = get_provider(conn)
	missing = provider.missing_fields()
	if missing:
		conn.db_set({"status": "Not configured", "last_error": _("Missing: {0}").format(", ".join(missing))})
		return {"ok": False, "message": _("Fill in: {0}").format(", ".join(missing))}
	notes = []
	try:
		notes.append(provider.test())
		if hasattr(provider, "ensure_webhooks"):
			provider.ensure_webhooks(conn.webhook_url())
			notes.append(_("webhooks registered"))
		if cint(conn.push_blocks) and hasattr(provider, "register_busy_feed"):
			provider.register_busy_feed(busy_feed_url(conn))
			notes.append(_("busy feed registered"))
	except Exception as exc:
		conn.db_set({"status": "Error", "last_error": str(exc)[:1000]})
		return {"ok": False, "message": str(exc)[:500]}
	conn.db_set({"status": "Connected", "last_error": None})
	return {"ok": True, "message": " · ".join(n for n in notes if n)}


@frappe.whitelist(methods=["POST"])
def sync_now(name: str) -> dict:
	_check_manager()
	_check_connection(name)
	from crm.booking_platforms.sync import sync_connection

	return sync_connection(name)


@frappe.whitelist()
def fetch_catalog(name: str) -> list[dict]:
	"""The platform's services and staff, for the mapping table."""
	_check_manager()
	_check_connection(name)
	conn = frappe.get_doc("CRM Booking Connection", name)
	try:
		items = get_provider(conn).fetch_catalog()
	except NotSupported:
		return []
	except PlatformError as exc:
		frappe.throw(str(exc))
	return [{"id": i.id, "name": i.name, "kind": i.kind} for i in items]
