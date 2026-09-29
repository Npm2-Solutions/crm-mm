# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The PDF of a signed form: made once, at signing, and kept.

Rendered from `templates/modulo_firmato.html` by WeasyPrint, then turned into
PDF/A-3b by the engine invoicing already has (`crm.invoicing.engine.pdfa`), which
also re-reads what it produced and says what came out. The file that proves a
signature is the one made then: its SHA-256 is stored on the form, and a PDF made
again later would be a different file, so it is never made again.

Everything the page shows is inside it: the signatures travel as images in the
HTML, nothing is fetched from a server, and the fonts are the system's.
"""

from __future__ import annotations

import base64
import json

import frappe
from frappe import _
from frappe.utils import format_datetime, formatdate, get_fullname, get_system_timezone, getdate

from crm.moduli import schema as S
from crm.moduli import traccia

MODELLO_HTML = "crm/moduli/templates/modulo_firmato.html"

VESTI = {"patient": "The patient", "operator": "The operator", "guardian": "A parent or guardian"}
LIVELLI = {"simple": "Simple signature", "advanced": "Advanced signature", "qualified": "Qualified signature"}
METODI = {
	"Drawn": "drawn on the screen",
	"On paper": "on paper, scanned",
	"Provider": "with a signature provider",
}
EVENTI = {
	"created": "Started",
	"answers_saved": "Answers saved",
	"signed": "Signed",
	"pdf_generated": "PDF made",
	"consent_recorded": "Consent recorded",
	"sent": "Sent",
	"opened": "Opened",
	"code_sent": "Code sent",
	"code_verified": "Code checked",
}


def _numero(valore, unita=None) -> str:
	testo = str(valore)
	return f"{testo} {unita}" if unita else testo


def risposta_in_parole(campo: dict, valore, fascia: str | None = None) -> str:
	"""An answer as a person reads it on paper."""
	if S.vuoto(valore):
		return ""
	tipo = campo.get("type")
	if tipo in ("number", "calc"):
		return _numero(valore, campo.get("unit"))
	if tipo == "score":
		return f"{valore} · {fascia}" if fascia else str(valore)
	if tipo in ("yesno",):
		return _("Yes") if valore else _("No")
	if tipo == "consent":
		return _("Agreed") if valore else _("Did not agree")
	if tipo == "date":
		return formatdate(valore)
	if tipo == "choice":
		return ", ".join(valore) if isinstance(valore, list) else str(valore)
	if tipo == "scale":
		estremi = " – ".join(filter(None, [campo.get("min_label"), campo.get("max_label")]))
		return f"{valore} ({estremi})" if estremi else str(valore)
	if tipo == "sides":
		unita = campo.get("unit") or ""
		parti = []
		if not S.vuoto(valore.get("left")):
			parti.append(_("Left: {0}").format(f"{valore['left']} {unita}".strip()))
		if not S.vuoto(valore.get("right")):
			parti.append(_("Right: {0}").format(f"{valore['right']} {unita}".strip()))
		return " · ".join(parti)
	if tipo == "attachment":
		file = valore if isinstance(valore, list) else [valore]
		return ", ".join(f.rsplit("/", 1)[-1] for f in file)
	return str(valore)


def _immagine(file_url: str | None) -> str | None:
	"""A signature as a data URI: inside the PDF, never fetched."""
	if not file_url:
		return None
	try:
		contenuto = frappe.get_doc("File", {"file_url": file_url}).get_content(encodings=[])
	except Exception:
		return None
	if isinstance(contenuto, str):
		contenuto = contenuto.encode()
	return "data:image/png;base64," + base64.b64encode(contenuto).decode()


def contesto(doc, versione) -> dict:
	"""What the page shows: the answers in the order of the form, the signatures,
	and the evidence."""
	schema = json.loads(versione.schema) if isinstance(versione.schema, str) else versione.schema
	risposte = json.loads(doc.answers or "{}") if isinstance(doc.answers, str) else (doc.answers or {})
	stato = S.valuta(schema, risposte)
	avvisi = {avviso["field"]: avviso["message"] for avviso in stato["stops"]}
	firme = {riga.field: riga for riga in doc.signatures}

	sezioni = []
	for sezione in S.sezioni(schema):
		if not stato["sections"].get(sezione.get("id")):
			continue
		voci = []
		for campo in S.campi_della_sezione(sezione):
			chiave = campo.get("id")
			if not stato["visible"].get(chiave):
				continue
			voce = {
				"tipo": campo.get("type"),
				"etichetta": campo.get("label") or "",
				"avviso": avvisi.get(chiave),
			}
			valore = stato["values"].get(chiave)
			if voce["tipo"] == "paragraph":
				voce["testo"] = campo.get("text") or ""
			elif voce["tipo"] == "signature":
				riga = firme.get(chiave)
				voce["immagine"] = _immagine(riga.image) if riga else None
				voce["firmatario"] = riga.signer_name if riga else None
			elif voce["tipo"] == "consent":
				voce["testo"] = campo.get("text") or ""
				voce["risposta"] = risposta_in_parole(campo, valore)
			elif voce["tipo"] == "table":
				colonne = [c for c in campo.get("columns") or [] if isinstance(c, dict)]
				voce["colonne"] = [c.get("label") for c in colonne]
				voce["righe"] = [
					[
						risposta_in_parole({"type": c.get("type") or "text"}, (riga or {}).get(c.get("id")))
						for c in colonne
					]
					for riga in (valore or [])
				]
			else:
				voce["risposta"] = risposta_in_parole(campo, valore, stato["bands"].get(chiave))
			voci.append(voce)
		sezioni.append(
			{"titolo": sezione.get("title"), "descrizione": sezione.get("description"), "voci": voci}
		)

	etichette = {campo.get("id"): campo.get("label") for campo in S.campi(schema)}
	return {
		"doc": doc,
		"versione": versione,
		"titolo": doc.title,
		"lingua": (frappe.local.lang or "it")[:2],
		"centro": frappe.db.get_single_value("FCRM Settings", "brand_name")
		if frappe.get_meta("FCRM Settings").has_field("brand_name")
		else None,
		"persona": doc.lead_name or doc.lead,
		"dato_da": frappe.db.get_value("CRM Lead", doc.given_by, "lead_name") if doc.given_by else None,
		"firmato_il": format_datetime(doc.signed_on),
		"pubblicata_il": formatdate(getdate(versione.published_on)),
		"canale": _(doc.channel),
		"compilato_da": get_fullname(doc.filled_by) if doc.filled_by else None,
		"sezioni": sezioni,
		"firme": [
			{
				"etichetta": etichette.get(riga.field) or riga.field,
				"chi": riga.signer_name,
				"veste": _(VESTI.get(riga.signer, riga.signer)),
				"livello": _(LIVELLI.get(riga.level, riga.level)),
				"metodo": _(METODI.get(riga.method, riga.method)),
				"quando": f"{format_datetime(riga.signed_at)} ({get_system_timezone()})",
				"ip": riga.ip_address,
				"dispositivo": riga.user_agent,
				"impronta": riga.document_hash,
			}
			for riga in doc.signatures
		],
		"eventi": [
			{
				"quando": format_datetime(evento.occurred_on),
				"cosa": _(EVENTI.get(evento.event, evento.event)),
				"chi": get_fullname(evento.user) if evento.user else None,
				"ip": evento.ip_address,
			}
			for evento in traccia.eventi(doc.doctype, doc.name)
		],
		"_": _,
	}


def html(doc, versione) -> str:
	return frappe.render_template(MODELLO_HTML, contesto(doc, versione))


def rendi(doc, versione) -> bytes:
	"""The bytes as rendered, before PDF/A. Separate, so a test can swap it."""
	from weasyprint import HTML

	return HTML(string=html(doc, versione)).write_pdf()


def genera_e_allega(doc) -> dict:
	"""Make the PDF/A once and attach it, private. Never raises on a rendering
	problem: a signed form without its PDF is still signed, and the failure says
	so in the register and in the log."""
	from crm.invoicing.engine import pdfa

	if doc.pdf_file:
		return {"skipped": True, "file": doc.pdf_file}
	versione = frappe.get_doc("CRM Form Template Version", doc.template_version)
	try:
		reso = rendi(doc, versione)
	except Exception as errore:
		frappe.log_error(title=f"Form PDF {doc.name}", message=frappe.get_traceback())
		traccia.traccia(doc.doctype, doc.name, "pdf_failed", str(errore)[:500])
		return {"skipped": True, "reason": str(errore)}

	risultato = pdfa.converti(reso, titolo=doc.title or doc.name, data_documento=getdate(doc.signed_on))
	allegato = frappe.get_doc(
		{
			"doctype": "File",
			# a neutral name: the file name should not say what the form was about
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
	traccia.traccia(
		doc.doctype,
		doc.name,
		"pdf_generated",
		risultato.conformita,
		{"sha256": risultato.sha256, "bytes": risultato.byte},
	)
	return {"file": allegato.file_url, "sha256": risultato.sha256, "conformance": risultato.conformita}
