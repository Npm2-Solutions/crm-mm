# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The SMS of the centre without a site: the sender's name (doc 52, fourth part)."""

import unittest

from crm.telephony import sms_regole as R


class IlNome(unittest.TestCase):
	def test_un_nome_che_twilio_prende(self):
		self.assertEqual(R.problema_del_nome("Aurora"), "")
		self.assertEqual(R.problema_del_nome("Centro 2000"), "")
		self.assertEqual(R.problema_del_nome("ABCDEFGHIJK"), "")

	def test_un_nome_che_no(self):
		self.assertIn("Write", R.problema_del_nome("  "))
		self.assertIn("11", R.problema_del_nome("Centro Aurora Milano"))
		self.assertIn("letters", R.problema_del_nome("Città"))
		self.assertIn("letters", R.problema_del_nome("A&B"))
		self.assertIn("digits", R.problema_del_nome("12345"))

	def test_dal_nome_del_centro(self):
		self.assertEqual(R.nome_dal_centro("Studio Più"), "Studio Piu")
		# too long: what says which centre it is, never a word cut in half
		self.assertEqual(R.nome_dal_centro("Centro Aurora"), "Aurora")
		self.assertEqual(R.nome_dal_centro("Centro Medico Aurora"), "Aurora")
		self.assertEqual(R.nome_dal_centro("Poliambulatorio San Marco Srl"), "San Marco")
		self.assertEqual(R.nome_dal_centro("Fisio Lab Milano"), "Fisio Lab")
		self.assertEqual(R.nome_dal_centro("Centro Medico"), "Centro")
		self.assertEqual(R.nome_dal_centro("Poliambulatorio Città"), "Citta")
		self.assertEqual(R.nome_dal_centro("Studio d'Amico & C."), "dAmico")
		self.assertEqual(R.nome_dal_centro("Fisioterapiamilanese"), "Fisioterapi")
		self.assertEqual(R.nome_dal_centro("Più"), "Piu")
		self.assertEqual(R.nome_dal_centro("123"), "")
		self.assertEqual(R.nome_dal_centro(""), "")
