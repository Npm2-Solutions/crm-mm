# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""A qualification, as the practice can correct it.

The shipped register is a documented starting point, not a tax opinion. These
checks stop the two combinations that are always a mistake rather than a choice:
a qualification that reports to the Sistema TS while its documents are allowed on
the SdI, and one that claims the art. 10 exemption without being a health
profession at all.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from crm.invoicing.engine.codici import RegolaSdI, SoggettoInviante, tipi_spesa_ammessi


class CRMProfessionalQualification(Document):
	def validate(self):
		self.code = (self.code or "").strip().lower().replace(" ", "_")
		self.allinea_sanitario()
		self.valida_coerenza()

	def allinea_sanitario(self):
		if self.sender_category and self.sender_category != SoggettoInviante.NON_SANITARIO:
			self.is_healthcare = 1

	def valida_coerenza(self):
		if self.vat_exempt and not self.is_healthcare:
			frappe.throw(
				_(
					"The art. 10 exemption is a joint requirement: objective, the service, and "
					"subjective, a supervised health profession. A qualification that is not one "
					"cannot carry it - see Risoluzione AdE n. 9 del 24 febbraio 2026 on osteopaths, "
					"chiropractors and kinesiologists."
				)
			)
		if self.ts_required and self.sdi_rule != RegolaSdI.VIETATO:
			frappe.throw(
				_(
					"A qualification that reports to the Sistema TS is one whose documents towards a "
					"natural person cannot go through the SdI. Set the SdI rule to 'vietato', or turn "
					"the Sistema TS duty off."
				)
			)
		if self.ts_required and not tipi_spesa_ammessi(self.sender_category):
			frappe.throw(
				_(
					"Sender category {0} has no admitted tipoSpesa: pick the category the Sistema TS "
					"enrolled this profession under"
				).format(self.sender_category)
			)
		if self.fund_mandatory and self.fund_subject_to_withholding:
			frappe.throw(
				_(
					"A contributo integrativo is not subject to the withholding; the optional INPS "
					"rivalsa is. Only one of the two flags belongs on a qualification."
				)
			)
		if self.verified and not self.verified_on:
			self.verified_on = frappe.utils.getdate()
