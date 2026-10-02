# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The SMS of the centre without a site: the sender's name, the words that stop
and start again, the hours of a promotional SMS (doc 52, fourth part)."""

import unittest
from datetime import datetime

from crm.telephony import sms_regole as R

# 2 October 2026 is a Friday
VENERDI = datetime(2026, 10, 2)


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


class LeParole(unittest.TestCase):
	def test_stop_come_lo_scrive_la_gente(self):
		for testo in ("STOP", "stop", " Stop! ", "stop all", "Basta.", "ARRESTA", "unsubscribe"):
			self.assertEqual(R.parola_chiave(testo), "stop", testo)

	def test_di_nuovo(self):
		for testo in ("START", "inizia", "Iscrivimi"):
			self.assertEqual(R.parola_chiave(testo), "start", testo)

	def test_un_messaggio_non_e_una_parola(self):
		for testo in ("Basta così, grazie", "stop alle 18?", "", None, "Posso spostare l'appuntamento?"):
			self.assertEqual(R.parola_chiave(testo), "", testo)


class LeOre(unittest.TestCase):
	def test_da_lunedi_a_sabato_dalle_8_alle_22(self):
		self.assertTrue(R.ora_consentita(VENERDI.replace(hour=8)))
		self.assertTrue(R.ora_consentita(VENERDI.replace(hour=21, minute=59)))
		self.assertFalse(R.ora_consentita(VENERDI.replace(hour=22)))
		self.assertFalse(R.ora_consentita(VENERDI.replace(hour=7, minute=59)))
		self.assertFalse(R.ora_consentita(datetime(2026, 10, 4, 12)))  # Sunday

	def test_il_momento_dopo(self):
		# Friday night: Saturday at 8
		self.assertEqual(R.prossimo_momento(VENERDI.replace(hour=23)), datetime(2026, 10, 3, 8))
		# Friday early: the same morning at 8
		self.assertEqual(R.prossimo_momento(VENERDI.replace(hour=6)), datetime(2026, 10, 2, 8))
		# Saturday night and Sunday: Monday at 8
		self.assertEqual(R.prossimo_momento(datetime(2026, 10, 3, 22, 30)), datetime(2026, 10, 5, 8))
		self.assertEqual(R.prossimo_momento(datetime(2026, 10, 4, 15)), datetime(2026, 10, 5, 8))
		# open already: now
		adesso = VENERDI.replace(hour=10, minute=15)
		self.assertEqual(R.prossimo_momento(adesso), adesso)
