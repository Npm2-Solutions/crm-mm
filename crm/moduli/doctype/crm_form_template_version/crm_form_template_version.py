# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A published version of a form template: what people fill, and never changes.

Its schema is frozen with the words of the consents it records, and its SHA-256
is what a filled form points at to prove, years later, which questions and which
words it was. A change is a new version (`crm.moduli.modelli.publish_template`).
"""

import frappe
from frappe import _
from frappe.model.document import Document


class CRMFormTemplateVersion(Document):
	def validate(self):
		if not self.is_new():
			frappe.throw(_("A published version does not change: publish a new one"))

	def on_trash(self):
		frappe.throw(
			_("A published version is kept: the forms filled on it point at it"),
			frappe.LinkExistsError,
		)
