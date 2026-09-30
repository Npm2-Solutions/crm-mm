# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A programme of stages, without a site: what a programme needs, when each stage
opens by time, and how the patient reads them - done, open, locked."""

from __future__ import annotations

import datetime

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the rules are still testable
	from unittest import TestCase as UnitTestCase

from crm.piani import programmi_regole as P

LUNEDI = datetime.date(2026, 10, 5)


def giorno(n: int) -> datetime.date:
	return LUNEDI + datetime.timedelta(days=n)


def tappe(*giorni):
	return [{"key": f"t{n}", "title": f"Tappa {n}", "days": g} for n, g in enumerate(giorni, 1)]


class CosaServe(UnitTestCase):
	def test_per_tempo_ogni_tappa_dice_quanto_dura_tranne_l_ultima(self):
		self.assertEqual(P.valida(P.TEMPO, tappe(7, 14, None)), [])
		self.assertEqual(P.valida(P.TEMPO, tappe(7, 14, 21)), [])
		[problema] = P.valida(P.TEMPO, tappe(7, None, 21))
		self.assertEqual(problema.testo(), "Stage 2 lasts from 1 to 365 days")
		self.assertEqual(len(P.valida(P.TEMPO, tappe(0, 400))), 2)

	def test_al_proprio_ritmo_i_giorni_non_contano(self):
		self.assertEqual(P.valida(P.RITMO, tappe(None, None, "x")), [])

	def test_almeno_una_tappa_con_il_suo_titolo_e_la_sua_chiave(self):
		self.assertEqual([p.testo() for p in P.valida(P.RITMO, [])], ["A programme has at least one stage"])
		doppie = [{"key": "a", "title": "Uno"}, {"key": "a", "title": " "}]
		self.assertEqual(
			[p.testo() for p in P.valida(P.RITMO, doppie)],
			["Every stage has its own key (a)", "Every stage has a title"],
		)
		self.assertEqual(
			[p.testo() for p in P.valida("Whenever", tappe(1))], ["Whenever is not a way a programme goes on"]
		)


class PerTempo(UnitTestCase):
	def test_le_finestre_una_dopo_l_altra(self):
		self.assertEqual(
			P.finestre(LUNEDI, tappe(7, 14, None)),
			[(giorno(0), giorno(6)), (giorno(7), giorno(20)), (giorno(21), None)],
		)

	def test_quale_tappa_e_aperta_in_un_giorno(self):
		programma = tappe(7, 14)
		self.assertIsNone(P.tappa_del_giorno(LUNEDI, programma, giorno(-1)))
		self.assertEqual(P.tappa_del_giorno(LUNEDI, programma, giorno(0)), 0)
		self.assertEqual(P.tappa_del_giorno(LUNEDI, programma, giorno(6)), 0)
		self.assertEqual(P.tappa_del_giorno(LUNEDI, programma, giorno(7)), 1)
		self.assertEqual(P.tappa_del_giorno(LUNEDI, programma, giorno(20)), 1)
		# after the last day: the programme is over
		self.assertEqual(P.tappa_del_giorno(LUNEDI, programma, giorno(21)), 2)
		# a last stage without days never ends by itself
		self.assertEqual(P.tappa_del_giorno(LUNEDI, tappe(7, None), giorno(400)), 1)
		self.assertIsNone(P.tappa_del_giorno(None, programma, giorno(3)))


class ComeLeLeggeIlPaziente(UnitTestCase):
	def test_fatte_aperta_chiuse_con_il_giorno_in_cui_si_aprono(self):
		programma = tappe(7, 14, None)
		programma[0].update(opened_on=giorno(0), completed_on=giorno(7))
		programma[1].update(opened_on=giorno(7))
		righe = P.stati(P.TEMPO, LUNEDI, programma, giorno(9))
		self.assertEqual([r["state"] for r in righe], [P.FATTA, P.APERTA, P.CHIUSA])
		self.assertEqual(righe[2]["opens_on"], giorno(21))
		self.assertEqual(righe[1]["ends_on"], giorno(20))
		self.assertEqual((P.aperta(programma), P.prossima(programma)), (1, 2))

	def test_al_proprio_ritmo_una_tappa_chiusa_non_ha_un_giorno(self):
		programma = tappe(None, None)
		programma[0]["opened_on"] = giorno(0)
		righe = P.stati(P.RITMO, LUNEDI, programma, giorno(30))
		self.assertEqual([(r["state"], r["opens_on"]) for r in righe], [(P.APERTA, None), (P.CHIUSA, None)])
		self.assertEqual(P.prossima(programma), 1)
		programma[1].update(opened_on=giorno(3), completed_on=giorno(5))
		programma[0]["completed_on"] = giorno(3)
		self.assertEqual((P.aperta(programma), P.prossima(programma)), (None, None))
