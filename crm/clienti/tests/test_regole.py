# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Who becomes a client: the rules, without a site."""

from __future__ import annotations

from datetime import datetime

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the rules are still testable
	from unittest import TestCase as UnitTestCase

from crm.clienti import regole as r


class ChiEVenuto(UnitTestCase):
	def test_chi_e_segnato_presente(self):
		self.assertTrue(r.presente("Confirmed", "Attended"))

	def test_un_appuntamento_svolto_rende_presenti_quelli_che_c_erano(self):
		self.assertTrue(r.presente("Completed", "Booked"))

	def test_chi_non_e_venuto_resta_un_contatto(self):
		"""Better a client less than a no-show counted as a client."""
		self.assertFalse(r.presente("Completed", "No Show"))
		self.assertFalse(r.presente("Completed", "Cancelled"))
		self.assertFalse(r.presente("No Show", "Booked"))
		self.assertFalse(r.presente("Confirmed", "Booked"))

	def test_accolto_al_banco(self):
		self.assertTrue(r.accolto(datetime(2026, 5, 4, 9, 55), "Arrived"))
		self.assertTrue(r.accolto("2026-05-04 09:55:00", "Attended"))
		self.assertFalse(r.accolto(None, "Arrived"))
		# checked in, then marked as gone: nobody came
		self.assertFalse(r.accolto(datetime(2026, 5, 4, 9, 55), "No Show"))


class LaFattura(UnitTestCase):
	def test_una_fattura_vende(self):
		self.assertTrue(r.vendita("TD01"))
		self.assertTrue(r.vendita("TD06"))
		self.assertTrue(r.vendita(None))

	def test_una_nota_di_credito_no(self):
		self.assertFalse(r.vendita("TD04"))
		self.assertFalse(r.vendita("TD08"))


class IlPrimoFatto(UnitTestCase):
	def test_niente_fatti_niente_cliente(self):
		self.assertIsNone(r.primo([]))
		self.assertIsNone(r.primo([(None, r.FATTURA)]))

	def test_vince_il_primo_nel_tempo(self):
		"""January's invoice came before March's appointment: January is when."""
		gennaio, marzo = datetime(2026, 1, 20), datetime(2026, 3, 2, 10)
		self.assertEqual(
			r.primo([(marzo, r.APPUNTAMENTO_SVOLTO), (gennaio, r.FATTURA)]), (gennaio, r.FATTURA)
		)

	def test_allo_stesso_momento_conta_l_ordine(self):
		adesso = datetime(2026, 5, 4, 10)
		self.assertEqual(r.primo([(adesso, r.FATTURA), (adesso, r.ACCETTAZIONE)]), (adesso, r.ACCETTAZIONE))

	def test_i_valori_restano_in_inglese(self):
		self.assertEqual(
			[regola.valore for regola in r.REGOLE], ["Check-in", "Appointment attended", "Invoice"]
		)
