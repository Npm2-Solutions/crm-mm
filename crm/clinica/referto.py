# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The report of a visit: the visit as signed, made once, and kept.

When the practitioner signs a visit it becomes a PDF/A: what was written and,
for a visit on a clinical sheet (a template whose use is "clinical sheet",
checked by the same engine as every form), the sheet in words with the version
and the hashes of what it asked and of what was answered; who signed and when.
Like the signed form's PDF, it is made once; the record keeps its SHA-256, and
the person's documents file it (`crm.clinica.documenti.dal_referto`). What is signed is
added to, never rewritten: an addendum is a visit of its own, with its report.
"""

from __future__ import annotations

import json
import re

import frappe
from frappe import _
from frappe.utils import format_datetime, get_fullname, getdate

from crm import marchio
from crm.moduli import schema as S
from crm.moduli import sigillo

MODELLO_HTML = "crm/clinica/templates/referto.html"


def contesto(doc, versione=None) -> dict:
	"""``versione`` is the clinical sheet's, or None for a visit written freely."""
	from crm.moduli import pdf

	schema = {"sections": []}
	if versione:
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
		"titolo": doc.title or (versione.title if versione else _("Visit")),
		# an addendum says which visit it adds to
		"integra": _integra(doc),
		"lingua": (frappe.local.lang or "it")[:2],
		"centro": frappe.db.get_single_value("FCRM Settings", "brand_name"),
		"persona": doc.lead_name or frappe.db.get_value("CRM Lead", doc.lead, "lead_name"),
		"medico": get_fullname(doc.practitioner),
		"data": format_datetime(doc.record_date),
		"firmato_il": format_datetime(doc.signed_on),
		"sezioni": sezioni,
		# the notes: written in the CRM as text, kept as text; in the Desk's editor as
		# HTML, cleaned of anything but formatting before it goes in
		**_note(doc.content or ""),
		"_": _,
	}


def _integra(doc) -> str | None:
	if not doc.get("addendum_to"):
		return None
	originale = frappe.db.get_value("Clinic Record", doc.addendum_to, ["title", "record_date"], as_dict=True)
	if not originale:
		return None
	parti = (originale.title, format_datetime(originale.record_date))
	return " · ".join(parte for parte in parti if parte)


def _note(contenuto: str) -> dict:
	if re.search(r"<[a-zA-Z/][^>]*>", contenuto):
		return {"note_html": frappe.utils.sanitize_html(contenuto), "note": None}
	return {"note_html": None, "note": contenuto.strip()}


def html(doc, versione=None) -> str:
	# nosemgrep: frappe-ssti — the app's own template
	return frappe.render_template(MODELLO_HTML, contesto(doc, versione))


def rendi(doc, versione=None) -> bytes:
	from crm.moduli import pdf

	return pdf.pdf_da_html(html(doc, versione))


def genera_e_allega(doc) -> dict:
	"""The report, made once when the visit is signed, attached private. A report
	that cannot be made does not undo the signature: the log says so."""
	from crm.invoicing.engine import pdfa

	if doc.get("pdf_file") or doc.get("kind") != "Visit":
		return {"skipped": True}
	versione = (
		frappe.get_doc("CRM Form Template Version", doc.template_version)
		if doc.get("template_version")
		else None
	)
	try:
		reso = rendi(doc, versione)
	except Exception:
		frappe.log_error(title=f"Clinical report {doc.name}", message=frappe.get_traceback())
		return {"skipped": True}
	risultato = pdfa.converti(
		reso,
		titolo=doc.title or _("Visit") + f" {doc.name}",
		data_documento=getdate(doc.signed_on),
		produttore=marchio.nome(),
	)
	# sealed by the centre before the fingerprint, as a signed form is
	sigillato = sigillo.sigilla(risultato.dati, motivo=_("Visit report"))
	allegato = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": f"{doc.name}.pdf",
			"attached_to_doctype": doc.doctype,
			"attached_to_name": doc.name,
			"attached_to_field": "pdf_file",
			"is_private": 1,
			"content": sigillato.dati,
		}
	).insert(ignore_permissions=True)
	doc.db_set(
		{
			"pdf_file": allegato.file_url,
			"pdf_hash": sigillato.sha256,
			"pdf_conformance": sigillato.descrizione(risultato.conformita),
		},
		update_modified=False,
	)
	return {"file": allegato.file_url, "sha256": sigillato.sha256}
