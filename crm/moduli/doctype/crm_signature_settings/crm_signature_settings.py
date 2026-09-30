# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's signature provider (`crm.moduli.firme`): which one, and its keys."""

import frappe
from frappe import _
from frappe.model.document import Document

from crm.marchio import con_nome


class CRMSignatureSettings(Document):
	def validate(self):
		from crm.moduli import firme

		if self.enabled and self.provider not in firme.fornitori():
			frappe.throw(
				con_nome(_("{0} is not a provider {brand} knows: {1}")).format(
					frappe.bold(self.provider or "-"), ", ".join(firme.fornitori()) or _("none yet")
				)
			)
