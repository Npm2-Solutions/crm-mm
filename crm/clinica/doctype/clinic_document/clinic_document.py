# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""A document of the clinical archive: a report, a test, an image, a prescription.

A file the patient brought, or that came in a conversation, or the report the
centre made when a visit was signed: private, with its type, its date, where it
comes from and whom it is for. Who reads it and who adds one is
`crm.clinica.archivio`'s business; like every clinical document, the first one
about a person makes them a patient (rule 1).
"""

import frappe
from frappe import _
from frappe.utils import now_datetime

from crm.clinica.base import DocumentoClinico

SOLO_IO = "Only me"


class ClinicDocument(DocumentoClinico):
	dice_che_e_venuto = False

	def validate(self):
		from crm.clinica import dossier

		if self.is_new():
			self.added_by = self.added_by or frappe.session.user
			self.added_on = self.added_on or now_datetime()
			# "my discipline" means the discipline of whom it is for
			if not self.discipline and self.practitioner:
				self.discipline = dossier.disciplina_di(self.practitioner)
		else:
			if self.has_value_changed("file") or self.has_value_changed("record"):
				frappe.throw(_("The file of a document is not replaced: add a new document"))
			if self.has_value_changed("practitioner"):
				self.discipline = dossier.disciplina_di(self.practitioner) if self.practitioner else None
		if self.visibility == dossier.DISCIPLINA and not self.discipline:
			frappe.throw(_("{0} has no discipline: choose the care team").format(self.practitioner))
		if not (self.file or self.record):
			frappe.throw(_("A document of the archive is a file"))
		if self.visibility == SOLO_IO and not self.practitioner:
			self.practitioner = self.added_by

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
		super().after_insert()

	def on_trash(self):
		# the patient card keeps the rule that made them a patient, not a link to a
		# document taken away: the audit log says what it was
		for scheda in frappe.get_all(
			"Clinic Patient", filters={"source_doctype": self.doctype, "source_name": self.name}, pluck="name"
		):
			frappe.db.set_value("Clinic Patient", scheda, {"source_doctype": None, "source_name": None})
