# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""A line of the clinical record: a visit or a note, in words and attachments.

It is its author's while it is a draft. Signed, it is not rewritten any more: it
is added to, with an addendum that points at it - a clinical record is
integrated, never corrected in place. Who reads it is `crm.clinica.cartella`'s
business, and every read from the CRM leaves a trace in the access log.
"""

import frappe
from frappe import _
from frappe.utils import now_datetime

from crm.clinica.base import DocumentoClinico

SOLO_IO = "Only me"


class ClinicRecord(DocumentoClinico):
	def validate(self):
		if self.is_new():
			self.practitioner = self.practitioner or frappe.session.user
		if self.addendum_to:
			firmato = frappe.db.get_value(
				"Clinic Record", self.addendum_to, ["lead", "docstatus"], as_dict=True
			)
			if not firmato or firmato.lead != self.lead:
				frappe.throw(_("An addendum belongs to the same patient's record"))
			if firmato.docstatus != 1:
				frappe.throw(_("A draft is edited, not added to"))

	def before_submit(self):
		allegati = frappe.db.exists(
			"File", {"attached_to_doctype": self.doctype, "attached_to_name": self.name}
		)
		if not frappe.utils.strip_html(self.content or "").strip() and not allegati:
			frappe.throw(_("A signed record says something: write what happened, or attach it"))
		self.signed_on = now_datetime()

	def before_cancel(self):
		frappe.throw(_("A signed record is not taken back: add an addendum to it"))
