# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""Home Actions may not carry anything a browser runs.

The avatar menu is opened by everyone, System Managers included, and a Sales
Manager can edit it. These pin the two rules — the icon is a Feather name, the
route a path or an http(s) link — on both ways a row can be saved.
"""

import frappe
import frappe.client
from frappe.tests import IntegrationTestCase, UnitTestCase

from crm.fcrm.doctype.crm_dropdown_item.crm_dropdown_item import is_allowed_icon, is_safe_route
from crm.fcrm.doctype.fcrm_settings.fcrm_settings import sync_table

MARKUP_ICON = "<svg><image href=x onerror=alert(document.cookie)>"
SCRIPT_ROUTE = "javascript:alert(document.cookie)"

SAFE_ROUTES = [
	"/crm/leads",
	"/app/todo?status=Open#top",
	"#",
	"?tab=1",
	"crm/leads",
	"https://docs.frappe.io/crm",
	"http://example.com",
	"HTTPS://EXAMPLE.COM/A",
	"  /crm/leads  ",
	# scheme-relative: the page's own http(s), so just another link
	"//cdn.example.com/page",
]

UNSAFE_ROUTES = [
	SCRIPT_ROUTE,
	"JavaScript:alert(1)",
	"  javascript:alert(1)",
	"\njavascript:alert(1)",
	" javascript:alert(1)",
	# browsers drop tabs and newlines anywhere, so these still read javascript:
	"java\tscript:alert(1)",
	"java\nscript:alert(1)",
	"java\rscript:alert(1)",
	"\x00javascript:alert(1)",
	"\x01javascript:alert(1)",
	"data:text/html,<script>alert(1)</script>",
	"data:image/svg+xml;base64,PHN2ZyBvbmxvYWQ9YWxlcnQoMSk+",
	"vbscript:msgbox(1)",
	"file:///etc/passwd",
	"mailto:someone@example.com",
	"blob:https://example.com/0f0e",
	"about:blank",
	# http(s) without a host
	"https:",
	"https://",
	"http:example.com",
	"https://[::1",
]


class UnitTestCRMDropdownItem(UnitTestCase):
	def test_feather_names_are_allowed(self):
		for icon in ("settings", "info", "log-out", "external-link", "book-open"):
			with self.subTest(icon=icon):
				self.assertTrue(is_allowed_icon(icon))

	def test_anything_else_is_not_an_icon(self):
		for icon in (
			MARKUP_ICON,
			"<svg onload=alert(1)></svg>",
			# markup is refused as a whole, however harmless this one is
			'<svg viewBox="0 0 24 24"><path d="M0 0h24v24H0z"/></svg>',
			# the menu turns lucide-* strings into CSS classes
			"lucide-settings",
			"settings fixed inset-0 z-50",
			"Settings",
			" settings",
			"",
			None,
			42,
			["settings"],
		):
			with self.subTest(icon=icon):
				self.assertFalse(is_allowed_icon(icon))

	def test_paths_and_http_links_are_safe(self):
		for route in SAFE_ROUTES:
			with self.subTest(route=route):
				self.assertTrue(is_safe_route(route))

	def test_other_schemes_are_not(self):
		for route in [*UNSAFE_ROUTES, "", "   ", None, 7]:
			with self.subTest(route=route):
				self.assertFalse(is_safe_route(route))


def make_sales_manager():
	email = "home-actions-manager@example.com"
	if not frappe.db.exists("User", email):
		user = frappe.get_doc(
			doctype="User", email=email, first_name="Home Actions", send_welcome_email=0
		).insert(ignore_permissions=True)
		user.add_roles("Sales Manager")
	return email


class TestCRMDropdownItem(IntegrationTestCase):
	def setUp(self):
		frappe.set_user(make_sales_manager())

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def save_settings_with(self, **row):
		settings = frappe.get_doc("FCRM Settings")
		settings.append("dropdown_items", {"label": "Docs", "type": "Route", "route": "/crm", **row})
		settings.save()
		return settings.dropdown_items[-1]

	def save_row_alone(self, **values):
		"""What frappe.client.save lets anyone who can write FCRM Settings do."""
		row = frappe.get_doc("FCRM Settings").dropdown_items[0]
		payload = row.as_dict(convert_dates_to_str=True)
		payload.update(values)
		frappe.client.save(payload)

	def test_sales_manager_cannot_save_a_markup_icon(self):
		self.assertRaises(frappe.ValidationError, self.save_settings_with, icon=MARKUP_ICON)
		self.assertFalse(frappe.db.exists("CRM Dropdown Item", {"icon": MARKUP_ICON}))

	def test_sales_manager_cannot_save_a_script_route(self):
		for route in UNSAFE_ROUTES:
			with self.subTest(route=route):
				self.assertRaises(frappe.ValidationError, self.save_settings_with, route=route)

	def test_a_row_saved_on_its_own_is_checked_too(self):
		self.assertRaises(frappe.ValidationError, self.save_row_alone, icon=MARKUP_ICON)
		self.assertRaises(frappe.ValidationError, self.save_row_alone, route=SCRIPT_ROUTE)
		self.assertFalse(frappe.db.exists("CRM Dropdown Item", {"icon": MARKUP_ICON}))
		self.assertFalse(frappe.db.exists("CRM Dropdown Item", {"route": SCRIPT_ROUTE}))

	def test_a_value_that_is_not_text_is_refused_cleanly(self):
		# the API takes any JSON: a number is a validation error, not a crash
		self.assertRaises(frappe.ValidationError, self.save_settings_with, icon=42)
		self.assertRaises(frappe.ValidationError, self.save_row_alone, route=["javascript:alert(1)"])

	def test_the_rejected_value_is_not_echoed(self):
		# error dialogs render HTML: the message must not carry the payload
		with self.assertRaises(frappe.ValidationError) as caught:
			self.save_settings_with(icon=MARKUP_ICON)
		self.assertNotIn("<", str(caught.exception))

	def test_icon_names_and_links_still_save(self):
		row = self.save_settings_with(icon="  book-open ", route=" https://docs.frappe.io/crm ")
		self.assertEqual(
			frappe.db.get_value("CRM Dropdown Item", row.name, ["icon", "route"]),
			("book-open", "https://docs.frappe.io/crm"),
		)
		self.save_row_alone(icon="info", route="/crm/leads")

	def test_standard_items_pass(self):
		frappe.set_user("Administrator")
		for item in frappe.get_hooks("standard_dropdown_items"):
			with self.subTest(item=item.get("name1")):
				self.assertTrue(not item.get("icon") or is_allowed_icon(item["icon"]))
				self.assertTrue(is_safe_route(item.get("route")) or item.get("type") == "Separator")
		# what every migrate runs: it saves the settings
		sync_table("dropdown_items", "standard_dropdown_items")
