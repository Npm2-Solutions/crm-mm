# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Itala, the accredited intermediary every electronic invoice leaves through.

Written against the published contract (fattura-elettronica-api.it, REST API 2.0),
summarised in `.pi/vendor/itala.md`. Anything this file does that is not written
there is an invention and should be taken out.

What the provider sells is the accredited channel and the archiving, not the
format: the XML arrives already built and already checked against the SdI's own
rejection codes. So sending is a POST and a read-back of what they did with it -
they rewrite the transmission block with their own identifiers, so **the file name
the SdI will answer to is theirs**, and it is kept on the invoice.

**One account, every centre a company under it.** Their multi-company management
registers a company by its VAT number and codice fiscale (`/aziende`); an invoice
sent as XML is filed under the company whose VAT number issues it. So before the
first invoice of a company in each environment, the company is registered, and the
identifier they give it is kept. A company with an account of its own registers
nothing: the account is the company.

**Their state is a hint, not the truth.** They summarise the SdI's answer into
`INVI`, `CONS`, `NONC` and the rest. The real notice - the one that names a
rejection code, or says an invoice is issued but undeliverable - is a file the SdI
produced, and they hand it over whole at `/fatture/{id}/notifica`. So a state change
is what tells us to go and fetch that file, and the module's own parser is what
decides what it means.
"""

from __future__ import annotations

import json

import frappe
from frappe import _

from crm.invoicing import connessione
from crm.invoicing.engine import busta
from crm.invoicing.sdi.base import ErroreCanale, EsitoInvio

CODICE = "provider"
ETICHETTA = "Itala, accredited intermediary"
NOME = "Itala"

AZIENDA = "CRM Invoicing Company"
#: Where the company's identifier at Itala is kept, by environment.
CAMPO_ID = {connessione.SANDBOX: "itala_id_test", connessione.PRODUZIONE: "itala_id"}


def _contenuto(url: str) -> bytes:
	allegato = frappe.get_doc("File", {"file_url": url})
	contenuto = allegato.get_content(encodings=[])
	return contenuto.encode() if isinstance(contenuto, str) else contenuto


def _json(risposta):
	try:
		return risposta.json() if risposta.content else None
	except (json.JSONDecodeError, ValueError):
		return (risposta.text or "").strip() or None


def _errore(risposta) -> str:
	"""Their errors come back as {"error": "..."}: the sentence, truncated, because a
	provider that echoes the invoice back would otherwise put it in a log."""
	corpo = _json(risposta)
	if isinstance(corpo, dict) and corpo.get("error"):
		return str(corpo["error"])[:300]
	return (risposta.text or "")[:300]


def _dati_azienda(emittente: dict) -> dict:
	"""What their company record takes from ours. With invoices sent as XML only the
	VAT number and the codice fiscale are required; the rest keeps their dashboard
	readable for whoever opens it."""
	nome = (
		" ".join(p for p in (emittente.get("first_name"), emittente.get("last_name")) if p)
		if emittente.get("last_name")
		else emittente.get("company_name")
	)
	indirizzo = " ".join(
		p for p in (emittente.get("address_line"), emittente.get("civic_number")) if p
	).strip()
	dati = {
		"ragione_sociale": nome or emittente.get("name"),
		"piva": (emittente.get("tax_id") or "").replace(" ", ""),
		"cfis": (emittente.get("fiscal_code") or emittente.get("tax_id") or "").replace(" ", ""),
		"indirizzo": indirizzo,
		"cap": emittente.get("postal_code"),
		"citta": emittente.get("city"),
		"provincia": emittente.get("province"),
		"paese": emittente.get("country") or "IT",
		"tipo_regime_fiscale": emittente.get("tax_regime"),
		"email_amministrazione": emittente.get("email"),
		"telefono_amministrazione": emittente.get("phone"),
		"iban": emittente.get("iban"),
	}
	dati = {chiave: valore for chiave, valore in dati.items() if valore}
	# the invoices its suppliers send come here too (both directions, always): said,
	# not left to Itala's default
	dati["abilita_ricezione"] = 1
	return dati


def _cerca_azienda(chi: connessione.Accesso, partita_iva: str) -> str | None:
	"""Their identifier for a company registered before, found by its VAT number."""
	pagina = 1
	while pagina <= 20:
		risposta = connessione.leggi(chi, "aziende", {"per_page": 1000, "page": pagina})
		if risposta.status_code != 200:
			return None
		righe = _json(risposta)
		if not isinstance(righe, list) or not righe:
			return None
		for riga in righe:
			if isinstance(riga, dict) and (riga.get("piva") or "").replace(" ", "") == partita_iva:
				return str(riga.get("id") or "") or None
		pagina += 1
	return None


def registra_azienda(emittente: dict, ambiente: str | None = None) -> str | None:
	"""Register the company under the agency's account, once per environment.

	Returns their identifier, or None for a company with an account of its own,
	which needs no registering. Registered before, under another site or by hand,
	it is found by its VAT number rather than registered twice.
	"""
	chi = connessione.accesso(emittente, ambiente)
	if chi.proprio:
		return None
	campo = CAMPO_ID[chi.ambiente]
	gia = (emittente.get(campo) or "").strip()
	if gia:
		return gia

	dati = _dati_azienda(emittente)
	if not dati.get("piva"):
		raise ErroreCanale(_("The company has no VAT number: Itala cannot register it"))
	risposta = connessione.posta_json(chi, "aziende", dati)
	corpo = _json(risposta)
	identificativo = str(corpo.get("id") or "") if isinstance(corpo, dict) else ""
	if risposta.status_code != 200 or not identificativo:
		identificativo = _cerca_azienda(chi, dati["piva"]) or ""
	if not identificativo:
		raise ErroreCanale(
			_("Itala did not register the company ({0}): {1}").format(risposta.status_code, _errore(risposta))
		)
	frappe.db.set_value(AZIENDA, emittente.get("name"), campo, identificativo, update_modified=False)
	emittente[campo] = identificativo
	sito_che_legge(emittente)
	return identificativo


def sito_che_legge(emittente: dict) -> bool:
	"""Whether this site is the one that reads the company's updates at Itala.

	Itala gives each update once: a copy of the site elsewhere - a test copy, a
	restored backup - reading them would take them away from the real one. The
	first site that registers the company, or reads its updates, is the one; another
	reads nothing, until the agency clears the field (the site has moved for good).
	"""
	qui = frappe.local.site
	registrato = (emittente.get("itala_site") or "").strip()
	if registrato:
		return registrato == qui
	if emittente.get("name") and frappe.db.exists(AZIENDA, emittente.get("name")):
		frappe.db.set_value(AZIENDA, emittente["name"], "itala_site", qui, update_modified=False)
	emittente["itala_site"] = qui
	return True


def rimuovi_azienda(emittente: dict, ambiente: str) -> bool:
	"""Take the company away from the agency's account at Itala, in one environment:
	a centre that leaves stops receiving through it. Its identifier here is cleared."""
	chi = connessione.accesso(emittente, ambiente)
	if chi.proprio:
		return False
	campo = CAMPO_ID[chi.ambiente]
	identificativo = (emittente.get(campo) or "").strip()
	if not identificativo:
		return False
	risposta = connessione.cancella(chi, f"aziende/{identificativo}")
	if risposta.status_code not in (200, 204, 404):
		raise ErroreCanale(
			_("Itala did not remove the company ({0}): {1}").format(risposta.status_code, _errore(risposta))
		)
	frappe.db.set_value(AZIENDA, emittente.get("name"), campo, "", update_modified=False)
	emittente[campo] = ""
	return True


def invia(doc, emittente: dict) -> EsitoInvio:
	"""Send the invoice's XML as it is: Itala writes its own transmission data, and
	signs what goes to a public body itself - a signed file could not be rewritten.

	After a send whose answer was lost, Itala is asked first whether it has the
	invoice already: sending it twice would come back from the SdI as a duplicate.
	"""
	if not doc.xml_file:
		raise ErroreCanale(_("This invoice has no XML to send"))
	ambiente = connessione.ambiente_del_documento(doc)
	try:
		registra_azienda(emittente, ambiente)
		chi = connessione.accesso(emittente, ambiente)
		gia = cerca_inviata(chi, doc, emittente) if _invio_incerto(doc) else None
		if gia:
			return _esito(gia, doc, ambiente, _("Itala already had it"))
		risposta = connessione.posta(chi, "fatture", _contenuto(doc.xml_file), tipo="application/xml")
	except connessione.ErroreProvider as errore:
		raise ErroreCanale(str(errore), incerto=errore.incerto) from None

	if risposta.status_code not in (200, 201, 202):
		raise ErroreCanale(_("Itala answered {0}: {1}").format(risposta.status_code, _errore(risposta)))

	corpo = _json(risposta)
	corpo = corpo if isinstance(corpo, dict) else {}
	if corpo.get("sdi_stato") == "ERRO":
		raise ErroreCanale(
			_("Itala refused the document: {0}").format(
				(corpo.get("sdi_messaggio") or _("no reason given"))[:500]
			)
		)
	return _esito(corpo, doc, ambiente, _("Accepted by Itala"))


def _esito(corpo: dict, doc, ambiente: str, detto: str) -> EsitoInvio:
	"""What a send left behind. The SdI's identifier is only Itala's
	`sdi_identificativo`: it is empty until the SdI takes the file, and comes later
	with the updates - Itala's own id is not it."""
	identificativo = str(corpo.get("sdi_identificativo") or "").strip() or None
	trasmesso = corpo.get("sdi_fattura")
	return EsitoInvio(
		canale=CODICE,
		inviato=True,
		identificativo=identificativo,
		nome_file=corpo.get("sdi_nome_file") or doc.sdi_filename,
		messaggio=detto
		+ (f" ({identificativo})" if identificativo else "")
		+ ". "
		+ _("The outcome arrives as a notice.")
		+ connessione.etichetta_ambiente(ambiente),
		dettagli={
			"environment": ambiente,
			"provider_id": str(corpo.get("id") or "") or None,
			"provider_state": corpo.get("sdi_stato"),
			"transmitted_xml": trasmesso if isinstance(trasmesso, str) and trasmesso.strip() else None,
		},
	)


