# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The PDF of a signed form: made once, at signing, and kept.

Rendered from `templates/modulo_firmato.html` by WeasyPrint, then turned into
PDF/A-3b by the engine invoicing already has (`crm.invoicing.engine.pdfa`), which
also re-reads what it produced and says what came out. The file that proves a
signature is the one made then: its SHA-256 is stored on the form, and a PDF made
again later would be a different file, so it is never made again.

Everything the page shows is inside it: the signatures travel as images in the
HTML, nothing is fetched from a server, and the fonts are the system's. The
renderer is told so too (`pdf_da_html`): it loads only what is written in the
page, so an answer or a browser's name that looked like HTML could not bring a
file of the server, or a request to one, into a signed document - and the
templates escape what they print.
"""

from __future__ import annotations

import base64
import json

import frappe
from frappe import _
from frappe.utils import format_datetime, formatdate, get_fullname, get_system_timezone, getdate

from crm.moduli import compilazioni, traccia
from crm.moduli import schema as S

MODELLO_HTML = "crm/moduli/templates/modulo_firmato.html"

VESTI = {"patient": "The patient", "operator": "The operator", "guardian": "A parent or guardian"}
LIVELLI = {
	"simple": "Simple signature",
	"advanced": "Advanced signature",
	"qualified": "Qualified signature",
	"handwritten": "Handwritten signature",
}
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
	"filled": "Filled by the person, to sign at the desk",
	"printed": "Printed to sign on paper",
	"attested": "Scan attested as a true copy",
	"provider_sent": "Sent to the signature provider",
	"provider_withdrawn": "Taken back from the signature provider",
	"provider_declined": "Declined at the signature provider",
	"provider_expired": "Expired at the signature provider",
	"pdf_received": "Signed PDF received",
	"copy_downloaded": "Copy downloaded",
	"cancelled": "Cancelled",
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


def _contenuto(file_url: str) -> bytes:
	contenuto = frappe.get_doc("File", {"file_url": file_url}).get_content(encodings=[])
	return contenuto.encode() if isinstance(contenuto, str) else contenuto


def _come_immagine(contenuto: bytes) -> str | None:
	"""A scanned page as a data URI, when it is a picture (a PDF scan is merged
	as pages instead)."""
	for inizio, tipo in ((b"\x89PNG", "image/png"), (b"\xff\xd8\xff", "image/jpeg")):
		if contenuto.startswith(inizio):
			return f"data:{tipo};base64," + base64.b64encode(contenuto).decode()
	return None


def _caselle(campo: dict) -> list[str]:
	"""What a person ticks on paper for an empty answer."""
	tipo = campo.get("type")
	if tipo == "consent":
		return [_("Agreed")] if campo.get("must_accept") else [_("Agreed"), _("Did not agree")]
	if tipo == "yesno":
		return [_("Yes"), _("No")]
	if tipo == "choice":
		return [o.get("label") for o in campo.get("options") or [] if isinstance(o, dict) and o.get("label")]
	if tipo == "scale":
		minimo, massimo = int(campo.get("min") or 0), int(campo.get("max") or 10)
		return [str(n) for n in range(minimo, massimo + 1)][:21]
	return []


def _chi_firmera(campo: dict, doc) -> str | None:
	"""Who is expected to sign a field, on a copy to sign."""
	veste = compilazioni._veste(campo, doc)
	if veste == "operator":
		return None
	if veste == "guardian":
		return frappe.db.get_value("CRM Lead", doc.given_by, "lead_name") if doc.given_by else None
	return doc.lead_name or frappe.db.get_value("CRM Lead", doc.lead, "lead_name")


def contesto(doc, versione, da_firmare: bool = False) -> dict:
	"""What the page shows: the answers in the order of the form, the signatures,
	and the evidence. ``da_firmare`` is the copy to sign (on paper, or at a
	provider): room for the signatures, and no evidence of a signature yet."""
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
				voce["immagine"] = _immagine(riga.image) if riga and riga.image else None
				voce["firmatario"] = riga.signer_name if riga else None
				voce["su_carta"] = bool(riga and riga.method == "On paper")
				voce["atteso"] = _chi_firmera(campo, doc) if da_firmare else None
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
			if da_firmare and not voce.get("risposta"):
				# on paper an empty answer is given by hand: boxes to tick, or a line
				voce["opzioni"] = _caselle(campo)
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
			for evento in compilazioni.eventi_del_modulo(doc)
		],
		"riconoscimento": compilazioni.riconoscimento(doc),
		"da_firmare": da_firmare,
		"carta": _carta(doc) if not da_firmare else None,
		"_": _,
	}


def _carta(doc) -> dict | None:
	"""A form signed on paper: who attested the scan, its hash, and its pages
	when they are pictures."""
	if not doc.get("paper_file"):
		return None
	immagine = None
	try:
		immagine = _come_immagine(_contenuto(doc.paper_file))
	except Exception:
		frappe.log_error(title=f"Form scan {doc.name}", message=frappe.get_traceback())
	return {
		"attestato_da": get_fullname(doc.attested_by) if doc.attested_by else None,
		"il": f"{format_datetime(doc.attested_on)} ({get_system_timezone()})",
		"impronta": doc.paper_hash,
		"immagini": [immagine] if immagine else [],
	}


def html(doc, versione, da_firmare: bool = False) -> str:
	return frappe.render_template(MODELLO_HTML, contesto(doc, versione, da_firmare))


def _solo_nella_pagina():
	"""A fetcher for WeasyPrint that loads only a data URI: what is written in the
	page. Not a file of the server (``file://``, which WeasyPrint would even embed as
	an attachment of the PDF), not an address on the network."""
	from weasyprint.urls import URLFetcher

	class SoloNellaPagina(URLFetcher):
		def fetch(self, url, headers=None):
			if not str(url).lower().startswith("data:"):
				raise ValueError("A signed document loads nothing from outside itself")
			return super().fetch(url, headers)

	return SoloNellaPagina(allow_redirects=False)


def pdf_da_html(pagina: str) -> bytes:
	"""A document the CRM keeps, from its HTML: every resource inside it."""
	from weasyprint import HTML

	return HTML(string=pagina, url_fetcher=_solo_nella_pagina()).write_pdf()


def rendi(doc, versione, da_firmare: bool = False) -> bytes:
	"""The bytes as rendered, before PDF/A. Separate, so a test can swap it."""
	return pdf_da_html(html(doc, versione, da_firmare))


def _con_le_pagine(reso: bytes, scansione: bytes) -> bytes:
	"""The rendered form followed by the pages of a scanned PDF."""
	import io

	from pypdf import PdfReader, PdfWriter

	scrittore = PdfWriter(clone_from=PdfReader(io.BytesIO(reso)))
	scrittore.append(PdfReader(io.BytesIO(scansione)))
	uscita = io.BytesIO()
	scrittore.write(uscita)
	return uscita.getvalue()


def da_firmare(doc) -> bytes:
	"""The form as it is to be signed - on paper, or at a provider - with the
	answers so far. Not the evidence of anything: it is not kept."""
	from crm.invoicing.engine import pdfa

	versione = frappe.get_doc("CRM Form Template Version", doc.template_version)
	reso = rendi(doc, versione, da_firmare=True)
	return pdfa.converti(reso, titolo=doc.title or doc.name, data_documento=getdate()).dati


def allega_dal_fornitore(doc, firmato: bytes, prove: bytes | None, fornitore: str) -> dict:
	"""The provider's signed PDF is the form's document: kept as it came, since
	converting it would break its signature. Its audit trail goes next to it."""
	import hashlib

	allegato = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": f"{doc.name}.pdf",
			"attached_to_doctype": doc.doctype,
			"attached_to_name": doc.name,
			"attached_to_field": "pdf_file",
			"is_private": 1,
			"content": firmato,
		}
	).insert(ignore_permissions=True)
	valori = {
		"pdf_file": allegato.file_url,
		"pdf_hash": hashlib.sha256(firmato).hexdigest(),
		"pdf_conformance": _("Signed by {0} (PAdES)").format(fornitore),
	}
	if prove:
		prova = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": f"{doc.name}-evidence.pdf",
				"attached_to_doctype": doc.doctype,
				"attached_to_name": doc.name,
				"attached_to_field": "provider_evidence",
				"is_private": 1,
				"content": prove,
			}
		).insert(ignore_permissions=True)
		valori["provider_evidence"] = prova.file_url
	doc.db_set(valori, update_modified=False)
	traccia.traccia(
		doc.doctype,
		doc.name,
		"pdf_received",
		fornitore,
		{"sha256": valori["pdf_hash"], "bytes": len(firmato)},
	)
	return {"file": allegato.file_url, "sha256": valori["pdf_hash"]}


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

	originale = None
	if doc.get("paper_file"):
		# signed on paper: the scan is inside the file, as its source, and a scanned
		# PDF's pages follow the form's
		scansione = _contenuto(doc.paper_file)
		estensione = doc.paper_file.rsplit(".", 1)[-1].lower()
		originale = (f"{doc.name}-paper.{estensione}", scansione)
		if scansione.startswith(b"%PDF"):
			try:
				reso = _con_le_pagine(reso, scansione)
			except Exception as errore:
				traccia.traccia(doc.doctype, doc.name, "pdf_failed", f"scan pages: {errore}"[:500])

	risultato = pdfa.converti(
		reso,
		titolo=doc.title or doc.name,
		data_documento=getdate(doc.signed_on),
		allegato_xml=originale,
		relazione_allegato="Source",
	)
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
