# Copyright (c) 2026, NPM2 Solutions Srl and contributors
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
		# the badge is a flag on the base list, not a view of its own: the pile
		# sits on top of «open» and is marked there
		waiting = [row.name for row in people(waiting=True, limit=200)]
		self.assertIn(self.wrote.name, waiting)
		self.assertNotIn(self.silent.name, waiting)


class TestAConversationOpenedFromALink(FrappeTestCase):
	"""A link can name anybody; the list only holds the top of one view."""

	def setUp(self):
		frappe.set_user("Administrator")
		self.lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Alessandro",
				"last_name": "Colombo",
				"mobile_no": "+393906480180",
				"email": "alessandro.colombo@example.com",
			}
		).insert(ignore_permissions=True)
		# handled last week: in no live view, so never among the rows on screen
		frappe.db.set_value("CRM Lead", self.lead.name, "conversation_status", "Handled")

	def tearDown(self):
		frappe.db.rollback()

	def test_the_header_has_a_name_to_say(self):
		from crm.api.conversations import person

		row = person(self.lead.name)
		self.assertEqual(row.lead_name, "Alessandro Colombo")
		self.assertEqual(row.mobile_no, "+393906480180")
		self.assertEqual(row.email, "alessandro.colombo@example.com")
		self.assertEqual(row.conversation_status, "Handled")

	def test_it_is_the_same_row_the_list_draws(self):
		from crm.api.conversations import ROW, people, person

		self.assertEqual(set(person(self.lead.name)), set(ROW))
		listed = next(row for row in people(search="Colombo") if row.name == self.lead.name)
		self.assertEqual(person(self.lead.name), listed)

	def test_a_link_to_nobody_says_so(self):
		from crm.api.conversations import person

		with self.assertRaises(frappe.DoesNotExistError):
			person("CRM-LEAD-NOBODY")


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

	def test_whoever_spoke_last_is_at_the_top_waiting_or_not(self):
		"""Sorted by when something was said, and by nothing else.

		Unread used to come first, and reading was then a thing that moved rows:
		marked read, a conversation dropped below everything still unread.
		"""
		from frappe.utils import add_to_date

		from crm.api.conversations import people, remember

		answered = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Risposto", "last_name": "Prova"}
		).insert(ignore_permissions=True)
		# spoken to a minute ago, and settled: recent, and nobody is waiting
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

		order = [row.name for row in people(view="open", limit=200)]
		# both are there — filtering the answered one out would leave a list
		# with holes in it, where somebody you spoke to this morning vanished
		self.assertIn(answered.name, order)
		self.assertIn(self.lead.name, order)
		# and the one spoken to last comes first, waiting or not: what is unread
		# is marked on its row and has a filter, it does not jump the queue
		self.assertLess(order.index(answered.name), order.index(self.lead.name))

	def test_reading_it_does_not_move_it(self):
		"""The row somebody is on stays where it is when they say they read it."""
		from crm.api.conversations import mark_read, mark_unread, people

		self._sms("Incoming", "ci sei?")
		before = [row.name for row in people(view="open", limit=200)]

		mark_read("CRM Lead", self.lead.name)
		self.assertEqual([row.name for row in people(view="open", limit=200)], before)

		mark_unread("CRM Lead", self.lead.name)
		self.assertEqual([row.name for row in people(view="open", limit=200)], before)

	def test_unread_again_is_a_flag_not_a_rewind(self):
		"""Marked unread, it keeps the moment it was read.

		Forgetting that moment used to turn the number on the row into every
		message they had ever sent.
		"""
		from crm.api.conversations import mark_read, mark_unread, unread

		self._sms("Incoming", "primo")
		self._sms("Incoming", "secondo")
		mark_read("CRM Lead", self.lead.name)
		read_at = frappe.db.get_value("CRM Lead", self.lead.name, "conversation_seen_until")

		mark_unread("CRM Lead", self.lead.name)
		self.assertEqual(self._waiting(), 1)
		self.assertEqual(frappe.db.get_value("CRM Lead", self.lead.name, "conversation_seen_until"), read_at)
		# flagged, with nothing new since: a dot on the row, not a count
		self.assertNotIn(f"CRM Lead:{self.lead.name}", unread([["CRM Lead", self.lead.name]]))

		# and what they write next is counted from where it was
		self._sms("Incoming", "terzo")
		self.assertEqual(unread([["CRM Lead", self.lead.name]]).get(f"CRM Lead:{self.lead.name}"), 1)

	def test_nothing_new_since_is_nothing_to_read(self):
		"""The reply after the reply does not make its writer the one who read it."""
		from crm.api.conversations import mark_read

		self._sms("Incoming", "ci sei?")
		first = mark_read("CRM Lead", self.lead.name)
		again = mark_read("CRM Lead", self.lead.name)
		self.assertEqual(str(again["seen_until"]), str(first["seen_until"]))
		self.assertEqual(again["receipts"], 0)

	def test_a_count_is_only_given_to_what_is_unread(self):
		"""A number on a row the header calls read is two answers to one question."""
		from crm.api.conversations import unread

		self._sms("Incoming", "ci sei?")
		frappe.db.set_value("CRM Lead", self.lead.name, "conversation_unread", 0, update_modified=False)
		self.assertNotIn(f"CRM Lead:{self.lead.name}", unread([["CRM Lead", self.lead.name]]))

	def test_what_you_dealt_with_leaves_the_list(self):
		from crm.api.conversations import HANDLED, people, set_state

		self._sms("Incoming", "ci sei?")
		set_state("CRM Lead", self.lead.name, HANDLED)
		self.assertNotIn(self.lead.name, [row.name for row in people(view="open", limit=200)])


