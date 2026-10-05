# Copyright (c) 2026, NPM2 Solutions Srl and contributors
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

**An update is given once.** Itala hands each update over once: read, it is gone.
So every update is kept first (`CRM SdI Update`), then applied; one that fails -
a notice that did not come, an error of ours - stays and is tried again at the
next round, never lost. An invoice that left and has heard nothing for a day is
asked about by name (`GET /fatture/{id}`).

Idempotent on both sides. A webhook and the sweep will both bring the same update,
and neither may move a document twice.
"""

from __future__ import annotations

import hashlib
import json

import frappe
from frappe import _
from frappe.utils import add_to_date, now_datetime

from crm.invoicing.engine import busta
from crm.invoicing.sdi import itala, ricezione

#: What a company may ask the provider for.
SOLO_USCITA = "uscita"
ENTRAMBI = "entrambi"

AGGIORNAMENTO = "CRM SdI Update"
#: How many times an update is tried before it is left to a person.
TENTATIVI = 10
#: An invoice that left this long ago and heard nothing is asked about by name...
SILENZIO_ORE = 24
#: ...at most this often.
RICHIESTA_ORE = 6


def _direzione(emittente: dict) -> str:
	return (emittente.get("sdi_flow") or SOLO_USCITA).strip() or SOLO_USCITA


def _vuole_ingresso(emittente: dict) -> bool:
	return _direzione(emittente) == ENTRAMBI


def da_chiedere(emittente: dict) -> bool:
	"""Whether there is anything to ask the provider for this company.

	Asked every ten minutes, so it asks only when something waits: an invoice that
	left and has no outcome yet, one delivered to a public body that has still to
	accept it, an update kept and not applied yet, or a company that receives its
	suppliers' invoices.
	"""
	if _vuole_ingresso(emittente):
		return True
	nome = emittente.get("name")
	if frappe.db.exists("CRM Invoice", {"company": nome, "docstatus": 1, "sdi_status": "inviato"}):
		return True
	if frappe.db.exists(AGGIORNAMENTO, {"company": nome, "done": 0, "attempts": ["<", TENTATIVI]}):
		return True
	return bool(
		frappe.db.exists(
			"CRM Invoice",
			{
				"company": nome,
				"docstatus": 1,
				"recipient_type": "pubblica_amministrazione",
				"sdi_status": "consegnata",
			},
		)
	)


def riconcilia(emittente: dict, voci: list[dict] | None = None) -> dict:
	"""Keep everything outstanding, then apply it. Returns what it did.

	A company that only issues asks for its transmissions alone: the invoices its
	suppliers send stay unread at the provider, for whoever does want them. One
	that receives too asks for both - never for the receptions alone, or the
	outcome of what it sent would never come back.
	"""
	if voci is None:
		voci = itala.aggiornamenti(
			emittente,
			solo_trasmissioni=None if _vuole_ingresso(emittente) else "true",
		)
		voci = [*voci, *_silenziose(emittente)]

	esito = {"notices": 0, "incoming": 0, "skipped": 0, "problems": []}
	for voce in voci:
		if not _conserva(emittente, voce):
			esito["skipped"] += 1
	# what was kept is safe before anything is applied: a failure from here on
	# rolls back only its own row
	_conferma()

	for nome in frappe.get_all(
		AGGIORNAMENTO,
		filters={"company": emittente.get("name"), "done": 0, "attempts": ["<", TENTATIVI]},
		order_by="creation asc",
		pluck="name",
		limit=500,
	):
		_applica_conservato(emittente, nome, esito)
	return esito


def _chiave(emittente: dict, voce: dict) -> str:
	"""One name per update: the same one, from the webhook or from the sweep, is one."""
	parti = (
		emittente.get("name") or "",
		"in" if busta.ricevuta(voce) else "out",
		str(voce.get("id") or ""),
		(voce.get("sdi_stato") or "").strip().upper(),
	)
	return "SDI-" + hashlib.sha1("|".join(parti).encode()).hexdigest()[:20]


def _conserva(emittente: dict, voce) -> bool:
	"""Keep one update, once. False for what is not the company's to keep: not a
	row, another VAT number's, a supplier's invoice for a company that does not
	receive them."""
	if not isinstance(voce, dict) or not voce.get("id"):
		return False
	if not busta.della_partita_iva(voce, emittente.get("tax_id")):
		return False
	entrata = busta.ricevuta(voce)
	if entrata and not _vuole_ingresso(emittente):
		return False
	nome = _chiave(emittente, voce)
	if frappe.db.exists(AGGIORNAMENTO, nome):
		return True
	frappe.get_doc(
		{
			"doctype": AGGIORNAMENTO,
			"company": emittente.get("name"),
			"incoming": 1 if entrata else 0,
			"provider_id": str(voce.get("id")),
			"provider_state": (voce.get("sdi_stato") or "").strip().upper() or None,
			"received_on": now_datetime(),
			"payload": json.dumps(voce, ensure_ascii=False, default=str),
		}
	).insert(ignore_permissions=True, set_name=nome)
	return True


def _applica_conservato(emittente: dict, nome: str, esito: dict) -> None:
	"""Apply one kept update. A failure keeps it for the next round, with why."""
	riga = frappe.get_doc(AGGIORNAMENTO, nome)
	try:
		voce = json.loads(riga.payload or "{}")
	except ValueError:
		voce = {}
	frappe.db.savepoint("aggiornamento")
	try:
		if riga.incoming:
			fatto = _registra_ingresso(emittente, voce)
			esito["incoming"] += 1 if fatto else 0
		else:
			fatto, fattura = _applica_aggiornamento(emittente, voce)
			esito["notices"] += 1 if fatto else 0
			if fattura:
				riga.db_set("invoice", fattura, update_modified=False)
		# applied, or nothing left to apply: it keeps only what identifies it
		riga.db_set({"done": 1, "payload": None, "last_error": None}, update_modified=False)
	except Exception as errore:
		frappe.db.rollback(save_point="aggiornamento")
		riga.reload()
		riga.db_set(
			{"attempts": (riga.attempts or 0) + 1, "last_error": str(errore)[:500]},
			update_modified=False,
		)
		esito["problems"].append(str(errore)[:200])
	_conferma()


def _conferma() -> None:
	"""Make what is kept durable now: Itala will not give it again. Not in tests,
	whose transaction is rolled back at their end."""
	if not frappe.flags.in_test:
		frappe.db.commit()  # nosemgrep: frappe-manual-commit


def _silenziose(emittente: dict) -> list[dict]:
	"""Invoices that left a day ago and have heard nothing: asked about one by one,
	at most every few hours each. An update lost on the way is found again here."""
	soglia = add_to_date(now_datetime(), hours=-SILENZIO_ORE)
	righe = []
	for fattura in frappe.get_all(
		"CRM Invoice",
		filters={
			"company": emittente.get("name"),
			"docstatus": 1,
			"sdi_status": "inviato",
			"sdi_provider_id": ["is", "set"],
			"sdi_sent_on": ["<", soglia],
		},
		fields=["name", "sdi_provider_id"],
		limit=20,
	):
		chiave = f"itala:chiesta:{fattura.name}"
		if frappe.cache().get_value(chiave):
			continue
		frappe.cache().set_value(chiave, 1, expires_in_sec=RICHIESTA_ORE * 3600)
		try:
			stato = itala.stato_di(emittente, fattura.sdi_provider_id)
		except Exception:
			continue
		if isinstance(stato, dict) and (stato.get("sdi_stato") or "").upper() not in ("", "INVI", "PREN"):
			righe.append({"id": fattura.sdi_provider_id, "ricezione": 0, **stato})
	return righe


def _fattura_di(voce: dict) -> str | None:
	"""Which of our invoices an update is about: Itala's own id first (the one key
	that never moves), then the file name it transmitted, then the SdI's id."""
	if voce.get("id"):
		nome = frappe.db.get_value("CRM Invoice", {"sdi_provider_id": str(voce["id"])}, "name")
		if nome:
			return nome
	if voce.get("sdi_nome_file"):
		nome = frappe.db.get_value("CRM Invoice", {"sdi_filename": voce["sdi_nome_file"]}, "name")
		if nome:
			return nome
	if voce.get("sdi_identificativo"):
		return frappe.db.get_value("CRM Invoice", {"sdi_identifier": str(voce["sdi_identificativo"])}, "name")
	return None


