# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Connecting the centre's Telnyx account, without a site (doc 64).

- **Two codes, checked before Telnyx is asked**: the API key (``KEY`` and its
  hexadecimal digits, an underscore, its secret) and the account's public key
  (32 bytes in base64), which Telnyx signs every webhook with and gives to nobody
  through its API: the centre copies both from the portal, once.
- **A webhook is Telnyx's** when its Ed25519 signature of ``"<timestamp>|<raw
  body>"`` is right for the public key and the timestamp is within five minutes,
  ahead or behind: anything else is refused.
- **DottorCloud's resources** in the account carry the site's name, so the centre
  recognises them in its portal and another site does not take them.
- **What a number needs to reach DottorCloud**: its voice on DottorCloud's TeXML
  application, its SMS on DottorCloud's messaging profile, DottorCloud's tag. A
  number on the centre's own switchboard - a SIP connection - is left as it is, and
  so is one on another application that DottorCloud never managed.
- **Telnyx's answers in words**: a key Telnyx does not recognise, an account it
  blocked, Telnyx that does not answer.
- **An SMS's state** in Telnyx's words, as DottorCloud keeps it.

The words are English, translated where they are shown.
"""

from __future__ import annotations

import base64
import binascii
import re
from urllib.parse import urlsplit

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from crm.telephony.collegamento_regole import nome_dello_spazio

#: The first word of the name DottorCloud's resources carry in the account.
NOME = "DottorCloud"
#: How far a webhook's timestamp may be from now, in seconds, ahead or behind.
TOLLERANZA = 300

#: Whose account it is: the centre's, or the agency's for a centre with the
#: agency's front desk.
CENTRO, AGENZIA = "Centre", "Agency"

_CHIAVE = re.compile(r"KEY[0-9A-Fa-f]{20,}_[A-Za-z0-9_\-]{8,}")


def pulito(codice: str | None) -> str:
	"""A code as it was copied, without the spaces and lines around it or inside it."""
	return re.sub(r"\s+", "", codice or "")


def chiave_valida(chiave: str | None) -> bool:
	return bool(_CHIAVE.fullmatch(pulito(chiave)))


def chiave_pubblica(valore: str | None) -> bytes | None:
	"""The public key's 32 bytes, from its base64; None for anything else."""
	try:
		grezza = base64.b64decode(pulito(valore), validate=True)
	except (binascii.Error, ValueError):
		return None
	return grezza if len(grezza) == 32 else None


def cosa_manca(chiave: str | None, pubblica: str | None) -> str:
	"""What stops asking Telnyx with these two codes; '' when nothing does."""
	if not pulito(chiave):
		return "Paste the API key."
	if not chiave_valida(chiave):
		return "The API key starts with KEY and holds an underscore: copy it again from the portal."
	if not pulito(pubblica):
		return "Paste the public key."
	if not chiave_pubblica(pubblica):
		return "The public key is 44 letters, digits and signs ending with =: copy it again from the portal."
	return ""


def mascherata(chiave: str | None) -> str:
	"""A key as the page shows it: its kind and its last four characters."""
	chiave = pulito(chiave)
	if len(chiave) <= 8:
		return chiave
	return f"{chiave[:3]}…{chiave[-4:]}"


def nome_delle_risorse(indirizzo: str | None, prodotto: str = NOME) -> str:
	"""The name of DottorCloud's resources in the account: the product's and the
	site's address, as the portal shows it."""
	return nome_dello_spazio(indirizzo, prodotto or NOME)


# ---------------------------------------------------------------------------
# a webhook's signature


def firma_valida(
	corpo: bytes,
	firma: str | None,
	momento: str | None,
	pubblica: str | None,
	adesso: float,
	tolleranza: int = TOLLERANZA,
) -> bool:
	"""Whether Telnyx signed this request: ``firma`` (header
	``telnyx-signature-ed25519``, base64) of ``"<momento>|<corpo>"`` with the
	account's public key, ``momento`` (header ``telnyx-timestamp``, Unix seconds)
	within ``tolleranza`` of ``adesso``. The body exactly as it arrived."""
	try:
		quando = int(str(momento or "").strip())
	except ValueError:
		return False
	if abs(adesso - quando) > tolleranza:
		return False
	chiave = chiave_pubblica(pubblica)
	try:
		segno = base64.b64decode((firma or "").strip(), validate=True)
	except (binascii.Error, ValueError):
		return False
	if not chiave or len(segno) != 64:
		return False
	try:
		Ed25519PublicKey.from_public_bytes(chiave).verify(segno, str(quando).encode() + b"|" + (corpo or b""))
	except InvalidSignature:
		return False
	return True


# ---------------------------------------------------------------------------
# a number of the account


#: The connections that are a switchboard of the centre's own: a number on one of
#: them keeps it, and the answering service cannot run there.
CENTRALINI = frozenset({"ip_connection", "fqdn_connection", "credential_connection"})


