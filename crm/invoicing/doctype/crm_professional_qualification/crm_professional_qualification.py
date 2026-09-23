# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""A qualification, as the practice actually configured it.

The register is invoicing's, not healthcare's: a lawyer, an engineer and a
consultant all have one, and what hangs off it - the fund, the withholding, the
default rate - is ordinary invoicing. The file that ships with the module is where
the research lives; these records are what the practice runs on, and the practice
wins.

What this controller checks is what holds for **any** qualification. The
healthcare coherence - that an art. 10 exemption needs a supervised profession,
that a Sistema TS duty and the SdI are mutually exclusive - is checked by
`crm.tessera_sanitaria`, through a `doc_events` hook, because those are its rules
and it is the module that can explain them.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


class CRMProfessionalQualification(Document):
	def validate(self):
		self.code = (self.code or "").strip().lower().replace(" ", "_")
		self.valida_coerenza()

	def valida_coerenza(self):
		if self.fund_mandatory and self.fund_subject_to_withholding:
			frappe.throw(
				_(
					"A contributo integrativo is not subject to the withholding; the optional INPS "
					"rivalsa is. Only one of the two flags belongs on a qualification."
				)
			)
		if self.verified and not self.verified_on:
			self.verified_on = frappe.utils.getdate()
