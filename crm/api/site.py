# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The website, driven from inside the CRM.

Frappe Builder owns the canvas; everything around it — which pages exist, which are
published, what the catalogue shows, how the site is configured — is handled here so the
user never has to go looking for a second application. Builder's own dashboard stays
reachable, it just stops being where the work happens.

Every endpoint degrades cleanly when Builder is not installed: `get_status()` says so and
the UI offers the install instructions instead of a broken screen.
"""

import json

import frappe
from frappe import _
from frappe.utils import cint

from crm.api.site_routes import normalise_route, route_conflict, unique_slug

MANAGER_ROLES = {"System Manager", "Sales Manager"}
PAGE_DOCTYPE = "Builder Page"
SETTINGS = "CRM Website Settings"

# What the pages list needs. `blocks` is deliberately absent: a page's block tree is
# hundreds of kilobytes and the list never renders it.
PAGE_FIELDS = (
	"name",
	"page_title",
	"route",
	"published",
	"published_at",
	"modified",
	"preview",
	"dynamic_route",
	"draft_blocks",
)

# Catalogue doctypes the showcase can publish, with the fields each one carries.
SHOWCASE = {
	"CRM Service": {
		"title": "service_name",
		"image": "website_image",
		"extra": ("category", "duration", "default_price", "currency", "enabled", "booking_calendar"),
		"enabled_field": "enabled",
	},
	"CRM Product": {
		"title": "product_name",
		"image": "image",
		"extra": ("standard_rate", "disabled"),
		"enabled_field": None,
	},
}

EDITABLE_SHOWCASE_FIELDS = (
	"publish_on_website",
	"website_slug",
	"website_order",
	"website_image",
	"image",
	"short_description",
	"website_description",
	"description",
	"cta_type",
	"cta_label",
	"cta_target",
	"booking_calendar",
	"seo_title",
	"seo_description",
)


def is_manager() -> bool:
	return bool(MANAGER_ROLES & set(frappe.get_roles()))


def check_manager():
	if not is_manager():
		frappe.throw(_("Only sales managers can manage the website"), frappe.PermissionError)


def builder_installed() -> bool:
	return "builder" in frappe.get_installed_apps()


def _require_builder():
	if not builder_installed():
		frappe.throw(
			_("Frappe Builder is not installed on this site. Install it to build website pages."),
			title=_("Builder missing"),
		)


def editor_path() -> str:
	"""Where Builder's editor lives. The path is configurable on the bench, so never
	hardcode `/builder` — read what this site actually serves."""
	return (frappe.conf.get("builder_path") or "builder").strip("/")


@frappe.whitelist()
def get_status() -> dict:
	"""Everything the Site section needs to decide what to render, in one call."""
	settings = frappe.get_cached_doc(SETTINGS) if frappe.db.exists("DocType", SETTINGS) else None
	return {
		"builder_installed": builder_installed(),
		"can_manage": is_manager(),
		"editor_path": editor_path(),
		"enabled": bool(settings and settings.enabled),
		"home_page": (settings and settings.home_page) or "",
		"serve_at_root": bool(settings and settings.serve_at_root),
		"site_url": frappe.utils.get_url(),
	}


# ---------------------------------------------------------------- pages


@frappe.whitelist()
def list_pages(search: str | None = None) -> list[dict]:
	check_manager()
	_require_builder()
	filters = {"is_template": 0}
	or_filters = None
	if search:
		or_filters = {"page_title": ["like", f"%{search}%"], "route": ["like", f"%{search}%"]}
	rows = frappe.get_all(
		PAGE_DOCTYPE,
		filters=filters,
		or_filters=or_filters,
		fields=list(PAGE_FIELDS),
		order_by="modified desc",
		limit_page_length=200,
	)
	home = frappe.db.get_single_value(SETTINGS, "home_page") or ""
	for row in rows:
		# a page with a draft is one whose live version is behind the editor
		row["has_draft"] = bool(row.pop("draft_blocks", None))
		row["is_home"] = bool(home) and row["route"] == home
		row["url"] = frappe.utils.get_url(f"/{row['route']}") if row["route"] else ""
	return rows


@frappe.whitelist()
def get_page(name: str) -> dict:
	check_manager()
	_require_builder()
	page = frappe.get_doc(PAGE_DOCTYPE, name)
	return {
		"name": page.name,
		"page_title": page.page_title,
		"route": page.route,
		"published": bool(page.published),
		"has_draft": bool(page.draft_blocks),
		"url": frappe.utils.get_url(f"/{page.route}") if page.route else "",
		"editor_url": f"/{editor_path()}/page/{page.name}",
		"modified": page.modified,
	}


@frappe.whitelist(methods=["POST"])
def create_page(title: str, route: str | None = None, template: str | None = None) -> dict:
	"""A new, unpublished page. `template` names a shipped Builder Page to copy blocks from."""
	check_manager()
	_require_builder()
	title = (title or "").strip()
	if not title:
		frappe.throw(_("The page needs a name"))

	route = normalise_route(route) or unique_slug(PAGE_DOCTYPE, title, field="route")
	if reason := route_conflict(route):
		frappe.throw(reason, title=_("Reserved address"))

	blocks = None
	if template and frappe.db.exists(PAGE_DOCTYPE, template):
		blocks = frappe.db.get_value(PAGE_DOCTYPE, template, "blocks")

	page = frappe.get_doc(
		{
			"doctype": PAGE_DOCTYPE,
			"page_title": title,
			"route": route,
			"published": 0,
			"blocks": blocks or _empty_body(),
		}
	).insert()
	return get_page(page.name)


@frappe.whitelist(methods=["POST"])
def duplicate_page(name: str) -> dict:
	check_manager()
	_require_builder()
	source = frappe.get_doc(PAGE_DOCTYPE, name)
	copy = frappe.copy_doc(source)
	copy.page_title = _("{0} (copy)").format(source.page_title)
	copy.route = unique_slug(PAGE_DOCTYPE, copy.page_title, field="route")
	copy.published = 0
	copy.published_at = None
	copy.insert()
	return get_page(copy.name)


@frappe.whitelist(methods=["POST"])
def rename_page(name: str, title: str, route: str | None = None) -> dict:
	check_manager()
	_require_builder()
	page = frappe.get_doc(PAGE_DOCTYPE, name)
	page.page_title = (title or "").strip() or page.page_title
	if route is not None:
		new_route = normalise_route(route)
		if new_route and new_route != page.route:
			if reason := route_conflict(new_route):
				frappe.throw(reason, title=_("Reserved address"))
			page.route = new_route
	page.save()
	return get_page(page.name)


@frappe.whitelist(methods=["POST"])
def set_published(name: str, published: bool | int) -> dict:
	"""Publish or withdraw, through Builder's own methods so snapshots still happen."""
	check_manager()
	_require_builder()
	page = frappe.get_doc(PAGE_DOCTYPE, name)
	if cint(published):
		if reason := route_conflict(page.route):
			frappe.throw(reason, title=_("Reserved address"))
		page.publish()
	else:
		if _is_home(page.route):
			frappe.throw(
				_("This is the site home page. Choose another home page before withdrawing it."),
				title=_("Home page"),
			)
		page.unpublish()
	return get_page(name)


