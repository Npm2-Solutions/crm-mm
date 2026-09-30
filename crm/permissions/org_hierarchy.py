# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# Modifications copyright (c) 2026, NPM2 Solutions Srl
# For license information, please see license.txt

"""Which people and deals a user sees, and what follows them.

**The scope comes from the level** (doc 30, "L'ambito: su quali record"): the
capability that shows people (`persone.vedi`) or deals (`trattative.vedi`) says on
which records. The whole centre - front desk, manager, medical director; the team in
the sales hierarchy - sales; their own - the practitioner, who also sees the people
they look after: an appointment with them, their patients. A place in the hierarchy
narrows it: whoever sits in the tree sees their team, as a Sales Manager there did.
Somebody working from the Desk with roles only, outside the levels, keeps the rule of
before: their records, their subtree, everything for a Sales Manager outside the tree.

**What belongs to a person follows the person**: calls, notes and tasks here; the
agenda, the messages and the tracking in `crm.permissions.seguono`. One condition
for the list and for the record, so the two never disagree.
"""

import frappe
from frappe import _
from frappe.query_builder.functions import IfNull
from frappe.utils import add_days, now_datetime
from frappe.utils.caching import request_cache

from crm.permissions import livelli

_OWNER_FIELD = {
	"CRM Lead": "lead_owner",
	"CRM Deal": "deal_owner",
}

#: The capability whose scope says how far a user sees each kind of record.
_CAPACITA = {
	"CRM Lead": "persone.vedi",
	"CRM Deal": "trattative.vedi",
}

#: A user who may not see a kind of record at all: not even their own.
NIENTE = "niente"

#: How long a closed assignment still opens the record: the work is done, the
#: follow-up is not; for ever would be a key nobody remembers giving.
GIORNI_ASSEGNAZIONE_CHIUSA = 90


def hierarchy_enabled() -> bool:
	return bool(frappe.db.get_single_value("FCRM Settings", "enable_sales_hierarchy"))


def _scope(user: str, doctype: str = "CRM Lead"):
	"""How far ``user`` sees ``doctype``: ``None`` everything, ``NIENTE`` nothing,
	otherwise whether they see their subtree (``True``) or only their own (``False``).

	Worked out once per request: one list asks it for every subquery it builds.
	`livelli.dimentica_cache` forgets it with the rest.
	"""
	cache = getattr(frappe.local, "crm_ambiti", None)
	if cache is None:
		cache = frappe.local.crm_ambiti = {}
	if (user, doctype) not in cache:
		cache[(user, doctype)] = _work_out_scope(user, doctype)
	return cache[(user, doctype)]


def _work_out_scope(user: str, doctype: str):
	if user == "Administrator":
		return None

	roles = frappe.get_roles(user)
	if "System Manager" in roles:
		return None

	if livelli.nel_crm(user):
		ambito = livelli.ambito(_CAPACITA[doctype], user)
		if ambito not in (livelli.CENTRO, livelli.MASCHERATO, livelli.TEAM, livelli.SUOI):
			return NIENTE
		# a place in the sales hierarchy narrows whatever the level says: whoever
		# sits in the tree sees their team - the team lead, as a Sales Manager did
		if hierarchy_enabled() and _in_hierarchy(user):
			return True
		return None if ambito in (livelli.CENTRO, livelli.MASCHERATO) else False

	in_tree = hierarchy_enabled() and _in_hierarchy(user)

	# Sales Manager outside the tree retains the default ie sees everything
	if "Sales Manager" in roles and not in_tree:
		return None

	return in_tree


def _in_care_of(user: str, doctype: str) -> bool:
	"""Whether ``user`` also sees the people they look after: a practitioner does."""
	return (
		doctype == "CRM Lead"
		and livelli.nel_crm(user)
		and livelli.ambito(_CAPACITA[doctype], user) == livelli.SUOI
	)


def _in_care(user: str, DT):
	"""The people ``user`` looks after: an appointment with them, and whatever a module
	adds (`crm_people_in_care`: the clinic's patients of theirs)."""
	Part = frappe.qb.DocType("CRM Appointment Participant").as_("_care_part")
	Staff = frappe.qb.DocType("CRM Appointment Staff").as_("_care_staff")
	condition = DT.name.isin(
		frappe.qb.from_(Part)
		.join(Staff)
		.on(Staff.parent == Part.parent)
		.select(Part.party)
		.where(
			(Part.parenttype == "CRM Appointment")
			& (Part.party_type == "CRM Lead")
			& (Staff.parenttype == "CRM Appointment")
			& (Staff.user == user)
		)
	)
	for method in frappe.get_hooks("crm_people_in_care"):
		extra = frappe.get_attr(method)(user)
		if extra is not None:
			condition = condition | DT.name.isin(extra)
	return condition


