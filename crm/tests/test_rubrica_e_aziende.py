# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The address book follows the person, and a company is written like a person.

A practitioner who sees their own people read the whole centre's names, emails and
phones in the address book, and was offered a company's deletion: an entry now
follows the person who owns it, writing a company asks for writing people and
deleting one is the Manager's, as deleting a person is (doc 30).
"""

import frappe

from crm.api.contact import get_owning_lead
from crm.api.doc import get_doc_permissions
from crm.tests.test_livelli_facoltativi import (
	AMMINISTRAZIONE,
	MANAGER,
	OPERATORE,
	SEGRETERIA,
	FacoltativiTestCase,
)


def _contatto_di(persona) -> str:
	return frappe.db.get_value("CRM Lead", persona.name, "contact")


class TestTheAddressBookFollowsThePerson(FacoltativiTestCase):
	def legge(self, user: str, contatto: str) -> bool:
		self.come(user)
		try:
			per_riga = frappe.has_permission("Contact", "read", doc=contatto)
			in_lista = bool(frappe.get_list("Contact", filters={"name": contatto}))
			self.assertEqual(per_riga, in_lista, "the list and the record must agree")
			return per_riga
		finally:
			frappe.set_user("Administrator")

	def test_the_practitioner_reads_the_entries_of_their_people(self):
		contatto = _contatto_di(self.persona)
		self.assertTrue(contatto, "every person carries an entry of their own")
		self.assertFalse(self.legge(OPERATORE, contatto))
		frappe.db.set_value("CRM Lead", self.persona.name, "lead_owner", OPERATORE)
		self.assertTrue(self.legge(OPERATORE, contatto))

	def test_the_front_desk_reads_them_all(self):
		self.assertTrue(self.legge(SEGRETERIA, _contatto_di(self.persona)))

	def test_an_entry_nobody_owns_is_the_centres(self):
		di_nessuno = frappe.get_doc({"doctype": "Contact", "first_name": "Fornitore"}).insert(
			ignore_permissions=True
		)
		self.assertTrue(self.legge(OPERATORE, di_nessuno.name))

	def test_the_owner_opens_only_where_it_is_read(self):
		contatto = _contatto_di(self.persona)
		self.come(OPERATORE)
		self.assertIsNone(get_owning_lead(contatto))
		frappe.set_user("Administrator")
		frappe.db.set_value("CRM Lead", self.persona.name, "lead_owner", OPERATORE)
		self.come(OPERATORE)
		self.assertEqual(get_owning_lead(contatto), self.persona.name)


class TestAnEntryIsWrittenLikeItsPerson(FacoltativiTestCase):
	"""The entry's email and phone are written back to the person: Accounting, which
	reads people without changing them, changed them through the address book."""

	def test_who_reads_the_person_reads_the_entry_but_does_not_change_it(self):
		contatto = _contatto_di(self.persona)
		self.come(AMMINISTRAZIONE)
		self.assertTrue(frappe.has_permission("Contact", "read", doc=contatto))
		self.assertFalse(frappe.has_permission("Contact", "write", doc=contatto))
		self.assertFalse(frappe.has_permission("Contact", "delete", doc=contatto))
		permessi = get_doc_permissions("Contact", contatto)["permissions"]
		self.assertEqual(permessi["write"], 0)
		voce = frappe.get_doc("Contact", contatto)
		voce.first_name = "Cambiato"
		with self.assertRaises(frappe.PermissionError):
			voce.save()

	def test_the_front_desk_changes_it(self):
		self.come(SEGRETERIA)
		self.assertTrue(frappe.has_permission("Contact", "write", doc=_contatto_di(self.persona)))

	def test_what_the_server_writes_for_the_person_goes_through(self):
		# a person saved by somebody who writes people carries the change to the entry
		self.come(SEGRETERIA)
		persona = frappe.get_doc("CRM Lead", self.persona.name)
		persona.mobile_no = "+393339876543"
		persona.save()
		self.assertEqual(frappe.db.get_value("Contact", persona.contact, "mobile_no"), "+393339876543")


class TestACompanyIsWrittenLikeAPerson(FacoltativiTestCase):
	def setUp(self):
		super().setUp()
		self.azienda = frappe.get_doc(
			{"doctype": "CRM Organization", "organization_name": "Studio Associato Test"}
		).insert(ignore_permissions=True)

	def test_only_the_manager_deletes_one(self):
		self.come(OPERATORE)
		self.assertTrue(frappe.has_permission("CRM Organization", "write", doc=self.azienda.name))
		self.assertFalse(frappe.has_permission("CRM Organization", "delete", doc=self.azienda.name))
		self.come(MANAGER)
		self.assertTrue(frappe.has_permission("CRM Organization", "delete", doc=self.azienda.name))

	def test_the_screen_offers_no_delete_it_would_refuse(self):
		self.come(OPERATORE)
		permessi = get_doc_permissions("CRM Organization", self.azienda.name)["permissions"]
		self.assertEqual(permessi["delete"], 0)
		self.assertEqual(permessi["write"], 1)

	def test_who_does_not_write_people_does_not_write_companies(self):
		self.come(AMMINISTRAZIONE)
		self.assertTrue(frappe.has_permission("CRM Organization", "read", doc=self.azienda.name))
		self.assertFalse(frappe.has_permission("CRM Organization", "write", doc=self.azienda.name))
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc({"doctype": "CRM Organization", "organization_name": "Nuova Test"}).insert()

	def test_what_the_server_makes_for_itself_goes_through(self):
		# a person's company is created with them, whoever saved the person
		self.come(AMMINISTRAZIONE)
		frappe.get_doc({"doctype": "CRM Organization", "organization_name": "Dal Server Test"}).insert(
			ignore_permissions=True
		)
		self.assertTrue(frappe.db.exists("CRM Organization", "Dal Server Test"))
