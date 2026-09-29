# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""A form to fill away from the operator's screen (`crm.moduli.richieste`).

Sent as a link, or handed over on the desk's tablet. One link can open several
forms: the first request holds the link, the code and the session, and the
others say which one they came with (``via``). Only SHA-256 of the secrets is
kept here; what happened to it is in its register (`CRM Audit Log`).
"""

import frappe
from frappe import _
from frappe.model.document import Document


class CRMFormRequest(Document):
	def on_trash(self):
		if self.form or self.status in ("Filled", "Signed"):
			# the register of a signed form says which request it came from
			frappe.throw(_("A request that was answered is kept"), frappe.LinkExistsError)
