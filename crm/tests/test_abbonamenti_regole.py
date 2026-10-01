# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A subscription, without a site: its last day, the instalments, the week or month
an entry is counted in, suspensions, which appointment uses an entry, the reminder."""

from __future__ import annotations

import datetime

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the rules are still testable
	from unittest import TestCase as UnitTestCase

from crm.scheduling import abbonamenti_regole as A
from crm.scheduling import cicli_regole as C

D = datetime.date


class IlTempo(UnitTestCase):
	def test_lo_stesso_giorno_dei_mesi_dopo(self):
		self.assertEqual(A.piu_mesi(D(2026, 10, 5), 1), D(2026, 11, 5))
		self.assertEqual(A.piu_mesi(D(2026, 10, 5), 3), D(2027, 1, 5))
		self.assertEqual(A.piu_mesi(D(2026, 12, 15), 12), D(2027, 12, 15))
		# a shorter month: its last day
		self.assertEqual(A.piu_mesi(D(2027, 1, 31), 1), D(2027, 2, 28))
		self.assertEqual(A.piu_mesi(D(2028, 1, 31), 1), D(2028, 2, 29))
		self.assertEqual(A.piu_mesi(D(2026, 8, 31), 1), D(2026, 9, 30))

	def test_l_ultimo_giorno(self):
		# a month from 5 October: until 4 November
		self.assertEqual(A.fine(D(2026, 10, 5), 1), D(2026, 11, 4))
		self.assertEqual(A.fine(D(2026, 10, 1), 3), D(2026, 12, 31))
		self.assertEqual(A.fine(D(2026, 1, 1), 12), D(2026, 12, 31))
		# a week suspended moves it a week later
		self.assertEqual(A.fine(D(2026, 10, 5), 1, [(D(2026, 10, 12), D(2026, 10, 18))]), D(2026, 11, 11))

	def test_i_giorni_sospesi_contano_il_primo_e_l_ultimo(self):
		self.assertEqual(A.giorni_sospesi([]), 0)
		self.assertEqual(A.giorni_sospesi([(D(2026, 10, 12), D(2026, 10, 12))]), 1)
		self.assertEqual(
			A.giorni_sospesi([(D(2026, 10, 12), D(2026, 10, 18)), (D(2026, 11, 1), D(2026, 11, 3))]), 10
		)
		# backwards counts nothing
		self.assertEqual(A.giorni_sospesi([(D(2026, 10, 18), D(2026, 10, 12))]), 0)

	def test_i_numeri_del_centro(self):
		self.assertEqual(A.entro(None, A.MESI), 1)
		self.assertEqual(A.entro(3, A.MESI), 3)
		self.assertEqual(A.entro(99, A.MESI), 36)
		self.assertEqual(A.entro("x", A.PROMEMORIA), 7)


class LeRate(UnitTestCase):
	def test_subito_una_sola(self):
		self.assertEqual(A.rate(D(2026, 10, 5), 3, 270, A.SUBITO), [(D(2026, 10, 5), 270.0)])
		# a month by the month is one instalment too
		self.assertEqual(A.rate(D(2026, 10, 5), 1, 60, A.MENSILE), [(D(2026, 10, 5), 60.0)])

	def test_una_al_mese_lo_stesso_giorno(self):
		self.assertEqual(
			A.rate(D(2026, 10, 31), 3, 270, A.MENSILE),
			[(D(2026, 10, 31), 90.0), (D(2026, 11, 30), 90.0), (D(2026, 12, 31), 90.0)],
		)

	def test_l_ultima_prende_i_centesimi(self):
		fatto = A.rate(D(2026, 10, 5), 3, 100, A.MENSILE)
		self.assertEqual([importo for _giorno, importo in fatto], [33.33, 33.33, 33.34])
		self.assertEqual(round(sum(importo for _giorno, importo in fatto), 2), 100.0)
		fatto = A.rate(D(2026, 1, 1), 12, 499, A.MENSILE)
		self.assertEqual(len(fatto), 12)
		self.assertEqual(round(sum(importo for _giorno, importo in fatto), 2), 499.0)
		self.assertEqual(fatto[-1][0], D(2026, 12, 1))


class IlPeriodo(UnitTestCase):
	def test_la_settimana_dal_lunedi_alla_domenica(self):
		# 7 October 2026 is a Wednesday
		self.assertEqual(
			A.periodo(D(2026, 10, 7), D(2026, 10, 1), A.A_SETTIMANA), (D(2026, 10, 5), D(2026, 10, 11))
		)
		self.assertEqual(
			A.periodo(D(2026, 10, 11), D(2026, 10, 1), A.A_SETTIMANA), (D(2026, 10, 5), D(2026, 10, 11))
		)
		self.assertEqual(
			A.periodo(D(2026, 10, 12), D(2026, 10, 1), A.A_SETTIMANA), (D(2026, 10, 12), D(2026, 10, 18))
		)

	def test_il_mese_dell_abbonamento(self):
		inizio = D(2026, 10, 15)
		self.assertEqual(A.periodo(D(2026, 10, 15), inizio, A.AL_MESE), (D(2026, 10, 15), D(2026, 11, 14)))
		self.assertEqual(A.periodo(D(2026, 11, 14), inizio, A.AL_MESE), (D(2026, 10, 15), D(2026, 11, 14)))
		self.assertEqual(A.periodo(D(2026, 11, 15), inizio, A.AL_MESE), (D(2026, 11, 15), D(2026, 12, 14)))
		self.assertEqual(A.periodo(D(2027, 1, 2), inizio, A.AL_MESE), (D(2026, 12, 15), D(2027, 1, 14)))
		# from the 31st: the shorter months end earlier
		inizio = D(2026, 1, 31)
		self.assertEqual(A.periodo(D(2026, 2, 27), inizio, A.AL_MESE), (D(2026, 1, 31), D(2026, 2, 27)))
		self.assertEqual(A.periodo(D(2026, 2, 28), inizio, A.AL_MESE), (D(2026, 2, 28), D(2026, 3, 30)))

	def test_senza_conti(self):
		self.assertIsNone(A.periodo(D(2026, 10, 7), D(2026, 10, 1), A.ILLIMITATI))


class GliIngressi(UnitTestCase):
	def test_quelli_che_contano(self):
		ingressi = [C.FATTA, C.PRENOTATA, C.PERSA, C.ANNULLATA]
		self.assertEqual(A.usati(ingressi), 3)
		self.assertEqual(A.usati(ingressi, perse_contano=False), 2)
		self.assertEqual(A.ingresso("Scheduled", "Arrived"), C.FATTA)
		self.assertEqual(A.ingresso("Cancelled", "Booked"), C.ANNULLATA)

	def test_chi_usa_un_ingresso(self):
		inizio, ultimo = D(2026, 10, 1), D(2026, 10, 31)
		sospensioni = [(D(2026, 10, 12), D(2026, 10, 18))]

		def entra(giorno, usati=0, quanti=2, come=A.A_SETTIMANA, chiuso=False):
			return A.si_aggiunge(chiuso, giorno, inizio, ultimo, sospensioni, usati, quanti, come)

		self.assertTrue(entra(D(2026, 10, 7)))
		self.assertTrue(entra(D(2026, 10, 7), usati=1))
		# the week's two are taken
		self.assertFalse(entra(D(2026, 10, 7), usati=2))
		# any number
		self.assertTrue(entra(D(2026, 10, 7), usati=40, quanti=0, come=A.ILLIMITATI))
		# outside its days, suspended, closed
		self.assertFalse(entra(D(2026, 9, 30)))
		self.assertFalse(entra(D(2026, 11, 1)))
		self.assertFalse(entra(D(2026, 10, 14)))
		self.assertFalse(entra(D(2026, 10, 7), chiuso=True))
		# a count of none takes none
		self.assertFalse(entra(D(2026, 10, 7), quanti=0, come=A.AL_MESE))


class LoStato(UnitTestCase):
	def test_come_sta(self):
		ultimo = D(2026, 10, 31)
		sospensioni = [(D(2026, 10, 12), D(2026, 10, 18))]
		self.assertEqual(A.stato(D(2026, 10, 7), ultimo, sospensioni), A.ATTIVO)
		self.assertEqual(A.stato(D(2026, 10, 12), ultimo, sospensioni), A.SOSPESO)
		self.assertEqual(A.stato(D(2026, 10, 31), ultimo, sospensioni), A.ATTIVO)
		self.assertEqual(A.stato(D(2026, 11, 1), ultimo, sospensioni), A.SCADUTO)
		self.assertEqual(A.stato(D(2026, 10, 7), ultimo, sospensioni, chiuso=True), A.CHIUSO)
		# sold to start later: active
		self.assertEqual(A.stato(D(2026, 9, 20), ultimo), A.ATTIVO)


class LaSospensione(UnitTestCase):
	inizio, ultimo = D(2026, 10, 1), D(2026, 12, 31)

	def problema(self, da, a, gia=(), massimo=0):
		return A.problema_della_sospensione(da, a, self.inizio, self.ultimo, list(gia), massimo)

	def test_quando_si_puo(self):
		self.assertIsNone(self.problema(D(2026, 10, 12), D(2026, 10, 18)))
		self.assertIsNone(self.problema(D(2026, 12, 31), D(2027, 1, 6)))
		self.assertIsNone(
			self.problema(D(2026, 11, 1), D(2026, 11, 7), [(D(2026, 10, 12), D(2026, 10, 18))], 14)
		)

	def test_quando_no(self):
		self.assertEqual(self.problema(None, D(2026, 10, 18)), "Both days are needed")
		self.assertEqual(
			self.problema(D(2026, 10, 18), D(2026, 10, 12)), "The suspension ends before it starts"
		)
		self.assertEqual(
			self.problema(D(2026, 9, 20), D(2026, 10, 5)), "The suspension starts outside the subscription"
		)
		self.assertEqual(
			self.problema(D(2026, 10, 15), D(2026, 10, 20), [(D(2026, 10, 12), D(2026, 10, 18))]),
			"It overlaps another suspension",
		)
		self.assertEqual(
			self.problema(D(2026, 11, 1), D(2026, 11, 10), [(D(2026, 10, 12), D(2026, 10, 18))], 14),
			"More days than the type allows",
		)


class LaFine(UnitTestCase):
	def test_il_promemoria(self):
		ultimo = D(2026, 10, 31)
		self.assertFalse(A.da_ricordare(D(2026, 10, 23), ultimo, 7))
		self.assertTrue(A.da_ricordare(D(2026, 10, 24), ultimo, 7))
		self.assertTrue(A.da_ricordare(D(2026, 10, 31), ultimo, 7))
		self.assertFalse(A.da_ricordare(D(2026, 11, 1), ultimo, 7))
		# on the last day only
		self.assertTrue(A.da_ricordare(D(2026, 10, 31), ultimo, 0))
		self.assertFalse(A.da_ricordare(D(2026, 10, 30), ultimo, 0))

	def test_il_rinnovo_parte_il_giorno_dopo(self):
		self.assertEqual(A.rinnovo_da(D(2026, 10, 31)), D(2026, 11, 1))
