# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A plan for a person (`crm.piani.api`): what somebody of the centre writes and the
person follows in their area - a training, habits, and the kinds a module adds
(the clinic's diets and exercises at home). A draft is its author's; published,
it is not rewritten: a new version replaces it, or it is closed."""

import frappe
from frappe import _
from frappe.model.document import Document


class CRMPersonalPlan(Document):
	def validate(self):
		prima = None if self.is_new() else self.get_doc_before_save()
		if prima and prima.status != "Draft" and not self.flags.dal_piano:
			frappe.throw(_("A published plan is not rewritten: make a new version"))

	def on_trash(self):
		if self.status != "Draft":
			frappe.throw(_("A published plan is kept: close it instead"))
