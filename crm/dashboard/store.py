# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Dashboards on disk: who sees which, who may change it, and what it shows.

A dashboard is a ``CRM Dashboard`` row. Shared ones (``private = 0``) are for the
whole team and only managers change them; private ones belong to one person,
any salesperson included. A dashboard made from a template keeps its layout
empty and is laid out afresh for each viewer — so it follows the site and the
viewer's role — until somebody rearranges it and saves; "reset" empties it
again.

The widgets on a saved layout are checked on the way out too: a widget whose
feature was switched off, or that only managers may see, is dropped for a
salesperson and shown to a manager as "not available" with the reason — they
are the ones who can do something about it.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _

from crm.dashboard import features, layout, registry, templates
from crm.dashboard.context import is_manager

DOCTYPE = "CRM Dashboard"
MANAGER_DASHBOARD = "Manager Dashboard"
PERIODS = (
	"today",
	"yesterday",
	"this_week",
	"last_7_days",
	"this_month",
	"last_month",
	"last_30_days",
	"last_90_days",
	"this_quarter",
	"this_year",
)
DEFAULT_PERIOD = "last_30_days"


# -- who may do what ---------------------------------------------------------------


def can_view(doc, user: str | None = None) -> bool:
	user = user or frappe.session.user
	if not doc.private:
		template = templates.get(doc.template)
		return not (template and template.managers_only and not is_manager(user))
	return doc.user == user


def can_edit(doc, user: str | None = None) -> bool:
	user = user or frappe.session.user
	if doc.private:
		return doc.user == user
	return is_manager(user)


def get_viewable(name: str):
	if not name or not frappe.db.exists(DOCTYPE, name):
		frappe.throw(_("This dashboard does not exist any more"), frappe.DoesNotExistError)
	doc = frappe.get_doc(DOCTYPE, name)
	if not can_view(doc):
		frappe.throw(_("You cannot open this dashboard"), frappe.PermissionError)
	return doc


def get_editable(name: str):
	doc = get_viewable(name)
	if not can_edit(doc):
		frappe.throw(_("Only managers can change a shared dashboard"), frappe.PermissionError)
	return doc


# -- which widgets a viewer can have -----------------------------------------------


def availability(widget: registry.Widget, user: str | None = None) -> dict[str, Any] | None:
	"""Why ``widget`` cannot be shown to ``user``; ``None`` when it can."""
	user = user or frappe.session.user
	if widget.managers_only and not is_manager(user):
		return {"reason": "managers_only", "message": _("Only managers can see this")}
	missing = features.missing(widget.requires)
	if missing:
		first = features.describe(missing[0])
		return {"reason": "feature", "feature": first, "message": first["hint"]}
	return None


def showable(widget: registry.Widget) -> bool:
	return not widget.retired and availability(widget) is None


# -- reading ------------------------------------------------------------------------


def _stored_layout(doc) -> list[dict[str, Any]]:
	try:
		value = json.loads(doc.layout or "[]")
	except (TypeError, ValueError):
		return []
	return value if isinstance(value, list) else []


def is_managed(doc) -> bool:
	"""The dashboard follows its template: nobody has saved a layout of their own on it."""
	return bool(templates.get(doc.template)) and not doc.customized


def resolve(doc) -> list[dict[str, Any]]:
	"""The layout ``doc`` shows to the person asking, every item marked with what it needs."""
	template = templates.get(doc.template)
	if is_managed(doc):
		items = templates.build(template, showable)
	else:
		items = layout.sanitize(_stored_layout(doc), allowed_options())
	manager = is_manager()
	resolved = []
	for item in items:
		if item["name"] in layout.STRUCTURAL:
			resolved.append(item)
			continue
		widget = registry.get(item["name"])
		if not widget:
			if manager:
				item["unavailable"] = {
					"reason": "unknown",
					"message": _("This widget does not exist any more"),
				}
				resolved.append(item)
			continue
		blocked = availability(widget)
		if blocked:
			# a salesperson cannot switch WhatsApp on: showing them the gap is noise
			if not manager or blocked["reason"] == "managers_only":
				continue
			item["unavailable"] = blocked
		item["type"] = widget.kind
		resolved.append(item)
	return resolved


def title_of(doc) -> str:
	if doc.title:
		return doc.title
	template = templates.get(doc.template)
	return str(template.title) if template else _("Dashboard")


def summary(doc, *, with_availability: bool = True) -> dict[str, Any]:
	template = templates.get(doc.template)
	managed = is_managed(doc)
	available = True
	if with_availability and managed:
		available = any(item["name"] not in layout.STRUCTURAL for item in templates.build(template, showable))
	return {
		"name": doc.name,
		"title": title_of(doc),
		"icon": doc.icon or (template.icon if template else "layout-dashboard"),
		"template": doc.template,
		"private": bool(doc.private),
		"only_mine": bool(doc.only_mine),
		"period": doc.period or (template.period if template else DEFAULT_PERIOD),
		"managed": managed,
		"can_edit": can_edit(doc),
		"available": available,
		"sequence": doc.sequence or 0,
	}


def visible_dashboards() -> list[dict[str, Any]]:
	ensure_defaults()
	user = frappe.session.user
	rows = frappe.get_all(
		DOCTYPE,
		or_filters={"private": 0, "user": user},
		fields=[
			"name",
			"title",
			"icon",
			"template",
			"customized",
			"private",
			"user",
			"only_mine",
			"period",
			"sequence",
		],
		order_by="private asc, sequence asc, creation asc",
		ignore_permissions=True,
	)
	out = []
	for row in rows:
		doc = frappe._dict(row)
		if can_view(doc, user):
			out.append(summary(doc))
	return out


