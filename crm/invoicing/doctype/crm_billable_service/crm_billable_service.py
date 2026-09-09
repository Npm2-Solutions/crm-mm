# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The fiscal card of a service.

A service without a card is not billable, and that is the point of the doctype:
the exemption is a configured property that an accountant signs off, never
something the system reads out of the service name.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from crm.invoicing.engine.codici import DESCRIZIONE_TIPO_SPESA, NATURE_RITIRATE


class CRMBillableService(Document):
	def validate(self):
		self.valida_iva()
		self.valida_sistema_ts()

	def valida_iva(self):
		if self.vat_exempt:
			self.vat_rate = 0
			if not self.vat_nature:
				self.vat_nature = "N4"
			if not self.exemption_reference:
				frappe.msgprint(
					_(
						"No exemption reference: the 'operazione esente' annotation is mandatory on the "
						"document (art. 21, c. 6, lett. c), and on a PDF it is the annotation that "
						"carries weight, not the N4 code."
					),
					indicator="orange",
				)
		if self.vat_nature in NATURE_RITIRATE:
			frappe.throw(
				_("Natura {0} was retired with tracciato 1.2.2: use the sub-code").format(self.vat_nature)
			)
		if self.vat_nature and self.vat_rate:
			frappe.throw(
				_(
					"A line carries either a VAT rate or a Natura, never both. The Natura says why no "
					"tax is charged."
				)
			)
		if self.is_advance and not self.vat_nature:
			self.vat_nature = "N1"

	def valida_sistema_ts(self):
		if self.ts_expense_type and not self.is_healthcare:
			frappe.throw(
				_(
					"A tipoSpesa on a service that is not healthcare: the Sistema TS only knows "
					"healthcare expenses. Either the service is healthcare or the code does not belong."
				)
			)
		if self.ts_expense_flag and self.ts_expense_type not in ("TK", "SR"):
			frappe.throw(
				_(
					"flagTipoSpesa is only admitted with TK (emergency room) or SR (intramoenia), "
					"not with {0}"
				).format(DESCRIZIONE_TIPO_SPESA.get(self.ts_expense_type, "-"))
			)
