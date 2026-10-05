# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Whoever performs the service. Their qualification decides the expense type and the VAT regime."""

import frappe
from frappe import _
from frappe.model.document import Document

#: Who issues, never who performs: a facility or a pharmacy is the company's
#: category for the Sistema TS, not a person's qualification.
DI_CHI_EMETTE = frozenset({"struttura_autorizzata", "struttura_accreditata", "farmacia", "parafarmacia"})


class CRMServiceProvider(Document):
	def validate(self):
		if not self.qualification:
			return
		categoria = frappe.db.get_value(
			"CRM Professional Qualification", self.qualification, "sender_category"
		)
		if categoria in DI_CHI_EMETTE:
			frappe.throw(
				_(
					"{0} is who issues the invoice, not what a person does: choose the profession of whoever performs the service"
				).format(
					frappe.db.get_value(
						"CRM Professional Qualification", self.qualification, "qualification_name"
					)
				)
			)
