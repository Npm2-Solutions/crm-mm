# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Staying authenticated with Itala, the one accredited intermediary.

DottorCloud sends electronic invoices through one provider, Itala
(fattura-elettronica-api.it, REST API 2.0: `.pi/vendor/itala.md`), on **one account,
the agency's**, with every centre registered under it as a company of its own
(their multi-company management). The centre configures nothing: the account is
kept on the site's invoicing settings, where only the agency reads it, or once for
every site of the server in `common_site_config.json` (`itala_client_id`,
`itala_client_secret`). A company may still carry an account of its own, entered by
the agency on the company: then that one is used, and nothing is registered.

The environment is the company's: **a company starts in test** and goes live when
somebody says so (`crm.invoicing.prova`). A document carries its own environment -
a test invoice always goes to the test door, a real one always to production -
so nothing depends on where a switch was when it left.

Two things the provider's own contract lets us do, and both are worth the code:

* **the token is harvested, not fetched.** Every call made with Basic credentials
  comes back carrying `X-auth-token` and `X-auth-expires`. So the first useful call
  of the day pays for the token, and no login round trip is spent at all;
* **the expiry is read, never assumed.** The contract does not state how long a
  token lasts, so nothing here guesses a number: the cache is told exactly what the
  provider said, minus a minute of slack.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field

import frappe
from frappe import _
from frappe.utils import cint, now_datetime
from frappe.utils.password import get_decrypted_password

from crm.invoicing.engine import busta

SANDBOX = "sandbox"
PRODUZIONE = "production"
AMBIENTI = (SANDBOX, PRODUZIONE)

#: Itala's two doors. The test one answers the same calls and reaches no SdI.
BASE = {
	SANDBOX: "https://fattura-elettronica-api.it/ws2.0/test",
	PRODUZIONE: "https://fattura-elettronica-api.it/ws2.0/prod",
}

IMPOSTAZIONI = "CRM Invoicing Settings"
#: The agency's account for every site of a server, in `common_site_config.json`.
CONF_UTENTE = "itala_client_id"
CONF_SEGRETO = "itala_client_secret"

#: Re-exported so a reader of this module finds them where they look. They live in
#: the engine because deciding how long to trust a credential is a rule, and rules
#: are worth testing without a site.
DURATA_PRUDENTE = busta.DURATA_PRUDENTE
DURATA_MASSIMA = busta.DURATA_MASSIMA
MARGINE = busta.MARGINE

TIMEOUT = 60


class ErroreProvider(Exception):
	"""The provider could not be talked to. Never carries a credential.

	`incerto`: the request may have reached it and only the answer was lost."""

	def __init__(self, messaggio: str = "", incerto: bool = False):
		super().__init__(messaggio)
		self.incerto = incerto


@dataclass(frozen=True)
class Accesso:
	"""Who we are to Itala for one company, in one environment. Never printed."""

	ambiente: str
	base: str
	utente: str = field(repr=False)
	password: str = field(repr=False)
	#: the company's own account, entered by the agency: nothing to register
	proprio: bool = False
	azienda: str = ""

	@property
	def chiave_cache(self) -> str:
		# The environment is part of the key: a test token is no good in production,
		# and failing on it would read like bad credentials.
		chi = f"azienda:{self.azienda}" if self.proprio else "agenzia"
		return f"provider:token:{chi}:{self.ambiente}"

	def url(self, percorso: str) -> str:
		return f"{self.base}/{percorso.lstrip('/')}"


def ambiente(emittente: dict) -> str:
	"""Where this company is: in test until it goes live.

	Test is the safe default: a company nobody switched reaches nobody, which is
	visible. The opposite default sends real invoices from a configuration nobody
	finished.
	"""
	scelto = (emittente.get("provider_environment") or "").strip()
	return scelto if scelto in AMBIENTI else SANDBOX


def in_produzione(emittente: dict) -> bool:
	return ambiente(emittente) == PRODUZIONE


def ambiente_del_documento(doc) -> str:
	"""A test invoice goes to the test door, a real one to production. Always."""
	return SANDBOX if cint(doc.get("test_document")) else PRODUZIONE


def segreto(emittente: dict, campo: str) -> str | None:
	return get_decrypted_password(
		"CRM Invoicing Company", emittente.get("name"), campo, raise_exception=False
	)


def account_agenzia() -> tuple[str, str] | None:
	"""The agency's account: on the site first, else the server's for every site."""
	utente = (frappe.db.get_single_value(IMPOSTAZIONI, "itala_client_id") or "").strip()
	if utente:
		password = get_decrypted_password(
			IMPOSTAZIONI, IMPOSTAZIONI, "itala_client_secret", raise_exception=False
		)
		if password:
			return utente, password
	utente = str(frappe.conf.get(CONF_UTENTE) or "").strip()
	password = str(frappe.conf.get(CONF_SEGRETO) or "").strip()
	if utente and password:
		return utente, password
	return None


def codice_destinatario() -> str:
	"""Itala's recipient code for the agency's account: each centre registers it at
	the Agenzia to receive its suppliers' invoices here. On the site first, else the
	server's (`itala_codice_destinatario`)."""
	codice = (frappe.db.get_single_value(IMPOSTAZIONI, "itala_recipient_code") or "").strip()
	return (codice or str(frappe.conf.get("itala_codice_destinatario") or "")).strip().upper()


