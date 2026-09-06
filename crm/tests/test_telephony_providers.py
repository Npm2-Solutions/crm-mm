# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.telephony import answering, inbound, providers, routing
from crm.telephony.providers.base import (
	Announcement,
	CallInstruction,
	ProviderNotSupported,
	TelephonyProvider,
)

STUDIO_NUMBER = "+390212345678"
CALLER = "+393331234567"


class FakeProvider(TelephonyProvider):
	"""A carrier that speaks nothing but records what it was asked to do.

	The point of the whole abstraction: the decision can be tested without a
	single line of TwiML, which is also what makes it swappable.
	"""

	name = "fake"
	label = "Fake"
	agent_number_field = "twilio_number"
	controls_call_flow = True
	rings_browser = True

	def __init__(self):
		self.asked = []

	def is_enabled(self) -> bool:
		return True

	def say(self, announcement, hang_up=True):
		self.asked.append(("say", announcement))
		return CallInstruction(body=f"SAY::{announcement.text}", mimetype="text/plain")

	def dial_phone(self, caller_id, to_number):
		self.asked.append(("dial_phone", caller_id, to_number))
		return CallInstruction(body=f"PHONE::{to_number}", mimetype="text/plain")

	def dial_agent(self, agent):
		self.asked.append(("dial_agent", agent))
		return CallInstruction(body=f"AGENT::{agent}", mimetype="text/plain")


class DashboardProvider(FakeProvider):
	"""A carrier whose call flow lives in its own dashboard, like Exotel."""

	name = "dashboard"
	label = "Dashboard"
	controls_call_flow = False


