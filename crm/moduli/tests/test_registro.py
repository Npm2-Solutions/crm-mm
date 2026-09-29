# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The consent register's rules, without a site."""

from __future__ import annotations

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the rules are still testable
	from unittest import TestCase as UnitTestCase

from crm.moduli import registro as r


def risposta(stato, quando, creata="2026-01-01 00:00:00"):
	return {"status": stato, "answered_on": quando, "creation": creata}


class StatoTest(UnitTestCase):
	def test_mai_chiesto(self):
		self.assertIsNone(r.stato_attuale([]))

	def test_conta_l_ultima_risposta(self):
		righe = [risposta(r.DATO, "2026-01-10 09:00:00"), risposta(r.RIFIUTATO, "2026-03-01 09:00:00")]
		self.assertEqual(r.stato_attuale(righe)["status"], r.RIFIUTATO)

	def test_una_revoca_resta_l_ultima_finche_non_si_risponde_di_nuovo(self):
		"""A withdrawal stamps the row that gave the consent: it does not move it."""
		revocato = risposta(r.REVOCATO, "2026-01-10 09:00:00")
		self.assertEqual(r.stato_attuale([revocato])["status"], r.REVOCATO)
		di_nuovo = risposta(r.DATO, "2026-05-01 09:00:00")
		self.assertEqual(r.stato_attuale([revocato, di_nuovo])["status"], r.DATO)

	def test_nello_stesso_istante_vale_la_riga_scritta_dopo(self):
		prima = risposta(r.DATO, "2026-01-10 09:00:00", "2026-01-10 09:00:00.1")
		dopo = risposta(r.RIFIUTATO, "2026-01-10 09:00:00", "2026-01-10 09:00:00.2")
		self.assertEqual(r.stato_attuale([dopo, prima])["status"], r.RIFIUTATO)


class RevocaTest(UnitTestCase):
	def test_si_revoca_solo_un_consenso_dato(self):
		self.assertTrue(r.puo_revocare({"status": r.DATO}, r.CONSENSO))
		self.assertFalse(r.puo_revocare({"status": r.RIFIUTATO}, r.CONSENSO))
		self.assertFalse(r.puo_revocare({"status": r.REVOCATO}, r.CONSENSO))
		self.assertFalse(r.puo_revocare(None, r.CONSENSO))

	def test_una_presa_visione_non_si_revoca(self):
		"""An information read is not taken back: there is nothing to withdraw."""
		self.assertFalse(r.puo_revocare({"status": r.DATO}, r.PRESA_VISIONE))


class TipiTest(UnitTestCase):
	def test_il_testo_nella_lingua_del_sito(self):
		tipo = r.TipoConsenso("prova", "Prova", testi={"it": "Acconsento", "en": "I agree"})
		self.assertEqual(r.testo_per_lingua(tipo, "en-GB"), "I agree")
		self.assertEqual(r.testo_per_lingua(tipo, "de"), "Acconsento")
		self.assertEqual(r.testo_per_lingua(tipo, None), "Acconsento")

	def test_una_natura_che_non_esiste_non_si_registra(self):
		with self.assertRaises(ValueError):
			r.registra_tipo(r.TipoConsenso("prova", "Prova", natura="Maybe"))

	def test_i_canali_a_mano_sono_canali(self):
		self.assertTrue(set(r.CANALI_A_MANO) <= set(r.CANALI))
