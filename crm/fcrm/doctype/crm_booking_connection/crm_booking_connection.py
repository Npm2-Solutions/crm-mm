# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CRMBookingConnection(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.fcrm.doctype.crm_booking_connection_map.crm_booking_connection_map import (
			CRMBookingConnectionMap,
		)

		access_token: DF.Password | None
		account_id: DF.Data | None
		api_base_url: DF.Data | None
		api_key: DF.Password | None
		client_id: DF.Data | None
		client_secret: DF.Password | None
		connection_name: DF.Data
		create_leads: DF.Check
		default_service: DF.Link | None
		default_staff: DF.Link | None
		enabled: DF.Check
		extra_param: DF.Data | None
		field_map: DF.Code | None
		ical_url: DF.SmallText | None
		import_bookings: DF.Check
		imported_count: DF.Int
		imported_status: DF.Literal["Confirmed", "Scheduled"]
		inbound_email_account: DF.Link | None
		last_error: DF.SmallText | None
		last_sync: DF.Datetime | None
		last_webhook: DF.Datetime | None
		lookback_days: DF.Int
		mappings: DF.Table[CRMBookingConnectionMap]
		platform: DF.Literal[
			"MioDottore (Docplanner)",
			"MioDottore (email)",
			"Treatwell / Uala",
			"Fresha",
			"Booksy",
			"Elty",
			"iDoctors",
			"Doctolib (Dottori.it)",
			"Top Doctors",
			"Pazienti.it",
			"SimplyBook.me",
			"Calendly",
			"Cal.com",
			"Acuity Scheduling",
			"Microsoft Bookings",
			"TIMIFY",
			"Setmore",
			"Easy!Appointments",
			"iCal feed",
			"Notification email (any platform)",
			"Generic webhook (Zapier, Make, n8n)",
		]
		push_blocks: DF.Check
		push_cancellations: DF.Check
		refresh_token: DF.Password | None
		sender_filter: DF.Data | None
		status: DF.Literal["Not configured", "Connected", "Error"]
		sync_window_days: DF.Int
		tenant_id: DF.Data | None
		token_expires_on: DF.Datetime | None
		webhook_secret: DF.Password | None
		webhook_token: DF.Data | None
	# end: auto-generated types

	def validate(self):
		if not self.webhook_token:
			self.webhook_token = frappe.generate_hash(length=32)
		if self.sync_window_days is not None and self.sync_window_days > 366:
			self.sync_window_days = 366
		self.validate_mappings()
		self.validate_field_map()

	def validate_mappings(self):
		seen = set()
		for row in self.mappings:
			key = (row.map_type, (row.external_id or "").strip())
			if key in seen:
				frappe.throw(
					_("Row {0}: {1} {2} is mapped twice").format(row.idx, _(row.map_type), row.external_id)
				)
			seen.add(key)
			target = {"Service": row.service, "Staff": row.staff, "Resource": row.resource}.get(row.map_type)
			if not target:
				frappe.throw(
					_("Row {0}: pick what {1} corresponds to in the CRM").format(row.idx, row.external_id)
				)

	def validate_field_map(self):
		if not self.field_map:
			return
		try:
			parsed = frappe.parse_json(self.field_map)
		except Exception:
			parsed = None
		if not isinstance(parsed, dict):
			frappe.throw(_("The payload field map must be a JSON object"))

	def provider(self):
		from crm.booking_platforms import get_provider

		return get_provider(self)

	def webhook_url(self) -> str:
		return frappe.utils.get_url(
			f"/api/method/crm.api.booking_platforms.webhook?token={self.webhook_token}"
		)

	def store_token(self, token: str, expires_at) -> None:
		"""Keep a fresh platform access token without touching ``modified``."""
		from frappe.utils.password import set_encrypted_password

		from crm.scheduling.timeutils import to_system_naive

		set_encrypted_password(self.doctype, self.name, token, "access_token")
		self.db_set("token_expires_on", to_system_naive(expires_at), update_modified=False)
		self.access_token = token
		self.token_expires_on = to_system_naive(expires_at)
