# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Reading an envelope that arrived from outside.

This lives with the engine rather than with the channel for one reason: it is the
code that decides whether an unauthenticated caller gets in, and that decision
should be testable without a database, a site or a network. Everything here is a
pure function over bytes and dictionaries, so the suite that proves it runs in a
tenth of a second wherever it is checked out.

**The payload contract is not verified.** The provider documents its event names,
not the envelope it wraps them in, and this was written without a real delivery to
read. So nothing here insists on a shape: it looks for what it needs in several
plausible places, refuses to guess when it is absent, and describes what it saw by
the *names* of the keys rather than their values - the shape is what the first real
delivery has to teach you, and the content is never what a log should keep.
"""

from __future__ import annotations

import base64
import binascii
import hmac
import re
from datetime import datetime
from urllib.parse import unquote

#: The provider's events. Only a notification carries an SdI notice; the rest are
#: lifecycle news, kept because silence about them is how an invoice dies quietly.
EVENTO_NOTIFICA = "customer-notification"
EVENTO_INVIATA = "customer-invoice"
EVENTO_RICEVUTA = "supplier-invoice"
EVENTI_GUASTO = ("invoice-status-invoice-error", "invoice-status-quarantena")

#: Headers the secret may arrive in, in the order they are trusted.
INTESTAZIONI_TOKEN = ("X-Provider-Token", "X-Webhook-Token", "X-Hook-Secret")
#: Query parameters it may arrive in instead, because the provider's configuration
#: chooses between the two placements and both are legitimate.
ARGOMENTI_TOKEN = ("token", "secret", "key")

CHIAVI_EVENTO = ("event", "type", "topic", "name", "event_type", "eventType")
CHIAVI_CONTENUTO = ("attachment", "file", "content", "xml", "payload", "body", "data", "notification")
CHIAVI_UUID = ("uuid", "id", "identifier", "invoice_uuid", "identificativoSdI", "sdi_id")
CHIAVI_NOME = ("filename", "file_name", "name")

#: A notice is a few kilobytes. This is not a tuning knob, it is a refusal to buffer
#: whatever an unauthenticated caller feels like sending.
CORPO_MASSIMO = 20 * 1024 * 1024

#: How far down the envelope is followed. Deep enough for a wrapped payload, shallow
#: enough that a hostile caller cannot make the search itself the attack.
PROFONDITA_MASSIMA = 4


def token_presentato(intestazioni: dict, argomenti: dict) -> str:
	"""The secret the caller presented, from wherever it was told to put it.

	`Authorization` is read last and unwrapped, because a provider told to use a
	header literally named `Bearer` sends `Authorization: Bearer <secret>`, while one
	told to use any other name sends the bare value.
	"""

	def _leggi(sorgente, nome):
		valore = sorgente.get(nome) if sorgente else None
		return str(valore).strip() if valore else ""

	for nome in INTESTAZIONI_TOKEN:
		valore = _leggi(intestazioni, nome)
		if valore:
			return valore

	autorizzazione = _leggi(intestazioni, "Authorization")
	if autorizzazione:
		parti = autorizzazione.split(None, 1)
		return (parti[1] if len(parti) == 2 else parti[0]).strip()

	for nome in ARGOMENTI_TOKEN:
		valore = _leggi(argomenti, nome)
		if valore:
			return valore
	return ""


def segreto_corrisponde(presentato: str, atteso: str | None) -> bool:
	"""Constant time, always.

	A caller must not be able to learn a secret one byte at a time from how long the
	answer takes, and an empty stored secret must never match an empty presented one -
	a company that has not configured a secret has not opened a door.
	"""
	if not presentato or not atteso:
		return False
	return hmac.compare_digest(str(atteso), str(presentato))


def cerca(corpo, chiavi: tuple[str, ...], profondita: int = PROFONDITA_MASSIMA) -> str | None:
	"""First string value under any of these keys, at any depth. Envelopes nest."""
	if profondita <= 0:
		return None
	if isinstance(corpo, dict):
		for chiave in chiavi:
			valore = corpo.get(chiave)
			if isinstance(valore, str) and valore.strip():
				return valore.strip()
		for valore in corpo.values():
			trovato = cerca(valore, chiavi, profondita - 1)
			if trovato:
				return trovato
	elif isinstance(corpo, list):
		for elemento in corpo:
			trovato = cerca(elemento, chiavi, profondita - 1)
			if trovato:
				return trovato
	return None


def forse_xml(testo: str) -> bytes | None:
	"""A notice's bytes, whether they arrived as XML or as base64 around it.

	Neither form is assumed: what comes back is only returned if it actually looks
	like a document, so a caller cannot use this to smuggle arbitrary bytes into the
	notice parser.
	"""
	if not testo:
		return None
	spogliato = testo.strip()
	if spogliato.startswith("<"):
		return spogliato.encode()
	try:
		decodificato = base64.b64decode(spogliato, validate=True)
	except (binascii.Error, ValueError):
		return None
	return decodificato if decodificato.lstrip()[:1] == b"<" else None


def forma(corpo: dict) -> dict:
	"""What arrived, described without quoting it.

	The contract is unverified, so the shape of a real delivery is worth keeping and
	its content never is. A notice is only metadata, but the same door takes an
	incoming supplier invoice, and that one carries somebody's healthcare document.
	"""
	chiavi = sorted(corpo.keys())[:20] if isinstance(corpo, dict) else []
	return {
		"keys": chiavi,
		"event": cerca(corpo, CHIAVI_EVENTO),
		"uuid": cerca(corpo, CHIAVI_UUID),
	}


def porta_una_notifica(evento: str | None) -> bool:
	"""Whether this event is one that should have carried something to apply."""
	return bool(evento) and (evento == EVENTO_NOTIFICA or evento in EVENTI_GUASTO)


# --------------------------------------------------------- the provider's words

#: The intermediary's transmission states, and the invoice state each leaves behind
#: (the `sdi_status` options, the same the SdI's own notices give: `ricevute`).
#: `NONC` is the one that gets misread: not delivered is **not** a failure - the
#: invoice is issued, the sender's obligation is discharged, and what is owed is
#: telling the client to go and fetch it. A public body's answer, yes or no, is its
#: outcome (`esito_pa`), as the notice it sends is; Itala's `ERRO` is a transmission
#: that did not go through: not issued, to correct and send again.
STATO_PROVIDER = {
	"PREN": "inviato",
	"INVI": "inviato",
	"CONS": "consegnata",
	"NONC": "mancata_consegna",
	"ACCE": "esito_pa",
	"RIFI": "esito_pa",
	"DECO": "decorrenza_termini",
	"ERRO": "scartata",
}

#: The states somebody has to hear about, as the notices behind them say it.
STATI_DA_DIRE = frozenset({"NONC", "RIFI", "ERRO"})

#: States that mean the SdI has answered, so there is a notice worth fetching.
#: Asking for one before that is a wasted call and a 404 to explain.
STATI_CON_NOTIFICA = frozenset({"CONS", "NONC", "ACCE", "RIFI", "DECO", "ERRO"})

#: Where an identifier hides. The provider's own field first, then the shapes other
#: providers use, because the adapter stays generic on purpose.
CHIAVI_IDENTIFICATIVO = ("sdi_identificativo", "uuid", "id", "identifier", "invoice_uuid", "sdi_id")


def identificativo(corpo) -> str | None:
	"""The provider's reference for a document, wherever it put it."""
	if isinstance(corpo, str):
		return corpo.strip() or None
	if not isinstance(corpo, dict):
		return None
	for chiave in CHIAVI_IDENTIFICATIVO:
		valore = corpo.get(chiave)
		if valore not in (None, "", []):
			return str(valore)
	for annidato in corpo.values():
		if isinstance(annidato, dict):
			trovato = identificativo(annidato)
			if trovato:
				return trovato
	return None