@frappe.whitelist(methods=["POST"])
def delete_page(name: str) -> None:
	check_manager()
	_require_builder()
	route = frappe.db.get_value(PAGE_DOCTYPE, name, "route")
	if _is_home(route):
		frappe.throw(
			_("This is the site home page. Choose another home page before deleting it."),
			title=_("Home page"),
		)
	frappe.delete_doc(PAGE_DOCTYPE, name)


@frappe.whitelist()
def check_route(route: str, exclude: str | None = None) -> dict:
	"""Live validation for the route field: is it free, and if not what would work."""
	check_manager()
	route = normalise_route(route)
	if reason := route_conflict(route):
		return {"ok": False, "reason": reason, "suggestion": ""}
	taken = builder_installed() and frappe.db.exists(
		PAGE_DOCTYPE, {"route": route, "name": ["!=", exclude or ""]}
	)
	if taken:
		return {
			"ok": False,
			"reason": _("Another page already answers at this address."),
			"suggestion": unique_slug(PAGE_DOCTYPE, route, exclude=exclude, field="route"),
		}
	return {"ok": True, "reason": "", "suggestion": ""}


def _is_home(route: str | None) -> bool:
	if not route:
		return False
	return normalise_route(route) == normalise_route(frappe.db.get_single_value(SETTINGS, "home_page"))


def _empty_body() -> str:
	"""The root block Builder expects on a fresh page: a body-shaped div, nothing in it."""
	return json.dumps(
		[
			{
				"blockId": frappe.generate_hash(length=8),
				"element": "div",
				"originalElement": "body",
				"baseStyles": {"display": "flex", "flexDirection": "column", "minHeight": "100vh"},
				"mobileStyles": {},
				"tabletStyles": {},
				"rawStyles": {},
				"attributes": {},
				"customAttributes": {},
				"classes": [],
				"children": [],
			}
		]
	)


# ---------------------------------------------------------------- showcase


