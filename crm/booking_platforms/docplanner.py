# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""MioDottore — the Docplanner Integrations API (also Doctoralia, ZnanyLekarz, jameda).

Partner-only: the practice's software vendor applies as a certified integrator,
gets sandbox credentials and passes Docplanner's acceptance tests. With those
credentials this connector:

* reads bookings per doctor and address (``…/addresses/{a}/bookings``),
* receives push notifications (``slot-booked``, ``booking-canceled``,
  ``booking-moved``, ``booking-confirmed``…),
* cancels bookings, and blocks a doctor's time with *breaks* when the CRM
  books them elsewhere.

Docplanner nests everything as facility → doctor → address (a doctor's agenda
at one location), so a booking's id here is ``doctor/address/booking``: that is
the path every follow-up call needs.

Reference: https://integrations.docplanner.com/docs/ · guide:
https://integrations.docplanner.com/guide/
"""

from __future__ import annotations

import base64

from crm.booking_platforms.base import (
	STATUS_CANCELLED,
	STATUS_CONFIRMED,
	STATUS_PENDING,
	BookingPlatform,
	CatalogItem,
	ExternalBooking,
	InvalidSignature,
	PlatformError,
	header,
	join_name,
	load_json,
	safe_equal,
)

CANCEL_EVENTS = {"booking-canceled", "booking-cancelled"}
BOOKING_EVENTS = {"slot-booked", "booking-moved", "booking-confirmed", "presence-marked"} | CANCEL_EVENTS


def booking_from_docplanner(item: dict, doctor_id: str, address_id: str, event: str = "") -> ExternalBooking:
	"""A Docplanner booking object → ExternalBooking (pure)."""
	patient = item.get("patient") or {}
	service = item.get("address_service") or {}
	status_text = str(item.get("status") or "").lower()
	if event in CANCEL_EVENTS or item.get("canceled_at") or "cancel" in status_text:
		status = STATUS_CANCELLED
	elif status_text in ("pending", "waiting", "to_confirm"):
		status = STATUS_PENDING
	else:
		status = STATUS_CONFIRMED
	return ExternalBooking(
		external_id=f"{doctor_id}/{address_id}/{item.get('id')}",
		start=item.get("start_at"),
		end=item.get("end_at"),
		status=status,
		service_ref=str(service.get("id") or ""),
		service_name=service.get("name") or "",
		staff_ref=str(doctor_id or ""),
		customer_name=join_name(patient.get("name"), patient.get("surname")),
		email=patient.get("email") or "",
		phone=patient.get("phone") or "",
		notes=item.get("comment") or "",
		price=float(service.get("price") or 0),
		currency="EUR",
		raw=item,
	)


def bookings_from_notification(payload: dict) -> list[ExternalBooking]:
	"""A push notification → the booking it carries, if it carries one."""
	event = str(payload.get("name") or "")
	if event not in BOOKING_EVENTS:
		return []
	data = payload.get("data") or {}
	doctor = str((data.get("doctor") or {}).get("id") or "")
	address = str((data.get("address") or {}).get("id") or "")
	# the key under data differs per event (visit_booking, booking…): take the one
	# that looks like a booking rather than guess its name
	for value in data.values():
		if isinstance(value, dict) and value.get("id") and value.get("start_at"):
			return [booking_from_docplanner(value, doctor, address, event)]
	return []


class Docplanner(BookingPlatform):
	key = "docplanner"
	label = "MioDottore (Docplanner)"
	sector = "medical"
	website = "https://www.miodottore.it"
	docs_url = "https://integrations.docplanner.com/docs/"
	api_access = "partner"
	capabilities = frozenset({"pull", "webhook", "catalog", "cancel", "block"})
	required_fields = ("account_id", "client_id", "client_secret")
	fields = ("api_base_url", "account_id", "client_id", "client_secret", "webhook_secret")
	default_base_url = "https://www.miodottore.it"
	setup_help = (
		"MioDottore opens its API only to certified software vendors: request "
		"integration access at integrations.docplanner.com (sandbox + acceptance tests). "
		"Enter the facility ID as Account ID and the OAuth client ID/secret. Map every "
		"MioDottore doctor (Staff) and address service (Service). Ask your integration "
		"specialist to send push notifications to the webhook address; if they add an "
		"API-key header, put its value in the signing secret. Without partner access, "
		"use the 'Notification email' connector on the MioDottore booking emails instead."
	)

	# -- auth -------------------------------------------------------------------

	def _login(self):
		import requests

		basic = base64.b64encode(
			f"{self.value('client_id')}:{self.secret('client_secret')}".encode()
		).decode()
		try:
			response = requests.post(
				f"{self.base_url}/oauth/v2/token",
				data={"grant_type": "client_credentials", "scope": "integration"},
				headers={"Authorization": f"Basic {basic}"},
				timeout=self.timeout,
			)
		except requests.RequestException as exc:
			raise PlatformError(f"MioDottore: {exc.__class__.__name__}") from exc
		if not response.ok:
			raise PlatformError(f"MioDottore login refused (HTTP {response.status_code})")
		data = response.json()
		return data["access_token"], data.get("expires_in") or 86400

	def auth_headers(self):
		return {"Authorization": f"Bearer {self.cached_token(self._login)}"}

	@property
	def api(self) -> str:
		return f"{self.base_url}/api/v3/integration/facilities/{self.value('account_id')}"

	# -- structure --------------------------------------------------------------

	def doctors(self) -> list[dict]:
		data = self.request("GET", f"{self.api}/doctors") or {}
		return data.get("_items") or []

	def addresses(self, doctor_id: str) -> list[dict]:
		data = self.request("GET", f"{self.api}/doctors/{doctor_id}/addresses") or {}
		return data.get("_items") or []

	def agendas(self):
		"""Every (doctor, address) pair of the facility."""
		for doctor in self.doctors():
			for address in self.addresses(doctor["id"]):
				yield str(doctor["id"]), str(address["id"])

	# -- operations -------------------------------------------------------------

	def fetch_bookings(self, since, until):
		out = []
		for doctor, address in self.agendas():
			page = 1
			while True:
				data = (
					self.request(
						"GET",
						f"{self.api}/doctors/{doctor}/addresses/{address}/bookings",
						params={
							"start": since.isoformat(timespec="seconds"),
							"end": until.isoformat(timespec="seconds"),
							"page": page,
							"limit": 100,
							"with": "booking.patient,booking.address_service",
						},
					)
					or {}
				)
				out.extend(
					booking_from_docplanner(item, doctor, address) for item in data.get("_items") or []
				)
				if page >= int(data.get("pages") or 1):
					break
				page += 1
		return out

	def parse_webhook(self, headers, body, url=""):
		secret = self.secret("webhook_secret")
		if secret:
			given = header(headers, "X-Api-Key") or header(headers, "Authorization").removeprefix("Bearer ")
			if not safe_equal(given, secret):
				raise InvalidSignature("MioDottore notification without the agreed API key")
		payload = load_json(body)
		items = payload if isinstance(payload, list) else [payload]
		out = []
		for item in items:
			out.extend(bookings_from_notification(item or {}))
		return out

	def pull_notifications(self) -> list[ExternalBooking]:
		"""The pull-mode queue (messages live 72 h) — a safety net for missed pushes."""
		data = self.request(
			"GET", f"{self.base_url}/api/v3/integration/notifications/multiple", params={"limit": 100}
		)
		items = data if isinstance(data, list) else (data or {}).get("_items") or []
		out = []
		for item in items:
			out.extend(bookings_from_notification(item))
		return out

	def fetch_catalog(self):
		items = []
		for doctor in self.doctors():
			items.append(
				CatalogItem(str(doctor["id"]), join_name(doctor.get("name"), doctor.get("surname")), "Staff")
			)
			for address in self.addresses(doctor["id"]):
				data = (
					self.request(
						"GET", f"{self.api}/doctors/{doctor['id']}/addresses/{address['id']}/services"
					)
					or {}
				)
				for service in data.get("_items") or []:
					items.append(CatalogItem(str(service["id"]), service.get("name") or "", "Service"))
		return items

	def _split(self, external_id: str) -> tuple[str, str, str]:
		parts = external_id.split("/")
		if len(parts) != 3:
			raise PlatformError(f"Not a MioDottore booking id: {external_id}")
		return parts[0], parts[1], parts[2]

	def cancel_booking(self, external_id, reason=""):
		doctor, address, booking = self._split(external_id)
		self.request("DELETE", f"{self.api}/doctors/{doctor}/addresses/{address}/bookings/{booking}")

	def block_time(self, staff_ref, start, end, reason=""):
		addresses = self.addresses(staff_ref)
		if not addresses:
			raise PlatformError(f"MioDottore doctor {staff_ref} has no address")
		address = str(addresses[0]["id"])
		data = self.request(
			"POST",
			f"{self.api}/doctors/{staff_ref}/addresses/{address}/breaks",
			json={
				"since": start.isoformat(timespec="seconds"),
				"till": end.isoformat(timespec="seconds"),
				"description": reason or "CRM",
				"apply_on_coupled_addresses": True,
			},
		)
		block_id = (data or {}).get("id") if isinstance(data, dict) else ""
		return f"{staff_ref}/{address}/{block_id or ''}"

	def unblock_time(self, block_id, staff_ref=""):
		doctor, address, break_id = self._split(block_id)
		if not break_id:
			raise PlatformError("The break id was not returned when it was created")
		self.request("DELETE", f"{self.api}/doctors/{doctor}/addresses/{address}/breaks/{break_id}")
