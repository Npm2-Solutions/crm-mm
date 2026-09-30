# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""A message from the centre on the person's board in their area
(`crm.clinica.area.messaggi`): administrative from the desk, or about their care
from a practitioner. Written once, read by the patient; not a chat."""

import frappe
from frappe import _

from crm.clinica.base import DocumentoClinico


class ClinicMessage(DocumentoClinico):
	dice_che_e_venuto = False

	def validate(self):
		if not self.is_new():
			frappe.throw(_("A message is not rewritten: write another one"))

	def after_insert(self):
		# a message about their care is health data, and makes a patient; one from the desk is not
		if self.kind == "Care":
			super().after_insert()
