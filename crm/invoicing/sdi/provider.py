# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""An accredited intermediary's REST API.

What a provider sells here is the accredited channel and the archiving, not the
format: the XML arrives already built and already checked against the SdI's own
rejection codes. So this posts a file and reads back an identifier, and that is
the whole contract.

Endpoint, authentication and the field the identifier comes back in are
configuration, because they differ per provider and pinning one vendor's shape into
the code is how the next migration turns into a rewrite.

Onboarding rule worth keeping from the original design: **one registration per
company, never a shared master account.** That way fiscal responsibility and the
archive stay with whoever issued the invoices, and a client who leaves takes their
history with them.
"""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils.password import get_decrypted_password

from crm.invoicing.sdi.base import ErroreCanale, EsitoInvio

CODICE = "provider"
ETICHETTA = "Accredited provider (REST)"

TIMEOUT = 60
#: Where the identifier hides, depending on who is answering.
CHIAVI_IDENTIFICATIVO = ("uuid", "id", "identifier", "invoice_uuid", "identificativoSdI", "sdi_id")


def _segreto(emittente: dict, campo: str) -> str | None:
	return get_decrypted_password(
		"CRM Invoicing Company", emittente.get("name"), campo, raise_exception=False
	)


def _intestazioni(emittente: dict, sessione) -> dict:
	"""Bearer token if there is one, otherwise a login exchange, otherwise Basic."""
	chiave = _segreto(emittente, "sdi_api_key")
	if chiave:
		return {"Authorization": f"Bearer {chiave}"}

	utente = emittente.get("sdi_username")
	password = _segreto(emittente, "sdi_password")
	if not (utente and password):
		raise ErroreCanale(_("No credentials for the provider: set an API key, or a user and password."))

	login = (emittente.get("sdi_login_url") or "").strip()
	if not login:
		# No login endpoint configured: the provider takes HTTP Basic directly.
		import base64

		coppia = base64.b64encode(f"{utente}:{password}".encode()).decode()
		return {"Authorization": f"Basic {coppia}"}

	risposta = sessione.post(login, json={"email": utente, "password": password}, timeout=TIMEOUT)
	if risposta.status_code != 200:
		raise ErroreCanale(
			_("The provider refused the login ({0}). The credentials never appear in this message.").format(
				risposta.status_code
			)
		)
	corpo = risposta.json() if risposta.content else {}
	token = corpo.get("token") or corpo.get("access_token")
	if not token:
		raise ErroreCanale(_("The provider's login answered without a token"))
	return {"Authorization": f"Bearer {token}"}


def _contenuto(url: str) -> bytes:
	allegato = frappe.get_doc("File", {"file_url": url})
	contenuto = allegato.get_content(encodings=[])
	return contenuto.encode() if isinstance(contenuto, str) else contenuto


def _identificativo(corpo) -> str | None:
	if isinstance(corpo, str):
		return corpo.strip() or None
	if not isinstance(corpo, dict):
		return None
	for chiave in CHIAVI_IDENTIFICATIVO:
		valore = corpo.get(chiave)
		if valore:
			return str(valore)
	for annidato in corpo.values():
		if isinstance(annidato, dict):
			trovato = _identificativo(annidato)
			if trovato:
				return trovato
	return None


def invia(doc, emittente: dict) -> EsitoInvio:
	endpoint = (emittente.get("sdi_endpoint") or "").strip()
	if not endpoint:
		raise ErroreCanale(
			_("No endpoint for provider {0}: the XML is ready, the channel is not.").format(
				emittente.get("sdi_provider") or "-"
			)
		)
	if not doc.xml_file:
		raise ErroreCanale(_("This invoice has no XML to send"))

	sessione = frappe.utils.get_request_session()
	intestazioni = _intestazioni(emittente, sessione)
	intestazioni.update({"Content-Type": "application/xml", "Accept": "application/json"})
	contenuto = _contenuto(doc.get("sdi_signed_file") or doc.xml_file)

	try:
		risposta = sessione.post(endpoint, data=contenuto, headers=intestazioni, timeout=TIMEOUT)
	except Exception as errore:
		raise ErroreCanale(_("The provider is unreachable: {0}").format(errore)) from None

	if risposta.status_code not in (200, 201, 202):
		# The body is worth keeping - it usually names the field that was refused -
		# but it is truncated, because a provider that echoes the invoice back would
		# otherwise put the whole document in a log.
		raise ErroreCanale(
			_("The provider answered {0}: {1}").format(risposta.status_code, (risposta.text or "")[:500])
		)

	try:
		corpo = risposta.json() if risposta.content else {}
	except json.JSONDecodeError:
		corpo = (risposta.text or "").strip()

	identificativo = _identificativo(corpo)
	return EsitoInvio(
		canale=CODICE,
		inviato=True,
		identificativo=identificativo,
		nome_file=doc.sdi_filename,
		messaggio=_("Accepted by {0}{1}. The outcome arrives as a notice.").format(
			emittente.get("sdi_provider") or _("the provider"),
			f" ({identificativo})" if identificativo else "",
		),
	)
