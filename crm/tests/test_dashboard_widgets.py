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

from crm.dashboard import features, registry
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

	def skip_if_unavailable(self, widget):
		"""Skip a widget whose app is not installed here, by the product's own rule.

		`store.availability` is what decides whether a viewer may have a widget at all,
		and a widget whose feature is off is never rendered: the dashboard shows the
		reason instead. Calling its query anyway tests a path that does not exist in
		production and fails on a table the site has no reason to own - the WhatsApp
		widgets read `tabWhatsApp Message`, which belongs to `frappe_whatsapp`, an app
		this suite does not install.

		The skip is loud on purpose: the run says which widgets went uncovered, so a
		hole in the net is visible rather than assumed away.
		"""
		assente = features.missing(widget.requires)
		if assente:
			self.skipTest(f"{widget.id}: needs {', '.join(assente)}, not available on this site")

	def answer(self, widget_id, user=None, config=None, **dates):
		widget = registry.get(widget_id)
		self.assertIsNotNone(widget, widget_id)
		self.skip_if_unavailable(widget)
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


PIPELINE = "Dashboard numbers"
MARCH = ("2025-03-01", "2025-03-31")


class TestSalesNumbers(IntegrationTestCase):
	"""Known deals in a pipeline of their own, and the numbers they must add up to.

	The period is March 2025; the one before it is the 31 days up to 28 February.
	Every widget is asked about this pipeline only, so deals made by other tests
	cannot move the numbers.
	"""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not frappe.db.exists("CRM Pipeline", PIPELINE):
			frappe.get_doc({"doctype": "CRM Pipeline", "pipeline_name": PIPELINE}).insert(
				ignore_permissions=True
			)
		for stage, kind, probability in (
			("Numbers open", "Open", 20),
			("Numbers won", "Won", 100),
			("Numbers lost", "Lost", 0),
		):
			if not frappe.db.exists("CRM Deal Status", stage):
				frappe.get_doc(
					{
						"doctype": "CRM Deal Status",
						"deal_status": stage,
						"type": kind,
						"pipeline": PIPELINE,
						"probability": probability,
					}
				).insert(ignore_permissions=True)
		if not frappe.db.exists("CRM Lost Reason", "Numbers price"):
			frappe.get_doc({"doctype": "CRM Lost Reason", "lost_reason": "Numbers price"}).insert(
				ignore_permissions=True
			)
		frappe.db.delete("CRM Deal", {"pipeline": PIPELINE})

		cls.deal("Numbers won", 1000, created="2025-02-10", closed="2025-03-05")
		cls.deal("Numbers won", 2000, created="2025-03-02", closed="2025-03-20", owner=SALES_USER)
		cls.deal("Numbers won", 3000, created="2025-03-10", closed="2025-03-31", owner=SALES_USER)
		cls.deal("Numbers won", 500, created="2025-02-01", closed="2025-02-15")
		cls.deal("Numbers lost", 800, created="2025-03-03", lost="2025-03-12")
		cls.deal("Numbers open", 4000, created="2025-03-15", expected=5000)
		cls.deal("Numbers open", 1500, created="2025-01-05")

	@classmethod
	def tearDownClass(cls):
		frappe.db.rollback()
		super().tearDownClass()

	@staticmethod
	def deal(stage, value, *, created, closed=None, lost=None, expected=None, owner="Administrator"):
		doc = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"status": stage,
				"deal_value": value,
				"expected_deal_value": expected or value,
				"expected_closure_date": closed or created,
				"deal_owner": owner,
				"lost_reason": "Numbers price" if lost else None,
			}
		).insert(ignore_permissions=True)
		# saving stamps today on everything; put the deal back where it belongs in time
		Deal = frappe.qb.DocType("CRM Deal")
		frappe.qb.update(Deal).set(Deal.creation, f"{created} 10:00:00").set(
			Deal.modified, f"{lost or closed or created} 10:00:00"
		).set(Deal.closed_date, closed).where(Deal.name == doc.name).run()
		if lost:
			Log = frappe.qb.DocType("CRM Status Change Log")
			frappe.qb.update(Log).set(Log.from_date, f"{lost} 10:00:00").where(Log.parent == doc.name).where(
				Log.from_type == "Lost"
			).run()

	def answer(self, widget_id, user=None):
		widget = registry.get(widget_id)
		ctx = Context.build(
			*MARCH,
			requested_user=user,
			scope=widget.scope,
			config=widget.clean_config({"pipeline": PIPELINE}),
		)
		return widget.fn(ctx)

	def test_won_lost_and_the_rate_between_them(self):
		won = self.answer("won_deals")
		self.assertEqual((won["value"], won["previous"]), (3, 1))
		lost = self.answer("deals_lost")
		self.assertEqual((lost["value"], lost["previous"]), (1, 0))
		# 3 won of 4 closed, against 1 of 1 before: a fall of 25 points, not of 25%
		rate = self.answer("win_rate")
		self.assertEqual((rate["value"], rate["previous"]), (75, 100))
		self.assertEqual((rate["delta"], rate["deltaUnit"]), (-25, "points"))

	def test_revenue_is_what_was_won_in_the_period(self):
		won = self.answer("won_value")
		self.assertEqual((won["value"], won["previous"]), (6000, 500))
		self.assertEqual(won["delta"], 1100)
		self.assertEqual(self.answer("average_won_deal_value")["value"], 2000)

	def test_new_deals_are_counted_when_they_were_opened(self):
		new = self.answer("deals_new")
		self.assertEqual((new["value"], new["previous"]), (4, 2))

	def test_the_open_pipeline_is_worth_what_is_expected_of_it(self):
		self.assertEqual(self.answer("deals_open")["value"], 2)
		# the expected value when there is one (5000), else the deal value (1500)
		self.assertEqual(self.answer("pipeline_value")["value"], 6500)
		self.assertEqual(self.answer("weighted_pipeline")["value"], 1300)

	def test_one_salesperson_sees_their_own_deals(self):
		self.assertEqual(self.answer("won_deals", user=SALES_USER)["value"], 2)
		self.assertEqual(self.answer("won_value", user=SALES_USER)["value"], 5000)
		self.assertEqual(self.answer("deals_open", user=SALES_USER)["value"], 0)
