# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Telnyx's errors in DottorCloud's words, without a site (doc 64).

Telnyx names a problem with a code - 40300, 10009 - a title and a detail, in
English. The ones a medical centre meets get a sentence of DottorCloud's that says
what happened and, where there is one, what to do; any other keeps Telnyx's words
with its code. Where they come from: an SMS that did not leave or did not arrive
(its ``errors``), a refusal of the API, the last days' failed messages on Telnyx's
page in DottorCloud.

The codes and their meaning are Telnyx's own list ("Telnyx Messaging Error
Codes", support.telnyx.com 6505121). The words are English, translated where they
are shown; ``{brand}`` is the product's name, filled in with it.
"""

from __future__ import annotations

#: A code Telnyx gives and what it means here.
ERRORI: dict[int, str] = {
	# the account and its key
	10009: "Telnyx refused {brand}'s key: check the connection on Telnyx's page.",
	10010: "Telnyx refused {brand}'s key: check the connection on Telnyx's page.",
	20002: "The Telnyx key was revoked: connect Telnyx again with a new one.",
	20012: "The Telnyx account is not active: usually its balance ran out. Top it up on Telnyx.",
	20013: "Telnyx blocked the account: write to Telnyx's support.",
	20100: "The Telnyx balance ran out: top it up on Telnyx.",
	20015: "SMS are not switched on in the Telnyx account.",
	20017: "Telnyx sends with the centre's name only from an account verified to level 2: verify it on Telnyx, or choose a number as the sender.",
	# the person's number
	10002: "The person's number is not a valid number.",
	10016: "The person's number is not a valid number.",
	40001: "The person's number is a landline, or its operator does not take SMS.",
	40012: "The person's number does not exist any more, or cannot receive SMS.",
	40310: "The person's number is not a valid number.",
	40300: "The person had asked to stop the SMS from this number, with STOP.",
	# the operators
	40002: "The operator stopped the message as unwanted.",
	40003: "The operator stopped the message as unwanted.",
	40015: "Telnyx stopped the message as unwanted.",
	40004: "The person's operator refused the message.",
	40005: "The operator did not deliver the message in time.",
	40006: "The person's operator could not be reached: the message did not arrive.",
	40008: "The operator did not deliver the message and did not say why.",
	40009: "The operator did not take the message's words.",
	40322: "Telnyx stopped the message for its words.",
	40014: "Too many messages at once: this one waited too long and did not leave.",
	40318: "Too many messages at once: this one waited too long and did not leave.",
	40011: "Too many messages at once: the operator stopped them.",
	# the sender
	40013: "This number of the centre cannot send SMS.",
	40100: "This number of the centre cannot send SMS: it has no messaging profile in Telnyx. Check the connection on Telnyx's page.",
	40305: "Telnyx does not take the number or the name shown: choose another sender on Telnyx's page.",
	40306: "Telnyx does not take the centre's name as the sender: choose another on Telnyx's page.",
	40315: "Telnyx holds this number of the centre unhealthy for SMS: too many messages were not delivered.",
	40320: "This number of the centre is still being bought: try again in a few minutes.",
	40321: "The centre has no number that can send SMS in Telnyx.",
	40309: "SMS to this country are not allowed in the Telnyx account's messaging profile.",
	40312: "The messaging profile is switched off in Telnyx: check the connection on Telnyx's page.",
	40314: "SMS are switched off in the Telnyx account.",
	40333: "The Telnyx account reached its spending limit for today.",
}

#: The SIP reasons Telnyx gives a call that did not leave (its "D" codes), and
#: what they mean here.
CHIAMATE: dict[str, str] = {
	"D11": "The number called is not a valid number.",
	"D14": "The number called is not a valid number.",
	"D13": "Calls to this country are not allowed in the Telnyx account's outbound voice profile.",
	"D35": "The number shown on the call is not one Telnyx lets the account show: choose another.",
	"D36": "The number shown on the call is another Telnyx customer's: choose another.",
	"D51": "The number shown on the call is not verified in Telnyx: verify it on Telnyx's page, under Numbers.",
	"D39": "The Telnyx account reached its daily spending limit for calls abroad.",
	"D54": "Telnyx holds the number shown on the call at risk: choose another.",
}

#: How many kinds of problem the page lists.
QUANTI = 8


def codice(valore) -> int | None:
	"""Telnyx's code as a number: it comes as a string ("40300"), a number, or nothing."""
	try:
		numero = int(str(valore).strip())
	except (TypeError, ValueError):
		return None
	return numero or None


def frase(valore) -> str | None:
	"""DottorCloud's sentence for a code of Telnyx's; None for one it does not know."""
	return ERRORI.get(codice(valore))


def primo_errore(errori: list | None) -> tuple[int | None, str]:
	"""The first of a message's or a refusal's ``errors``: its code and Telnyx's
	words (the detail, else the title)."""
	for errore in errori or []:
		if isinstance(errore, dict):
			testo = (errore.get("detail") or errore.get("title") or "").strip()
			return codice(errore.get("code")), testo[:300]
		if isinstance(errore, str | int):
			return codice(errore), ""
	return None, ""


def raggruppa(righe: list[dict], quanti: int = QUANTI) -> list[dict]:
	"""The last days' failed messages, one row per code: how many times, the last
	one, DottorCloud's sentence (``sentence``, None when it has none). The most
	recent first, at most ``quanti``. ``righe``: ``{"code", "created_at"}``."""
	gruppi: dict[int | str, dict] = {}
	for riga in righe:
		numero = codice(riga.get("code"))
		chiave = numero if numero is not None else ""
		quando = riga.get("created_at") or ""
		gruppo = gruppi.get(chiave)
		if gruppo is None:
			gruppi[chiave] = {
				"code": numero,
				"count": 1,
				"last": quando,
				"sentence": ERRORI.get(numero),
				"telnyx": (riga.get("title") or "").strip()[:300],
			}
			continue
		gruppo["count"] += 1
		if quando and quando > (gruppo["last"] or ""):
			gruppo["last"] = quando
	return sorted(gruppi.values(), key=lambda g: str(g["last"] or ""), reverse=True)[:quanti]
