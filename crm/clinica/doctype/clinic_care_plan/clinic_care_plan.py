# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A dental care plan (`crm.clinica.cure`): a quote first, written as a draft by its
dentist; proposed, it is not rewritten - accepted or declined, then done treatment
by treatment, or closed. A new version starts from it as a draft."""

import frappe
from frappe import _

from crm.clinica import cure_regole as R
from crm.clinica.base import DocumentoClinico


class ClinicCarePlan(DocumentoClinico):
	dice_che_e_venuto = False

	def validate(self):
		prima = None if self.is_new() else self.get_doc_before_save()
		if prima and prima.status != R.BOZZA and not self.flags.dal_piano:
			frappe.throw(_("A proposed plan is not rewritten: make a new version"))
		from crm.clinica import cure

		cure.calcola(self)

	def on_trash(self):
		if self.status != R.BOZZA:
			frappe.throw(_("A proposed plan is kept: close it instead"))
		super().on_trash()
