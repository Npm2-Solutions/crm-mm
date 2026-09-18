# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.integrations.meta import conversions as C


def turn_on(dataset="999000", enabled=1):
	settings = frappe.get_doc("CRM Meta Settings")
	settings.conversions_enabled = enabled
	settings.conversions_dataset_id = dataset
	settings.user_access_token = "user-token"
	settings.save(ignore_permissions=True)
	frappe.clear_cache(doctype="CRM Meta Settings")
	return settings


def a_lead(email="capi@example.com", lead_id="7790001", status=None):
	values = {
		"doctype": "CRM Lead",
		"first_name": "Mario",
		"email": email,
		"facebook_lead_id": lead_id,
	}
	if status:
		values["status"] = status
	return frappe.get_doc(values).insert(ignore_permissions=True)


class TestMetaConversions(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()
		frappe.clear_cache(doctype="CRM Meta Settings")

	def test_nothing_leaves_while_it_is_switched_off(self):
		"""Off means off: a queue filling up in the background would surprise
		somebody later with months of history in one batch."""
		turn_on(enabled=0)
		lead = a_lead()
		self.assertFalse(frappe.db.exists("Meta Conversion Event", {"lead": lead.name}))

	def test_the_raw_lead_stage_is_queued_first(self):
		"""Meta cannot put the later stages in proportion without it."""
		turn_on()
		lead = a_lead(email="grezzo@example.com")
		self.assertTrue(
			frappe.db.exists("Meta Conversion Event", {"lead": lead.name, "event_name": C.RAW_LEAD})
		)

	def test_a_status_change_is_a_stage(self):
		turn_on()
		lead = a_lead(email="stadio@example.com")
		status = frappe.db.get_value("CRM Lead Status", {}, "name")
		lead.status = status
		lead.save(ignore_permissions=True)

		self.assertTrue(frappe.db.exists("Meta Conversion Event", {"lead": lead.name, "event_name": status}))

	def test_the_same_stage_is_not_reported_twice(self):
		"""A status flipped back and forth by hand is not two qualifications."""
		turn_on()
		lead = a_lead(email="avanti-indietro@example.com")
		C.queue(lead.name, "Qualified")
		C.queue(lead.name, "Qualified")

		rows = frappe.get_all("Meta Conversion Event", filters={"lead": lead.name, "event_name": "Qualified"})
		self.assertEqual(len(rows), 1)

	def test_a_lead_meta_never_sent_has_nothing_to_report(self):
		"""Without Meta's lead id there is nothing it could match this to."""
		turn_on()
		manual = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "A mano", "email": "amano@example.com"}
		).insert(ignore_permissions=True)
		self.assertIsNone(C.queue(manual.name, "Qualified"))

	def test_the_payload_is_the_one_the_crm_integration_wants(self):
		"""`system_generated` and `user_data.lead_id`: the web flavour of this
		API uses different values and the wrong one is silently ignored."""
		turn_on()
		lead = a_lead(email="payload@example.com", lead_id="7790099")

		with patch.object(C, "graph_post_body", return_value={"events_received": 1}) as post:
			C.send_pending()

		endpoint, token, payload = post.call_args.args
		self.assertEqual(endpoint, "999000/events")
		self.assertEqual(token, "user-token")
		events = frappe.parse_json(payload["data"])
		self.assertEqual(events[0]["action_source"], "system_generated")
		self.assertEqual(events[0]["user_data"]["lead_id"], 7790099)
		self.assertEqual(events[0]["custom_data"]["event_source"], "crm")
		self.assertEqual(frappe.db.get_value("Meta Conversion Event", {"lead": lead.name}, "state"), "Sent")

	def test_a_refusal_is_retried_but_not_forever(self):
		"""A payload Meta will never accept would otherwise block the queue
		behind it for good."""
		turn_on()
		a_lead(email="rifiutato@example.com")

		with patch.object(C, "graph_post_body", side_effect=Exception("bad dataset")):
			for _attempt in range(C.MAX_ATTEMPTS):
				C.send_pending()

		row = frappe.get_all("Meta Conversion Event", fields=["state", "attempts", "response"], limit=1)[0]
		self.assertEqual(row.state, "Failed")
		self.assertEqual(row.attempts, C.MAX_ATTEMPTS)
		self.assertIn("bad dataset", row.response)

	def test_coverage_counts_leads_not_events(self):
		"""Meta grades the share of leads reported, so three stages of one lead
		are one lead covered, not three."""
		turn_on()
		lead = a_lead(email="copertura@example.com")
		C.queue(lead.name, "Qualified")
		with patch.object(C, "graph_post_body", return_value={"events_received": 2}):
			C.send_pending()

		report = C.coverage(30)
		self.assertEqual(report["reported"], 1)
		self.assertLessEqual(report["reported"], report["leads"])
		self.assertEqual(report["pending"], 0)

	def test_a_deal_reports_against_its_lead(self):
		turn_on()
		from crm.fcrm.doctype.crm_deal.test_crm_deal import create_test_deal

		lead = a_lead(email="trattativa-capi@example.com")
		won = frappe.db.get_value("CRM Deal Status", {"type": "Won"}, "name")
		deal = create_test_deal(organization="CAPI Org", lead=lead.name)
		deal.status = won
		deal.save(ignore_permissions=True)

		self.assertTrue(frappe.db.exists("Meta Conversion Event", {"lead": lead.name, "event_name": won}))
