# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""A programme of stages (`crm.clinica.programmi`): written as a draft by its
author, published to the person's area, where its stages open with time or one
after the other. Published, it is not rewritten: it goes on, or it is closed."""

import frappe
from frappe import _

from crm.clinica.base import DocumentoClinico


class ClinicProgramme(DocumentoClinico):
	dice_che_e_venuto = False

	def validate(self):
		prima = None if self.is_new() else self.get_doc_before_save()
		if prima and prima.status != "Draft" and not self.flags.dal_programma:
			frappe.throw(_("A published programme is not rewritten: close it and write another"))

	def on_trash(self):
		if self.status != "Draft":
			frappe.throw(_("A published programme is kept: close it instead"))
		super().on_trash()
