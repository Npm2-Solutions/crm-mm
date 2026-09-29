# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Whitelisted endpoints answer only to whoever may see what they return.

A patient portal is coming, and its patients log in as Website Users: every
whitelisted method without a permission check is theirs to call. So each
endpoint here is tried by someone it belongs to, by a Sales User outside the
sales hierarchy, and by a logged-in user with no CRM role at all.
"""

import inspect
import json
from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils.nestedset import rebuild_tree

from crm.api.appointments import get_calendar, get_scheduler_meta, get_workload
from crm.api.contact import get_linked_deals
from crm.api.doc import assigned_users_of, get_assigned_users, get_linked_docs_of_document, remove_assignments
from crm.fcrm.doctype.crm_call_log.crm_call_log import get_call_log
from crm.fcrm.doctype.crm_deal.api import get_deal_contacts
from crm.integrations.api import (
	find_contact_by_phone_number,
	get_contact_by_phone_number,
	get_contact_lead_or_deal_from_number,
	get_recording_url,
)
from crm.permissions.test_org_hierarchy import make_deal, make_hierarchy_node, make_lead, make_user
from crm.telephony.transcription import get_transcript, transcribe_now
from crm.tests.test_scheduling import SchedulingCase

MANAGER = "manager@perm.test"
REP = "rep@perm.test"
OUTSIDER = "outsider@perm.test"
PATIENT = "patient@perm.test"


def make_people():
	"""
	manager@perm.test   Sales Manager, top of the hierarchy
	└── rep@perm.test   Sales User
	outsider@perm.test  Sales User, not in the hierarchy
	patient@perm.test   Website User: logged in, no CRM role
	"""
	make_user(MANAGER, roles=["Sales Manager", "Sales User"])
	make_user(REP, roles=["Sales User"])
	make_user(OUTSIDER, roles=["Sales User"])
	make_user(PATIENT)

	manager = make_hierarchy_node(MANAGER, is_group=1)
	make_hierarchy_node(REP, reports_to=manager.name)
	rebuild_tree("CRM Sales Hierarchy")

	settings = frappe.get_single("FCRM Settings")
	settings.enable_sales_hierarchy = 1
	settings.save(ignore_permissions=True)


class PermissionTestCase(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		make_people()


class TestFixture(PermissionTestCase):
	def test_the_patient_is_a_website_user_with_no_crm_role(self):
		self.assertEqual(frappe.db.get_value("User", PATIENT, "user_type"), "Website User")
		self.assertFalse({"Sales User", "Sales Manager", "System Manager"} & set(frappe.get_roles(PATIENT)))


class TestCallLogs(PermissionTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.lead = make_lead(REP).name
		# the way telephony files a call: the lead under `links`, nobody we test as on the line
		cls.call = make_call_log(links=[("CRM Lead", cls.lead)]).name

	def test_the_leads_owner_and_their_manager_open_the_call(self):
		for user in (REP, MANAGER):
			with self.set_user(user):
				call = get_call_log(self.call)
			self.assertEqual(call["name"], self.call)
			self.assertEqual(call["_lead"], self.lead)

	def test_a_sales_user_outside_the_hierarchy_cannot_open_the_call(self):
		with self.set_user(OUTSIDER), self.assertRaises(frappe.PermissionError):
			get_call_log(self.call)

	def test_a_website_user_cannot_open_a_call(self):
		unfiled = make_call_log().name
		for name in (self.call, unfiled):
			with self.set_user(PATIENT), self.assertRaises(frappe.PermissionError):
				get_call_log(name)

	def test_whoever_took_the_call_opens_it(self):
		answered = make_call_log(links=[("CRM Lead", self.lead)], receiver=OUTSIDER).name
		with self.set_user(OUTSIDER):
			self.assertEqual(get_call_log(answered)["name"], answered)

	def test_a_call_filed_on_nobody_opens_for_any_sales_user(self):
		unfiled = make_call_log().name
		with self.set_user(OUTSIDER):
			self.assertEqual(get_call_log(unfiled)["name"], unfiled)

	def test_a_call_logged_by_hand_follows_its_deal(self):
		deal = make_deal(REP).name
		logged = make_call_log(reference_doctype="CRM Deal", reference_docname=deal).name
		with self.set_user(REP):
			self.assertEqual(get_call_log(logged)["_deal"], deal)
		with self.set_user(OUTSIDER), self.assertRaises(frappe.PermissionError):
			get_call_log(logged)

	def test_the_recording_plays_only_for_whoever_may_open_the_call(self):
		frappe.db.set_value("CRM Call Log", self.call, "recording_url", "https://recordings.test/call.mp3")
		upstream = MagicMock(status_code=200, headers={"Content-Type": "audio/mpeg"})
		upstream.iter_content.return_value = iter([b"audio"])
		with (
			self.set_user(REP),
			patch("crm.integrations.api._fetch_recording", return_value=upstream),
			patch("frappe.get_request_header", return_value=None),
		):
			response = get_recording_url(self.call)
		self.assertEqual(b"".join(response.response), b"audio")

		for user in (OUTSIDER, PATIENT):
			with (
				self.set_user(user),
				patch("crm.integrations.api._fetch_recording") as fetch,
				self.assertRaises(frappe.PermissionError),
			):
				get_recording_url(self.call)
			fetch.assert_not_called()

	def test_the_transcript_reads_only_for_whoever_may_open_the_call(self):
		frappe.db.set_value("CRM Call Log", self.call, "transcript", "Buongiorno, chiamo per l'esame.")
		with self.set_user(REP):
			self.assertEqual(get_transcript(self.call)["transcript"], "Buongiorno, chiamo per l'esame.")
		for user in (OUTSIDER, PATIENT):
			with self.set_user(user), self.assertRaises(frappe.PermissionError):
				get_transcript(self.call)

	def test_only_whoever_may_open_the_call_asks_for_a_transcript(self):
		# the rep gets past the permission check to the provider not being set up
		with self.set_user(REP), self.assertRaises(frappe.ValidationError):
			transcribe_now(self.call)
		for user in (OUTSIDER, PATIENT):
			with self.set_user(user), self.assertRaises(frappe.PermissionError):
				transcribe_now(self.call)


class TestAppointmentFeeds(SchedulingCase):
	"""The calendar has no sales hierarchy: it is the practice's day, the same for every Sales User."""

	def setUp(self):
		super().setUp()
		make_people()
		self.make_service("Visita permessi", [REP])
		start = self.tomorrow(10)
		self.make_appointment(
			"Visita permessi",
			start,
			[REP],
			participants=[{"participant_name": "Mario Rossi", "phone": "+393331234567"}],
		)
		self.day = start.date().isoformat()

	def test_every_sales_user_reads_the_calendar(self):
		for user in (REP, OUTSIDER):
			with self.set_user(user):
				feed = get_calendar(self.day, self.day, include_events=False)
				workload = get_workload(self.day, self.day)
				meta = get_scheduler_meta()
			row = next(a for a in feed["appointments"] if a["service"] == "Visita permessi")
			self.assertEqual([p["participant_name"] for p in row["participants"]], ["Mario Rossi"])
			self.assertEqual(workload["staff"][REP], 60)
			self.assertIn("Visita permessi", [s["name"] for s in meta["services"]])

	def test_a_website_user_reads_none_of_it(self):
		calls = {
			"calendar": lambda: get_calendar(self.day, self.day),
			"calendar by source": lambda: get_calendar(self.day, self.day, sources=["Internal", "Treatwell"]),
			"workload": lambda: get_workload(self.day, self.day),
			"scheduler meta": get_scheduler_meta,
		}
		for label, call in calls.items():
			with self.subTest(label), self.set_user(PATIENT), self.assertRaises(frappe.PermissionError):
				call()


