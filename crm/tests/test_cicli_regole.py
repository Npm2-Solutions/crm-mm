# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""A cycle of sessions, without a site: what each appointment is for the cycle,
how many are left, when a cycle is over or expired, and which appointment joins it."""

from __future__ import annotations

import datetime

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the rules are still testable
	from unittest import TestCase as UnitTestCase

from crm.scheduling import cicli_regole as C

OGGI = datetime.date(2026, 10, 5)


class LaSeduta(UnitTestCase):
	def test_da_come_e_andata(self):
		for appuntamento, persona, atteso in (
			("Scheduled", "Booked", C.PRENOTATA),
			("Confirmed", "Booked", C.PRENOTATA),
			("Scheduled", "Arrived", C.FATTA),
			("Completed", "Booked", C.FATTA),
			("Scheduled", "Attended", C.FATTA),
			("No Show", "Booked", C.PERSA),
			("Scheduled", "No Show", C.PERSA),
			("Cancelled", "Booked", C.ANNULLATA),
			("Scheduled", "Cancelled", C.ANNULLATA),
			(None, None, C.PRENOTATA),
		):
			self.assertEqual(C.seduta(appuntamento, persona), atteso, (appuntamento, persona))


class IConti(UnitTestCase):
	def test_quante_ne_restano(self):
		sedute = [C.FATTA, C.FATTA, C.PERSA, C.PRENOTATA, C.ANNULLATA]
		self.assertEqual(
			C.conta(sedute, 10),
			{"done": 2, "missed": 1, "booked": 1, "used": 3, "left": 6, "total": 10},
		)
		# a missed session not counted is one more to book
		self.assertEqual(C.conta(sedute, 10, perse_contano=False)["left"], 7)
		self.assertEqual(C.conta([C.PRENOTATA] * 12, 10)["left"], 0)

	def test_finito_scaduto_chiuso(self):
		finito = C.conta([C.FATTA] * 9 + [C.PERSA], 10)
		self.assertEqual(C.stato(finito, None, OGGI), C.COMPLETATO)
		a_meta = C.conta([C.FATTA] * 4, 10)
		self.assertEqual(C.stato(a_meta, OGGI, OGGI), C.ATTIVO)
		self.assertEqual(C.stato(a_meta, OGGI - datetime.timedelta(days=1), OGGI), C.SCADUTO)
		self.assertEqual(C.stato(a_meta, None, OGGI, chiuso=True), C.CHIUSO)


class ChiSiAggiunge(UnitTestCase):
	def test_solo_un_ciclo_in_corso_nei_suoi_giorni_con_sedute_da_prenotare(self):
		conti = C.conta([C.FATTA, C.PRENOTATA], 3)
		fine = OGGI + datetime.timedelta(days=30)
		self.assertTrue(C.si_aggiunge(C.ATTIVO, conti, OGGI, fine, OGGI + datetime.timedelta(days=7)))
		self.assertFalse(C.si_aggiunge(C.ATTIVO, conti, OGGI, fine, OGGI - datetime.timedelta(days=1)))
		self.assertFalse(C.si_aggiunge(C.ATTIVO, conti, OGGI, fine, fine + datetime.timedelta(days=1)))
		self.assertFalse(C.si_aggiunge(C.SCADUTO, conti, OGGI, fine, OGGI))
		pieno = C.conta([C.FATTA, C.PRENOTATA, C.PRENOTATA], 3)
		self.assertFalse(C.si_aggiunge(C.ATTIVO, pieno, OGGI, None, OGGI))

	def test_la_seduta_numero(self):
		sedute = [("a", C.FATTA), ("b", C.ANNULLATA), ("c", C.PERSA), ("d", C.PRENOTATA)]
		self.assertEqual(C.numeri(sedute), {"a": 1, "c": 2, "d": 3})
		# a missed session the cycle does not count is booked again: no number
		self.assertEqual(C.numeri(sedute, perse_contano=False), {"a": 1, "d": 2})