def completa_riferimenti(nome: str, voce: dict) -> None:
	"""What the update knows and the invoice did not yet: the SdI's identifier (empty
	while Itala had only taken the file), the name Itala transmitted it under, the
	XML as transmitted."""
	doc = frappe.get_doc("CRM Invoice", nome)
	valori = {}
	identificativo = str(voce.get("sdi_identificativo") or "").strip()
	if identificativo and identificativo != (doc.sdi_identifier or ""):
		valori["sdi_identifier"] = identificativo
	nome_file = (voce.get("sdi_nome_file") or "").strip()
	if nome_file and nome_file != (doc.sdi_filename or ""):
		valori["sdi_filename"] = nome_file
	if valori:
		doc.db_set(valori, update_modified=False)
	conserva_trasmesso(doc, voce.get("sdi_fattura"))


def conserva_trasmesso(doc, xml: str | None) -> None:
	"""The XML Itala transmitted, with its own transmission data: the one the SdI
	holds. Kept once, private, beside ours."""
	if doc.get("sdi_sent_file") or not isinstance(xml, str) or not xml.lstrip().startswith("<"):
		return
	allegato = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": doc.sdi_filename or f"{doc.name}-trasmesso.xml",
			"attached_to_doctype": "CRM Invoice",
			"attached_to_name": doc.name,
			"is_private": 1,
			"content": xml.encode(),
		}
	)
	allegato.insert(ignore_permissions=True)
	doc.db_set("sdi_sent_file", allegato.file_url, update_modified=False)


