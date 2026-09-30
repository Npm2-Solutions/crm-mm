import frappe
from frappe import _
from frappe.auth import LoginAttemptTracker
from frappe.rate_limiter import rate_limit
from frappe.utils.password import check_password, update_password

from crm.permissions import livelli, utenti
from crm.permissions.catalogo import MANAGER, SEGRETERIA


@frappe.whitelist()
@rate_limit(limit=5, seconds=300)  # 5 attempts per 5 minutes per user/IP
def change_password(old_password: str, new_password: str):
	"""
	Change password for the current logged-in user.
	Uses Frappe's LoginAttemptTracker for attempt counting/lockout, and rate_limit for API abuse protection.
	"""
	user = frappe.session.user
	if user == "Guest":
		frappe.throw(_("You must be logged in to change your password"), frappe.AuthenticationError)

	tracker = LoginAttemptTracker(user)
	if not tracker.is_user_allowed():
		frappe.throw(_("Too many failed attempts. Please try again after some time."))

	if old_password == new_password:
		frappe.throw(
			_("New password cannot be the same as current password. Please choose a different password.")
		)

	try:
		check_password(user, old_password)
	except frappe.AuthenticationError:
		tracker.add_failure_attempt()
		frappe.throw(_("Incorrect current password. Please try again."))
	else:
		tracker.add_success_attempt()

	# Validate new password strength (server-side enforcement)
	from frappe.core.doctype.user.user import test_password_strength

	result = test_password_strength(new_password)
	feedback = result.get("feedback", {})
	if not feedback.get("password_policy_validation_passed", False):
		suggestions = feedback.get("suggestions", [])
		frappe.throw(_("Password is too weak. {0}").format(" ".join(suggestions) if suggestions else ""))

	update_password(user=user, pwd=new_password, logout_all_sessions=False)
	return _("Password Updated Successfully")


def needs_password_setup() -> bool:
	"""Whether the session user has no password of their own and must set one.

	True for users provisioned without a password — the Frappe Cloud site owner,
	users created by a script — who are logged into a session they never
	authenticated for and so have no way back in once it expires.

	Users who sign in through SSO are excluded: having no password is the
	correct state for them, not something to fix.
	"""
	user = frappe.session.user

	# Checked first: it is the discriminating one, and it short-circuits the
	# other queries for everyone who already has a password — which is almost
	# everyone, on every CRM page load.
	if has_password(user):
		return False

	if frappe.get_system_settings("disable_user_pass_login"):
		return False

	# Every user carries a `frappe` provider row (Frappe issues one on insert
	# so the site can act as an identity provider), so only other providers
	# mean the user actually signs in through SSO.
	if frappe.db.exists(
		"User Social Login",
		{
			"parenttype": "User",
			"parent": user,
			"provider": ["!=", "frappe"],
			"userid": ["is", "set"],
		},
	):
		return False

	return True


def has_password(user: str) -> bool:
	"""Whether a password is stored for the user.

	User passwords are hashed rows in `__Auth` with `encrypted = 0`, so
	`get_decrypted_password` (which only looks at encrypted rows) cannot answer
	this — hence the direct query.
	"""
	Auth = frappe.qb.Table("__Auth")

	return bool(
		(
			frappe.qb.from_(Auth)
			.select(Auth.name)
			.where(
				(Auth.doctype == "User")
				& (Auth.name == user)
				& (Auth.fieldname == "password")
				& (Auth.encrypted == 0)
			)
			.limit(1)
		).run()
	)


@frappe.whitelist()
def get_levels() -> list[dict]:
	"""The levels a manager may give here, with the optional capabilities each offers."""
	livelli.verifica("utenti.gestisci", messaggio=_("Only a manager can change who does what"))
	registrate = livelli.capacita_registrate()
	return [
		{
			"key": livello.chiave,
			"label": livello.etichetta,
			"description": livello.descrizione,
			"base": livello.base,
			# Read only: added to another level, never alone
			"additive": livello.aggiuntivo,
			"optional": [
				{"name": nome, "description": registrate[nome].descrizione}
				for nome in livelli.a_scelta_dei_livelli([livello.chiave])
			],
		}
		for livello in utenti.livelli_offerti()
	]


@frappe.whitelist(methods=["POST"])
def set_user_levels(user: str, levels: str | list) -> None:
	"""Give ``user`` exactly these levels. A manager may give any of them, never the site."""
	utenti.verifica_gestione(user)
	chiavi = utenti.verifica_livelli(_chiavi(levels))

	agenzia = livelli.e_agenzia(frappe.session.user)
	if user == frappe.session.user and not agenzia and MANAGER not in chiavi:
		frappe.throw(
			_("You cannot take the Manager level away from yourself: ask another manager"),
			frappe.PermissionError,
		)
	if MANAGER not in chiavi:
		_verifica_gerarchia(user)
	utenti.assegna_livelli(user, chiavi)


