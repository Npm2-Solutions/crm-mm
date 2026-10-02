# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Twilio's errors in DottorCloud's words, without a site (doc 52, fifth part).

Twilio names a problem with a number - 30003, 21610 - and a sentence of its own,
in English. The ones a medical centre meets get a sentence of DottorCloud's that
says what happened and, where there is one, what to do; any other keeps Twilio's
words with its code. Where they come from: an SMS that did not leave or did not
arrive (the error on the message), and Twilio's log of the space's problems (its
"Monitor"), on Twilio's page in DottorCloud.

The words are English, translated where they are shown; ``{brand}`` is the
product's name, filled in with it (``marchio.con_nome``).
"""

from __future__ import annotations

#: A code Twilio gives and what it means here.
ERRORI: dict[int, str] = {
	# the account
	10001: "The Twilio account is not active: usually its credit ran out. Top it up on Twilio.",
	20005: "The Twilio account is not active: usually its credit ran out. Top it up on Twilio.",
	20003: "Twilio refused {brand}'s codes: check the connection on Twilio's page.",
	# the SMS
	21211: "The person's number is not a valid number.",
	21212: "Twilio does not take the SMS sender: choose another one on Twilio's page.",
	21408: "SMS to this country are not allowed in the Twilio account's permissions.",
	21606: "This number of the centre cannot send SMS.",
	21610: "The person had asked Twilio to stop the SMS from this number, with STOP.",
	21612: "The person's number cannot receive SMS from this sender.",
	21614: "The person's number is not a mobile: it cannot receive SMS.",
	30003: "The person's phone was off or out of reach.",
	30005: "The person's number does not exist any more.",
	30006: "The person's number is a landline, or its operator does not take SMS.",
	30007: "The operator stopped the message as unwanted.",
	30008: "The operator did not deliver the message and did not say why.",
	# the calls
	13224: "The number called is not a valid number.",
	13225: "Twilio blocked the call: it holds that number at risk of fraud.",
	13227: "Calls to this country are not allowed in the Twilio account's permissions.",
	21215: "Calls to this country are not allowed in the Twilio account's permissions.",
	21216: "Twilio blocked the call: the number is premium-rate or on its block list.",
	# the product and Twilio
	11200: "Twilio could not reach {brand}: an incoming call or SMS may have been lost.",
	11205: "Twilio could not reach {brand}: an incoming call or SMS may have been lost.",
	12100: "Twilio could not read {brand}'s answer to a call or an SMS.",
	12200: "Twilio could not read {brand}'s answer to a call or an SMS.",
	12300: "Twilio could not read {brand}'s answer to a call or an SMS.",
}

#: How many kinds of problem the page lists.
QUANTI = 8


def codice(valore) -> int | None:
	"""Twilio's code as a number: it comes as a number, a string, or nothing."""
	try:
		numero = int(str(valore).strip())
	except (TypeError, ValueError):
		return None
	return numero or None


def frase(valore) -> str | None:
	"""DottorCloud's sentence for a code of Twilio's; None for one it does not know."""
	return ERRORI.get(codice(valore))


def raggruppa(avvisi: list[dict], quanti: int = QUANTI) -> list[dict]:
	"""Twilio's log of problems, one row per code: how many times, the last one,
	DottorCloud's sentence (``sentence``, None when it has none) and Twilio's own
	words. The most recent first, at most ``quanti``."""
	righe: dict[int | str, dict] = {}
	for avviso in avvisi:
		numero = codice(avviso.get("error_code"))
		chiave = numero if numero is not None else (avviso.get("alert_text") or "")[:80]
		quando = avviso.get("date_created")
		riga = righe.get(chiave)
		if riga is None:
			righe[chiave] = {
				"code": numero,
				"count": 1,
				"last": quando,
				"sentence": ERRORI.get(numero),
				"twilio": (avviso.get("alert_text") or "").strip()[:300],
				"more_info": avviso.get("more_info") or "",
			}
			continue
		riga["count"] += 1
		if quando and (not riga["last"] or quando > riga["last"]):
			riga["last"] = quando
			riga["twilio"] = (avviso.get("alert_text") or riga["twilio"]).strip()[:300]
	return sorted(righe.values(), key=lambda riga: str(riga["last"] or ""), reverse=True)[:quanti]
