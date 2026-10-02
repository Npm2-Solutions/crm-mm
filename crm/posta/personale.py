# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Each person's own mailbox in DottorCloud (doc 51, second part).

Somebody of the centre connects the mailbox they work with - from the providers the
centre's page offers, with an app password, or signing in with Google or Microsoft
where the agency has registered DottorCloud there (a Connected App, found by where it
signs in) - and writes to people from a person's page with their own address. The
answers come back to that page.

From somebody's own mailbox DottorCloud keeps only what is the centre's: the answers
to what was written from DottorCloud, and what the people the centre knows write
(`da_tenere`, when the mailbox is read). The rest is that person's own post and is
never stored; nobody becomes a person from it.

Which of the centre's mailboxes somebody writes from is their choice too
(`set_my_senders`): the framework keeps that list where only the administrator
writes (`User.user_emails`, permlevel 1), so it is written here.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import validate_email_address

from crm.permissions.livelli import nel_crm, richiede

#: The field saying whose own mailbox an account is (`crm.install`).
CAMPO = "crm_owner"
#: Signing in with Google or Microsoft: how their Connected App is told apart, and
#: the servers of their mailboxes.
ACCESSI = {
	"google": {
		"segno": "accounts.google.com",
		"valori": {
			"service": "GMail",
			"email_server": "imap.gmail.com",
			"incoming_port": 993,
			"use_ssl": 1,
			"smtp_server": "smtp.gmail.com",
			"smtp_port": 587,
			"use_tls": 1,
			"use_ssl_for_outgoing": 0,
		},
	},
	"microsoft": {
		"segno": "login.microsoftonline.com",
		"valori": {
			"service": "Outlook.com",
			"email_server": "outlook.office365.com",
			"incoming_port": 993,
			"use_ssl": 1,
			"smtp_server": "smtp.office365.com",
			"smtp_port": 587,
			"use_tls": 1,
			"use_ssl_for_outgoing": 0,
		},
	},
}
#: Where Google or Microsoft send the person back: the page that tells the popup's
#: opener and closes (`crm/www/oauth_connected`), or opens this page.
RITORNO = "/oauth_connected?provider=posta"


def ha_il_campo() -> bool:
	return frappe.get_meta("Email Account").has_field(CAMPO)


def del_centro() -> dict:
	"""The filter for the centre's mailboxes: nobody's own."""
	return {CAMPO: ["is", "not set"]} if ha_il_campo() else {}


def propria(user: str | None = None) -> str | None:
	"""The name of somebody's own mailbox; None without one."""
	if not ha_il_campo():
		return None
	return frappe.db.get_value("Email Account", {CAMPO: user or frappe.session.user}, "name")


def di_chi(account: str | None) -> str | None:
	"""Whose own mailbox an account is; None for one of the centre's."""
	if not account or not ha_il_campo():
		return None
	return frappe.db.get_value("Email Account", account, CAMPO)


def app_di(accesso: str) -> str | None:
	"""The Connected App the agency registered for signing in with Google or Microsoft."""
	segno = ACCESSI[accesso]["segno"]
	for app in frappe.get_all(
		"Connected App", fields=["name", "authorization_uri", "openid_configuration"], order_by="creation asc"
	):
		if segno in (app.authorization_uri or "") or segno in (app.openid_configuration or ""):
			return app.name
	return None


def da_tenere(mail) -> bool:
	"""Whether an email that reached somebody's own mailbox is the centre's: an answer
	to what was written from DottorCloud, or from a person the centre knows."""
	from crm.api.lead import find_person

	try:
		if mail.parent_communication():
			return True
	except Exception:
		# a reply the framework cannot place is judged by who wrote it
		pass
	return bool(find_person(email=getattr(mail, "from_email", None)))


# ---------------------------------------------------------------- the page


def _accesso_di(doc) -> str | None:
	if doc.get("auth_method") != "OAuth" or not doc.get("connected_app"):
		return None
	for accesso in ACCESSI:
		if app_di(accesso) == doc.connected_app:
			return accesso
	return None


def _ha_il_token(doc) -> bool:
	if not (doc.get("connected_app") and doc.get("connected_user")):
		return False
	from frappe.integrations.doctype.connected_app.connected_app import has_token

	return has_token(doc.connected_app, doc.connected_user)


def _del_centro_da_cui_si_scrive() -> list[dict]:
	"""The centre's mailboxes one may write from: they send, they are nobody's own,
	and they are not DottorCloud's sending service."""
	from crm.posta import servizio

	return frappe.get_all(
		"Email Account",
		# as the centre's page lists them (`crm.api.settings.get_email_accounts`)
		filters={
			"enable_outgoing": 1,
			"name": ["!=", servizio.ACCOUNT],
			"email_id": ["not like", "%example%"],
			**del_centro(),
		},
		fields=["name", "email_id"],
		order_by="email_account_name asc",
	)


