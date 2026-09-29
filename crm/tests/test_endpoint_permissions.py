# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Whitelisted endpoints answer only to whoever may see what they return.

A patient portal is coming, and its patients log in as Website Users: every
whitelisted method without a permission check is theirs to call. So each
endpoint here is tried by someone it belongs to, by a Sales User outside the
sales hierarchy, and by a logged-in user with no CRM role at all.
"""

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils.nestedset import rebuild_tree

from crm.api.appointments import get_calendar, get_scheduler_meta, get_workload
from crm.api.contact import get_linked_deals
from crm.fcrm.doctype.crm_call_log.crm_call_log import get_call_log
from crm.fcrm.doctype.crm_deal.api import get_deal_contacts
from crm.integrations.api import get_recording_url
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
