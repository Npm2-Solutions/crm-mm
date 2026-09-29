import frappe
from frappe import _

from crm.permissions import livelli


def crm_allowed_roles() -> list[str]:
	"""Every role that opens the CRM, from every module that registered one."""
	livelli.carica()
	return sorted(livelli.ruoli_di_accesso())


def get_session_role_flags():
	roles = set(frappe.get_roles())

	if not roles.intersection(crm_allowed_roles()):
		frappe.throw(_("You are not permitted to access CRM resources."), frappe.PermissionError)

	return {
		"is_system_manager": "System Manager" in roles,
		"is_sales_manager": "Sales Manager" in roles and "System Manager" not in roles,
		"is_sales_user": "Sales User" in roles
		and "Sales Manager" not in roles
		and "System Manager" not in roles,
	}


USER_FIELDS = [
	"name",
	"email",
	"enabled",
	"user_image",
	"first_name",
	"last_name",
	"full_name",
	"user_type",
	"language",
]


@frappe.whitelist()
def get_users(include_all: bool = False):
	"""Return (users, crm_users) for the CRM frontend.

	By default (`include_all=False`) the User query is filtered at SQL level
	to just users with CRM roles — typically a handful of rows. This unblocks
	the UI on initial load even on sites with hundreds of thousands of users.

	When `include_all=True` and the session has System Manager, the full
	enabled user list is returned. The frontend uses this path for a
	non-blocking background fetch that populates name/avatar info for
	non-CRM users referenced in CRM activity. Non-System-Manager sessions
	cannot escalate by passing this param.
	"""
	session_roles = get_session_role_flags()

	# Param arrives as a string from the HTTP layer; coerce.
	if isinstance(include_all, str):
		include_all = include_all.lower() in ("1", "true", "yes")
	if not session_roles["is_system_manager"]:
		include_all = False

	# Always need the CRM user name set — used both as the filter for the
	# fast path and as the membership check on the full path.
	allowed_roles = crm_allowed_roles()
	crm_user_names = set(
		frappe.get_all(
			"Has Role",
			filters={"parenttype": "User", "role": ["in", allowed_roles]},
			pluck="parent",
			distinct=True,
		)
	)
	crm_user_names.add("Administrator")

	user_filters = {"enabled": 1}
	if not include_all:
		user_filters["name"] = ["in", list(crm_user_names)]

	users = frappe.qb.get_query(
		"User",
		fields=USER_FIELDS,
		order_by="full_name asc",
		filters=user_filters,
	).run(as_dict=1)

	if not users:
		return [], []

	system_language = frappe.db.get_single_value("System Settings", "language")
	session_user = frappe.session.user

	# Has Role lookup — restrict by parent on the fast path (tiny IN list);
	# unfiltered scan on the full path because the IN list would otherwise
	# carry every enabled user name (see commit dropping IN-list filters).
	if include_all:
		role_filters = {"parenttype": "User"}
	else:
		role_filters = {"parenttype": "User", "parent": ["in", list(crm_user_names)]}
	role_rows = frappe.get_all("Has Role", filters=role_filters, fields=["parent", "role"])
	roles_by_user = {}
	for row in role_rows:
		roles_by_user.setdefault(row.parent, []).append(row.role)

	# Telephony agent table is tiny on any real site; full pluck is cheaper
	# than serializing an IN list and gives identical results.
	telephony_agents = set(frappe.get_all("CRM Telephony Agent", pluck="user"))

	# levels, by user, and the optional capabilities turned on: what the Users page
	# shows and changes
	levels_by_user = _levels_by_user(role_filters)
	optional_by_user = {}
	for row in frappe.get_all(
		"CRM User Capability",
		filters={"enabled": 1, **({"user": role_filters["parent"]} if "parent" in role_filters else {})},
		fields=["user", "capability"],
	):
		optional_by_user.setdefault(row.user, []).append(row.capability)

	role_priority = ("System Manager", "Sales Manager", "Sales User", "Guest")
	crm_users = []

	for user in users:
		if session_user == user.name:
			user.session_user = True

		# Administrator has every role implicitly via frappe.get_roles() but
		# its Has Role child table is not guaranteed to contain System Manager
		# on every install — special-case it to avoid locking the admin out.
		if user.name == "Administrator":
			user.roles = ["System Manager", "All"]
			user.role = "System Manager"
		else:
			# Mirror frappe.get_roles() which appends implicit "All" and "Guest"
			user.roles = [*roles_by_user.get(user.name, []), "All", "Guest"]
			user.role = ""
			for role in role_priority:
				if role in user.roles:
					user.role = role
					break

		user.is_telephony_agent = user.name in telephony_agents
		user.language = user.language or system_language
		# the agency's users hold no level: they manage the site
		user.agency = user.name == "Administrator" or "System Manager" in user.roles
		user.levels = levels_by_user.get(user.name) or (
			[] if user.agency else livelli.livelli_impliciti(user.roles)
		)
		user.levels_implied = not levels_by_user.get(user.name)
		user.optional = sorted(optional_by_user.get(user.name, []))

		if user.name == "Administrator" or set(user.roles).intersection(allowed_roles):
			crm_users.append(user)

	if not include_all:
		# Fast path — both positions are the CRM users.
		return crm_users, crm_users

	return users, crm_users


