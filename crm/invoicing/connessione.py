# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Staying authenticated with the accredited provider.

One place, because both channels come through it. The defaults name the provider
this system ships with; endpoint, login URL and the field an identifier hides in
stay configuration, so the next provider is a settings change and not a rewrite.

Two things the provider's own contract lets us do, and both are worth the code:

* **the token is harvested, not fetched.** Every call made with Basic credentials
  comes back carrying `X-auth-token` and `X-auth-expires`. So the first useful call
  of the day pays for the token, and the dedicated login round trip is spent only
  when there is nothing else to piggyback on;
* **the expiry is read, never assumed.** The contract does not state how long a
  token lasts, so nothing here guesses a number: the cache is told exactly what the
  provider said, minus a minute of slack.

**The environment is not a detail.** A document sent to the sandbox has left
nothing: nobody saw it, the client never got it, and the only thing separating it
from a real invoice is which switch was set months ago. So it travels with the
document rather than staying in the configuration, and every message about a
sandbox send says so.
"""

from __future__ import annotations

from datetime import datetime

import frappe
from frappe import _
from frappe.utils.password import get_decrypted_password

from crm.invoicing.engine import busta

#: What the company's login field is seeded with. It lives on the DocType rather
#: than in this code, so clearing the field is a real choice and not a fallback.
LOGIN_PREDEFINITO = "https://fattura-elettronica-api.it/ws2.0/prod/authentication"

SANDBOX = "sandbox"
PRODUZIONE = "production"
AMBIENTI = (SANDBOX, PRODUZIONE)

#: Used when the provider does not say when its token expires. Short on purpose.
#: Never trust a stated expiry further than this, whatever the provider claims.
#: Slack between what the provider says and what we act on, so a token cannot die
#: between the check and the call.

#: Re-exported so a reader of this module finds them where they look. They live in
#: the engine because deciding how long to trust a credential is a rule, and rules
#: are worth testing without a site.
DURATA_PRUDENTE = busta.DURATA_PRUDENTE
DURATA_MASSIMA = busta.DURATA_MASSIMA
MARGINE = busta.MARGINE

TIMEOUT = 60


class ErroreProvider(Exception):
	"""The provider could not be talked to. Never carries a credential."""


def ambiente(emittente: dict) -> str:
	"""Which environment this company is aimed at. Unset means sandbox.

	Defaulting to sandbox is the safe direction: a company that has not said reaches
	nothing, which is visible. The opposite default sends real invoices from a
	configuration nobody finished.
	"""
	scelto = (emittente.get("provider_environment") or "").strip()
	return scelto if scelto in AMBIENTI else SANDBOX


def in_produzione(emittente: dict) -> bool:
	return ambiente(emittente) == PRODUZIONE


def segreto(emittente: dict, campo: str) -> str | None:
	return get_decrypted_password(
		"CRM Invoicing Company", emittente.get("name"), campo, raise_exception=False
	)


def _chiave_cache(emittente: dict) -> str:
	# The environment is part of the key: switching a company to production must not
	# reuse the sandbox token, which would fail in a way that reads like bad credentials.
	return f"provider:token:{emittente.get('name')}:{ambiente(emittente)}"


def dimentica_token(emittente: dict) -> None:
	"""Drop the cached token. Called when the provider says it is no longer good."""
	frappe.cache().delete_value(_chiave_cache(emittente))


def _accedi(emittente: dict, sessione) -> str:
	"""Exchange credentials for a token. The credentials never leave this function."""
	utente = (emittente.get("sdi_username") or "").strip()
	password = segreto(emittente, "sdi_password")
	if not (utente and password):
		raise ErroreProvider(_("No credentials for the provider: set an API key, or a user and password."))

	url = (emittente.get("sdi_login_url") or "").strip()
	if not url:
		raise ErroreProvider(_("No login endpoint for the provider"))
	try:
		risposta = sessione.post(
			url,
			headers={"Accept": "application/json", **_basic(utente, password)},
			timeout=TIMEOUT,
		)
	except Exception as errore:
		raise ErroreProvider(_("The provider's login is unreachable: {0}").format(str(errore))) from None

	if risposta.status_code != 200:
		# The status code is the whole diagnosis worth keeping. The body of a refused
		# login can echo back what was sent, and what was sent was a password.
		raise ErroreProvider(
			_("The provider refused the login ({0}). The credentials never appear in this message.").format(
				risposta.status_code
			)
		)

	corpo = risposta.json() if risposta.content else {}
	token = corpo.get("token") or corpo.get("access_token")
	if not token:
		raise ErroreProvider(_("The provider's login answered without a token"))
	return str(token), busta.durata_token(corpo.get("expires") or risposta.headers.get("X-auth-expires"))


def _basic(utente: str, password: str) -> dict:
	import base64

	coppia = base64.b64encode(f"{utente}:{password}".encode()).decode()
	return {"Authorization": f"Basic {coppia}"}


def raccogli_token(emittente: dict, risposta) -> None:
	"""Keep a token the provider volunteered on an ordinary call.

	Their contract returns `X-auth-token` alongside every Basic-authenticated
	response. Storing it here is what turns a login per request into a login per day.
	"""
	token = (risposta.headers or {}).get("X-auth-token")
	if token:
		frappe.cache().set_value(
			_chiave_cache(emittente),
			token,
			expires_in_sec=busta.durata_token((risposta.headers or {}).get("X-auth-expires")),
		)


def token(emittente: dict, sessione, rinnova: bool = False) -> str:
	"""A valid token, from the cache when there is one.

	The provider's token lasts a day, so logging in once per invoice is a round trip
	bought for nothing and a rate limit waiting for the first batch.
	"""
	chiave = _chiave_cache(emittente)
	if not rinnova:
		memorizzato = frappe.cache().get_value(chiave)
		if memorizzato:
			return memorizzato if isinstance(memorizzato, str) else memorizzato.decode()

	fresco, durata = _accedi(emittente, sessione)
	frappe.cache().set_value(chiave, fresco, expires_in_sec=durata)
	return fresco


def intestazioni(emittente: dict, sessione, rinnova: bool = False) -> dict:
	"""Authorisation for a call, whichever way this company authenticates.

	An API key is taken as given - it does not expire and there is nothing to cache.
	Otherwise the token is fetched, and reused until the provider says otherwise.
	"""
	chiave_api = segreto(emittente, "sdi_api_key")
	if chiave_api:
		return {"Authorization": f"Bearer {chiave_api}"}

	if (emittente.get("sdi_login_url") or "").strip():
		return {"Authorization": f"Bearer {token(emittente, sessione, rinnova=rinnova)}"}

	# No login exchange configured: the provider takes HTTP Basic directly. Kept
	# because the contract allows it - the first call may simply be Basic, and the
	# token then arrives in the response headers for the ones after it.
	utente = (emittente.get("sdi_username") or "").strip()
	password = segreto(emittente, "sdi_password")
	if not (utente and password):
		raise ErroreProvider(_("No credentials for the provider: set an API key, or a user and password."))
	return _basic(utente, password)


def posta(emittente: dict, url: str, contenuto, tipo: str = "application/xml"):
	"""POST to the provider, renewing the token once if it has gone stale.

	A cached token can expire early - the provider reissues, an account is touched
	from the dashboard - and the answer to that is one retry, not a failed invoice.
	A second 401 is a real authentication problem and is reported as one.
	"""
	sessione = frappe.utils.get_request_session()

	def _chiama(rinnova: bool):
		testate = intestazioni(emittente, sessione, rinnova=rinnova)
		testate.update({"Content-Type": tipo, "Accept": "application/json"})
		return sessione.post(url, data=contenuto, headers=testate, timeout=TIMEOUT)

	try:
		risposta = _chiama(rinnova=False)
		if risposta.status_code == 401:
			dimentica_token(emittente)
			risposta = _chiama(rinnova=True)
	except ErroreProvider:
		raise
	except Exception as errore:
		raise ErroreProvider(_("The provider is unreachable: {0}").format(str(errore))) from None

	# Their contract hands a token back on ordinary calls. Taking it here is what
	# makes the next call free rather than another login.
	raccogli_token(emittente, risposta)
	return risposta


def etichetta_ambiente(emittente: dict) -> str:
	"""What to append to a message so a sandbox send can never read as a real one."""
	return "" if in_produzione(emittente) else " " + _("[SANDBOX - this document reached nobody]")


def leggi(emittente: dict, url: str, parametri: dict | None = None):
	"""GET from the provider, with the same one-renewal rule as a POST.

	The inbound cycle reads; only the outbound one writes. Both authenticate the
	same way, so both go through here.
	"""
	sessione = frappe.utils.get_request_session()

	def _chiama(rinnova: bool):
		testate = intestazioni(emittente, sessione, rinnova=rinnova)
		testate["Accept"] = "application/json"
		return sessione.get(url, params=parametri or {}, headers=testate, timeout=TIMEOUT)

	try:
		risposta = _chiama(rinnova=False)
		if risposta.status_code == 401:
			dimentica_token(emittente)
			risposta = _chiama(rinnova=True)
	except ErroreProvider:
		raise
	except Exception as errore:
		raise ErroreProvider(_("The provider is unreachable: {0}").format(str(errore))) from None

	raccogli_token(emittente, risposta)
	return risposta
