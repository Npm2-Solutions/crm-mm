# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from crm.telephony import caller_ids, providers
from crm.telephony.providers.base import TelephonyProvider
from crm.telephony.providers.twilio import TwilioProvider

STUDIO = "+390212345678"
MOBILE = "+393331234567"
TOLL_FREE = "+39800123456"
CRM_HANDLER = "/api/method/crm.integrations.twilio.api.twilio_incoming_call_handler"


class FakeNumberProvider(TelephonyProvider):
	"""A carrier that reports whatever the test wants it to."""

	name = "fake"
	label = "Fake"
	agent_number_field = "twilio_number"
	controls_call_flow = True

	def __init__(self, rows=None):
		self.rows = rows or []

	def is_enabled(self) -> bool:
		return True

	def list_caller_ids(self) -> list[dict]:
		return self.rows


class CallerIdCase(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.db.rollback()
		if hasattr(frappe.local, "crm_telephony_providers"):
			del frappe.local.crm_telephony_providers

	def sync_with(self, rows):
		"""Run a sync against a carrier that reports exactly these rows.

		Registered for the duration and seeded straight into the per-request cache,
		so the sync resolves this instance rather than building a fresh one.
		"""
		providers.register("fake", "crm.tests.test_caller_ids.FakeNumberProvider")
		self.addCleanup(providers.REGISTRY.pop, "fake", None)
		frappe.local.crm_telephony_providers = {"fake": FakeNumberProvider(rows)}
		return caller_ids.sync("fake")


# ---------------------------------------------------------------------------
# reading a number
# ---------------------------------------------------------------------------


class TestClassify(IntegrationTestCase):
	def test_an_italian_landline_is_geographic(self):
		facts = caller_ids.classify("+39 02 1234 5678")
		self.assertEqual(facts["e164"], STUDIO)
		self.assertEqual(facts["number_type"], "Geographic")
		self.assertEqual(facts["country"], "IT")

	def test_an_italian_mobile_is_a_mobile(self):
		self.assertEqual(caller_ids.classify(MOBILE)["number_type"], "Mobile")

	def test_a_numero_verde_is_toll_free(self):
		self.assertEqual(caller_ids.classify(TOLL_FREE)["number_type"], "Toll Free")

	def test_spacing_does_not_change_the_answer(self):
		self.assertEqual(caller_ids.classify("+390212345678"), caller_ids.classify("+39 02 1234 5678"))

	def test_nonsense_classifies_as_nothing(self):
		facts = caller_ids.classify("chiamare la reception")
		self.assertEqual(facts["number_type"], "")
		self.assertEqual(facts["country"], "")

	def test_an_empty_value_is_handled(self):
		self.assertEqual(caller_ids.classify("")["number_type"], "")
		self.assertEqual(caller_ids.classify(None)["number_type"], "")


# ---------------------------------------------------------------------------
# does a call to it reach us
# ---------------------------------------------------------------------------


class TestRoutingDerivation(IntegrationTestCase):
	def test_a_number_pointed_at_our_handler_reaches_us(self):
		result = caller_ids._routing({"source": caller_ids.SOURCE_ACCOUNT, "points_at_crm": True})
		self.assertEqual(result["routes_to_crm"], 1)
		self.assertIsNone(result["routing_note"])

	def test_a_trunked_number_never_reaches_us(self):
		result = caller_ids._routing(
			{
				"source": caller_ids.SOURCE_ACCOUNT,
				"points_at_crm": True,
				"sip_trunk_sid": "TK1",
				"sip_trunk": "Studio PBX",
			}
		)
		# the trunk wins even when a voice webhook is still set: Twilio ignores it
		self.assertEqual(result["routes_to_crm"], 0)
		self.assertIn("Studio PBX", result["routing_note"])

	def test_a_verified_number_is_outbound_only(self):
		result = caller_ids._routing({"source": caller_ids.SOURCE_VERIFIED})
		self.assertEqual(result["routes_to_crm"], 0)
		self.assertIn("outgoing caller ID", result["routing_note"])

	def test_pointing_at_the_outbound_app_is_called_out(self):
		result = caller_ids._routing(
			{"source": caller_ids.SOURCE_ACCOUNT, "uses_crm_app": True, "points_at_crm": False}
		)
		self.assertEqual(result["routes_to_crm"], 0)
		self.assertIn("outgoing calls", result["routing_note"])

	def test_someone_elses_webhook_is_called_out(self):
		result = caller_ids._routing(
			{"source": caller_ids.SOURCE_ACCOUNT, "voice_url": "https://elsewhere.test/voice"}
		)
		self.assertEqual(result["routes_to_crm"], 0)
		self.assertIn("somewhere other than this CRM", result["routing_note"])

	def test_no_webhook_at_all_is_called_out(self):
		result = caller_ids._routing({"source": caller_ids.SOURCE_ACCOUNT})
		self.assertEqual(result["routes_to_crm"], 0)
		self.assertIn("No voice webhook", result["routing_note"])


class TestWebhookMatching(IntegrationTestCase):
	def test_our_handler_is_recognised_whatever_the_host(self):
		expected = "https://crm.studio.it" + CRM_HANDLER
		self.assertTrue(TwilioProvider._points_at("https://other-name.it" + CRM_HANDLER, expected))
		self.assertTrue(TwilioProvider._points_at("https://crm.studio.it" + CRM_HANDLER, expected))

	def test_a_query_string_does_not_confuse_it(self):
		expected = "https://crm.studio.it" + CRM_HANDLER
		self.assertTrue(TwilioProvider._points_at(f"https://crm.studio.it{CRM_HANDLER}?x=1", expected))

	def test_another_endpoint_is_not_ours(self):
		expected = "https://crm.studio.it" + CRM_HANDLER
		self.assertFalse(TwilioProvider._points_at("https://crm.studio.it/api/method/other", expected))
		self.assertFalse(TwilioProvider._points_at(None, expected))


# ---------------------------------------------------------------------------
# syncing the list
# ---------------------------------------------------------------------------


class TestSync(CallerIdCase):
	def test_numbers_are_created_with_their_facts(self):
		result = self.sync_with(
			[
				{
					"phone_number": "+39 02 1234 5678",
					"label": "Reception",
					"source": caller_ids.SOURCE_ACCOUNT,
					"voice_capable": True,
					"sms_capable": True,
					"points_at_crm": True,
				}
			]
		)
		self.assertEqual(result["total"], 1)
		self.assertEqual(result["added"], 1)

		doc = frappe.get_doc("CRM Caller ID", STUDIO)
		self.assertEqual(doc.label, "Reception")
		self.assertEqual(doc.number_type, "Geographic")
		self.assertEqual(doc.routes_to_crm, 1)
		self.assertEqual(doc.sms_capable, 1)

	def test_syncing_twice_updates_rather_than_duplicates(self):
		rows = [{"phone_number": STUDIO, "source": caller_ids.SOURCE_ACCOUNT, "points_at_crm": True}]
		self.sync_with(rows)
		second = self.sync_with(rows)
		self.assertEqual(second["added"], 0)
		self.assertEqual(frappe.db.count("CRM Caller ID", {"phone_number": STUDIO}), 1)

	def test_a_hand_written_label_survives_a_refresh(self):
		self.sync_with([{"phone_number": STUDIO, "source": caller_ids.SOURCE_ACCOUNT}])
		caller_ids.set_label(STUDIO, "Studio Rossi — reception")
		self.sync_with(
			[{"phone_number": STUDIO, "label": "Twilio's own name", "source": caller_ids.SOURCE_ACCOUNT}]
		)
		self.assertEqual(frappe.db.get_value("CRM Caller ID", STUDIO, "label"), "Studio Rossi — reception")

	def test_a_number_that_left_the_account_is_switched_off_not_deleted(self):
		self.sync_with([{"phone_number": STUDIO, "source": caller_ids.SOURCE_ACCOUNT}])
		result = self.sync_with([{"phone_number": MOBILE, "source": caller_ids.SOURCE_ACCOUNT}])

		self.assertEqual(result["retired"], 1)
		self.assertTrue(frappe.db.exists("CRM Caller ID", STUDIO))
		self.assertEqual(frappe.db.get_value("CRM Caller ID", STUDIO, "enabled"), 0)

	def test_a_manual_entry_is_left_alone_by_the_sync(self):
		frappe.get_doc(
			{
				"doctype": "CRM Caller ID",
				"phone_number": TOLL_FREE,
				"provider": "fake",
				"source": caller_ids.SOURCE_MANUAL,
				"label": "Numero verde",
			}
		).insert(ignore_permissions=True)

		self.sync_with([{"phone_number": STUDIO, "source": caller_ids.SOURCE_ACCOUNT}])
		# a number somebody added by hand is not the provider's to retire
		self.assertEqual(frappe.db.get_value("CRM Caller ID", TOLL_FREE, "enabled"), 1)

	def test_a_trunked_number_is_recorded_as_unreachable(self):
		self.sync_with(
			[
				{
					"phone_number": STUDIO,
					"source": caller_ids.SOURCE_ACCOUNT,
					"sip_trunk_sid": "TK1",
					"sip_trunk": "Studio PBX",
					"points_at_crm": True,
				}
			]
		)
		doc = frappe.get_doc("CRM Caller ID", STUDIO)
		self.assertEqual(doc.routes_to_crm, 0)
		self.assertEqual(doc.sip_trunk, "Studio PBX")

	def test_rubbish_from_the_provider_is_skipped(self):
		result = self.sync_with(
			[
				{"phone_number": "", "source": caller_ids.SOURCE_ACCOUNT},
				{"phone_number": STUDIO, "source": caller_ids.SOURCE_ACCOUNT},
			]
		)
		self.assertEqual(result["total"], 1)


class TestReadingTheList(CallerIdCase):
	def test_only_numbers_that_reach_us_can_answer(self):
		self.sync_with(
			[
				{"phone_number": STUDIO, "source": caller_ids.SOURCE_ACCOUNT, "points_at_crm": True},
				{"phone_number": MOBILE, "source": caller_ids.SOURCE_VERIFIED},
			]
		)
		self.assertEqual(caller_ids.answering_capable_numbers(), [STUDIO])

	def test_verified_numbers_still_count_for_outbound(self):
		self.sync_with(
			[
				{"phone_number": STUDIO, "source": caller_ids.SOURCE_ACCOUNT, "points_at_crm": True},
				{"phone_number": MOBILE, "source": caller_ids.SOURCE_VERIFIED},
			]
		)
		# presentable is a wider set than answerable, which is the point of verifying
		self.assertEqual(sorted(caller_ids.usable_for_outbound("fake")), sorted([STUDIO, MOBILE]))

	def test_a_disabled_number_is_offered_to_nobody(self):
		self.sync_with([{"phone_number": STUDIO, "source": caller_ids.SOURCE_ACCOUNT, "points_at_crm": True}])
		caller_ids.set_enabled(STUDIO, False)
		self.assertEqual(caller_ids.usable_for_outbound("fake"), [])
		self.assertEqual(caller_ids.answering_capable_numbers(), [])
