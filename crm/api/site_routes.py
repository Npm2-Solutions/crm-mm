# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Route hygiene for the website.

Frappe's own `WebsiteGenerator` checks that two published pages don't claim the same
route, and stops there. It does not know that `/crm` is this app's SPA, that `/book`
serves the booking pages, or that `/crm-form` serves the forms — so nothing stops an
author from publishing a page at one of those and quietly shadowing a working part of
the product. That is the collision this module exists to prevent.

The reserved set is derived from the route rules the installed apps actually declare,
plus the framework paths that have no rule because they are wired lower down. Deriving
it beats hardcoding: an app installed tomorrow gets its routes protected for free.
"""

import re

import frappe
from frappe import _

# Framework and server paths that own their prefix without declaring a website route rule.
CORE_RESERVED = frozenset(
	{
		"api",
		"app",
		"assets",
		"desk",
		"files",
		"login",
		"method",
		"private",
		"socket.io",
		"update-password",
		"robots.txt",
		"sitemap.xml",
		"website_script.js",
		# Builder's own editor and asset routes
		"builder",
		"builder_assets",
		"_builder",
	}
)

SLUG_RE = re.compile(r"[^a-z0-9]+")


def normalise_route(route: str | None) -> str:
	"""A route as we store it: no scheme, no leading or trailing slash, lowercase."""
	if not route:
		return ""
	route = str(route).strip().lower()
	route = re.sub(r"^https?://[^/]+", "", route)
	return route.strip("/")


def slugify(text: str | None) -> str:
	"""A URL-safe slug. Accents are folded so 'Trattamento Viso' becomes 'trattamento-viso'."""
	if not text:
		return ""
	import unicodedata

	text = unicodedata.normalize("NFKD", str(text))
	text = "".join(c for c in text if not unicodedata.combining(c))
	return SLUG_RE.sub("-", text.lower()).strip("-")


def reserved_prefixes() -> set[str]:
	"""First path segment of every route rule any installed app declares, plus the core set.

	`/crm/<path:app_path>` reserves `crm`; `/book/<route>` reserves `book`. A rule whose
	first segment is itself a placeholder (`/<slug>`) reserves nothing — it is a catch-all
	and blocking on it would block everything.
	"""
	reserved = set(CORE_RESERVED)
	for rule in frappe.get_hooks("website_route_rules") or []:
		from_route = (rule.get("from_route") or "").strip("/")
		if not from_route:
			continue
		first = from_route.split("/")[0]
		if first.startswith("<"):
			continue
		reserved.add(first.lower())
	return reserved


def route_conflict(route: str) -> str | None:
	"""Why this route cannot be used, or None when it is free.

	Checks the first segment only: owning `crm` means owning everything under it.
	"""
	route = normalise_route(route)
	if not route:
		return _("A route is required.")
	if route.startswith((".", "_")):
		return _("A route cannot start with {0}.").format(frappe.bold(route[0]))
	first = route.split("/")[0]
	if first in reserved_prefixes():
		return _("{0} is reserved by the CRM. Pick another address.").format(frappe.bold("/" + first))
	return None


def guard_builder_route(doc, method=None):
	"""`Builder Page.validate` hook: refuse routes that shadow the CRM.

	Runs before the framework's own uniqueness check has any say — a page that never
	saves can never be published over `/crm`.
	"""
	if not doc.get("route"):
		return
	doc.route = normalise_route(doc.route)
	# a dynamic route carries a placeholder segment (/servizi/:slug); only the static
	# head of it can collide with anything of ours
	head = doc.route.split("/")[0]
	if head.startswith((":", "<")):
		frappe.throw(_("A route cannot begin with a parameter."))
	if reason := route_conflict(head):
		frappe.throw(reason, title=_("Reserved address"))


def guard_home_page(doc, method=None):
	"""Refuse to take the site's home page off the air.

	Only a *transition* counts. An earlier version threw whenever the home page was saved
	while unpublished, which meant a home page chosen before it went live could never be
	published at all: publish() saves, the save threw, and the page was stuck as a draft.
	So the rule is "was live, is being pulled", not "is not live".

	It lives on the document rather than in our API because a page can also be unpublished
	or deleted from Builder's own dashboard, and a home page that stops answering leaves
	the site root on a 404.
	"""
	if not doc.get("route") or not frappe.db.exists("DocType", "CRM Web Site"):
		return
	if not frappe.db.exists("CRM Web Site", {"home_page": normalise_route(doc.route)}):
		return

	if method == "on_trash":
		frappe.throw(_home_page_message(doc.route), title=_("Home page"))

	if doc.get("published"):
		return
	previous = doc.get_doc_before_save() if hasattr(doc, "get_doc_before_save") else None
	if previous and previous.get("published"):
		frappe.throw(_home_page_message(doc.route), title=_("Home page"))


def _home_page_message(route: str) -> str:
	return _("{0} is the site home page. Choose another home page first.").format(
		frappe.bold("/" + normalise_route(route))
	)


def unique_slug(doctype: str, text: str, exclude: str | None = None, field: str = "website_slug") -> str:
	"""A slug free within `doctype`, suffixed with -2, -3 … when it is already taken."""
	base = slugify(text) or "pagina"
	candidate, n = base, 1
	while True:
		filters = {field: candidate}
		if exclude:
			filters["name"] = ["!=", exclude]
		if not frappe.db.exists(doctype, filters):
			return candidate
		n += 1
		candidate = f"{base}-{n}"


def apply_website_fields(doc):
	"""Shared `validate` step for the publishable catalogue doctypes.

	Fills the slug from the record's own title the first time it is published, and keeps
	an empty CTA target from claiming to be a working button.
	"""
	title = doc.get("service_name") or doc.get("product_name") or doc.get("name")
	if doc.get("website_slug"):
		doc.website_slug = slugify(doc.website_slug)
	elif doc.get("publish_on_website"):
		doc.website_slug = unique_slug(doc.doctype, title, exclude=doc.get("name"))

	if doc.get("website_slug") and (reason := route_conflict(doc.website_slug)):
		frappe.throw(reason, title=_("Reserved address"))

	if doc.get("cta_type") == "Book" and not doc.get("booking_calendar"):
		# Book with nowhere to book is a dead button on a live page
		doc.cta_type = "None"
