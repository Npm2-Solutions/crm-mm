# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""Dashboards on disk: templates that follow the site, and who may see and change what."""

import json

import frappe
from frappe.tests import IntegrationTestCase

from crm.api import dashboard as api
from crm.dashboard import features, store, templates

MANAGER = "crm.manager@example.com"
SALES_USER = "crm.user1@example.com"
OTHER_SALES_USER = "crm.user2@example.com"


class TestDashboardStore(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.delete("CRM Dashboard")
		features.forget()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def names(self, dashboards):
		return [row["template"] for row in dashboards if not row["private"]]

	def test_a_new_site_gets_one_shared_dashboard_per_template(self):
		store.ensure_defaults()
		have = set(frappe.get_all("CRM Dashboard", filters={"private": 0}, pluck="template"))
		self.assertEqual(have, {template.id for template in templates.TEMPLATES})
		main = frappe.get_doc("CRM Dashboard", store.MANAGER_DASHBOARD)
		self.assertEqual(main.template, "overview")
		self.assertTrue(store.is_managed(main))

	def test_salespeople_do_not_see_the_team_dashboard(self):
		store.ensure_defaults()
		frappe.set_user(SALES_USER)
		self.assertNotIn("team", self.names(api.get_dashboards()["dashboards"]))
		frappe.set_user(MANAGER)
		self.assertIn("team", self.names(api.get_dashboards()["dashboards"]))

	def test_a_template_dashboard_follows_the_site(self):
		store.ensure_defaults()
		overview = lambda: [item["name"] for item in store.load(store.MANAGER_DASHBOARD)["layout"]]  # noqa: E731
		self.assertNotIn("appointments_today", overview())

		frappe.get_doc(
			{
				"doctype": "CRM Service",
				"service_name": "Test cut",
				"enabled": 1,
				"staff": [{"user": MANAGER}],
			}
		).insert(ignore_permissions=True)
		features.forget()
		self.assertIn("appointments_today", overview())

	def test_a_section_without_widgets_loses_its_heading(self):
		layout_ = templates.build(
			templates.get("conversations"), lambda widget: widget.category != "whatsapp"
		)
		headings = [item["config"]["title"] for item in layout_ if item["name"] == "heading"]
		self.assertNotIn("WhatsApp", headings)
		self.assertIn("SMS", headings)

	def test_salesperson_makes_private_dashboards_but_cannot_touch_shared_ones(self):
		store.ensure_defaults()
		frappe.set_user(SALES_USER)
		mine = api.create_dashboard("My numbers", private=1)
		self.assertTrue(mine["can_edit"])
		api.save_dashboard_layout(mine["name"], json.dumps([{"name": "won_deals"}]))
		with self.assertRaises(frappe.PermissionError):
			api.save_dashboard_layout(store.MANAGER_DASHBOARD, "[]")
		with self.assertRaises(frappe.PermissionError):
			api.create_dashboard("For everyone", private=0)
		with self.assertRaises(frappe.PermissionError):
			api.delete_dashboard(store.MANAGER_DASHBOARD)

	def test_private_dashboards_stay_private(self):
		frappe.set_user(SALES_USER)
		mine = api.create_dashboard("Only mine", private=1)["name"]
		frappe.set_user(OTHER_SALES_USER)
		self.assertNotIn(mine, [row["name"] for row in api.get_dashboards()["dashboards"]])
		with self.assertRaises(frappe.PermissionError):
			api.get_dashboard_layout(mine)
		self.assertNotIn(mine, frappe.get_list("CRM Dashboard", pluck="name"))

	def test_saving_customizes_and_reset_follows_the_template_again(self):
		store.ensure_defaults()
		frappe.set_user(MANAGER)
		saved = api.save_dashboard_layout(
			store.MANAGER_DASHBOARD,
			json.dumps(
				[
					{
						"name": "deals_by_stage",
						"layout": {"x": 0, "y": 0, "w": 10, "h": 8, "i": "stages"},
						"config": {"measure": "value", "title": "Where the money is", "period": "today"},
						"data": {"kind": "axis"},
					}
				]
			),
		)
		self.assertFalse(saved["managed"])
		self.assertEqual([item["name"] for item in saved["layout"]], ["deals_by_stage"])
		# the dashboard's period is the only one; the widget's own settings survive
		self.assertEqual(saved["layout"][0]["config"], {"title": "Where the money is", "measure": "value"})
		self.assertNotIn("data", saved["layout"][0])

		reset = api.reset_dashboard(store.MANAGER_DASHBOARD)
		self.assertTrue(reset["managed"])
		self.assertGreater(len(reset["layout"]), 1)

	def test_an_emptied_dashboard_stays_empty(self):
		store.ensure_defaults()
		frappe.set_user(MANAGER)
		self.assertEqual(api.save_dashboard_layout(store.MANAGER_DASHBOARD, "[]")["layout"], [])

	def test_a_copy_takes_the_layout_as_the_person_sees_it(self):
		store.ensure_defaults()
		frappe.set_user(SALES_USER)
		copy = api.create_dashboard("", private=1, copy_of=store.MANAGER_DASHBOARD)
		self.assertIn("(copy)", copy["title"])
		self.assertFalse(copy["managed"])
		layout_ = api.get_dashboard_layout(copy["name"])["layout"]
		self.assertTrue(layout_)
		self.assertTrue(all("unavailable" not in item for item in layout_))

	def test_a_salesperson_never_gets_manager_widgets(self):
		frappe.set_user(SALES_USER)
		catalog = api.get_widget_catalog()["widgets"]
		self.assertNotIn("team_leaderboard", [widget["id"] for widget in catalog])
		answer = api.get_widgets_data(json.dumps([{"i": "t", "name": "team_leaderboard"}]))
		self.assertEqual(answer["t"]["unavailable"]["reason"], "managers_only")

	def test_widget_answers_do_not_take_each_other_down(self):
		answer = api.get_widgets_data(
			json.dumps(
				[
					{"i": "ok", "name": "won_deals"},
					{"i": "gone", "name": "no_such_widget"},
					{"i": "h", "name": "heading"},
				]
			)
		)
		self.assertEqual(answer["ok"]["kind"], "number")
		self.assertIn("error", answer["gone"])
		self.assertNotIn("h", answer)

	def test_only_mine_counts_only_the_viewer(self):
		frappe.set_user(MANAGER)
		team = api.widget_answer("won_deals", {}, None, None, None, 0)
		mine = api.widget_answer("won_deals", {}, None, None, None, 1)
		self.assertEqual(team["scope"], "team")
		self.assertEqual(mine["scope"], "me")

	def test_catalogue_explains_what_is_missing(self):
		catalog = {widget["id"]: widget for widget in api.get_widget_catalog()["widgets"]}
		if "calls" not in features.active():
			missing = catalog["calls_total"]["unavailable"]
			self.assertEqual(missing["reason"], "feature")
			self.assertEqual(missing["feature"]["key"], "calls")
			self.assertTrue(missing["message"])

	def test_the_first_dashboard_endpoints_still_answer(self):
		items = api.get_dashboard()
		self.assertTrue(items)
		self.assertTrue(all("name" in item for item in items))
		api.reset_to_default()
		self.assertTrue(store.is_managed(frappe.get_doc("CRM Dashboard", store.MANAGER_DASHBOARD)))
