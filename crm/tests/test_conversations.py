# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The People list and the Inbox are the same list of people."""

import frappe
from frappe.tests.utils import FrappeTestCase

from crm.api.conversations import belongs_to, snippet


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

		with (
			patch("crm.api.conversations.remember", side_effect=RuntimeError("boom")),
			patch("frappe.log_error") as logged,
		):
			# no exception: the message was already sent, and where the person
			# sits in a list is not worth taking it down for
			quietly("CRM Lead", "whatever")

		# and the fault is not simply swallowed: the point of the handler is the
		# line it leaves behind, so a bare `except: pass` must not pass this
		logged.assert_called_once()

	def test_the_line_in_the_log_is_not_itself_the_fault(self):
		from functools import partial
		from unittest.mock import patch

		from crm.api.conversations import quiet

		def blow_up(_who) -> None:
			raise RuntimeError("boom")

		# the line is titled after whatever was run, and a `partial` has no name —
		# nor has a callable object, nor a mock standing in for one of ours. Asking
		# for one must not be what finally takes the message down
		with patch("frappe.log_error") as logged:
			quiet(partial(blow_up, "CRM Lead"))
		logged.assert_called_once()


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


class TestTheColumnBesideARecord(FrappeTestCase):
	"""It is a chat list, so it has to behave like one."""

	def setUp(self):
		frappe.set_user("Administrator")
		self.wrote = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Giulia", "last_name": "Neri", "mobile_no": "+393331112223"}
		).insert(ignore_permissions=True)
		self.silent = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Paolo", "last_name": "Gialli"}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.db.rollback()

	def test_whoever_wrote_last_comes_first(self):
		from crm.api.conversations import people, remember

		frappe.get_doc(
			{
				"doctype": "CRM SMS Message",
				"type": "Incoming",
				"message": "ci sei?",
				"from": "+393331112223",
				"to": "+390000000002",
				"reference_doctype": "CRM Lead",
				"reference_name": self.wrote.name,
			}
		).insert(ignore_permissions=True)
		remember("CRM Lead", self.wrote.name)

		found = [row.name for row in people(limit=200)]
		self.assertIn(self.wrote.name, found)
		self.assertIn(self.silent.name, found)
		# and not in a heap: the one who wrote is ahead of the one who did not
		self.assertLess(found.index(self.wrote.name), found.index(self.silent.name))

	def test_a_search_looks_in_the_name_the_company_and_the_number(self):
		from crm.api.conversations import people

		self.assertIn(self.wrote.name, [row.name for row in people(search="Neri")])
		self.assertIn(self.wrote.name, [row.name for row in people(search="3331112223")])
		# and a surname that is not in the field the filter happened to pick must
		# not answer «nobody»
		self.assertNotIn(self.wrote.name, [row.name for row in people(search="Rossini")])

	def test_only_the_ones_waiting_when_that_is_asked(self):
		from crm.api.conversations import people

		frappe.db.set_value("CRM Lead", self.wrote.name, "conversation_unread", 1, update_modified=False)
		frappe.db.set_value("CRM Lead", self.silent.name, "conversation_unread", 0, update_modified=False)
		waiting = [row.name for row in people(waiting=True, limit=200)]
		self.assertIn(self.wrote.name, waiting)
		self.assertNotIn(self.silent.name, waiting)


