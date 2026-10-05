# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt
"""The clinic's words read in Italian. They are pairs of English strings
(`crm.clinica.parole`): the base's sentence and the clinic's, translated when the
boot or `parola()` reads it. The catalog's extraction sees neither: without its
entry in `it.po` the clinic's sentence came out in English, and a base sentence
that left the code kept a pair nobody reads."""

import unittest

from crm.clinica.parole import PAROLE
from crm.tests.test_frasi_costanti import _msgid


class LeParoleDellaClinica(unittest.TestCase):
	def test_ogni_parola_della_clinica_ha_il_suo_italiano(self):
		catalogo = _msgid()
		mancano = sorted(sua for sua in PAROLE.values() if sua not in catalogo)
		self.assertEqual(mancano, [])

	def test_ogni_parola_della_base_esiste(self):
		# the base's sentence is one the screens say: a pair over a sentence that
		# changed would never be read
		catalogo = _msgid()
		mancano = sorted(base for base in PAROLE if base not in catalogo)
		self.assertEqual(mancano, [])
