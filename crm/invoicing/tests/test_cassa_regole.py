# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The cash closing without a site: by way of paying, by who issued, the credit
notes out, the drawer's cash and the difference to the cent."""

import unittest

from crm.invoicing import cassa_regole as R


def riga(metodo, importo, chi="anna@centro.it"):
	return {"payment_method": metodo, "amount": importo, "issued_by": chi}


class IlGiorno(unittest.TestCase):
	def test_per_metodo_e_per_chi(self):
		conti = R.riepilogo(
			[
				riga("MP01", 50),
				riga("MP08", 80, "luca@centro.it"),
				riga("MP01", 0.1),
				riga("MP01", 0.2),
			],
			[riga("MP01", 20)],
		)
		self.assertEqual(conti["collected"], 130.3)
		self.assertEqual(conti["refunded"], 20)
		self.assertEqual(conti["total"], 110.3)
		self.assertEqual(conti["count"], 4)
		contanti = next(voce for voce in conti["methods"] if voce["method"] == "MP01")
		self.assertEqual(
			(
				contanti["collected"],
				contanti["refunded"],
				contanti["net"],
				contanti["count"],
				contanti["notes"],
			),
			(50.3, 20, 30.3, 3, 1),
		)
		# the way most money came by first
		self.assertEqual([voce["method"] for voce in conti["methods"]], ["MP08", "MP01"])
		self.assertEqual(conti["expected_cash"], 30.3)
		self.assertEqual(
			[(chi["user"], chi["total"], chi["count"]) for chi in conti["by_user"]],
			[("luca@centro.it", 80, 1), ("anna@centro.it", 50.3, 3)],
		)

	def test_un_giorno_vuoto_o_senza_contanti(self):
		self.assertEqual(R.riepilogo([])["expected_cash"], 0)
		self.assertEqual(R.riepilogo([riga("MP05", 100)])["expected_cash"], 0)
		self.assertEqual(R.riepilogo([riga(None, 10)])["methods"][0]["method"], "")

	def test_la_nota_di_credito_restituisce_soltanto(self):
		conti = R.riepilogo([], [riga("MP01", 30)])
		self.assertEqual((conti["collected"], conti["total"], conti["expected_cash"]), (0, -30, -30))
		self.assertEqual(conti["by_user"], [])


class LaDifferenza(unittest.TestCase):
	def test_al_centesimo(self):
		self.assertEqual(R.differenza(100, 100), 0)
		self.assertEqual(R.differenza(99.9, 100), -0.1)
		self.assertEqual(R.differenza("120.30", 120.1), 0.2)
		self.assertEqual(str(R.differenza(0.3, 0.1 + 0.2)), "0.0")
		self.assertEqual(R.differenza(None, 5), -5)


if __name__ == "__main__":
	unittest.main()