@frappe.whitelist()
@richiede("conversazioni.usa")
def get_my_email() -> dict:
	"""Settings > Your account > Your email: one's own mailbox, the centre's mailboxes
	one writes from, whether Google or Microsoft sign in here."""
	from crm.api import settings

	user = frappe.session.user
	casella = None
	nome = propria(user)
	if nome:
		doc = frappe.get_doc("Email Account", nome)
		accesso = _accesso_di(doc)
		casella = {
			"name": doc.name,
			"email_id": doc.email_id,
			"provider": accesso or settings.fornitore_di(doc),
			"signed_in_with": accesso,
			"connected": bool(doc.enable_outgoing or doc.enable_incoming),
			"waiting": bool(accesso) and not _ha_il_token(doc),
		}
	propri = {nome} if nome else set()
	return {
		"mailbox": casella,
		"sign_in": {accesso: bool(app_di(accesso)) for accesso in ACCESSI},
		"centre": _del_centro_da_cui_si_scrive(),
		"senders": [
			riga.email_account
			for riga in frappe.get_all(
				"User Email",
				filters={"parent": user, "parenttype": "User"},
				fields=["email_account"],
				order_by="idx asc",
			)
			if riga.email_account not in propri
		],
		"login_email": frappe.db.get_value("User", user, "email"),
	}


@frappe.whitelist()
def get_my_senders() -> list[dict]:
	"""What the composer offers to write from: one's own mailbox first, then the
	centre's one chose. Empty: one writes through {brand}'s service, in one's name and
	the centre's, and the answers come back to the centre."""
	user = frappe.session.user
	if not nel_crm(user):
		return []
	righe = frappe.get_all(
		"User Email",
		filters={"parent": user, "parenttype": "User"},
		fields=["email_account", "email_id"],
		order_by="idx asc",
	)
	attive = set(
		frappe.get_all(
			"Email Account",
			filters={"name": ["in", [r.email_account for r in righe] or [""]], "enable_outgoing": 1},
			pluck="name",
		)
	)
	propria_nome = propria(user)
	scelte = [
		{"email_account": r.email_account, "email_id": r.email_id} for r in righe if r.email_account in attive
	]
	scelte.sort(key=lambda r: r["email_account"] != propria_nome)
	return scelte


def _righe(user: str, conti: list[str]) -> None:
	"""The mailboxes somebody writes from, in order: written here, the framework would
	ask for the administrator (`user_emails` is on permlevel 1)."""
	doc = frappe.get_doc("User", user)
	indirizzi = dict(
		frappe.get_all(
			"Email Account",
			filters={"name": ["in", conti or [""]]},
			fields=["name", "email_id"],
			as_list=True,
		)
	)
	doc.set(
		"user_emails",
		[{"email_account": conto, "email_id": indirizzi.get(conto)} for conto in conti if conto in indirizzi],
	)
	doc.flags.ignore_permissions = True
	doc.save()


def _scelte(user: str) -> list[str]:
	return frappe.get_all(
		"User Email",
		filters={"parent": user, "parenttype": "User"},
		pluck="email_account",
		order_by="idx asc",
	)


@frappe.whitelist(methods=["POST"])
@richiede("conversazioni.usa")
def set_my_senders(accounts: list | str | None = None) -> dict:
	"""The centre's mailboxes one writes from; one's own stays first."""
	scelti = frappe.parse_json(accounts) if isinstance(accounts, str) else (accounts or [])
	ammessi = {conto.name for conto in _del_centro_da_cui_si_scrive()}
	user = frappe.session.user
	propria_nome = propria(user)
	conti = ([propria_nome] if propria_nome else []) + [c for c in scelti if c in ammessi]
	_righe(user, list(dict.fromkeys(conti)))
	return get_my_email()


def _nome_libero(indirizzo: str, attuale: str | None) -> None:
	altro = frappe.db.get_value("Email Account", {"email_id": indirizzo}, "name")
	if altro and altro != attuale:
		frappe.throw(
			_("{0} is a mailbox of the centre already: choose it among the ones you write from.").format(
				indirizzo
			)
		)


def _propria_per(user: str, indirizzo: str):
	"""One's own mailbox, made the first time, named after its address."""
	nome = propria(user)
	_nome_libero(indirizzo, nome)
	if nome and nome != indirizzo:
		from frappe.model.rename_doc import rename_doc

		nome = rename_doc(
			doctype="Email Account", old=nome, new=indirizzo, ignore_permissions=True, show_alert=False
		)
	doc = frappe.get_doc("Email Account", nome) if nome else frappe.new_doc("Email Account")
	doc.update(
		{
			"email_account_name": indirizzo,
			"email_id": indirizzo,
			CAMPO: user,
			"default_incoming": 0,
			"default_outgoing": 0,
			# nobody becomes a person from somebody's own mailbox, nor an address-book entry
			"create_lead_from_incoming_email": 0,
			"create_contact": 0,
			"use_imap": 1,
			"email_sync_option": "ALL",
			"initial_sync_count": "100",
			"track_email_status": 1,
		}
	)
	if not doc.imap_folder:
		doc.append("imap_folder", {"folder_name": "INBOX"})
	return doc


