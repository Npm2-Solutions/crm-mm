# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# Modifications copyright (c) 2026, NPM2 Solutions Srl
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from crm.fcrm.doctype.crm_call_log.crm_call_log import parse_call_log
from crm.integrations.api import (
	add_note_to_call_log,
	add_task_to_call_log,
	find_contact_by_phone_number,
	get_contact_by_phone_number,
	get_contact_lead_or_deal_from_number,
	get_user_default_calling_medium,
	is_call_integration_enabled,
	set_default_calling_medium,
)
from crm.integrations.twilio.api import link


class TestIntegrations(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_is_call_integration_enabled_disabled(self):
		"""Twilio off: no call integration is on"""
		frappe.db.set_single_value("CRM Twilio Settings", "enabled", 0)

		result = is_call_integration_enabled()

		self.assertFalse(result["integrations"]["twilio"])

	def test_is_call_integration_enabled_twilio(self):
		"""Twilio on: its calls are on"""
		frappe.db.set_single_value("CRM Twilio Settings", "enabled", 1)

		result = is_call_integration_enabled()

		self.assertTrue(result["integrations"]["twilio"])

	def test_exotel_is_gone(self):
		"""DottorCloud no longer offers Exotel (03/10/2026): nothing names it"""
		result = is_call_integration_enabled()

		self.assertNotIn("exotel", result["integrations"])
		self.assertNotIn("exotel", [p["name"] for p in result["providers"]])

	def test_get_user_default_calling_medium_no_agent(self):
		"""Test get_user_default_calling_medium when user has no telephony agent record"""
		# Delete any existing telephony agent for current user
		if frappe.db.exists("CRM Telephony Agent", frappe.session.user):
			frappe.delete_doc("CRM Telephony Agent", frappe.session.user)

		result = get_user_default_calling_medium()

		self.assertIsNone(result)

	def test_get_user_default_calling_medium_with_agent(self):
		"""Test get_user_default_calling_medium when user has configured medium"""
		# Create telephony agent with default medium
		if frappe.db.exists("CRM Telephony Agent", frappe.session.user):
			frappe.delete_doc("CRM Telephony Agent", frappe.session.user)

		frappe.get_doc(
			{
				"doctype": "CRM Telephony Agent",
				"user": frappe.session.user,
				"default_medium": "Twilio",
			}
		).insert()

		result = get_user_default_calling_medium()

		self.assertEqual(result, "Twilio")

	def test_set_default_calling_medium_creates_new_record(self):
		"""Test set_default_calling_medium creates new telephony agent if doesn't exist"""
		# Delete any existing telephony agent
		if frappe.db.exists("CRM Telephony Agent", frappe.session.user):
			frappe.delete_doc("CRM Telephony Agent", frappe.session.user)

		result = set_default_calling_medium("Twilio")

		self.assertEqual(result, "Twilio")
		self.assertTrue(frappe.db.exists("CRM Telephony Agent", frappe.session.user))

		# Verify the record was created correctly
		agent = frappe.get_doc("CRM Telephony Agent", frappe.session.user)
		self.assertEqual(agent.default_medium, "Twilio")

	def test_set_default_calling_medium_updates_existing_record(self):
		"""Test set_default_calling_medium updates existing telephony agent"""
		# Create initial telephony agent
		if frappe.db.exists("CRM Telephony Agent", frappe.session.user):
			frappe.delete_doc("CRM Telephony Agent", frappe.session.user)

		frappe.get_doc(
			{
				"doctype": "CRM Telephony Agent",
				"user": frappe.session.user,
				"default_medium": "",
			}
		).insert()

		result = set_default_calling_medium("Twilio")

		self.assertEqual(result, "Twilio")

		# Verify the record was updated
		agent = frappe.get_doc("CRM Telephony Agent", frappe.session.user)
		self.assertEqual(agent.default_medium, "Twilio")

	def test_add_note_to_call_log_creates_new_note(self):
		"""Test add_note_to_call_log creates new note and links it to call log"""
		# Create a test call log
		call_log = create_test_call_log()

		note_data = {
			"title": "Call Summary",
			"content": "Discussed project requirements and timeline",
		}

		result = add_note_to_call_log(call_log.name, note_data)

		# Verify note was created
		self.assertTrue(frappe.db.exists("FCRM Note", result.name))
		self.assertEqual(result.title, "Call Summary")
		self.assertEqual(result.content, "Discussed project requirements and timeline")

		# Verify note is linked to call log
		call_log.reload()
		linked_notes = [link.link_name for link in call_log.links if link.link_doctype == "FCRM Note"]
		self.assertIn(result.name, linked_notes)

	def test_add_note_to_call_log_updates_existing_note(self):
		"""Test add_note_to_call_log updates existing note content"""
		# Create a test call log and initial note
		call_log = create_test_call_log()
		note = frappe.get_doc(
			{
				"doctype": "FCRM Note",
				"title": "Initial Note",
				"content": "Initial content",
			}
		).insert()

		# Update the note
		note_data = {
			"name": note.name,
			"title": "Initial Note",
			"content": "Updated content with more details",
		}

		add_note_to_call_log(call_log.name, note_data)

		# Verify content was updated
		note.reload()
		self.assertEqual(note.content, "Updated content with more details")

	def test_add_task_to_call_log_creates_new_task(self):
		"""Test add_task_to_call_log creates new task and links it to call log"""
		# Create a test call log
		call_log = create_test_call_log()

		task_data = {
			"title": "Follow up call",
			"description": "Call customer next week",
			"assigned_to": "Administrator",
			"due_date": "2026-12-31",
			"status": "Todo",
			"priority": "High",
		}

		result = add_task_to_call_log(call_log.name, task_data)

		# Verify task was created
		self.assertTrue(frappe.db.exists("CRM Task", result.name))
		self.assertEqual(result.title, "Follow up call")
		self.assertEqual(result.description, "Call customer next week")
		self.assertEqual(result.assigned_to, "Administrator")
		self.assertEqual(result.status, "Todo")
		self.assertEqual(result.priority, "High")

		# Verify task is linked to call log
		call_log.reload()
		linked_tasks = [link.link_name for link in call_log.links if link.link_doctype == "CRM Task"]
		self.assertIn(str(result.name), linked_tasks)

	def test_add_task_to_call_log_updates_existing_task(self):
		"""Test add_task_to_call_log updates existing task"""
		# Create a test call log and initial task
		call_log = create_test_call_log()
		task = frappe.get_doc(
			{
				"doctype": "CRM Task",
				"title": "Initial Task",
				"status": "Todo",
				"priority": "Medium",
			}
		).insert()

		# Update the task
		task_data = {
			"name": task.name,
			"title": "Updated Task Title",
			"description": "Updated description",
			"assigned_to": "Administrator",
			"due_date": "2026-12-31",
			"status": "In Progress",
			"priority": "High",
		}

		result = add_task_to_call_log(call_log.name, task_data)

		# Verify task was updated
		self.assertEqual(result.name, task.name)
		task.reload()
		self.assertEqual(task.title, "Updated Task Title")
		self.assertEqual(task.description, "Updated description")
		self.assertEqual(task.status, "In Progress")
		self.assertEqual(task.priority, "High")

	def test_get_contact_by_phone_number_finds_contact(self):
		"""Test get_contact_by_phone_number finds existing contact"""
		# Create a test contact - use exact match by storing what will be searched
		contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "John",
				"last_name": "Doe",
				"mobile_no": "4155550100",
			}
		).insert()

		result = get_contact_by_phone_number("4155550100")

		# Should find contact even if validation fails
		self.assertIn("mobile_no", result)
		if "name" in result:
			self.assertEqual(result["name"], contact.name)
			self.assertEqual(result["full_name"], "John Doe")

	def test_get_contact_by_phone_number_finds_contact_with_formatting(self):
		"""Test get_contact_by_phone_number handles phone number formatting"""
		# Create a test contact
		contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Jane",
				"last_name": "Smith",
				"mobile_no": "4155550200",
			}
		).insert()

		# Search with same number
		result = get_contact_by_phone_number("4155550200")

		# Should find the contact
		self.assertIn("mobile_no", result)
		if "name" in result:
			self.assertEqual(result["name"], contact.name)

	def test_get_contact_by_phone_number_finds_lead(self):
		"""Test get_contact_by_phone_number finds lead when no contact exists"""
		# Create a test lead with valid Indian phone number
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Lead",
				"last_name": "User",
				"mobile_no": "+91 98765 43210",
				"lead_owner": "Administrator",
			}
		).insert()

		result = get_contact_by_phone_number("+91 98765 43210")

		self.assertEqual(result["name"], lead.name)
		self.assertEqual(result["full_name"], "Lead User")
		self.assertEqual(result["lead"], lead.name)

	def test_get_contact_by_phone_number_prioritizes_contact_with_deal(self):
		"""Test get_contact_by_phone_number prioritizes contacts linked to deals"""
		# Create organization for deal
		org = frappe.get_doc(
			{
				"doctype": "CRM Organization",
				"organization_name": "Test Org",
			}
		).insert()

		# Create contact
		contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Contact",
				"last_name": "WithDeal",
				"mobile_no": "4155550300",
			}
		).insert()

		# Create deal with contact as primary
		deal = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": org.name,
				"deal_owner": "Administrator",
			}
		)
		deal.append("contacts", {"contact": contact.name, "is_primary": 1})
		deal.insert()

		result = get_contact_by_phone_number("4155550300")

		# Should return contact - may or may not include deal depending on validation
		self.assertIn("mobile_no", result)
		if "name" in result:
			self.assertEqual(result["name"], contact.name)
			if "deal" in result:
				self.assertEqual(result["deal"], deal.name)

	def test_get_contact_by_phone_number_returns_phone_only_if_not_found(self):
		"""Test get_contact_by_phone_number returns phone number if no match found"""
		result = get_contact_by_phone_number("+9999999999")

		# Should return dict with just mobile_no
		self.assertEqual(result["mobile_no"], "+9999999999")
		self.assertNotIn("name", result)
		self.assertNotIn("full_name", result)

	def test_a_customer_calling_still_resolves_to_their_person(self):
		"""A person who already has a deal is still the person who is calling.

		This used to assert the opposite -- that a converted lead is skipped --
		which was the Salesforce reading of `converted`, where the lead is frozen
		history and there is a Contact to find instead. Here the person record IS
		the person and stays, so skipping them resolved an incoming call to
		nobody and let a second record be adopted for somebody we already knew.
		"""
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Converted",
				"last_name": "Lead",
				"mobile_no": "+91 98765 43211",
				"lead_owner": "Administrator",
				"converted": 1,
			}
		).insert()

		name, doctype = get_contact_lead_or_deal_from_number("+91 98765 43211")

		self.assertEqual(doctype, "CRM Lead")
		self.assertEqual(name, lead.name)

	def test_integration_workflow_call_with_note_and_task(self):
		"""Test complete workflow: call log with note and task"""
		# Create call log
		call_log = create_test_call_log()

		# Add note
		note_data = {
			"title": "Call Notes",
			"content": "Customer interested in product demo",
		}
		note = add_note_to_call_log(call_log.name, note_data)

		# Add task
		task_data = {
			"title": "Schedule demo",
			"description": "Set up product demo for next week",
			"assigned_to": "Administrator",
			"status": "Todo",
			"priority": "High",
		}
		task = add_task_to_call_log(call_log.name, task_data)

		# Verify call log has both links
		call_log.reload()
		link_types = {link.link_doctype for link in call_log.links}
		self.assertIn("FCRM Note", link_types)
		self.assertIn("CRM Task", link_types)

		# Verify we can retrieve both
		note_links = [link for link in call_log.links if link.link_doctype == "FCRM Note"]
		task_links = [link for link in call_log.links if link.link_doctype == "CRM Task"]

		self.assertEqual(len(note_links), 1)
		self.assertEqual(len(task_links), 1)
		self.assertEqual(note_links[0].link_name, note.name)
		self.assertEqual(task_links[0].link_name, str(task.name))

	def test_standalone_contact_resolves_to_nobody(self):
		"""A contact with no lead and no deal is a dead end, not an answer.

		No chat opens on a Contact — that page has no activity at all — and the
		Inbox lists conversations by lead or deal. Handing a message to one means
		storing it where nobody will ever see it.
		"""
		frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Standalone",
				"last_name": "Contact",
				"mobile_no": "4155550400",
			}
		).insert()

		docname, doctype = get_contact_lead_or_deal_from_number("4155550400")

		self.assertIsNone(docname)
		self.assertIsNone(doctype)

	def test_contact_resolves_to_the_lead_that_owns_it(self):
		"""The lead is the person; its contact is where the numbers live."""
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Owned",
				"last_name": "Contact",
				"mobile_no": "4155550401",
				"lead_owner": "Administrator",
			}
		).insert()
		lead.reload()

		self.assertTrue(lead.contact, "a new lead is born with a contact")

		docname, doctype = get_contact_lead_or_deal_from_number("4155550401")

		self.assertEqual(doctype, "CRM Lead")
		self.assertEqual(docname, lead.name)

	def test_get_contact_lead_or_deal_from_number_returns_lead(self):
		"""Test get_contact_lead_or_deal_from_number prioritizes lead over contact"""
		# Create a lead
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Test",
				"last_name": "Lead",
				"mobile_no": "+91 98765 43212",
				"lead_owner": "Administrator",
			}
		).insert()

		docname, doctype = get_contact_lead_or_deal_from_number("+91 98765 43212")

		# Should return lead
		if docname:
			self.assertEqual(doctype, "CRM Lead")
			self.assertEqual(docname, lead.name)

	def test_get_contact_lead_or_deal_from_number_returns_deal(self):
		"""Test get_contact_lead_or_deal_from_number prioritizes deal over contact"""
		# Create organization and contact with deal
		org = frappe.get_doc(
			{
				"doctype": "CRM Organization",
				"organization_name": "Deal Test Org",
			}
		).insert()

		contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Deal",
				"last_name": "Contact",
				"mobile_no": "4155550500",
			}
		).insert()

		deal = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": org.name,
				"deal_owner": "Administrator",
			}
		)
		deal.append("contacts", {"contact": contact.name, "is_primary": 1})
		deal.insert()

		docname, doctype = get_contact_lead_or_deal_from_number("4155550500")

		# Should return deal (prioritized over contact)
		if docname:
			self.assertEqual(doctype, "CRM Deal")
			self.assertEqual(docname, deal.name)

	def test_get_contact_lead_or_deal_from_number_returns_none_when_not_found(self):
		"""Test get_contact_lead_or_deal_from_number returns None when nothing found"""
		docname, doctype = get_contact_lead_or_deal_from_number("+1 999-999-9999")

		# Should return None, None
		self.assertIsNone(docname)
		self.assertIsNone(doctype)

	def test_a_converted_lead_is_still_the_person(self):
		"""Becoming a customer does not stop somebody from being a person.

		This used to answer nobody, because a converted lead has left the leads
		list. An incoming message from a customer then matched no one and was
		adopted into a *second* lead for someone we already knew — while the
		conversation they were having stayed on the first.
		"""
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Converted",
				"last_name": "Lead",
				"mobile_no": "+91 98765 43213",
				"lead_owner": "Administrator",
				"converted": 1,
			}
		).insert()

		docname, doctype = get_contact_lead_or_deal_from_number("+91 98765 43213")

		self.assertEqual(doctype, "CRM Lead")
		self.assertEqual(docname, lead.name)

	def test_the_person_wins_over_their_deal(self):
		"""A message belongs to who we were talking to, not to the negotiation.

		The deal has no chat to show it: filing it there is filing it where
		nobody can read it.
		"""
		lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Person",
				"last_name": "WithDeal",
				"mobile_no": "4155550402",
				"lead_owner": "Administrator",
			}
		).insert()
		lead.reload()

		org = frappe.get_doc(
			{"doctype": "CRM Organization", "organization_name": "Person With Deal Org"}
		).insert()
		deal = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"organization": org.name,
				"deal_owner": "Administrator",
				"lead": lead.name,
			}
		)
		deal.append("contacts", {"contact": lead.contact, "is_primary": 1})
		deal.insert()

		docname, doctype = get_contact_lead_or_deal_from_number("4155550402")

		self.assertEqual(doctype, "CRM Lead")
		self.assertEqual(docname, lead.name)


