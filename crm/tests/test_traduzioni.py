# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The page's words: not inside every page, but a script the browser keeps until
they change (crm.www.crm.traduzioni)."""

import json

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.translate import clear_cache

from crm.www.crm import (
	get_boot,
	get_translated_messages,
	impronta_delle_traduzioni,
	traduzioni,
)

PREFISSO = "window.translated_messages="


class TestTraduzioni(FrappeTestCase):
	def setUp(self):
		# the modules (the vertical whose words lay over the base's) register at a
		# request; a test has none
		from crm.registrazione import carica

		carica()
		frappe.set_user("Administrator")
		self.lingua_di_prima = frappe.local.lang
		frappe.local.lang = "it"

	def tearDown(self):
		frappe.local.lang = self.lingua_di_prima
		frappe.set_user("Administrator")

	def parole(self, risposta):
		testo = risposta.get_data(as_text=True)
		self.assertTrue(testo.startswith(PREFISSO))
		self.assertTrue(testo.endswith(";"))
		return json.loads(testo[len(PREFISSO) : -1])

	def test_the_page_names_the_words_instead_of_carrying_them(self):
		boot = get_boot()
		self.assertNotIn("translated_messages", boot)
		self.assertIn("/api/method/crm.www.crm.traduzioni?", boot.traduzioni)
		self.assertIn("lang=it", boot.traduzioni)
		self.assertIn(f"v={impronta_delle_traduzioni()}", boot.traduzioni)

	def test_the_script_holds_the_words_of_the_page(self):
		risposta = traduzioni(lang="it", v=impronta_delle_traduzioni())
		self.assertEqual(risposta.mimetype, "application/javascript")
		self.assertEqual(self.parole(risposta), get_translated_messages())

	def test_kept_for_good_only_at_the_address_of_todays_words(self):
		oggi = traduzioni(lang="it", v=impronta_delle_traduzioni())
		self.assertIn("immutable", oggi.headers.get("Cache-Control", ""))
		# an address from a page of before: the words of now, never kept under it
		vecchia = traduzioni(lang="it", v="0000000000000000")
		self.assertNotIn("immutable", vecchia.headers.get("Cache-Control", ""))
		self.assertEqual(self.parole(vecchia), get_translated_messages())
		# another language than the session's: not kept either
		altra = traduzioni(lang="de", v=impronta_delle_traduzioni())
		self.assertNotIn("immutable", altra.headers.get("Cache-Control", ""))

	def test_a_new_word_gives_a_new_address(self):
		# from words merged afresh, as at the end: the first merge of a test process
		# can leave out the countries and the site's own translations, which the
		# framework merges inside a suppress(Exception)
		clear_cache()
		prima = impronta_delle_traduzioni()
		traduzione = frappe.get_doc(
			{
				"doctype": "Translation",
				"language": "it",
				"source_text": "A word only this test translates",
				"translated_text": "Una parola che traduce solo questo test",
			}
		).insert(ignore_permissions=True)
		try:
			clear_cache()
			self.assertNotEqual(impronta_delle_traduzioni(), prima)
			self.assertEqual(
				get_translated_messages().get("A word only this test translates"),
				"Una parola che traduce solo questo test",
			)
		finally:
			traduzione.delete(ignore_permissions=True)
			clear_cache()
		self.assertEqual(impronta_delle_traduzioni(), prima)
