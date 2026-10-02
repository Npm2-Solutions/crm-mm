# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The invoice made inside DottorCloud.

The Desk's form asked whoever was at the desk to know what a FatturaPA field is.
Here an invoice is what the desk sees: who it is for, what was done and by whom,
how it was paid and - before anything is issued - where it is going: to the
patient as a PDF and the expense to the Sistema TS, or to the SdI. Everything else
is the engine's, and every answer comes back in words.

A new invoice lives in memory until it is saved: the preview classifies and adds up
a document that does not exist yet, so nothing half-typed is left behind, and a
draft is saved only when somebody says so.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate

from crm.invoicing import documento, prova, scelte
from crm.invoicing.engine import voci
from crm.invoicing.engine.codici import Canale, TipoDestinatario
from crm.permissions.livelli import puo

FATTURA = "CRM Invoice"

#: What the dialog may write on a draft: the client, how it was paid, the lines.
#: Everything else - the fund, the withholding, the stamp duty, the channel - the
#: company and the engine decide.
CAMPI_CLIENTE = (
	"party_type",
	"party",
	"billing_name",
	"first_name",
	"last_name",
	"fiscal_code",
	"tax_id",
	"recipient_type",
	"recipient_code",
	"pec",
	"address_line",
	"civic_number",
	"postal_code",
	"city",
	"province",
	"country",
)
CAMPI_PAGAMENTO = ("payment_method", "payment_date", "advance_payment", "privacy_opposition", "causale")
CAMPI_RIGA = ("billable_service", "service_provider", "description", "qty", "rate")

#: Credit and debit notes: the amount reads the other way, and they say which
#: document they correct.
NOTE = ("TD04", "TD05", "TD08", "TD09")


def _iva(riga) -> str:
	"""A line's VAT in words: «Esente (art. 10)», «IVA 22%»."""
	if riga.vat_exempt:
		return _(voci.etichetta("natura", "N4"))
	if riga.vat_nature:
		return _(voci.etichetta("natura", riga.vat_nature))
	return _("VAT {0}%").format(f"{flt(riga.vat_rate):g}")


def _nome_di(doctype: str | None, nome: str | None) -> str:
	"""A record by its title, as a person reads it."""
	if not (doctype and nome):
		return ""
	campo = frappe.get_meta(doctype).title_field
	return (frappe.db.get_value(doctype, nome, campo) if campo else None) or nome


def _scelta(famiglia: str, valore: str | None) -> dict:
	voce = next((v for v in voci.tutte(famiglia) if v.valore == valore), None)
	return {
		"value": valore or "",
		"label": _(voce.etichetta) if voce else (valore or ""),
		"description": _(voce.spiegazione) if voce and voce.spiegazione else "",
	}


def _applica(doc, dati: dict) -> None:
	"""What the dialog sent, on the document: only what it may write."""
	for campo in (*CAMPI_CLIENTE, *CAMPI_PAGAMENTO):
		if campo in dati:
			doc.set(campo, dati.get(campo))
	if "items" in dati:
		doc.set("items", [])
		for riga in dati.get("items") or []:
			if not riga.get("billable_service"):
				continue
			doc.append(
				"items",
				{
					"billable_service": riga.get("billable_service"),
					"service_provider": riga.get("service_provider"),
					"description": riga.get("description") or "",
					"qty": flt(riga.get("qty")) or 1,
					"rate": flt(riga.get("rate")),
				},
			)


def _totali(doc, conto=None) -> dict:
	if conto is not None:
		return {
			"net_total": float(conto.imponibile),
			"fund_contribution": float(conto.cassa),
			"vat_total": float(conto.iva),
			"advances": float(conto.anticipazioni),
			"stamp_duty": float(conto.bollo),
			"withholding": float(conto.ritenuta),
			"grand_total": float(conto.totale),
			"net_payable": float(conto.netto_a_pagare),
			"ts_total": float(conto.totale_ts),
		}
	return {
		"net_total": flt(doc.net_total),
		"fund_contribution": flt(doc.fund_contribution),
		"vat_total": flt(doc.vat_total),
		"advances": flt(doc.excluded_total),
		"stamp_duty": flt(doc.stamp_duty),
		"withholding": flt(doc.withholding_amount),
		"grand_total": flt(doc.grand_total),
		"net_payable": flt(doc.net_payable),
		"ts_total": flt(doc.ts_total),
	}


