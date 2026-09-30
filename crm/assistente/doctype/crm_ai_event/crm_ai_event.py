# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""One request to the assistant (`crm.assistente`): what it was for, the model,
the provider and the region, the fingerprints of what went in and came out, the
draft and how far the final text went from it. Only added to: a person accepts
or throws away the draft, and a monthly sample is re-read."""

import frappe
from frappe import _
from frappe.model.document import Document


class CRMAIEvent(Document):
	def on_trash(self):
		frappe.throw(_("The assistant's register is kept: an event is not deleted"))
