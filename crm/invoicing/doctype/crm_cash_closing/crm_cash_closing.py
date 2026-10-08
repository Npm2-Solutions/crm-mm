# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A day's cash closing at the desk: what the day collected, what the drawer held,
the difference (`crm.invoicing.cassa`). One per day and location (none: the whole
centre, docs/crm/62); closed again, it is counted again, and its versions keep
what it said before."""

import frappe
from frappe import _
from frappe.model.document import Document


class CRMCashClosing(Document):
	def validate(self):
		# its numbers are the day's, worked out by `cassa.chiudi`: never typed by hand
		# (the agency, in the Desk, may still put one right)
		if not self.flags.dalla_cassa and "System Manager" not in frappe.get_roles():
			frappe.throw(_("A cash closing is made from the reception desk"), frappe.PermissionError)
		# one a day for each location, and one for the whole centre
		filtri = {"date": self.date, "name": ["!=", self.name or ""]}
		filtri["centre_location"] = self.centre_location or ["is", "not set"]
		if frappe.db.exists("CRM Cash Closing", filtri):
			frappe.throw(_("This day is already closed: close it again from the reception desk"))
