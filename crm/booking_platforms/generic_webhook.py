# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""A webhook anybody can send: Zapier, Make, n8n, an email parser, a website.

For platforms with no API and no calendar feed, the booking notification email
still exists. Zapier's *Email Parser*, Make's *Mailhook* or n8n turn it into
JSON and post it here; so does any in-house system. The payload shape is free:
the connection's *Payload Field Map* says where each field lives, with dot
paths, and falls back to sensible names (``id``, ``start``, ``end``…).

When a signing secret is set, the call must carry an HMAC-SHA256 of the raw
body (hex) in ``X-Signature`` or ``X-Hub-Signature-256: sha256=…``; otherwise
the unguessable token in the URL is the only credential.
"""

from __future__ import annotations

import datetime
import json

from crm.booking_platforms.base import (
	STATUS_CANCELLED,
	STATUS_COMPLETED,
	STATUS_CONFIRMED,
	STATUS_NO_SHOW,
	STATUS_PENDING,
	BookingPlatform,
	ExternalBooking,
	InvalidSignature,
	PlatformError,
	dig,
	header,
	hmac_hex,
	join_name,
	load_json,
	safe_equal,
)

DEFAULT_MAP = {
	"list": "",
	"id": "id|booking_id|appointment_id|uid",
	"start": "start|start_time|starts_at|start_at|datetime",
	"end": "end|end_time|ends_at|end_at",
	"duration": "duration|duration_minutes",
	"status": "status|event|action|type",
	"customer_name": "customer.name|client.name|name|customer_name|full_name",
	"first_name": "customer.first_name|client.first_name|first_name",
	"last_name": "customer.last_name|client.last_name|last_name",
	"email": "customer.email|client.email|email",
	"phone": "customer.phone|client.phone|phone|mobile",
	"service": "service.id|service_id",
	"service_name": "service.name|service_name|service",
	"staff": "staff.id|staff_id|employee_id|provider_id",
	"staff_name": "staff.name|staff_name|employee|provider",
	"notes": "notes|note|comment|message",
	"price": "price|amount|total",
	"currency": "currency",
	"url": "url|link",
}

STATUS_WORDS = {
	STATUS_CANCELLED: ("cancel", "annull", "delete", "declin", "reject", "rifiut", "removed", "disdett"),
	STATUS_PENDING: ("pending", "tentative", "request", "attesa", "unconfirmed"),
	STATUS_NO_SHOW: ("no_show", "noshow", "no-show", "missed", "assente"),
	STATUS_COMPLETED: ("complet", "done", "attended", "checked_out", "finished"),
}


def normalise_status(value, overrides: dict | None = None) -> str:
	text = str(value or "").strip().lower()
	if overrides and text in overrides:
		return overrides[text]
	for status, words in STATUS_WORDS.items():
		if any(word in text for word in words):
			return status
	return STATUS_CONFIRMED


def pick(item: dict, paths: str):
	"""First non-empty value among ``a.b|c|d``."""
	for path in (paths or "").split("|"):
		value = dig(item, path.strip())
		if value not in (None, "", [], {}):
			return value
	return None


def payload_to_bookings(payload, field_map: dict | None = None) -> list[ExternalBooking]:
	mapping = {**DEFAULT_MAP, **(field_map or {})}
	overrides = {str(k).lower(): v for k, v in (mapping.get("status_map") or {}).items()}
	items = dig(payload, mapping["list"]) if mapping.get("list") else payload
	if isinstance(items, dict):
		# Zapier/Make sometimes wrap a single record: {"data": {...}}
		items = [items.get("data") if isinstance(items.get("data"), dict) and "id" not in items else items]
	if not isinstance(items, list):
		raise PlatformError("Unexpected webhook payload")
	out = []
	for item in items:
		if not isinstance(item, dict):
			continue
		external_id = pick(item, mapping["id"])
		start = pick(item, mapping["start"])
		if not external_id or not start:
			continue
		end = pick(item, mapping["end"])
		if not end:
			minutes = pick(item, mapping["duration"])
			from crm.booking_platforms.base import as_utc

			end = as_utc(start) + datetime.timedelta(minutes=int(float(minutes or 30)))
		price = pick(item, mapping["price"])
		try:
			price = float(price or 0)
		except (TypeError, ValueError):
			price = 0.0
		out.append(
			ExternalBooking(
				external_id=str(external_id),
				start=start,
				end=end,
				status=normalise_status(pick(item, mapping["status"]), overrides),
				service_ref=str(pick(item, mapping["service"]) or ""),
				service_name=str(pick(item, mapping["service_name"]) or ""),
				staff_ref=str(pick(item, mapping["staff"]) or ""),
				staff_name=str(pick(item, mapping["staff_name"]) or ""),
				customer_name=str(
					pick(item, mapping["customer_name"])
					or join_name(pick(item, mapping["first_name"]), pick(item, mapping["last_name"]))
				),
				email=str(pick(item, mapping["email"]) or ""),
				phone=str(pick(item, mapping["phone"]) or ""),
				notes=str(pick(item, mapping["notes"]) or ""),
				price=price,
				currency=str(pick(item, mapping["currency"]) or ""),
				url=str(pick(item, mapping["url"]) or ""),
				raw=item,
			)
		)
	return out


def verify_generic_signature(secret: str, headers: dict, body: bytes) -> None:
	if not secret:
		return
	expected = hmac_hex(secret, body)
	given = header(headers, "X-Signature") or header(headers, "X-Hub-Signature-256")
	given = given.split("=", 1)[1] if given.lower().startswith("sha256=") else given
	if not given or not safe_equal(given, expected):
		raise InvalidSignature("Webhook signature does not match")


class GenericWebhook(BookingPlatform):
	key = "webhook"
	label = "Generic webhook (Zapier, Make, n8n)"
	sector = "general"
	api_access = "none"
	# the payload shape is ours to define: nothing on the other side can drift
	stability = "stable"
	capabilities = frozenset({"webhook"})
	fields = ("webhook_secret", "field_map")
	setup_help = (
		"Point Zapier, Make, n8n or any system at the webhook address below, sending one "
		"booking (or a list) as JSON. Use the field map to tell the CRM where the id, start, "
		"end, status and client live in your payload. Tip: for platforms that only send "
		"emails, forward the booking email to a Zapier Email Parser or Make Mailhook."
	)

	def field_map(self) -> dict:
		raw = self.value("field_map")
		if not raw:
			return {}
		try:
			parsed = json.loads(raw)
		except ValueError:
			raise PlatformError("The payload field map is not valid JSON")
		return parsed if isinstance(parsed, dict) else {}

	def parse_webhook(self, headers, body, url=""):
		verify_generic_signature(self.secret("webhook_secret"), headers, body)
		return payload_to_bookings(load_json(body), self.field_map())

	def test(self):
		return "Waiting for the first webhook"
