# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""«I'm here» from the phone, without a site: when it is offered."""

import datetime
import unittest

from crm.scheduling import arrivi_regole as R


def ora(ore: int, minuti: int = 0) -> datetime.datetime:
	return datetime.datetime(2026, 10, 8, ore, minuti)


class QuandoSiArriva(unittest.TestCase):
	def test_da_mezz_ora_prima_alla_fine(self):
		inizio, fine = ora(10), ora(11)
		self.assertEqual(R.perche_no(inizio, fine, ora(9, 29), "Confirmed", "Booked"), R.PRESTO)
		self.assertIsNone(R.perche_no(inizio, fine, ora(9, 30), "Confirmed", "Booked"))
		self.assertIsNone(R.perche_no(inizio, fine, ora(10, 40), "Scheduled", "Booked"))
		self.assertEqual(R.perche_no(inizio, fine, ora(11), "Confirmed", "Booked"), R.FINITO)

	def test_senza_fine_finisce_quando_comincia(self):
		self.assertEqual(R.finestra(ora(10), None), (ora(9, 30), ora(10)))
		self.assertEqual(R.perche_no(ora(10), None, ora(10, 1), "Confirmed", "Booked"), R.FINITO)

	def test_annullato_o_gia_detto(self):
		inizio, fine = ora(10), ora(11)
		self.assertEqual(R.perche_no(inizio, fine, ora(10), "Cancelled", "Booked"), R.ANNULLATO)
		self.assertEqual(R.perche_no(inizio, fine, ora(10), "Confirmed", "Cancelled"), R.ANNULLATO)
		self.assertEqual(R.perche_no(inizio, fine, ora(10), "Confirmed", "Arrived"), R.GIA_DETTO)
		self.assertEqual(R.perche_no(inizio, fine, ora(10), "Completed", "Attended"), R.ANNULLATO)

	def test_tra_quanto(self):
		self.assertEqual(R.tra_quanto(ora(10), ora(11), ora(9)), {"opens_in": 1800, "closes_in": 7200})
		self.assertEqual(R.tra_quanto(ora(10), ora(11), ora(10)), {"opens_in": 0, "closes_in": 3600})
		self.assertEqual(R.tra_quanto(ora(10), ora(11), ora(12)), {"opens_in": 0, "closes_in": 0})
