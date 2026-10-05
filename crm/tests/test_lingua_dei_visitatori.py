# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A visitor reads the public pages in Italian or in English, the two languages
DottorCloud speaks: the framework ships Italian switched off and sixteen others
on, in which DottorCloud has no words, and DottorCloud turns Italian on and the
others off (`lingue.solo_italiano_e_inglese`)."""

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
		# as the framework ships them: Italian off, German on
		frappe.db.set_value("Language", "it", "enabled", 0)
		frappe.db.set_value("Language", "de", "enabled", 1)
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

	def test_solo_italiano_e_inglese_accesi(self):
		self.assertNotIn("it", get_all_languages())
		self.assertIn("de", get_all_languages())
		lingue.solo_italiano_e_inglese()
		self.assertEqual(sorted(get_all_languages()), ["en", "it"])
		self.assertEqual(frappe.db.get_value("Language", "it", "enabled"), 1)
		self.assertEqual(frappe.db.get_value("Language", "de", "enabled"), 0)

	def test_spento_un_telefono_in_italiano_leggeva_inglese(self):
		# on a site left in the framework's English: one in Italian answers in Italian
		# anyway (`lingue.italia_dove_nessuno_ha_scelto`)
		with patch("frappe.get_system_settings", return_value=None):
			self.visitatore("it-IT,it;q=0.9")
			self.assertEqual(get_language(), "en")

	def test_un_telefono_in_italiano_legge_italiano(self):
		lingue.solo_italiano_e_inglese()
		self.visitatore("it-IT,it;q=0.9")
		self.assertEqual(get_language(), "it")

	def test_un_telefono_in_tedesco_legge_la_lingua_del_centro(self):
		# DottorCloud has no German words: the framework's German around its
		# English was what such a phone read
		lingue.solo_italiano_e_inglese()
		with patch("frappe.get_system_settings", return_value="it"):
			self.visitatore("de-DE,de;q=0.9")
			self.assertEqual(get_language(), "it")

	def test_un_telefono_che_legge_anche_l_inglese_legge_inglese(self):
		lingue.solo_italiano_e_inglese()
		self.visitatore("de-DE,de;q=0.9,en;q=0.8")
		self.assertEqual(get_language(), "en")