def etichetta(indirizzo: str | None) -> str:
	"""The tag DottorCloud writes on the numbers it manages in the account: its own
	and the site's, so that an account holding other sites' numbers (the agency's)
	tells them apart."""
	indirizzo = (indirizzo or "").strip()
	host = urlsplit(indirizzo).hostname if "//" in indirizzo else indirizzo.strip("/")
	parola = re.sub(r"[^a-z0-9.-]+", "-", (host or "").lower()).strip("-")
	return f"dottorcloud-{parola}"[:64] if parola else "dottorcloud"


def cosa_fare(
	numero: dict,
	applicazione: str,
	profilo: str | None,
	nostre: set[str],
	tipi: dict[str, str],
	segno: str,
	prende_i_liberi: bool = True,
) -> tuple[str, dict]:
	"""What DottorCloud does with a number of the account: ``("ok", {})`` when its
	calls reach DottorCloud's TeXML application (``applicazione``) and its SMS
	DottorCloud's messaging profile (``profilo``); ``("sistema", changes)`` when they
	do not yet - the connection, the messaging profile, DottorCloud's tag
	(``segno``); ``("altrove", {})`` when it is not DottorCloud's to change.

	A number is DottorCloud's when it carries its tag, or is on one of its
	connections (``nostre``), or is on none at all and DottorCloud takes the free
	ones (the centre's own account, not the agency's, which holds other sites').
	One on a switchboard of the centre's (``tipi``: a connection's record type) keeps
	it, tag or not; one on another application stays there unless it is tagged.

	``numero`` as Telnyx describes it: ``connection_id``, ``messaging_profile_id``,
	``tags``, and ``sms`` when its messaging features say it sends SMS."""
	connessione = str(numero.get("connection_id") or "")
	etichette = list(numero.get("tags") or [])
	nostro = segno in etichette
	if connessione and connessione not in nostre:
		if not nostro or tipi.get(connessione) in CENTRALINI:
			return "altrove", {}
	if not connessione and not (nostro or prende_i_liberi):
		return "altrove", {}
	cambi = {}
	if connessione != str(applicazione):
		cambi["connection_id"] = str(applicazione)
	if not nostro:
		cambi["tags"] = [*etichette, segno]
	if profilo and numero.get("sms") and str(numero.get("messaging_profile_id") or "") != str(profilo):
		cambi["messaging_profile_id"] = str(profilo)
	return ("sistema" if cambi else "ok"), cambi


def paesi_del_profilo(paesi: list[str]) -> list[str]:
	"""The countries an outbound voice profile and a messaging profile take: two
	capital letters each, Italy when none is chosen."""
	scelti = [p.strip().upper() for p in paesi or [] if re.fullmatch(r"[A-Za-z]{2}", (p or "").strip())]
	return sorted(set(scelti)) or ["IT"]


# ---------------------------------------------------------------------------
# what Telnyx answers


def errore_in_parole(stato: int | None, codice=None, dettaglio: str | None = None) -> tuple[str, list]:
	"""Telnyx's refusal in words: the sentence and what goes in it.

	``stato``: the HTTP status Telnyx answered with, None when it did not answer;
	``codice``: Telnyx's own error code ("10009")."""
	codice = str(codice or "").strip()
	if stato == 401 or codice == "10009":
		return ("Telnyx does not recognise this API key: copy it again from the portal.", [])
	if stato == 403 or codice in ("10010", "10006"):
		return ("The API key may not do this in Telnyx: use a key of the account's owner.", [])
	if stato == 404 or codice == "10005":
		return ("Telnyx does not find what was asked: it may have been removed from the portal.", [])
	if stato == 429 or codice == "10011":
		return ("Telnyx is asked too often: try again in a minute.", [])
	if stato is None:
		return ("Telnyx does not answer: try again in a few minutes.", [])
	if stato in (400, 422) and dettaglio:
		return ("Telnyx says: {0}", [dettaglio.strip()[:300]])
	return ("Telnyx answered with an error ({0}): try again in a few minutes.", [codice or stato])


#: An SMS's state in Telnyx's words (``to[0].status``), as `CRM SMS Message` keeps it.
STATI_SMS = {
	"queued": "Queued",
	"sending": "Queued",
	"sent": "Sent",
	"delivered": "Delivered",
	"delivery_unconfirmed": "Sent",
	"delivery_failed": "Undelivered",
	"sending_failed": "Failed",
	"expired": "Failed",
}


def stato_sms(stato: str | None) -> str | None:
	"""An SMS's state as DottorCloud keeps it; None for one it does not know."""
	return STATI_SMS.get((stato or "").strip().lower())


#: A call's state in TeXML's words (``CallStatus``), as `CRM Call Log` keeps it.
STATI_CHIAMATA = {
	"queued": "Queued",
	"initiated": "Initiated",
	"ringing": "Ringing",
	"in-progress": "In Progress",
	"answered": "In Progress",
	"completed": "Completed",
	"busy": "Busy",
	"no-answer": "No Answer",
	"canceled": "Canceled",
	"cancelled": "Canceled",
	"failed": "Failed",
}


def stato_chiamata(stato: str | None) -> str:
	"""A call's state as DottorCloud keeps it; as it came, in words, for one it does
	not know."""
	valore = (stato or "").strip().lower()
	return STATI_CHIAMATA.get(valore) or " ".join(valore.split("-")).title()
