# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""How a person becomes a patient: the rules, without a site."""

from __future__ import annotations

from datetime import datetime

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the rules are still testable
	from unittest import TestCase as UnitTestCase

from crm.clinica import regole as r
from crm.permissions import livelli


class PresenteTest(UnitTestCase):
	def test_chi_e_segnato_presente(self):
		self.assertTrue(r.presente("Confirmed", "Attended"))

	def test_un_appuntamento_svolto_rende_presenti_quelli_che_c_erano(self):
		self.assertTrue(r.presente("Completed", "Booked"))

	def test_chi_non_e_venuto_resta_un_contatto(self):
		"""Better a patient less than a no-show counted as a patient."""
		self.assertFalse(r.presente("Completed", "No Show"))
		self.assertFalse(r.presente("Completed", "Cancelled"))
		self.assertFalse(r.presente("No Show", "Booked"))
		self.assertFalse(r.presente("Confirmed", "Booked"))


class PrimaRegolaTest(UnitTestCase):
	def test_niente_fatti_niente_paziente(self):
		self.assertIsNone(r.prima_regola({}))
		self.assertIsNone(r.prima_regola({r.FATTURA_SANITARIA.valore: None}))

	def test_vince_la_prima_nel_tempo(self):
		"""Last January's invoice came before March's appointment: the invoice converted."""
		regola, quando = r.prima_regola(
			{
				r.APPUNTAMENTO_SVOLTO.valore: datetime(2026, 3, 1),
				r.FATTURA_SANITARIA.valore: datetime(2026, 1, 15),
			}
		)
		self.assertEqual(regola, r.FATTURA_SANITARIA)
		self.assertEqual(quando, datetime(2026, 1, 15))

	def test_nello_stesso_momento_l_ordine_della_tabella(self):
		stesso = datetime(2026, 2, 2, 10)
		regola, _quando = r.prima_regola(
			{r.FATTURA_SANITARIA.valore: stesso, r.APPUNTAMENTO_SVOLTO.valore: stesso}
		)
		self.assertEqual(regola, r.APPUNTAMENTO_SVOLTO)

	def test_le_regole_sono_sei_e_in_ordine(self):
		self.assertEqual([regola.numero for regola in r.REGOLE], [1, 2, 3, 4, 5, 6])
		self.assertEqual(len(r.PER_VALORE), 6)


class PianoTest(UnitTestCase):
	"""The clinic is a module of the plan, off unless the agency switches it on."""

	def setUp(self):
		from crm.clinica import registra
		from crm.permissions import catalogo

		self._isolato = livelli.registro_isolato()
		self._isolato.__enter__()
		catalogo.registra()
		registra()

	def tearDown(self):
		self._isolato.__exit__(None, None, None)

	def test_spenta_nessuno_vede_i_pazienti(self):
		self.assertNotIn("pazienti.vedi", livelli.calcola(["manager"], moduli={}))
		self.assertNotIn("pazienti.vedi", livelli.calcola([], agenzia=True, moduli={}))

	def test_accesa_li_vedono_segreteria_operatore_e_manager(self):
		accesa = {"clinica": livelli.ATTIVO}
		self.assertEqual(livelli.calcola(["segreteria"], moduli=accesa)["pazienti.vedi"], livelli.CENTRO)
		self.assertEqual(livelli.calcola(["operatore"], moduli=accesa)["pazienti.vedi"], livelli.SUOI)
		self.assertIn("pazienti.recupera", livelli.calcola(["manager"], moduli=accesa))

	def test_il_commerciale_non_sa_chi_e_paziente(self):
		self.assertNotIn(
			"pazienti.vedi", livelli.calcola(["commerciale"], moduli={"clinica": livelli.ATTIVO})
		)

	def test_l_agenzia_non_li_vede_senza_un_accesso_clinico(self):
		accesa = {"clinica": livelli.ATTIVO}
		self.assertNotIn("pazienti.vedi", livelli.calcola([], agenzia=True, moduli=accesa))
		self.assertIn("pazienti.vedi", livelli.calcola([], agenzia=True, accessi_clinici=True, moduli=accesa))
		# finding the patients is a job on the data, not a look at anybody's health
		self.assertIn("pazienti.recupera", livelli.calcola([], agenzia=True, moduli=accesa))
