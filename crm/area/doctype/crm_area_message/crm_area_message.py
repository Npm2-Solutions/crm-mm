# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A message from the centre on the person's board in their area
(`crm.area.messaggi`): administrative from the desk, or of a kind another module
brings - the clinic's, about the care, from a practitioner. Written once, read by
the person; not a chat. A question the person passed on from the area's chat is on
the board too, for the desk to answer there."""

import frappe
from frappe import _
from frappe.model.document import Document


class CRMAreaMessage(Document):
	def validate(self):
		if not self.is_new():
			frappe.throw(_("A message is not rewritten: write another one"))
