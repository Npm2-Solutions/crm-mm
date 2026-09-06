# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from crm.api.site_render import sync_builder_head
from crm.api.site_routes import normalise_route


class CRMWebsiteSettings(Document):
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
		site_title: DF.Data | None
		social_links: DF.Table[CRMWebSocialLink]
		tagline: DF.SmallText | None
		terms_route: DF.Data | None
		vat_number: DF.Data | None
		whatsapp_number: DF.Data | None
	# end: auto-generated types

	def validate(self):
		self.home_page = normalise_route(self.home_page)
		self.privacy_route = normalise_route(self.privacy_route)
		self.terms_route = normalise_route(self.terms_route)
		self.whatsapp_number = _digits(self.whatsapp_number)
		self._validate_home_page()

	def _validate_home_page(self):
		"""A home page has to exist and be published, or the site root would 404.

		Only checked when Builder is installed: without it there are no pages to point at,
		and the setting is inert anyway.
		"""
		if not self.home_page or not frappe.db.exists("DocType", "Builder Page"):
			return
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
		self.apply_home_page()
		sync_builder_head(self)

	def apply_home_page(self):
		"""Mirror our home page choice into Builder Settings.

		Builder resolves the site root through its own `home_page` (the
		`get_website_user_home_page` hook), so that is the switch that has to move —
		writing ours alone would change nothing. Cleared when `serve_at_root` is off, so
		turning the toggle back leaves the root exactly as it was found.
		"""
		if not frappe.db.exists("DocType", "Builder Settings"):
			return
		wanted = self.home_page if (self.enabled and self.serve_at_root) else None
		current = frappe.db.get_single_value("Builder Settings", "home_page")
		if (current or None) == (wanted or None):
			return
		frappe.db.set_single_value("Builder Settings", "home_page", wanted)
		frappe.clear_cache()


def _digits(value: str | None) -> str | None:
	"""Keep only digits — a wa.me link takes no +, spaces or dashes."""
	if not value:
		return value
	return "".join(c for c in value if c.isdigit())
