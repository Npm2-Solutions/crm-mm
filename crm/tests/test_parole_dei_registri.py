# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The registries' words a screen shows, translated where they are drawn
(`_(uso.descrizione)` for the forms builder, `__(capability.description)` in a
user's access): the catalogue's extraction reads only literals, so their Italian
is written by hand. A word missing there reads in English ("Filled in by the
person: a privacy notice…" under the use of a new form)."""

import unittest

from crm.tests.test_frasi_costanti import _msgid


class LeParoleDeiRegistri(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		from crm.registrazione import carica

		carica()
		cls.catalogo = _msgid()

	def test_gli_usi_di_un_modulo(self):
		from crm.moduli import modelli

		mancano = [
			parola
			for uso in modelli.usi()
			for parola in (uso.etichetta, uso.descrizione)
			if parola and parola not in self.catalogo
		]
		self.assertEqual(mancano, [])

	def test_i_livelli(self):
		from crm.permissions import livelli

		mancano = [
			parola
			for livello in livelli.livelli()
			for parola in (livello.etichetta, livello.descrizione)
			if parola and parola not in self.catalogo
		]
		self.assertEqual(mancano, [])

	def test_le_capacita_a_scelta_si_dicono_in_parole(self):
		# a capability one may also allow is a box to tick in a user's access:
		# without a sentence the box showed its technical name
		from crm.permissions import livelli

		registrate = livelli.capacita_registrate()
		nomi = livelli.a_scelta_dei_livelli([livello.chiave for livello in livelli.livelli()])
		self.assertTrue(nomi)
		senza = [nome for nome in nomi if not registrate[nome].descrizione]
		self.assertEqual(senza, [])
		mancano = [
			registrate[nome].descrizione for nome in nomi if registrate[nome].descrizione not in self.catalogo
		]
		self.assertEqual(mancano, [])