class TestTheViews(FrappeTestCase):
	"""Every inbox worth using has these few, and each one is one honest question."""

	def setUp(self):
		frappe.set_user("Administrator")
		self.them = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Aspetta", "last_name": "Prova"}
		).insert(ignore_permissions=True)
		self.us = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Risposto", "last_name": "Prova"}
		).insert(ignore_permissions=True)
		frappe.db.set_value(
			"CRM Lead",
			self.them.name,
			{"last_conversation_direction": "Incoming", "conversation_unread": 1},
			update_modified=False,
		)
		frappe.db.set_value(
			"CRM Lead",
			self.us.name,
			{"last_conversation_direction": "Outgoing", "conversation_unread": 0},
			update_modified=False,
		)

	def tearDown(self):
		frappe.db.rollback()

	def _in(self, view):
		from crm.api.conversations import people

		return [row.name for row in people(view=view, limit=500)]

	def test_reading_something_does_not_settle_it(self):
		from crm.api.conversations import mark_read

		# read this morning, still owed an answer: the badge goes, «in attesa di
		# risposta» does not — which is the one that costs money
		mark_read("CRM Lead", self.them.name)
		self.assertFalse(frappe.db.get_value("CRM Lead", self.them.name, "conversation_unread"))
		self.assertIn(self.them.name, self._in("unanswered"))

	def test_our_own_last_word_is_not_waiting_for_anything(self):
		self.assertNotIn(self.us.name, self._in("unanswered"))
		self.assertIn(self.us.name, self._in("open"))

	def test_what_is_filed_away_is_out_of_every_live_view(self):
		from crm.api.conversations import HANDLED, set_state

		set_state("CRM Lead", self.them.name, HANDLED)
		for view in ("open", "unanswered"):
			self.assertNotIn(self.them.name, self._in(view), view)
		self.assertIn(self.them.name, self._in("handled"))

	def test_a_view_nobody_defined_says_so(self):
		"""A stale name must not be answered with the base list.

		Falling back to «open» is how a renamed view passes unnoticed: the caller
		asks for a pile and silently gets everything still going on.
		"""
		from crm.api.conversations import people

		with self.assertRaises(frappe.ValidationError):
			people(view="unread", limit=1)

	def test_a_name_is_looked_for_everywhere_whatever_view_is_open(self):
		"""Searching inside the current view is how a CRM loses a customer.

		You look for somebody, find nothing, and conclude they are not there —
		when they were simply marked as dealt with last week.
		"""
		from crm.api.conversations import HANDLED, people, set_state

		set_state("CRM Lead", self.them.name, HANDLED)
		found = [row.name for row in people(view="open", search="Aspetta", limit=500)]
		self.assertIn(self.them.name, found)

	def test_the_numbers_beside_the_views_agree_with_the_views(self):
		# counted with the view's own filter rather than the length of a page of
		# it: the list stops at 200 rows, and the database a suite runs on can
		# hold more open conversations than that
		from crm.api.conversations import COUNTABLE, conditions_for, counts

		tally = counts()
		for view in COUNTABLE:
			self.assertEqual(tally.get(view), frappe.db.count("CRM Lead", conditions_for(view)), view)

	def test_the_unread_numbers_agree_with_the_unread_filter(self):
		from crm.api.conversations import COUNTABLE, conditions_for, counts

		tally = counts()
		for view in COUNTABLE:
			unread = frappe.db.count("CRM Lead", {**conditions_for(view), "conversation_unread": 1})
			self.assertEqual(tally.get(f"{view}_unread"), unread, view)

	def test_a_name_is_looked_for_read_or_not(self):
		"""«Only unread» narrows a view; a name typed is somebody wanted, read or not."""
		from crm.api.conversations import people

		found = [row.name for row in people(search="Risposto", waiting=1, limit=500)]
		self.assertIn(self.us.name, found)