def _salva(doc) -> None:
	from crm.api import settings

	doc.flags.ignore_permissions = True
	try:
		with settings._dove_archivia():
			doc.save()
	except frappe.ValidationError:
		raise
	except Exception as errore:
		frappe.throw(settings._parole_dell_errore(errore))


def _indirizzo(data: dict) -> str:
	indirizzo = (data.get("email_id") or "").strip().lower()
	if not indirizzo or not validate_email_address(indirizzo):
		frappe.throw(_("{0} is not an email address").format(indirizzo or "—"))
	return indirizzo


def _collega(user: str, nome: str) -> None:
	_righe(user, [nome, *[c for c in _scelte(user) if c != nome]])


@frappe.whitelist(methods=["POST"])
@richiede("conversazioni.usa")
def connect_my_mailbox(data: dict | str) -> dict:
	"""One's own mailbox from one of the page's providers, with its password (an app
	password where the provider wants one). Its connection is tried before it is kept."""
	from crm.api import settings

	data = frappe.parse_json(data)
	valori = settings.FORNITORI.get(data.get("provider") or "")
	if not valori:
		frappe.throw(_("Choose where the mailbox is."))
	user = frappe.session.user
	indirizzo = _indirizzo(data)
	gia = propria(user)
	password = data.get("password") or ""
	if not password and not (
		gia and settings.fornitore_di(frappe.get_doc("Email Account", gia)) == data.get("provider")
	):
		frappe.throw(_("Write the password."))
	doc = _propria_per(user, indirizzo)
	doc.update(
		{
			**{campo: valore for campo, valore in valori.items()},
			"auth_method": "Basic",
			"connected_app": None,
			"connected_user": None,
			"enable_incoming": 1,
			"enable_outgoing": 1,
			"awaiting_password": 0,
		}
	)
	if "service" not in valori:
		doc.service = None
	if password:
		doc.password = password
	_salva(doc)
	_collega(user, doc.name)
	return get_my_email()


@frappe.whitelist(methods=["POST"])
@richiede("conversazioni.usa")
def start_sign_in(provider: str, email_id: str) -> str:
	"""The address of Google's or Microsoft's own page, where the person lets
	DottorCloud use their mailbox; they come back to this page after."""
	if provider not in ACCESSI:
		frappe.throw(_("Choose where the mailbox is."))
	app = app_di(provider)
	if not app:
		frappe.throw(_("Signing in with this provider is not set up yet: the agency sets it up."))
	user = frappe.session.user
	doc = _propria_per(user, _indirizzo({"email_id": email_id}))
	doc.update(
		{
			**ACCESSI[provider]["valori"],
			"auth_method": "OAuth",
			"connected_app": app,
			"connected_user": user,
			# until the sign-in comes back, it neither reads nor writes
			"enable_incoming": 0,
			"enable_outgoing": 0,
		}
	)
	doc.password = None
	_salva(doc)
	# signing in, the password it had before is not kept
	from frappe.utils.password import remove_encrypted_password

	remove_encrypted_password("Email Account", doc.name, "password")
	return frappe.get_doc("Connected App", app).initiate_web_application_flow(user=user, success_uri=RITORNO)


@frappe.whitelist(methods=["POST"])
@richiede("conversazioni.usa")
def finish_sign_in() -> dict:
	"""Back from Google or Microsoft: with the access given, the mailbox starts
	reading and writing."""
	user = frappe.session.user
	nome = propria(user)
	if nome:
		doc = frappe.get_doc("Email Account", nome)
		if doc.auth_method == "OAuth" and _ha_il_token(doc) and not doc.enable_outgoing:
			doc.enable_incoming = 1
			doc.enable_outgoing = 1
			_salva(doc)
			_collega(user, doc.name)
	return get_my_email()


@frappe.whitelist(methods=["POST"])
@richiede("conversazioni.usa")
def disconnect_my_mailbox() -> dict:
	"""One's own mailbox stops reading and writing, and its password or access goes.
	What it brought stays on the people's pages."""
	from frappe.utils.password import remove_encrypted_password

	user = frappe.session.user
	nome = propria(user)
	if nome:
		app = frappe.db.get_value("Email Account", nome, "connected_app")
		frappe.db.set_value(
			"Email Account", nome, {"enable_incoming": 0, "enable_outgoing": 0, "awaiting_password": 0}
		)
		remove_encrypted_password("Email Account", nome, "password")
		if app and frappe.db.exists("Token Cache", f"{app}-{user}"):
			frappe.delete_doc("Token Cache", f"{app}-{user}", ignore_permissions=True, force=True)
		_righe(user, [c for c in _scelte(user) if c != nome])
	return get_my_email()
