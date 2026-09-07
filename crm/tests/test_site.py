# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""The website's route hygiene and its catalogue face.

The rules here exist so the site cannot damage the product it lives next to: a page
published over `/crm` would take the app off the air, and a slug colliding with `/book`
would break the booking links already in circulation. Frappe checks neither — its own
uniqueness test only compares one page's route with another's.
"""

import frappe
from frappe.tests import IntegrationTestCase

from crm.api import site
from crm.api.site_routes import (
	apply_website_fields,
	guard_home_page,
	normalise_route,
	reserved_prefixes,
	route_conflict,
	slugify,
	unique_slug,
)


class TestSiteRoutes(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	# ---- normalising ----

	def test_route_is_normalised(self):
		self.assertEqual(normalise_route("/Servizi/"), "servizi")
		self.assertEqual(normalise_route("https://example.com/chi-siamo"), "chi-siamo")
		self.assertEqual(normalise_route("  "), "")
		self.assertEqual(normalise_route(None), "")

	def test_slugify_folds_accents_and_punctuation(self):
		self.assertEqual(slugify("Trattamento Viso — Base"), "trattamento-viso-base")
		self.assertEqual(slugify("Città & Benessere"), "citta-benessere")
		self.assertEqual(slugify(""), "")

	# ---- the reserved set ----

	def test_reserved_set_is_derived_from_installed_route_rules(self):
		"""Derived, not hardcoded: an app installed later gets its routes protected too."""
		reserved = reserved_prefixes()
		# from crm's own hooks
		self.assertIn("crm", reserved)
		self.assertIn("book", reserved)
		self.assertIn("crm-form", reserved)
		# framework paths that have no route rule
		self.assertIn("api", reserved)
		self.assertIn("assets", reserved)
		self.assertIn("app", reserved)

	def test_catch_all_rules_reserve_nothing(self):
		"""A rule like `/<slug>` must not make every route reserved."""
		self.assertNotIn("<slug>", reserved_prefixes())
		self.assertIsNone(route_conflict("qualsiasi-pagina"))

	# ---- conflicts ----

	def test_app_routes_are_refused(self):
		for route in ("crm", "crm/leads", "book", "book/consulenza", "api", "assets/x"):
			with self.subTest(route=route):
				self.assertIsNotNone(route_conflict(route), f"{route} should be refused")

	def test_ordinary_routes_are_allowed(self):
		for route in ("servizi", "chi-siamo", "servizi/trattamento-viso", "blog/2026/estate"):
			with self.subTest(route=route):
				self.assertIsNone(route_conflict(route))

	def test_empty_and_dotted_routes_are_refused(self):
		self.assertIsNotNone(route_conflict(""))
		self.assertIsNotNone(route_conflict("../etc"))
		self.assertIsNotNone(route_conflict("_private"))

	def test_reserved_check_is_case_insensitive(self):
		self.assertIsNotNone(route_conflict("CRM"))
		self.assertIsNotNone(route_conflict("/Book/"))

	# ---- unique slugs ----

	def test_unique_slug_suffixes_only_when_taken(self):
		service = _service("Massaggio", publish=True)
		self.assertEqual(service.website_slug, "massaggio")
		twin = _service("Massaggio!", publish=True)
		self.assertEqual(twin.website_slug, "massaggio-2")

	def test_unique_slug_ignores_the_record_itself(self):
		service = _service("Sauna", publish=True)
		again = unique_slug("CRM Service", "Sauna", exclude=service.name)
		self.assertEqual(again, "sauna")


class TestWebsiteFields(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_slug_is_filled_in_on_publish_and_left_alone_otherwise(self):
		draft = _service("Non pubblicato")
		self.assertFalse(draft.website_slug)
		draft.publish_on_website = 1
		draft.save()
		self.assertEqual(draft.website_slug, "non-pubblicato")

	def test_an_author_typed_slug_is_cleaned_not_replaced(self):
		service = _service("Peeling", publish=True, slug="Peeling Viso Profondo")
		self.assertEqual(service.website_slug, "peeling-viso-profondo")

	def test_a_reserved_slug_is_refused(self):
		service = _service("Prova")
		service.publish_on_website = 1
		service.website_slug = "crm"
		self.assertRaises(frappe.ValidationError, service.save)

	def test_book_without_a_calendar_is_not_a_button(self):
		"""A Book button with nowhere to book is a dead link on a live page."""
		service = _service("Consulenza", publish=True)
		service.cta_type = "Book"
		service.booking_calendar = None
		service.save()
		self.assertEqual(service.cta_type, "None")

	def test_apply_website_fields_is_shared_by_products(self):
		product = frappe.get_doc(
			{
				"doctype": "CRM Product",
				"product_code": frappe.generate_hash(length=6),
				"product_name": "Crema Idratante",
				"publish_on_website": 1,
			}
		)
		product.flags.ignore_erpnext_sync = True
		product.insert()
		self.assertEqual(product.website_slug, "crema-idratante")


class TestSiteAPI(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_status_reports_what_the_ui_needs(self):
		status = site.get_status()
		self.assertIn("builder_installed", status)
		self.assertIn("editor_path", status)
		self.assertTrue(status["editor_path"])

	def test_editor_path_follows_the_bench_setting(self):
		"""Builder's editor route is configurable, so it is never hardcoded."""
		frappe.conf.builder_path = "pagine"
		try:
			self.assertEqual(site.editor_path(), "pagine")
		finally:
			frappe.conf.pop("builder_path", None)

	def test_check_route_refuses_reserved_addresses(self):
		result = site.check_route("crm")
		self.assertFalse(result["ok"])
		self.assertTrue(result["reason"])

	def test_check_route_accepts_a_free_address(self):
		self.assertTrue(site.check_route("una-pagina-nuova")["ok"])

	def test_showcase_lists_services_with_their_website_face(self):
		_service("Vetrina Uno", publish=True)
		rows = site.list_showcase("CRM Service")
		titles = [row["title"] for row in rows]
		self.assertIn("Vetrina Uno", titles)
		row = next(r for r in rows if r["title"] == "Vetrina Uno")
		self.assertEqual(row["doctype"], "CRM Service")
		self.assertTrue(row["url"].endswith("/servizi/vetrina-uno"))

	def test_showcase_refuses_a_doctype_it_does_not_publish(self):
		self.assertRaises(frappe.ValidationError, site.list_showcase, "CRM Lead")

	def test_saving_a_card_writes_only_website_fields(self):
		"""A stale client must not be able to move a price through this endpoint."""
		service = _service("Prezzo Fermo", publish=True)
		service.db_set("default_price", 120)
		site.save_showcase_item(
			"CRM Service",
			service.name,
			{"short_description": "Due righe", "default_price": 1, "duration": 5},
		)
		service.reload()
		self.assertEqual(service.short_description, "Due righe")
		self.assertEqual(service.default_price, 120)
		self.assertEqual(service.duration, 30)

	def test_public_service_list_only_shows_published_ones(self):
		_service("Pubblico", publish=True)
		_service("Nascosto")
		titles = [row["title"] for row in site.list_services()]
		self.assertIn("Pubblico", titles)
		self.assertNotIn("Nascosto", titles)

	def test_public_service_list_never_leaks_internal_fields(self):
		_service("Riservato", publish=True)
		rows = site.list_services()
		for row in rows:
			self.assertNotIn("default_price", row)
			self.assertNotIn("staff", row)
			self.assertIn("price", row)

	def test_write_endpoints_need_a_manager(self):
		frappe.set_user("Guest")
		self.assertRaises(frappe.PermissionError, site.check_route, "qualcosa")