@frappe.whitelist(methods=["POST"])
def set_user_capability(user: str, capability: str, enabled: bool | int | str) -> None:
	"""Turn one of ``user``'s optional capabilities on or off."""
	utenti.verifica_gestione(user)
	utenti.imposta_capacita(user, capability, frappe.utils.cint(enabled) == 1)


@frappe.whitelist(methods=["POST"])
def add_existing_users(users: str | list, role: str | None = None, levels: str | list | None = None):
	"""Bring existing users into the CRM with these levels.

	``role`` is the old way in, kept for callers that still send one.
	"""
	users = frappe.parse_json(users) if isinstance(users, str) else users
	for user in users:
		if levels:
			set_user_levels(user, levels)
		else:
			update_user_role(user, role or "Sales User")


def _chiavi(levels: str | list | None) -> list[str]:
	"""Level keys from a list, a JSON list, or a comma-separated string."""
	if isinstance(levels, str):
		try:
			levels = frappe.parse_json(levels)
		except ValueError:
			levels = levels.split(",")
	if isinstance(levels, str):
		levels = [levels]
	return [str(chiave).strip() for chiave in (levels or []) if str(chiave).strip()]


#: The old roles, as the levels that stand for them now.
LIVELLO_DEL_RUOLO = {"Sales Manager": MANAGER, "Sales User": SEGRETERIA}


@frappe.whitelist(methods=["POST"])
def update_user_role(user: str, new_role: str):
	"""The old way to change access, one role at a time; now it gives the level that
	stands for the role. System Manager stays the agency's to give.
	"""
	if new_role not in ["System Manager", "Sales Manager", "Sales User"]:
		frappe.throw(_("Cannot assign this role"))
	if new_role == "System Manager":
		_rendi_agenzia(user)
		return
	set_user_levels(user, [LIVELLO_DEL_RUOLO[new_role]])


def _rendi_agenzia(user: str) -> None:
	"""The agency's own users: System Manager and no centre level, which Frappe would
	take it away with at the next save."""
	if not livelli.e_agenzia(frappe.session.user):
		frappe.throw(_("Only System Managers can assign the System Manager role"), frappe.PermissionError)
	doc = frappe.get_doc("User", user)
	crm = utenti.profili_crm()
	if [riga for riga in doc.role_profiles if riga.role_profile not in crm]:
		# Frappe would rebuild the roles from those profiles and drop System Manager
		frappe.throw(_("{0} has other Role Profiles: make them System Manager from the Desk").format(user))
	doc.set("role_profiles", [])
	doc.role_profile_name = None
	doc.append_roles("System Manager", "Sales Manager", "Sales User")
	doc.set("block_modules", [])
	doc.save(ignore_permissions=True)
	livelli.dimentica_cache()


def _verifica_gerarchia(user: str) -> None:
	"""Someone who heads part of the sales hierarchy keeps a level that manages it."""
	node = frappe.db.get_value("CRM Sales Hierarchy", {"user": user}, ["name", "reports_to"], as_dict=True)
	if node:
		has_reports = frappe.db.exists("CRM Sales Hierarchy", {"reports_to": node.name})
		if has_reports or not node.reports_to:
			frappe.throw(_("Remove this user from the sales hierarchy before taking the Manager level away"))


@frappe.whitelist(methods=["POST"])
def remove_crm_roles_from_user(user: str):
	"""Take ``user`` out of the CRM: their levels, the roles they carry, their place in
	the hierarchy and their optional capabilities."""
	livelli.verifica("utenti.gestisci", messaggio=_("Only a manager can change who does what"))
	if user == frappe.session.user:
		frappe.throw(_("You cannot remove yourself."), frappe.PermissionError)
	if livelli.e_agenzia(user) and not livelli.e_agenzia(frappe.session.user):
		frappe.throw(_("Only System Managers can modify other System Managers"), frappe.PermissionError)

	if livelli.e_agenzia(user):
		# the agency's own user: their System Manager goes with the rest
		doc = frappe.get_doc("User", user)
		remove_roles(doc, "System Manager")
		doc.save(ignore_permissions=True)
	utenti.togli_dal_crm(user)
	frappe.msgprint(_("User {0} has been removed from DottorCloud roles.").format(user))


def remove_roles(self, *roles):
	existing_roles = {d.role: d for d in self.get("roles")}
	for role in roles:
		if role in existing_roles:
			self.get("roles").remove(existing_roles[role])
