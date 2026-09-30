# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""What the assistant may do, and how its words are kept: the rules, without a site."""

from __future__ import annotations

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the rules are still testable
	from unittest import TestCase as UnitTestCase

from crm.assistente import regole as r


class IlJson(UnitTestCase):
	def test_nudo_in_un_recinto_o_in_una_frase(self):
		self.assertEqual(r.estrai_json('{"a": 1}'), {"a": 1})
		self.assertEqual(r.estrai_json('Ecco:\n```json\n{"a": [1, 2]}\n```\nFatto.'), {"a": [1, 2]})
		self.assertEqual(
			r.estrai_json('Lo schema è {"a": "x}y", "b": {"c": 2}} come chiesto'), {"a": "x}y", "b": {"c": 2}}
		)

	def test_niente_da_leggere_niente_da_indovinare(self):
		for testo in (None, "", "no", "[1, 2]", "{rotto", '{"a": }'):
			self.assertIsNone(r.estrai_json(testo), testo)


class LaDifferenza(UnitTestCase):
	def test_riga_per_riga(self):
		diff = r.differenza(
			"Gentile collega,\nla paziente sta bene.", "Gentile collega,\nla paziente sta meglio."
		)
		self.assertIn("-la paziente sta bene.", diff)
		self.assertIn("+la paziente sta meglio.", diff)
		self.assertEqual(r.differenza("uguale", "uguale"), "")

	def test_quanto_e_cambiata(self):
		self.assertEqual(r.quanto_cambiata("abc", "abc"), 0.0)
		self.assertEqual(r.quanto_cambiata("abc", "xyz"), 1.0)
		self.assertEqual(r.quanto_cambiata("", ""), 0.0)


class IlResto(UnitTestCase):
	def test_l_impronta(self):
		self.assertEqual(r.impronta("a"), r.impronta(b"a"))
		self.assertEqual(len(r.impronta(None)), 64)

	def test_un_testo_lungo_si_taglia_e_lo_dice(self):
		self.assertEqual(r.taglia("breve", 10), "breve")
		self.assertEqual(r.taglia("x" * 20, 10), "x" * 10 + "\n[…]")

	def test_pronto_solo_con_tutto(self):
		self.assertEqual(r.pronto(1, r.ANTHROPIC, "https://api.anthropic.com", "claude", 1), [])
		self.assertEqual(r.pronto(1, r.COMPATIBILE_OPENAI, "http://localhost:8080/v1", "llama", 1), [])
		mancano = r.pronto(0, "Altro", "http://example.com", "", 0)
		self.assertEqual(len(mancano), 5)
		self.assertIn("The contract says the provider keeps nothing and trains on nothing", mancano)
