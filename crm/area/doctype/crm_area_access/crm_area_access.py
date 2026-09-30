# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Who enters whose area (`crm.area`): the person themselves, a parent or guardian
for a minor, somebody who follows an elderly parent with their say-so. Opened and
closed by the centre; kept, as the trace of who could see what."""

import frappe
from frappe import _
from frappe.model.document import Document


class CRMAreaAccess(Document):
	def validate(self):
		if self.is_new() and frappe.db.exists(
			self.doctype, {"user": self.user, "lead": self.lead, "name": ("!=", self.name)}
		):
			frappe.throw(_("{0} already enters this area").format(self.user))

	def on_trash(self):
		frappe.throw(_("An access to the area is closed, not deleted: it is part of the trace"))
