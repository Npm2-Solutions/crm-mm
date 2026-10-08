# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's locations without a site (docs/crm/62): plain `unittest`."""

import unittest
from types import SimpleNamespace

from crm.scheduling import sedi_regole as R

STANZE = [
	{"name": "Studio 1", "resource_type": "Room", "centre_location": "MI"},
	{"name": "Studio 2", "resource_type": "Room", "centre_location": "MI"},
	{"name": "Monza A", "resource_type": "Room", "centre_location": "MB"},
	{"name": "Ecografo", "resource_type": "Equipment", "centre_location": None},
]


class TestUnaSedeNonESede(unittest.TestCase):
	def test_piu_sedi(self):
		self.assertFalse(R.piu_sedi([]))
		self.assertFalse(R.piu_sedi(None))
		self.assertFalse(R.piu_sedi([{"name": "MI"}]))
		self.assertTrue(R.piu_sedi([{"name": "MI"}, {"name": "MB"}]))


class TestDove(unittest.TestCase):
	def test_senza_sede_serve_tutte(self):
		self.assertTrue(R.serve(None, "MI"))
		self.assertTrue(R.serve("", "MI"))
		self.assertTrue(R.serve("MB", None))
		self.assertTrue(R.serve("MI", "MI"))
		self.assertFalse(R.serve("MB", "MI"))

	def test_righe_della_sede(self):
		righe = [
			SimpleNamespace(workday="Tuesday", centre_location="MB"),
			SimpleNamespace(workday="Monday", centre_location=None),
			{"workday": "Friday", "centre_location": "MI"},
		]
		self.assertEqual(len(R.della_sede(righe, "MI")), 2)
		self.assertEqual(len(R.della_sede(righe, "MB")), 2)
		self.assertEqual(len(R.della_sede(righe, None)), 3)

	def test_la_stanza_di_un_altra_sede_lascia_il_posto_al_suo_tipo(self):
		self.assertEqual(R.stanze_al_posto("Studio 2", None, STANZE, "MI"), ["Studio 2"])
		self.assertEqual(R.stanze_al_posto("Studio 2", None, STANZE, "MB"), ["Monza A"])
		self.assertEqual(R.stanze_al_posto("Studio 2", None, STANZE, None), ["Studio 2"])
		# equipment without a location goes anywhere
		self.assertEqual(R.stanze_al_posto("Ecografo", None, STANZE, "MB"), ["Ecografo"])
		self.assertEqual(R.stanze_al_posto("Sparita", None, STANZE, "MB"), [])

	def test_per_tipo(self):
		self.assertEqual(R.stanze_al_posto(None, "Room", STANZE, "MI"), ["Studio 1", "Studio 2"])
		self.assertEqual(R.stanze_al_posto(None, "Room", STANZE, "MB"), ["Monza A"])

	def test_la_sede_dell_appuntamento(self):
		self.assertEqual(R.sede_dell_appuntamento(["MB"], "MI", "MI", ["MI", "MB"]), "MB")
		self.assertEqual(R.sede_dell_appuntamento([None], "MI", "MB", ["MI", "MB"]), "MI")
		self.assertEqual(R.sede_dell_appuntamento([], None, "MB", ["MI", "MB"]), "MB")
		self.assertEqual(R.sede_dell_appuntamento([], None, None, ["MI"]), "MI")
		self.assertIsNone(R.sede_dell_appuntamento([], None, None, ["MI", "MB"]))
		self.assertIsNone(R.sede_dell_appuntamento([], None, None, []))

	def test_in_due_posti(self):
		self.assertEqual(R.in_conflitto("MB", ["MI"]), "MI")
		self.assertIsNone(R.in_conflitto("MB", ["MB", None]))
		self.assertIsNone(R.in_conflitto(None, ["MI"]))

	def test_dove_si_tiene_un_servizio(self):
		attive = ["MI", "MB"]
		# a room in Milan, a professional only in Milan: Milan
		self.assertEqual(R.sedi_del_servizio([{"resource": "Studio 1"}], STANZE, [["MI"]], attive), ["MI"])
		# a room in Milan, a professional in both: both (Monza takes its own room)
		self.assertIsNone(R.sedi_del_servizio([{"resource": "Studio 1"}], STANZE, [["MI", "MB"]], attive))
		# no room, a professional good anywhere
		self.assertIsNone(R.sedi_del_servizio([], STANZE, [[""]], attive))
		# no room, one professional in Monza only
		self.assertEqual(R.sedi_del_servizio([], STANZE, [["MB"]], attive), ["MB"])
		# a kind nobody has in Monza
		self.assertEqual(
			R.sedi_del_servizio(
				[{"resource_type": "Vehicle"}],
				STANZE + [{"name": "Auto", "resource_type": "Vehicle", "centre_location": "MI"}],
				[[""]],
				attive,
			),
			["MI"],
		)


class TestIndirizzo(unittest.TestCase):
	def test_come_una_busta(self):
		sede = {
			"location_name": "Sede di Monza",
			"address_line": "Via  Italia 12",
			"pincode": "20900",
			"city": "Monza",
			"province": "mb",
		}
		self.assertEqual(R.indirizzo(sede), "Via Italia 12, 20900 Monza (MB)")
		self.assertEqual(R.dove(sede), "Sede di Monza, Via Italia 12, 20900 Monza (MB)")
		self.assertEqual(R.dove({"location_name": "Sede di Monza"}), "Sede di Monza")
		self.assertEqual(R.indirizzo(None), "")
		self.assertEqual(R.dove(None), "")

	def test_link(self):
		self.assertTrue(R.link_valido("https://maps.app.goo.gl/abc"))
		self.assertFalse(R.link_valido("http://maps.example.com"))
		self.assertFalse(R.link_valido("javascript:alert(1)"))
		self.assertFalse(R.link_valido(""))


if __name__ == "__main__":
	unittest.main()