@frappe.whitelist()
def list_showcase(doctype: str = "CRM Service") -> list[dict]:
	"""Catalogue records with their website face, published first, in display order."""
	check_manager()
	spec = _showcase_spec(doctype)
	fields = [
		"name",
		f"{spec['title']} as title",
		"publish_on_website",
		"website_slug",
		"website_order",
		"short_description",
		f"{spec['image']} as image",
		*spec["extra"],
	]
	rows = frappe.get_all(
		doctype,
		fields=fields,
		order_by="publish_on_website desc, website_order asc, modified desc",
		limit_page_length=500,
	)
	for row in rows:
		row["doctype"] = doctype
		row["url"] = _public_url(row)
	return rows


@frappe.whitelist(methods=["POST"])
def set_showcase_published(doctype: str, name: str, published: bool | int) -> dict:
	check_manager()
	_showcase_spec(doctype)
	doc = frappe.get_doc(doctype, name)
	doc.publish_on_website = cint(published)
	doc.save()
	return {"name": doc.name, "publish_on_website": doc.publish_on_website, "slug": doc.website_slug}


@frappe.whitelist(methods=["POST"])
def save_showcase_item(doctype: str, name: str, values: dict | str) -> dict:
	"""Write the website face of one catalogue record — and nothing else.

	The dialog posts whatever it holds; only the website fields are applied, so a stale
	client can never write a price or a duration through this endpoint.
	"""
	check_manager()
	_showcase_spec(doctype)
	if isinstance(values, str):
		values = json.loads(values)
	doc = frappe.get_doc(doctype, name)
	for field in EDITABLE_SHOWCASE_FIELDS:
		if field in values and doc.meta.has_field(field):
			doc.set(field, values[field])
	doc.save()
	return {"name": doc.name, "website_slug": doc.website_slug, "url": _public_url(doc.as_dict())}


@frappe.whitelist(methods=["POST"])
def reorder_showcase(doctype: str, order: list | str) -> None:
	"""Persist a drag-and-drop reorder as `website_order` on each row."""
	check_manager()
	_showcase_spec(doctype)
	if isinstance(order, str):
		order = json.loads(order)
	for index, name in enumerate(order):
		frappe.db.set_value(doctype, name, "website_order", index, update_modified=False)


def _showcase_spec(doctype: str) -> dict:
	spec = SHOWCASE.get(doctype)
	if not spec:
		frappe.throw(_("{0} cannot be published on the website").format(doctype))
	return spec


def _public_url(row: dict) -> str:
	slug = row.get("website_slug")
	if not slug or not row.get("publish_on_website"):
		return ""
	prefix = "servizi" if row.get("doctype") == "CRM Service" else "prodotti"
	return frappe.utils.get_url(f"/{prefix}/{slug}")


# ---------------------------------------------------------------- settings


@frappe.whitelist()
def get_settings() -> dict:
	check_manager()
	doc = frappe.get_doc(SETTINGS)
	data = doc.as_dict()
	data["_editor_path"] = editor_path()
	data["_builder_installed"] = builder_installed()
	return data


@frappe.whitelist(methods=["POST"])
def save_settings(settings: dict | str) -> dict:
	check_manager()
	if isinstance(settings, str):
		settings = json.loads(settings)
	doc = frappe.get_doc(SETTINGS)
	for field in doc.meta.get_valid_columns():
		if field in settings:
			doc.set(field, settings[field])
	for table in ("nav_items", "social_links"):
		if table in settings:
			doc.set(table, settings[table] or [])
	doc.save()
	return get_settings()


@frappe.whitelist(methods=["POST"])
def set_home_page(route: str, serve_at_root: bool | int | None = None) -> dict:
	"""Point the site home at a page — the one setting that changes what `/` serves."""
	check_manager()
	doc = frappe.get_doc(SETTINGS)
	doc.home_page = normalise_route(route)
	if serve_at_root is not None:
		doc.serve_at_root = cint(serve_at_root)
	doc.save()
	return {"home_page": doc.home_page, "serve_at_root": doc.serve_at_root}


# ---------------------------------------------------------------- public


@frappe.whitelist(allow_guest=True, methods=["GET"])
def list_services(category: str | None = None, limit: int = 24) -> list[dict]:
	"""Published services, for anything that renders the catalogue outside a Builder page.

	Guest-safe by construction: an explicit field list, published rows only, and nothing
	about staff, costs or internal notes.
	"""
	filters = {"publish_on_website": 1, "enabled": 1}
	if category:
		filters["category"] = category
	rows = frappe.get_all(
		"CRM Service",
		filters=filters,
		fields=[
			"service_name as title",
			"website_slug as slug",
			"short_description",
			"category",
			"duration",
			"default_price",
			"currency",
			"website_image as image",
		],
		order_by="website_order asc, service_name asc",
		limit_page_length=min(cint(limit) or 24, 96),
	)
	for row in rows:
		row["price"] = (
			frappe.utils.fmt_money(row.default_price, currency=row.currency or "EUR")
			if row.default_price
			else ""
		)
		row.pop("default_price", None)
		row.pop("currency", None)
	return rows
