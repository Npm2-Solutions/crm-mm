# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""The widget catalogue against a real database.

The first test is the net under all the others: every widget in the catalogue is
asked for its answer, for the whole team and for one salesperson, and must give
back a payload of the kind it promises. A query that only breaks on MariaDB, a
column renamed under a widget, a join that no longer exists — they all fail
here, by name, instead of as a blank tile on somebody's dashboard.
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.tests.utils import make_test_records
from frappe.utils import add_days, get_first_day, get_last_day, nowdate

from crm.dashboard import registry
from crm.dashboard.context import Context

SALES_USER = "crm.user1@example.com"


class TestDashboardWidgets(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.from_date = get_first_day(nowdate())
		cls.to_date = get_last_day(nowdate())
		for doctype in (
			"CRM Lead Status",
			"CRM Deal Status",
			"CRM Lead Source",
			"CRM Lost Reason",
			"CRM Organization",
			"CRM Lead",
			"CRM Deal",
		):
			make_test_records(doctype)

	@classmethod
	def tearDownClass(cls):
		frappe.db.rollback()
		super().tearDownClass()

	def answer(self, widget_id, user=None, config=None, **dates):
		widget = registry.get(widget_id)
		self.assertIsNotNone(widget, widget_id)
		ctx = Context.build(
			dates.get("from_date", self.from_date),
			dates.get("to_date", self.to_date),
			requested_user=user,
			scope=widget.scope,
			config=widget.clean_config(config),
		)
		return widget.fn(ctx)

	def test_every_widget_answers_with_its_kind(self):
		for widget in registry.all_widgets():
			for user in (None, SALES_USER):
				with self.subTest(widget=widget.id, user=user):
					data = self.answer(widget.id, user)
					self.assertIsInstance(data, dict)
					self.assertIn(data["kind"], registry.KINDS)
					if not widget.retired:
						self.assertEqual(data["kind"], widget.kind)

	def test_every_widget_survives_an_empty_period(self):
		far = add_days(nowdate(), 3650)
		for widget in registry.all_widgets():
			with self.subTest(widget=widget.id):
				data = self.answer(widget.id, from_date=far, to_date=add_days(far, 30))
				self.assertIn(data["kind"], registry.KINDS)

	def test_catalogue_is_consistent(self):
		for widget in registry.all_widgets():
			with self.subTest(widget=widget.id):
				self.assertIn(widget.category, registry.CATEGORIES)
				self.assertTrue(str(widget.title))
				width, height = widget.size
				self.assertTrue(1 <= width <= 20 and 1 <= height <= 40)
