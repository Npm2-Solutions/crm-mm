# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A document of the person: a contract, a signed form, a certificate - with the
clinic a report, a test, an image, a prescription.

A file the person brought, or that came in a conversation, or that the centre
made: private, with its type, its date, where it comes from and whom it is for,
its SHA-256 kept. Who reads it and who adds one is `crm.documenti.api`'s business;
what carries the mark of health data is read by the rule the clinic registers
(`crm.permissions.sanitari`).
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class CRMDocument(Document):
	def validate(self):
		if self.is_new():
			self.added_by = self.added_by or frappe.session.user
			self.added_on = self.added_on or now_datetime()
		elif self.has_value_changed("file"):
			frappe.throw(_("The file of a document is not replaced: add a new document"))
		if not self.file:
			frappe.throw(_("A document is a file"))
		# the discipline of whom it is for: a health professional's makes it health data
		if self.has_value_changed("practitioner") or (self.is_new() and not self.discipline):
			from crm.documenti.api import qualifica_di

			self.discipline = qualifica_di(self.practitioner) if self.practitioner else None

	def after_insert(self):
		# the file uploaded for it is attached to it now, before Frappe's own hook
		# could pick another unattached copy of the same content
		if self.flags.get("allegato"):
			frappe.db.set_value(
				"File",
				self.flags.allegato,
				{
					"attached_to_doctype": self.doctype,
					"attached_to_name": self.name,
					"attached_to_field": "file",
				},
			)
