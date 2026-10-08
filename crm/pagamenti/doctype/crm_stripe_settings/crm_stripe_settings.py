# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's Stripe account (`crm.pagamenti.collegamento`): written by the
connection's calls, never by hand."""

from frappe.model.document import Document


class CRMStripeSettings(Document):
	def validate(self):
		if self.refund_hours is not None and self.refund_hours < 0:
			self.refund_hours = 0
