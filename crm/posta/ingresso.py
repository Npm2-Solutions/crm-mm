# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""An email that arrives reaches the person it is from.

The framework files a received email where its thread was: the record a reply
answers, else nothing. Here what follows, on every email received (Communication
`after_insert`):

- **somebody the centre knows** writes: the email goes on their page. A reply to a
  reminder, an offer of the waiting list, a subscription about to end was filed on
  the appointment, the entry, the subscription - nobody read it; now it is the
  person's conversation, and the document keeps a link to it. Only DottorCloud's
  own documents give their replies away: another app's thread (a ticket) stays
  where it is;
- **somebody new** writes to a mailbox that says so (`create_lead_from_incoming_email`):
  a person is made for them. Never for an automatic sender - "noreply", a mail
  server's bounce - nor for somebody of the centre, one of its mailboxes, or the
  mailbox a booking platform writes to (its sync finds the person);
- whoever follows the person is told, as for WhatsApp, and so are whose own mailbox
  it reached and who wrote the email it answers.

The person is found as everywhere else (`crm.api.lead.find_person`), by their email.
"""

from __future__ import annotations

import re

import frappe

from crm.posta import personale

PERSONA = "CRM Lead"
#: Where an email already belongs to somebody: their page or their deal's.
DELLE_PERSONE = ("CRM Lead", "CRM Deal")

#: Senders nobody answers: the part before the @ says so.
AUTOMATICI = re.compile(
	r"^(no[-_.]?reply|do[-_.]?not[-_.]?reply|mailer[-_.]?daemon|postmaster|bounces?|"
	r"notifications?|notifiche|newsletter|info[-_.]?noreply)([-_.+].*)?$",
	re.IGNORECASE,
)


def mittente_automatico(indirizzo: str | None) -> bool:
	"""Whether an address is a machine's, which nobody answers."""
	locale = (indirizzo or "").strip().partition("@")[0]
	return bool(locale) and bool(AUTOMATICI.match(locale))


def ricevuta(doc) -> bool:
	return (
		doc.doctype == "Communication"
		and doc.communication_type == "Communication"
		and doc.sent_or_received == "Received"
		and (doc.communication_medium or "Email") == "Email"
	)


def alla_ricezione(doc, method: str | None = None) -> None:
	"""The email to its person; a new person where the mailbox says so; whoever
	follows them told."""
	if not ricevuta(doc):
		return
	gia = doc.reference_doctype in DELLE_PERSONE and doc.reference_name
	if not gia:
		altrove = bool(doc.reference_doctype and doc.reference_name)
		if altrove and not di_dottorcloud(doc.reference_doctype):
			return
		persona = _trovata(doc) or _nuova(doc)
		if not persona:
			return
		if altrove:
			# a reply to a document of theirs: the document keeps it in its history
			doc.add_link(doc.reference_doctype, doc.reference_name)
		doc.reference_doctype = PERSONA
		doc.reference_name = persona
		doc.flags.ignore_permissions = True
		doc.save()
	avvisa(doc)


def di_dottorcloud(doctype: str) -> bool:
	"""Whether a document is one of DottorCloud's own, whose replies go to the person."""
	modulo = frappe.db.get_value("DocType", doctype, "module")
	return bool(modulo) and frappe.local.module_app.get(frappe.scrub(modulo)) == "crm"


def _trovata(doc) -> str | None:
	from crm.api.lead import find_person

	return find_person(email=doc.sender)


def _nuova(doc) -> str | None:
	"""A person for who writes the first time, where the mailbox makes them: never for
	a machine, never for a reply to something else."""
	if doc.reference_doctype or not doc.email_account or mittente_automatico(doc.sender):
		return None
	# somebody's own mailbox brings only people the centre knows (crm.posta.personale)
	if personale.di_chi(doc.email_account):
		return None
	if not frappe.db.get_value("Email Account", doc.email_account, "create_lead_from_incoming_email"):
		return None
	if del_centro(doc.sender) or frappe.db.exists(
		"CRM Booking Connection", {"inbound_email_account": doc.email_account}
	):
		return None
	lead = frappe.new_doc(PERSONA)
	lead.email = doc.sender
	nome, cognome = nome_e_cognome(doc.sender_full_name, doc.sender)
	lead.first_name = nome
	lead.last_name = cognome
	if frappe.db.exists("CRM Lead Source", "Email"):
		lead.source = "Email"
	lead.insert(ignore_permissions=True)
	return lead.name


def del_centro(indirizzo: str | None) -> bool:
	"""Somebody who works in DottorCloud, or one of the centre's mailboxes."""
	indirizzo = (indirizzo or "").strip()
	return bool(indirizzo) and bool(
		frappe.db.exists("User", {"email": indirizzo, "user_type": "System User"})
		or frappe.db.exists("Email Account", {"email_id": indirizzo})
	)


def nome_e_cognome(nome_completo: str | None, indirizzo: str | None) -> tuple[str, str]:
	"""First and last name from how the email signs: "Anna Maria Rossi" is Anna Maria
	and Rossi; without a name, the address's first part."""
	parole = (nome_completo or "").replace('"', "").split()
	if len(parole) > 1:
		return " ".join(parole[:-1]), parole[-1]
	if parole:
		return parole[0], ""
	return (indirizzo or "").partition("@")[0], ""


def destinatari(doc, seguono: list[str]) -> list[str]:
	"""Whoever follows the person; whose own mailbox it reached; who wrote the email it
	answers, when they work in DottorCloud."""
	from crm.permissions.livelli import nel_crm

	chi = list(seguono)
	proprietario = personale.di_chi(doc.email_account)
	if proprietario:
		chi.append(proprietario)
	if doc.in_reply_to:
		autore = frappe.db.get_value("Communication", doc.in_reply_to, "owner")
		if autore and nel_crm(autore):
			chi.append(autore)
	return list(dict.fromkeys(chi))


def avvisa(doc) -> None:
	"""Whoever follows the person reads it in their panel; the emails after it, while
	it is unread, add to it."""
	from crm.api.doc import assigned_users_of
	from crm.fcrm.doctype.crm_notification.crm_notification import nome_di
	from crm.notifiche import regole as R
	from crm.notifiche.avvisi import avvisa as scrivi

	if doc.reference_doctype not in DELLE_PERSONE or not doc.reference_name:
		return
	trattativa = doc.reference_doctype == "CRM Deal"
	nomi = [nome_di(doc.reference_doctype, doc.reference_name)]
	for user in destinatari(doc, assigned_users_of(doc.reference_doctype, doc.reference_name)):
		scrivi(
			user,
			"Email",
			R.EMAIL_TRATTATIVA if trattativa else R.EMAIL,
			nomi,
			frase_molti=R.EMAIL_TRATTATIVA_MOLTI if trattativa else R.EMAIL_MOLTI,
			riguarda=(doc.reference_doctype, doc.reference_name),
			oggetto=("Communication", doc.name),
			messaggio=doc.subject,
		)