class TestTheBlueTicksGoWhenItIsRead(FrappeTestCase):
	"""What the customer sees on their phone goes at the moment the CRM says the
	conversation was read, and at no other.

	It used to go when a chat was opened, while the badge stayed: the customer
	was told somebody had read them while the CRM said nobody had.
	"""

	def setUp(self):
		from crm.integrations.whatsapp.api import whatsapp_installed

		if not whatsapp_installed():
			self.skipTest("frappe_whatsapp is not installed on this bench")
		frappe.set_user("Administrator")
		self.was = frappe.db.get_single_value("FCRM Settings", "whatsapp_read_receipts")
		frappe.db.set_single_value("FCRM Settings", "whatsapp_read_receipts", 1)
		self.lead = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Spunte", "last_name": "Blu"}
		).insert(ignore_permissions=True)
		frappe.db.set_value("CRM Lead", self.lead.name, "conversation_unread", 1, update_modified=False)

	def tearDown(self):
		frappe.db.set_single_value("FCRM Settings", "whatsapp_read_receipts", self.was)
		frappe.db.rollback()

	def _from_them(self, minutes_ago, status="", reference=None):
		from frappe.utils import add_to_date

		reference = reference or ("CRM Lead", self.lead.name)
		doc = frappe.get_doc(
			{
				"doctype": "WhatsApp Message",
				"type": "Incoming",
				"message_type": "Manual",
				"content_type": "text",
				"message": "ci sei?",
				"message_id": frappe.generate_hash(length=20),
				"from": "393400000077",
				"to": "393883768154",
				"status": status,
				"reference_doctype": reference[0],
				"reference_name": reference[1],
			}
		)
		# a moment of its own each, so «the latest» is a fact and not a tie
		doc.creation = doc.modified = add_to_date(None, minutes=-minutes_ago)
		doc.db_insert()
		return doc.name

	def _told(self, call):
		"""What the call answers, and which messages it queued a receipt for."""
		from unittest.mock import patch

		with patch("frappe.enqueue") as enqueue:
			answer = call()
		return answer, [queued.kwargs.get("message") for queued in enqueue.call_args_list]

	def test_opening_it_tells_nobody(self):
		from crm.api.conversations import person

		self._from_them(5)
		_, told = self._told(lambda: person(self.lead.name))
		self.assertEqual(told, [])

	def test_reading_it_tells_whatsapp_once_for_the_latest(self):
		"""WhatsApp reads everything before a message as read too: one says it all."""
		from crm.api.conversations import mark_read

		self._from_them(10)
		latest = self._from_them(2)
		answer, told = self._told(lambda: mark_read("CRM Lead", self.lead.name))
		self.assertEqual(told, [latest])
		self.assertEqual(answer["receipts"], 1)

	def test_nothing_is_told_unless_the_site_asked_for_it(self):
		from crm.api.conversations import mark_read

		frappe.db.set_single_value("FCRM Settings", "whatsapp_read_receipts", 0)
		self._from_them(2)
		answer, told = self._told(lambda: mark_read("CRM Lead", self.lead.name))
		self.assertEqual(told, [])
		self.assertEqual(answer["receipts"], 0)
		# the badge is ours, and goes either way
		self.assertEqual(frappe.db.get_value("CRM Lead", self.lead.name, "conversation_unread"), 0)

	def test_what_was_already_told_is_not_told_again(self):
		from crm.api.conversations import READ_BY_US, mark_read

		self._from_them(2, status=READ_BY_US)
		_, told = self._told(lambda: mark_read("CRM Lead", self.lead.name))
		self.assertEqual(told, [])

	def test_handled_is_a_moment_of_reading_too(self):
		from crm.api.conversations import HANDLED, set_state

		latest = self._from_them(2)
		_, told = self._told(lambda: set_state("CRM Lead", self.lead.name, HANDLED))
		self.assertEqual(told, [latest])

	def test_the_second_reply_does_not_tell_twice(self):
		from crm.api.conversations import mark_read

		self._from_them(2)
		self._told(lambda: mark_read("CRM Lead", self.lead.name))
		_, told = self._told(lambda: mark_read("CRM Lead", self.lead.name))
		self.assertEqual(told, [])

	def test_unread_again_tells_nothing(self):
		from crm.api.conversations import mark_unread

		self._from_them(2)
		_, told = self._told(lambda: mark_unread("CRM Lead", self.lead.name))
		self.assertEqual(told, [])

	def test_what_they_wrote_on_their_deal_is_theirs_too(self):
		"""The conversation that was read is the person's, deals included."""
		from crm.api.conversations import mark_read

		organization = frappe.get_doc(
			{"doctype": "CRM Organization", "organization_name": "Spunte Srl"}
		).insert(ignore_permissions=True)
		deal = frappe.get_doc(
			{"doctype": "CRM Deal", "lead": self.lead.name, "organization": organization.name}
		).insert(ignore_permissions=True)
		on_the_deal = self._from_them(1, reference=("CRM Deal", deal.name))
		_, told = self._told(lambda: mark_read("CRM Lead", self.lead.name))
		self.assertEqual(told, [on_the_deal])

	def test_the_receipt_is_written_down_without_saving_the_message(self):
		"""Saving an incoming message runs what runs when one arrives."""
		from unittest.mock import patch

		from crm.api.conversations import READ_BY_US, send_read_receipt

		message = self._from_them(2)
		with (
			patch("crm.api.conversations.whatsapp_account", return_value=FakeAccount()),
			patch("requests.post", return_value=FakeAnswer(200, {"success": True})) as post,
			patch("frappe.model.document.Document.save") as save,
		):
			self.assertTrue(send_read_receipt(message))
		self.assertEqual(post.call_args.kwargs["json"]["status"], "read")
		self.assertEqual(
			post.call_args.kwargs["json"]["message_id"],
			frappe.db.get_value("WhatsApp Message", message, "message_id"),
		)
		save.assert_not_called()
		self.assertEqual(frappe.db.get_value("WhatsApp Message", message, "status"), READ_BY_US)

	def test_a_refused_receipt_is_not_written_down(self):
		from unittest.mock import patch

		from crm.api.conversations import READ_BY_US, send_read_receipt

		message = self._from_them(2)
		with (
			patch("crm.api.conversations.whatsapp_account", return_value=FakeAccount()),
			patch("requests.post", return_value=FakeAnswer(400, {"error": {"message": "too old"}})),
			patch("frappe.log_error"),
		):
			self.assertFalse(send_read_receipt(message))
		self.assertNotEqual(frappe.db.get_value("WhatsApp Message", message, "status"), READ_BY_US)


