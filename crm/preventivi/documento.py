# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A quote's PDF, as it is handed over: made once when it is proposed, kept private
with the quote (`templates/preventivo.html`)."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import formatdate, get_fullname, getdate, now_datetime

from crm.preventivi import regole as R
from crm.preventivi.api import DOCTYPE, leggi_voce

MODELLO = "crm/preventivi/templates/preventivo.html"


def _contesto(doc) -> dict:
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
		"_": _,
	}


def html(doc) -> str:
	return frappe.render_template(MODELLO, _contesto(doc))  # nosemgrep: frappe-ssti — literal template path


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
