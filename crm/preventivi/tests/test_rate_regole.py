# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A quote paid in instalments, without a site: the deposit, the schedule to the
cent, what is wrong, how it goes - on the cases the browser proves too."""

import datetime
import json
import pathlib
import unittest

from crm.preventivi import rate_regole as R

CASI = json.loads((pathlib.Path(__file__).parent / "casi_rate.json").read_text())


def giorno(testo):
	return datetime.date.fromisoformat(testo) if testo else None


class ICasiInComune(unittest.TestCase):
	def test_l_acconto(self):
		for caso in CASI["acconto"]:
			with self.subTest(caso=caso):
				self.assertEqual(R.acconto(caso["totale"], caso["tipo"], caso["valore"]), caso["atteso"])

	def test_le_quote(self):
		for caso in CASI["quote"]:
			with self.subTest(caso=caso):
				fatto = R.quote(caso["resto"], caso["numero"])
				self.assertEqual(len(fatto), caso["numero"])
				self.assertAlmostEqual(sum(fatto), caso["resto"], places=6)
				if "atteso" in caso:
					self.assertEqual(fatto, caso["atteso"])
				else:
					self.assertEqual(fatto[0], caso["atteso_prima"])
					self.assertEqual(fatto[-1], caso["atteso_ultima"])

	def test_il_piano(self):
		for caso in CASI["piano"]:
			with self.subTest(caso=caso["totale"]):
				fatto = R.piano(
					caso["totale"], caso["acconto"], caso["numero"], caso["ogni"], giorno(caso["primo"])
				)
				atteso = [{**riga, "due_on": giorno(riga["due_on"])} for riga in caso["atteso"]]
				self.assertEqual(fatto, atteso)
				self.assertAlmostEqual(sum(r["amount"] for r in fatto), caso["totale"], places=6)

	def test_cosa_non_va(self):
		for caso in CASI["problemi"]:
			with self.subTest(caso=caso):
				fatto = R.problemi(
					caso["totale"],
					caso["tipo"],
					caso["valore"],
					caso["numero"],
					caso["ogni"],
					giorno(caso["primo"]),
					giorno(caso.get("oggi")),
				)
				self.assertEqual([p.messaggio for p in fatto], caso["atteso"])

	def test_come_va(self):
		for caso in CASI["riassunto"]:
			rate = [{**riga, "due_on": giorno(riga["due_on"])} for riga in caso["rate"]]
			fatto = R.riassunto(rate, giorno(caso["oggi"]))
			atteso = caso["atteso"]
			self.assertEqual(fatto["count"], atteso["count"])
			self.assertEqual(fatto["paid"], atteso["paid"])
			self.assertEqual(fatto["next"]["due_on"], giorno(atteso["next_due_on"]))
			self.assertEqual(fatto["late"], atteso["late"])
			self.assertEqual(fatto["late_amount"], atteso["late_amount"])
			self.assertEqual(fatto["left"], atteso["left"])
			self.assertEqual(fatto["cancelled"], atteso["cancelled"])


class LeRighe(unittest.TestCase):
	def setUp(self):
		self.rate = [
			{"kind": R.ACCONTO, "due_on": datetime.date(2026, 10, 8), "amount": 400, "status": R.PAGATA},
			{"kind": R.RATA, "due_on": datetime.date(2026, 11, 1), "amount": 360, "status": R.DA_PAGARE},
			{"kind": R.RATA, "due_on": datetime.date(2026, 12, 1), "amount": 360, "status": R.DA_PAGARE},
			{"kind": R.RATA, "due_on": datetime.date(2027, 1, 1), "amount": 360, "status": R.FATTURATA},
		]

	def test_le_dovute_oggi(self):
		self.assertEqual(R.dovute(self.rate, datetime.date(2026, 10, 31)), [])
		self.assertEqual(R.dovute(self.rate, datetime.date(2026, 11, 1)), [1])
		self.assertEqual(R.dovute(self.rate, datetime.date(2027, 3, 1)), [1, 2])

	def test_cosa_si_annulla_e_il_resto(self):
		self.assertEqual(R.da_annullare(self.rate), [1, 2])
		self.assertEqual(R.resto(self.rate), 720)

	def test_lo_stato_dalla_fattura(self):
		self.assertEqual(R.stato(True, True, True), R.ANNULLATA)
		self.assertEqual(R.stato(False, True, True), R.PAGATA)
		self.assertEqual(R.stato(False, True, False), R.FATTURATA)
		self.assertEqual(R.stato(False, False, False), R.DA_PAGARE)
		self.assertEqual(R.stato(False, False, False, segnata=True), R.PAGATA)

	def test_nulla_da_seguire(self):
		self.assertIsNone(R.riassunto([], datetime.date(2026, 1, 1)))
		self.assertIsNone(R.riassunto([{"kind": R.RATA, "status": R.ANNULLATA}], datetime.date(2026, 1, 1)))

	def test_tutto_pagato(self):
		rate = [{**r, "status": R.PAGATA} for r in self.rate]
		fatto = R.riassunto(rate, datetime.date(2027, 6, 1))
		self.assertIsNone(fatto["next"])
		self.assertEqual((fatto["paid"], fatto["count"], fatto["left"]), (3, 3, 0))


if __name__ == "__main__":
	unittest.main()
