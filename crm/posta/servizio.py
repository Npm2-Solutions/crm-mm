# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""DottorCloud's own emails leave through the agency's sending service.

Reminders, codes, confirmations, offers, notifications: whatever DottorCloud writes
by itself goes out through one sending service the agency runs for every centre (a
relay such as Amazon SES or Brevo, its domain proven once with SPF, DKIM and
DMARC). The centre sets nothing up: the email comes from the centre - its name -
and the answers go to the centre's own address. Somebody writing from a person's
page without a mailbox of their own writes through it too, in their name and the
centre's, and the answer comes back to the centre (`intestazioni`).

The agency writes the service once, for every site of the server, in
`common_site_config.json` (or in one site's `site_config.json`):

    "dottorcloud_posta": {
        "server": "email-smtp.eu-central-1.amazonaws.com",
        "porta": 587,
        "utente": "...",
        "password": "...",
        "mittente": "notifiche@posta.dottorcloud.it"
    }

Each site keeps it as an email account of its own, "DottorCloud", the one emails
leave from when nothing else is asked (`default_outgoing`): `assicura()` makes it
and follows the configuration at every migrate and every hour. Without one the
account stops, and the centre's own account sends as before.
"""

from __future__ import annotations

import email.utils
from email.header import Header

import frappe
from frappe import _
from frappe.utils import cint, parse_addr, validate_email_address

from crm.permissions.livelli import puo, richiede
from crm.posta import personale

#: The configuration's key, and the account it becomes on each site.
CONF = "dottorcloud_posta"
ACCOUNT = "DottorCloud"
#: Where the centre wants the answers to DottorCloud's emails.
IMPOSTAZIONI = "FCRM Settings"
CAMPO_RISPOSTE = "reply_to_email"
#: The centre's mailbox emails left from before the service: it is again, if the
#: service goes.
PRECEDENTE = "crm_posta_casella_precedente"
SALVATAGGIO = "crm_posta_servizio"


def configurazione() -> dict | None:
	"""The service the agency wrote, checked; None where there is none, or it is
	missing what an email needs to leave."""
	conf = frappe.conf.get(CONF)
	if not isinstance(conf, dict):
		return None
	server = str(conf.get("server") or "").strip()
	mittente = str(conf.get("mittente") or "").strip()
	if not server or not mittente or not validate_email_address(mittente):
		return None
	porta = cint(conf.get("porta")) or 587
	utente = str(conf.get("utente") or "").strip()
	return {
		"server": server,
		"porta": porta,
		"utente": utente,
		"password": str(conf.get("password") or ""),
		"mittente": mittente,
		# 465 speaks TLS from the first byte, the others ask for it (STARTTLS)
		"ssl": porta == 465,
	}


def _valori(conf: dict) -> dict:
	diverso = bool(conf["utente"]) and conf["utente"] != conf["mittente"]
	return {
		"email_account_name": ACCOUNT,
		"email_id": conf["mittente"],
		"enable_outgoing": 1,
		"default_outgoing": 1,
		"enable_incoming": 0,
		"default_incoming": 0,
		"use_imap": 0,
		"auth_method": "Basic",
		"smtp_server": conf["server"],
		# a text field in the framework
		"smtp_port": str(conf["porta"]),
		"use_ssl_for_outgoing": 1 if conf["ssl"] else 0,
		"use_tls": 0 if conf["ssl"] else 1,
		"login_id_is_different": 1 if diverso else 0,
		"login_id": conf["utente"] if diverso else None,
		"no_smtp_authentication": 0 if conf["password"] else 1,
		# the address is always the service's, proven by its domain: the name says who
		"always_use_account_email_id_as_sender": 1,
		"always_use_account_name_as_sender_name": 0,
		"add_reply_to_header": 1,
		"track_email_status": 1,
		# a reminder or a code carries no "leave this conversation"
		"send_unsubscribe_message": 0,
	}


def _cambiato(doc, valori: dict, password: str) -> bool:
	if any(doc.get(campo) != valore for campo, valore in valori.items()):
		return True
	attuale = doc.get_password("password", raise_exception=False) if not doc.is_new() else None
	return (attuale or "") != password


def assicura() -> str | None:
	"""The site's account follows the agency's configuration. Saved only when
	something changed: saving tries the connection, and a service that does not
	answer is said once, never installed as the way every email leaves."""
	conf = configurazione()
	esiste = frappe.db.exists("Email Account", ACCOUNT)
	if not conf:
		if esiste:
			_ferma()
		return None
	doc = frappe.get_doc("Email Account", ACCOUNT) if esiste else frappe.new_doc("Email Account")
	valori = _valori(conf)
	if not _cambiato(doc, valori, conf["password"]):
		return doc.name
	if not doc.default_outgoing:
		precedente = frappe.db.get_value(
			"Email Account", {"default_outgoing": 1, "name": ["!=", ACCOUNT]}, "name"
		)
		if precedente:
			frappe.db.set_default(PRECEDENTE, precedente)
	doc.update(valori)
	if conf["password"]:
		doc.password = conf["password"]
	doc.flags.ignore_permissions = True
	# only this save is undone: at a migrate, what the other hooks wrote stays
	frappe.db.savepoint(SALVATAGGIO)
	try:
		doc.save()
	except Exception:
		frappe.db.rollback(save_point=SALVATAGGIO)
		frappe.log_error(title=_("{0}: the sending service did not answer").format(ACCOUNT))
		return None
	return doc.name


def _ferma() -> None:
	"""Without a configuration the account stops: the centre's mailbox emails left
	from before is the one again, else the first of its mailboxes that sends."""
	if not frappe.db.get_value("Email Account", ACCOUNT, "enable_outgoing"):
		return
	frappe.db.set_value("Email Account", ACCOUNT, {"enable_outgoing": 0, "default_outgoing": 0})
	if frappe.db.exists("Email Account", {"default_outgoing": 1, "enable_outgoing": 1}):
		return
	precedente = frappe.db.get_default(PRECEDENTE)
	if not (precedente and frappe.db.get_value("Email Account", precedente, "enable_outgoing")):
		precedente = frappe.db.get_value(
			"Email Account",
			{"enable_outgoing": 1, "name": ["!=", ACCOUNT], **personale.del_centro()},
			"name",
			order_by="creation asc",
		)
	if precedente:
		frappe.db.set_value("Email Account", precedente, "default_outgoing", 1)


def attivo() -> bool:
	"""Whether DottorCloud's emails leave through the service on this site."""
	return bool(frappe.db.get_value("Email Account", ACCOUNT, "enable_outgoing"))


def nome_del_centro() -> str:
	"""The name the centre's emails come from: the centre's, else the product's."""
	from crm.marchio import nome
	from crm.moduli.richieste import nome_del_centro as del_centro

	return del_centro() or nome()


def casella_principale() -> str | None:
	"""The mailbox where the centre reads its answers in DottorCloud: its main one,
	else the first that receives. None where it reads none."""
	for filtri in (
		{"enable_incoming": 1, "default_incoming": 1},
		{"enable_incoming": 1},
	):
		trovato = frappe.db.get_value(
			"Email Account",
			{**filtri, "name": ["!=", ACCOUNT], **personale.del_centro()},
			"email_id",
			order_by="creation asc",
		)
		if trovato:
			return trovato
	return None


def indirizzo_per_le_risposte() -> str | None:
	"""Where the answers to DottorCloud's emails go: the address the centre chose,
	else its main mailbox. None where the centre has neither: the answers would go
	nowhere."""
	scelto = (frappe.db.get_single_value(IMPOSTAZIONI, CAMPO_RISPOSTE) or "").strip()
	return scelto or casella_principale()


def _formatta(nome: str, indirizzo: str) -> str:
	return email.utils.formataddr((str(Header(nome, "utf-8")), indirizzo))


def mostrato(nome_mittente: str | None, centro: str) -> str:
	"""Whose name an email through the service shows: the centre's when DottorCloud
	writes by itself, "Anna Rossi · Centro Aurora" when a person of the centre does."""
	nome_mittente = (nome_mittente or "").strip()
	if not nome_mittente or nome_mittente == ACCOUNT or nome_mittente == centro:
		return centro
	if centro and centro.lower() not in nome_mittente.lower():
		return f"{nome_mittente} · {centro}"
	return nome_mittente


def _lavora_qui(indirizzo: str) -> bool:
	return bool(frappe.db.exists("User", {"email": indirizzo, "user_type": "System User", "enabled": 1}))


def intestazioni(mail) -> None:
	"""`make_email_body_message`: an email leaving through the service comes from the
	centre, on the service's address, and its answers go to the centre.

	The sender is set on the message and on the email itself: the queue takes the
	envelope from it, and the service accepts only its own address."""
	account = getattr(mail, "email_account", None)
	if not account or account.name != ACCOUNT:
		return
	centro = nome_del_centro()
	nome, _indirizzo = parse_addr(mail.sender)
	mail.sender = _formatta(mostrato(nome, centro), account.email_id)
	mail.set_header("From", mail.sender)

	# the answer to an email written here comes back here, to the centre, where
	# whoever follows the person reads it - also when somebody of the centre wrote it
	# without a mailbox of their own (the framework would send it to their address);
	# a Reply-To somebody chose stays
	_nome, risponde = parse_addr(mail.reply_to or "")
	if risponde and risponde != account.email_id and not _lavora_qui(risponde):
		return
	risposte = indirizzo_per_le_risposte()
	if risposte:
		mail.reply_to = _formatta(centro, risposte)
		mail.set_header("Reply-To", mail.reply_to)


# ---------------------------------------------------------------- the settings page


@frappe.whitelist()
@richiede("email.account_centro")
def get_sending_service() -> dict:
	"""How DottorCloud's emails leave this site, for the Email settings page."""
	conf = configurazione()
	fatto = {
		"active": attivo(),
		"configured": bool(conf),
		"sender": None,
		"reply_to": indirizzo_per_le_risposte(),
		"reply_to_chosen": frappe.db.get_single_value(IMPOSTAZIONI, CAMPO_RISPOSTE) or None,
		"reply_to_main": casella_principale(),
		# the mailboxes the page lists (`crm.api.settings.get_email_accounts`)
		"inboxes": frappe.get_all(
			"Email Account",
			filters={
				"enable_incoming": 1,
				"name": ["!=", ACCOUNT],
				"email_id": ["not like", "%example%"],
				**personale.del_centro(),
			},
			pluck="email_id",
			order_by="creation asc",
		),
		"agency": puo("tecnico.integrazioni"),
	}
	if fatto["active"]:
		indirizzo = frappe.db.get_value("Email Account", ACCOUNT, "email_id")
		fatto["sender"] = _formatta(nome_del_centro(), indirizzo)
	if fatto["agency"] and conf:
		fatto["server"] = f"{conf['server']}:{conf['porta']}"
	return fatto


@frappe.whitelist(methods=["POST"])
@richiede("email.account_centro")
def set_reply_address(address: str | None = None) -> dict:
	"""The address the answers to DottorCloud's emails go to; empty, the mailbox
	where the centre reads them in DottorCloud."""
	address = (address or "").strip()
	if address and not validate_email_address(address):
		frappe.throw(_("{0} is not an email address").format(address))
	frappe.db.set_single_value(IMPOSTAZIONI, CAMPO_RISPOSTE, address or None)
	return get_sending_service()


@frappe.whitelist(methods=["POST"])
@richiede("tecnico.integrazioni")
def sync_sending_service() -> dict:
	"""The agency, after writing the configuration: the site follows it now."""
	assicura()
	return get_sending_service()