def _theirs(field, user: str, in_tree: bool):
	"""The field names the user themselves or, in the tree, any member of their subtree."""
	if in_tree:
		return (field == user) | field.isin(_team_mem_query(user))
	return field == user


def _assigned(doctype: str, DT, user: str, in_tree: bool):
	"""The record is assigned by ToDo to the user or, in the tree, any member of their
	subtree: an open assignment, or one closed in the last few weeks."""
	Todo = frappe.qb.DocType("ToDo").as_("_todo")
	chiusa_da_poco = (Todo.status == "Closed") & (
		Todo.modified >= add_days(now_datetime(), -GIORNI_ASSEGNAZIONE_CHIUSA)
	)
	return DT.name.isin(
		frappe.qb.from_(Todo)
		.select(Todo.reference_name)
		.where(
			(Todo.reference_type == doctype)
			& ((Todo.status == "Open") | chiusa_da_poco)
			& _theirs(Todo.allocated_to, user, in_tree)
		)
	)


def _nothing(DT):
	return DT.name.isnull()


def _permission_query_conditions(user: str | None, doctype: str):
	user = user or frappe.session.user
	in_tree = _scope(user, doctype)
	if in_tree is None:
		return ""

	DT = frappe.qb.DocType(doctype)
	if in_tree == NIENTE:
		return _nothing(DT)

	# their own records and the ones assigned to them; in the tree, their subtree's
	# as well; a practitioner, the people they look after
	condition = _theirs(DT[_OWNER_FIELD[doctype]], user, in_tree) | _assigned(doctype, DT, user, in_tree)
	if _in_care_of(user, doctype):
		condition = condition | _in_care(user, DT)
	return condition


def _as_sql(condition) -> str:
	return (
		condition.get_sql(with_namespace=True, quote_char="`", secondary_quote_char="'") if condition else ""
	)


def get_lead_permission_query_conditions(user=None):
	return _as_sql(_permission_query_conditions(user, "CRM Lead"))


def get_deal_permission_query_conditions(user=None):
	return _as_sql(_permission_query_conditions(user, "CRM Deal"))


def _has_permission(doc, ptype, user, doctype: str, conditions=_permission_query_conditions) -> bool:
	if ptype == "create" or not doc.name:
		return True

	# the same rule as the lists, asked of the one row: the two can never disagree
	condition = conditions(user or frappe.session.user, doctype)
	if not condition:
		return True

	DT = frappe.qb.DocType(doctype)
	return bool(
		frappe.qb.from_(DT).select(DT.name).where(DT.name == doc.name).where(condition).limit(1).run()
	)


#: Writing a person or a deal asks for its capability (doc 30, PR 4): seeing one is
#: not enough, and every level carries Sales User, which may write them. The scope
#: of each is within the scope that shows the record, so seeing is the rest.
#: Emailing from one asks for conversing: sending is not writing the person.
_SCRITTURE = {
	"CRM Lead": {
		"create": "persone.scrivi",
		"write": "persone.scrivi",
		"delete": "persone.elimina",
		"email": "conversazioni.usa",
	},
	"CRM Deal": {
		"create": "trattative.scrivi",
		"write": "trattative.scrivi",
		"delete": "trattative.scrivi",
		"email": "conversazioni.usa",
	},
	"FCRM Note": {"create": "note.scrivi", "write": "note.scrivi", "delete": "note.scrivi"},
}


def _puo_scrivere(doctype: str, ptype: str | None, user: str | None) -> bool:
	capacita = _SCRITTURE[doctype].get(ptype or "read")
	if not capacita:
		return True
	user = user or frappe.session.user
	return not livelli.nel_crm(user) or livelli.puo(capacita, user)


def scrittura_per_capacita(doc, method=None):
	"""`validate` of people, deals and notes: a save on the user's behalf asks for the
	capability even on a record shared with them.

	Frappe grants what is shared without asking the `has_permission` hooks, and the
	CRM shares every person and deal with its owner, for writing: an owner whose
	level does not change deals would change them anyway. What the server saves for
	itself (`ignore_permissions`) is not asked, as it is not asked anything else.
	"""
	if doc.flags.ignore_permissions:
		return
	if not _puo_scrivere(doc.doctype, "create" if doc.is_new() else "write", None):
		frappe.throw(_("Your level does not change this"), frappe.PermissionError)


