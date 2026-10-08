# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A day's cash closing at the desk: what the day collected, what the drawer held,
the difference (`crm.invoicing.cassa`). One per day; closed again, it is counted
again, and its versions keep what it said before."""

from frappe.model.document import Document


class CRMCashClosing(Document):
	pass
