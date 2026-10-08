# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from crm.convenzioni import regole


class CRMConventionCover(Document):
	def validate(self):
		problemi = regole.problemi_della_copertura(self.as_dict())
		if problemi:
			frappe.throw("\n".join(p.testo(_) for p in problemi))