@frappe.whitelist()
def get_user_info(users: str | list):
	"""Resolve display info for a batch of User names.

	Used by the frontend to fill in name/avatar info for non-CRM users
	referenced in CRM activity (comment authors, doc owners, etc.) when
	the background full-list fetch has not yet landed. Gated behind a
	CRM role; capped at 200 names per call to limit enumeration cost.
	"""
	get_session_role_flags()

	if isinstance(users, str):
		users = frappe.parse_json(users)
	if not users:
		return []

	return frappe.get_all(
		"User",
		filters={"name": ["in", list(users)[:200]]},
		fields=["name", "email", "full_name", "user_image", "user_type"],
	)


@frappe.whitelist()
def get_organizations():
	get_session_role_flags()

	organizations = frappe.qb.get_query(
		"CRM Organization",
		fields=["*"],
		order_by="name asc",
		distinct=True,
	).run(as_dict=1)

	return organizations


def _levels_by_user(role_filters: dict) -> dict[str, list[str]]:
	"""user -> level keys, from the CRM's Role Profiles, in the registry's order."""
	per_profilo = {livello.profilo: livello.chiave for livello in livelli.livelli()}
	ordine = {livello.chiave: i for i, livello in enumerate(livelli.livelli())}
	filters = {"parenttype": "User", "role_profile": ["in", list(per_profilo) or [""]]}
	if "parent" in role_filters:
		filters["parent"] = role_filters["parent"]
	by_user: dict[str, list[str]] = {}
	for row in frappe.get_all("User Role Profile", filters=filters, fields=["parent", "role_profile"]):
		by_user.setdefault(row.parent, []).append(per_profilo[row.role_profile])
	for keys in by_user.values():
		keys.sort(key=lambda key: ordine.get(key, 99))
	return by_user


@frappe.whitelist()
def get_permissions() -> dict:
	"""What the session may do: its levels, every capability with its scope, and the plan.

	The frontend asks this rather than comparing role names: the answer is the one the
	server gives every endpoint, so a button never shows what the server refuses.
	"""
	get_session_role_flags()
	return session_permissions()


def session_permissions() -> dict:
	"""The session's levels, capabilities and plan; for callers that already checked it
	may open the CRM, like the page boot."""
	user = frappe.session.user
	return {
		"levels": livelli.livelli_di(user),
		"agency": livelli.e_agenzia(user),
		"capabilities": livelli.capacita_di(user),
		"modules": {
			modulo.chiave: livelli.stato_modulo(modulo.chiave, livelli.moduli_attivi())
			for modulo in livelli.moduli_piano()
		},
	}
