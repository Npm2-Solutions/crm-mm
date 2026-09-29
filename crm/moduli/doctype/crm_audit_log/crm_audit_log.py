# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""One event of a document, chained to the one before (`crm.moduli.traccia`).

Only added to: an event is not edited and not deleted. The discarded draft of a
form takes its events with it, by `frappe.db.delete`: nothing was signed there.
"""

import frappe
from frappe import _
from frappe.model.document import Document


class CRMAuditLog(Document):
	def validate(self):
		if not self.is_new():
			frappe.throw(_("An event of the register is not changed"))
		if not self.flags.dalla_traccia:
			frappe.throw(_("Events are written by the CRM, not by hand"))

	def on_trash(self):
		frappe.throw(_("An event of the register is not deleted"), frappe.LinkExistsError)
