# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""The core documents the Manager's pages write (doc 30, PR 3b).

Email templates, assignment rules and imports are documents of Frappe, which gives
them to System Manager only: the Manager's pages showed them and the server said
no. A role now carries the rule and the capability narrows it. Email accounts go
through the CRM's own calls, never with servers and ports of their own. Conditions
written in Python stay the agency's: for anybody else the server writes them from
the guided conditions.
"""

import json

import frappe
from frappe.tests import IntegrationTestCase

from crm.permissions import documenti, livelli, utenti

MANAGER = "core.manager@example.com"
FRONT_DESK = "core.desk@example.com"
AGENCY = "core.agency@example.com"

#: What a Manager's browser could send along with a guided condition.
PYTHON = "__import__('os').system('true') or True"


def make_user(email: str, *roles: str):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"send_welcome_email": 0,
				"roles": [{"role": role} for role in roles],
			}
		).insert(ignore_permissions=True)


def regola(nome: str, **valori):
	return frappe.get_doc(
		{
			"doctype": "Assignment Rule",
			"name": nome,
			"assignment_rule_name": nome,
			"document_type": "CRM Lead",
			"description": "Test",
			"rule": "Round Robin",
			"priority": 1,
			"users": [{"user": MANAGER}],
			"assignment_days": [{"day": "Monday"}],
			**valori,
		}
	)


class CoreTestCase(IntegrationTestCase):
	def setUp(self):
		documenti.concedi_documenti_del_core()
		make_user(MANAGER, "Sales User")
		make_user(FRONT_DESK, "Sales User")
		make_user(AGENCY, "System Manager")
		utenti.assegna_livelli(MANAGER, ["manager"])
		utenti.assegna_livelli(FRONT_DESK, ["segreteria"])
		livelli.dimentica_cache()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		livelli.dimentica_cache()


class TestTheRulesAreGiven(CoreTestCase):
	def test_each_core_document_has_its_role(self):
		for doctype, ruolo in documenti.DEL_CORE.items():
			for ptype in ("read", "write", "create", "delete"):
				self.assertTrue(
					frappe.db.exists(
						"Custom DocPerm", {"parent": doctype, "role": ruolo, "permlevel": 0, ptype: 1}
					),
					f"{doctype} {ruolo} {ptype}",
				)

	def test_giving_them_twice_changes_nothing(self):
		prima = frappe.db.count("Custom DocPerm", {"parent": ("in", list(documenti.DEL_CORE))})
		documenti.concedi_documenti_del_core()
		self.assertEqual(
			frappe.db.count("Custom DocPerm", {"parent": ("in", list(documenti.DEL_CORE))}), prima
		)

	def test_system_manager_keeps_its_rules(self):
		for doctype in documenti.DEL_CORE:
			self.assertTrue(
				frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": "System Manager", "write": 1}),
				doctype,
			)


class TestEmailTemplates(CoreTestCase):
	def template(self, nome: str):
		return frappe.get_doc(
			{
				"doctype": "Email Template",
				"name": nome,
				"subject": "Hello",
				"response": "Hello {{ first_name }}",
				"reference_doctype": "CRM Lead",
			}
		)

	def test_the_manager_writes_them(self):
		frappe.set_user(MANAGER)
		doc = self.template("Core test welcome").insert()
		doc.subject = "Welcome"
		doc.save()
		doc.delete()

	def test_the_front_desk_uses_them_and_does_not_write_them(self):
		frappe.set_user(FRONT_DESK)
		self.assertTrue(frappe.has_permission("Email Template", "read"))
		with self.assertRaises(frappe.PermissionError):
			self.template("Core test desk").insert()


class TestAssignmentRules(CoreTestCase):
	def test_the_server_writes_the_managers_conditions(self):
		guidata = [["status", "==", "New"], "and", ["source", "in", "Web, Ads"]]
		frappe.set_user(MANAGER)
		doc = regola(
			"Core test guided",
			assign_condition=PYTHON,
			assign_condition_json=json.dumps(guidata),
		).insert()
		self.assertEqual(doc.assign_condition, 'status == "New" and (source and source in ["Web", "Ads"])')
		self.assertEqual(
			frappe.db.get_value("Assignment Rule", doc.name, "assign_condition"), doc.assign_condition
		)

	def test_python_with_nothing_guided_is_the_agencys(self):
		frappe.set_user(MANAGER)
		with self.assertRaises(frappe.PermissionError):
			regola("Core test python", assign_condition=PYTHON).insert()
		with self.assertRaises(frappe.PermissionError):
			regola(
				"Core test close",
				assign_condition_json=json.dumps([["status", "==", "New"]]),
				close_condition=PYTHON,
			).insert()

	def test_a_condition_the_screen_cannot_build_is_refused(self):
		frappe.set_user(MANAGER)
		for guidata in (
			[["status", "==", "New"], "or __import__('os')", ["status", "==", "Lost"]],
			[["password", "==", "x"]],
			[["status", "== 1 or", "x"]],
		):
			with self.assertRaises(frappe.ValidationError, msg=repr(guidata)):
				regola("Core test bad", assign_condition_json=json.dumps(guidata)).insert()

	def test_rules_are_for_people_and_deals(self):
		frappe.set_user(MANAGER)
		with self.assertRaises(frappe.PermissionError):
			regola(
				"Core test users",
				document_type="Note",
				assign_condition_json=json.dumps([["title", "==", "x"]]),
			).insert()

	def test_the_agency_writes_python(self):
		frappe.set_user(AGENCY)
		doc = regola("Core test agency", assign_condition="status == 'New'").insert()
		self.assertEqual(doc.assign_condition, "status == 'New'")

	def test_the_manager_switches_off_an_agency_rule(self):
		frappe.set_user(AGENCY)
		doc = regola("Core test switch", assign_condition="status == 'New'").insert()
		frappe.set_user(MANAGER)
		doc = frappe.get_doc("Assignment Rule", doc.name)
		doc.disabled = 1
		doc.save()
		self.assertEqual(doc.assign_condition, "status == 'New'")

	def test_the_front_desk_does_not_see_them(self):
		frappe.set_user(FRONT_DESK)
		self.assertFalse(frappe.has_permission("Assignment Rule", "read"))


class TestSLAConditions(CoreTestCase):
	def test_the_server_writes_the_managers_sla_condition(self):
		from crm.fcrm.doctype.crm_service_level_agreement.test_crm_service_level_agreement import (
			create_test_sla,
		)

		frappe.set_user(MANAGER)
		doc = create_test_sla(
			sla_name="Core test SLA",
			condition=PYTHON,
			condition_json=json.dumps([["status", "==", "New"]]),
		)
		self.assertEqual(doc.condition, 'doc.status == "New"')


class TestDataImport(CoreTestCase):
	def test_the_manager_imports_people(self):
		frappe.set_user(MANAGER)
		doc = frappe.get_doc(
			{"doctype": "Data Import", "reference_doctype": "CRM Lead", "import_type": "Insert New Records"}
		).insert()
		self.assertTrue(frappe.db.exists("Data Import", doc.name))

	def test_the_manager_imports_a_file(self):
		"""The whole way: the file, the import, the people. It worked for Administrator only."""
		email = "importata.core@studio.test"
		frappe.set_user(MANAGER)
		file = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "core-import.csv",
				"content": f"First Name,Last Name,Email\nImportata,Dal Manager,{email}\n",
				"is_private": 1,
			}
		).save(ignore_permissions=True)
		importazione = frappe.get_doc(
			{
				"doctype": "Data Import",
				"reference_doctype": "CRM Lead",
				"import_type": "Insert New Records",
				"import_file": file.file_url,
			}
		).insert()

		from frappe.core.doctype.data_import.data_import import form_start_import

		try:
			form_start_import(importazione.name)
			frappe.set_user("Administrator")
			self.assertTrue(
				frappe.db.exists("CRM Lead", {"email": email}),
				frappe.db.get_value("Data Import", importazione.name, "status"),
			)
		finally:
			# the importer commits as it goes: nothing rolls this back
			frappe.set_user("Administrator")
			for nome in frappe.get_all("CRM Lead", {"email": email}, pluck="name"):
				frappe.delete_doc("CRM Lead", nome, force=True, ignore_permissions=True)
			frappe.db.delete("Data Import Log", {"data_import": importazione.name})
			frappe.delete_doc("Data Import", importazione.name, force=True, ignore_permissions=True)
			frappe.delete_doc("File", file.name, force=True, ignore_permissions=True)
			frappe.db.commit()  # nosemgrep: frappe-manual-commit — undoing what the importer committed

	def test_the_front_desk_does_not(self):
		frappe.set_user(FRONT_DESK)
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc(
				{
					"doctype": "Data Import",
					"reference_doctype": "CRM Lead",
					"import_type": "Insert New Records",
				}
			).insert()

	def test_only_the_crms_documents(self):
		frappe.set_user(MANAGER)
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc(
				{"doctype": "Data Import", "reference_doctype": "User", "import_type": "Insert New Records"}
			).insert()


class TestEmailAccounts(CoreTestCase):
	def account(self, nome: str, service: str = "GMail"):
		return frappe.get_doc(
			{
				"doctype": "Email Account",
				"email_account_name": nome,
				"email_id": f"{nome.lower().replace(' ', '.')}@studio.test",
				"service": service,
				"enable_incoming": 0,
				"enable_outgoing": 0,
			}
		).insert(ignore_permissions=True)

	def test_the_manager_lists_them_without_secrets(self):
		self.account("Core Desk")
		from crm.api import settings

		frappe.set_user(MANAGER)
		accounts = {a.name: a for a in settings.get_email_accounts()}
		self.assertIn("Core Desk", accounts)
		self.assertNotIn("password", accounts["Core Desk"])

	def test_the_front_desk_picks_one_and_no_more(self):
		self.account("Core Picks")
		from crm.api import settings

		frappe.set_user(FRONT_DESK)
		with self.assertRaises(frappe.PermissionError):
			settings.get_email_accounts()
		scelte = settings.list_email_accounts()
		self.assertIn("Core Picks", [a.name for a in scelte])
		self.assertEqual(set(scelte[0]), {"name", "email_id"})

	def test_the_manager_changes_and_renames_one(self):
		self.account("Core Old")
		from crm.api import settings

		frappe.set_user(MANAGER)
		nome = settings.update_email_account(
			"Core Old",
			{"email_account_name": "Core New", "create_lead_from_incoming_email": 1, "password": "*****"},
		)
		self.assertEqual(nome, "Core New")
		self.assertEqual(
			frappe.db.get_value("Email Account", "Core New", "create_lead_from_incoming_email"), 1
		)

	def test_servers_of_its_own_are_the_agencys(self):
		self.account("Core Custom", service="")
		from crm.api import settings

		frappe.set_user(MANAGER)
		with self.assertRaises(frappe.PermissionError):
			settings.update_email_account("Core Custom", {"enable_outgoing": 1})
