# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""The sale has one scale of states, and it lives on the deal.

A person does not carry a stage of their own, so an inquiry worth working has to
open a deal or it lands in no pipeline. These cover the one judgement that makes
it work: not a second deal while the first is open, and a new deal -- not a
resurrection of the old one -- when somebody comes back after it closed.
"""

import frappe
from frappe.tests import IntegrationTestCase

from crm.api.lead import open_deal_for_inquiry, open_deal_of


class TestInquiryOpensADeal(IntegrationTestCase):
	def tearDown(self) -> None:
		frappe.db.rollback()

	def _person(self, email="chi.torna@example.com"):
		return frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Chi",
				"last_name": "Torna",
				"email": email,
				"mobile_no": "+39 333 7654321",
			}
		).insert(ignore_permissions=True)

	def _close(self, deal: str, type: str = "Won") -> None:
		status = frappe.get_all("CRM Deal Status", filters={"type": type}, pluck="name", limit=1)
		self.assertTrue(status, f"no {type} stage on this site")
		deal = frappe.get_doc("CRM Deal", deal)
		deal.status = status[0]
		if type == "Lost":
			deal.lost_reason = frappe.get_all("CRM Lost Reason", pluck="name", limit=1)[0]
		deal.save(ignore_permissions=True)

	def test_an_inquiry_opens_a_deal_in_the_first_stage(self):
		person = self._person()
		name = open_deal_for_inquiry(person.name)

		self.assertTrue(name)
		deal = frappe.get_doc("CRM Deal", name)
		self.assertEqual(deal.lead, person.name)
		self.assertTrue(deal.status, "a deal with no stage sits in no board")
		self.assertEqual(frappe.db.get_value("CRM Lead", person.name, "converted"), 1)

	def test_a_second_inquiry_joins_the_deal_already_open(self):
		"""Two boards for one conversation is how somebody gets called twice."""
		person = self._person()
		first = open_deal_for_inquiry(person.name)
		second = open_deal_for_inquiry(person.name)

		self.assertEqual(first, second)

	def test_coming_back_after_a_closed_deal_opens_a_new_one(self):
		"""The whole point of moving the state onto the deal.

		With a single permanent status on the person, somebody who came back
		stayed marked Lost and no clock restarted. Their return is a new sale.
		"""
		person = self._person()
		first = open_deal_for_inquiry(person.name)
		self._close(first, "Lost")

		second = open_deal_for_inquiry(person.name)

		self.assertTrue(second)
		self.assertNotEqual(first, second)
		self.assertEqual(open_deal_of(person.name), second)

	def test_the_deal_says_where_the_person_came_from(self):
		"""Not decoration: `stamp_manual_source` claims for "CRM UI" any record
		a signed-in user creates that nothing else has claimed, and the hourly
		Meta reconciliation runs as one. Without carrying the snapshot over, a
		deal born from a paid ad reported as typed into the CRM by hand.
		"""
		person = self._person()
		person.db_set(
			{
				"first_touch_category": "Paid Social",
				"first_touch_source": "facebook",
				"last_touch_category": "Paid Social",
				"last_touch_source": "facebook",
			},
			update_modified=False,
		)

		deal = frappe.get_doc("CRM Deal", open_deal_for_inquiry(person.name))

		self.assertEqual(deal.first_touch_category, "Paid Social")
		self.assertEqual(deal.first_touch_source, "facebook")

	def test_forecasting_on_does_not_swallow_the_deal(self):
		"""With forecasting on, the deal controller requires an expected value
		and a closing date. Nobody can supply either from a webhook, so the
		insert was refused, the failure was swallowed into the error log, and
		the sale existed in no pipeline while the person existed fine.
		"""
		frappe.db.set_single_value("FCRM Settings", "enable_forecasting", 1)
		self.addCleanup(frappe.db.set_single_value, "FCRM Settings", "enable_forecasting", 0)

		name = open_deal_for_inquiry(self._person().name)

		self.assertTrue(name, "an inquiry with forecasting on still opens its deal")

	def test_a_person_still_has_to_forecast_by_hand(self):
		"""The exemption is for the webhook, not for the salesperson."""
		frappe.db.set_single_value("FCRM Settings", "enable_forecasting", 1)
		self.addCleanup(frappe.db.set_single_value, "FCRM Settings", "enable_forecasting", 0)

		deal = frappe.get_doc("CRM Deal", open_deal_for_inquiry(self._person().name))
		deal.next_step = "chiamare"

		with self.assertRaises(frappe.MandatoryError):
			deal.save(ignore_permissions=True)

	def test_a_person_with_no_deal_has_none_open(self):
		self.assertIsNone(open_deal_of(self._person().name))
