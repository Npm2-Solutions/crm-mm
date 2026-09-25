# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Google Calendar goes one way only: out of the CRM.

The CRM now copies each user's appointments into their Google account and reads
nothing back (`crm.integrations.google.sync`). Calendars connected before that were
left with the framework's pull switched on: every hour it would make a calendar of
its own in the user's Google account and import it into the CRM as Events.

A record whose connection never finished has no token to copy with: it stays off
until the user connects, which switches the copy on.
"""

import frappe
from frappe.utils.password import get_decrypted_password


def execute():
	for row in frappe.get_all("Google Calendar", fields=["name", "pull_from_google_calendar"]):
		values = {}
		if row.pull_from_google_calendar:
			values["pull_from_google_calendar"] = 0
		if not get_decrypted_password("Google Calendar", row.name, "refresh_token", raise_exception=False):
			values["push_to_google_calendar"] = 0
		if values:
			frappe.db.set_value("Google Calendar", row.name, values, update_modified=False)
