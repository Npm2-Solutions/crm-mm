# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The teeth without a site: the FDI notation and the surfaces, the chart, the teeth
on a quote's rows (its sums are the CRM's: `crm/preventivi/tests/test_regole.py`)."""

from __future__ import annotations

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the rules are still testable
	from unittest import TestCase as UnitTestCase

from crm.clinica import cure_regole as R


class IDenti(UnitTestCase):
	def test_la_notazione_fdi(self):
		for dente in (11, 18, 21, 28, 31, 38, 41, 48, 51, 55, 65, 71, 85, "36"):
			self.assertTrue(R.e_dente(dente), dente)
		for dente in (10, 19, 56, 91, 9, "3a", None, ""):
			self.assertFalse(R.e_dente(dente), dente)
		self.assertTrue(R.deciduo(75))
		self.assertTrue(R.superiore(26) and R.superiore(55))
		self.assertFalse(R.superiore(36))
		self.assertTrue(R.anteriore(13) and not R.anteriore(14))

	def test_le_arcate_come_le_disegna_il_dentista(self):
		sopra, sotto = R.arcate()
		self.assertEqual(sopra[:3] + sopra[-3:], [18, 17, 16, 26, 27, 28])
		self.assertEqual(sopra[7:9], [11, 21])
		self.assertEqual(sotto[7:9], [41, 31])
		self.assertEqual(len(sopra) + len(sotto), 32)
		self.assertEqual(R.arcate(R.DECIDUA)[0], [55, 54, 53, 52, 51, 61, 62, 63, 64, 65])
		self.assertEqual([len(riga) for riga in R.arcate(R.MISTA)], [16, 10, 10, 16])

	def test_le_superfici(self):
		self.assertEqual(R.superfici("dom"), "MOD")
		self.assertEqual(R.superfici("b, p"), "VL")
		self.assertEqual(R.superfici("I"), "O")
		self.assertEqual(R.superfici(""), "")
		self.assertIsNone(R.superfici("MX"))


class LoStato(UnitTestCase):
	def test_una_riga_per_dente_e_condizione(self):
		righe = R.pulisci_stato(
			[
				{"tooth": "36", "condition": R.CARIE, "surfaces": "o"},
				{"tooth": 36, "condition": R.CARIE, "surfaces": "M", "note": "profonda"},
				{"tooth": "16", "condition": R.CORONA, "surfaces": "MOD"},
				{"tooth": "99", "condition": R.CARIE},
				{"tooth": "11", "condition": "Unicorn"},
			]
		)
		self.assertEqual(
			righe,
			[
				{"tooth": "16", "condition": R.CORONA, "surfaces": "", "note": ""},
				{"tooth": "36", "condition": R.CARIE, "surfaces": "MO", "note": "profonda"},
			],
		)

	def test_cosa_non_va(self):
		problemi = R.valida_stato(
			[
				{"tooth": "46", "condition": R.MANCANTE},
				{"tooth": "46", "condition": R.CARIE, "surfaces": "O"},
				{"tooth": "37", "condition": R.OTTURAZIONE, "surfaces": "MX"},
				{"tooth": "19", "condition": R.CARIE},
				{"tooth": "26", "condition": R.DEVITALIZZATO},
				{"tooth": "26", "condition": R.CORONA},
			]
		)
		self.assertEqual(
			[p.testo() for p in problemi],
			[
				"Tooth 37: MX are not surfaces",
				"19 is not a tooth",
				"Tooth 46 is missing: nothing else goes on it",
			],
		)


def voce(servizio="Otturazione", **altro):
	return {"service": servizio, **altro}


class SuUnPreventivo(UnitTestCase):
	def test_i_denti_delle_righe(self):
		self.assertEqual(R.valida_denti([voce(tooth="36", surfaces="MOD"), voce()]), [])
		problemi = R.valida_denti(
			[voce(tooth="36"), voce(tooth="19"), voce(surfaces="O"), voce(tooth="46", surfaces="X")]
		)
		self.assertEqual(
			[p.testo() for p in problemi],
			[
				"Row 2: 19 is not a tooth",
				"Row 3: surfaces go with a tooth, as M, O, D, V, L",
				"Row 4: surfaces go with a tooth, as M, O, D, V, L",
			],
		)
