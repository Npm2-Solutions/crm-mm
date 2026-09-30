# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Where the clinic meets the sales side: which pipeline is the new patients' one,
and where a booking moves its deals. The quotes' is the CRM's (`CRM Quote
Settings`).

Written by `crm.clinica.pipeline`: the two pipelines are created when the clinic
is switched on, and the Manager can point these at pipelines of their own.
"""

import frappe
from frappe import _
from frappe.model.document import Document


class ClinicSettings(Document):
	def validate(self):
		if self.booked_stage and self.new_patients_pipeline:
			pipeline = frappe.db.get_value("CRM Deal Status", self.booked_stage, "pipeline")
			if pipeline != self.new_patients_pipeline:
				frappe.throw(
					_("The stage after a booking has to be one of the new patients pipeline's stages")
				)
		preventivi = frappe.db.get_single_value("CRM Quote Settings", "quotes_pipeline")
		if self.new_patients_pipeline and self.new_patients_pipeline == preventivi:
			frappe.throw(_("New patients and quotes need two different pipelines"))
