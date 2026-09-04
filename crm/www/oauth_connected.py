# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Landing page for the end of an OAuth login, shown inside the popup.

Every connect button (Facebook, Google) opens a popup so the CRM behind it
never navigates away and keeps its state. This is what the provider's redirect
finally lands on: it tells the opener how it went and closes itself. Opened as
a normal tab instead — popup blocked, link pasted by hand — it falls back to
the settings page, which is what used to happen for every login.
"""

import frappe

no_cache = 1

# provider -> settings page it belongs to. The label is matched untranslated by
# the settings modal, which compares against the item's `key`.
SETTINGS_PAGE = {
	"meta": "Meta connection",
	"google": "Google Calendar",
}


def get_context(context):
	context.no_cache = 1
	context.error = frappe.form_dict.get("error") or ""
	provider = frappe.form_dict.get("provider") or ""
	context.provider = provider if provider in SETTINGS_PAGE else ""
	context.settings_page = SETTINGS_PAGE.get(context.provider, "")
