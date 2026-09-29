# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.query_builder.functions import IfNull
from frappe.utils.caching import request_cache

_OWNER_FIELD = {
	"CRM Lead": "lead_owner",
	"CRM Deal": "deal_owner",
}


def hierarchy_enabled() -> bool:
	return bool(frappe.db.get_single_value("FCRM Settings", "enable_sales_hierarchy"))


def _scope(user: str) -> bool | None:
	"""``None`` when the user sees every record, otherwise whether they are in the tree."""
	if user == "Administrator":
		return None

	roles = frappe.get_roles(user)
	if "System Manager" in roles:
		return None

	in_tree = hierarchy_enabled() and _in_hierarchy(user)

	# Sales Manager outside the tree retains the default ie sees everything
	if "Sales Manager" in roles and not in_tree:
		return None

	return in_tree


def _theirs(field, user: str, in_tree: bool):
	"""The field names the user themselves or, in the tree, any member of their subtree."""
	if in_tree:
		return (field == user) | field.isin(_team_mem_query(user))
	return field == user


def _assigned(doctype: str, DT, user: str, in_tree: bool):
	"""The record is assigned by ToDo to the user or, in the tree, any member of their subtree."""
	Todo = frappe.qb.DocType("ToDo").as_("_todo")
	return DT.name.isin(
		frappe.qb.from_(Todo)
		.select(Todo.reference_name)
		.where(
			(Todo.reference_type == doctype)
			& (Todo.status != "Cancelled")
			& _theirs(Todo.allocated_to, user, in_tree)
		)
	)


def _permission_query_conditions(user: str | None, doctype: str):
	user = user or frappe.session.user
	in_tree = _scope(user)
	if in_tree is None:
		return ""

	# Sales User default: own records and records directly assigned to them.
	# In the tree, their subtree's records as well.
	DT = frappe.qb.DocType(doctype)
	return _theirs(DT[_OWNER_FIELD[doctype]], user, in_tree) | _assigned(doctype, DT, user, in_tree)


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


def has_lead_permission(doc, ptype, user):
	return _has_permission(doc, ptype, user, "CRM Lead")


def has_deal_permission(doc, ptype, user):
	return _has_permission(doc, ptype, user, "CRM Deal")


# --------------------------------------------------------------------------
# calls, notes and tasks follow the lead or deal they are about
# --------------------------------------------------------------------------

_ABOUT = ("CRM Lead", "CRM Deal")

# aliased, so the subqueries never collide with a table the list itself joins
_ALIAS = {"CRM Lead": "_lead", "CRM Deal": "_deal"}


def _visible(doctype: str, user: str, in_tree: bool):
	"""The leads (or deals) the user sees, as a subquery.

	Shared ones included: a share opens a lead whatever the hierarchy says, both in
	the list and on its page, and its calls, notes and tasks come along with it.
	"""
	DT = frappe.qb.DocType(doctype).as_(_ALIAS[doctype])
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
	return (
		frappe.qb.from_(DT)
		.select(DT.name)
		.where(
			_theirs(DT[_OWNER_FIELD[doctype]], user, in_tree)
			| _assigned(doctype, DT, user, in_tree)
			| DT.name.isin(shared)
		)
	)


def visible_leads(user: str | None = None):
	"""The leads ``user`` sees, as a subquery, or ``None`` when they see them all.

	For what belongs to a person and follows them - their billing details, say:
	the same rule as the list of people, shares included, so the two never disagree.
	"""
	user = user or frappe.session.user
	in_tree = _scope(user)
	if in_tree is None:
		return None
	return _visible("CRM Lead", user, in_tree)


def _about_visible(doctype_field, name_field, user: str, in_tree: bool):
	"""The record points at a lead or a deal the user sees."""
	return ((doctype_field == "CRM Lead") & name_field.isin(_visible("CRM Lead", user, in_tree))) | (
		(doctype_field == "CRM Deal") & name_field.isin(_visible("CRM Deal", user, in_tree))
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
		| _about_visible(Call.reference_doctype, Call.reference_docname, user, in_tree)
		| Call.name.isin(linked.where(_about_visible(Link.link_doctype, Link.link_name, user, in_tree)))
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


def _activity_conditions(user: str | None, doctype: str):
	user = user or frappe.session.user
	in_tree = _scope(user)
	if in_tree is None:
		return ""

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
		| _about_visible(DT.reference_doctype, DT.reference_docname, user, in_tree)
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
	return _has_permission(doc, ptype, user, "FCRM Note", _activity_conditions)


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
	if user == "Administrator":
		return None

	roles = frappe.get_roles(user)
	if "System Manager" in roles:
		return None

	if hierarchy_enabled() and _in_hierarchy(user):
		members = {row[0] for row in _team_mem_query(user).run() if row[0]}
		return sorted(members | {user})

	if "Sales Manager" in roles:
		return None

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