class ProviderCase(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.provider = FakeProvider()
		self.set_answering()

	def tearDown(self):
		frappe.db.rollback()
		for attr in ("crm_answering_settings", "crm_scheduling_settings", "crm_company_hours"):
			if hasattr(frappe.local, attr):
				delattr(frappe.local, attr)

	def set_answering(self, **values):
		doc = frappe.get_single("CRM Answering Settings")
		doc.update(
			{
				"enabled": 1,
				"answer_mode": answering.MODE_ALWAYS,
				"use_working_hours": 0,
				"callback_hours": 3,
				"dedupe_window_hours": 4,
				"greeting_source": answering.SOURCE_TEXT,
				"greeting_text": "La richiamiamo entro {hours} ore",
				"language": "it-IT",
				"voice": "Polly.Bianca",
				**values,
			}
		)
		doc.save()
		if hasattr(frappe.local, "crm_answering_settings"):
			del frappe.local.crm_answering_settings
		return doc

	def make_agent(self, device="Computer"):
		if frappe.db.exists("CRM Telephony Agent", "Administrator"):
			frappe.delete_doc("CRM Telephony Agent", "Administrator", force=True)
		return frappe.get_doc(
			{
				"doctype": "CRM Telephony Agent",
				"user": "Administrator",
				"mobile_no": "+393480000000",
				"twilio_number": STUDIO_NUMBER,
				"call_receiving_device": device,
			}
		).insert(ignore_permissions=True)

	def incoming(self):
		return inbound.handle_incoming_call(self.provider, CALLER, STUDIO_NUMBER)


# ---------------------------------------------------------------------------
# the decision, with no carrier in sight
# ---------------------------------------------------------------------------


class TestInboundDecision(ProviderCase):
	def test_the_announcement_answers_without_any_twilio(self):
		instruction = self.incoming()

		self.assertEqual([kind for kind, *_ in self.provider.asked], ["say"])
		self.assertIn("3 ore", instruction.body)
		self.assertEqual(instruction.mimetype, "text/plain")

	def test_the_announcement_carries_the_configured_voice(self):
		self.incoming()
		_kind, announcement = self.provider.asked[0]
		self.assertEqual(announcement.language, "it-IT")
		self.assertEqual(announcement.voice, "Polly.Bianca")

	def test_always_mode_ignores_an_agent_sitting_right_there(self):
		self.make_agent(device="Computer")
		with patch.object(routing, "logged_in", return_value={"Administrator"}):
			self.incoming()
		# the mode is the whole answer: an available agent changes nothing
		self.assertEqual([kind for kind, *_ in self.provider.asked], ["say"])

	def test_ring_first_reaches_an_agent_at_their_desk(self):
		self.set_answering(answer_mode=answering.MODE_RING_FIRST)
		self.make_agent(device="Computer")
		with patch.object(routing, "logged_in", return_value={"Administrator"}):
			instruction = self.incoming()

		self.assertEqual(self.provider.asked[0][0], "dial_agent")
		self.assertEqual(instruction.body, "AGENT::Administrator")

	def test_ring_first_reaches_an_agent_on_their_mobile(self):
		self.set_answering(answer_mode=answering.MODE_RING_FIRST)
		self.make_agent(device="Phone")
		with patch.object(routing, "logged_in", return_value=set()):
			instruction = self.incoming()

		self.assertEqual(self.provider.asked[0][0], "dial_phone")
		self.assertEqual(instruction.body, "PHONE::+393480000000")

	def test_ring_first_falls_back_to_the_announcement(self):
		self.set_answering(answer_mode=answering.MODE_RING_FIRST)
		with patch.object(routing, "logged_in", return_value=set()):
			instruction = self.incoming()

		self.assertEqual(self.provider.asked[0][0], "say")
		self.assertIn("3 ore", instruction.body)

	def test_without_the_answering_service_nobody_available_gets_an_apology(self):
		self.set_answering(enabled=0)
		with patch.object(routing, "logged_in", return_value=set()):
			instruction = self.incoming()

		self.assertEqual(self.provider.asked[0][0], "say")
		self.assertNotIn("3 ore", instruction.body)

	def test_a_dashboard_carrier_is_refused_outright(self):
		self.provider = DashboardProvider()
		# its flow is built in its own dashboard, so being asked what a call should
		# hear means a webhook was wired to the wrong provider — say so loudly
		with self.assertRaises(ProviderNotSupported):
			self.incoming()
		self.assertEqual(self.provider.asked, [])

	def test_a_carrier_that_cannot_control_the_call_says_so(self):
		class Mute(FakeProvider):
			def say(self, announcement, hang_up=True):
				return TelephonyProvider.say(self, announcement, hang_up)

		with self.assertRaises(ProviderNotSupported):
			Mute().say(Announcement(text="hello"))


# ---------------------------------------------------------------------------
# routing
# ---------------------------------------------------------------------------


class TestRouting(ProviderCase):
	def test_owners_are_found_by_the_provider_own_field(self):
		self.make_agent()
		owners = routing.number_owners(self.provider, STUDIO_NUMBER)
		self.assertIn("Administrator", owners)
		self.assertEqual(owners["Administrator"]["mobile_no"], "+393480000000")

	def test_a_number_nobody_owns_returns_nothing(self):
		self.assertEqual(routing.number_owners(self.provider, "+390299999999"), {})

	def test_a_provider_without_a_number_field_owns_nobody(self):
		class Numberless(FakeProvider):
			agent_number_field = ""

		self.assertEqual(routing.number_owners(Numberless(), STUDIO_NUMBER), {})

	def test_formatting_of_the_called_number_does_not_matter(self):
		self.make_agent()
		self.assertIn("Administrator", routing.number_owners(self.provider, "+39 02 1234 5678"))

	def test_an_agent_at_their_desk_is_only_picked_when_online(self):
		owners = {"a@x.it": {"name": "a@x.it", "call_receiving_device": "Computer", "mobile_no": None}}
		with patch.object(routing, "logged_in", return_value=set()):
			self.assertIsNone(routing.pick_attender(owners))
		with patch.object(routing, "logged_in", return_value={"a@x.it"}):
			self.assertEqual(routing.pick_attender(owners)["name"], "a@x.it")

	def test_the_person_who_knows_the_caller_is_preferred(self):
		owners = {
			"other@x.it": {"name": "other@x.it", "call_receiving_device": "Computer", "mobile_no": None},
			"owner@x.it": {"name": "owner@x.it", "call_receiving_device": "Computer", "mobile_no": None},
		}
		with (
			patch.object(routing, "logged_in", return_value={"other@x.it", "owner@x.it"}),
			patch.object(routing, "record_owner", return_value="owner@x.it"),
		):
			self.assertEqual(routing.pick_attender(owners, CALLER)["name"], "owner@x.it")


# ---------------------------------------------------------------------------
# the registry
# ---------------------------------------------------------------------------


class TestRegistry(IntegrationTestCase):
	def tearDown(self):
		if hasattr(frappe.local, "crm_telephony_providers"):
			del frappe.local.crm_telephony_providers

	def test_the_shipped_carriers_load(self):
		self.assertEqual(providers.get("twilio").label, "Twilio")
		self.assertEqual(providers.get("exotel").label, "Exotel")

	def test_an_unknown_carrier_is_refused(self):
		with self.assertRaises(frappe.ValidationError):
			providers.get("nosuchcarrier")

	def test_a_provider_is_built_once_per_request(self):
		self.assertIs(providers.get("twilio"), providers.get("twilio"))

	def test_a_call_log_medium_finds_its_carrier(self):
		self.assertEqual(providers.for_medium("Twilio").name, "twilio")
		self.assertEqual(providers.for_medium("exotel").name, "exotel")

	def test_a_manual_call_has_no_carrier_behind_it(self):
		self.assertIsNone(providers.for_medium("Manual"))
		self.assertIsNone(providers.for_medium(None))

	def test_only_twilio_can_run_the_answering_service(self):
		# Exotel's flow lives in its own dashboard, so it is not a candidate
		self.assertFalse(providers.get("exotel").controls_call_flow)
		self.assertTrue(providers.get("twilio").controls_call_flow)

	def test_a_carrier_can_be_added_at_runtime(self):
		providers.register("fake", "crm.tests.test_telephony_providers.FakeProvider")
		try:
			self.assertEqual(providers.get("fake").label, "Fake")
		finally:
			providers.REGISTRY.pop("fake", None)
