# Modifications copyright (c) 2026, NPM2 Solutions Srl

from urllib.parse import urlencode

import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.core.api.file import get_max_file_size
from frappe.rate_limiter import rate_limit
from frappe.translate import get_all_translations
from frappe.utils import cstr, sha256_hash, split_emails, validate_email_address


# nosemgrep: guest-whitelisted-method — the login page needs its strings before anyone is logged in
@frappe.whitelist(allow_guest=True)
def get_translations():
	if frappe.session.user != "Guest":
		language = frappe.db.get_value("User", frappe.session.user, "language")
	else:
		language = frappe.db.get_single_value("System Settings", "language")

	return get_all_translations(language)


@frappe.whitelist()
def get_user_signature():
	user = frappe.session.user
	user_email_signature = (
		frappe.db.get_value(
			"User",
			user,
			"email_signature",
		)
		if user
		else None
	)

	signature = user_email_signature or frappe.db.get_value(
		"Email Account",
		{"default_outgoing": 1, "add_signature": 1},
		"signature",
	)

	if not signature:
		return

	soup = BeautifulSoup(signature, "html.parser")
	html_signature = soup.find("div", {"class": "ql-editor read-mode"})
	_signature = None
	if html_signature:
		_signature = html_signature.renderContents()
	content = ""
	if cstr(_signature) or signature:
		content = f'<br><p class="signature">{signature}</p>'
	return content


def check_app_permission():
	if frappe.session.user == "Administrator":
		return True

	# FCRM is the app's module: whoever has it blocked has no way in. Asked of the
	# blocked modules, not of Frappe's list of every app's modules: that list is
	# cached per app, and a request that misses the cache while another fills it
	# gets None back (`frappe.utils.caching.redis_cache`), which made the whole
	# page a server error and the apps screen lose DottorCloud.
	if "FCRM" in _moduli_bloccati(frappe.session.user):
		return False

	# every role a module registered as a way in: the levels decide the rest
	from crm.permissions import livelli

	livelli.carica()
	return bool(livelli.ruoli_di_accesso() & set(frappe.get_roles()))


def dopo_l_accesso(login_manager=None) -> None:
	"""`on_session_creation`: whoever works in DottorCloud lands in it after signing
	in. The framework answers the sign-in with `get_home_page()`, the desk, and the
	desk is the apps' screen: one icon to tap, every time, «DottorC…» on a phone.
	That answer reads this request's `flags.home_page` first."""
	if frappe.session.user in ("Guest", None):
		return
	if frappe.get_cached_value("User", frappe.session.user, "user_type") != "System User":
		return
	if check_app_permission():
		frappe.local.flags.home_page = "/crm"


def _moduli_bloccati(user: str) -> list[str]:
	"""The modules closed to ``user``: their own and everybody's (Administrator's),
	as Frappe reads them."""
	return [
		*frappe.get_cached_doc("User", "Administrator").get_blocked_modules(),
		*frappe.get_cached_doc("User", user).get_blocked_modules(),
	]


# nosemgrep: guest-whitelisted-method — the invitation link itself: the key is the credential, 10/h
@frappe.whitelist(allow_guest=True)
@rate_limit(limit=10, seconds=60 * 60)
def accept_invitation(key: str | None = None):
	if not key:
		frappe.throw(_("Invalid or expired key"))

	# only the key's hash is stored
	result = frappe.db.get_all("CRM Invitation", filters={"key": sha256_hash(key)}, pluck="name")
	if not result:
		frappe.throw(_("Invalid or expired key"))
	invitation = frappe.get_doc("CRM Invitation", result[0])

	# The link shows someone got hold of the email, not that they own an account: whoever
	# already has one logs in as usual first, then comes back here to take the role.
	existing_user = frappe.db.exists("User", invitation.email)
	if existing_user and existing_user != frappe.session.user:
		if frappe.session.user != "Guest":
			frappe.throw(
				_("This invitation is for another account. Log out, then open the link again."),
				frappe.PermissionError,
			)
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = "/login?" + urlencode(
			{"redirect-to": f"/api/method/crm.api.accept_invitation?key={key}"}
		)
		return

	is_new_user = invitation.accept()
	invitation.reload()

	# this is a GET request, which is rolled back unless a commit is requested
	frappe.local.flags.commit = True

	if invitation.status == "Accepted":
		frappe.local.response["type"] = "redirect"
		if is_new_user:
			# a new user has no password yet, send them to the set password page
			# which logs them in and redirects to /crm once the password is set
			user = frappe.get_doc("User", invitation.email)
			frappe.local.response["location"] = user._reset_password()
		else:
			frappe.local.response["location"] = "/crm"


