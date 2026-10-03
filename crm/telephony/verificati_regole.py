# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A number of the centre's, verified to be shown on calls, without a site (doc 52).

A number the centre has with another operator - its landline, a doctor's mobile -
is shown on DottorCloud's calls once Twilio has verified it in the space: Twilio
calls the number from +1 415 723 4000, a recorded voice in English asks for a
code, and whoever answers types on the keypad the six digits DottorCloud shows on
the screen. No document is asked: answering proves the line is the centre's. What
these rules decide:

- **what Twilio is asked**: a name of at most 64 characters, the digits to dial
  once the call is answered (a switchboard's extension, ``w`` for half a second's
  wait), the seconds before Twilio calls (0 to 60);
- **where a verification stands**: waiting for the code, verified, or not. Twilio
  says how it went when the call is over; a verification still waiting after a
  quarter of an hour did not happen;
- **Twilio's refusals** in DottorCloud's words.

The words are English, translated where they are shown.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

#: How a verification stands (`CRM Caller ID.verification_status`).
IN_ATTESA = "Pending"
VERIFICATO = "Verified"
NON_VERIFICATO = "Failed"

#: Twilio's longest name of a caller ID.
NOME_MASSIMO = 64
#: The longest wait Twilio takes before its call, in seconds.
ATTESA_MASSIMA = 60
#: After this long, a verification nobody heard of again did not happen.
SCADENZA = timedelta(minutes=15)

#: The digits Twilio dials once the call is answered: digits, * and #, w to wait.
_INTERNO = re.compile(r"[0-9*#w]{1,32}")

#: What Twilio's StatusCallback says (`VerificationStatus`), as the row keeps it.
ESITI = {"success": VERIFICATO, "failed": NON_VERIFICATO}

#: Twilio's refusals of a verification, in DottorCloud's words.
RIFIUTI = {
	21449: "This number is already one of the centre's numbers on Twilio: it can be shown on calls already.",
	21450: "This number is verified already: it can be shown on calls.",
	21454: "Twilio waits from 0 to 60 seconds before calling.",
	21211: "Twilio does not take this number: write it with its country code, +39 for Italy.",
	21401: "Twilio does not take this number: write it with its country code, +39 for Italy.",
	13224: "Twilio does not take this number: write it with its country code, +39 for Italy.",
	21215: "The Twilio space may not call this country: add it to the countries the centre calls.",
	13227: "The Twilio space may not call this country: add it to the countries the centre calls.",
	20429: "Twilio asks to wait a little: try again in a minute.",
}


def nome_per_twilio(etichetta: str | None, numero: str) -> str:
	"""The name Twilio keeps for the caller ID: the label, else the number."""
	return ((etichetta or "").strip() or numero)[:NOME_MASSIMO]


def interno(valore: str | None) -> tuple[str, str]:
	"""The digits to dial once the call is answered, and why they cannot be ('' when
	they can). Spaces and dashes go; ``W`` reads as ``w``."""
	scritto = re.sub(r"[\s\-.]", "", valore or "").replace("W", "w")
	if not scritto:
		return "", ""
	if not _INTERNO.fullmatch(scritto):
		return "", "The extension takes digits, * and #, and w for half a second's wait: at most 32."
	return scritto, ""


def attesa(valore) -> tuple[int, str]:
	"""The seconds before Twilio calls, and why they cannot be ('' when they can)."""
	if valore in (None, ""):
		return 0, ""
	try:
		secondi = int(str(valore).strip())
	except ValueError:
		return 0, "Twilio waits from 0 to 60 seconds before calling."
	if not 0 <= secondi <= ATTESA_MASSIMA:
		return 0, "Twilio waits from 0 to 60 seconds before calling."
	return secondi, ""


def esito(stato_di_twilio: str | None) -> str:
	"""How the verification went, from Twilio's `VerificationStatus`; '' when it
	does not say."""
	return ESITI.get((stato_di_twilio or "").strip().lower(), "")


def scaduta(chiesta_il: datetime | None, adesso: datetime) -> bool:
	"""Whether a verification still waiting is over: past a quarter of an hour, or
	with no date at all."""
	return not chiesta_il or adesso - chiesta_il > SCADENZA


def rifiuto(codice) -> str:
	"""Twilio's refusal of a verification in DottorCloud's words; '' for a code it
	has no sentence of its own for."""
	try:
		return RIFIUTI.get(int(str(codice).strip()), "")
	except (TypeError, ValueError):
		return ""
