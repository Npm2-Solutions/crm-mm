# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The door the provider pushes notices through.

Until this existed the `provider` channel was a one-way street: invoices left, and
nothing came back except what a human downloaded by hand. That is the precise
failure an accredited intermediary is paid to prevent, so the door matters as much
as the channel does.

It is a public endpoint that accepts fiscal notices, so the first question is not
what it does but who is allowed to knock:

* **one shared secret per company**, compared in constant time and presented either
  as a header or as a query parameter, because the provider's configuration chooses
  between the two. One secret per company, so a leaked one exposes one company and
  is rotated on its own;
* **a refused delivery is told nothing.** Unknown company, wrong secret and junk
  body all get the same answer. An endpoint that explains itself to strangers is an
  enumeration oracle;
* **the body is never trusted for identity.** Which invoice a notice answers is
  resolved the way every other channel resolves it - by the file name the SdI put on
  it - and not by a field the caller chose.

Reading the envelope is `crm.invoicing.engine.busta`, which is pure and tested
without a site. What is left here is the part that needs a database.
"""

from __future__ import annotations

import json

import frappe
from frappe import _

from crm.invoicing import connessione
from crm.invoicing.engine import busta
from crm.invoicing.sdi import ricezione


class Rifiutata(Exception):
	"""The delivery is not accepted. The caller learns nothing beyond that."""


def _aziende_candidate(richiesta) -> list[str]:
	"""Which companies to check the secret against.

	The URL handed to the provider names its company, so the usual case decrypts one
	secret. Without that hint every company on the provider channel is checked: it
	keeps a URL pasted without its query string working, and the list is short.
	"""
	indicata = (richiesta.args or {}).get("company")
	if indicata:
		return [str(indicata)]
	return [
		riga.name
		for riga in frappe.get_all("CRM Invoicing Company", filters={"sdi_mode": "provider"}, fields=["name"])
	]


def autentica(richiesta) -> str:
	"""Which company this delivery is for, or Rifiutata.

	Every candidate is checked even after one matches: returning early would let a
	caller time how far down the list its guess landed.
	"""
	presentato = busta.token_presentato(richiesta.headers or {}, richiesta.args or {})
	if not presentato:
		raise Rifiutata

	trovata = ""
	for nome in _aziende_candidate(richiesta):
		atteso = connessione.segreto({"name": nome}, "sdi_webhook_secret")
		if busta.segreto_corrisponde(presentato, atteso):
			trovata = nome
	if not trovata:
		raise Rifiutata
	return trovata


def _corpo(richiesta) -> dict:
	grezzo = richiesta.get_data() or b""
	if len(grezzo) > busta.CORPO_MASSIMO:
		raise Rifiutata
	if not grezzo:
		return {}
	try:
		caricato = json.loads(grezzo)
	except (ValueError, UnicodeDecodeError):
		return {}
	# They post a list of updates; other providers post an object. Both are accepted,
	# and a list is handed on as one rather than flattened into nothing.
	if isinstance(caricato, list):
		return {"data": caricato}
	return caricato if isinstance(caricato, dict) else {}


def gestisci(richiesta) -> dict:
	"""Authenticate, then do what the delivery asks."""
	azienda = autentica(richiesta)
	corpo = _corpo(richiesta)
	descrizione = busta.forma(corpo)
	evento = descrizione["event"] or ""

	frappe.logger("invoicing").info({"provider_webhook": descrizione, "company": azienda})

	grezzo = busta.cerca(corpo, busta.CHIAVI_CONTENUTO)
	contenuto = busta.forse_xml(grezzo) if grezzo else None
	if contenuto:
		nome = busta.cerca(corpo, busta.CHIAVI_NOME)
		esito = ricezione.applica_file(contenuto, nome)
		if esito.get("applied"):
			return {"handled": True, **esito}
		# It parsed, and it answers no invoice held here. Recording beats retrying:
		# the provider would send the same bytes again to the same answer.
		_registra_inapplicata(azienda, descrizione, esito.get("reason"))
		return {"handled": False, "reason": esito.get("reason")}

	# Nothing readable in the body. That is the normal case with a provider that
	# pushes a list of updates rather than a notice: the delivery is the alarm, and
	# the reconciliation is what goes and gets the record. Doing it here rather than
	# waiting for the sweep is the whole point of having a webhook.
	from crm.invoicing.sdi import riconciliazione

	emittente = frappe.get_cached_doc("CRM Invoicing Company", azienda).as_dict()
	voci = corpo if isinstance(corpo, list) else corpo.get("data") if isinstance(corpo, dict) else None
	esito = riconciliazione.riconcilia(emittente, voci if isinstance(voci, list) else None)
	if esito["notices"] or esito["incoming"]:
		return {"handled": True, **esito}

	if busta.porta_una_notifica(evento):
		# The event claimed something happened and nothing came of it. Worth surfacing:
		# either the contract moved or we are looking in the wrong place.
		_registra_inapplicata(azienda, descrizione, _("No update could be applied"))
	return {"handled": False, **esito}


def _registra_inapplicata(azienda: str, descrizione: dict, motivo: str | None) -> None:
	"""Surface a delivery nobody could act on, by its shape and never its content."""
	frappe.log_error(
		title=_("Provider webhook: nothing applied"),
		message=json.dumps(
			{"company": azienda, "shape": descrizione, "reason": motivo}, indent=1, default=str
		),
	)
