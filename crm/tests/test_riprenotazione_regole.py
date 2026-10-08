# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Who booked again — pure, no database: runs with plain ``unittest`` too."""

import datetime
import unittest

from crm.dashboard import riprenotazione_regole as R

ADESSO = datetime.datetime(2026, 10, 8, 12, 0)


def giorni(n):
	return ADESSO + datetime.timedelta(days=n)


class TestRiprenotazione(unittest.TestCase):
	visite = (
		("anna", giorni(-30), "rossi"),
		("anna", giorni(-10), "bianchi"),
		("bruno", giorni(-5), "rossi"),
		("carla", giorni(-20), "rossi"),
	)

	def test_ogni_persona_conta_per_la_sua_ultima_visita(self):
		ultime = R.ultime_visite(self.visite)
		self.assertEqual(ultime["anna"], (giorni(-10), "bianchi"))
		self.assertEqual(len(ultime), 3)

	def test_ha_riprenotato_chi_ha_qualcosa_dopo(self):
		# anna has something after her last visit, carla only something before it
		prossimi = {"anna": giorni(3), "carla": giorni(-25), "bruno": giorni(-5)}
		self.assertEqual(R.tasso(self.visite, prossimi), (1, 3))
		self.assertEqual(R.tasso((), {}), (0, 0))

	def test_per_professionista_ognuno_con_la_sua_ultima_visita(self):
		# anna's visit with rossi was before one with bianchi: rossi saw her come back
		prossimi = {"anna": giorni(-10)}
		self.assertEqual(R.per_professionista(self.visite, prossimi), {"rossi": (1, 3), "bianchi": (0, 1)})

	def test_senza_nulla_davanti_da_chi_e_venuto_da_piu_tempo(self):
		# bruno booked again but it is past (a no-show): nothing ahead all the same
		prossimi = {"anna": giorni(2), "bruno": giorni(-1)}
		fuori = R.senza_prossimo(self.visite, prossimi, ADESSO)
		self.assertEqual([riga[0] for riga in fuori], ["carla", "bruno"])
		self.assertEqual(fuori[0], ("carla", giorni(-20), "rossi"))


if __name__ == "__main__":
	unittest.main()
