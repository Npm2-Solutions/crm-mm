# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""How the clients pay, and the reminders of what they still owe (`crm.invoicing.solleciti`)."""

from frappe.model.document import Document


class CRMPaymentReminderSettings(Document):
	def validate(self):
		from crm.invoicing import solleciti_regole as R

		(
			self.first_after_days,
			self.every_days,
			self.max_reminders,
			self.minimum_amount,
		) = R.numeri(self.first_after_days, self.every_days, self.max_reminders, self.minimum_amount)