def load(name: str) -> dict[str, Any]:
	doc = get_viewable(name)
	return {**summary(doc, with_availability=False), "layout": resolve(doc)}


# -- writing ------------------------------------------------------------------------


def allowed_options() -> dict[str, set[str]]:
	return {widget.id: {option.key for option in widget.options} for widget in registry.all_widgets()}


def save_layout(name: str, items: Any) -> dict[str, Any]:
	doc = get_editable(name)
	cleaned = layout.sanitize(items, allowed_options())
	for item in cleaned:
		widget = registry.get(item["name"])
		if widget:
			item["type"] = widget.kind
			if item.get("config"):
				item["config"] = _clean_config(widget, item["config"])
	doc.layout = json.dumps(cleaned)
	doc.customized = 1
	doc.save(ignore_permissions=True)
	return load(doc.name)


def _clean_config(widget: registry.Widget, config: dict) -> dict:
	cleaned = {key: config[key] for key in layout.COMMON_CONFIG if config.get(key) not in (None, "")}
	cleaned.pop("period", None)  # the dashboard's period is the one every widget follows
	for option in widget.options:
		if option.key in config:
			value = option.clean(config[option.key])
			if value not in (None, "") and value != option.default:
				cleaned[option.key] = value
	return cleaned


def update(name: str, **values) -> dict[str, Any]:
	doc = get_editable(name)
	if "title" in values and values["title"] is not None:
		doc.title = str(values["title"]).strip()[:140]
	if values.get("icon") is not None:
		doc.icon = str(values["icon"]).strip()[:40]
	if values.get("period") is not None:
		doc.period = values["period"] if values["period"] in PERIODS else None
	if values.get("only_mine") is not None:
		doc.only_mine = 1 if frappe.utils.cint(values["only_mine"]) else 0
	doc.save(ignore_permissions=True)
	return summary(doc)


def create(
	title: str, *, private: bool = True, template: str | None = None, copy_of: str | None = None
) -> dict[str, Any]:
	if not private and not is_manager():
		frappe.throw(_("Only managers can create a dashboard for the whole team"), frappe.PermissionError)
	doc = frappe.new_doc(DOCTYPE)
	doc.title = (title or "").strip()[:140]
	doc.private = 1 if private else 0
	doc.user = frappe.session.user if private else None
	doc.sequence = 100
	if copy_of:
		source = get_viewable(copy_of)
		doc.template = source.template
		doc.icon = source.icon
		doc.period = source.period
		doc.only_mine = source.only_mine
		# a copy is a starting point to change: it takes the layout as the person sees it
		doc.layout = json.dumps([_without_state(item) for item in resolve(source)])
		doc.customized = 1
		doc.title = doc.title or _("{0} (copy)").format(title_of(source))
	elif template:
		chosen = templates.get(template)
		if not chosen:
			frappe.throw(_("Unknown dashboard template"))
		doc.template = chosen.id
		doc.icon = chosen.icon
		doc.period = chosen.period
		doc.only_mine = 1 if chosen.only_mine else 0
		doc.layout = "[]"
	else:
		doc.layout = "[]"
	if not doc.title:
		frappe.throw(_("Give the dashboard a name"))
	doc.insert(ignore_permissions=True)
	return summary(doc)


def _without_state(item: dict) -> dict:
	return {key: value for key, value in item.items() if key in ("name", "type", "layout", "config")}


def delete(name: str) -> None:
	doc = get_editable(name)
	frappe.delete_doc(DOCTYPE, doc.name, ignore_permissions=True)


def reset(name: str) -> dict[str, Any]:
	doc = get_editable(name)
	if not templates.get(doc.template):
		frappe.throw(_("This dashboard was not made from a template"))
	doc.layout = "[]"
	doc.customized = 0
	doc.save(ignore_permissions=True)
	return load(doc.name)


# -- the dashboards every site starts with -----------------------------------------


def ensure_manager_dashboard(force: bool = False) -> str:
	"""The team's main dashboard (it keeps the name the first dashboard had)."""
	if not frappe.db.exists(DOCTYPE, MANAGER_DASHBOARD):
		doc = frappe.new_doc(DOCTYPE)
		doc.template = "overview"
		doc.icon = templates.get("overview").icon
		doc.period = templates.get("overview").period
		doc.sequence = templates.get("overview").sequence
		doc.layout = "[]"
		doc.insert(ignore_permissions=True, set_name=MANAGER_DASHBOARD)
	elif force:
		doc = frappe.get_doc(DOCTYPE, MANAGER_DASHBOARD)
		doc.template = "overview"
		doc.layout = "[]"
		doc.customized = 0
		doc.save(ignore_permissions=True)
	return frappe.db.get_value(DOCTYPE, MANAGER_DASHBOARD, "layout") or "[]"


def ensure_defaults() -> None:
	"""A site with no shared dashboard gets one per template."""
	if frappe.db.exists(DOCTYPE, {"private": 0}):
		return
	create_template_dashboards()


def create_template_dashboards(only: tuple[str, ...] | None = None) -> list[str]:
	"""A shared dashboard for every template (or those in ``only``) that does not have one yet."""
	ensure_manager_dashboard()
	have = set(frappe.get_all(DOCTYPE, filters={"private": 0}, pluck="template"))
	made = []
	for template in templates.TEMPLATES:
		if template.id in have or template.id == "overview":
			continue
		if only is not None and template.id not in only:
			continue
		doc = frappe.new_doc(DOCTYPE)
		doc.template = template.id
		doc.icon = template.icon
		doc.period = template.period
		doc.only_mine = 1 if template.only_mine else 0
		doc.sequence = template.sequence
		doc.layout = "[]"
		doc.insert(ignore_permissions=True)
		made.append(doc.name)
	return made