def xml_in_ingresso(voce: dict) -> bytes | None:
	"""An incoming invoice's own XML, whichever way the provider encoded it.

	Plain text wins over base64 when both are present: it is the one that needs no
	decoding step to go wrong.
	"""
	grezzo = voce.get("sdi_fattura_xml") if isinstance(voce, dict) else None
	if isinstance(grezzo, str) and grezzo.lstrip().startswith("<"):
		return grezzo.encode()
	codificato = voce.get("sdi_fattura_base64") if isinstance(voce, dict) else None
	if isinstance(codificato, str) and codificato.strip():
		try:
			return base64.b64decode(codificato, validate=True)
		except (binascii.Error, ValueError):
			return None
	return None


#: Used when the provider does not say when its token expires. Short on purpose.
DURATA_PRUDENTE = 3600
#: Never trust a stated expiry further than this, whatever the provider claims: a
#: year-long token is either a mistake or a compromise, and neither gets cached.
DURATA_MASSIMA = 23 * 3600
#: Slack between what the provider says and what we act on, so a token cannot die
#: between the check and the call that uses it.
MARGINE = 60


def durata_token(scadenza: str | None, adesso: datetime | None = None) -> int:
	"""How long to keep a token, from what the provider said rather than a guess.

	An unreadable or absent expiry falls back to a short life: re-authenticating an
	hour early costs one call, while trusting a number nobody stated costs a failed
	invoice at the worst moment. The expiry carries no time zone: it is Italy's, as
	`adesso` is when the site's clock is (the caller passes it).
	"""
	if not scadenza:
		return DURATA_PRUDENTE
	try:
		fine = datetime.strptime(str(scadenza).strip(), "%Y-%m-%d %H:%M:%S")
	except (TypeError, ValueError):
		return DURATA_PRUDENTE
	restano = int((fine - (adesso or datetime.now())).total_seconds()) - MARGINE
	return max(MARGINE, min(restano, DURATA_MASSIMA))


