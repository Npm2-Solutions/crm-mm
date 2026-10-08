# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Whom a missed call's SMS may reach, without a site."""

import datetime
import unittest

from crm.telephony import persa_regole as R


class AChiScrivere(unittest.TestCase):
	def test_un_cellulare_italiano_come_lo_vuole_twilio(self):
		self.assertEqual(R.a_chi_scrivere("333 123 4567", ["IT"]), "+393331234567")
		self.assertEqual(R.a_chi_scrivere("0039 333 1234567", "IT"), "+393331234567")

	def test_un_fisso_non_legge_sms(self):
		self.assertIsNone(R.a_chi_scrivere("+390212345678", ["IT"]))

	def test_mai_a_pagamento_ne_fuori_dai_paesi(self):
		self.assertIsNone(R.a_chi_scrivere("+39 899 123456", ["IT"]))
		self.assertIsNone(R.a_chi_scrivere("+33612345678", ["IT"]))
		self.assertEqual(R.a_chi_scrivere("+33612345678", ["IT", "FR"]), "+33612345678")

	def test_un_numero_illeggibile_o_nascosto(self):
		self.assertIsNone(R.a_chi_scrivere("", ["IT"]))
		self.assertIsNone(R.a_chi_scrivere("anonymous", ["IT"]))

	def test_una_volta_al_giorno(self):
		oggi, domani = datetime.date(2026, 10, 8), datetime.date(2026, 10, 9)
		self.assertNotEqual(R.chiave_del_giorno("+39333", oggi), R.chiave_del_giorno("+39333", domani))


class Conta(unittest.TestCase):
	def test_nessuno_risponde_conta_da_subito(self):
		self.assertTrue(R.conta(R.NESSUNO_RISPONDE, {}))
		self.assertFalse(R.conta(R.NESSUNO_RISPONDE, {"missed_when_nobody_answers": 0}))

	def test_gli_altri_casi_solo_se_il_centro_li_accende(self):
		for caso in (R.NESSUNO_DA_FAR_SQUILLARE, R.SEGRETERIA):
			self.assertFalse(R.conta(caso, {}))
		self.assertTrue(R.conta(R.NESSUNO_DA_FAR_SQUILLARE, {"missed_when_nobody_to_ring": 1}))
		self.assertTrue(R.conta(R.SEGRETERIA, {"missed_when_service_answers": 1}))


if __name__ == "__main__":
	unittest.main()