class TestDealContacts(PermissionTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.contact = make_contact("Giulia", "Bianchi", "+39 333 765 4321")
		cls.deal = make_deal_with(REP, cls.contact)

	def test_a_deals_contacts_are_listed_to_whoever_may_read_the_deal(self):
		for user in (REP, MANAGER):
			with self.set_user(user):
				contacts = get_deal_contacts(self.deal)
			self.assertEqual([c["name"] for c in contacts], [self.contact])
		for user in (OUTSIDER, PATIENT):
			with self.set_user(user), self.assertRaises(frappe.PermissionError):
				get_deal_contacts(self.deal)


class TestContactDeals(PermissionTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.contact = make_contact("Giulia", "Bianchi", "+39 333 765 4321")
		cls.reps_deal = make_deal_with(REP, cls.contact)
		cls.outsiders_deal = make_deal_with(OUTSIDER, cls.contact)

	def test_a_contacts_deals_are_only_the_ones_the_user_may_read(self):
		seen = {}
		for user in ("Administrator", REP, MANAGER, OUTSIDER):
			with self.set_user(user):
				seen[user] = {d["name"] for d in get_linked_deals(self.contact)}
		self.assertEqual(seen["Administrator"], {self.reps_deal, self.outsiders_deal})
		self.assertEqual(seen[REP], {self.reps_deal})
		self.assertEqual(seen[MANAGER], {self.reps_deal})
		self.assertEqual(seen[OUTSIDER], {self.outsiders_deal})

	def test_a_website_user_reads_no_contacts_deals(self):
		with self.set_user(PATIENT), self.assertRaises(frappe.PermissionError):
			get_linked_deals(self.contact)


LEAD_NUMBER = "+39 333 123 4567"
DEAL_NUMBER = "+39 333 222 3344"


class TestPhoneLookups(PermissionTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.lead = (
			frappe.get_doc(
				{
					"doctype": "CRM Lead",
					"first_name": "Mario",
					"last_name": "Rossi",
					"mobile_no": LEAD_NUMBER,
					"lead_owner": REP,
				}
			)
			.insert(ignore_permissions=True)
			.name
		)
		cls.contact = make_contact("Anna", "Neri", DEAL_NUMBER)
		cls.deal = make_deal_with(REP, cls.contact)

	def test_whoever_may_read_the_lead_learns_whose_number_it_is(self):
		for user in (REP, MANAGER):
			with self.set_user(user):
				found = get_contact_by_phone_number(LEAD_NUMBER)
			self.assertEqual(found["lead"], self.lead)
			self.assertEqual(found["full_name"], "Mario Rossi")

	def test_a_lead_out_of_sight_answers_like_a_number_nobody_has(self):
		for user in (OUTSIDER, PATIENT):
			with self.set_user(user):
				# what get_contact answers for an unknown number: the number it searched
				self.assertEqual(get_contact_by_phone_number(LEAD_NUMBER), {"mobile_no": "3331234567"})

	def test_a_contacts_deal_is_named_only_to_whoever_may_read_it(self):
		with self.set_user(REP):
			self.assertEqual(get_contact_by_phone_number(DEAL_NUMBER)["deal"], self.deal)
		with self.set_user(OUTSIDER):
			found = get_contact_by_phone_number(DEAL_NUMBER)
		self.assertEqual(found["name"], self.contact)
		self.assertNotIn("deal", found)
		with self.set_user(PATIENT):
			self.assertEqual(get_contact_by_phone_number(DEAL_NUMBER), {"mobile_no": "3332223344"})

	def test_webhooks_still_file_calls_and_messages_as_guest(self):
		with self.set_user("Guest"):
			self.assertEqual(find_contact_by_phone_number(LEAD_NUMBER)["lead"], self.lead)
			self.assertEqual(get_contact_lead_or_deal_from_number(LEAD_NUMBER), (self.lead, "CRM Lead"))

	def test_whose_number_it_is_is_asked_over_http_only_through_the_checked_lookup(self):
		with self.set_user(PATIENT):
			frappe.is_whitelisted(get_contact_by_phone_number)
			with self.assertRaises(frappe.PermissionError):
				frappe.is_whitelisted(get_contact_lead_or_deal_from_number)


class TestLinkedDocsAndAssignees(PermissionTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		# a lead is assigned to its owner as it is made
		cls.lead = make_lead(REP).name
		cls.call = make_call_log(links=[("CRM Lead", cls.lead)]).name
		# the person's deal, in the hands of somebody the rep cannot see
		cls.deal = make_deal(OUTSIDER).name
		frappe.db.set_value("CRM Deal", cls.deal, "lead", cls.lead)

	def test_assignees_are_listed_to_whoever_may_read_the_record(self):
		for user in (REP, MANAGER):
			with self.set_user(user):
				self.assertEqual(get_assigned_users("CRM Lead", self.lead), [REP])
		for user in (OUTSIDER, PATIENT):
			with self.set_user(user), self.assertRaises(frappe.PermissionError):
				get_assigned_users("CRM Lead", self.lead)

	def test_the_server_still_finds_assignees_as_guest(self):
		with self.set_user("Guest"):
			self.assertEqual(assigned_users_of("CRM Lead", self.lead), [REP])

	def test_linked_documents_are_only_the_ones_the_user_may_read(self):
		linked = get_linked_docs_of_document("CRM Lead", self.lead)
		self.assertLessEqual({self.call, self.deal}, {d["reference_docname"] for d in linked})

		with self.set_user(REP):
			linked = {d["reference_docname"] for d in get_linked_docs_of_document("CRM Lead", self.lead)}
		self.assertIn(self.call, linked)
		self.assertNotIn(self.deal, linked)

		for user in (OUTSIDER, PATIENT):
			with self.set_user(user), self.assertRaises(frappe.PermissionError):
				get_linked_docs_of_document("CRM Lead", self.lead)

	def test_a_record_that_is_gone_has_nothing_linked(self):
		with self.set_user(REP):
			self.assertEqual(get_linked_docs_of_document("CRM Lead", "CRM-LEAD-GONE"), [])


class TestRemoveAssignments(PermissionTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		# a lead is assigned to its owner as it is made
		cls.lead = make_lead(REP).name

	def test_the_caller_cannot_ask_to_skip_permissions(self):
		self.assertNotIn("ignore_permissions", inspect.signature(remove_assignments).parameters)

	def test_nobody_outside_the_lead_unassigns_it(self):
		for user in (OUTSIDER, PATIENT):
			# the way a request reaches it, asking for ignore_permissions all the same
			with self.set_user(user), self.assertRaises(frappe.PermissionError):
				frappe.call(
					remove_assignments,
					doctype="CRM Lead",
					name=self.lead,
					assignees=json.dumps([REP]),
					ignore_permissions=True,
				)
		self.assertEqual(frappe.db.get_value("CRM Lead", self.lead, "lead_owner"), REP)
		self.assertEqual(assigned_users_of("CRM Lead", self.lead), [REP])

	def test_whoever_may_read_the_lead_unassigns_it(self):
		with self.set_user(MANAGER):
			remove_assignments("CRM Lead", self.lead, json.dumps([REP]))
		self.assertEqual(assigned_users_of("CRM Lead", self.lead), [])
		self.assertFalse(frappe.db.get_value("CRM Lead", self.lead, "lead_owner"))


def make_call_log(links=(), **fields):
	doc = frappe.get_doc(
		{
			"doctype": "CRM Call Log",
			"type": "Incoming",
			"status": "Completed",
			# not Manual: a call logged by hand fills its caller in from the session
			"telephony_medium": "Twilio",
			"from": "+393331234567",
			"to": "+390212345678",
			**fields,
		}
	)
	for doctype, name in links:
		doc.append("links", {"link_doctype": doctype, "link_name": name})
	return doc.insert(ignore_permissions=True)


def make_contact(first_name, last_name, mobile_no):
	contact = frappe.get_doc({"doctype": "Contact", "first_name": first_name, "last_name": last_name})
	contact.append("phone_nos", {"phone": mobile_no, "is_primary_mobile_no": 1})
	return contact.insert(ignore_permissions=True).name


def make_deal_with(owner, contact):
	deal = make_deal(owner)
	deal.append("contacts", {"contact": contact, "is_primary": 1})
	deal.save(ignore_permissions=True)
	return deal.name
