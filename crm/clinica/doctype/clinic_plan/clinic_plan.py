# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A plan (`crm.clinica.piani`): what a practitioner writes and the patient
follows in their area - a menu, an exchange diet, a training, exercises at home,
habits. A draft is its author's; published, it is not rewritten: a new version
replaces it, or it is closed."""

import frappe
from frappe import _

from crm.clinica.base import DocumentoClinico


class ClinicPlan(DocumentoClinico):
	dice_che_e_venuto = False

	def validate(self):
		prima = None if self.is_new() else self.get_doc_before_save()
		if prima and prima.status != "Draft" and not self.flags.dal_piano:
			frappe.throw(_("A published plan is not rewritten: make a new version"))

	def on_trash(self):
		if self.status != "Draft":
			frappe.throw(_("A published plan is kept: close it instead"))
		super().on_trash()
