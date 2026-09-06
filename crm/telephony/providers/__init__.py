# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The providers this site knows about.

Adding a carrier is one entry here plus one module implementing
``TelephonyProvider``. Nothing else in the CRM needs to learn its name.
"""

from __future__ import annotations

import frappe

from crm.telephony.providers.base import (  # re-exported so callers import one place
	Announcement,
	CallInstruction,
	ProviderNotSupported,
	TelephonyProvider,
)

REGISTRY: dict[str, str] = {
	"twilio": "crm.telephony.providers.twilio.TwilioProvider",
	"exotel": "crm.telephony.providers.exotel.ExotelProvider",
}


def register(name: str, dotted_path: str) -> None:
	"""Add a provider at runtime — for a site-specific carrier in another app."""
	REGISTRY[name] = dotted_path


def get(name: str) -> TelephonyProvider:
	"""One provider by name, built once per request."""
	if name not in REGISTRY:
		frappe.throw(frappe._("Unknown telephony provider: {0}").format(name))

	cache = getattr(frappe.local, "crm_telephony_providers", None)
	if cache is None:
		cache = frappe.local.crm_telephony_providers = {}
	if name not in cache:
		cache[name] = frappe.get_attr(REGISTRY[name])()
	return cache[name]


def all_providers() -> list[TelephonyProvider]:
	return [get(name) for name in REGISTRY]


def enabled() -> list[TelephonyProvider]:
	return [provider for provider in all_providers() if provider.is_enabled()]


def for_medium(medium: str | None) -> TelephonyProvider | None:
	"""The provider behind a ``CRM Call Log.telephony_medium`` value.

	Returns ``None`` for a manual or unrecognised medium — a call somebody logged
	by hand has no carrier behind it.
	"""
	if not medium:
		return None
	for provider in all_providers():
		if provider.label == medium or provider.name == medium.lower():
			return provider
	return None


def answering_capable() -> list[TelephonyProvider]:
	"""Providers the answering service can actually run on."""
	return [p for p in enabled() if p.controls_call_flow]
