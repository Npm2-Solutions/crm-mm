# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The phone at hand: the last calls one may read, who they were with and whether
nobody answered; people to call found by name or by number, only the ones the
session may read."""

import unittest

import frappe
from frappe.tests import IntegrationTestCase

from crm.permissions import utenti
from crm.permissions.test_org_hierarchy import make_user
from crm.telephony import pannello

SEGRETERIA = "pannello.desk@example.com"
MARKETING = "pannello.marketing@example.com"


class LaChiamataPersa(unittest.TestCase):
	def test_una_chiamata_in_arrivo_che_nessuno_ha_preso(self):
		self.assertTrue(pannello.persa({"type": "Incoming", "status": "No Answer"}))
		self.assertTrue(pannello.persa({"type": "Incoming", "status": "Busy"}))
		self.assertTrue(pannello.persa({"type": "Incoming", "status": "Completed", "left_message": 1}))

	def test_una_presa_o_una_fatta_non_lo_e(self):
		self.assertFalse(pannello.persa({"type": "Incoming", "status": "Completed"}))
		self.assertFalse(pannello.persa({"type": "Outgoing", "status": "No Answer"}))


class TestPannello(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		make_user(SEGRETERIA)
		utenti.assegna_livelli(SEGRETERIA, ["segreteria"])
		make_user(MARKETING)
		utenti.assegna_livelli(MARKETING, ["marketing"])

	def setUp(self):
		frappe.set_user("Administrator")
		self.persona = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Pannello",
				"last_name": f"Prova {frappe.generate_hash(length=5)}",
				"mobile_no": "+39 347 555 1234",
			}
		).insert(ignore_permissions=True)
		self.persa = frappe.get_doc(
			{
				"doctype": "CRM Call Log",
				"id": frappe.generate_hash(length=12),
				"type": "Incoming",
				"status": "No Answer",
				"from": "+393475551234",
				"to": "+390212345678",
				"reference_doctype": "CRM Lead",
				"reference_docname": self.persona.name,
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_the_last_calls_with_their_person(self):
		frappe.set_user(SEGRETERIA)
		dati = pannello.get_phone_panel()
		riga = next(c for c in dati["calls"] if c["name"] == self.persa.name)
		self.assertTrue(riga["missed"])
		self.assertEqual(riga["number"], "+393475551234")
		self.assertEqual(riga["person"], self.persona.lead_name)
		self.assertTrue(dati["can_call"])
		self.assertIn("due", dati["callbacks"])

	def test_somebody_found_by_name(self):
		frappe.set_user(SEGRETERIA)
		trovate = pannello.find_people(self.persona.last_name)
		self.assertEqual([r.name for r in trovate], [self.persona.name])

	def test_somebody_found_by_number_however_written(self):
		frappe.set_user(SEGRETERIA)
		for scritto in ("3475551234", "+39 347 5551234", "555 1234"):
			nomi = [r.name for r in pannello.find_people(scritto)]
			self.assertIn(self.persona.name, nomi, scritto)

	def test_too_little_finds_nothing(self):
		frappe.set_user(SEGRETERIA)
		self.assertEqual(pannello.find_people("3"), [])
		self.assertEqual(pannello.find_people(" "), [])

	def test_whoever_does_not_call_finds_nobody(self):
		frappe.set_user(MARKETING)
		with self.assertRaises(frappe.PermissionError):
			pannello.find_people(self.persona.last_name)
		with self.assertRaises(frappe.PermissionError):
			pannello.get_phone_panel()
