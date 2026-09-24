# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The People list and the Inbox are the same list of people."""

import frappe
from frappe.tests.utils import FrappeTestCase

from crm.api.conversations import ANSWERED, SEEN, badge_clears, belongs_to, cutoff_field, snippet


class TestWhatTheRowSays(FrappeTestCase):
	def test_an_email_reads_as_a_line_of_text_not_as_html(self):
		self.assertEqual(
			snippet("<p>Buongiorno,<br>le mando il <b>preventivo</b></p>"),
			"Buongiorno, le mando il preventivo",
		)

	def test_the_entities_are_read_back(self):
		self.assertEqual(snippet("Rossi &amp; Figli &lt;3"), "Rossi & Figli <3")

	def test_a_preview_does_not_go_on_forever(self):
		self.assertEqual(len(snippet("ciao " * 200)), 140)

	def test_nothing_said_is_an_empty_line(self):
		self.assertEqual(snippet(None), "")
		self.assertEqual(snippet(""), "")


class TestAPreviewIsOnlyAPreview(FrappeTestCase):
	"""It runs on the way in for every message, so it may never be the reason
	one does not go out."""

	def test_it_does_not_reach_for_an_api_that_may_not_be_there(self):
		# a wrong helper name here made sending a WhatsApp message fail with a
		# Python error about a string nobody had asked for
		self.assertEqual(snippet("Rossi &amp; Figli &lt;3"), "Rossi & Figli <3")

	def test_a_fault_costs_a_line_in_the_log_and_nothing_else(self):
		from unittest.mock import patch

		from crm.api.conversations import quietly

		with patch("crm.api.conversations.remember", side_effect=RuntimeError("boom")):
			# no exception: the message was already sent, and where the person
			# sits in a list is not worth taking it down for
			quietly("CRM Lead", "whatever")


class TestTheBadgeSetting(FrappeTestCase):
	def setUp(self):
		self.was = frappe.db.get_single_value("FCRM Settings", "conversation_badge_clears")

	def tearDown(self):
		frappe.db.set_single_value("FCRM Settings", "conversation_badge_clears", self.was)

	def test_seen_is_what_it_falls_back_to(self):
		# an unset or unknown value must not silently mean the other behaviour
		frappe.db.set_single_value("FCRM Settings", "conversation_badge_clears", None)
		self.assertEqual(badge_clears(), SEEN)
		self.assertEqual(cutoff_field(), "conversation_seen_until")

	def test_answering_is_read_from_when_somebody_wrote_back(self):
		frappe.db.set_single_value("FCRM Settings", "conversation_badge_clears", ANSWERED)
		self.assertEqual(badge_clears(), ANSWERED)
		self.assertEqual(cutoff_field(), "last_answered_on")


class TestAPersonsConversationIncludesTheirDeals(FrappeTestCase):
	def test_one_query_matches_a_whole_scope(self):
		# a person and two of their deals: one filter, not three round trips
		where = [("CRM Lead", "L1"), ("CRM Deal", "D1"), ("CRM Deal", "D2")]
		self.assertEqual(
			belongs_to(where),
			{
				"reference_doctype": ["in", ["CRM Deal", "CRM Lead"]],
				"reference_name": ["in", ["D1", "D2", "L1"]],
			},
		)


