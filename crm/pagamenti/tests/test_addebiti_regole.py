# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Subscriptions bought from the area and charged on the saved card, without a
site: what is sold, when the card is tried, the card in words, why it failed."""

import datetime
import unittest

from crm.pagamenti import addebiti_regole as R

TIPO = {
	"enabled": 1,
	"sold_online": 1,
	"billable_service": "Abbonamento",
	"price": 120,
	"payment": "Upfront",
	"months": 3,
}


class TestInVendita(unittest.TestCase):
	def test_subito_basta_vendere_dall_area(self):
		self.assertIsNone(R.perche_non_in_vendita(TIPO, True, False))
		self.assertIn("does not sell", R.perche_non_in_vendita(TIPO, False, False))
		self.assertIn("not connected", R.perche_non_in_vendita(TIPO, True, True, collegato=False))

	def test_al_mese_solo_con_la_carta(self):
		mensile = {**TIPO, "payment": "Monthly"}
		self.assertIn("saved card", R.perche_non_in_vendita(mensile, True, False))
		self.assertIsNone(R.perche_non_in_vendita(mensile, True, True))
		# by the month over one month is paid at once
		self.assertIsNone(R.perche_non_in_vendita({**mensile, "months": 1}, True, False))

	def test_il_tipo_deve_potersi_fatturare(self):
		self.assertIn("fiscal card", R.perche_non_in_vendita({**TIPO, "billable_service": None}, True, True))
		self.assertIn("price", R.perche_non_in_vendita({**TIPO, "price": 0}, True, True))
		self.assertIn("not sold online", R.perche_non_in_vendita({**TIPO, "sold_online": 0}, True, True))
		self.assertIn("not sold online", R.perche_non_in_vendita({**TIPO, "enabled": 0}, True, True))


class TestTentativi(unittest.TestCase):
	dovuta = datetime.date(2026, 11, 1)

	def giorno(self, n):
		return self.dovuta + datetime.timedelta(days=n)

	def test_il_giorno_poi_tre_e_sette_giorni_dopo(self):
		self.assertFalse(R.da_tentare(self.giorno(-1), self.dovuta, 0))
		self.assertTrue(R.da_tentare(self.dovuta, self.dovuta, 0))
		# after the first, not before three days
		self.assertFalse(R.da_tentare(self.giorno(2), self.dovuta, 1, self.dovuta))
		self.assertTrue(R.da_tentare(self.giorno(3), self.dovuta, 1, self.dovuta))
		self.assertFalse(R.da_tentare(self.giorno(6), self.dovuta, 2, self.giorno(3)))
		self.assertTrue(R.da_tentare(self.giorno(7), self.dovuta, 2, self.giorno(3)))
		# three, and no more
		self.assertFalse(R.da_tentare(self.giorno(30), self.dovuta, 3, self.giorno(7)))
		self.assertTrue(R.esauriti(3))
		self.assertFalse(R.esauriti(2))

	def test_mai_due_volte_lo_stesso_giorno(self):
		self.assertFalse(R.da_tentare(self.dovuta, self.dovuta, 0, self.dovuta))
		# a round missed: the next one tries
		self.assertTrue(R.da_tentare(self.giorno(5), self.dovuta, 1, self.dovuta))

	def test_quando_di_nuovo(self):
		self.assertEqual(R.prossimo(self.dovuta, 0), self.dovuta)
		self.assertEqual(R.prossimo(self.dovuta, 1), self.giorno(3))
		self.assertEqual(R.prossimo(self.dovuta, 2), self.giorno(7))
		self.assertIsNone(R.prossimo(self.dovuta, 3))

	def test_una_chiave_per_tentativo(self):
		self.assertEqual(R.chiave("s", "ABB-1", "r1", 1), "s:ABB-1:r1:1")
		self.assertNotEqual(R.chiave("s", "ABB-1", "r1", 1), R.chiave("s", "ABB-1", "r1", 2))


class TestCarta(unittest.TestCase):
	def test_come_la_descrive_stripe(self):
		self.assertEqual(
			R.carta({"brand": "visa", "last4": "4242", "exp_month": 3, "exp_year": 2030, "fingerprint": "x"}),
			{"brand": "Visa", "last4": "4242", "expiry": "03/2030"},
		)
		self.assertEqual(R.carta({"brand": "cartes_bancaires", "last4": "0001"})["brand"], "Cartes Bancaires")
		self.assertIsNone(R.carta({}))
		self.assertIsNone(R.carta(None))

	def test_scaduta(self):
		self.assertFalse(R.scaduta("03/2030", datetime.date(2030, 3, 31)))
		self.assertTrue(R.scaduta("03/2030", datetime.date(2030, 4, 1)))
		self.assertFalse(R.scaduta("", datetime.date(2030, 4, 1)))

	def test_perche_non_e_passato(self):
		self.assertEqual(R.motivo("insufficient_funds"), "There is not enough money on the card.")
		self.assertEqual(
			R.motivo("authentication_required"), "The bank asks the person to confirm the payment."
		)
		self.assertEqual(R.motivo("qualcosa"), "The card could not be charged.")
		self.assertEqual(R.motivo(None), "The card could not be charged.")


if __name__ == "__main__":
	unittest.main()
