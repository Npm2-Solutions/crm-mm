# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, nowdate

from crm.fcrm.doctype.crm_deal.test_crm_deal import create_test_deal
from crm.integrations.meta import insights as I


def make_account(account_id="act_1", enabled=1, currency="EUR"):
	if not frappe.db.exists("Facebook Ad Account", account_id):
		frappe.get_doc(
			{
				"doctype": "Facebook Ad Account",
				"account_id": account_id,
				"account_name": "Test Account",
				"currency": currency,
				"account_status": 1,
				"sync_enabled": enabled,
			}
		).insert(ignore_permissions=True)
	return account_id


def day_row(ad_id="120300", date=None, spend="10.00", **extra):
	row = {
		"ad_id": ad_id,
		"ad_name": "Promo Autunno",
		"adset_name": "Milano 25-45",
		"campaign_id": "23850",
		"campaign_name": "Lead Settembre",
		"spend": spend,
		"impressions": "1000",
		"clicks": "50",
		"date_start": date or nowdate(),
	}
	row.update(extra)
	return row


def make_lead(ad_id="120300", email="uno@example.com"):
	return frappe.get_doc(
		{
			"doctype": "CRM Lead",
			"first_name": "Mario",
			"email": email,
			"facebook_ad_id": ad_id,
		}
	).insert(ignore_permissions=True)


class TestMetaInsights(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_the_same_day_is_never_counted_twice(self):
		"""Meta keeps revising the last days, so we re-read them. A report that
		adds the second reading to the first is worse than no report."""
		account = make_account()
		I._store_insight(account, day_row(spend="10.00"))
		I._store_insight(account, day_row(spend="12.50"))

		rows = frappe.get_all("Facebook Ad Insight", filters={"ad_id": "120300"}, fields=["spend"])
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0].spend, 12.5)

	def test_an_ad_that_spends_without_bringing_leads_still_shows(self):
		"""That is the line worth seeing, so the rows cannot be a join on leads."""
		account = make_account()
		I._store_insight(account, day_row(ad_id="120301", spend="80.00"))

		row = next(r for r in I.performance(30)["rows"] if r["ad_id"] == "120301")
		self.assertEqual(row["spend"], 80.0)
		self.assertEqual(row["leads"], 0)
		# nothing to divide by: "0 per lead" would read as free
		self.assertIsNone(row["cost_per_lead"])

	def test_the_cost_per_customer_needs_a_customer(self):
		"""The number nobody can read off Meta: spend over deals actually won."""
		account = make_account()
		I._store_insight(account, day_row(ad_id="120302", spend="100.00"))
		lead = make_lead(ad_id="120302", email="cliente@example.com")

		row = next(r for r in I.performance(30)["rows"] if r["ad_id"] == "120302")
		self.assertEqual(row["leads"], 1)
		self.assertEqual(row["cost_per_lead"], 100.0)
		self.assertIsNone(row["cost_per_won"])

		won = frappe.db.get_value("CRM Deal Status", {"type": "Won"}, "name")
		create_test_deal(organization="Insights Org", lead=lead.name, status=won, deal_value=500)

		row = next(r for r in I.performance(30)["rows"] if r["ad_id"] == "120302")
		self.assertEqual(row["won"], 1)
		self.assertEqual(row["cost_per_won"], 100.0)
		self.assertEqual(row["revenue"], 500.0)
		self.assertEqual(row["roas"], 5.0)

	def test_spend_outside_the_window_is_not_counted(self):
		account = make_account()
		I._store_insight(account, day_row(ad_id="120303", spend="5.00"))
		I._store_insight(account, day_row(ad_id="120303", date=add_days(nowdate(), -60), spend="900.00"))

		row = next(r for r in I.performance(30)["rows"] if r["ad_id"] == "120303")
		self.assertEqual(row["spend"], 5.0)

	def test_one_account_failing_does_not_cost_the_others_their_numbers(self):
		make_account("act_broken")
		make_account("act_fine")

		def refuse_the_broken_one(account, days=7):
			if account == "act_broken":
				raise frappe.ValidationError("no role on this account")
			return 3

		# the job commits each account and rolls back the one that failed, which
		# in a test would take this test's own setup with it
		with (
			patch.object(frappe.db, "commit"),
			patch.object(frappe.db, "rollback"),
			patch.object(I, "sync_account", side_effect=refuse_the_broken_one),
		):
			read = I.sync_ad_spend()

		self.assertEqual(read.get("act_fine"), 3)
		self.assertNotIn("act_broken", read)
		self.assertTrue(frappe.db.get_value("Facebook Ad Account", "act_broken", "last_error"))

	def test_finding_an_account_does_not_switch_it_on(self):
		"""An agency user can see accounts that have nothing to do with this CRM:
		the list is an offer, not a decision."""
		with (
			patch.object(I, "user_token", return_value="tok"),
			patch.object(
				I,
				"graph_get_paginated",
				return_value=iter([{"id": "act_new", "name": "Somebody Else", "currency": "USD"}]),
			),
		):
			I.discover_accounts()

		self.assertEqual(frappe.db.get_value("Facebook Ad Account", "act_new", "sync_enabled"), 0)

	def test_finding_accounts_again_keeps_the_choice(self):
		"""Refreshing the list must not silently re-read an account somebody
		switched off, nor switch off one they wanted."""
		make_account("act_chosen", enabled=1)
		with (
			patch.object(I, "user_token", return_value="tok"),
			patch.object(
				I,
				"graph_get_paginated",
				return_value=iter([{"id": "act_chosen", "name": "Renamed", "currency": "EUR"}]),
			),
		):
			I.discover_accounts()

		self.assertEqual(frappe.db.get_value("Facebook Ad Account", "act_chosen", "sync_enabled"), 1)
		self.assertEqual(frappe.db.get_value("Facebook Ad Account", "act_chosen", "account_name"), "Renamed")

	def test_a_mixed_currency_total_says_so(self):
		"""Summing euros and dollars produces a confident number that means
		nothing. It is still shown, but it is flagged."""
		make_account("act_eur", currency="EUR")
		make_account("act_usd", currency="USD")
		I._store_insight("act_eur", day_row(ad_id="120304", spend="10.00"))
		I._store_insight("act_usd", day_row(ad_id="120305", spend="10.00"))

		totals = I.performance(30)["totals"]
		self.assertTrue(totals["mixed_currencies"])
		self.assertEqual(totals["currency"], "")