_NOME_IN_DISPOSIZIONE = re.compile(r"""filename\*?\s*=\s*(?:UTF-8''|utf-8'')?"?([^";]+)"?""", re.IGNORECASE)


def nome_da_disposizione(valore: str | None) -> str | None:
	"""The file name a `Content-Disposition` gives: the notice's own, which is what
	tells one notice of an invoice from the next. Only a plain name is kept: a path,
	or anything that is not a file's name, is no name."""
	if not valore:
		return None
	trovato = _NOME_IN_DISPOSIZIONE.search(str(valore))
	if not trovato:
		return None
	nome = unquote(trovato.group(1).strip())
	if not nome or "/" in nome or "\\" in nome or nome.startswith("."):
		return None
	return nome[:140]


def della_partita_iva(voce, partita_iva: str | None) -> bool:
	"""Whether a row the provider pushed or listed belongs to this VAT number.

	Under the agency's account the rows of every centre come from one place: a row
	that names another VAT number is somebody else's. One that names none is taken
	as the company's whose door it came through (the list is filtered by it)."""
	if not isinstance(voce, dict):
		return False
	nominata = ""
	for chiave in ("partita_iva", "piva"):
		valore = voce.get(chiave)
		if isinstance(valore, (str, int)) and str(valore).strip():
			nominata = str(valore)
			break
	if not nominata:
		return True
	return bool(partita_iva) and _partita_iva(nominata) == _partita_iva(partita_iva)


def stessa_partita_iva(una, altra) -> bool:
	"""Whether two VAT numbers are the same one, however each is written: Itala keeps
	a company's with its country's prefix (`IT13832480969`), DottorCloud without."""
	return bool(_partita_iva(una)) and _partita_iva(una) == _partita_iva(altra)


def _partita_iva(valore) -> str:
	"""A VAT number as compared: letters and digits only, without the IT prefix."""
	return "".join(c for c in str(valore or "") if c.isalnum()).upper().removeprefix("IT")
