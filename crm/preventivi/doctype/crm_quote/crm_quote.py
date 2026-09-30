# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A quote (`crm.preventivi.api`): a draft of its author; proposed, it is not
rewritten - accepted or declined, then done service by service, or closed. A new
version starts from it as a draft."""

import frappe
from frappe import _
from frappe.model.document import Document

from crm.preventivi import regole as R


class CRMQuote(Document):
	def validate(self):
		prima = None if self.is_new() else self.get_doc_before_save()
		if prima and prima.status != R.BOZZA and not self.flags.dal_preventivo:
			frappe.throw(_("A proposed quote is not rewritten: make a new version"))
		from crm.preventivi import api

		api.calcola(self)

	def on_trash(self):
		if self.status != R.BOZZA:
			frappe.throw(_("A proposed quote is kept: close it instead"))