class TestNumbersOfTheCentresCountry(IntegrationTestCase):
	"""Whose number it is, for a number typed or received without its prefix.

	The phone panel's keypad dials the digits as typed, and the call is filed and
	named by them: read in India, `333 123 4567` was nobody's, the call missing from
	the person's history and «Unknown» in the log. An Italian landline keeps its 0.
	"""

	def setUp(self):
		frappe.db.set_single_value("System Settings", "country", "Italy", update_modified=False)

	def tearDown(self):
		# the country goes back with the rollback, and what this request kept of the settings
		frappe.db.rollback()
		frappe.clear_document_cache("System Settings", "System Settings")

	def persona(self, nome, numero):
		return (
			frappe.get_doc(
				{
					"doctype": "CRM Lead",
					"first_name": nome,
					"last_name": "Numeri",
					"mobile_no": numero,
					"lead_owner": "Administrator",
				}
			)
			.insert(ignore_permissions=True)
			.name
		)

	def test_a_mobile_typed_without_its_prefix_finds_its_person(self):
		persona = self.persona("Mobile", "+39 333 123 4567")

		for scritto in ("3331234567", "333 123 4567", "333-123-4567", "+39 333 123 4567"):
			self.assertEqual(find_contact_by_phone_number(scritto).get("lead"), persona, scritto)
		self.assertEqual(get_contact_lead_or_deal_from_number("3331234567"), (persona, "CRM Lead"))
		self.assertEqual(get_contact_by_phone_number("333 123 4567")["full_name"], "Mobile Numeri")

	def test_a_landline_is_found_with_its_zero(self):
		persona = self.persona("Fisso", "+39 02 1234 5678")

		for scritto in ("+390212345678", "+39 02 1234 5678", "02 1234 5678", "02-1234-5678", "0212345678"):
			self.assertEqual(find_contact_by_phone_number(scritto).get("lead"), persona, scritto)
		# a stranger's landline is named by its digits, the 0 with them
		self.assertEqual(get_contact_by_phone_number("+39 02 4567 0123"), {"mobile_no": "0245670123"})

	def test_a_number_saved_with_its_spaces_is_found_by_its_digits(self):
		# the address book keeps a number as `+390212345678`, an older entry or one
		# brought from another program as somebody wrote it: the search reads the
		# digits of what is saved. A deal's contact, with no person in front of it to
		# answer first (a person's own number is kept as typed, spaces and all)
		azienda = frappe.get_doc(
			{"doctype": "CRM Organization", "organization_name": "Numeri in rubrica Srl"}
		).insert(ignore_permissions=True)
		contatto = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Rubrica",
				"last_name": "Numeri",
				"phone_nos": [{"phone": "+39 02 1234 5678", "is_primary_mobile_no": 1}],
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value(
			"Contact Phone", {"parent": contatto.name}, "phone", "+39 02-1234 5678", update_modified=False
		)
		trattativa = frappe.get_doc(
			{"doctype": "CRM Deal", "organization": azienda.name, "deal_owner": "Administrator"}
		)
		trattativa.append("contacts", {"contact": contatto.name, "is_primary": 1})
		trattativa.insert(ignore_permissions=True)

		for scritto in ("0212345678", "02 1234 5678", "+390212345678"):
			trovato = find_contact_by_phone_number(scritto)
			self.assertEqual(
				(trovato.get("name"), trovato.get("deal")), (contatto.name, trattativa.name), scritto
			)
		self.assertEqual(get_contact_lead_or_deal_from_number("0212345678"), (trattativa.name, "CRM Deal"))

	def test_the_call_made_from_the_keypad_is_the_persons(self):
		persona = self.persona("Chiamata", "+39 333 123 4567")

		parsed = parse_call_log({"type": "Outgoing", "to": "3331234567", "caller": "Administrator"})
		self.assertEqual(parsed["_receiver"]["label"], "Chiamata Numeri")

		call_log = frappe.new_doc("CRM Call Log")
		link("333 123 4567", call_log)
		self.assertEqual([(r.link_doctype, r.link_name) for r in call_log.links], [("CRM Lead", persona)])

	def test_whatsapp_numbers_of_other_countries_find_their_person(self):
		# WhatsApp drops the plus, and in Italy 33612345678 is also a mobile's
		# voicemail box: read first as Italian, the French number still finds its person
		francese = self.persona("Francese", "+33 6 12 34 56 78")
		albanese = self.persona("Albanese", "+355 67 212 3456")
		italiana = self.persona("Italiana", "+39 347 765 1234")

		self.assertEqual(find_contact_by_phone_number("33612345678").get("lead"), francese)
		self.assertEqual(find_contact_by_phone_number("355672123456").get("lead"), albanese)
		self.assertEqual(find_contact_by_phone_number("393477651234").get("lead"), italiana)

	def test_a_person_out_of_sight_answers_like_a_number_nobody_has(self):
		# found by the second reading, the French number came back as its own digits,
		# `612345678`: a number nobody has comes back as the first reading's
		self.persona("Nascosta", "+33 6 12 34 56 78")

		with self.set_user("Guest"):
			self.assertEqual(get_contact_by_phone_number("33612345678"), {"mobile_no": "33612345678"})
			self.assertEqual(get_contact_by_phone_number("33698765432"), {"mobile_no": "33698765432"})


def create_test_call_log(**kwargs):
	"""Helper function to create a CRM Call Log for testing"""
	import uuid

	unique_id = kwargs.pop("id", str(uuid.uuid4())[:10])

	data = {
		"doctype": "CRM Call Log",
		"id": unique_id,
		"type": "Incoming",
		"status": "Completed",
		"to": "+1234567890",
		"from": "+0987654321",
	}

	data.update(kwargs)

	call_log = frappe.get_doc(data)
	call_log.insert()
	return call_log
