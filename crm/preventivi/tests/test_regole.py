# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A quote without a site: how it goes, its sums, which row an appointment takes,
and what is checked before it is proposed."""

import unittest

from crm.preventivi import regole as R


def voce(servizio="Pulizia", fase=1, stato=R.DA_FARE, qty=1, rate=100, sconto=0, **altro):
	return {
		"service": servizio,
		"phase": fase,
		"status": stato,
		"qty": qty,
		"rate": rate,
		"discount": sconto,
		**altro,
	}


class ComeVa(unittest.TestCase):
	def test_i_passaggi(self):
		self.assertTrue(R.si_passa(R.BOZZA, R.PROPOSTO))
		self.assertTrue(R.si_passa(R.PROPOSTO, R.BOZZA))
		self.assertTrue(R.si_passa(R.PROPOSTO, R.ACCETTATO))
		self.assertFalse(R.si_passa(R.BOZZA, R.ACCETTATO))
		self.assertFalse(R.si_passa(R.RIFIUTATO, R.ACCETTATO))
		self.assertTrue(R.si_passa(R.ACCETTATO, R.CHIUSO))

	def test_completato(self):
		self.assertFalse(R.completato([voce(stato=R.FATTA), voce()]))
		self.assertTrue(R.completato([voce(stato=R.FATTA), voce(stato=R.ANNULLATA)]))
		self.assertFalse(R.completato([voce(stato=R.ANNULLATA)]))


class LeSomme(unittest.TestCase):
	def test_quantita_prezzo_e_sconto(self):
		self.assertEqual(R.importo(2, 80, 10), 144)
		self.assertEqual(R.importo(1, 99.99, 33), 66.99)
		self.assertEqual(R.importo(1, 100, 150), 0)

	def test_una_riga_annullata_non_conta(self):
		voci = [
			voce(rate=100, sconto=10, stato=R.FATTA),
			voce("Laser", 2, qty=6, rate=200),
			voce("Massaggio", 1, rate=70, stato=R.ANNULLATA),
		]
		self.assertEqual(
			R.totali(voci), {"gross": 1300, "discount": 10, "net": 1290, "done": 90, "left": 1200}
		)


class LAppuntamento(unittest.TestCase):
	def test_prende_la_prima_da_fare_nell_ordine_delle_fasi(self):
		voci = [
			voce("Laser", 3),
			voce("Pulizia", 2),
			voce("Pulizia", 1, stato=R.FATTA),
			voce("Pulizia", 1),
		]
		self.assertEqual([fase for fase, _posizioni in R.fasi(voci)], [1, 2, 3])
		self.assertEqual(R.voce_per(voci, "Pulizia"), 3)
		voci[3]["status"] = R.PRENOTATA
		self.assertEqual(R.voce_per(voci, "Pulizia"), 1)
		self.assertIsNone(R.voce_per(voci, "Massaggio"))


class PrimaDiProporlo(unittest.TestCase):
	def test_cosa_non_va(self):
		self.assertEqual([p.testo() for p in R.valida([])], ["A quote has at least one service"])
		troppe = [voce()] * (R.MAX_VOCI + 1)
		self.assertEqual([p.testo() for p in R.valida(troppe)], ["A quote has at most 200 services"])
		problemi = R.valida([voce(), voce(servizio=""), voce(qty=0, sconto=120), voce(rate=-1)])
		self.assertEqual(
			[p.testo() for p in problemi],
			[
				"Row 2: choose the service",
				"Row 3: the quantity is more than zero",
				"Row 3: the discount is from 0 to 100%",
				"Row 4: the price is not negative",
			],
		)
