# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Which parts of the product this site actually uses.

A widget about WhatsApp on a site without WhatsApp is a zero that means nothing,
and a dashboard full of such zeros hides the numbers that do mean something. So
every widget names the features it needs, and the catalogue and the ready-made
dashboards only offer what the site can answer.

Each check is cheap (a single flag or an ``exists``) and computed once per
request. A check that fails — a doctype missing because an optional app is not
installed — counts as "not in use", never as an error on the dashboard.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import frappe
from frappe import _lt
from frappe.utils.caching import request_cache


@dataclass(frozen=True)
class Feature:
	key: str
	label: Any
	hint: Any
	# the Settings page (its untranslated label) where it is switched on
	settings: str | None
	check: Callable[[], bool]


def _whatsapp() -> bool:
	from crm.api.whatsapp import is_whatsapp_enabled

	return bool(is_whatsapp_enabled())


def _sms() -> bool:
	from crm.api.sms import is_sms_enabled

	return bool(is_sms_enabled())


def _calls() -> bool:
	from crm.telephony.providers import enabled

	return bool(enabled())


def _agenda() -> bool:
	return bool(frappe.db.exists("CRM Service", {"enabled": 1}) or frappe.db.exists("CRM Appointment"))


def _online_booking() -> bool:
	if not frappe.db.get_single_value("CRM Scheduling Settings", "online_booking_enabled"):
		return False
	return bool(frappe.db.exists("CRM Service", {"enabled": 1, "bookable_online": 1}))


def _booking_platforms() -> bool:
	return bool(frappe.db.exists("CRM Booking Connection", {"enabled": 1}))


def _tracking() -> bool:
	return bool(frappe.db.get_single_value("CRM Tracking Settings", "enabled"))


def _meta_leads() -> bool:
	# a page importing leads today, or leads imported before it was switched off
	return bool(
		frappe.db.exists("Facebook Page", {"sync_enabled": 1})
		or frappe.db.exists("CRM Lead", {"facebook_lead_id": ("is", "set")})
	)


def _meta_ads() -> bool:
	return bool(
		frappe.db.exists("Facebook Ad Account", {"sync_enabled": 1})
		or frappe.db.exists("Facebook Ad Insight")
	)


def _meta_conversions() -> bool:
	from crm.integrations.meta.conversions import enabled

	return bool(enabled())


def _automations() -> bool:
	return bool(frappe.db.exists("CRM Automation"))


def _social() -> bool:
	return bool(frappe.db.exists("CRM Social Account", {"enabled": 1}))


def _tracked_links() -> bool:
	return bool(frappe.db.exists("CRM Tracked Link"))


def _web_forms() -> bool:
	return bool(frappe.db.exists("Web Form", {"module": "FCRM", "published": 1}))


def _sla() -> bool:
	return bool(frappe.db.exists("CRM Service Level Agreement", {"enabled": 1}))


def _website() -> bool:
	return bool(frappe.db.get_single_value("CRM Website Settings", "enabled"))


FEATURES: dict[str, Feature] = {
	feature.key: feature
	for feature in (
		Feature(
			"whatsapp",
			_lt("WhatsApp"),
			_lt("Connect a WhatsApp number to see these"),
			"WhatsApp",
			_whatsapp,
		),
		Feature("sms", _lt("SMS"), _lt("Turn on Twilio to send and receive SMS"), "Telephony", _sms),
		Feature("calls", _lt("Calls"), _lt("Connect a telephony provider to see calls"), "Telephony", _calls),
		Feature(
			"agenda", _lt("Agenda"), _lt("Add your services to start using the agenda"), "Services", _agenda
		),
		Feature(
			"online_booking",
			_lt("Online booking"),
			_lt("Open online booking for at least one service"),
			"Online booking",
			_online_booking,
		),
		Feature(
			"booking_platforms",
			_lt("Booking platforms"),
			_lt("Connect a booking platform such as MioDottore or Treatwell"),
			"Booking platforms",
			_booking_platforms,
		),
		Feature(
			"tracking",
			_lt("Lead tracking"),
			_lt("Turn on lead tracking to see where visitors come from"),
			"Lead Tracking",
			_tracking,
		),
		Feature(
			"tracked_links",
			_lt("Tracked links"),
			_lt("Create a tracked link to count its clicks"),
			"Tracked Links",
			_tracked_links,
		),
		Feature(
			"web_forms",
			_lt("Forms"),
			_lt("Publish a form to collect requests from your website"),
			"Forms",
			_web_forms,
		),
		Feature(
			"meta_leads",
			_lt("Meta Lead Ads"),
			_lt("Connect Facebook and choose the pages that send you leads"),
			"Lead forms",
			_meta_leads,
		),
		Feature(
			"meta_ads",
			_lt("Ad spend"),
			_lt("Choose the ad accounts to read the spend from"),
			"Ad performance",
			_meta_ads,
		),
		Feature(
			"meta_conversions",
			_lt("Lead quality"),
			_lt("Turn on the Conversions API to send your sales back to Meta"),
			"Lead quality",
			_meta_conversions,
		),
		Feature(
			"automations",
			_lt("Automations"),
			_lt("Create an automation to see how it performs"),
			None,
			_automations,
		),
		Feature(
			"social",
			_lt("Social planner"),
			_lt("Connect your Facebook and Instagram profiles"),
			"Social profiles",
			_social,
		),
		Feature(
			"sla",
			_lt("Service level agreements"),
			_lt("Set up an SLA policy to measure response times"),
			"SLA Policies",
			_sla,
		),
		Feature("website", _lt("Website"), _lt("Turn on the website"), "Website", _website),
	)
}


@request_cache
def active() -> frozenset[str]:
	"""The features this site uses right now."""
	on = set()
	for key, feature in FEATURES.items():
		try:
			if feature.check():
				on.add(key)
		except Exception:
			# an optional app missing is "not in use", never a broken dashboard
			continue
	return frozenset(on)


def forget() -> None:
	"""Check again on the next call: a feature was switched on or off during this request."""
	cache = getattr(frappe.local, "request_cache", None)
	if cache is not None:
		cache.pop(active.__wrapped__, None)


def missing(requires: tuple[str, ...]) -> list[str]:
	"""The features in ``requires`` the site does not use."""
	on = active()
	return [key for key in requires if key not in on]


def describe(key: str) -> dict[str, Any]:
	feature = FEATURES.get(key)
	if not feature:
		return {"key": key, "label": key, "hint": "", "settings": None}
	return {
		"key": key,
		"label": str(feature.label),
		"hint": str(feature.hint),
		"settings": feature.settings,
	}
