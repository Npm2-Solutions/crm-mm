# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Invitations whose key was stored as it is.

Until now the key of an invitation link sat in plain text in a field every
Sales User could read through REST, so any pending invitation could be taken:
a new user's password, a role for an existing account. Keys are now stored as
a SHA-256 hash, and a plain one no longer opens anything — but it is still in
the table, and its invitation still reads «Pending».

This clears those keys and expires the pending invitations that had one: the
people who got them are invited again from Settings → Invite User. A hash, 64
hex characters, was written by the fixed code and is left alone.
"""

import frappe


def execute():
	for invitation in frappe.get_all(
		"CRM Invitation", filters={"key": ["is", "set"]}, fields=["name", "status", "key"]
	):
		if len(invitation.key) == 64:
			continue

		values = {"key": None}
		if invitation.status == "Pending":
			values["status"] = "Expired"
		frappe.db.set_value("CRM Invitation", invitation.name, values, update_modified=False)
