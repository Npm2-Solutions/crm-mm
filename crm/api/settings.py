"""The centre's mailboxes, from DottorCloud's settings page (doc 30, doc 51).

Email Account is a core document Frappe gives to System Manager only, so the
Manager's page could list, add and change nothing. These calls ask for
`email.account_centro` instead, and only ever through the providers the page
offers (`FORNITORI`): their servers and ports are written here, never typed. A
mailbox with servers of its own is the agency's, from the Desk, and so is
DottorCloud's sending service (`crm.posta.servizio`): the page lists neither.

A mailbox here is where the centre reads and writes its email in DottorCloud. What
DottorCloud sends by itself leaves through the agency's service, so while that is
on, no mailbox of the centre is the default for sending.
"""

from contextlib import contextmanager

import frappe
from frappe import _

from crm.marchio import con_nome
from crm.permissions.livelli import richiede
from crm.posta import servizio

#: What the settings page shows of an account: never a password or a key.
CAMPI_ACCOUNT = (
	"name",
	"email_account_name",
	"email_id",
	"service",
	"email_server",
	"enable_incoming",
	"enable_outgoing",
	"default_incoming",
	"default_outgoing",
	"create_lead_from_incoming_email",
)

#: What the page changes. A password comes only when it is typed again.
MODIFICABILI = (
	"email_id",
	"enable_incoming",
	"enable_outgoing",
	"default_incoming",
	"default_outgoing",
	"create_lead_from_incoming_email",
)
SEGRETI = ("password",)

#: The mailboxes the page offers, with their servers: IMAP to read, SMTP to send.
#: `service` is the framework's own name where it has one. Gmail, iCloud and Yahoo
#: take an app password; Microsoft's mailboxes need a sign-in of Microsoft's.
FORNITORI = {
	"gmail": {
		"service": "GMail",
		"email_server": "imap.gmail.com",
		"incoming_port": 993,
		"use_ssl": 1,
		"smtp_server": "smtp.gmail.com",
		"smtp_port": 587,
		"use_tls": 1,
		"use_ssl_for_outgoing": 0,
	},
	"aruba": {
		"email_server": "imaps.aruba.it",
		"incoming_port": 993,
		"use_ssl": 1,
		"smtp_server": "smtps.aruba.it",
		"smtp_port": 465,
		"use_tls": 0,
		"use_ssl_for_outgoing": 1,
	},
	"libero": {
		"email_server": "imapmail.libero.it",
		"incoming_port": 993,
		"use_ssl": 1,
		"smtp_server": "smtp.libero.it",
		"smtp_port": 465,
		"use_tls": 0,
		"use_ssl_for_outgoing": 1,
	},
	"virgilio": {
		"email_server": "in.virgilio.it",
		"incoming_port": 993,
		"use_ssl": 1,
		"smtp_server": "out.virgilio.it",
		"smtp_port": 465,
		"use_tls": 0,
		"use_ssl_for_outgoing": 1,
	},
	"tiscali": {
		"email_server": "imap.tiscali.it",
		"incoming_port": 993,
		"use_ssl": 1,
		"smtp_server": "smtp.tiscali.it",
		"smtp_port": 465,
		"use_tls": 0,
		"use_ssl_for_outgoing": 1,
	},
	"icloud": {
		"email_server": "imap.mail.me.com",
		"incoming_port": 993,
		"use_ssl": 1,
		"smtp_server": "smtp.mail.me.com",
		"smtp_port": 587,
		"use_tls": 1,
		"use_ssl_for_outgoing": 0,
	},
	"yahoo": {
		"service": "Yahoo Mail",
		"email_server": "imap.mail.yahoo.com",
		"incoming_port": 993,
		"use_ssl": 1,
		"smtp_server": "smtp.mail.yahoo.com",
		"smtp_port": 465,
		"use_tls": 0,
		"use_ssl_for_outgoing": 1,
	},
}
#: The names the page used before for the same mailboxes.
VECCHI_NOMI = {"GMail": "gmail", "Yahoo": "yahoo", "Yahoo Mail": "yahoo"}


def fornitore_di(account) -> str | None:
	"""Which of the page's providers a mailbox is, by its server; None for one the
	agency set up by hand."""
	server = (account.get("email_server") or "").strip().lower()
	for chiave, valori in FORNITORI.items():
		if server and server == valori["email_server"]:
			return chiave
	return VECCHI_NOMI.get(account.get("service") or "") if not server else None


@frappe.whitelist()
@richiede("email.account_centro")
def get_email_accounts() -> list[dict]:
	"""The centre's mailboxes, for the settings page: not DottorCloud's sending
	service, which is the agency's."""
	righe = frappe.get_all(
		"Email Account",
		filters={"email_id": ["not like", "%example%"], "name": ["!=", servizio.ACCOUNT]},
		fields=list(CAMPI_ACCOUNT),
		order_by="creation asc",
	)
	for riga in righe:
		riga["provider"] = fornitore_di(riga)
		riga["editable"] = bool(riga["provider"])
	return righe


@frappe.whitelist()
def list_email_accounts(incoming: bool = False, outgoing: bool = False) -> list[dict]:
	"""Names and addresses to pick one from: one's own sending address in the
	profile, the inbox a booking platform writes to. Nothing more is in them."""
	from crm.api.session import get_session_role_flags

	get_session_role_flags()  # somebody who works in the CRM
	filters = {}
	if frappe.utils.sbool(incoming):
		filters["enable_incoming"] = 1
	if frappe.utils.sbool(outgoing):
		filters["enable_outgoing"] = 1
	filters["name"] = ["!=", servizio.ACCOUNT]
	return frappe.get_all(
		"Email Account", filters=filters, fields=["name", "email_id"], order_by="email_account_name asc"
	)


