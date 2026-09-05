# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Call scripts: the procedure an agent works through while the line is open.

A script is steps, and each step carries the wording to actually say. That shape
is what a receptionist selling a service needs — the sequence keeps them on
track, the wording means a new hire has the sentence ready — and it degrades
gracefully into a plain reference document when a practice writes one long step.
"""

import frappe
from frappe import _

MANAGER_ROLES = {"System Manager", "Sales Manager"}


def _check_manager():
	if not (MANAGER_ROLES & set(frappe.get_roles())):
		frappe.throw(_("Not permitted"), frappe.PermissionError)


def _as_dict(doc) -> dict:
	return {
		"name": doc.name,
		"script_name": doc.script_name,
		"enabled": bool(doc.enabled),
		"service": doc.service,
		"description": doc.description,
		"order": doc.idx_hint,
		"steps": [
			{
				"name": step.name,
				"idx": step.idx,
				"title": step.title,
				"body": step.body,
				"optional": bool(step.optional),
			}
			for step in doc.steps
		],
	}


@frappe.whitelist()
def list_scripts(service: str | None = None, include_disabled: bool = False) -> list[dict]:
	"""Scripts an agent can pick from, the ones for this service first.

	Readable by anyone who can read the doctype: an agent needs their script
	mid-call, and a permission error at that moment is a lost sale.
	"""
	filters = {} if frappe.utils.sbool(include_disabled) else {"enabled": 1}
	names = frappe.get_list(
		"CRM Call Script", filters=filters, pluck="name", order_by="idx_hint asc, script_name asc"
	)
	scripts = [_as_dict(frappe.get_cached_doc("CRM Call Script", name)) for name in names]
	if not service:
		return scripts
	# the service's own scripts first, then the general ones — never hide either,
	# because the call that starts about one service often ends about another
	return sorted(scripts, key=lambda s: (s["service"] != service, s["service"] is not None))


@frappe.whitelist()
def get_script(name: str) -> dict:
	doc = frappe.get_doc("CRM Call Script", name)
	doc.check_permission("read")
	return _as_dict(doc)


@frappe.whitelist(methods=["POST"])
def save_script(script: str | dict, name: str | None = None) -> dict:
	_check_manager()
	payload = frappe.parse_json(script) or {}
	if not isinstance(payload, dict):
		frappe.throw(_("Invalid script"))

	values = {
		"script_name": (payload.get("script_name") or "").strip(),
		"enabled": frappe.utils.cint(payload.get("enabled", 1)),
		"service": payload.get("service") or None,
		"description": payload.get("description") or None,
		"idx_hint": frappe.utils.cint(payload.get("order")),
		"steps": [
			{
				"title": (step.get("title") or "").strip(),
				"body": step.get("body") or None,
				"optional": frappe.utils.cint(step.get("optional")),
			}
			for step in payload.get("steps") or []
			if (step.get("title") or "").strip()
		],
	}
	if not values["script_name"]:
		frappe.throw(_("The script needs a name."))

	if name:
		doc = frappe.get_doc("CRM Call Script", name)
		# a child table is replaced wholesale; merging would leave removed steps behind
		doc.set("steps", [])
		doc.update(values)
		doc.save()
	else:
		doc = frappe.get_doc({"doctype": "CRM Call Script", **values})
		doc.insert()
	return _as_dict(doc)


@frappe.whitelist(methods=["POST"])
def delete_script(name: str) -> None:
	_check_manager()
	frappe.delete_doc("CRM Call Script", name)
