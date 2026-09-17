# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""An accredited intermediary's REST API.

What a provider sells here is the accredited channel and the archiving, not the
format: the XML arrives already built and already checked against the SdI's own
rejection codes. So this posts a file and reads back an identifier, and that is
the whole contract.

Endpoint, authentication and the field the identifier comes back in are
configuration, because they differ per provider and pinning one vendor's shape into
the code is how the next migration turns into a rewrite. Getting authenticated and
staying that way is `crm.invoicing.acube`, shared with the Sistema TS channel.

Onboarding rule worth keeping from the original design: **one registration per
company, never a shared master account.** That way fiscal responsibility and the
archive stay with whoever issued the invoices, and a client who leaves takes their
history with them.
"""

from __future__ import annotations

import json

import frappe
from frappe import _

from crm.invoicing import acube
from crm.invoicing.sdi.base import ErroreCanale, EsitoInvio

CODICE = "provider"
ETICHETTA = "Accredited provider (REST)"

#: Where the identifier hides, depending on who is answering.
CHIAVI_IDENTIFICATIVO = ("uuid", "id", "identifier", "invoice_uuid", "identificativoSdI", "sdi_id")


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

	contenuto = _contenuto(doc.get("sdi_signed_file") or doc.xml_file)

	try:
		risposta = acube.posta(emittente, endpoint, contenuto, tipo="application/xml")
	except acube.ErroreAcube as errore:
		raise ErroreCanale(str(errore)) from None

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
		)
		+ acube.etichetta_ambiente(emittente),
		dettagli={"environment": acube.ambiente(emittente)},
	)