@frappe.whitelist(methods=["POST"])
def invite_by_email(emails: str, role: str | None = None, levels: str | list | None = None):
	"""Invite people by email, with the levels they will have.

	``role`` is the old way, kept for callers that still send one: System Manager
	stays the agency's, and a Sales Manager invites Sales Users only.
	"""
	from crm.permissions import livelli, utenti

	livelli.verifica("utenti.gestisci", messaggio=_("Only a manager can invite users"))

	chiavi = []
	if levels:
		from crm.api.user import _chiavi

		chiavi = utenti.verifica_livelli(_chiavi(levels))
	else:
		role = role or "Sales User"
		user_roles = frappe.get_roles(frappe.session.user)
		if role not in ["System Manager", "Sales Manager", "Sales User"]:
			frappe.throw(_("Cannot invite for this role"), frappe.PermissionError)
		if role == "System Manager" and "System Manager" not in user_roles:
			frappe.throw(_("You are not allowed to invite System Managers"), frappe.PermissionError)
		if role == "Sales Manager" and "System Manager" not in user_roles:
			frappe.throw(_("You are not allowed to invite Sales Managers"), frappe.PermissionError)

	if not emails:
		return

	email_string = validate_email_address(emails, throw=False)
	email_list = split_emails(email_string)
	if not email_list:
		return
	existing_members = frappe.db.get_all("User", filters={"email": ["in", email_list]}, pluck="email")
	existing_invites = frappe.db.get_all(
		"CRM Invitation",
		filters={
			"email": ["in", email_list],
			# an expired invitation must not stop a new one
			"status": "Pending",
		},
		pluck="email",
	)

	to_invite = list(set(email_list) - set(existing_members) - set(existing_invites))
	# the Professional plan is one person's (the listino, 07/10/2026)
	from crm.api.plan import verifica_utenti

	verifica_utenti(len(to_invite))

	for email in to_invite:
		invitation = {"doctype": "CRM Invitation", "email": email}
		if chiavi:
			invitation["levels"] = "\n".join(chiavi)
		else:
			invitation["role"] = role
		frappe.get_doc(invitation).insert(ignore_permissions=True)

	return {
		"existing_members": existing_members,
		"existing_invites": existing_invites,
		"to_invite": to_invite,
	}


@frappe.whitelist(methods=["DELETE", "POST"])
def delete_attachment(doctype: str, docname: str, file_url: str):
	if not frappe.has_permission(doctype, doc=docname, ptype="write"):
		frappe.throw(_("You don't have permission to delete this attachment"), frappe.PermissionError)

	file_name = frappe.db.get_value(
		"File",
		{"file_url": file_url, "attached_to_doctype": doctype, "attached_to_name": docname},
		"name",
	)
	if file_name:
		frappe.delete_doc("File", file_name)


@frappe.whitelist()
def get_file_uploader_defaults(doctype: str):
	max_number_of_files = None
	make_attachments_public = False
	if doctype:
		meta = frappe.get_meta(doctype)
		max_number_of_files = meta.get("max_attachments")
		make_attachments_public = meta.get("make_attachments_public")

	return {
		"allowed_file_types": frappe.get_system_settings("allowed_file_extensions"),
		"max_file_size": get_max_file_size(),
		"max_number_of_files": max_number_of_files,
		"make_attachments_public": bool(make_attachments_public),
	}