class TestTheConversationOfARealPerson(FrappeTestCase):
	"""End to end, with rows in the database."""

	def setUp(self):
		frappe.set_user("Administrator")
		self.lead = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Conversazione", "last_name": "Prova"}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.db.rollback()

	def _sms(self, direction, message, reference=None):
		reference = reference or ("CRM Lead", self.lead.name)
		return frappe.get_doc(
			{
				"doctype": "CRM SMS Message",
				"type": direction,
				"message": message,
				"from": "+390000000001",
				"to": "+390000000002",
				"reference_doctype": reference[0],
				"reference_name": reference[1],
			}
		).insert(ignore_permissions=True)

	def test_the_last_message_lands_on_the_person(self):
		from crm.api.conversations import remember

		self._sms("Incoming", "mi mandi il preventivo?")
		remember("CRM Lead", self.lead.name)
		row = frappe.db.get_value(
			"CRM Lead",
			self.lead.name,
			[
				"last_conversation_on",
				"last_conversation_channel",
				"last_conversation_direction",
				"last_conversation_preview",
			],
			as_dict=True,
		)
		self.assertTrue(row.last_conversation_on)
		self.assertEqual(row.last_conversation_channel, "SMS")
		self.assertEqual(row.last_conversation_direction, "Incoming")
		self.assertEqual(row.last_conversation_preview, "mi mandi il preventivo?")

	def test_a_message_waiting_is_counted_and_opening_it_clears_the_count(self):
		from crm.api.conversations import mark_seen, unread

		frappe.db.set_single_value("FCRM Settings", "conversation_badge_clears", SEEN)
		self._sms("Incoming", "primo")
		self._sms("Incoming", "secondo")
		key = f"CRM Lead:{self.lead.name}"
		self.assertEqual(unread([["CRM Lead", self.lead.name]]).get(key), 2)

		mark_seen("CRM Lead", self.lead.name)
		self.assertNotIn(key, unread([["CRM Lead", self.lead.name]]))

	def test_we_do_not_count_our_own_messages(self):
		from crm.api.conversations import unread

		self._sms("Outgoing", "buongiorno")
		self.assertEqual(unread([["CRM Lead", self.lead.name]]), {})

	def test_answering_is_what_clears_it_when_that_is_the_setting(self):
		from crm.api.conversations import remember, unread

		frappe.db.set_single_value("FCRM Settings", "conversation_badge_clears", ANSWERED)
		self._sms("Incoming", "c'è nessuno?")
		remember("CRM Lead", self.lead.name)
		key = f"CRM Lead:{self.lead.name}"
		self.assertEqual(unread([["CRM Lead", self.lead.name]]).get(key), 1)

		# opening it is not enough under this setting — somebody has to reply
		self._sms("Outgoing", "eccomi")
		remember("CRM Lead", self.lead.name)
		self.assertNotIn(key, unread([["CRM Lead", self.lead.name]]))
		frappe.db.set_single_value("FCRM Settings", "conversation_badge_clears", SEEN)

	def test_the_flag_the_list_filters_on_follows_the_conversation(self):
		from crm.api.conversations import mark_seen, mark_unread, remember

		frappe.db.set_single_value("FCRM Settings", "conversation_badge_clears", SEEN)
		waiting = lambda: frappe.db.get_value("CRM Lead", self.lead.name, "conversation_unread")  # noqa: E731

		self._sms("Incoming", "c'è nessuno?")
		remember("CRM Lead", self.lead.name)
		self.assertEqual(waiting(), 1)

		mark_seen("CRM Lead", self.lead.name)
		self.assertEqual(waiting(), 0)

		mark_unread("CRM Lead", self.lead.name)
		self.assertEqual(waiting(), 1)

	def test_a_conversation_already_seen_is_not_called_waiting_again(self):
		# remember() writes the dates but not the cutoff, and reading the cutoff
		# back as unset would have put every answered conversation on the pile
		from crm.api.conversations import mark_seen, remember

		frappe.db.set_single_value("FCRM Settings", "conversation_badge_clears", SEEN)
		self._sms("Incoming", "una domanda")
		remember("CRM Lead", self.lead.name)
		mark_seen("CRM Lead", self.lead.name)

		# nothing new was said; recomputing must not change the answer
		remember("CRM Lead", self.lead.name)
		self.assertEqual(frappe.db.get_value("CRM Lead", self.lead.name, "conversation_unread"), 0)

	def test_our_own_last_word_leaves_nobody_waiting(self):
		from crm.api.conversations import remember

		self._sms("Incoming", "domanda")
		self._sms("Outgoing", "risposta")
		remember("CRM Lead", self.lead.name)
		self.assertEqual(frappe.db.get_value("CRM Lead", self.lead.name, "conversation_unread"), 0)

	def test_changing_the_setting_redoes_the_flag_for_everybody(self):
		from crm.api.conversations import refresh_waiting_flags, remember

		frappe.db.set_single_value("FCRM Settings", "conversation_badge_clears", SEEN)
		self._sms("Incoming", "ci sei?")
		remember("CRM Lead", self.lead.name)
		from crm.api.conversations import mark_seen

		mark_seen("CRM Lead", self.lead.name)
		self.assertEqual(frappe.db.get_value("CRM Lead", self.lead.name, "conversation_unread"), 0)

		# seen, but never answered: under the other rule this one is waiting again
		frappe.db.set_single_value("FCRM Settings", "conversation_badge_clears", ANSWERED)
		refresh_waiting_flags()
		self.assertEqual(frappe.db.get_value("CRM Lead", self.lead.name, "conversation_unread"), 1)
		frappe.db.set_single_value("FCRM Settings", "conversation_badge_clears", SEEN)

	def test_a_message_on_a_deal_is_a_message_with_the_person(self):
		from crm.api.conversations import remember, unread

		frappe.db.set_single_value("FCRM Settings", "conversation_badge_clears", SEEN)
		deal = frappe.get_doc(
			{"doctype": "CRM Deal", "lead": self.lead.name, "organization": "Prova Srl"}
		).insert(ignore_permissions=True)
		self._sms("Incoming", "novità?", reference=("CRM Deal", deal.name))
		remember("CRM Deal", deal.name)

		# the person moves up the Inbox, not only the negotiation
		self.assertTrue(frappe.db.get_value("CRM Lead", self.lead.name, "last_conversation_on"))
		self.assertEqual(unread([["CRM Lead", self.lead.name]]).get(f"CRM Lead:{self.lead.name}"), 1)
