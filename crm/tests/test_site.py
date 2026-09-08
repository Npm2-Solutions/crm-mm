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
from crm.api import site as site_api
from crm.api.site_routes import (
	apply_website_fields,
	guard_home_page,
	normalise_route,
	reserved_prefixes,
	route_conflict,
	slugify,
	unique_slug,
)
from crm.patches.v1_0 import create_first_web_site


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

	def setUp(self):
		self.site = frappe.get_doc(
			{"doctype": "CRM Web Site", "site_name": "Guardia", "slug": "guardia", "enabled": 1}
		).insert()

	def tearDown(self):
		frappe.db.rollback()

	def set_home(self, route):
		frappe.db.set_value("CRM Web Site", self.site.name, "home_page", route)

	def test_taking_a_live_home_page_offline_is_refused(self):
		self.set_home("casa")
		self.assertRaises(frappe.ValidationError, guard_home_page, _page("casa", 0, was=1))

	def test_deleting_the_home_page_is_refused(self):
		self.set_home("casa")
		self.assertRaises(frappe.ValidationError, guard_home_page, _page("casa", 1), "on_trash")

	def test_a_draft_home_page_can_still_be_saved_and_published(self):
		"""The regression that made a chosen-but-not-yet-live home page impossible to
		publish: publish() saves, the save threw, the page stayed a draft forever."""
		self.set_home("casa")
		guard_home_page(_page("casa", 0, was=0))
		guard_home_page(_page("casa", 1, was=0))

	def test_a_published_home_page_saves_normally(self):
		self.set_home("casa")
		guard_home_page(_page("casa", 1, was=1))

	def test_other_pages_are_untouched(self):
		self.set_home("casa")
		guard_home_page(_page("contatti", 0, was=1))
		guard_home_page(_page("contatti", 0, was=1), "on_trash")

	def test_no_home_page_configured_blocks_nothing(self):
		self.set_home(None)
		guard_home_page(_page("casa", 0, was=1))


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


def _page(route: str, published: int, was: int | None = None):
	"""A stand-in for a Builder Page, with the "before this save" state the guard reads."""
	doc = frappe._dict(route=route, published=published)
	doc.get_doc_before_save = lambda: frappe._dict(published=was) if was is not None else None
	return doc


class TestSitesInFolders(IntegrationTestCase):
	"""Several websites on one domain, each living in its own folder.

	The folder is not a label: a page's route *is* `<folder>/<page>`, so Frappe and
	Builder resolve it natively and no request-time rewriting exists anywhere.
	"""

	def tearDown(self):
		frappe.db.rollback()

	def test_folder_comes_from_the_name_and_stays_unique(self):
		first = _site("Studio Rossi")
		self.assertEqual(first.slug, "studio-rossi")
		second = _site("Studio Rossi!")
		self.assertNotEqual(second.slug, first.slug)

	def test_a_reserved_folder_is_refused(self):
		self.assertRaises(frappe.ValidationError, _site, "CRM", slug="crm")

	def test_page_routes_land_inside_the_folder(self):
		site = _site("Vetrina")
		self.assertEqual(site.page_route("chi-siamo"), "vetrina/chi-siamo")
		# already inside: left alone rather than nested twice
		self.assertEqual(site.page_route("vetrina/chi-siamo"), "vetrina/chi-siamo")
		# the home of a site is the folder itself
		self.assertEqual(site.page_route(""), "vetrina")

	def test_only_one_site_answers_at_the_root(self):
		first = _site("Primo", serve_at_root=1)
		second = _site("Secondo", serve_at_root=1)
		first.reload()
		self.assertFalse(first.serve_at_root, "the newcomer takes the root over")
		self.assertTrue(second.serve_at_root)

	def test_a_home_page_must_belong_to_its_own_site(self):
		site = _site("Terzo")
		site.home_page = "un-altro-sito/casa"
		self.assertRaises(frappe.ValidationError, site.save)

	def test_a_site_with_pages_is_not_deleted_by_accident(self):
		if "builder" not in frappe.get_installed_apps():
			self.skipTest("builder app is not installed on this site")
		site = _site("Con pagine")
		frappe.get_doc(
			{
				"doctype": "Builder Page",
				"page_title": "Casa",
				"route": f"{site.slug}/casa",
				"crm_site": site.name,
			}
		).insert()
		self.assertRaises(frappe.ValidationError, site_api.delete_site, site.name)


def _site(name: str, slug: str | None = None, serve_at_root: int = 0):
	doc = frappe.get_doc(
		{
			"doctype": "CRM Web Site",
			"site_name": name,
			"slug": slug,
			"enabled": 1,
			"serve_at_root": serve_at_root,
		}
	).insert()
	return doc


class TestFirstSitePatch(IntegrationTestCase):
	"""The migration reads values whose field no longer exists.

	`get_single_value` looks the fieldname up in the doctype meta and throws when it is
	gone — which is precisely the case for the fields that moved to `CRM Web Site`. The
	rows survive in `tabSingles`, so that is where the patch reads them, and this test
	pins that behaviour so nobody "simplifies" it back into a broken migrate.
	"""

	def tearDown(self):
		frappe.db.rollback()

	def test_get_single_value_refuses_a_field_that_moved(self):
		self.assertRaises(Exception, frappe.db.get_single_value, "CRM Website Settings", "site_title")

	def test_stored_values_still_finds_it(self):
		frappe.db.sql(
			"""insert into `tabSingles` (doctype, field, value) values (%s, %s, %s)""",
			("CRM Website Settings", "site_title", "Studio Rossi"),
		)
		stored = create_first_web_site._stored_values("CRM Website Settings")
		self.assertEqual(stored.get("site_title"), "Studio Rossi")

	def test_blank_values_are_left_out(self):
		frappe.db.sql(
			"""insert into `tabSingles` (doctype, field, value) values (%s, %s, %s)""",
			("CRM Website Settings", "tagline", ""),
		)
		self.assertNotIn("tagline", create_first_web_site._stored_values("CRM Website Settings"))
