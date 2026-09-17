# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The connection to the accredited provider.

One place holds what every call to the provider needs - which environment it is
aimed at, and a token that is still valid - because both channels go through it:
the Sistema di Interscambio and, for companies that want it there too, the Sistema
Tessera Sanitaria.

The defaults name A-Cube, because that is the provider this system is sold with.
Nothing here is welded to it: endpoint, login URL and the field the identifier
comes back in stay configuration, so the next provider is a settings change and not
a rewrite.

**The environment is not a detail.** A document sent to the sandbox has left
nothing: the SdI never saw it, the client never got it, and the only thing that
distinguishes it from a real invoice is that somebody remembered which switch was
set. So the environment travels with the document rather than staying in the
configuration, and every message this module writes about a sandbox send says so.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils.password import get_decrypted_password

#: What the company's login field is seeded with. It lives on the DocType rather
#: than in this code, so clearing the field is a real choice and not a fallback.
LOGIN_PREDEFINITO = "https://common.api.acubeapi.com/login"

SANDBOX = "sandbox"
PRODUZIONE = "production"
AMBIENTI = (SANDBOX, PRODUZIONE)

#: The token is good for 24 hours. Dropping it an hour early costs one login and
#: removes the race where a token expires between the check and the call.
DURATA_TOKEN = 23 * 3600

TIMEOUT = 60


class ErroreAcube(Exception):
	"""The provider could not be talked to. Never carries a credential."""


def ambiente(emittente: dict) -> str:
	"""Which environment this company is aimed at. Unset means sandbox.

	Defaulting to sandbox is the safe direction: a company that has not said reaches
	nothing, which is visible. The opposite default sends real invoices from a
	configuration nobody finished.
	"""
	scelto = (emittente.get("acube_environment") or "").strip()
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
	return f"acube:token:{emittente.get('name')}:{ambiente(emittente)}"


def dimentica_token(emittente: dict) -> None:
	"""Drop the cached token. Called when the provider says it is no longer good."""
	frappe.cache().delete_value(_chiave_cache(emittente))


def _accedi(emittente: dict, sessione) -> str:
	"""Exchange credentials for a token. The credentials never leave this function."""
	utente = (emittente.get("sdi_username") or "").strip()
	password = segreto(emittente, "sdi_password")
	if not (utente and password):
		raise ErroreAcube(_("No credentials for the provider: set an API key, or a user and password."))

	url = (emittente.get("sdi_login_url") or "").strip()
	if not url:
		raise ErroreAcube(_("No login endpoint for the provider"))
	try:
		risposta = sessione.post(
			url,
			json={"email": utente, "password": password, "environment": ambiente(emittente)},
			headers={"Accept": "application/json", "Content-Type": "application/json"},
			timeout=TIMEOUT,
		)
	except Exception as errore:
		raise ErroreAcube(_("The provider's login is unreachable: {0}").format(errore)) from None

	if risposta.status_code != 200:
		# The status code is the whole diagnosis worth keeping. The body of a refused
		# login can echo back what was sent, and what was sent was a password.
		raise ErroreAcube(
			_("The provider refused the login ({0}). The credentials never appear in this message.").format(
				risposta.status_code
			)
		)

	corpo = risposta.json() if risposta.content else {}
	token = corpo.get("token") or corpo.get("access_token")
	if not token:
		raise ErroreAcube(_("The provider's login answered without a token"))
	return str(token)


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

	fresco = _accedi(emittente, sessione)
	frappe.cache().set_value(chiave, fresco, expires_in_sec=DURATA_TOKEN)
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

	# No login exchange configured: the provider takes HTTP Basic directly. Kept for
	# the providers that still work that way - the default login URL is the one this
	# system ships with, and clearing that field is how you ask for this path.
	import base64

	utente = (emittente.get("sdi_username") or "").strip()
	password = segreto(emittente, "sdi_password")
	if not (utente and password):
		raise ErroreAcube(_("No credentials for the provider: set an API key, or a user and password."))
	coppia = base64.b64encode(f"{utente}:{password}".encode()).decode()
	return {"Authorization": f"Basic {coppia}"}


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
	except ErroreAcube:
		raise
	except Exception as errore:
		raise ErroreAcube(_("The provider is unreachable: {0}").format(errore)) from None
	return risposta


def etichetta_ambiente(emittente: dict) -> str:
	"""What to append to a message so a sandbox send can never read as a real one."""
	return "" if in_produzione(emittente) else _(" [SANDBOX - this document reached nobody]")
