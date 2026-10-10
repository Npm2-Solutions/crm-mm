# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What is invoiced when money arrives online, without a site: the line that adds up
to the money received, the balance after the advances, a refund's credit note."""

import unittest
from decimal import Decimal

from crm.pagamenti import fatture_regole as R


class TestImporto(unittest.TestCase):
	def test_la_riga_che_torna_con_la_cassa(self):
		# 30 paid, a 2% fund on top: the line is 29.41, the invoice 30.00
		imponibile = R.imponibile_per(30, 30, Decimal("30.60"))
		self.assertEqual(imponibile, Decimal("29.41"))
		self.assertTrue(R.torna(30, Decimal("29.41") * Decimal("1.02")))
		# with VAT
		self.assertEqual(R.imponibile_per(122, 122, Decimal("148.84")), Decimal("100.00"))

	def test_niente_da_dividere(self):
		self.assertEqual(R.imponibile_per(30, 0, 0), Decimal("30.00"))
		self.assertFalse(R.torna(30, "29.99"))
		self.assertTrue(R.torna("30.004", 30))


class TestSaldo(unittest.TestCase):
	def test_il_prezzo_meno_gli_acconti(self):
		anticipato = R.anticipato([{"net_total": 29.41}])
		self.assertEqual(R.saldo(80, anticipato), Decimal("50.59"))
		self.assertFalse(R.coperto(80, anticipato))

	def test_una_nota_di_credito_riduce_l_acconto(self):
		anticipato = R.anticipato([{"net_total": 30}, {"net_total": 10, "nota": True}])
		self.assertEqual(anticipato, Decimal("20.00"))
		self.assertEqual(R.saldo(80, anticipato), Decimal("60.00"))

	def test_tutto_pagato_prima(self):
		self.assertTrue(R.coperto(80, R.anticipato([{"net_total": 80}])))
		self.assertEqual(R.saldo(80, 95), Decimal("0.00"))
		# no advance, nothing covered; no price, never covered by nothing
		self.assertFalse(R.coperto(80, 0))
		self.assertFalse(R.coperto(0, 0))
		self.assertEqual(R.anticipato([{"net_total": 10, "nota": True}]), Decimal("0.00"))


class TestRimborso(unittest.TestCase):
	def test_dove_e_l_acconto(self):
		self.assertEqual(R.al_rimborso(1), R.NOTA)
		self.assertEqual(R.al_rimborso(0), R.TOGLI)
		self.assertEqual(R.al_rimborso(2), R.NIENTE)
		self.assertEqual(R.al_rimborso(None), R.NIENTE)

	def test_tutto_o_in_parte(self):
		# all of the 30 back: all the taxable
		self.assertEqual(R.da_stornare(30, 30, Decimal("29.41"), 0), Decimal("29.41"))
		# half back, then the rest
		meta = R.da_stornare(15, 30, Decimal("29.41"), 0)
		self.assertEqual(meta, Decimal("14.71"))
		self.assertEqual(R.da_stornare(30, 30, Decimal("29.41"), meta), Decimal("14.70"))
		# the same refund told twice: nothing more
		self.assertEqual(R.da_stornare(30, 30, Decimal("29.41"), Decimal("29.41")), Decimal("0.00"))
		self.assertEqual(R.da_stornare(0, 30, 29, 0), Decimal("0.00"))


if __name__ == "__main__":
	unittest.main()
