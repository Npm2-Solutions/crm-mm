# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Applying what the SdI sent back.

One path for every channel: a notice is a file with a name that says which
document it answers, whether it arrived by PEC, by webhook, or because somebody
downloaded it from the portal and dropped it on the invoice.

Idempotent by name. A PEC mailbox re-delivers, a provider retries its webhook, and
a notice applied twice would move a document that had already moved on.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint

from crm.invoicing.engine import ricevute
from crm.invoicing.engine.ricevute import Ricevuta, TipoRicevuta

#: How far back the inbox scan looks. Notices arrive within minutes; a week of
#: slack covers a mailbox that was down over a weekend.
GIORNI_ARRETRATI = 7


def trova_fattura(ricevuta: Ricevuta) -> str | None:
	"""Which invoice this notice belongs to.

	The file name first, because it is the only field always present. The SdI
	identifier second, for the notices that carry one and no name.
	"""
	riferimento = ricevuta.nome_file or ricevuta.riferimento_fattura
	if riferimento:
		nome = frappe.db.get_value("CRM Invoice", {"sdi_filename": riferimento}, "name")
		if nome:
			return nome
	if ricevuta.identificativo_sdi:
		return frappe.db.get_value("CRM Invoice", {"sdi_identifier": ricevuta.identificativo_sdi}, "name")
	return None


def gia_applicata(doc, nome_ricevuta: str | None) -> bool:
	if not nome_ricevuta:
		return False
	return nome_ricevuta in (doc.sdi_notices or "").split("\n")


def applica(ricevuta: Ricevuta, nome_ricevuta: str | None = None, fattura: str | None = None) -> dict:
	"""Move the invoice to where the notice leaves it."""
	from crm.invoicing import documento

	nome = fattura or trova_fattura(ricevuta)
	if not nome:
		return {
			"applied": False,
			"reason": _("No invoice matches this notice ({0})").format(
				ricevuta.nome_file or ricevuta.identificativo_sdi or "-"
			),
		}

	doc = frappe.get_doc("CRM Invoice", nome)
	if gia_applicata(doc, nome_ricevuta):
		return {"applied": False, "invoice": nome, "reason": _("Already applied")}

	valori = {
		"sdi_status": ricevuta.stato,
		"sdi_message": ricevuta.riassunto(),
	}
	if ricevuta.identificativo_sdi:
		valori["sdi_identifier"] = ricevuta.identificativo_sdi
	if nome_ricevuta:
		notizie = [r for r in (doc.sdi_notices or "").split("\n") if r]
		valori["sdi_notices"] = "\n".join([*notizie, nome_ricevuta])
	doc.db_set(valori, update_modified=False)

	documento.registra(
		doc,
		"sdi_receipt",
		ricevuta.riassunto(),
		stato=ricevuta.tipo,
		payload={
			"notice": nome_ricevuta,
			"sdi_id": ricevuta.identificativo_sdi,
			"codes": [e.codice for e in ricevuta.errori],
		},
	)

	if ricevuta.tipo == TipoRicevuta.CONSEGNA:
		_impara_indirizzo(doc, ricevuta)
	if ricevuta.tipo == TipoRicevuta.MANCATA_CONSEGNA:
		# Not a failure, and the one that gets misread: the invoice is issued and sits
		# in the client's reserved area. What is owed is telling the client, because
		# the SdI will not.
		_avvisa(
			doc,
			_("Invoice {0} is issued but not delivered").format(doc.document_number),
			_(
				"The Sistema di Interscambio has it and filed it in the client's reserved area. "
				"The client has to be told: send them the PDF."
			),
		)
	if ricevuta.scartata:
		_avvisa(
			doc,
			_("Invoice {0} was rejected").format(doc.document_number),
			_(
				"It counts as not issued, and the five days to correct and resend run from the notice. {0}"
			).format(ricevuta.riassunto()),
		)
	return {"applied": True, "invoice": nome, "status": ricevuta.stato, "summary": ricevuta.riassunto()}


def _impara_indirizzo(doc, ricevuta: Ricevuta) -> None:
	"""On PEC, the delivery receipt names the address for every invoice after this one."""
	if frappe.db.get_value("CRM Invoicing Company", doc.company, "sdi_mode") != "pec":
		return
	mittente = (ricevuta.descrizione or "") if "@" in (ricevuta.descrizione or "") else ""
	if mittente:
		from crm.invoicing.sdi.pec import aggiorna_indirizzo

		aggiorna_indirizzo(doc.company, mittente)


def _avvisa(doc, titolo: str, dettaglio: str) -> None:
	from crm.invoicing.monitoraggio import avvisa

	avvisa(titolo, doc.company, dettaglio)


def applica_file(contenuto: bytes, nome_file: str | None = None, fattura: str | None = None) -> dict:
	"""Read a notice file and apply it. Returns why not, when it is not one."""
	ricevuta = ricevute.analizza(contenuto, nome_file)
	if not ricevuta:
		return {"applied": False, "reason": _("{0} is not an SdI notice").format(nome_file or "-")}
	return applica(ricevuta, nome_file, fattura)


def _contenuto(file_url: str) -> bytes:
	allegato = frappe.get_doc("File", {"file_url": file_url})
	contenuto = allegato.get_content(encodings=[])
	return contenuto.encode() if isinstance(contenuto, str) else contenuto


def scansiona_posta(giorni: int = GIORNI_ARRETRATI) -> list[dict]:
	"""Look through incoming mail for notices nobody has applied yet.

	The PEC route has no webhook: the notices arrive as email, and if nothing reads
	the mailbox the invoices stay in `inviato` forever - which looks like nothing is
	wrong, and is exactly the silence this whole module watches for.
	"""
	da = frappe.utils.add_days(frappe.utils.nowdate(), -cint(giorni))
	allegati = frappe.get_all(
		"File",
		filters={
			"attached_to_doctype": "Communication",
			"file_name": ["like", "%.xml"],
			"creation": [">=", da],
		},
		fields=["name", "file_name", "file_url"],
		limit=500,
	)
	esiti: list[dict] = []
	for allegato in allegati:
		if not ricevute.e_ricevuta(allegato["file_name"]):
			continue
		try:
			esito = applica_file(_contenuto(allegato["file_url"]), allegato["file_name"])
		except Exception:
			frappe.log_error(title=f"SdI notice {allegato['file_name']}", message=frappe.get_traceback())
			continue
		if esito.get("applied"):
			esiti.append(esito)
	return esiti
