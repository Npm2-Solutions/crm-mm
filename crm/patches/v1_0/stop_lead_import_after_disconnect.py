# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Switch off lead sync on sites that are already disconnected from Meta.

Disconnecting used to clear only the user access token. Page tokens do not
expire with it, so every Page kept its own token and its `leadgen` webhook
subscription, and leads went on arriving — hourly polling included — for a
connection the settings screen showed as gone.

`disconnect()` now stops the pages itself. This is for the sites where the
button was pressed before that: with no user token there is no connection, so
no page may import. The page tokens are left alone — they are also what the
Social Planner publishes with, and unsubscribing on Meta's side needs network
calls that do not belong in a migration. The pages stay subscribed at Meta and
its notifications are simply ignored; pressing Connect again reconnects them.
"""

import frappe


def execute():
	if not frappe.db.exists("DocType", "Facebook Page") or not frappe.db.exists(
		"DocType", "CRM Meta Settings"
	):
		return

	settings = frappe.get_single("CRM Meta Settings")
	if settings.get_password("user_access_token", raise_exception=False):
		return  # still connected: leave the pages as the user set them

	for page in frappe.get_all("Facebook Page", filters={"sync_enabled": 1}, pluck="name"):
		frappe.db.set_value(
			"Facebook Page",
			page,
			{"sync_enabled": 0, "webhook_subscribed": 0},
			update_modified=False,
		)
