# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""PEC: the practice's own mailbox writes to the Sistema di Interscambio.

This is the route that needs nobody. A certified mailbox, an address, and the
invoice leaves - no intermediary holding the documents, no contract, no per-invoice
fee. The original design could not take it, because it had no mailbox of its own to
send from; here the CRM already runs email accounts, so it does.

Two details that decide whether it works at all:

* **the first submission goes to `sdi01@pec.fatturapa.it`, and only the first.**
  With the delivery receipt the SdI tells you which address to use from then on,
  and mail sent to the wrong one is not answered. So the address is stored on the
  company and updated when the SdI says so, rather than hard-coded in a send call;
* **an invoice to a public administration has to be signed.** A qualified
  signature is mandatory on FPA12 and optional on FPR12. Sending an unsigned PA
  invoice gets `00102` back, and by then the five days are running - so this
  refuses instead, and says what is missing.
"""

from __future__ import annotations

import frappe
from frappe import _

from crm.invoicing.engine.codici import FORMATO_PA
from crm.invoicing.engine.fatturapa import DIMENSIONE_MASSIMA_MESSAGGIO_PEC
from crm.invoicing.sdi.base import ErroreCanale, EsitoInvio

CODICE = "pec"
ETICHETTA = "PEC (own certified mailbox)"

#: Where the very first invoice goes. Afterwards the SdI names its own address.
INDIRIZZO_INIZIALE = "sdi01@pec.fatturapa.it"


def _contenuto(url: str) -> bytes:
	allegato = frappe.get_doc("File", {"file_url": url})
	contenuto = allegato.get_content(encodings=[])
	return contenuto.encode() if isinstance(contenuto, str) else contenuto


def indirizzo_sdi(emittente: dict) -> str:
	return (emittente.get("sdi_pec_address") or "").strip() or INDIRIZZO_INIZIALE


def invia(doc, emittente: dict) -> EsitoInvio:
	mittente = (emittente.get("pec") or "").strip()
	if not mittente:
		raise ErroreCanale(
			_("No PEC address on the company: the SdI only accepts mail from a certified mailbox")
		)
	if not frappe.db.exists("Email Account", {"email_id": mittente, "enable_outgoing": 1}):
		raise ErroreCanale(
			_(
				"There is no outgoing Email Account for {0}. Add the PEC mailbox under Email "
				"Accounts, with both sending and receiving on - the notices come back to it."
			).format(mittente)
		)
	if not doc.xml_file:
		raise ErroreCanale(_("This invoice has no XML to send"))

	firmato = bool(doc.get("sdi_signed_file"))
	if doc.recipient_type == "pubblica_amministrazione" and not firmato:
		raise ErroreCanale(
			_(
				"An invoice to a public administration has to carry a qualified signature "
				"(format {0}). Sign the XML and attach the .p7m, or transmit it through an "
				"intermediary: sending it unsigned comes back as rejection 00102."
			).format(FORMATO_PA)
		)

	url = doc.get("sdi_signed_file") or doc.xml_file
	nome = doc.sdi_filename or url.rsplit("/", 1)[-1]
	if firmato and not nome.endswith(".p7m"):
		nome = f"{nome}.p7m"

	contenuto = _contenuto(url)
	if len(contenuto) > DIMENSIONE_MASSIMA_MESSAGGIO_PEC:
		# The cap is on the message and not on the invoice, so it is measured here
		# rather than at generation: over it, delivery is simply not guaranteed.
		raise ErroreCanale(
			_("The message would be {0} MB, over the {1} MB the SdI accepts by PEC").format(
				len(contenuto) // (1024 * 1024), DIMENSIONE_MASSIMA_MESSAGGIO_PEC // (1024 * 1024)
			)
		)

	destinatario = indirizzo_sdi(emittente)
	frappe.sendmail(
		recipients=[destinatario],
		sender=mittente,
		subject=nome,
		# The body is not read by anything: the SdI looks at the attachment. It stays
		# empty of anything that describes the service.
		message=_("Invoice transmission to the Sistema di Interscambio."),
		attachments=[{"fname": nome, "fcontent": contenuto}],
		now=True,
		reference_doctype=doc.doctype,
		reference_name=doc.name,
	)
	return EsitoInvio(
		canale=CODICE,
		inviato=True,
		nome_file=nome,
		messaggio=_(
			"Sent to {0}. The delivery receipt names the address to use from the next invoice on."
		).format(destinatario),
		dettagli={"recipient": destinatario, "signed": firmato},
	)


def aggiorna_indirizzo(azienda: str, indirizzo: str) -> None:
	"""Record the address the SdI answered from.

	Only the first invoice goes to `sdi01@`. Keeping the initial address forever is
	how a practice ends up with invoices that leave and are never answered.
	"""
	pulito = (indirizzo or "").strip().lower()
	if not pulito or "@" not in pulito:
		return
	attuale = frappe.db.get_value("CRM Invoicing Company", azienda, "sdi_pec_address")
	if (attuale or "").strip().lower() == pulito:
		return
	frappe.db.set_value("CRM Invoicing Company", azienda, "sdi_pec_address", pulito)