def da_dove_l_account() -> str:
	"""Where the agency's account is read from: `site`, `server`, or nothing."""
	if (frappe.db.get_single_value(IMPOSTAZIONI, "itala_client_id") or "").strip():
		return "site"
	if frappe.conf.get(CONF_UTENTE) and frappe.conf.get(CONF_SEGRETO):
		return "server"
	return ""


def ha_un_account_proprio(emittente: dict) -> bool:
	return bool((emittente.get("sdi_username") or "").strip() and segreto(emittente, "sdi_password"))


def accesso(emittente: dict, ambiente_scelto: str | None = None) -> Accesso:
	"""How to reach Itala for this company: its own account, else the agency's."""
	dove = ambiente_scelto if ambiente_scelto in AMBIENTI else ambiente(emittente)
	nome = emittente.get("name") or ""
	utente = (emittente.get("sdi_username") or "").strip()
	password = segreto(emittente, "sdi_password") if utente else None
	if utente and password:
		return Accesso(dove, BASE[dove], utente, password, proprio=True, azienda=nome)
	agenzia = account_agenzia()
	if not agenzia:
		raise ErroreProvider(
			_("Itala is not connected yet: the agency enters its account, then invoices can leave.")
		)
	return Accesso(dove, BASE[dove], agenzia[0], agenzia[1], azienda=nome)


def dimentica_token(chi: Accesso) -> None:
	"""Drop the cached token. Called when the provider says it is no longer good."""
	frappe.cache().delete_value(chi.chiave_cache)


def _basic(utente: str, password: str) -> dict:
	coppia = base64.b64encode(f"{utente}:{password}".encode()).decode()
	return {"Authorization": f"Basic {coppia}"}


def raccogli_token(chi: Accesso, risposta) -> None:
	"""Keep a token the provider volunteered on an ordinary call.

	Their contract returns `X-auth-token` alongside every Basic-authenticated
	response. Storing it here is what turns a login per request into a login per day.
	"""
	testate = risposta.headers or {}
	if testate.get("X-auth-token"):
		frappe.cache().set_value(
			chi.chiave_cache,
			testate["X-auth-token"],
			# their expiry is Italy's time, as the site's clock is
			expires_in_sec=busta.durata_token(testate.get("X-auth-expires"), now_datetime()),
		)


def intestazioni(chi: Accesso, rinnova: bool = False) -> dict:
	"""Authorisation for a call: the harvested token, else Basic.

	A Basic call is never wasted: its answer carries the token for the ones after it.
	"""
	if not rinnova:
		memorizzato = frappe.cache().get_value(chi.chiave_cache)
		if memorizzato:
			valore = memorizzato if isinstance(memorizzato, str) else memorizzato.decode()
			return {"Authorization": f"Bearer {valore}"}
	return _basic(chi.utente, chi.password)


def _chiama(chi: Accesso, metodo: str, url: str, **argomenti):
	"""One call, renewing the authorisation once if it has gone stale.

	A cached token can expire early - the provider reissues, an account is touched
	from the dashboard - and the answer to that is one retry with Basic, not a failed
	invoice. A second 401 is a real authentication problem and is reported as one.
	"""
	sessione = frappe.utils.get_request_session()
	testate_extra = argomenti.pop("headers", {})

	def _una(rinnova: bool):
		testate = {**intestazioni(chi, rinnova=rinnova), "Accept": "application/json", **testate_extra}
		return sessione.request(metodo, url, headers=testate, timeout=TIMEOUT, **argomenti)

	try:
		risposta = _una(rinnova=False)
		if risposta.status_code == 401:
			dimentica_token(chi)
			risposta = _una(rinnova=True)
	except Exception as errore:
		# a send that timed out, or lost its connection, may have arrived all the
		# same: who sends again must ask first (`itala.invia`)
		incerto = metodo == "POST" and _forse_arrivata(errore)
		# the message may carry the URL, never the credentials: they are in a header
		raise ErroreProvider(_("Itala is unreachable: {0}").format(str(errore)), incerto=incerto) from None

	if risposta.status_code == 401:
		raise ErroreProvider(
			_("Itala refused the account ({0}). The credentials never appear in this message.").format(401)
		)
	raccogli_token(chi, risposta)
	return risposta


def _forse_arrivata(errore: Exception) -> bool:
	"""Whether a failed call may have reached Itala: a timeout or a connection lost
	once it was open. One that never connected did not arrive."""
	nome = type(errore).__name__
	if nome in ("ConnectTimeout", "SSLError", "InvalidURL", "MissingSchema"):
		return False
	return "Timeout" in nome or nome in ("ConnectionError", "ChunkedEncodingError", "ProtocolError")


def posta(chi: Accesso, percorso: str, contenuto, tipo: str = "application/xml"):
	return _chiama(chi, "POST", chi.url(percorso), data=contenuto, headers={"Content-Type": tipo})


def posta_json(chi: Accesso, percorso: str, dati: dict):
	return _chiama(chi, "POST", chi.url(percorso), json=dati)


def leggi(chi: Accesso, percorso: str, parametri: dict | None = None, accetta: str = "application/json"):
	"""A GET. `accetta`: what is asked back - a notice is the SdI's XML."""
	return _chiama(chi, "GET", chi.url(percorso), params=parametri or {}, headers={"Accept": accetta})


def cancella(chi: Accesso, percorso: str):
	return _chiama(chi, "DELETE", chi.url(percorso))


def etichetta_ambiente(ambiente_scelto: str) -> str:
	"""What to append to a message so a test send can never read as a real one."""
	return "" if ambiente_scelto == PRODUZIONE else " " + _("[TEST - this document reached nobody]")