def _da_completare(doc) -> list[str]:
	"""What keeps the engine from classifying the lines yet, said as what is missing.

	Each line takes its card's price and words first, so the amounts show while
	somebody is still choosing who performed it."""
	mancano = []
	for riga in doc.get("items") or []:
		dati = documento.scheda(riga.billable_service)
		documento.applica_scheda(riga, dati)
		documento.importo_riga(riga)
		if not dati.get("enabled"):
			mancano.append(
				_("The service {0} is disabled: re-enable it or pick another one").format(
					riga.billable_service
				)
			)
		if not riga.service_provider:
			mancano.append(
				_("Line {0}: say who performed it. It decides the expense type and the VAT regime").format(
					riga.idx
				)
			)
	return mancano


def _vista(doc) -> dict:
	"""The invoice as the dialog draws it: everything in words."""
	bozza = cint(doc.docstatus) == 0
	errori, avvisi, totali = [], [], None
	if bozza and doc.get("items"):
		errori = _da_completare(doc)
		if not errori:
			preparato = documento.prepara(doc)
			errori, avvisi = documento.da_correggere(doc, preparato)
			totali = _totali(doc, preparato["calcolo"])
	elif bozza:
		errori = [_("Add what was done: a service, and who performed it")]
		totali = _totali(doc)
	else:
		totali = _totali(doc)
		# what was found when it was issued: the Sistema TS's report, the engine's notes
		avvisi = [riga for riga in (doc.warnings or "").splitlines() if riga.strip()]

	scelte_fattura = scelte.get_options(FATTURA, doc.as_dict())
	return {
		"name": doc.name if not doc.is_new() else None,
		"docstatus": cint(doc.docstatus),
		"document_number": doc.document_number,
		# issued in test, or - a draft - to be issued while the company is in test
		"test": bool(cint(doc.test_document)) if not bozza else _in_prova(doc.company),
		"document_type": _scelta("tipo_documento", doc.document_type or "TD01"),
		"is_note": (doc.document_type or "") in NOTE,
		"posting_date": str(getdate(doc.posting_date)) if doc.posting_date else None,
		"company": doc.company,
		"client": {
			**{campo: doc.get(campo) for campo in CAMPI_CLIENTE},
			"party_label": _nome_di(doc.party_type, doc.party),
		},
		"payment": {campo: doc.get(campo) for campo in CAMPI_PAGAMENTO},
		"items": [
			{
				"name": riga.name if not doc.is_new() else None,
				**{campo: riga.get(campo) for campo in CAMPI_RIGA},
				"service_label": _nome_di("CRM Billable Service", riga.billable_service),
				"provider_label": _nome_di("CRM Service Provider", riga.service_provider),
				"amount": flt(riga.amount),
				"healthcare": cint(riga.is_healthcare),
				"vat": _iva(riga),
			}
			for riga in doc.get("items") or []
		],
		# where it goes is known once every line is classified
		"destination": _scelta("canale_documento", doc.channel) if doc.channel and totali else None,
		"errors": errori,
		"warnings": avvisi,
		# none while a line is incomplete: a total without the fund and the stamp
		# would be a number that is not the invoice's
		"totals": totali,
		"options": {
			"recipient_type": scelte_fattura["fields"].get("recipient_type", []),
			"payment_method": scelte_fattura["fields"].get("payment_method", []),
		},
		# where it is on its way: only for a document that has left
		"states": {
			"sdi": _stato(doc.sdi_status) if not bozza else "",
			"ts": _stato(doc.ts_status) if not bozza else "",
		},
		"pdf": doc.pdf_file,
		# what the SdI said when it refused it: the thing to correct
		"rejection": doc.sdi_message if doc.sdi_status == "scartata" else None,
		# what the SdI's own checks found in the file before it leaves, each with its code
		"findings": [riga for riga in (doc.sdi_message or "").splitlines() if riga.strip()]
		if doc.sdi_status == "da_inviare"
		else [],
		"reference": {
			"name": doc.reference_invoice,
			"number": frappe.db.get_value(FATTURA, doc.reference_invoice, "document_number")
			if doc.reference_invoice
			else None,
		},
		"shape": _forma(doc.company),
		"can": _puo(doc),
	}