def _invio_incerto(doc) -> bool:
	"""Whether a send of this invoice lost its answer: the log says so."""
	return bool(
		frappe.db.exists(
			"CRM Invoice Log",
			{"invoice": doc.name, "event": "sdi_sent", "status": "incerto"},
		)
	)


def cerca_inviata(chi: connessione.Accesso, doc, emittente: dict) -> dict | None:
	"""Itala's record of this invoice, if it has one: found by its number and its
	year under the company's VAT number."""
	anno = str(doc.posting_date or "")[:4]
	parametri = {
		"numero_documento": doc.document_number,
		"anno_documento": anno,
		"partita_iva": (emittente.get("tax_id") or "").replace(" ", ""),
	}
	risposta = connessione.leggi(chi, "fatture", {k: v for k, v in parametri.items() if v})
	if risposta.status_code != 200:
		return None
	righe = _json(risposta)
	for riga in righe if isinstance(righe, list) else []:
		if (
			isinstance(riga, dict)
			and not riga.get("ricezione")
			and str(riga.get("numero_documento") or doc.document_number) == str(doc.document_number)
		):
			return riga
	return None


def stato_di(emittente: dict, riferimento) -> dict | None:
	"""One of their records as it stands now (`GET /fatture/{id}`): what an invoice
	that left long ago and heard nothing is asked about."""
	chi = connessione.accesso(emittente)
	risposta = connessione.leggi(chi, f"fatture/{riferimento}")
	if risposta.status_code != 200:
		return None
	corpo = _json(risposta)
	return corpo if isinstance(corpo, dict) else None


