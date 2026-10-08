# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""How the clients pay, and the reminders of what they still owe (`crm.invoicing.solleciti`)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class CRMPaymentReminderSettings(Document):
	def validate(self):
		# a number out of its range is said, never put right in silence
		limiti = (
			(
				"first_after_days",
				1,
				365,
				_("The first reminder leaves from 1 to 365 days after the due date"),
			),
			("every_days", 1, 365, _("Between one reminder and the next, from 1 to 365 days")),
			("max_reminders", 1, 10, _("From 1 to 10 reminders for an invoice")),
		)
		for campo, basso, alto, frase in limiti:
			valore = self.get(campo)
			if valore in (None, ""):
				continue
			if not basso <= int(valore) <= alto:
				frappe.throw(frase)
		if flt(self.minimum_amount) < 0:
			frappe.throw(_("The minimum amount cannot be below zero"))