class FakeAccount:
	url = "https://graph.facebook.com"
	version = "v21.0"
	phone_id = "100000000000001"

	def get_password(self, fieldname):
		return "token"


class FakeAnswer:
	def __init__(self, status_code, body):
		self.status_code = status_code
		self.body = body
		self.text = str(body)

	def json(self):
		return self.body


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

	def test_giving_a_settled_one_to_a_colleague_does_not_read_it(self):
		from crm.api.conversations import HANDLED, mark_unread, set_state

		self._sms("Incoming", "grazie")
		set_state("CRM Lead", self.lead.name, HANDLED)
		mark_unread("CRM Lead", self.lead.name)
		set_state("CRM Lead", self.lead.name, HANDLED, assign_to="Administrator")
		self.assertEqual(self._state("conversation_unread"), 1)

	def test_undo_puts_it_back_as_it_was(self):
		from crm.api.conversations import HANDLED, OPEN, person, restore, set_state

		self._sms("Incoming", "ci sei?")
		was = person(self.lead.name)
		set_state("CRM Lead", self.lead.name, HANDLED)

		restore("CRM Lead", self.lead.name, was)
		self.assertEqual(self._state(), OPEN)
		self.assertEqual(self._state("conversation_unread"), 1)
		self.assertEqual(self._state("conversation_seen_until"), was.conversation_seen_until)

	def test_undo_does_not_bury_what_arrived_in_between(self):
		"""Putting «handled» back over a new message would hide the message."""
		from crm.api.conversations import HANDLED, OPEN, person, restore, set_state

		self._sms("Incoming", "ci sei?")
		was = person(self.lead.name)
		set_state("CRM Lead", self.lead.name, HANDLED)
		self._sms("Incoming", "pronto?")

		with self.assertRaises(frappe.ValidationError):
			restore("CRM Lead", self.lead.name, was)
		self.assertEqual(self._state(), OPEN)
		self.assertEqual(self._state("conversation_unread"), 1)

	def test_the_list_answers_the_four_questions_separately(self):
		from frappe.utils import add_to_date

		from crm.api.conversations import HANDLED, people, set_state

		parked = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Rinviata", "last_name": "Prova"}
		).insert(ignore_permissions=True)
		set_state("CRM Lead", parked.name, "Snoozed", until=add_to_date(None, days=1))
		set_state("CRM Lead", self.lead.name, HANDLED)

		def named(state):
			return [row.name for row in people(view=state, limit=200)]

		self.assertIn(self.lead.name, named("handled"))
		self.assertNotIn(self.lead.name, named("open"))
		self.assertIn(parked.name, named("snoozed"))
		self.assertNotIn(parked.name, named("open"))


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


