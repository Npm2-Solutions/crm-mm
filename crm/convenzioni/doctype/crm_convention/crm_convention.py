# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from crm.convenzioni import regole


class CRMConvention(Document):
	def validate(self):
		dati = self.as_dict()
		dati["shares"] = [r.as_dict() for r in self.shares]
		problemi = regole.problemi(dati)
		if problemi:
			frappe.throw("\n".join(p.testo(_) for p in problemi))
