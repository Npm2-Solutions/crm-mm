# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""How the centre reminds its clients of their appointments: whether, how many
hours before, by which ways, and what a «cannot come» does
(`crm.scheduling.promemoria`)."""

import frappe
from frappe import _
from frappe.model.document import Document

from crm.scheduling import promemoria_regole as R


class CRMReminderSettings(Document):
	def validate(self):
		self.hours_before = R.ore_prima(self.hours_before)
		if self.whatsapp_template and not (
			frappe.db.exists("DocType", "WhatsApp Templates")
			and frappe.db.exists("WhatsApp Templates", self.whatsapp_template)
		):
			frappe.throw(_("This WhatsApp template does not exist"))
