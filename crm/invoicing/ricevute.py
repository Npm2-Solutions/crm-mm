# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The invoices the centre's suppliers sent: the Invoices page's «Received» tab.

They arrive through Itala with the SdI's updates (`sdi.riconciliazione`), each
filed with its own XML and the amounts read out of it (`engine.fornitori`).
Here: the list, one invoice with its lines, what the desk does with it (seen,
passed to the accountant, disputed, paid), Itala's PDF to read it, and the month's
files for the accountant, issued and received together.

A register, not a ledger: nothing here posts anything. Whoever manages invoicing is
told when one arrives (`annuncia`).
"""

from __future__ import annotations

import io
import zipfile

import frappe
from frappe import _
from frappe.utils import cint, fmt_money, get_first_day, get_last_day, getdate

from crm.invoicing.engine import fornitori

FORNITORE = "CRM Supplier Invoice"
FATTURA = "CRM Invoice"

#: What the desk can say of one: arrived, seen, passed to the accountant, disputed.
STATI = ("ricevuta", "letta", "registrata", "rifiutata")

CAMPI = [
	"name",
	"company",
	"supplier_name",
	"supplier_tax_id",
	"document_type",
	"document_number",
	"document_date",
	"total_amount",
	"taxable_amount",
	"vat_amount",
	"currency",
	"due_date",
	"paid_on",
	"status",
	"received_on",
]


@frappe.whitelist()
def get_received(
	company: str = "",
	status: str = "",
	search: str = "",
	from_date: str = "",
	to_date: str = "",
	limit: int = 100,
) -> dict:
	"""The list, newest first, with what it adds up to."""
	frappe.has_permission(FORNITORE, "read", throw=True)
	filtri: dict = {}
	if company:
		filtri["company"] = company
	if status == "da_pagare":
		filtri["paid_on"] = ["is", "not set"]
		filtri["status"] = ["!=", "rifiutata"]
	elif status in STATI:
		filtri["status"] = status
	if from_date and to_date:
		filtri["document_date"] = ["between", [from_date, to_date]]
	altri = None
	if search:
		parola = f"%{search.strip()}%"
		altri = [
			[FORNITORE, "supplier_name", "like", parola],
			[FORNITORE, "document_number", "like", parola],
			[FORNITORE, "supplier_tax_id", "like", parola],
		]
	righe = frappe.get_list(
		FORNITORE,
		filters=filtri,
		or_filters=altri,
		fields=CAMPI,
		order_by="document_date desc, received_on desc",
		limit_page_length=min(max(cint(limit) or 100, 1), 500),
	)
	return {
		"rows": righe,
		"total": sum(float(r.total_amount or 0) for r in righe if r.status != "rifiutata"),
		"to_see": sum(1 for r in righe if r.status == "ricevuta"),
	}


@frappe.whitelist()
def get_received_invoice(name: str) -> dict:
	"""One invoice: its fields, the lines its XML says, and what may be done."""
	doc = frappe.get_doc(FORNITORE, name)
	doc.check_permission("read")
	vista = {campo: doc.get(campo) for campo in CAMPI}
	vista["notes"] = doc.notes
	vista["xml_file"] = doc.xml_file
	vista["pdf_file"] = doc.pdf_file
	letta = _letta(doc)
	vista["lines"] = [
		{
			"description": riga.descrizione,
			"qty": float(riga.quantita) if riga.quantita is not None else None,
			"amount": float(riga.prezzo_totale),
			"vat_rate": float(riga.aliquota_iva),
			"nature": riga.natura,
		}
		for riga in (letta.righe if letta else [])
	]
	scrive = frappe.has_permission(FORNITORE, "write", doc=doc)
	vista["can"] = {
		"write": bool(scrive),
		"pdf": bool(doc.pdf_file or doc.provider_id),
	}
	return vista


def _letta(doc):
	if not doc.xml_file:
		return None
	contenuto = _contenuto(doc.xml_file)
	return fornitori.leggi(contenuto) if contenuto else None


def _contenuto(url: str) -> bytes | None:
	try:
		file = frappe.get_doc("File", {"file_url": url})
	except frappe.DoesNotExistError:
		return None
	contenuto = file.get_content(encodings=[])
	return contenuto.encode() if isinstance(contenuto, str) else contenuto


@frappe.whitelist(methods=["POST"])
def set_received_status(name: str, status: str, notes: str | None = None) -> dict:
	"""Seen, passed to the accountant, disputed - or back to arrived."""
	if status not in STATI:
		frappe.throw(_("Unknown state {0}").format(status))
	doc = frappe.get_doc(FORNITORE, name)
	doc.check_permission("write")
	if status == "rifiutata" and not (notes or doc.notes or "").strip():
		frappe.throw(_("Say why it is disputed: the supplier will ask."))
	doc.status = status
	if notes is not None:
		doc.notes = notes
	doc.save()
	return get_received_invoice(name)


@frappe.whitelist(methods=["POST"])
def set_received_paid(name: str, paid_on: str | None = None) -> dict:
	"""Paid on a day, or not paid after all (no day)."""
	doc = frappe.get_doc(FORNITORE, name)
	doc.check_permission("write")
	doc.paid_on = getdate(paid_on) if paid_on else None
	doc.save()
	return get_received_invoice(name)


@frappe.whitelist(methods=["POST"])
def make_received_pdf(name: str) -> dict:
	"""The PDF to read it by, asked of Itala once and kept with the invoice."""
	from crm.invoicing import connessione
	from crm.invoicing.sdi import itala

	doc = frappe.get_doc(FORNITORE, name)
	doc.check_permission("read")
	if doc.pdf_file:
		return {"file": doc.pdf_file}
	if not doc.provider_id:
		frappe.throw(_("This invoice did not come through Itala: there is no PDF to ask for."))
	emittente = frappe.get_doc("CRM Invoicing Company", doc.company).as_dict()
	try:
		contenuto = itala.pdf(emittente, doc.provider_id)
	except connessione.ErroreProvider as errore:
		frappe.throw(str(errore), title=_("Itala"))
	if not contenuto:
		frappe.throw(_("Itala has no PDF of this invoice: its XML is the original."))
	allegato = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": f"{(doc.sdi_filename or doc.name).rsplit('.', 1)[0]}.pdf",
			"attached_to_doctype": FORNITORE,
			"attached_to_name": doc.name,
			"attached_to_field": "pdf_file",
			"is_private": 1,
			"content": contenuto,
		}
	).insert(ignore_permissions=True)
	doc.db_set("pdf_file", allegato.file_url, update_modified=False)
	return {"file": allegato.file_url}


@frappe.whitelist()
def export_month(company: str, year: int, month: int) -> None:
	"""The month's files for the accountant, as one ZIP: the electronic invoices
	issued (as transmitted, else as made) and the ones received. Test invoices are
	the centre's rehearsal: they are left out."""
	from crm.permissions.livelli import verifica_nel_crm

	verifica_nel_crm("fatture.esporta", messaggio=_("You are not allowed to export invoices"))
	frappe.has_permission(FATTURA, "read", throw=True)
	frappe.has_permission(FORNITORE, "read", throw=True)
	primo = get_first_day(f"{cint(year):04d}-{cint(month):02d}-01")
	ultimo = get_last_day(primo)
	periodo = ["between", [primo, ultimo]]

	emesse = frappe.get_list(
		FATTURA,
		filters={"company": company, "docstatus": 1, "test_document": 0, "posting_date": periodo},
		fields=["name", "xml_file", "sdi_sent_file", "sdi_filename"],
		limit_page_length=0,
	)
	ricevute = frappe.get_list(
		FORNITORE,
		filters={"company": company, "document_date": periodo},
		fields=["name", "xml_file", "sdi_filename"],
		limit_page_length=0,
	)

	memoria = io.BytesIO()
	with zipfile.ZipFile(memoria, "w", zipfile.ZIP_DEFLATED) as archivio:
		for cartella, righe, campi in (
			("emesse", emesse, ("sdi_sent_file", "xml_file")),
			("ricevute", ricevute, ("xml_file",)),
		):
			for riga in righe:
				url = next((riga.get(c) for c in campi if riga.get(c)), None)
				contenuto = _contenuto(url) if url else None
				if contenuto:
					nome = riga.get("sdi_filename") or url.rsplit("/", 1)[-1]
					archivio.writestr(f"{cartella}/{nome}", contenuto)

	frappe.local.response.filename = f"fatture-{primo.strftime('%Y-%m')}.zip"
	frappe.local.response.filecontent = memoria.getvalue()
	frappe.local.response.type = "download"


def annuncia(name: str) -> None:
	"""Whoever manages invoicing is told a supplier's invoice arrived. Never raises:
	an invoice filed is worth more than the notification about it."""
	try:
		from crm.notifiche import regole as R
		from crm.notifiche.avvisi import avvisa

		doc = frappe.get_doc(FORNITORE, name)
		importo = fmt_money(doc.total_amount or 0, currency=doc.currency or "EUR")
		chi = doc.supplier_name or doc.supplier_tax_id or _("A supplier")
		for utente in frappe.get_all(
			"Has Role", filters={"role": "Invoicing Manager", "parenttype": "User"}, pluck="parent"
		):
			avvisa(
				utente,
				"Invoicing",
				R.FATTURA_FORNITORE,
				[chi, importo],
				oggetto=(FORNITORE, name),
				una_volta=True,
			)
	except Exception:
		frappe.log_error(title=f"Supplier invoice {name}: notification", message=frappe.get_traceback())