def _stato(stato: str | None) -> str:
	"""A transmission state, as the Agenzia words it: «Da inviare», not `da_inviare`."""
	if not stato or stato == "non_applicabile":
		return ""
	if stato == "prova":
		return _("Test: checked, not sent")
	parole = stato.replace("_", " ")
	return parole[:1].upper() + parole[1:]


def _in_prova(company: str | None) -> bool:
	if not company:
		return False
	return prova.in_prova(frappe.get_cached_doc("CRM Invoicing Company", company).as_dict())


def _forma(company: str | None) -> dict:
	"""One professional or more: with one, the line does not ask who performed."""
	filtri = {"enabled": 1}
	erogatori = [
		riga
		for riga in frappe.get_all("CRM Service Provider", filters=filtri, fields=["name", "company"])
		if not riga.company or riga.company == company
	]
	return {"solo": len(erogatori) == 1, "provider": erogatori[0].name if len(erogatori) == 1 else None}


def _puo(doc) -> dict:
	emessa = cint(doc.docstatus) == 1
	# a test invoice of a company gone live goes nowhere, and needs no correcting
	superata = bool(cint(doc.test_document)) and not _in_prova(doc.company)
	return {
		"save": not emessa and frappe.has_permission(FATTURA, "write" if not doc.is_new() else "create"),
		"issue": not emessa and frappe.has_permission(FATTURA, "submit"),
		# a draft with a number is a rejected invoice being corrected: thrown away,
		# it would leave a hole in the numbering
		"delete": not emessa
		and not doc.is_new()
		and not doc.document_number
		and frappe.has_permission(FATTURA, "delete"),
		"transmit": emessa
		and not superata
		and doc.channel == Canale.SDI
		and doc.sdi_status == "da_inviare"
		and puo("fatture.invia"),
		# refused by the SdI it counts as never issued: corrected with the same number
		"reopen": emessa and doc.sdi_status == "scartata" and frappe.has_permission(FATTURA, "submit"),
		"credit_note": emessa
		and not superata
		and (doc.document_type or "TD01") not in NOTE
		and frappe.has_permission(FATTURA, "create"),
		"pdf": emessa and bool(doc.pdf_file),
		"make_pdf": emessa and not doc.pdf_file,
	}


def _carica(invoice: str | None, dati: dict | None):
	"""The draft being edited: the stored one with what the dialog changed, or a new
	one in memory. Nothing is written here."""
	if invoice:
		doc = frappe.get_doc(FATTURA, invoice)
		doc.check_permission("write" if cint(doc.docstatus) == 0 else "read")
	else:
		frappe.has_permission(FATTURA, "create", throw=True)
		doc = frappe.new_doc(FATTURA)
		doc.recipient_type = TipoDestinatario.PERSONA_FISICA
	if dati and cint(doc.docstatus) == 0:
		prima = doc.recipient_type
		_applica(doc, dati)
		if not doc.is_new() and doc.recipient_type != prima:
			# who it is for decides the withholding, as on the first save: never
			# towards a private person (art. 23, c. 1, DPR 600/73)
			doc.apply_withholding = int(
				bool(documento.azienda(doc).get("apply_withholding_by_default"))
				and doc.recipient_type != TipoDestinatario.PERSONA_FISICA
			)
	if doc.is_new():
		# the company's choices, copied as the first save will copy them: the
		# preview adds up what the invoice will add up to
		doc.before_insert()
	if cint(doc.docstatus) == 0:
		# the client's name and details come from the record and their profile
		doc.compila_da_controparte()
		doc.applica_predefiniti()
	return doc


