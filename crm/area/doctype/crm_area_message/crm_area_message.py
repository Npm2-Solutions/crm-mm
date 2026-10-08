# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A message on the person's board in their area (`crm.area.messaggi`): from the
centre - administrative from the desk, or of a kind another module brings, the
clinic's, about the care, from a practitioner - or from the person, written in the
area with a photo or a PDF maybe, or passed on from the area's chat. Written once,
never rewritten."""

import frappe
from frappe import _
from frappe.model.document import Document


class CRMAreaMessage(Document):
	def validate(self):
		if not self.is_new():
			frappe.throw(_("A message is not rewritten: write another one"))
