# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A visitor whose phone is set in Italian reads the public pages in Italian: the
framework ships Italian switched off, and DottorCloud switches it on."""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.translate import get_all_languages, get_language
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request

from crm import lingue


def _dimentica_le_lingue():
	frappe.client_cache.delete_value("languages")
	frappe.cache.delete_value("languages_with_name")


class LaLinguaDeiVisitatori(IntegrationTestCase):
	def setUp(self):
		self.utente = frappe.session.user
		self.richiesta = getattr(frappe.local, "request", None)
		frappe.db.set_value("Language", "it", "enabled", 0)
		_dimentica_le_lingue()

	def tearDown(self):
		frappe.set_user(self.utente)
		frappe.local.request = self.richiesta
		frappe.db.rollback()
		_dimentica_le_lingue()

	def visitatore(self, lingue_del_telefono: str):
		frappe.set_user("Guest")
		frappe.local.request = Request(
			EnvironBuilder(headers={"Accept-Language": lingue_del_telefono}).get_environ()
		)

	def test_l_italiano_del_framework_si_accende(self):
		self.assertNotIn("it", get_all_languages())
		lingue.accendi_l_italiano()
		self.assertIn("it", get_all_languages())
		self.assertEqual(frappe.db.get_value("Language", "it", "enabled"), 1)

	def test_spento_un_telefono_in_italiano_leggeva_inglese(self):
		# on a site left in the framework's English: one in Italian answers in Italian
		# anyway (`lingue.italia_dove_nessuno_ha_scelto`)
		with patch("frappe.get_system_settings", return_value=None):
			self.visitatore("it-IT,it;q=0.9")
			self.assertEqual(get_language(), "en")

	def test_un_telefono_in_italiano_legge_italiano(self):
		lingue.accendi_l_italiano()
		self.visitatore("it-IT,it;q=0.9")
		self.assertEqual(get_language(), "it")

	def test_un_telefono_in_un_altra_lingua_resta_nella_sua(self):
		lingue.accendi_l_italiano()
		self.visitatore("de-DE,de;q=0.9")
		self.assertEqual(get_language(), "de")