def notifica(emittente: dict, riferimento) -> tuple[bytes | None, str | None]:
	"""The original SdI notice for one of their records, and its own file name.

	This is what keeps their summary from becoming the record: the file that comes
	back is the one the SdI produced, and this module's own parser is what reads it.
	Its name is the notice's (`Content-Disposition`), not the invoice's: an invoice to
	a public body has two notices, and each is applied once.
	"""
	chi = connessione.accesso(emittente)
	risposta = connessione.leggi(chi, f"fatture/{riferimento}/notifica", accetta="application/xml")
	if risposta.status_code != 200 or not risposta.content:
		return None, None
	testate = risposta.headers or {}
	return risposta.content, busta.nome_da_disposizione(testate.get("Content-Disposition"))


def aggiornamenti(emittente: dict, solo_non_letti: bool = True, **filtri) -> list[dict]:
	"""Everything the provider has for this company that we have not acted on yet.

	One call covers both directions - a status change on something we sent, and an
	invoice somebody sent us - and the `ricezione` field tells them apart. Under the
	agency's account every centre's updates sit together: the VAT number is what
	keeps one centre from reading, and marking as read, another's.
	"""
	chi = connessione.accesso(emittente)
	if not chi.proprio and not sito_che_legge(emittente):
		# a copy of the site: reading would take the updates from the real one
		return []
	parametri = {k: v for k, v in filtri.items() if v not in (None, "")}
	if solo_non_letti:
		parametri["unread"] = "true"
	if emittente.get("tax_id"):
		parametri.setdefault("partita_iva", emittente["tax_id"].replace(" ", ""))
	elif not chi.proprio:
		# without a VAT number the filter is gone, and so is every other centre's privacy
		return []

	risposta = connessione.leggi(chi, "fatture", parametri)
	if risposta.status_code != 200:
		raise ErroreCanale(
			_("Itala answered {0} when asked for updates: {1}").format(
				risposta.status_code, _errore(risposta)
			)
		)
	corpo = _json(risposta)
	if isinstance(corpo, str):
		raise ErroreCanale(_("Itala's update list is not JSON"))
	return corpo if isinstance(corpo, list) else []


def pronta(emittente: dict) -> bool:
	"""Whether an invoice of this company can leave: an account to send it with."""
	return connessione.ha_un_account_proprio(emittente) or bool(connessione.account_agenzia())


#: Re-exported so a reader of this adapter finds the provider's vocabulary where
#: they look for it. It lives in the engine because it is translation, not
#: transport, and translation is worth testing without a site.
STATO_PROVIDER = busta.STATO_PROVIDER
STATI_CON_NOTIFICA = busta.STATI_CON_NOTIFICA
xml_in_ingresso = busta.xml_in_ingresso
