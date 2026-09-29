# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""A form filled for a person on a published version (`crm.moduli.compilazioni`).

A draft keeps the answers so far. Signed, it is submitted and not rewritten: the
answers, the signatures and the PDF are what the person signed. A correction is
cancel and amend, as for an invoice, and the register of the form says so.
"""

import frappe
from frappe import _
from frappe.model.document import Document

from crm.moduli import traccia


class CRMForm(Document):
	def validate(self):
		if self.given_by and self.given_by == self.lead:
			self.given_by = None

	def before_submit(self):
		if not self.signed_on or not self.answers_hash:
			# signing goes through `compilazioni.sign_form`, which checks the answers
			# and keeps the signatures: a submit from anywhere else would skip both
			frappe.throw(_("A form is signed from the CRM, where its answers are checked"))

	def on_cancel(self):
		traccia.traccia(self.doctype, self.name, "cancelled", _("Cancelled, to be amended"))

	def on_trash(self):
		if self.docstatus == 1:
			frappe.throw(_("A signed form is kept"), frappe.LinkExistsError)
