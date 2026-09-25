# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Settings-modal API for the Google Calendar connection."""

import frappe
from frappe import _

from crm.integrations.google.oauth import client_id, client_secret, is_managed


@frappe.whitelist()
def get_status() -> dict:
	"""State of the current user's calendar link, for the Connect button, and how the
	copy of their appointments into Google is doing."""
	name = frappe.db.get_value("Google Calendar", {"user": frappe.session.user})
	connected = False
	if name:
		try:
			connected = bool(
				frappe.get_doc("Google Calendar", name).get_password("refresh_token", raise_exception=False)
			)
		except Exception:
			connected = False

	return {
		"can_connect": bool(client_id() and client_secret()),
		"managed": is_managed(),
		"name": name,
		"connected": connected,
		"sync": _sync_status(name) if connected else None,
	}


def _sync_status(name: str) -> dict:
	from crm.integrations.google.sync import calendar_title, is_ready

	fields = ["enable", "push_to_google_calendar"]
	if is_ready():
		fields += ["crm_calendar_id", "crm_last_sync", "crm_sync_error", "crm_synced_events"]
	row = frappe.db.get_value("Google Calendar", name, fields, as_dict=True) or {}
	return {
		"active": bool(row.get("enable") and row.get("push_to_google_calendar")),
		"calendar": calendar_title(),
		"calendar_ready": bool(row.get("crm_calendar_id")),
		"last_sync": row.get("crm_last_sync"),
		"error": row.get("crm_sync_error") or "",
		"events": row.get("crm_synced_events") or 0,
	}


@frappe.whitelist(methods=["POST"])
def sync_now() -> dict:
	"""Copy the user's appointments into Google now, not at the next hourly pass."""
	from crm.integrations.google.sync import account_of, queue_sync

	if not account_of(frappe.session.user):
		frappe.throw(_("Connect Google Calendar first"))
	queue_sync(frappe.session.user)
	return get_status()


@frappe.whitelist(methods=["POST"])
def disconnect() -> dict:
	"""Unlink this user's calendar. The events already in Google stay there."""
	from crm.integrations.google.oauth import sync_google_settings
	from crm.integrations.google.sync import forget_token

	name = frappe.db.get_value("Google Calendar", {"user": frappe.session.user})
	if not name:
		return get_status()
	doc = frappe.get_doc("Google Calendar", name)
	if doc.user != frappe.session.user:
		frappe.throw(_("This calendar belongs to another user"), frappe.PermissionError)
	# the framework refuses to save the record while `Google Settings` is off
	sync_google_settings()
	doc.refresh_token = ""
	doc.enable = 0
	doc.push_to_google_calendar = 0
	doc.save(ignore_permissions=True)
	forget_token(name)
	return get_status()
