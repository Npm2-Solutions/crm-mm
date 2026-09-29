"""The centre's email accounts, from the CRM's settings page (doc 30).

Email Account is a core document Frappe gives to System Manager only, so the
Manager's page could list, add and change nothing. These calls ask for
`email.account_centro` instead, and only ever through the providers the page
offers: their servers and ports come from `email_service_config`. An account with
servers and ports of its own is the agency's, from the Desk.
"""

import frappe
from frappe import _

from crm.permissions.livelli import richiede

#: What the settings page shows of an account: never a password or a key.
CAMPI_ACCOUNT = (
	"name",
	"email_account_name",
	"email_id",
	"service",
	"enable_incoming",
	"enable_outgoing",
	"default_incoming",
	"default_outgoing",
	"create_lead_from_incoming_email",
	"frappe_mail_site",
)

#: What the page changes. A password or a key comes only when it is typed again.
MODIFICABILI = (
	"email_id",
	"enable_incoming",
	"enable_outgoing",
	"default_incoming",
	"default_outgoing",
	"create_lead_from_incoming_email",
	"frappe_mail_site",
)
SEGRETI = ("password", "api_key", "api_secret")


@frappe.whitelist()
@richiede("email.account_centro")
def get_email_accounts() -> list[dict]:
	"""The centre's accounts, for the settings page."""
	return frappe.get_all(
		"Email Account",
		filters={"email_id": ["not like", "%example%"]},
		fields=list(CAMPI_ACCOUNT),
		order_by="creation asc",
	)


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
	return frappe.get_all(
		"Email Account", filters=filters, fields=["name", "email_id"], order_by="email_account_name asc"
	)


def _nuovo_segreto(valore) -> bool:
	"""Typed again, not the mask the page was given."""
	return bool(valore) and set(str(valore)) != {"*"}


@frappe.whitelist(methods=["POST"])
@richiede("email.account_centro")
def update_email_account(name: str, data: dict) -> str:
	"""Change an account the page added: its switches, its address, a new password.

	Renaming follows the change. Returns the account's name.
	"""
	data = frappe.parse_json(data)
	doc = frappe.get_doc("Email Account", name)
	if doc.service not in email_service_config:
		frappe.throw(_("This account has servers of its own: the agency changes it."), frappe.PermissionError)
	for campo in MODIFICABILI:
		if campo in data:
			doc.set(campo, data[campo])
	for campo in SEGRETI:
		if _nuovo_segreto(data.get(campo)):
			doc.set(campo, data[campo])
	doc.flags.ignore_permissions = True
	doc.save()

	nuovo_nome = (data.get("email_account_name") or "").strip()
	if nuovo_nome and nuovo_nome != doc.name:
		from frappe.model.rename_doc import rename_doc

		# the capability was asked: Frappe's own check would ask for System Manager
		return rename_doc(
			doctype="Email Account", old=doc.name, new=nuovo_nome, ignore_permissions=True, show_alert=False
		)
	return doc.name


@frappe.whitelist()
@richiede("email.account_centro")
def create_email_account(data: dict):
	service = data.get("service")
	service_config = email_service_config.get(service)
	if not service_config:
		return "Service not supported"

	try:
		email_doc = frappe.get_doc(
			{
				"doctype": "Email Account",
				"email_id": data.get("email_id"),
				"email_account_name": data.get("email_account_name"),
				"service": service,
				"enable_incoming": data.get("enable_incoming"),
				"enable_outgoing": data.get("enable_outgoing"),
				"default_incoming": data.get("default_incoming"),
				"default_outgoing": data.get("default_outgoing"),
				"email_sync_option": "ALL",
				"initial_sync_count": 100,
				"create_contact": 1,
				"track_email_status": 1,
				"use_tls": 1,
				"use_imap": 1,
				"smtp_port": 587,
				**service_config,
			}
		)
		if service == "Frappe Mail":
			email_doc.api_key = data.get("api_key")
			email_doc.api_secret = data.get("api_secret")
			email_doc.frappe_mail_site = data.get("frappe_mail_site")
			email_doc.append_to = "CRM Lead"
		else:
			email_doc.append("imap_folder", {"append_to": "CRM Lead", "folder_name": "INBOX"})
			email_doc.password = data.get("password")
			# validate whether the credentials are correct
			email_doc.get_incoming_server()

		# if correct credentials, save the email account: the capability was asked
		email_doc.flags.ignore_permissions = True
		email_doc.save()
	except Exception as e:
		frappe.throw(str(e))


email_service_config = {
	"Frappe Mail": {
		"domain": None,
		"password": None,
		"awaiting_password": 0,
		"ascii_encode_password": 0,
		"login_id_is_different": 0,
		"login_id": None,
		"use_imap": 0,
		"use_ssl": 0,
		"validate_ssl_certificate": 0,
		"use_starttls": 0,
		"email_server": None,
		"incoming_port": 0,
		"always_use_account_email_id_as_sender": 1,
		"use_tls": 0,
		"use_ssl_for_outgoing": 0,
		"smtp_server": None,
		"smtp_port": None,
		"no_smtp_authentication": 0,
	},
	"GMail": {
		"email_server": "imap.gmail.com",
		"use_ssl": 1,
		"smtp_server": "smtp.gmail.com",
	},
	"Outlook": {
		"email_server": "imap-mail.outlook.com",
		"use_ssl": 1,
		"smtp_server": "smtp-mail.outlook.com",
	},
	"Sendgrid": {
		"smtp_server": "smtp.sendgrid.net",
		"smtp_port": 587,
	},
	"SparkPost": {
		"smtp_server": "smtp.sparkpostmail.com",
	},
	"Yahoo": {
		"email_server": "imap.mail.yahoo.com",
		"use_ssl": 1,
		"smtp_server": "smtp.mail.yahoo.com",
		"smtp_port": 587,
	},
	"Yandex": {
		"email_server": "imap.yandex.com",
		"use_ssl": 1,
		"smtp_server": "smtp.yandex.com",
		"smtp_port": 587,
	},
}
