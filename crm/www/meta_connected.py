# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Landing page for the end of the Meta login, shown inside the popup.

The connect flow runs in a popup window so the CRM behind it never navigates
away and keeps its state. This page is what Facebook's redirect finally lands
on: it tells the opener how it went and closes itself. Opened as a normal tab
instead (popup blocked, link pasted by hand) it falls back to the settings
page, which is what used to happen for every login.
"""

import frappe

no_cache = 1


def get_context(context):
	context.no_cache = 1
	context.error = frappe.form_dict.get("error") or ""
	# the label is matched untranslated by the settings modal
	context.settings_page = "Meta connection"