class TestHomePageGuard(IntegrationTestCase):
	"""The home page must survive every path, not only the CRM's own buttons.

	Builder's dashboard can unpublish or delete a page too, so the rule sits on the
	document rather than in the API that happens to be convenient.
	"""

	def tearDown(self):
		frappe.db.set_single_value("CRM Website Settings", "home_page", None)
		frappe.db.rollback()

	def test_unpublishing_the_home_page_is_refused(self):
		frappe.db.set_single_value("CRM Website Settings", "home_page", "casa")
		doc = frappe._dict(route="casa", published=0)
		self.assertRaises(frappe.ValidationError, guard_home_page, doc)

	def test_deleting_the_home_page_is_refused(self):
		frappe.db.set_single_value("CRM Website Settings", "home_page", "casa")
		doc = frappe._dict(route="casa", published=1)
		self.assertRaises(frappe.ValidationError, guard_home_page, doc, "on_trash")

	def test_a_published_home_page_saves_normally(self):
		frappe.db.set_single_value("CRM Website Settings", "home_page", "casa")
		guard_home_page(frappe._dict(route="casa", published=1))

	def test_other_pages_are_untouched(self):
		frappe.db.set_single_value("CRM Website Settings", "home_page", "casa")
		guard_home_page(frappe._dict(route="contatti", published=0))
		guard_home_page(frappe._dict(route="contatti", published=0), "on_trash")

	def test_no_home_page_configured_blocks_nothing(self):
		frappe.db.set_single_value("CRM Website Settings", "home_page", None)
		guard_home_page(frappe._dict(route="casa", published=0))


def _service(name: str, *, publish: bool = False, slug: str | None = None):
	doc = frappe.get_doc(
		{
			"doctype": "CRM Service",
			"service_name": name,
			"enabled": 1,
			"duration": 30,
			"publish_on_website": 1 if publish else 0,
			"website_slug": slug,
		}
	)
	doc.insert()
	return doc
