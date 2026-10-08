# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A day's cash closing at the desk: what the day collected, what the drawer held,
the difference (`crm.invoicing.cassa`). One per day; closed again, it is counted
again, and its versions keep what it said before."""

import frappe
from frappe import _
from frappe.model.document import Document


class CRMCashClosing(Document):
	def validate(self):
		# its numbers are the day's, worked out by `cassa.chiudi`: never typed by hand
		# (the agency, in the Desk, may still put one right)
		if not self.flags.dalla_cassa and "System Manager" not in frappe.get_roles():
			frappe.throw(_("A cash closing is made from the reception desk"), frappe.PermissionError)