class TestWhereAnInvoiceSitsInTheHistory(FrappeTestCase):
	"""An invoice's place in the stream is its own date, not the day it was typed.

	The posting date is the date printed on the document and the one somebody
	looks for it under, so an invoice entered today for the 20th belongs on the
	20th. When the two agree the creation time is kept — midnight would float
	today's invoice above the whole day's messages.
	"""

	def test_a_backdated_invoice_sits_on_the_date_it_carries(self):
		from frappe.utils import get_datetime

		from crm.api.activities import invoice_moment

		row = frappe._dict({"posting_date": "2026-09-20", "creation": "2026-09-25 14:32:00"})
		self.assertEqual(invoice_moment(row), get_datetime("2026-09-20"))

	def test_an_invoice_written_on_its_own_date_keeps_the_hour(self):
		from crm.api.activities import invoice_moment

		row = frappe._dict({"posting_date": "2026-09-25", "creation": "2026-09-25 14:32:00"})
		self.assertEqual(invoice_moment(row), "2026-09-25 14:32:00")

	def test_without_a_posting_date_it_sits_where_it_was_written(self):
		from crm.api.activities import invoice_moment

		row = frappe._dict({"posting_date": None, "creation": "2026-09-25 14:32:00"})
		self.assertEqual(invoice_moment(row), "2026-09-25 14:32:00")
