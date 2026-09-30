# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""An opening of a record out of the care team (`crm.clinica.dossier`): who, whom,
why, until when. Written once, never changed: it is what the access log shows."""

import frappe
from frappe import _
from frappe.model.document import Document


class ClinicAccessGrant(Document):
	def validate(self):
		if not self.is_new():
			frappe.throw(_("An opening out of the care team is not changed: it is a record of what happened"))

	def on_trash(self):
		frappe.throw(_("An opening out of the care team is kept: it is part of the access log"))
