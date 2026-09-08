# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from crm.api.site_render import sync_builder_head
from crm.api.site_routes import normalise_route, route_conflict, slugify, unique_slug


class CRMWebSite(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.fcrm.doctype.crm_web_nav_item.crm_web_nav_item import CRMWebNavItem
		from crm.fcrm.doctype.crm_web_social_link.crm_web_social_link import CRMWebSocialLink

		address: DF.SmallText | None
		company_name: DF.Data | None
		consent_banner: DF.Check
		consent_text: DF.SmallText | None
		default_meta_description: DF.SmallText | None
		default_meta_title: DF.Data | None
		default_og_image: DF.AttachImage | None
		email: DF.Data | None
		enabled: DF.Check
		favicon: DF.AttachImage | None
		font_family: DF.Data | None
		footer_text: DF.SmallText | None
		ga4_id: DF.Data | None
		home_page: DF.Data | None
		logo: DF.AttachImage | None
		meta_pixel_id: DF.Data | None
		nav_items: DF.Table[CRMWebNavItem]
		phone: DF.Data | None
		primary_color: DF.Color | None
		privacy_route: DF.Data | None
		robots_indexable: DF.Check
		serve_at_root: DF.Check
		site_name: DF.Data
		site_title: DF.Data | None
		slug: DF.Data | None
		social_links: DF.Table[CRMWebSocialLink]
		tagline: DF.SmallText | None
		terms_route: DF.Data | None
		vat_number: DF.Data | None
		whatsapp_number: DF.Data | None
	# end: auto-generated types

	def validate(self):
		self.set_slug()
		self.home_page = normalise_route(self.home_page)
		self.privacy_route = normalise_route(self.privacy_route)
		self.terms_route = normalise_route(self.terms_route)
		self.whatsapp_number = _digits(self.whatsapp_number)
		self.validate_home_page()

	def set_slug(self):
		"""The folder is the site's address, so it has to be free and stay put.

		Renaming it would orphan every page underneath — the routes carry the old folder —
		so it is set once and then only changed deliberately, with the pages moved along
		(see `rename_folder`).
		"""
		self.slug = slugify(self.slug) or unique_slug("CRM Web Site", self.site_name, self.name, "slug")
		if reason := route_conflict(self.slug):
			frappe.throw(reason, title=_("Reserved address"))
		clash = frappe.db.exists("CRM Web Site", {"slug": self.slug, "name": ["!=", self.name]})
		if clash:
			frappe.throw(_("Another site already uses the folder {0}").format(frappe.bold(self.slug)))

	def validate_home_page(self):
		"""A home page has to be one of this site's own pages, and be live."""
		if not self.home_page or not frappe.db.exists("DocType", "Builder Page"):
			return
		if not self.home_page.startswith(f"{self.slug}/") and self.home_page != self.slug:
			frappe.throw(_("{0} is not a page of this site.").format(frappe.bold("/" + self.home_page)))
		page = frappe.db.get_value(
			"Builder Page", {"route": self.home_page}, ["name", "published"], as_dict=True
		)
		if not page:
			frappe.throw(_("No page has the route {0}").format(frappe.bold(self.home_page)))
		if self.serve_at_root and not page.published:
			frappe.throw(
				_("{0} is not published yet, so it cannot be served at the site root.").format(
					frappe.bold(self.home_page)
				)
			)

	def on_update(self):
		self.claim_the_root()
		sync_builder_head()

	def claim_the_root(self):
		"""Only one site can answer at `/`, and Builder has a single switch for it.

		Taking the root hands it over: the site that had it keeps working under its own
		folder, which is where its pages live anyway.
		"""
		if self.serve_at_root and self.enabled:
			others = frappe.get_all(
				"CRM Web Site", filters={"serve_at_root": 1, "name": ["!=", self.name]}, pluck="name"
			)
			for other in others:
				frappe.db.set_value("CRM Web Site", other, "serve_at_root", 0, update_modified=False)

		if not frappe.db.exists("DocType", "Builder Settings"):
			return
		wanted = self.home_page if (self.enabled and self.serve_at_root) else None
		if not wanted and frappe.db.get_all(
			"CRM Web Site", filters={"serve_at_root": 1, "enabled": 1}, limit=1
		):
			# another site owns the root — leave its choice alone
			return
		current = frappe.db.get_single_value("Builder Settings", "home_page")
		if (current or None) != (wanted or None):
			frappe.db.set_single_value("Builder Settings", "home_page", wanted)
			frappe.clear_cache()

	def page_route(self, route: str) -> str:
		"""A page's full route: its address inside this site's folder."""
		route = normalise_route(route)
		if not route:
			return self.slug
		return route if route == self.slug or route.startswith(f"{self.slug}/") else f"{self.slug}/{route}"


def _digits(value: str | None) -> str | None:
	"""Keep only digits — a wa.me link takes no +, spaces or dashes."""
	if not value:
		return value
	return "".join(c for c in value if c.isdigit())
