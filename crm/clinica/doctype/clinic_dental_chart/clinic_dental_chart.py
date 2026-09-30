# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""What each tooth of the person is now (`crm.clinica.cure`): one per person,
written by the dentists, its changes kept in the document's history."""

import frappe
from frappe import _

from crm.clinica import cure_regole as R
from crm.clinica.base import DocumentoClinico


class ClinicDentalChart(DocumentoClinico):
	dice_che_e_venuto = False

	def validate(self):
		problemi = R.valida_stato([riga.as_dict() for riga in self.teeth])
		if problemi:
			frappe.throw("<br>".join(p.testo(_) for p in problemi))

	def on_trash(self):
		frappe.throw(_("A dental chart is kept: correct it instead"))