def _nuovo_segreto(valore) -> bool:
	"""Typed again, not the mask the page was given."""
	return bool(valore) and set(str(valore)) != {"*"}


def _parole_dell_errore(errore: Exception) -> str:
	"""What went wrong with a mailbox, in words: the password, or the server."""
	testo = str(errore).lower()
	if any(segno in testo for segno in ("password", "credential", "authentic", "login", "535", "534")):
		return _(
			"The address or the password is not right. Gmail, iCloud and Yahoo want an app password, "
			"made in the mailbox's own security settings."
		)
	if any(
		segno in testo for segno in ("timed out", "timeout", "connect", "resolve", "unreachable", "refused")
	):
		return _("The mailbox's server does not answer: try again in a few minutes.")
	return _("The mailbox could not be connected: {0}").format(str(errore))


@contextmanager
def _dove_archivia():
	"""Saving a mailbox that receives, the framework checks where it files its emails
	against the documents that take them, read with the reader's permissions: the
	customisations among them (Property Setter) are the agency's, and the manager
	reads none. The capability was asked, and the page files nowhere (DottorCloud
	finds the person, `crm.posta.ingresso`): for that save, the list is read whole."""
	from frappe.email.doctype.email_account import email_account as modulo

	originale = modulo.get_append_to

	def tutti(*_args, **_kwargs):
		tipi = set(
			frappe.get_all(
				"DocType", filters={"istable": 0, "issingle": 0, "email_append_to": 1}, pluck="name"
			)
		)
		tipi.update(
			frappe.get_all(
				"Property Setter", filters={"property": "email_append_to", "value": 1}, pluck="doc_type"
			)
		)
		return [[tipo] for tipo in tipi]

	modulo.get_append_to = tutti
	try:
		yield
	finally:
		modulo.get_append_to = originale


@frappe.whitelist(methods=["POST"])
@richiede("email.account_centro")
def update_email_account(name: str, data: dict) -> str:
	"""Change a mailbox the page added: its switches, its address, a new password.

	Renaming follows the change. Returns the mailbox's name.
	"""
	data = frappe.parse_json(data)
	if name == servizio.ACCOUNT:
		frappe.throw(con_nome(_("{brand}'s sending service is the agency's.")), frappe.PermissionError)
	doc = frappe.get_doc("Email Account", name)
	if not fornitore_di(doc):
		frappe.throw(_("This account has servers of its own: the agency changes it."), frappe.PermissionError)
	for campo in MODIFICABILI:
		if campo in data:
			doc.set(campo, data[campo])
	if servizio.attivo():
		# what DottorCloud sends leaves through the agency's service
		doc.default_outgoing = 0
	for campo in SEGRETI:
		if _nuovo_segreto(data.get(campo)):
			doc.set(campo, data[campo])
	doc.flags.ignore_permissions = True
	try:
		with _dove_archivia():
			doc.save()
	except frappe.PermissionError:
		raise
	except Exception as errore:
		frappe.throw(_parole_dell_errore(errore))

	nuovo_nome = (data.get("email_account_name") or "").strip()
	if nuovo_nome and nuovo_nome != doc.name:
		if nuovo_nome == servizio.ACCOUNT:
			frappe.throw(_("{0} is the name of the sending service: choose another.").format(nuovo_nome))
		from frappe.model.rename_doc import rename_doc

		# the capability was asked: Frappe's own check would ask for System Manager
		return rename_doc(
			doctype="Email Account", old=doc.name, new=nuovo_nome, ignore_permissions=True, show_alert=False
		)
	return doc.name


@frappe.whitelist(methods=["POST"])
@richiede("email.account_centro")
def create_email_account(data: dict) -> str:
	"""A mailbox of the centre, from one of the page's providers. Its connection is
	tried before it is kept: a wrong password is said in words, and nothing stays."""
	data = frappe.parse_json(data)
	fornitore = data.get("provider") or VECCHI_NOMI.get(data.get("service") or "")
	valori = FORNITORI.get(fornitore or "")
	if not valori:
		frappe.throw(_("This mailbox is set up by the agency."), frappe.PermissionError)
	nome = (data.get("email_account_name") or data.get("email_id") or "").strip()
	if nome == servizio.ACCOUNT:
		frappe.throw(_("{0} is the name of the sending service: choose another.").format(nome))
	riceve = 1 if data.get("enable_incoming", 1) else 0
	doc = frappe.get_doc(
		{
			"doctype": "Email Account",
			"email_id": (data.get("email_id") or "").strip(),
			"email_account_name": nome,
			"enable_incoming": riceve,
			"enable_outgoing": 1 if data.get("enable_outgoing", 1) else 0,
			"default_incoming": 1 if riceve and data.get("default_incoming") else 0,
			# what DottorCloud sends leaves through the agency's service while it is on
			"default_outgoing": 0 if servizio.attivo() else (1 if data.get("default_outgoing") else 0),
			"create_lead_from_incoming_email": 1
			if riceve and data.get("create_lead_from_incoming_email")
			else 0,
			"email_sync_option": "ALL",
			"initial_sync_count": 100,
			"create_contact": 1,
			"track_email_status": 1,
			"use_imap": 1,
			"password": data.get("password"),
			**{campo: valore for campo, valore in valori.items()},
		}
	)
	# the inbox is read; who wrote is found by DottorCloud (crm.posta.ingresso), not
	# made a new person for every email the way the framework would
	doc.append("imap_folder", {"folder_name": "INBOX"})
	doc.flags.ignore_permissions = True
	try:
		with _dove_archivia():
			doc.insert()
	except frappe.PermissionError:
		raise
	except Exception as errore:
		frappe.throw(_parole_dell_errore(errore))
	return doc.name
