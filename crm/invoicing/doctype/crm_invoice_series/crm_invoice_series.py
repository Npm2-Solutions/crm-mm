# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The counter of one series in one year."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from crm.invoicing.engine.numerazione import FormatoNonCompatibile, valida_formato


class CRMInvoiceSeries(Document):
	def validate(self):
		try:
			valida_formato(self.number_format, self.series, self.fiscal_year)
		except FormatoNonCompatibile as errore:
			frappe.throw(str(errore), title=_("Numbering format"))
		if self.is_new():
			return
		precedente = self.get_doc_before_save()
		if precedente and (self.last_number or 0) < (precedente.last_number or 0):
			# Lowering the counter re-issues a number that already exists. A duplicate
			# number is not corrected, it is reversed with a credit note.
			frappe.throw(
				_(
					"The counter cannot go backwards: number {0} has already been used, and issuing it "
					"twice can only be undone with a credit note"
				).format(self.last_number)
			)
