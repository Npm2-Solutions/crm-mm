# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Fill in the last message on people who already have conversations.

The Inbox is the People list sorted by when somebody last wrote, and that date
is kept on the person as messages arrive. Everything said before this existed
has nowhere to be read from, so an inbox on a live site would have opened empty
with months of conversations sitting underneath it.

Only the records that have a message are touched, and only fields nobody types
into. Nothing is marked read: what was never seen should still be waiting.
"""

import frappe

from crm.api.conversations import RECORDS, available_channels, refresh_waiting_flags, remember


def execute():
	touched: set[tuple[str, str]] = set()
	for spec in available_channels().values():
		for row in frappe.get_all(
			spec["doctype"],
			filters={
				"reference_doctype": ["in", RECORDS],
				"reference_name": ["is", "set"],
			},
			fields=["reference_doctype", "reference_name"],
			group_by="reference_doctype, reference_name",
			limit_page_length=0,
		):
			touched.add((row.reference_doctype, row.reference_name))

	for doctype, name in touched:
		try:
			remember(doctype, name)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Conversations: could not read back {doctype} {name}")
	frappe.db.commit()

	# and the flag the Inbox filters on, for everybody at once — including the
	# people who have no conversation and are therefore waiting on nothing
	refresh_waiting_flags()
