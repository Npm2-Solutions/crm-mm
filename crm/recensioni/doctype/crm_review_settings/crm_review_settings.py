# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Where the centre's reviews are written, and how often a person is asked
(`crm.recensioni.chiedi`)."""

from frappe.model.document import Document


class CRMReviewSettings(Document):
	def validate(self):
		from crm.recensioni import chiedi

		chiedi.controlla(self)
