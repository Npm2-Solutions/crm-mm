# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The accredited intermediary's REST API.

Written against the published contract, which is kept in `.pi/vendor/itala.md`.
Anything this file does that is not written there is an invention and should be
taken out.

What the provider sells is the accredited channel and the archiving, not the
format: the XML arrives already built and already checked against the SdI's own
rejection codes. So sending is a POST and a read-back of one identifier.

**Their state is a hint, not the truth.** They summarise the SdI's answer into
`INVI`, `CONS`, `NONC` and the rest. The real notice - the one that names a
rejection code, or says an invoice is issued but undeliverable - is a file the SdI
produced, and they hand it over whole at `/fatture/{id}/notifica`. So a state change
is what tells us to go and fetch that file, and the module's own parser is what
decides what it means. A summary is a fine alarm and a poor record.

Onboarding rule kept from the original design: **one registration per company,
never a shared master account.** Fiscal responsibility and the archive stay with
whoever issued the invoices, and a client who leaves takes their history with them.
"""

from __future__ import annotations

import json

import frappe
from frappe import _

from crm.invoicing import connessione
from crm.invoicing.engine import busta
from crm.invoicing.sdi.base import ErroreCanale, EsitoInvio

CODICE = "provider"
ETICHETTA = "Accredited provider (REST)"


def _endpoint(emittente: dict) -> str:
	url = (emittente.get("sdi_endpoint") or "").strip().rstrip("/")
	if not url:
		raise ErroreCanale(
			_("No endpoint for provider {0}: the XML is ready, the channel is not.").format(
				emittente.get("sdi_provider") or "-"
			)
		)
	return url


def _contenuto(url: str) -> bytes:
	allegato = frappe.get_doc("File", {"file_url": url})
	contenuto = allegato.get_content(encodings=[])
	return contenuto.encode() if isinstance(contenuto, str) else contenuto


def invia(doc, emittente: dict) -> EsitoInvio:
	endpoint = _endpoint(emittente)
	if not doc.xml_file:
		raise ErroreCanale(_("This invoice has no XML to send"))

	contenuto = _contenuto(doc.get("sdi_signed_file") or doc.xml_file)
	try:
		risposta = connessione.posta(emittente, f"{endpoint}/fatture", contenuto, tipo="application/xml")
	except connessione.ErroreProvider as errore:
		raise ErroreCanale(str(errore)) from None

	if risposta.status_code not in (200, 201, 202):
		# Their errors come back as {"error": "..."}. The body is worth keeping because
		# it usually names the field that was refused, and truncated because a provider
		# that echoes the invoice back would otherwise put the document in a log.
		raise ErroreCanale(
			_("The provider answered {0}: {1}").format(risposta.status_code, (risposta.text or "")[:500])
		)

	try:
		corpo = risposta.json() if risposta.content else {}
	except json.JSONDecodeError:
		corpo = (risposta.text or "").strip()

	stato = (corpo or {}).get("sdi_stato") if isinstance(corpo, dict) else None
	if stato == "ERRO":
		raise ErroreCanale(
			_("The provider refused the document: {0}").format(
				(corpo.get("sdi_messaggio") or _("no reason given"))[:500]
			)
		)

	identificativo = busta.identificativo(corpo)
	nome_file = (corpo or {}).get("sdi_nome_file") if isinstance(corpo, dict) else None
	riferimento = (corpo or {}).get("id") if isinstance(corpo, dict) else None
	return EsitoInvio(
		canale=CODICE,
		inviato=True,
		identificativo=identificativo,
		nome_file=nome_file or doc.sdi_filename,
		messaggio=_("Accepted by {0}{1}. The outcome arrives as a notice.").format(
			emittente.get("sdi_provider") or _("the provider"),
			f" ({identificativo})" if identificativo else "",
		)
		+ connessione.etichetta_ambiente(emittente),
		dettagli={
			"environment": connessione.ambiente(emittente),
			"provider_id": riferimento,
			"provider_state": stato,
		},
	)


def notifica(emittente: dict, riferimento) -> bytes | None:
	"""The original SdI notice for one of their records.

	This is what keeps their summary from becoming the record: the file that comes
	back is the one the SdI produced, and this module's own parser is what reads it.
	"""
	endpoint = _endpoint(emittente)
	risposta = connessione.leggi(emittente, f"{endpoint}/fatture/{riferimento}/notifica")
	if risposta.status_code != 200 or not risposta.content:
		return None
	return risposta.content


def aggiornamenti(emittente: dict, solo_non_letti: bool = True, **filtri) -> list[dict]:
	"""Everything the provider has that we have not acted on yet.

	One call covers both directions - a status change on something we sent, and an
	invoice somebody sent us - and the `ricezione` field is what tells them apart.
	Which of the two this company actually wants is a setting, not an assumption.
	"""
	endpoint = _endpoint(emittente)
	parametri = {k: v for k, v in filtri.items() if v not in (None, "")}
	if solo_non_letti:
		parametri["unread"] = "true"
	if emittente.get("tax_id"):
		parametri.setdefault("partita_iva", emittente["tax_id"])

	risposta = connessione.leggi(emittente, f"{endpoint}/fatture", parametri)
	if risposta.status_code != 200:
		raise ErroreCanale(
			_("The provider answered {0} when asked for updates: {1}").format(
				risposta.status_code, (risposta.text or "")[:300]
			)
		)
	try:
		corpo = risposta.json() if risposta.content else []
	except json.JSONDecodeError:
		raise ErroreCanale(_("The provider's update list is not JSON")) from None
	return corpo if isinstance(corpo, list) else []


#: Re-exported so a reader of this adapter finds the provider's vocabulary where
#: they look for it. It lives in the engine because it is translation, not
#: transport, and translation is worth testing without a site.
STATO_PROVIDER = busta.STATO_PROVIDER
STATI_CON_NOTIFICA = busta.STATI_CON_NOTIFICA
xml_in_ingresso = busta.xml_in_ingresso
