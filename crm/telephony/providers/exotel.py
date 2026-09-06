# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Exotel, which works the other way round.

Its call flow is built from applets in Exotel's own dashboard; the CRM is only
told what happened afterwards. So the answering service cannot run on it —
``controls_call_flow`` is False and the call-control methods stay unimplemented,
which is the honest answer rather than a broken one.
"""

from __future__ import annotations

import frappe

from crm.telephony.providers.base import TelephonyProvider


class ExotelProvider(TelephonyProvider):
	name = "exotel"
	label = "Exotel"
	agent_number_field = "exotel_number"
	controls_call_flow = False
	rings_browser = False
	places_calls_server_side = True

	def is_enabled(self) -> bool:
		return bool(frappe.db.get_single_value("CRM Exotel Settings", "enabled"))

	def recording_credentials(self) -> tuple | None:
		settings = frappe.get_single("CRM Exotel Settings")
		token = settings.get_password("api_token", raise_exception=False)
		return (settings.api_key, token) if settings.api_key and token else None

	def place_call(self, to_number: str, from_number: str | None = None) -> dict:
		from crm.integrations.exotel.handler import make_a_call

		return make_a_call(to_number=to_number, from_number=from_number)
