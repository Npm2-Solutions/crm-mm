# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's first opening (crm.benvenuto): its language, then its name and
clock, by whoever sets it up; the framework's setup wizard marked done."""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm import benvenuto, lingue


def _utente(email: str, *ruoli: str, **campi) -> str:
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"send_welcome_email": 0,
				"roles": [{"role": ruolo} for ruolo in ruoli],
			}
		).insert(ignore_permissions=True)
	if campi:
		frappe.db.set_value("User", email, campi, update_modified=False)
	return email


class IlBenvenuto(IntegrationTestCase):
	def setUp(self):
		self.lingua = frappe.local.lang
		self.responsabile = _utente("benvenuto.responsabile@example.com", "Sales Manager", "Sales User")
		self.accoglienza = _utente("benvenuto.accoglienza@example.com", "Sales User")
		frappe.defaults.clear_default(benvenuto.FATTO)
		frappe.db.set_single_value("FCRM Settings", "brand_name", "")
		frappe.db.set_single_value("Website Settings", "app_name", "")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		frappe.local.lang = self.lingua
		# `is_setup_complete` is kept for the request, which a test run is
		frappe.local.request_cache.clear()
		frappe.clear_cache()

	def test_lo_vede_chi_imposta_il_centro(self):
		self.assertTrue(benvenuto.da_fare())
		frappe.set_user(self.responsabile)
		self.assertTrue(benvenuto.per_il_boot())
		self.assertIn("centre_name", benvenuto.get_welcome())
		frappe.set_user(self.accoglienza)
		self.assertFalse(benvenuto.per_il_boot())
		with self.assertRaises(frappe.PermissionError):
			benvenuto.get_welcome()
		with self.assertRaises(frappe.PermissionError):
			benvenuto.finish("Studio Rossi")

	def test_chi_sceglie_la_lingua_la_legge_subito(self):
		frappe.db.set_value("User", self.responsabile, "language", "it", update_modified=False)
		frappe.set_user(self.responsabile)
		with patch("frappe.enqueue"):
			stato = benvenuto.choose_language("en")
		self.assertEqual(stato["language"], "en")
		self.assertEqual(lingue.del_centro(), "en")
		self.assertFalse(frappe.db.get_value("User", self.responsabile, "language"))

	def test_il_nome_del_centro_e_suo(self):
		frappe.set_user(self.responsabile)
		for nome in ("", "  ", "DottorCloud"):
			with self.assertRaises(frappe.ValidationError, msg=nome):
				benvenuto.finish(nome)
		self.assertTrue(benvenuto.da_fare())

	def test_finito_una_volta(self):
		frappe.db.set_value("Installed Application", {"app_name": "frappe"}, "is_setup_complete", 0)
		frappe.local.request_cache.clear()
		self.assertFalse(frappe.is_setup_complete())
		frappe.set_user(self.responsabile)
		with patch("frappe.enqueue"), patch("crm.demo.api.create_demo_data") as demo:
			self.assertEqual(benvenuto.finish(" Studio Rossi ", "Europe/Rome"), {"done": True})
		demo.assert_not_called()
		self.assertEqual(frappe.db.get_single_value("FCRM Settings", "brand_name"), "Studio Rossi")
		self.assertEqual(frappe.db.get_single_value("System Settings", "time_zone"), "Europe/Rome")
		self.assertFalse(benvenuto.da_fare())
		self.assertFalse(benvenuto.per_il_boot())
		# the framework's wizard will not show in the Desk, nor load the demo after it
		self.assertTrue(frappe.is_setup_complete())
		self.assertEqual(frappe.db.get_single_value("System Settings", "setup_complete"), 1)
		# the name taken away later does not bring it back
		frappe.db.set_single_value("FCRM Settings", "brand_name", "")
		self.assertFalse(benvenuto.da_fare())

	def test_i_dati_di_prova_se_li_chiede(self):
		frappe.set_user("Administrator")
		with patch("frappe.enqueue"), patch("crm.demo.api.create_demo_data") as demo:
			benvenuto.finish("Studio Rossi", demo=1)
		demo.assert_called_once()