@frappe.whitelist()
def get_invoice(invoice: str) -> dict:
	"""An invoice, issued or draft, as the dialog draws it."""
	doc = frappe.get_doc(FATTURA, invoice)
	doc.check_permission("read")
	return _vista(doc)


@frappe.whitelist(methods=["POST"])
def preview(data: str | dict, invoice: str | None = None) -> dict:
	"""Where a draft would go, what it adds up to and what is still wrong, while it is
	being typed: classified and computed in memory, never saved."""
	return _vista(_carica(invoice, frappe.parse_json(data) if isinstance(data, str) else data))


@frappe.whitelist(methods=["POST"])
def save(data: str | dict, invoice: str | None = None) -> dict:
	"""Keep the draft: inserted the first time, updated after."""
	doc = _carica(invoice, frappe.parse_json(data) if isinstance(data, str) else data)
	if cint(doc.docstatus) != 0:
		frappe.throw(_("An issued invoice is not changed: correct it with a credit note"))
	if invoice:
		doc.save()
	else:
		doc.insert()
	return _vista(doc)


@frappe.whitelist(methods=["POST"])
def issue(data: str | dict, invoice: str | None = None) -> dict:
	"""Save and issue: the number, the files, and where it goes."""
	frappe.has_permission(FATTURA, "submit", throw=True)
	doc = _carica(invoice, frappe.parse_json(data) if isinstance(data, str) else data)
	if cint(doc.docstatus) != 0:
		frappe.throw(_("This invoice has already been issued"))
	if not invoice:
		doc.insert()
	doc.submit()
	doc.reload()
	return _vista(doc)


@frappe.whitelist(methods=["POST"])
def credit_note(invoice: str) -> dict:
	"""A credit note for an issued invoice, as a draft: the same client and the same
	lines, saying which document it corrects. For a document reported to the
	Sistema TS it is a refund (operazione R) of the original."""
	originale = frappe.get_doc(FATTURA, invoice)
	originale.check_permission("read")
	frappe.has_permission(FATTURA, "create", throw=True)
	if cint(originale.docstatus) != 1:
		frappe.throw(_("Only an issued invoice is corrected with a credit note"))
	if (originale.document_type or "") in NOTE:
		frappe.throw(_("A credit note is not corrected with another credit note"))
	if cint(originale.test_document) and not _in_prova(originale.company):
		frappe.throw(
			_("The invoice it corrects was a test: it has no fiscal value, and needs no credit note.")
		)

	nota = frappe.new_doc(FATTURA)
	nota.company = originale.company
	nota.document_type = "TD04"
	nota.reference_invoice = originale.name
	for campo in (*CAMPI_CLIENTE, "payment_method", "privacy_opposition", "appointment", "deal"):
		nota.set(campo, originale.get(campo))
	nota.causale = _("Credit note for invoice {0}").format(originale.document_number)
	if originale.channel == Canale.PDF_TS:
		# the money goes back to the patient on the day of the note
		nota.ts_operation = "R"
	for riga in originale.items:
		nota.append("items", {campo: riga.get(campo) for campo in CAMPI_RIGA})
	nota.insert()
	return _vista(nota)


@frappe.whitelist(methods=["POST"])
def delete_draft(invoice: str) -> dict:
	"""Throw a draft away: it has no number yet, so nothing is lost."""
	doc = frappe.get_doc(FATTURA, invoice)
	if cint(doc.docstatus) != 0:
		frappe.throw(_("Only a draft can be thrown away"))
	if doc.document_number:
		frappe.throw(_("This invoice already has its number: correct it and issue it again"))
	doc.check_permission("delete")
	frappe.delete_doc(FATTURA, invoice)
	return {"deleted": invoice}
