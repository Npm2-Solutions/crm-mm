# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Connecting the centre's Twilio account, without a site (doc 52).

- **Two codes, checked before Twilio is asked**: the Account SID is AC and 32
  hexadecimal digits, the Auth Token 32 of them; the spaces and the line copied
  around them do not count.
- **DottorCloud's space** in the account is a subaccount named after the site, so
  the centre recognises it in its console and another site does not take it.
- **What a number and the app need**: a number of the space sends its calls and its
  messages to DottorCloud, by POST, with no app of Twilio's in front of the address
  (an app set on the number wins over its address). A number handed to a SIP trunk
  is left as it is: the trunk takes its calls, and the page says so.
- **Twilio's answers in words**: codes Twilio does not recognise, an account it does
  not find, Twilio that does not answer; an account suspended, closed or on trial.

The words are English, translated where they are shown.
"""

from __future__ import annotations

import re
from urllib.parse import urlsplit

#: The name of DottorCloud's key and app, and the first word of its space.
NOME = "DottorCloud"
#: Twilio keeps a friendly name to 64 characters.
LUNGHEZZA_DEL_NOME = 64

#: Whose account the space lives in: the centre's, or the agency's for a centre with
#: the agency's front desk. Nothing: connected by hand in the Desk, before doc 52.
CENTRO, AGENZIA = "Centre", "Agency"

_SID = re.compile(r"AC[0-9a-fA-F]{32}")
_TOKEN = re.compile(r"[0-9a-fA-F]{32}")


def pulito(codice: str | None) -> str:
	"""A code as it was copied, without the spaces and lines around it or inside it."""
	return re.sub(r"\s+", "", codice or "")


def sid_valido(sid: str | None) -> bool:
	return bool(_SID.fullmatch(pulito(sid)))


def token_valido(token: str | None) -> bool:
	return bool(_TOKEN.fullmatch(pulito(token)))


def cosa_manca(sid: str | None, token: str | None) -> str:
	"""What stops asking Twilio with these two codes; '' when nothing does."""
	if not pulito(sid):
		return "Paste the Account SID."
	if not sid_valido(sid):
		return "The Account SID starts with AC and has 34 characters: copy it again from the console."
	if not pulito(token):
		return "Paste the Auth Token."
	if not token_valido(token):
		return "The Auth Token has 32 letters and digits: copy it again from the console."
	return ""


def mascherato(sid: str | None) -> str:
	"""A SID as the page shows it: its kind and its last four characters."""
	sid = pulito(sid)
	if len(sid) <= 8:
		return sid
	return f"{sid[:2]}…{sid[-4:]}"


def nome_dello_spazio(indirizzo: str | None, prodotto: str = NOME) -> str:
	"""The space's name: the product's and the site's address, as the console shows it."""
	indirizzo = (indirizzo or "").strip()
	prodotto = prodotto or NOME
	host = urlsplit(indirizzo).hostname if "//" in indirizzo else indirizzo.strip("/")
	nome = f"{prodotto} · {host}" if host else prodotto
	return nome[:LUNGHEZZA_DEL_NOME]


def _giusto(attuale: dict, tipo: str, indirizzo: str) -> dict:
	"""What to change so ``tipo`` (voice, sms) reaches ``indirizzo``: {} when it does."""
	app = attuale.get(f"{tipo}_application_sid")
	metodo = (attuale.get(f"{tipo}_method") or "POST").upper()
	if not app and (attuale.get(f"{tipo}_url") or "") == indirizzo and metodo == "POST":
		return {}
	cambi = {f"{tipo}_url": indirizzo, f"{tipo}_method": "POST"}
	if app:
		cambi[f"{tipo}_application_sid"] = ""
	return cambi


def da_sistemare(numero: dict, voce: str, sms: str) -> dict:
	"""What to change on a number of the space so its calls and its messages reach
	DottorCloud; {} when they do, or when a SIP trunk takes the number.

	``numero`` as Twilio describes it: ``voice_url``, ``voice_method``,
	``voice_application_sid``, the same for ``sms``, ``trunk_sid``, ``capabilities``.
	"""
	if numero.get("trunk_sid"):
		return {}
	capacita = numero.get("capabilities") or {}
	cambi = {}
	if capacita.get("voice", True):
		cambi.update(_giusto(numero, "voice", voce))
	if capacita.get("sms"):
		cambi.update(_giusto(numero, "sms", sms))
	return cambi


def app_da_sistemare(app: dict, voce: str) -> dict:
	"""What to change on DottorCloud's app so the browser's calls reach DottorCloud."""
	metodo = (app.get("voice_method") or "POST").upper()
	if (app.get("voice_url") or "") == voce and metodo == "POST":
		return {}
	return {"voice_url": voce, "voice_method": "POST"}


def errore_in_parole(stato: int | None, codice: int | None = None) -> tuple[str, list]:
	"""Twilio's refusal in words: the sentence and what goes in it.

	``stato``: the HTTP status Twilio answered with, None when it did not answer;
	``codice``: Twilio's own error code.
	"""
	if stato in (401, 403) or codice == 20003:
		return (
			"Twilio does not recognise these codes: copy the Account SID and the Auth Token again from the console.",
			[],
		)
	if stato == 404 or codice == 20404:
		return ("Twilio does not find this account, or it was closed.", [])
	if stato is None:
		return ("Twilio does not answer: try again in a few minutes.", [])
	return ("Twilio answered with an error ({0}): try again in a few minutes.", [codice or stato])


def stato_in_parole(stato: str | None, tipo: str | None) -> str:
	"""What the page says of the account Twilio describes; '' when it works."""
	if stato == "suspended":
		return "Twilio suspended the account: calls and messages stop until it is active again."
	if stato == "closed":
		return "The space was closed in Twilio: connect again to make a new one."
	if tipo == "Trial":
		return (
			"A trial account: Twilio calls only the numbers you verified and sells no Italian numbers. "
			"Upgrade it on Twilio with a payment method."
		)
	return ""