def has_lead_permission(doc, ptype, user):
	return _puo_scrivere("CRM Lead", ptype, user) and _has_permission(doc, ptype, user, "CRM Lead")


def has_deal_permission(doc, ptype, user):
	return _puo_scrivere("CRM Deal", ptype, user) and _has_permission(doc, ptype, user, "CRM Deal")


# --------------------------------------------------------------------------
# calls, notes and tasks follow the lead or deal they are about
# --------------------------------------------------------------------------

_ABOUT = ("CRM Lead", "CRM Deal")

# aliased, so the subqueries never collide with a table the list itself joins
_ALIAS = {"CRM Lead": "_lead", "CRM Deal": "_deal"}


def _visible(doctype: str, user: str):
	"""The leads (or deals) the user sees, as a subquery - all of them when they see
	them all.

	Shared ones included: a share opens a lead whatever the hierarchy says, both in
	the list and on its page, and its calls, notes and tasks come along with it.
	"""
	DT = frappe.qb.DocType(doctype).as_(_ALIAS[doctype])
	in_tree = _scope(user, doctype)
	if in_tree is None:
		return frappe.qb.from_(DT).select(DT.name)
	if in_tree == NIENTE:
		return frappe.qb.from_(DT).select(DT.name).where(_nothing(DT))
	Share = frappe.qb.DocType("DocShare").as_("_share")
	shared = (
		frappe.qb.from_(Share)
		.select(Share.share_name)
		.where(
			(Share.share_doctype == doctype)
			& (Share.read == 1)
			& ((Share.user == user) | (Share.everyone == 1))
		)
	)
	condition = (
		_theirs(DT[_OWNER_FIELD[doctype]], user, in_tree)
		| _assigned(doctype, DT, user, in_tree)
		| DT.name.isin(shared)
	)
	if _in_care_of(user, doctype):
		condition = condition | _in_care(user, DT)
	return frappe.qb.from_(DT).select(DT.name).where(condition)


def visible_leads(user: str | None = None):
	"""The leads ``user`` sees, as a subquery, or ``None`` when they see them all.

	For what belongs to a person and follows them - their billing details, say:
	the same rule as the list of people, shares included, so the two never disagree.
	"""
	user = user or frappe.session.user
	if _scope(user, "CRM Lead") is None:
		return None
	return _visible("CRM Lead", user)


def sees_everyone(user: str | None = None) -> bool:
	"""Whether ``user`` sees every lead and every deal: nothing to filter."""
	user = user or frappe.session.user
	return _scope(user, "CRM Lead") is None and _scope(user, "CRM Deal") is None


def _about(doctype: str, doctype_field, name_field, user: str):
	in_tree = _scope(user, doctype)
	if in_tree is None:
		return doctype_field == doctype
	return (doctype_field == doctype) & name_field.isin(_visible(doctype, user))


def _about_visible(doctype_field, name_field, user: str):
	"""The record points at a lead or a deal the user sees."""
	return _about("CRM Lead", doctype_field, name_field, user) | _about(
		"CRM Deal", doctype_field, name_field, user
	)


def _about_someone(doctype_field, name_field):
	"""The record points at a lead or a deal at all. Never NULL, so it can be negated."""
	return IfNull(doctype_field, "").isin(_ABOUT) & (IfNull(name_field, "") != "")


def _call_visible(Call, user: str, in_tree: bool):
	"""A call is theirs if they made it, took it or logged it. Otherwise it follows the
	leads and deals it is linked to — telephony files them under `links`, a call logged
	by hand under `reference_*` — and any one of them is enough, since the call sits on
	each one's timeline. A call linked to nobody is everyone's, as it always was."""
	Link = frappe.qb.DocType("Dynamic Link").as_("_call_link")
	linked = frappe.qb.from_(Link).select(Link.parent).where(Link.parenttype == "CRM Call Log")
	return (
		_theirs(Call.caller, user, in_tree)
		| _theirs(Call.receiver, user, in_tree)
		| _theirs(Call.owner, user, in_tree)
		| _about_visible(Call.reference_doctype, Call.reference_docname, user)
		| Call.name.isin(linked.where(_about_visible(Link.link_doctype, Link.link_name, user)))
		| ~(
			_about_someone(Call.reference_doctype, Call.reference_docname)
			| Call.name.isin(linked.where(Link.link_doctype.isin(_ABOUT)))
		)
	)


