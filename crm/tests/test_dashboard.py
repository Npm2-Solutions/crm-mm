# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt


import frappe
from frappe.tests import IntegrationTestCase
from frappe.tests.utils import make_test_records
from frappe.utils import add_days, get_first_day, get_last_day, nowdate

from crm.api.dashboard import (
	get_average_deal_value,
	get_average_ongoing_deal_value,
	get_average_time_to_close_a_deal,
	get_average_time_to_close_a_lead,
	get_average_won_deal_value,
	get_base_currency_symbol,
	get_chart,
	get_dashboard,
	get_deal_status_change_counts,
	get_deals_by_salesperson,
	get_deals_by_source,
	get_deals_by_stage_axis,
	get_deals_by_stage_donut,
	get_deals_by_territory,
	get_forecasted_revenue,
	get_funnel_conversion,
	get_leads_by_source,
	get_lost_deal_reasons,
	get_ongoing_deals,
	get_sales_trend,
	get_total_leads,
	get_won_deals,
)


class TestDashboard(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		"""Set up test records once for all tests"""
		super().setUpClass()

		# Mark timestamp before creating test data
		cls.test_start_time = frappe.utils.now()

		cls.from_date = get_first_day(nowdate())
		cls.to_date = get_last_day(nowdate())
		cls.user = "crm.manager@example.com"  # CRM manager from test_records.json
		cls.user2_email = "crm.user1@example.com"  # Test user from test_records.json

		# Load test records from test_records.json files in dependency order
		make_test_records("CRM Lead Status")
		make_test_records("CRM Deal Status")
		make_test_records("CRM Lead Source")
		make_test_records("CRM Lost Reason")
		make_test_records("CRM Organization")  # Load organizations before deals
		make_test_records("CRM Lead")
		make_test_records("CRM Deal")

		# Leads this class creates itself, which is what the lead assertions are
		# written against.
		#
		# The month is not this class's alone: other modules commit leads that
		# outlive their own rollback (the first CI run of this file found 37
		# leads in a month whose fixtures hold 35), and get_dashboard() commits
		# again while it writes the default dashboard, so a fixed total was
		# never going to hold. Counting the window a second time would not fix
		# it either — that only proves two queries agree, not that the dashboard
		# picked the right rows. So the class reads what each metric says before
		# it inserts anything, inserts leads it fully describes below, and then
		# requires each metric to have moved by exactly those leads, both
		# unfiltered and filtered to an owner no other fixture uses.
		cls.lead_owner = "crm.user2@example.com"  # owns no record in test_records.json

		# source, creation (None = now), and whether the window should hold it.
		# The two outside it sit a single day beyond each edge and carry a source
		# of their own, so a metric that stopped filtering by date would show up
		# twice over: in the totals, and as Cold Call leads appearing in a window
		# this class never put any in.
		cls.own_leads = [
			("Website", None, True),
			("Website", cls.from_date, True),  # first moment of the window
			("Referral", f"{cls.to_date} 23:59:59", True),  # last moment of the window
			("Cold Call", add_days(cls.from_date, -1), False),  # the day before it
			("Cold Call", add_days(cls.to_date, 1), False),  # the day after it
		]
		cls.own_leads_by_source = {source: 0 for source, _, _ in cls.own_leads}
		for source, _, inside_window in cls.own_leads:
			cls.own_leads_by_source[source] += int(inside_window)
		cls.own_leads_in_window = sum(cls.own_leads_by_source.values())

		cls.leads_before_all = cls._lead_metrics()
		cls.leads_before_owner = cls._lead_metrics(cls.lead_owner)
		cls._make_own_leads()

	@classmethod
	def _lead_metrics(cls, user: str | None = None):
		"""What each lead metric of the dashboard reports for this window.

		Taken once before the class inserts its own leads and compared against
		afterwards: every lead assertion is a before/after of the same metric
		across a change this test made, which is the only thing about the row
		set it actually controls.
		"""
		return {
			"total": get_total_leads(cls.from_date, cls.to_date, user)["value"],
			"chart": get_chart("total_leads", "number", cls.from_date, cls.to_date, user)["value"],
			"funnel": get_funnel_conversion(cls.from_date, cls.to_date, user)["data"][0]["count"],
			"by_source": {
				row["source"]: row["count"]
				for row in get_leads_by_source(cls.from_date, cls.to_date, user)["data"]
			},
		}

	@classmethod
	def _make_own_leads(cls):
		"""Insert the leads described by `cls.own_leads`, one owner, one email each.

		`creation` is stamped by Frappe on insert, so the leads that belong to a
		particular day are moved there afterwards.
		"""
		for i, (source, creation, _) in enumerate(cls.own_leads):
			lead = frappe.get_doc(
				{
					"doctype": "CRM Lead",
					"first_name": "Dashboard",
					"last_name": f"Fixture {i}",
					"email": f"dashboard.fixture{i}@example.com",
					"mobile_no": f"+1-555-99{i:02d}",
					"source": source,
					"status": "New Lead",
					"lead_owner": cls.lead_owner,
				}
			).insert(ignore_permissions=True)

			if creation:
				frappe.db.set_value("CRM Lead", lead.name, "creation", creation, update_modified=False)

	@classmethod
	def tearDownClass(cls):
		"""Clean up test records after all tests"""
		frappe.db.rollback()
		super().tearDownClass()

	def assertLeadsBySource(self, data, before, message):
		"""The per-source counts moved by this class's leads and nothing else.

		Every source is checked: the two it added leads to, the Cold Call it
		expects no movement from because those leads are dated outside the
		window, and any source the site already had.
		"""
		now = {row["source"]: row["count"] for row in data}
		for source in set(now) | set(before) | set(self.own_leads_by_source):
			self.assertEqual(
				now.get(source, 0) - before.get(source, 0),
				self.own_leads_by_source.get(source, 0),
				f"{message}: leads from {source} moved by the wrong amount",
			)

	def test_get_total_leads(self):
		"""Test get_total_leads returns correct lead count and delta calculation"""
		result = get_total_leads(self.from_date, self.to_date)

		# Verify actual count from test data
		self.assertEqual(result["title"], "Total leads")
		self.assertIsInstance(result["delta"], (int, float))
		self.assertEqual(result["deltaSuffix"], "%")

		# The three leads this class put inside the window are counted; the two
		# it put a day on either side of it are not.
		self.assertEqual(
			result["value"],
			self.leads_before_all["total"] + self.own_leads_in_window,
			"total leads did not move by exactly the leads created inside the window",
		)

		# and filtered to their owner, those three are all there is
		result_owner = get_total_leads(self.from_date, self.to_date, self.lead_owner)
		self.assertEqual(result_owner["value"], self.leads_before_owner["total"] + self.own_leads_in_window)

		# Test with user filter - crm.user1@example.com owns 3 leads
		result_user = get_total_leads(self.from_date, self.to_date, self.user2_email)
		self.assertEqual(result_user["value"], 3)

		# Verify each owner's leads are a subset of the total
		self.assertGreater(result["value"], result_user["value"])
		self.assertGreaterEqual(result["value"], result_user["value"] + result_owner["value"])

	def test_get_ongoing_deals(self):
		"""Test get_ongoing_deals returns correct non-won/lost deal count"""
		result = get_ongoing_deals(self.from_date, self.to_date)

		# Verify actual count: 13 Qualification + 8 Negotiation = 21
		self.assertEqual(result["title"], "Ongoing deals")
		self.assertEqual(result["value"], 21)

		# Verify it's not counting won/lost deals
		all_deals = frappe.db.count("CRM Deal")
		self.assertLess(result["value"], all_deals)

		# Test with user filter - crm.user1@example.com owns 2 ongoing deals
		result_user = get_ongoing_deals(self.from_date, self.to_date, self.user2_email)
		self.assertEqual(result_user["value"], 2)

		# Verify user owns subset of ongoing deals
		self.assertLess(result_user["value"], result["value"])

	def test_get_average_ongoing_deal_value(self):
		"""Test get_average_ongoing_deal_value calculates correct average"""
		result = get_average_ongoing_deal_value(self.from_date, self.to_date)

		self.assertEqual(result["title"], "Avg. ongoing deal value")

		# Expected average of ongoing deals (13 Qualification + 8 Negotiation = 21 deals)
		# Qualification: 50k,75k,100k,25k,80k,60k,90k,45k,70k,55k,85k,65k,95k = 895,000 / 13 = 68,846.15
		# Negotiation: 120k,110k,130k,105k,115k,125k,140k,135k = 980,000 / 8 = 122,500
		# Combined: 1,875,000 / 21 = 89,285.71
		expected_avg = 89285.71
		self.assertAlmostEqual(result["value"], expected_avg, places=2)
		self.assertIsNotNone(result["prefix"])  # Should have currency symbol
		self.assertIsInstance(result["delta"], (int, float))

		# Test with user filter - crm.user1@example.com owns 2 ongoing deals
		result_user = get_average_ongoing_deal_value(self.from_date, self.to_date, self.user2_email)
		# User1 has 2 deals: Cloud Systems (90k) + Smart Solutions (70k) = 160k / 2 = 80,000
		expected_user_avg = 80000.0
		self.assertAlmostEqual(result_user["value"], expected_user_avg, places=2)

		# Both should have same currency symbol
		self.assertEqual(result["prefix"], result_user["prefix"])

	def test_get_won_deals(self):
		"""Test get_won_deals returns correct won deal count"""
		result = get_won_deals(self.from_date, self.to_date)

		self.assertEqual(result["title"], "Won deals")
		self.assertEqual(result["value"], 8)  # 8 won deals from test_records.json
		self.assertIsNotNone(result.get("tooltip"))

		# Verify won deals is less than total deals
		ongoing_result = get_ongoing_deals(self.from_date, self.to_date)
		total_won_and_ongoing = result["value"] + ongoing_result["value"]
		all_deals = frappe.db.count("CRM Deal")
		self.assertLessEqual(total_won_and_ongoing, all_deals)

		# Test with user filter - crm.user1@example.com owns 0 won deals
		result_user = get_won_deals(self.from_date, self.to_date, self.user2_email)
		self.assertEqual(result_user["value"], 0)

		# User owns no won deals but has ongoing deals
		ongoing_user = get_ongoing_deals(self.from_date, self.to_date, self.user2_email)
		self.assertGreater(ongoing_user["value"], result_user["value"])

	def test_get_average_won_deal_value(self):
		"""Test get_average_won_deal_value calculates correct average for won deals"""
		result = get_average_won_deal_value(self.from_date, self.to_date)

		self.assertEqual(result["title"], "Avg. won deal value")

		# Expected average of won deals: 8 deals
		# 150k,160k,145k,170k,155k,165k,175k,180k = 1,300,000 / 8 = 162,500
		expected_avg = 162500.0
		won_count = get_won_deals(self.from_date, self.to_date)["value"]
		if won_count > 0:
			self.assertAlmostEqual(result["value"], expected_avg, places=2)
		else:
			self.assertEqual(result["value"], 0)

		# Test with user filter - user2 has no won deals
		result_user = get_average_won_deal_value(self.from_date, self.to_date, self.user2_email)
		self.assertEqual(result_user["value"], 0)  # No won deals = 0 average

		# Verify currency consistency
		self.assertEqual(result["prefix"], result_user["prefix"])

	def test_get_average_deal_value(self):
		"""Test get_average_deal_value for all non-lost deals includes won + ongoing"""
		result = get_average_deal_value(self.from_date, self.to_date)

		self.assertEqual(result["title"], "Avg. deal value")

		# Expected average: Ongoing (21 deals: 13 Qualification + 8 Negotiation, $1,875k) + Won (8 deals, $1,300k)
		# Total: 29 non-lost deals, $3,175k / 29 = 109,482.76
		expected_avg = 109482.76
		self.assertAlmostEqual(result["value"], expected_avg, places=2)

		self.assertIn(
			"ongoing & won", result["tooltip"].lower()
		)  # Verify tooltip describes ongoing & won deals

		# Test with user filter - crm.user1@example.com owns 2 ongoing deals (no won)
		result_user = get_average_deal_value(self.from_date, self.to_date, self.user2_email)
		# User1 has 2 ongoing deals: 90k + 70k = 160k / 2 = 80,000
		expected_user_avg = 80000.0
		self.assertAlmostEqual(result_user["value"], expected_user_avg, places=2)

	def test_get_average_time_to_close_a_lead(self):
		"""Test get_average_time_to_close_a_lead calculates time from lead creation"""
		result = get_average_time_to_close_a_lead(self.from_date, self.to_date)

		self.assertEqual(result["title"], "Avg. time to close a lead")
		self.assertEqual(result["value"], 0)  # Test records created on same day
		self.assertEqual(result["suffix"], " days")

		# Test with user filter
		result_user = get_average_time_to_close_a_lead(self.from_date, self.to_date, self.user2_email)
		self.assertEqual(result_user["value"], 0)  # Test records created on same day

	def test_get_average_time_to_close_a_deal(self):
		"""Test get_average_time_to_close_a_deal calculates time from deal creation"""
		result = get_average_time_to_close_a_deal(self.from_date, self.to_date)

		self.assertEqual(result["title"], "Avg. time to close a deal")
		self.assertEqual(result["value"], 0)  # Test records created on same day
		self.assertEqual(result.get("suffix", ""), " days")

		# Test with user filter
		result_user = get_average_time_to_close_a_deal(self.from_date, self.to_date, self.user2_email)
		self.assertEqual(result_user["value"], 0)  # Test records created on same day

	def test_get_sales_trend(self):
		"""Test get_sales_trend returns correct time series data"""
		result = get_sales_trend(self.from_date, self.to_date)

		self.assertEqual(result["title"], "Sales trend")
		self.assertEqual(len(result["series"]), 3)  # leads, deals, won_deals
		self.assertEqual(result["series"][0]["name"], "leads")
		self.assertEqual(result["series"][1]["name"], "deals")
		self.assertEqual(result["series"][2]["name"], "won_deals")

		# Verify data points exist
		self.assertIsInstance(result["data"], list)
		if len(result["data"]) > 0:
			# Each data point should have date and values
			first_point = result["data"][0]
			self.assertIsInstance(first_point, dict)

		# Test with user filter
		result_user = get_sales_trend(self.from_date, self.to_date, self.user2_email)
		self.assertIn("data", result_user)
		self.assertEqual(len(result_user["series"]), 3)

		# User data should be subset of total data
		self.assertLessEqual(len(result_user["data"]), len(result["data"]) if result["data"] else 0)

	def test_get_forecasted_revenue(self):
		"""Test get_forecasted_revenue returns forecasted vs actual revenue comparison"""
		result = get_forecasted_revenue(self.from_date, self.to_date)

		self.assertEqual(result["title"], "Forecasted revenue")

		# Should have both forecasted and actual series
		if result["series"]:
			series_names = [s["name"] for s in result["series"]]
			self.assertIn("forecasted", series_names)
			self.assertIn("actual", series_names)

		result_user = get_forecasted_revenue(self.from_date, self.to_date, self.user2_email)
		self.assertIn("data", result_user)
		self.assertIn("series", result_user)

	def test_get_funnel_conversion(self):
		"""Test get_funnel_conversion returns correct pipeline funnel data"""
		result = get_funnel_conversion(self.from_date, self.to_date)

		self.assertEqual(result["title"], "Funnel conversion")
		self.assertGreater(len(result["data"]), 0)

		# Verify funnel starts with Leads, and that its first stage gained
		# exactly the leads this class created inside the window
		self.assertEqual(result["data"][0]["stage"], "Leads")
		self.assertEqual(
			result["data"][0]["count"],
			self.leads_before_all["funnel"] + self.own_leads_in_window,
		)

		# Verify funnel stages are in order and counts decrease or stay same (funnel effect)
		for i in range(len(result["data"]) - 1):
			current_count = result["data"][i]["count"]
			next_count = result["data"][i + 1]["count"]
			# Each stage should have equal or fewer than previous (funnel narrows)
			self.assertGreaterEqual(
				current_count,
				next_count,
				f"Funnel should narrow or stay same: {result['data'][i]['stage']} ({current_count}) should be >= {result['data'][i + 1]['stage']} ({next_count})",
			)

		# Test with user filter - crm.user1@example.com owns 3 leads
		result_user = get_funnel_conversion(self.from_date, self.to_date, self.user2_email)
		self.assertIn("data", result_user)
		self.assertGreater(len(result_user["data"]), 0)
		self.assertEqual(result_user["data"][0]["stage"], "Leads")
		self.assertEqual(result_user["data"][0]["count"], 3)

		# Scoped to the owner of this class's leads, the funnel opens on exactly
		# the three of them that belong to the window
		result_owner = get_funnel_conversion(self.from_date, self.to_date, self.lead_owner)
		self.assertEqual(
			result_owner["data"][0]["count"],
			self.leads_before_owner["funnel"] + self.own_leads_in_window,
		)

		# User's funnel should be subset of total
		for i in range(min(len(result["data"]), len(result_user["data"]))):
			self.assertLessEqual(result_user["data"][i]["count"], result["data"][i]["count"])

	def test_get_deals_by_stage_axis(self):
		"""Test get_deals_by_stage_axis returns deal distribution by stage"""
		result = get_deals_by_stage_axis(self.from_date, self.to_date)

		self.assertEqual(result["title"], "Deals by ongoing & won stage")

		# Should have data for stages
		if result["data"]:
			# Each entry should have stage name and count
			for entry in result["data"]:
				self.assertIn("stage", entry)
				self.assertIn("count", entry)  # API uses 'count' not 'deals'
				self.assertGreater(entry["count"], 0)

		result_user = get_deals_by_stage_axis(self.from_date, self.to_date, self.user2_email)
		self.assertIsInstance(result_user["data"], list)

	def test_get_deals_by_stage_donut(self):
		"""Test get_deals_by_stage_donut returns proper donut chart data"""
		result = get_deals_by_stage_donut(self.from_date, self.to_date)

		self.assertEqual(result["title"], "Deals by stage")

		# Donut chart should have proper structure
		if result["data"]:
			total_count = sum(
				entry.get("count", 0) for entry in result["data"]
			)  # API uses 'count' not 'deals'
			self.assertGreater(total_count, 0)

		result_user = get_deals_by_stage_donut(self.from_date, self.to_date, self.user2_email)
		self.assertIsInstance(result_user["data"], list)

	def test_get_lost_deal_reasons(self):
		"""Test get_lost_deal_reasons returns distribution of loss reasons"""
		result = get_lost_deal_reasons(self.from_date, self.to_date)

		self.assertEqual(result["title"], "Lost deal reasons")

		# Lost reasons only apply to lost deals
		if result["data"]:
			for entry in result["data"]:
				self.assertIn("reason", entry)
				self.assertIn("count", entry)

		result_user = get_lost_deal_reasons(self.from_date, self.to_date, self.user2_email)
		self.assertIsInstance(result_user["data"], list)

	def test_get_leads_by_source(self):
		"""Test get_leads_by_source returns source distribution"""
		result = get_leads_by_source(self.from_date, self.to_date)

		self.assertEqual(result["title"], "Leads by source")

		# Two Website leads and one Referral lead joined the window; the two
		# Cold Call leads did not, because they are dated outside it
		self.assertLeadsBySource(result["data"], self.leads_before_all["by_source"], "all leads")

		result_owner = get_leads_by_source(self.from_date, self.to_date, self.lead_owner)
		self.assertLeadsBySource(
			result_owner["data"], self.leads_before_owner["by_source"], "leads of one owner"
		)
		self.assertEqual(
			sum(entry.get("count", 0) for entry in result_owner["data"]),
			sum(self.leads_before_owner["by_source"].values()) + self.own_leads_in_window,
		)

		result_user = get_leads_by_source(self.from_date, self.to_date, self.user2_email)
		user_total = sum(entry.get("count", 0) for entry in result_user["data"])  # API uses 'count'
		self.assertEqual(user_total, 3)  # user1 owns 3 leads

	def test_get_deals_by_source(self):
		"""Test get_deals_by_source returns source distribution"""
		result = get_deals_by_source(self.from_date, self.to_date)

		self.assertEqual(result["title"], "Deals by source")
		self.assertIsInstance(result["data"], list)

		result_user = get_deals_by_source(self.from_date, self.to_date, self.user2_email)
		self.assertIsInstance(result_user["data"], list)

	def test_get_deals_by_territory(self):
		"""Test get_deals_by_territory returns geographic distribution"""
		result = get_deals_by_territory(self.from_date, self.to_date)

		self.assertEqual(result["title"], "Deals by territory")
		self.assertIsInstance(result["data"], list)

		result_user = get_deals_by_territory(self.from_date, self.to_date, self.user2_email)
		self.assertIsInstance(result_user["data"], list)

	def test_get_deals_by_salesperson(self):
		"""Test get_deals_by_salesperson returns per-user performance"""
		result = get_deals_by_salesperson(self.from_date, self.to_date)

		self.assertEqual(result["title"], "Deals by salesperson")

		# Should show different salespeople
		if result["data"]:
			for entry in result["data"]:
				self.assertIn("salesperson", entry)
				self.assertIn("deals", entry)

		result_user = get_deals_by_salesperson(self.from_date, self.to_date, self.user2_email)
		self.assertIn("data", result_user)

	def test_get_base_currency_symbol(self):
		"""Test get_base_currency_symbol returns correct currency symbol"""
		# Set USD as base currency
		if not frappe.db.exists("FCRM Settings"):
			frappe.get_doc(
				{
					"doctype": "FCRM Settings",
					"currency": "USD",
				}
			).insert()
		else:
			frappe.db.set_single_value("FCRM Settings", "currency", "USD")

		symbol = get_base_currency_symbol()

		self.assertIsNotNone(symbol)
		self.assertIsInstance(symbol, str)
		self.assertGreater(len(symbol), 0)  # Should not be empty
		# Common currency symbols
		self.assertIn(symbol, ["$", "€", "£", "¥", "₹", "USD"])

	def test_get_dashboard(self):
		"""Test get_dashboard returns complete layout with valid data"""
		result = get_dashboard(self.from_date, self.to_date)

		self.assertIsInstance(result, list)
		self.assertGreater(len(result), 0)  # Should have layout items

		# Each layout item should have required fields
		for item in result:
			self.assertIn("name", item)
			self.assertIsInstance(item["name"], str)
			self.assertTrue(item["name"])  # Name should not be empty

	def test_get_chart(self):
		"""Test get_chart returns correct chart data for valid chart names"""
		result = get_chart("total_leads", "number", self.from_date, self.to_date)

		self.assertEqual(result["value"], self.leads_before_all["chart"] + self.own_leads_in_window)
		# and "total_leads" is dispatched to the metric of that name
		self.assertEqual(result["value"], get_total_leads(self.from_date, self.to_date)["value"])
		self.assertIsInstance(result["value"], (int, float))
		self.assertIsNotNone(result.get("title"))

		# the chart carries the user filter through to the metric it dispatches to
		result_owner = get_chart("total_leads", "number", self.from_date, self.to_date, self.lead_owner)
		self.assertEqual(result_owner["value"], self.leads_before_owner["chart"] + self.own_leads_in_window)

	def test_get_chart_invalid_name(self):
		"""Test get_chart returns proper error for invalid chart name"""
		result = get_chart("invalid_chart_name", "number", self.from_date, self.to_date)

		self.assertIsNotNone(result.get("error"))
		self.assertGreater(len(result["error"]), 0)

	def test_get_deal_status_change_counts(self):
		"""Test get_deal_status_change_counts returns status transition data"""
		result = get_deal_status_change_counts(self.from_date, self.to_date)

		self.assertIsInstance(result, list)
		# May be empty if no status changes recorded
		if result:
			for entry in result:
				self.assertIsInstance(entry, dict)

	def test_user_filtering_isolation(self):
		"""Test that user filtering correctly isolates data across metrics"""
		result_crm_user = get_total_leads(self.from_date, self.to_date, self.user2_email)
		result_owner = get_total_leads(self.from_date, self.to_date, self.lead_owner)
		result_all = get_total_leads(self.from_date, self.to_date, "")

		# Two owners, two disjoint sets of leads, neither leaking into the other:
		# three from test_records.json for one, three created by this class for
		# the other, and both inside the unfiltered total
		self.assertEqual(result_crm_user["value"], 3)  # crm.user1@example.com owns 3 leads
		self.assertEqual(result_owner["value"], self.leads_before_owner["total"] + self.own_leads_in_window)
		self.assertEqual(result_all["value"], self.leads_before_all["total"] + self.own_leads_in_window)
		self.assertGreater(result_all["value"], result_crm_user["value"])
		self.assertGreaterEqual(result_all["value"], result_crm_user["value"] + result_owner["value"])

	def test_date_range_filtering(self):
		"""Test that date range filtering works correctly"""
		result_current = get_total_leads(self.from_date, self.to_date)

		self.assertIsNotNone(result_current["value"])
		self.assertGreater(result_current["value"], 0)  # Should have leads created

	# ============================================================
	# EDGE CASE TESTS - Testing boundary conditions and errors
	# ============================================================

	def test_empty_date_range(self):
		"""Test behavior with empty/future date range"""
		# Future date range with no data
		future_start = add_days(nowdate(), 365)
		future_end = add_days(nowdate(), 400)

		result = get_total_leads(future_start, future_end)
		self.assertEqual(result["value"], 0)

		# Should handle gracefully without errors
		result_deals = get_ongoing_deals(future_start, future_end)
		self.assertEqual(result_deals["value"], 0)

	def test_invalid_date_order(self):
		"""Test with end date before start date"""
		# Swap dates - end before start
		result = get_total_leads(self.to_date, self.from_date)

		# Should still work (function handles it)
		self.assertIsInstance(result["value"], (int, float))

	def test_nonexistent_user_filter(self):
		"""Test filtering by non-existent user"""
		result = get_total_leads(self.from_date, self.to_date, "nonexistent@example.com")

		# Should return 0 for non-existent user
		self.assertEqual(result["value"], 0)

	def test_chart_with_empty_name(self):
		"""Test get_chart with empty chart name"""
		result = get_chart("", "number", self.from_date, self.to_date)

		self.assertIsNotNone(result.get("error"))

	def test_chart_with_none_values(self):
		"""Test get_chart handles None parameters gracefully"""
		result = get_chart("total_leads", "number", None, None)

		# Should handle gracefully
		self.assertTrue("value" in result or "error" in result)

	# ============================================================
	# BUSINESS LOGIC VALIDATION TESTS
	# ============================================================

	def test_deal_counts_consistency(self):
		"""Test that ongoing + won + lost deals = total deals"""
		ongoing = get_ongoing_deals(self.from_date, self.to_date)["value"]
		won = get_won_deals(self.from_date, self.to_date)["value"]

		# Get lost deals count
		lost_deals = frappe.db.count(
			"CRM Deal",
			{
				"creation": ["between", [self.from_date, self.to_date]],
				"status": ["in", frappe.db.get_list("CRM Deal Status", {"type": "Lost"}, pluck="name")],
			},
		)

		total_deals_by_type = ongoing + won + lost_deals
		total_deals = frappe.db.count("CRM Deal", {"creation": ["between", [self.from_date, self.to_date]]})

		# Total should match sum of all deal types
		self.assertEqual(
			total_deals_by_type,
			total_deals,
			f"Deal count mismatch: ongoing({ongoing}) + won({won}) + lost({lost_deals}) = {total_deals_by_type}, but total is {total_deals}",
		)

	def test_average_values_are_reasonable(self):
		"""Test that calculated averages match expected values from test data"""
		avg_ongoing = get_average_ongoing_deal_value(self.from_date, self.to_date)["value"]
		avg_won = get_average_won_deal_value(self.from_date, self.to_date)["value"]
		avg_all = get_average_deal_value(self.from_date, self.to_date)["value"]

		# Verify calculated averages match expected values
		self.assertAlmostEqual(avg_ongoing, 89285.71, places=2)  # $1,875,000 / 21 ongoing deals
		self.assertAlmostEqual(avg_won, 162500.0, places=2)  # $1,300,000 / 8 won deals
		self.assertAlmostEqual(avg_all, 109482.76, places=2)  # $3,175,000 / 29 non-lost deals

		# Business logic: won deals should have higher average than ongoing
		self.assertGreater(avg_won, avg_ongoing, "Won deals should have higher average than ongoing")

		# Average of all should be between ongoing and won
		self.assertGreater(avg_all, avg_ongoing, "All deals average should be greater than ongoing only")
		self.assertLess(avg_all, avg_won, "All deals average should be less than won only")

	def test_delta_calculation_logic(self):
		"""Test that delta values represent actual change"""
		result = get_total_leads(self.from_date, self.to_date)

		# Delta should exist and be a number
		self.assertIn("delta", result)
		self.assertIsInstance(result["delta"], (int, float))

		# Delta suffix should indicate percentage
		if "deltaSuffix" in result:
			self.assertEqual(result["deltaSuffix"], "%")

	def test_currency_symbol_consistency(self):
		"""Test that all value-based metrics use same currency symbol"""
		symbol1 = get_average_ongoing_deal_value(self.from_date, self.to_date).get("prefix")
		symbol2 = get_average_won_deal_value(self.from_date, self.to_date).get("prefix")
		symbol3 = get_average_deal_value(self.from_date, self.to_date).get("prefix")
		symbol4 = get_base_currency_symbol()

		# All should use same currency
		self.assertEqual(symbol1, symbol2)
		self.assertEqual(symbol2, symbol3)
		self.assertEqual(symbol3, symbol4)

	def test_user_isolation_across_multiple_metrics(self):
		"""Test that user filtering works consistently across all metrics"""
		user = self.user2_email

		# Get counts for user
		user_leads = get_total_leads(self.from_date, self.to_date, user)["value"]
		user_ongoing = get_ongoing_deals(self.from_date, self.to_date, user)["value"]
		user_won = get_won_deals(self.from_date, self.to_date, user)["value"]

		# Get total counts
		total_leads = get_total_leads(self.from_date, self.to_date)["value"]
		total_ongoing = get_ongoing_deals(self.from_date, self.to_date)["value"]
		total_won = get_won_deals(self.from_date, self.to_date)["value"]

		# User counts should be subset of totals
		self.assertLessEqual(user_leads, total_leads)
		self.assertLessEqual(user_ongoing, total_ongoing)
		self.assertLessEqual(user_won, total_won)

		# Verify specific user data matches expected
		self.assertEqual(user_leads, 3)  # crm.user1 owns 3 leads
		self.assertEqual(user_ongoing, 2)  # crm.user1 owns 2 ongoing deals
		self.assertEqual(user_won, 0)  # crm.user1 owns 0 won deals

	def test_time_to_close_calculations(self):
		"""Test that time to close metrics calculate correctly"""
		lead_time = get_average_time_to_close_a_lead(self.from_date, self.to_date)
		deal_time = get_average_time_to_close_a_deal(self.from_date, self.to_date)

		# Should have correct structure
		self.assertIn("value", lead_time)
		self.assertIn("suffix", lead_time)
		self.assertEqual(lead_time["suffix"], " days")

		self.assertIn("value", deal_time)
		self.assertIn("suffix", deal_time)
		self.assertEqual(deal_time["suffix"], " days")

		# Values should be non-negative
		self.assertGreaterEqual(lead_time["value"], 0)
		self.assertGreaterEqual(deal_time["value"], 0)

		# negativeIsBetter flag should be present (faster is better)
		if "negativeIsBetter" in lead_time:
			self.assertTrue(lead_time["negativeIsBetter"])
		if "negativeIsBetter" in deal_time:
			self.assertTrue(deal_time["negativeIsBetter"])

	def test_chart_data_types(self):
		"""Test that chart types return appropriate data structures"""
		# Number chart
		number_chart = get_chart("total_leads", "number", self.from_date, self.to_date)
		self.assertIn("value", number_chart)
		self.assertIsInstance(number_chart["value"], (int, float))

		# Test with different chart names
		charts = ["ongoing_deals", "won_deals", "total_leads"]
		for chart_name in charts:
			result = get_chart(chart_name, "number", self.from_date, self.to_date)
			self.assertIn("value", result, f"Chart {chart_name} missing value")
			self.assertIsInstance(result["value"], (int, float), f"Chart {chart_name} value not numeric")

	def test_dashboard_layout_structure(self):
		"""Test that dashboard returns valid layout with all required fields"""
		dashboard = get_dashboard(self.from_date, self.to_date)

		# Should be list of layout items
		self.assertIsInstance(dashboard, list)

		# Each item should have required fields
		for item in dashboard:
			self.assertIn("name", item)
			# Validate name is not empty
			self.assertTrue(item["name"])
