# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The documents filed before they were the CRM's were the clinical archive: they
keep the mark of health data (`clinical`), and so does whoever reads them. From
now on the kind decides, or whom a document is for.

A signed visit's report pointed to the visit for its file: it now names the file
itself, attached to it as well, so every document gives its own file.
"""

import frappe
from frappe.core.doctype.file.utils import attach_files_to_document
from frappe.query_builder.functions import IfNull

DOCUMENTO = "CRM Document"


def execute():
	# the DocType as this release has it, with the mark: never a silent skip
	frappe.reload_doc("documenti", "doctype", "crm_document")
	frappe.db.sql(f"update `tab{DOCUMENTO}` set clinical = 1")  # nosemgrep
	if not frappe.db.has_column(DOCUMENTO, "record"):
		return
	# the clinic's fields come back as customisations after this runs: read the table
	tabella = frappe.qb.DocType(DOCUMENTO)
	referti = (
		frappe.qb.from_(tabella)
		.select(tabella.name, tabella.record)
		.where((IfNull(tabella.record, "") != "") & (IfNull(tabella.file, "") == ""))
		.run()
	)
	for nome, visita in referti:
		pdf = frappe.db.get_value("Clinic Record", visita, "pdf_file")
		if not pdf:
			continue
		frappe.db.set_value(DOCUMENTO, nome, "file", pdf, update_modified=False)
		attach_files_to_document(frappe.get_doc(DOCUMENTO, nome), "on_update")
