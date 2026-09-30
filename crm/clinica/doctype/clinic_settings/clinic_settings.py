# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Where the clinic meets the sales side: which pipeline is the new patients' one,
where a booking moves its deals, which one holds the quotes.

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
		if self.new_patients_pipeline and self.new_patients_pipeline == self.quotes_pipeline:
			frappe.throw(_("New patients and quotes need two different pipelines"))