def _on_hidden_call(DT, doctype: str, user: str, in_tree: bool):
	"""A call the user does not see links to the record.

	A note or a task written during a call points at nothing; the call links to it.
	Anybody can link anything to a call of their own, so one hidden call is enough to
	hide it: otherwise linking it would be the way to read it.
	"""
	Link = frappe.qb.DocType("Dynamic Link").as_("_activity_link")
	Call = frappe.qb.DocType("CRM Call Log").as_("_call")
	visible_calls = frappe.qb.from_(Call).select(Call.name).where(_call_visible(Call, user, in_tree))
	return DT.name.isin(
		frappe.qb.from_(Link)
		.select(Link.link_name)
		.where(
			(Link.parenttype == "CRM Call Log")
			& (Link.link_doctype == doctype)
			& Link.link_name.isnotnull()
			& Link.parent.notin(visible_calls)
		)
	)


#: What each kind of activity asks for besides seeing the person (doc 30): the
#: calls their register, the notes the internal notes. Marketing, Accounting and the
#: medical director see people and none of these.
_CAPACITA_ATTIVITA = {"CRM Call Log": "telefono.registro", "FCRM Note": "note.vedi"}


def _activity_conditions(user: str | None, doctype: str):
	user = user or frappe.session.user
	capacita = _CAPACITA_ATTIVITA.get(doctype)
	if capacita and livelli.nel_crm(user) and not livelli.puo(capacita, user):
		return frappe.qb.DocType(doctype).name.isnull()
	if sees_everyone(user):
		return ""
	# their own, or their team's when they see the team's people
	in_tree = _scope(user, "CRM Lead") is True

	DT = frappe.qb.DocType(doctype)
	if doctype == "CRM Call Log":
		return _call_visible(DT, user, in_tree)

	# a note or a task: the user's (or their team's) own, the one they are assigned,
	# or about a lead or deal they see. About nobody, it is everyone's — unless a call
	# they do not see links to it
	theirs = _theirs(DT.owner, user, in_tree)
	if doctype == "CRM Task":
		theirs = theirs | _theirs(DT.assigned_to, user, in_tree) | _assigned(doctype, DT, user, in_tree)
	return (
		theirs
		| _about_visible(DT.reference_doctype, DT.reference_docname, user)
		| ~(
			_about_someone(DT.reference_doctype, DT.reference_docname)
			| _on_hidden_call(DT, doctype, user, in_tree)
		)
	)


def get_call_log_permission_query_conditions(user=None):
	return _as_sql(_activity_conditions(user, "CRM Call Log"))


def get_note_permission_query_conditions(user=None):
	return _as_sql(_activity_conditions(user, "FCRM Note"))


def get_task_permission_query_conditions(user=None):
	return _as_sql(_activity_conditions(user, "CRM Task"))


def has_call_log_permission(doc, ptype, user):
	return _has_permission(doc, ptype, user, "CRM Call Log", _activity_conditions)


def has_note_permission(doc, ptype, user):
	return _puo_scrivere("FCRM Note", ptype, user) and _has_permission(
		doc, ptype, user, "FCRM Note", _activity_conditions
	)


def has_task_permission(doc, ptype, user):
	return _has_permission(doc, ptype, user, "CRM Task", _activity_conditions)


def visible_owners(user: str | None = None) -> list[str] | None:
	"""Whose records ``user`` sees by ownership: a list of users, or ``None`` for everyone.

	The same rule as the permission query above, for the places that count
	instead of listing — the dashboard. Records assigned by ToDo are left out: a
	count is attributed to its owner, so a deal handed to a colleague for a day
	does not show up in two people's numbers.
	"""
	user = user or frappe.session.user
	in_tree = _scope(user, "CRM Lead")
	if in_tree is None:
		return None

	if in_tree is True:
		members = {row[0] for row in _team_mem_query(user).run() if row[0]}
		return sorted(members | {user})

	return [user]


def _in_hierarchy(user: str) -> bool:
	return bool(frappe.db.exists("CRM Sales Hierarchy", {"user": user}))


def _team_mem_query(user: str):
	Mgr = frappe.qb.DocType("CRM Sales Hierarchy").as_("_sqmgr")
	Member = frappe.qb.DocType("CRM Sales Hierarchy").as_("_sqmem")
	return (
		frappe.qb.from_(Mgr)
		.join(Member)
		.on((Member.lft >= Mgr.lft) & (Member.lft <= Mgr.rgt))
		.select(Member.user)
		.where(Mgr.user == user)
	)
