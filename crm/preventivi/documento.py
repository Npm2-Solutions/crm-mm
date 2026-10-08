# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A quote's PDF, as it is handed over: made once when it is proposed, kept private
with the quote (`templates/preventivo.html`).

Accepted and signed in the client area (`crm.preventivi.firma`), its signed copy:
the same pages with the person's signature where the lines to sign were, and the
evidence after them - who, when by the server's clock, from where, how they were
known, the fingerprint of what they signed, the quote's register. Made once, as
PDF/A, with the centre's seal and time stamp where the agency installed them, as a
signed form's (`crm.moduli.pdf`)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import formatdate, get_fullname, getdate, now_datetime

from crm import marchio
from crm.preventivi import regole as R
from crm.preventivi.api import DOCTYPE, leggi_voce

MODELLO = "crm/preventivi/templates/preventivo.html"


def _contesto(doc, firma: dict | None = None) -> dict:
	from crm.moduli.richieste import nome_del_centro
	from crm.verticali import parola

	voci = [leggi_voce(voce) for voce in doc.items if voce.status != R.ANNULLATA]
	gruppi = [{"phase": fase, "items": [voci[n] for n in posizioni]} for fase, posizioni in R.fasi(voci)]
	return {
		"doc": doc,
		"centro": nome_del_centro(),
		"titolo": doc.title,
		"lingua": (frappe.local.lang or "it")[:2],
		"persona": doc.lead_name,
		"autore": get_fullname(doc.practitioner),
		"data": formatdate(getdate(doc.proposed_on or now_datetime())),
		"valido_fino": formatdate(doc.valid_until) if doc.valid_until else None,
		"fasi": gruppi,
		"piu_fasi": len(gruppi) > 1,
		"totali": R.totali(voci),
		"valuta": doc.currency or "EUR",
		"soldi": lambda valore: frappe.utils.fmt_money(valore, currency=doc.currency or "EUR"),
		"parola": parola,
		"firma": firma,
		"_": _,
	}


def html(doc, firma: dict | None = None) -> str:
	# nosemgrep: frappe-ssti — literal template path
	return frappe.render_template(MODELLO, _contesto(doc, firma))


def fai_il_pdf(doc) -> None:
	"""The quote as it is handed over, kept private with it. One that cannot be made
	does not stop the proposal: the log says so."""
	from crm.moduli import pdf

	try:
		dati = pdf.pdf_da_html(html(doc))
	except Exception:
		frappe.log_error(title=f"Quote PDF {doc.name}", message=frappe.get_traceback())
		return
	allegato = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": f"{doc.name}.pdf",
			"attached_to_doctype": DOCTYPE,
			"attached_to_name": doc.name,
			"attached_to_field": "quote_pdf",
			"is_private": 1,
			"content": dati,
		}
	).insert(ignore_permissions=True)
	doc.db_set("quote_pdf", allegato.file_url, update_modified=False)


#: How the quote's register names its events, on the evidence page.
EVENTI = {
	"sent": "Sent to sign",
	"opened": "Opened in the client area",
	"copy_downloaded": "Copy downloaded",
	"signed": "Accepted and signed",
	"declined": "Declined by the person",
	"pdf_generated": "PDF made",
	"pdf_failed": "PDF not made",
	"sealed": "Sealed by the centre",
	"seal_failed": "Not sealed",
}
VESTI = {"patient": "The person", "guardian": "A parent or guardian"}


def _prove(doc, veste: str, riconoscimento: str) -> dict:
	"""What the evidence page says of the signature, from what the quote keeps."""
	import base64

	from frappe.utils import format_datetime, get_system_timezone

	from crm.moduli import traccia

	immagine = None
	if doc.signature:
		contenuto = frappe.get_doc("File", {"file_url": doc.signature}).get_content(encodings=[])
		immagine = "data:image/png;base64," + base64.b64encode(contenuto).decode("ascii")
	return {
		"immagine": immagine,
		"chi": doc.signer_name,
		"veste": _(VESTI.get(veste, veste)),
		"quando": f"{format_datetime(doc.signed_on)} ({get_system_timezone()})",
		"ip": doc.signer_ip,
		"dispositivo": doc.signer_device,
		"impronta": doc.signed_hash,
		"su_cosa": _("Its PDF as it was proposed") if doc.quote_pdf else _("Its services and sums"),
		"riconoscimento": riconoscimento,
		"eventi": [
			{
				"quando": format_datetime(evento.occurred_on),
				"cosa": _(EVENTI.get(evento.event, evento.event)),
				"chi": get_fullname(evento.user) if evento.user else None,
				"ip": evento.ip_address,
			}
			for evento in traccia.eventi(DOCTYPE, doc.name)
		],
	}


def fai_la_copia_firmata(doc, veste: str, riconoscimento: str) -> dict:
	"""The signed copy, once: PDF/A, sealed where the centre has a seal, its
	fingerprint kept. Never raises: a quote accepted without its copy is still
	accepted, and the register and the log say why."""
	from crm.invoicing.engine import pdfa
	from crm.moduli import pdf, sigillo, traccia

	if doc.signed_pdf:
		return {"skipped": True, "file": doc.signed_pdf}
	try:
		reso = pdf.pdf_da_html(html(doc, _prove(doc, veste, riconoscimento)))
		risultato = pdfa.converti(
			reso,
			titolo=doc.title or doc.name,
			data_documento=getdate(doc.signed_on),
			produttore=marchio.nome(),
		)
	except Exception as errore:
		frappe.log_error(title=f"Signed quote PDF {doc.name}", message=frappe.get_traceback())
		traccia.traccia(DOCTYPE, doc.name, "pdf_failed", str(errore)[:500])
		return {"skipped": True, "reason": str(errore)}
	# the centre's seal before the fingerprint: the fingerprint is the kept file's
	sigillato = sigillo.sigilla(risultato.dati, motivo=_("Quote accepted and signed"))
	conformita = sigillato.descrizione(risultato.conformita)
	allegato = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": f"{doc.name}-signed.pdf",
			"attached_to_doctype": DOCTYPE,
			"attached_to_name": doc.name,
			"attached_to_field": "signed_pdf",
			"is_private": 1,
			"content": sigillato.dati,
		}
	).insert(ignore_permissions=True)
	doc.db_set(
		{
			"signed_pdf": allegato.file_url,
			"signed_pdf_hash": sigillato.sha256,
			"signed_pdf_conformance": conformita,
		},
		update_modified=False,
	)
	traccia.traccia(
		DOCTYPE,
		doc.name,
		"pdf_generated",
		risultato.conformita,
		{"sha256": sigillato.sha256, "bytes": len(sigillato.dati)},
	)
	sigillato.traccia(DOCTYPE, doc.name)
	return {"file": allegato.file_url, "sha256": sigillato.sha256, "conformance": conformita}
