# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from crm.utils.attribution import get_domain


class CRMTrackingSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		allowed_origins: DF.SmallText | None
		anonymize_ip: DF.Check
		enabled: DF.Check
		exclude_bots: DF.Check
		excluded_ips: DF.SmallText | None
		require_consent: DF.Check
		respect_do_not_track: DF.Check
		retention_days: DF.Int
		session_timeout_minutes: DF.Int
		store_ip_address: DF.Check
		track_anonymous: DF.Check
		visitor_cookie_days: DF.Int
	# end: auto-generated types

	def validate(self):
		self.session_timeout_minutes = max(1, min(self.session_timeout_minutes or 30, 24 * 60))
		self.visitor_cookie_days = max(1, min(self.visitor_cookie_days or 365, 400))
		self.retention_days = max(0, self.retention_days or 0)

	# -- policy ------------------------------------------------------------

	@property
	def origins(self) -> list[str]:
		"""Allowed origins as bare hostnames — the entry is written as a URL but
		compared against the request's `Origin` host."""
		return [d for d in (get_domain(line) for line in _lines(self.allowed_origins)) if d]

	@property
	def excluded_ip_list(self) -> list[str]:
		return _lines(self.excluded_ips)

	def accepts_origin(self, origin: str | None) -> bool:
		"""Whether a browser at `origin` may post to the collect endpoint.

		An empty allow-list accepts everything: a site that has just pasted the
		snippet should see data before it has been told to list its domains.
		"""
		allowed = self.origins
		if not allowed:
			return True
		host = get_domain(origin)
		if not host:
			return False
		return any(host == a or host.endswith("." + a) for a in allowed)

	def accepts_ip(self, ip: str | None) -> bool:
		"""Whether traffic from `ip` counts. An unknown address is accepted — the
		exclusion list is for silencing known offices, not for demanding an IP."""
		return (ip or "") not in self.excluded_ip_list


def _lines(value: str | None) -> list[str]:
	return [line.strip() for line in (value or "").splitlines() if line.strip()]


def get_tracking_settings() -> "CRMTrackingSettings":
	"""The settings document. Read on every collect call, so it goes through the
	document cache rather than costing a query per beacon."""
	return frappe.get_cached_doc("CRM Tracking Settings")
