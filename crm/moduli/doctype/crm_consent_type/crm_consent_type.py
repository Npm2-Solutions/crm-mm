# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""A kind of consent, and the text the person reads for it.

The text belongs to the centre and each change of it is a new version: a consent
given keeps its own copy of the words it was given on, so rewriting the text never
rewrites what somebody agreed to.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class CRMConsentType(Document):
	def validate(self):
		self.text = (self.text or "").strip()
		if self.is_new():
			self.text_version = self.text_version or 1
			self.text_updated_on = self.text_updated_on or now_datetime()
			return
		before = self.get_doc_before_save()
		if before and (before.text or "").strip() != self.text:
			self.text_version = (before.text_version or 1) + 1
			self.text_updated_on = now_datetime()

	def on_trash(self):
		if self.standard:
			frappe.throw(_("A standard consent can be switched off, not deleted: the code asks about it"))
