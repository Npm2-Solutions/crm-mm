# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Records already stamped «Guest».

A lead from a Meta form, a WhatsApp message from a stranger, a booking on the
public page: all created with nobody logged in, and the history then reads
«Guest created this lead». From now on a hook credits the system instead; this
does the same for the rows already written.

The dates are left alone. Only the name of who did it changes, and it changes to
the truth: it was the system.
"""

import frappe

from crm.utils.ownership import SYSTEM_USER


def execute():
	for doctype in ("CRM Lead", "CRM Deal", "Contact"):
		if not frappe.db.exists("DocType", doctype):
			continue
		table = f"`tab{doctype}`"
		for field in ("owner", "modified_by"):
			# nosemgrep: frappe-sql-format-injection — table and field come from the tuples above; the user is bound with %s
			frappe.db.sql(
				f"update {table} set `{field}` = %s where `{field}` = 'Guest'",
				(SYSTEM_USER,),
			)
	frappe.db.commit()