class TestThePileIsWhatNobodyHasReadYet(FrappeTestCase):
	"""The badge is a fact now, not a calculation.

	It used to clear itself the moment a conversation was opened, under a setting
	that chose between «seen» and «answered». Both were guesses about what a
	glance meant. Now an arriving message puts a conversation on the pile and
	only somebody saying so takes it off.
	"""

	def setUp(self):
		frappe.set_user("Administrator")
		self.lead = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Pila", "last_name": "Prova"}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.db.rollback()

	def _sms(self, direction, message="ciao"):
		return frappe.get_doc(
			{
				"doctype": "CRM SMS Message",
				"type": direction,
				"message": message,
				"from": "+390000000001",
				"to": "+390000000002",
				"reference_doctype": "CRM Lead",
				"reference_name": self.lead.name,
			}
		).insert(ignore_permissions=True)

	def _waiting(self):
		return frappe.db.get_value("CRM Lead", self.lead.name, "conversation_unread")

	def test_a_message_from_them_puts_it_on_the_pile(self):
		self._sms("Incoming", "ci sei?")
		self.assertEqual(self._waiting(), 1)

	def test_our_own_message_does_not(self):
		self._sms("Outgoing", "buongiorno")
		self.assertFalse(self._waiting())

	def test_only_saying_so_takes_it_off(self):
		from crm.api.conversations import mark_read, mark_unread

		self._sms("Incoming", "ci sei?")
		mark_read("CRM Lead", self.lead.name)
		self.assertEqual(self._waiting(), 0)

		mark_unread("CRM Lead", self.lead.name)
		self.assertEqual(self._waiting(), 1)

	def test_replying_alone_does_not_clear_it(self):
		# the old model called a reply «dealt with». It is not: you can answer a
		# question and still owe the person the thing you promised
		self._sms("Incoming", "mi mandi il preventivo?")
		self._sms("Outgoing", "te lo mando domani")
		self.assertEqual(self._waiting(), 1)

	def test_dealing_with_it_clears_it_too(self):
		from crm.api.conversations import HANDLED, set_state

		self._sms("Incoming", "grazie mille")
		set_state("CRM Lead", self.lead.name, HANDLED)
		self.assertEqual(self._waiting(), 0)

	def test_the_count_is_measured_from_when_somebody_said_they_read_it(self):
		from crm.api.conversations import mark_read, unread

		self._sms("Incoming", "primo")
		self._sms("Incoming", "secondo")
		key = f"CRM Lead:{self.lead.name}"
		self.assertEqual(unread([["CRM Lead", self.lead.name]]).get(key), 2)

		mark_read("CRM Lead", self.lead.name)
		self.assertNotIn(key, unread([["CRM Lead", self.lead.name]]))

	def test_whoever_is_waiting_is_at_the_top_not_on_their_own(self):
		"""Sorted, not filtered — the way a chat app does it."""
		from frappe.utils import add_to_date

		from crm.api.conversations import people, remember

		answered = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Risposto", "last_name": "Prova"}
		).insert(ignore_permissions=True)
		# spoken to a minute ago, and settled: recent, but nobody is waiting
		frappe.db.set_value(
			"CRM Lead",
			answered.name,
			{
				"last_conversation_on": add_to_date(None, minutes=-1),
				"last_conversation_direction": "Outgoing",
				"conversation_unread": 0,
			},
			update_modified=False,
		)
		# and somebody who wrote yesterday and is still waiting
		self._sms("Incoming", "ci sei?")
		remember("CRM Lead", self.lead.name)
		frappe.db.set_value(
			"CRM Lead",
			self.lead.name,
			{"last_conversation_on": add_to_date(None, days=-1)},
			update_modified=False,
		)

		order = [row.name for row in people(state="open", limit=200)]
		# both are there — filtering the answered one out would leave a list
		# with holes in it, where somebody you spoke to this morning vanished
		self.assertIn(answered.name, order)
		self.assertIn(self.lead.name, order)
		# and the one waiting comes first, although it is the older message
		self.assertLess(order.index(self.lead.name), order.index(answered.name))

	def test_what_you_dealt_with_leaves_the_list(self):
		from crm.api.conversations import HANDLED, people, set_state

		self._sms("Incoming", "ci sei?")
		set_state("CRM Lead", self.lead.name, HANDLED)
		self.assertNotIn(self.lead.name, [row.name for row in people(state="open", limit=200)])


