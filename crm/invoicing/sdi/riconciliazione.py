# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Bringing back what the provider has for us.

One call covers both directions, and the `ricezione` field tells them apart: a
status change on something we sent, or an invoice somebody sent us. Which of the
two a company wants is a setting - a practice that only issues has no use for a
passive cycle, and switching it on when nobody reads it just fills a table.

**Their summary is the alarm; the notice is the record.** A state change says the
SdI has answered, and the answer itself is a file they hand over whole. So this
fetches that file and gives it to the module's own parser, which is the code that
knows what `00327` means and that `MC` is not a failure. Falling back to their
one-word state happens only when the notice cannot be had, and says so.

Idempotent on both sides. A webhook and the daily sweep will both bring the same
update, and neither may move a document twice.
"""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import now_datetime

from crm.invoicing.sdi import itala, ricezione

#: What a company may ask the provider for.
SOLO_USCITA = "uscita"
ENTRAMBI = "entrambi"


def _direzione(emittente: dict) -> str:
	return (emittente.get("sdi_flow") or SOLO_USCITA).strip() or SOLO_USCITA


def _vuole_ingresso(emittente: dict) -> bool:
	return _direzione(emittente) == ENTRAMBI


def riconcilia(emittente: dict, voci: list[dict] | None = None) -> dict:
	"""Apply everything outstanding. Returns what it did, per direction."""
	if voci is None:
		voci = itala.aggiornamenti(
			emittente,
			solo_ricezioni="true" if _direzione(emittente) == ENTRAMBI else None,
		)

	esito = {"notices": 0, "incoming": 0, "skipped": 0, "problems": []}
	for voce in voci:
		if not isinstance(voce, dict):
			esito["skipped"] += 1
			continue
		try:
			if voce.get("ricezione") in (1, "1", True):
				esito["incoming"] += 1 if _registra_ingresso(emittente, voce) else 0
			else:
				esito["notices"] += 1 if _applica_aggiornamento(emittente, voce) else 0
		except Exception as errore:  # one bad row must not cost the rest of the sweep
			esito["problems"].append(str(errore)[:200])
	return esito


def _applica_aggiornamento(emittente: dict, voce: dict) -> bool:
	"""A state change on one of ours: fetch the real notice and let the parser rule."""
	riferimento = voce.get("id")
	stato = (voce.get("sdi_stato") or "").strip().upper()

	if riferimento and stato in itala.STATI_CON_NOTIFICA:
		contenuto = itala.notifica(emittente, riferimento)
		if contenuto:
			risultato = ricezione.applica_file(contenuto, voce.get("sdi_nome_file"))
			if risultato.get("applied"):
				return True
			# Parsed and matched nothing we hold: recording beats retrying, since the
			# same bytes would reach the same answer.
			if risultato.get("reason"):
				return _annota_senza_notifica(voce, risultato["reason"])

	return _annota_senza_notifica(voce, None)


def _annota_senza_notifica(voce: dict, motivo: str | None) -> bool:
	"""No notice to be had: fall back to their word for it, and say that is what it is.

	Writing a state we did not read from an SdI file is a lesser record, so the
	document carries where it came from rather than looking like a parsed notice.
	"""
	identificativo = voce.get("sdi_identificativo")
	nome_file = voce.get("sdi_nome_file")
	nome = None
	if nome_file:
		nome = frappe.db.get_value("CRM Invoice", {"sdi_filename": nome_file}, "name")
	if not nome and identificativo:
		nome = frappe.db.get_value("CRM Invoice", {"sdi_identifier": str(identificativo)}, "name")
	if not nome:
		return False

	stato = itala.STATO_PROVIDER.get((voce.get("sdi_stato") or "").strip().upper())
	if not stato:
		return False

	doc = frappe.get_doc("CRM Invoice", nome)
	if doc.sdi_status == stato:
		return False

	messaggio = voce.get("sdi_messaggio") or ""
	doc.db_set(
		{
			"sdi_status": stato,
			"sdi_message": _("Reported by the provider as {0}. {1}")
			.format(voce.get("sdi_stato"), motivo or messaggio)
			.strip(),
		},
		update_modified=False,
	)
	from crm.invoicing import documento

	documento.registra(
		doc,
		"sdi_receipt",
		_("State from the provider, without the SdI notice behind it"),
		stato=stato,
		payload={"provider_state": voce.get("sdi_stato"), "provider_id": voce.get("id")},
	)
	return True


def _registra_ingresso(emittente: dict, voce: dict) -> bool:
	"""File an invoice somebody sent us. The XML is the record; the rest is convenience."""
	riferimento = str(voce.get("id") or "").strip()
	if not riferimento:
		return False
	if frappe.db.exists("CRM Supplier Invoice", {"provider_id": riferimento}):
		return False

	dati = voce.get("dati_documento") or {}
	if isinstance(dati, str):
		try:
			dati = json.loads(dati)
		except ValueError:
			dati = {}

	doc = frappe.new_doc("CRM Supplier Invoice")
	doc.update(
		{
			"company": emittente.get("name"),
			"provider_id": riferimento,
			"sdi_identifier": str(voce.get("sdi_identificativo") or "") or None,
			"sdi_filename": voce.get("sdi_nome_file"),
			"received_on": voce.get("sdi_data_aggiornamento") or now_datetime(),
			"status": "ricevuta",
			"payload": json.dumps(dati, ensure_ascii=False, default=str)[:8000] if dati else None,
			**_anagrafica(dati),
		}
	)
	doc.insert(ignore_permissions=True)

	contenuto = itala.xml_in_ingresso(voce)
	if contenuto:
		allegato = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": voce.get("sdi_nome_file") or f"{riferimento}.xml",
				"attached_to_doctype": "CRM Supplier Invoice",
				"attached_to_name": doc.name,
				"is_private": 1,
				"content": contenuto,
			}
		)
		allegato.insert(ignore_permissions=True)
		doc.db_set("xml_file", allegato.file_url, update_modified=False)
	return True


def _anagrafica(dati: dict) -> dict:
	"""Read the few fields worth showing off what the provider already parsed.

	Defensive on every key: the shape is theirs, it can change, and a missing field
	must not cost the filing of a document that did arrive.
	"""
	if not isinstance(dati, dict):
		return {}
	mittente = dati.get("mittente") or dati.get("cedente") or {}
	documento_ = dati.get("documento") or {}
	if not isinstance(mittente, dict):
		mittente = {}
	if not isinstance(documento_, dict):
		documento_ = {}
	return {
		"supplier_name": (mittente.get("denominazione") or mittente.get("nome") or "")[:140] or None,
		"supplier_tax_id": mittente.get("partita_iva") or mittente.get("piva"),
		"supplier_fiscal_code": mittente.get("codice_fiscale"),
		"document_type": documento_.get("tipo_documento") or documento_.get("tipo"),
		"document_number": documento_.get("numero"),
		"document_date": documento_.get("data"),
		"total_amount": documento_.get("importo_totale") or documento_.get("totale"),
		"currency": documento_.get("divisa") or "EUR",
	}