def _applica_aggiornamento(emittente: dict, voce: dict) -> tuple[bool, str | None]:
	"""A state change on one of ours: fetch the real notice and let the parser rule.
	Returns whether something moved, and the invoice it is about."""
	riferimento = voce.get("id")
	stato = (voce.get("sdi_stato") or "").strip().upper()
	fattura = _fattura_di(voce)
	if fattura:
		completa_riferimenti(fattura, voce)

	if riferimento and stato in itala.STATI_CON_NOTIFICA:
		contenuto, nome_notifica = itala.notifica(emittente, riferimento)
		if contenuto:
			# the notice's own name tells one notice of an invoice from the next; one
			# of each state, when Itala does not give it
			nome_notifica = nome_notifica or f"itala-{riferimento}-{stato}.xml"
			risultato = ricezione.applica_file(contenuto, nome_notifica, fattura=fattura)
			if risultato.get("applied"):
				return True, risultato.get("invoice") or fattura
			if risultato.get("invoice") and not risultato.get("status"):
				# applied before: nothing to do, nothing to say
				return False, risultato.get("invoice")
			# Parsed and matched nothing we hold: recording beats retrying, since the
			# same bytes would reach the same answer.
			if risultato.get("reason"):
				return _annota_senza_notifica(voce, risultato["reason"], fattura), fattura

	return _annota_senza_notifica(voce, None, fattura), fattura


def _annota_senza_notifica(voce: dict, motivo: str | None, nome: str | None = None) -> bool:
	"""No notice to be had: fall back to their word for it, and say that is what it is.

	Writing a state we did not read from an SdI file is a lesser record, so the
	document carries where it came from rather than looking like a parsed notice.
	"""
	nome = nome or _fattura_di(voce)
	if not nome:
		return False

	codice = (voce.get("sdi_stato") or "").strip().upper()
	stato = itala.STATO_PROVIDER.get(codice)
	if not stato or stato not in _stati_ammessi():
		return False

	doc = frappe.get_doc("CRM Invoice", nome)
	if doc.sdi_status == stato:
		return False

	messaggio = voce.get("sdi_messaggio") or ""
	doc.db_set(
		{
			"sdi_status": stato,
			"sdi_message": _("Reported by the provider as {0}. {1}")
			.format(codice, motivo or messaggio)
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
		payload={"provider_state": codice, "provider_id": voce.get("id")},
	)
	if codice in busta.STATI_DA_DIRE:
		_avvisa(doc, codice, messaggio)
	return True


def _stati_ammessi() -> set[str]:
	"""The states an invoice can be in: nothing else is ever written."""
	campo = frappe.get_meta("CRM Invoice").get_field("sdi_status")
	return {riga.strip() for riga in (campo.options or "").split("\n") if riga.strip()}


def _avvisa(doc, codice: str, messaggio: str) -> None:
	"""Who has to act hears it, as the notice behind the state would have said it."""
	from crm.invoicing.monitoraggio import avvisa

	if codice == "NONC":
		titolo = _("Invoice {0} is issued but not delivered").format(doc.document_number)
		dettaglio = _(
			"The Sistema di Interscambio has it and filed it in the client's reserved area. "
			"The client has to be told: send them the PDF."
		)
	elif codice == "RIFI":
		titolo = _("Invoice {0} was refused by the public body").format(doc.document_number)
		dettaglio = _("It has to be corrected with a credit note and issued again. {0}").format(messaggio)
	else:
		titolo = _("Invoice {0} did not go through").format(doc.document_number)
		dettaglio = _("It counts as not issued: correct it and send it again. {0}").format(messaggio)
	avvisa(titolo, doc.company, dettaglio.strip())


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
