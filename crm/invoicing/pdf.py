# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Render the invoice, and keep what was rendered.

**Generated once.** The renderer is not byte-stable across versions and settings,
so regenerating is not a recovery path: the file that was handed over is the one
stored, and the SHA-256 taken at creation is what proves it years later. That is
also why this refuses to run twice on the same document.

On the healthcare branch this is the only document there is - it does not travel
through the SdI - so it is the product, not a courtesy copy. On the SdI branch it
is a courtesy copy, and with PDF/A-3 the FatturaPA file rides inside it: the
readable rendering and the machine-readable original stay one file.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import getdate

from crm.invoicing.engine import pdfa

FORMATO_STAMPA = "Fattura"


def _xml_allegato(doc) -> tuple[str, bytes] | None:
	"""The FatturaPA file, to travel inside the PDF."""
	if not doc.xml_file:
		return None
	try:
		allegato = frappe.get_doc("File", {"file_url": doc.xml_file})
		contenuto = allegato.get_content(encodings=[])
		if isinstance(contenuto, str):
			contenuto = contenuto.encode()
		return (doc.sdi_filename or allegato.file_name, contenuto)
	except Exception:
		frappe.log_error(title="Invoice XML attachment", message=frappe.get_traceback())
		return None


def rendi(doc) -> bytes:
	"""The rendered bytes, before conversion. Separated so it can be swapped."""
	return frappe.get_print(
		doc.doctype,
		doc.name,
		print_format=FORMATO_STAMPA,
		as_pdf=True,
		no_letterhead=1,
	)


def genera_e_allega(doc) -> dict:
	"""Produce the PDF/A and attach it to the invoice.

	Never raises on a rendering problem: an invoice the client cannot be handed is
	worse than one whose PDF has to be produced again from the form. The failure is
	logged and reported, and the document keeps its number.
	"""
	if doc.pdf_file:
		return {
			"skipped": True,
			"reason": _("This invoice already has a PDF: regenerating would produce a different file"),
			"file": doc.pdf_file,
		}

	try:
		reso = rendi(doc)
	except Exception as errore:
		frappe.log_error(title=f"Invoice PDF {doc.name}", message=frappe.get_traceback())
		return {"skipped": True, "reason": str(errore)}

	risultato = pdfa.converti(
		reso,
		titolo=doc.document_number or doc.name,
		data_documento=getdate(doc.posting_date),
		allegato_xml=_xml_allegato(doc),
	)

	allegato = frappe.get_doc(
		{
			"doctype": "File",
			# The file name is data too: it must not say what the service was.
			"file_name": pdfa.nome_file_neutro(doc.document_number or doc.name),
			"attached_to_doctype": doc.doctype,
			"attached_to_name": doc.name,
			"attached_to_field": "pdf_file",
			"is_private": 1,
			"content": risultato.dati,
		}
	).insert(ignore_permissions=True)

	doc.db_set(
		{
			"pdf_file": allegato.file_url,
			"pdf_hash": risultato.sha256,
			"pdf_conformita": risultato.conformita,
		},
		update_modified=False,
	)

	from crm.invoicing import documento

	documento.registra(
		doc,
		"pdf_generated",
		"\n".join(risultato.avvisi) if risultato.avvisi else risultato.conformita,
		stato=risultato.conformita,
		# The payload carries a hash and a verdict, never anything about the service.
		payload={
			"sha256": risultato.sha256,
			"bytes": risultato.byte,
			"conformance": risultato.conformita,
			"embedded_files": risultato.rapporto.allegati,
		},
	)
	return {
		"file": allegato.file_url,
		"sha256": risultato.sha256,
		"conformance": risultato.conformita,
		"warnings": risultato.avvisi,
	}
