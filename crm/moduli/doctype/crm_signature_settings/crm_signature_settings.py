# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The centre's signature provider (`crm.moduli.firme`): which one, and its keys."""

import frappe
from frappe import _
from frappe.model.document import Document


class CRMSignatureSettings(Document):
	def validate(self):
		from crm.moduli import firme

		if self.enabled and self.provider not in firme.fornitori():
			frappe.throw(
				_("{0} is not a provider the CRM knows: {1}").format(
					frappe.bold(self.provider or "-"), ", ".join(firme.fornitori()) or _("none yet")
				)
			)