class TestMetaAds(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_the_creative_is_asked_once_a_month(self):
		"""The picture and the words of an ad do not change; asking every time a
		lead is opened would spend a call per page view."""
		from crm.integrations.meta import ads as A

		answer = {
			"name": "Promo Autunno",
			"preview_shareable_link": "https://facebook.com/ads/preview",
			"creative": {
				"title": "Sconto 20%",
				"body": "Solo questo mese",
				"thumbnail_url": "https://cdn/x.jpg",
			},
		}
		# ads.py asks insights.py for the token at call time, so that is the one
		# a test has to answer for
		with (
			patch("crm.integrations.meta.insights.user_token", return_value="tok"),
			patch.object(A, "graph_get", return_value=answer) as graph_get,
		):
			first = A.read_creative("120400")
			second = A.read_creative("120400")

		self.assertEqual(graph_get.call_count, 1)
		self.assertEqual(first["creative_title"], "Sconto 20%")
		self.assertEqual(second["creative_body"], "Solo questo mese")

	def test_a_refused_creative_does_not_break_the_lead_screen(self):
		from crm.integrations.meta import ads as A

		with (
			patch("crm.integrations.meta.insights.user_token", return_value="tok"),
			patch.object(A, "graph_get", side_effect=Exception("no ads access")),
		):
			self.assertEqual(A.read_creative("120401"), {})

	def test_only_ads_that_were_working_are_reported_as_stopped(self):
		"""An old paused ad is housekeeping. An ad that brought leads this month
		and is now rejected is money and leads stopping."""
		from crm.integrations.meta import ads as A

		A._remember("120402", {"ad_name": "Vecchia", "effective_status": "PAUSED"})
		A._remember("120403", {"ad_name": "Rifiutata", "effective_status": "DISAPPROVED"})
		make_lead(ad_id="120403", email="fermata@example.com")

		stopped = {row["ad_id"] for row in A.stopped_ads(30)}
		self.assertIn("120403", stopped)
		self.assertNotIn("120402", stopped)

	def test_a_deal_shows_the_ad_of_its_lead(self):
		from crm.integrations.meta import ads as A

		lead = make_lead(ad_id="120404", email="trattativa@example.com")
		deal = create_test_deal(organization="Ad Card Org", lead=lead.name)

		self.assertEqual(A.ad_of_record("CRM Deal", deal.name), "120404")
		self.assertEqual(A.ad_of_record("CRM Lead", lead.name), "120404")
		self.assertEqual(A.ad_of_record("Contact", "whatever"), "")
