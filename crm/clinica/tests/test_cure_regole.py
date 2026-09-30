# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Dental care plans, without a site: the teeth and their surfaces, the chart, the
sums of a quote, and which treatment an appointment takes."""

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


def voce(servizio="Otturazione", fase=1, stato=R.DA_FARE, qty=1, rate=100, sconto=0, **altro):
	return {
		"service": servizio,
		"phase": fase,
		"status": stato,
		"qty": qty,
		"rate": rate,
		"discount": sconto,
		**altro,
	}


class IlPiano(UnitTestCase):
	def test_i_passaggi(self):
		self.assertTrue(R.si_passa(R.BOZZA, R.PROPOSTO))
		self.assertTrue(R.si_passa(R.PROPOSTO, R.BOZZA))
		self.assertTrue(R.si_passa(R.PROPOSTO, R.ACCETTATO))
		self.assertFalse(R.si_passa(R.BOZZA, R.ACCETTATO))
		self.assertFalse(R.si_passa(R.RIFIUTATO, R.ACCETTATO))
		self.assertTrue(R.si_passa(R.ACCETTATO, R.CHIUSO))

	def test_le_somme(self):
		self.assertEqual(R.importo(2, 80, 10), 144)
		self.assertEqual(R.importo(1, 99.99, 33), 66.99)
		voci = [
			voce(rate=100, sconto=10, stato=R.FATTA),
			voce("Impianto", 2, qty=1, rate=1200),
			voce("Igiene", 1, rate=70, stato=R.ANNULLATA),
		]
		self.assertEqual(
			R.totali(voci), {"gross": 1300, "discount": 10, "net": 1290, "done": 90, "left": 1200}
		)

	def test_l_appuntamento_prende_la_prima_da_fare_nell_ordine_delle_fasi(self):
		voci = [
			voce("Impianto", 3),
			voce("Otturazione", 2, tooth="36"),
			voce("Otturazione", 1, tooth="46", stato=R.FATTA),
			voce("Otturazione", 1, tooth="26"),
		]
		self.assertEqual(R.voce_per(voci, "Otturazione"), 3)
		voci[3]["status"] = R.PRENOTATA
		self.assertEqual(R.voce_per(voci, "Otturazione"), 1)
		self.assertIsNone(R.voce_per(voci, "Igiene"))

	def test_completato(self):
		self.assertFalse(R.completato([voce(stato=R.FATTA), voce()]))
		self.assertTrue(R.completato([voce(stato=R.FATTA), voce(stato=R.ANNULLATA)]))
		self.assertFalse(R.completato([voce(stato=R.ANNULLATA)]))

	def test_prima_di_proporlo(self):
		self.assertEqual([p.testo() for p in R.valida_piano([])], ["A plan has at least one treatment"])
		problemi = R.valida_piano(
			[
				voce(tooth="36", surfaces="MOD"),
				voce(servizio="", tooth="19"),
				voce(surfaces="O"),
				voce(qty=0, sconto=120),
			]
		)
		self.assertEqual(
			[p.testo() for p in problemi],
			[
				"Treatment 2: choose the service",
				"Treatment 2: 19 is not a tooth",
				"Treatment 3: surfaces go with a tooth, as M, O, D, V, L",
				"Treatment 4: the quantity is more than zero",
				"Treatment 4: the discount is from 0 to 100%",
			],
		)
