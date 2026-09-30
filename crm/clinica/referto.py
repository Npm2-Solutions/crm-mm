# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The report of a visit: the clinical sheet as signed, made once, and kept.

A visit written on a clinical sheet (a template whose use is "clinical sheet")
has its answers checked by the same engine as every form, and, when the
practitioner signs it, becomes a PDF/A: the sheet in words, the notes, who
signed and when, the version and the hashes of what it asked and of what was
answered. Like the signed form's PDF, it is made once; the record keeps its
SHA-256. What is signed is added to, never rewritten: an addendum is a record
of its own.
"""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import format_datetime, get_fullname, getdate

from crm.moduli import schema as S

MODELLO_HTML = "crm/clinica/templates/referto.html"


def contesto(doc, versione) -> dict:
	from crm.moduli import pdf

	schema = json.loads(versione.schema) if isinstance(versione.schema, str) else versione.schema
	risposte = json.loads(doc.answers or "{}") if isinstance(doc.answers, str) else (doc.answers or {})
	stato = S.valuta(schema, risposte)
	avvisi = {avviso["field"]: avviso["message"] for avviso in stato["stops"]}
	sezioni = []
	for sezione in S.sezioni(schema):
		if not stato["sections"].get(sezione.get("id")):
			continue
		voci = []
		for campo in S.campi_della_sezione(sezione):
			chiave = campo.get("id")
			if not stato["visible"].get(chiave) or campo.get("type") == "signature":
				continue
			valore = stato["values"].get(chiave)
			voce = {
				"tipo": campo.get("type"),
				"etichetta": campo.get("label") or "",
				"avviso": avvisi.get(chiave),
			}
			if voce["tipo"] == "paragraph":
				voce["testo"] = campo.get("text") or ""
			elif voce["tipo"] == "table":
				colonne = [c for c in campo.get("columns") or [] if isinstance(c, dict)]
				voce["colonne"] = [c.get("label") for c in colonne]
				voce["righe"] = [
					[
						pdf.risposta_in_parole(
							{"type": c.get("type") or "text"}, (riga or {}).get(c.get("id"))
						)
						for c in colonne
					]
					for riga in (valore or [])
				]
			else:
				voce["risposta"] = pdf.risposta_in_parole(campo, valore, stato["bands"].get(chiave))
			voci.append(voce)
		sezioni.append({"titolo": sezione.get("title"), "voci": voci})
	return {
		"doc": doc,
		"versione": versione,
		"titolo": doc.title or versione.title,
		"lingua": (frappe.local.lang or "it")[:2],
		"centro": frappe.db.get_single_value("FCRM Settings", "brand_name"),
		"persona": doc.lead_name or frappe.db.get_value("CRM Lead", doc.lead, "lead_name"),
		"medico": get_fullname(doc.practitioner),
		"data": format_datetime(doc.record_date),
		"firmato_il": format_datetime(doc.signed_on),
		"sezioni": sezioni,
		# the notes are the practitioner's own HTML: cleaned before they go in
		"note": frappe.utils.sanitize_html(doc.content or ""),
		"_": _,
	}


def html(doc, versione) -> str:
	return frappe.render_template(MODELLO_HTML, contesto(doc, versione))


def rendi(doc, versione) -> bytes:
	from weasyprint import HTML

	return HTML(string=html(doc, versione)).write_pdf()


def genera_e_allega(doc) -> dict:
	"""The report, made once when the visit is signed, attached private. A report
	that cannot be made does not undo the signature: the log says so."""
	from crm.invoicing.engine import pdfa

	if doc.get("pdf_file") or not doc.get("template_version"):
		return {"skipped": True}
	versione = frappe.get_doc("CRM Form Template Version", doc.template_version)
	try:
		reso = rendi(doc, versione)
	except Exception:
		frappe.log_error(title=f"Clinical report {doc.name}", message=frappe.get_traceback())
		return {"skipped": True}
	risultato = pdfa.converti(reso, titolo=doc.title or doc.name, data_documento=getdate(doc.signed_on))
	allegato = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": f"{doc.name}.pdf",
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
			"pdf_conformance": risultato.conformita,
		},
		update_modified=False,
	)
	return {"file": allegato.file_url, "sha256": risultato.sha256}