class TestReadReceiptsAreSomebodyElsesScreen(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.was = frappe.db.get_single_value("FCRM Settings", "whatsapp_read_receipts")
		self.lead = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Conferme", "last_name": "Prova"}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.db.set_single_value("FCRM Settings", "whatsapp_read_receipts", self.was)
		frappe.db.rollback()

	def test_nothing_is_told_to_anybody_unless_the_site_asked_for_it(self):
		from crm.api.conversations import acknowledge

		frappe.db.set_single_value("FCRM Settings", "whatsapp_read_receipts", 0)
		self.assertEqual(acknowledge("CRM Lead", self.lead.name), {"acknowledged": 0})


class TestWhatWeDecidedAboutAConversation(FrappeTestCase):
	"""«In attesa» says what happened. The state says what we decided about it."""

	def setUp(self):
		frappe.set_user("Administrator")
		self.lead = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Stato", "last_name": "Prova"}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.db.rollback()

	def _state(self, field="conversation_status"):
		return frappe.db.get_value("CRM Lead", self.lead.name, field)

	def _sms(self, direction, message="ciao"):
		return frappe.get_doc(
			{
				"doctype": "CRM SMS Message",
				"type": direction,
				"message": message,
				"from": "+390000000001",
				"to": "+390000000002",
				"reference_doctype": "CRM Lead",
				"reference_name": self.lead.name,
			}
		).insert(ignore_permissions=True)

	def test_handled_takes_it_off_the_pile_and_clears_the_count(self):
		from crm.api.conversations import HANDLED, set_state

		self._sms("Incoming")
		set_state("CRM Lead", self.lead.name, HANDLED)
		self.assertEqual(self._state(), HANDLED)
		# a count left on something just closed would be the badge arguing
		self.assertEqual(self._state("conversation_unread"), 0)

	def test_they_write_again_and_it_is_open_again(self):
		from crm.api.conversations import HANDLED, OPEN, set_state

		set_state("CRM Lead", self.lead.name, HANDLED)
		self._sms("Incoming", "ci sei?")
		self.assertEqual(self._state(), OPEN)

	def test_our_own_message_does_not_reopen_what_we_closed(self):
		from crm.api.conversations import HANDLED, set_state

		set_state("CRM Lead", self.lead.name, HANDLED)
		self._sms("Outgoing", "ti aggiorno")
		self.assertEqual(self._state(), HANDLED)

	def test_a_recount_does_not_reopen_it_either(self):
		# handled while the last word is still theirs is the common case —
		# «grazie» needs no answer — and any later touch must not undo that
		from crm.api.conversations import HANDLED, remember, set_state

		self._sms("Incoming", "grazie mille")
		set_state("CRM Lead", self.lead.name, HANDLED)
		remember("CRM Lead", self.lead.name)
		self.assertEqual(self._state(), HANDLED)

	def test_snoozing_parks_it_and_the_hour_brings_it_back(self):
		from frappe.utils import add_to_date

		from crm.api.conversations import set_state, wake_the_snoozed

		set_state("CRM Lead", self.lead.name, "Snoozed", until=add_to_date(None, hours=-1))
		self.assertTrue(self._state("conversation_snoozed_until"))

		wake_the_snoozed()
		self.assertFalse(self._state("conversation_snoozed_until"))

	def test_one_that_is_still_parked_stays_parked(self):
		from frappe.utils import add_to_date

		from crm.api.conversations import set_state, wake_the_snoozed

		set_state("CRM Lead", self.lead.name, "Snoozed", until=add_to_date(None, days=2))
		wake_the_snoozed()
		self.assertTrue(self._state("conversation_snoozed_until"))

	def test_waking_answers_with_a_number(self):
		from crm.api.conversations import wake_the_snoozed

		# That the hour brings a conversation back is proved above, end to end.
		# What this one pins is the answer itself: the count used to be `0 +`
		# whatever `frappe.db.sql` hands back for an update, which is a tuple, so
		# the hourly job raised TypeError every time and nothing ever came back.
		# How many it finds depends on what the rest of the suite parked, so the
		# number is not asserted — that it is one at all is the whole point.
		self.assertIsInstance(wake_the_snoozed(), int)

	def test_the_moment_is_the_same_moment_however_it_was_said(self):
		from frappe.utils import add_to_date, get_datetime

		from crm.api.conversations import set_state

		# the browser says the moment as a string and our own code as a datetime,
		# because `add_to_date` hands one back; both park the conversation, and both
		# park it at the same instant
		moment = add_to_date(None, days=3)

		set_state("CRM Lead", self.lead.name, "Snoozed", until=moment)
		parked = self._state("conversation_snoozed_until")
		self.assertTrue(parked)

		set_state("CRM Lead", self.lead.name, "Snoozed", until=str(moment))
		self.assertEqual(get_datetime(self._state("conversation_snoozed_until")), get_datetime(parked))

	def test_snoozing_needs_a_moment_to_snooze_until(self):
		from crm.api.conversations import set_state

		with self.assertRaises(frappe.ValidationError):
			set_state("CRM Lead", self.lead.name, "Snoozed")

	def test_a_conversation_is_never_handled_and_parked_at_once(self):
		from frappe.utils import add_to_date

		from crm.api.conversations import HANDLED, set_state

		set_state("CRM Lead", self.lead.name, "Snoozed", until=add_to_date(None, days=1))
		set_state("CRM Lead", self.lead.name, HANDLED)
		self.assertEqual(self._state(), HANDLED)
		self.assertFalse(self._state("conversation_snoozed_until"))

	def test_the_list_answers_the_four_questions_separately(self):
		from frappe.utils import add_to_date

		from crm.api.conversations import HANDLED, people, set_state

		parked = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Rinviata", "last_name": "Prova"}
		).insert(ignore_permissions=True)
		set_state("CRM Lead", parked.name, "Snoozed", until=add_to_date(None, days=1))
		set_state("CRM Lead", self.lead.name, HANDLED)

		def named(state):
			return [row.name for row in people(state=state, limit=200)]

		self.assertIn(self.lead.name, named("handled"))
		self.assertNotIn(self.lead.name, named("unread"))
		self.assertIn(parked.name, named("snoozed"))
		self.assertNotIn(parked.name, named("unread"))
		self.assertIn(self.lead.name, named("all"))
		self.assertIn(parked.name, named("all"))


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

	def test_we_do_not_count_our_own_messages(self):
		from crm.api.conversations import unread

		self._sms("Outgoing", "buongiorno")
		self.assertEqual(unread([["CRM Lead", self.lead.name]]), {})

	def test_a_message_on_a_deal_is_a_message_with_the_person(self):
		from crm.api.conversations import remember, unread

		# the company has to be a row of its own before the deal can point at it:
		# on a deal `organization` is a Link, and unlike a lead a deal does not turn
		# a name typed into that field into a CRM Organization by itself
		organization = frappe.get_doc(
			{"doctype": "CRM Organization", "organization_name": "Prova Srl"}
		).insert(ignore_permissions=True)
		deal = frappe.get_doc(
			{"doctype": "CRM Deal", "lead": self.lead.name, "organization": organization.name}
		).insert(ignore_permissions=True)
		self._sms("Incoming", "novità?", reference=("CRM Deal", deal.name))
		remember("CRM Deal", deal.name)

		# the person moves up the Inbox, not only the negotiation
		self.assertTrue(frappe.db.get_value("CRM Lead", self.lead.name, "last_conversation_on"))
		self.assertEqual(unread([["CRM Lead", self.lead.name]]).get(f"CRM Lead:{self.lead.name}"), 1)
