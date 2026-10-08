# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The clinical sheets DottorCloud ships, without a site: each one ready to
publish in both languages, every word in Italian, the physiotherapist's with the
body chart."""

from __future__ import annotations

import json
from pathlib import Path

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the sheets are still fully testable
	from unittest import TestCase as UnitTestCase

from crm.clinica import schede_pronte_regole as R
from crm.moduli import schema as S

FILE = Path(__file__).parent.parent / "dati" / "schede_pronte.json"
DATI = json.loads(FILE.read_text(encoding="utf-8"))
#: the clinic registers "summary" as a property every field may carry
S.registra_proprieta_comune("summary")


class LeSchedePronte(UnitTestCase):
	def test_ci_sono_tutte(self):
		self.assertEqual(
			[s["key"] for s in DATI["sheets"]],
			[
				"physio_assessment",
				"physio_followup",
				"nutrition_first",
				"nutrition_followup",
				"dental_first",
				"general_history",
			],
		)

	def test_si_possono_pubblicare_in_tutte_e_due_le_lingue(self):
		for scheda in DATI["sheets"]:
			for lingua in ("en", "it"):
				with self.subTest(scheda["key"], lingua=lingua):
					tradotta = R.nella_lingua(scheda, DATI["words"], lingua)
					errori = S.pronto_da_pubblicare(S.normalizza(tradotta["schema"]))
					self.assertEqual([e.testo() for e in errori], [])

	def test_ogni_parola_ha_il_suo_italiano(self):
		italiano = DATI["words"]["it"]
		mancanti = {
			parola for scheda in DATI["sheets"] for parola in R.parole(scheda) if parola not in italiano
		}
		self.assertEqual(mancanti, set())
		# and nothing in the dictionary that no sheet says
		dette = {parola for scheda in DATI["sheets"] for parola in R.parole(scheda)}
		self.assertEqual(set(italiano) - dette, set())

	def test_una_condizione_segue_la_sua_opzione(self):
		visita = next(s for s in DATI["sheets"] if s["key"] == "physio_assessment")
		italiana = R.nella_lingua(visita, DATI["words"], "it")
		stato = S.valuta(italiana["schema"], {"neuro": "Con alterazioni"})
		self.assertTrue(stato["visible"]["neuro_notes"])
		self.assertEqual(italiana["title"], "Valutazione fisioterapica")
		self.assertEqual(italiana["specialty"], "Fisioterapia")

	def test_la_fisioterapia_segna_dove_fa_male(self):
		for chiave in ("physio_assessment", "physio_followup"):
			scheda = next(s for s in DATI["sheets"] if s["key"] == chiave)
			tipi = [c["type"] for c in S.campi(scheda["schema"])]
			self.assertIn("body_chart", tipi)
			# daily life adds up, and is followed over time
			self.assertIn("score", tipi)

	def test_un_segnale_d_allarme_ferma_la_seduta(self):
		visita = next(s for s in DATI["sheets"] if s["key"] == "physio_assessment")
		stato = S.valuta(visita["schema"], {"rf_saddle": True})
		self.assertEqual([f["field"] for f in stato["stops"]], ["rf_saddle"])

	def test_la_vita_di_ogni_giorno_si_somma(self):
		visita = next(s for s in DATI["sheets"] if s["key"] == "physio_followup")
		risposte = {
			chiave: 3
			for chiave in (
				"f_walk",
				"f_sit",
				"f_stand",
				"f_sleep",
				"f_lift",
				"f_dress",
				"f_work",
				"f_leisure",
			)
		}
		stato = S.valuta(visita["schema"], risposte)
		self.assertEqual((stato["values"]["difficulty"], stato["bands"]["difficulty"]), (24, "Moderate"))

	def test_nessuna_scala_validata(self):
		# their own questions: no validated scale's name in any language
		testo = FILE.read_text(encoding="utf-8").lower()
		for nome in ("oswestry", "neck disability", "roland", "womac", "dash", "koos", "phq", "gad-7", "mna"):
			self.assertNotIn(nome, testo)

	def test_l_impronta(self):
		scheda = DATI["sheets"][0]
		prima = R.impronta(scheda["title"], scheda["description"], scheda["specialty"], scheda["schema"])
		# the same words, written in another order: the same template
		rigirato = json.loads(json.dumps(scheda["schema"], sort_keys=True))
		self.assertEqual(
			prima, R.impronta(scheda["title"], scheda["description"], scheda["specialty"], rigirato)
		)
		cambiato = json.loads(json.dumps(scheda["schema"]))
		cambiato["sections"][0]["title"] = "Altro"
		self.assertNotEqual(
			prima, R.impronta(scheda["title"], scheda["description"], scheda["specialty"], cambiato)
		)
		self.assertNotEqual(
			prima, R.impronta("Altro", scheda["description"], scheda["specialty"], scheda["schema"])
		)

	def test_una_parola_senza_traduzione_resta(self):
		scheda = {"title": "Mai vista", "schema": {"sections": []}}
		self.assertEqual(R.nella_lingua(scheda, DATI["words"], "it")["title"], "Mai vista")
		self.assertEqual(R.nella_lingua(DATI["sheets"][0], DATI["words"], "en"), DATI["sheets"][0])
