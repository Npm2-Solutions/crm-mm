# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The patient card: one per person, written by the first rule that fires.

It holds when and why the person became a patient; the clinical record hangs off
it. Written through `crm.clinica.paziente.assicura_paziente`, or imported from the
previous software - then the rule is the import.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from crm.clinica import regole


class ClinicPatient(Document):
	def validate(self):
		if not self.rule and frappe.flags.in_import:
			self.rule = regole.IMPORTAZIONE.valore
		if self.rule not in regole.PER_VALORE:
			frappe.throw(_("Unknown rule: {0}").format(self.rule))
		self.patient_since = self.patient_since or now_datetime()
		if self.guardian and self.guardian == self.lead:
			frappe.throw(_("A person is not their own guardian"))
		if not self.guardian:
			self.guardian_relation = None
