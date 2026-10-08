# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The payment reminders' rules without a site: when an invoice is due, when its
next reminder leaves, by which way, what the screens say of it."""

import datetime
import unittest

from crm.invoicing import solleciti_regole as R


def giorno(numero: int, mese: int = 10) -> datetime.date:
	return datetime.date(2026, mese, numero)


class LaScadenza(unittest.TestCase):
	def test_senza_scadenze_e_il_giorno_dell_emissione(self):
		self.assertEqual(R.scadenza(giorno(1)), giorno(1))
		self.assertEqual(R.scadenza(giorno(1), [None]), giorno(1))

	def test_con_le_rate_e_l_ultima(self):
		self.assertEqual(R.scadenza(giorno(1), [giorno(15), None, giorno(31)]), giorno(31))


class QuandoSiSollecita(unittest.TestCase):
	def test_il_primo_dopo_i_giorni_scelti(self):
		self.assertFalse(R.da_sollecitare(giorno(7), giorno(1), [], 50, primo=7))
		self.assertTrue(R.da_sollecitare(giorno(8), giorno(1), [], 50, primo=7))

	def test_il_secondo_dopo_l_intervallo_poi_basta(self):
		self.assertFalse(R.da_sollecitare(giorno(21), giorno(1), [giorno(8)], 50, ogni=14))
		self.assertTrue(R.da_sollecitare(giorno(22), giorno(1), [giorno(8)], 50, ogni=14))
		self.assertFalse(R.da_sollecitare(giorno(30, 12), giorno(1), [giorno(8), giorno(22)], 50, massimo=2))
		self.assertIsNone(R.prossimo(giorno(1), [giorno(8), giorno(22)], 7, 14, 2))
		# a try that reached nobody waits its days, but leaves the most untouched
		self.assertFalse(R.da_sollecitare(giorno(21), giorno(1), [], 50, ogni=14, tentati=[giorno(8)]))
		self.assertTrue(
			R.da_sollecitare(
				giorno(30, 12), giorno(1), [giorno(8)], 50, massimo=2, ogni=14, tentati=[giorno(22)]
			)
		)

	def test_sotto_la_soglia_mai(self):
		self.assertFalse(R.da_sollecitare(giorno(30), giorno(1), [], 9.99, minimo=10))
		self.assertTrue(R.da_sollecitare(giorno(30), giorno(1), [], 10, minimo=10))
		self.assertFalse(R.da_sollecitare(giorno(30), giorno(1), [], 0, minimo=0))


class INumeri(unittest.TestCase):
	def test_niente_e_il_predefinito_e_i_limiti_tengono(self):
		self.assertEqual(R.numeri(None, "", None, None), (7, 14, 2, 10.0))
		self.assertEqual(R.numeri(0, -3, 50, -1), (1, 1, 10, 0.0))
		self.assertEqual(R.numeri("x", 1000, 3, "5"), (7, 365, 3, 5.0))


class LeVie(unittest.TestCase):
	def test_email_e_sms_dove_arrivano(self):
		self.assertEqual(R.canali(True, True, True, True, False), [R.EMAIL, R.SMS])
		self.assertEqual(R.canali(True, False, True, True, False), [R.EMAIL])
		self.assertEqual(R.canali(True, True, False, True, False), [R.SMS])
		self.assertEqual(R.canali(True, True, False, False, False), [])

	def test_mai_un_sms_a_chi_ha_scritto_stop(self):
		self.assertEqual(R.canali(True, True, True, True, True), [R.EMAIL])
		self.assertEqual(R.canali(False, True, True, True, True), [])


class QuantiSolleciti(unittest.TestCase):
	def test_contano_quelli_arrivati(self):
		righe = [
			{"status": R.INVIATO, "occurred_on": "2026-10-08 09:00:00"},
			{"status": R.NON_INVIATO, "occurred_on": "2026-10-30 09:00:00"},
			{"status": R.INVIATO, "occurred_on": datetime.datetime(2026, 10, 22, 9)},
			{"status": R.FALLITO, "occurred_on": "2026-11-05 09:00:00"},
		]
		self.assertEqual(R.quanti(righe), {"count": 2, "last": "2026-10-22"})
		self.assertEqual(R.quanti([]), {"count": 0, "last": None})


if __name__ == "__main__":
	unittest.main()
