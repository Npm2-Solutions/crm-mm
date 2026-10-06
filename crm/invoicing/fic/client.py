# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Fatture in Cloud's API v2, as a function: a method, a path, the token.

What it answers is its JSON (an XML for the e-invoice's file); what goes wrong is
an `ErroreFiC` with Fatture in Cloud's own sentence, already in Italian, and its
status. A token is never in a log nor in an error: the variables that hold one are
named `*_token`, which a traceback hides.
"""

from __future__ import annotations

import requests
from frappe import _

API = "https://api-v2.fattureincloud.it"
AUTORIZZA = f"{API}/oauth/authorize"
TOKEN = f"{API}/oauth/token"
#: Seconds before a call is given up: Fatture in Cloud answers in one or two.
ATTESA = 30


class ErroreFiC(Exception):
	"""Fatture in Cloud said no, or said nothing.

	`stato` is the HTTP status (401: the access is gone; 429: too many calls);
	`incerto`: the answer was lost on the way, so what was asked may have been done
	all the same - the next attempt asks first."""

	def __init__(self, messaggio: str, stato: int | None = None, incerto: bool = False, rilievi=None):
		super().__init__(messaggio)
		self.stato = stato
		self.incerto = incerto
		self.rilievi = list(rilievi or [])


def _parole(risposta: requests.Response) -> tuple[str, list[str]]:
	"""Fatture in Cloud's sentence for an error, and the findings of a check."""
	try:
		corpo = risposta.json()
	except ValueError:
		return "", []
	errore = (corpo or {}).get("error") or {}
	if isinstance(errore, str):
		return errore, []
	messaggio = errore.get("message") or (corpo or {}).get("message") or ""
	rilievi = errore.get("validation_result") or []
	if isinstance(rilievi, dict):
		rilievi = [f"{chiave}: {valore}" for chiave, valore in rilievi.items()]
	return str(messaggio), [str(rilievo) for rilievo in rilievi if rilievo]


def errore_da(risposta: requests.Response) -> ErroreFiC:
	messaggio, rilievi = _parole(risposta)
	stato = risposta.status_code
	if stato == 401:
		testo = _("Fatture in Cloud no longer recognises the access: connect it again.")
	elif stato == 403 and not messaggio:
		testo = _("Fatture in Cloud does not allow it with the access given: connect it again.")
	elif stato == 429:
		attesa = risposta.headers.get("Retry-After") or "60"
		testo = _("Fatture in Cloud asks to wait {0} seconds: too many requests in a short time.").format(
			attesa
		)
	elif stato >= 500:
		testo = _("Fatture in Cloud is not answering right now: try again in a few minutes.")
	else:
		testo = messaggio or _("Fatture in Cloud refused the request ({0}).").format(stato)
	return ErroreFiC(testo, stato=stato, rilievi=rilievi)


def chiama(
	metodo: str,
	percorso: str,
	access_token: str,
	json: dict | None = None,
	params: dict | None = None,
	testo: bool = False,
):
	"""One call. `testo`: the answer is a file (the e-invoice's XML), not JSON."""
	try:
		risposta = requests.request(
			metodo,
			f"{API}{percorso}",
			headers={
				"Authorization": f"Bearer {access_token}",
				"Accept": "text/xml" if testo else "application/json",
			},
			json=json,
			params=params,
			timeout=ATTESA,
		)
	except (requests.Timeout, requests.ConnectionError) as errore:
		raise ErroreFiC(_("Fatture in Cloud did not answer in time."), incerto=True) from errore
	if risposta.status_code >= 400:
		raise errore_da(risposta)
	if testo:
		return risposta.text
	if not risposta.content:
		return {}
	try:
		return risposta.json()
	except ValueError:
		return {}


def chiedi_token(dati: dict) -> dict:
	"""The token endpoint: a code or a refresh token for an access token. What it
	answers holds tokens: it goes nowhere but the connection's password fields."""
	try:
		risposta = requests.post(TOKEN, json=dati, timeout=ATTESA)
	except (requests.Timeout, requests.ConnectionError) as errore:
		raise ErroreFiC(_("Fatture in Cloud did not answer in time."), incerto=True) from errore
	if risposta.status_code >= 400:
		messaggio, _rilievi = _parole(risposta)
		try:
			codice = (risposta.json() or {}).get("error") or ""
		except ValueError:
			codice = ""
		if codice in ("invalid_grant", "invalid_request") or risposta.status_code in (400, 401):
			raise ErroreFiC(
				_("Fatture in Cloud did not accept the access: connect it again."),
				stato=risposta.status_code,
			)
		raise ErroreFiC(
			messaggio or _("Fatture in Cloud refused the request ({0}).").format(risposta.status_code),
			stato=risposta.status_code,
		)
	try:
		return risposta.json() or {}
	except ValueError as errore:
		raise ErroreFiC(_("Fatture in Cloud answered something unreadable.")) from errore
