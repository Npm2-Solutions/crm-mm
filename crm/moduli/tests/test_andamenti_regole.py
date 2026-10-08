# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A questionnaire's totals over time, without a site."""

from __future__ import annotations

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the rules are still fully testable
	from unittest import TestCase as UnitTestCase

from crm.moduli import andamenti_regole as A

DOLORE = {
	"sections": [
		{
			"id": "s",
			"fields": [
				{"id": "a", "type": "scale", "label": "Rest", "min": 0, "max": 10},
				{"id": "b", "type": "scale", "label": "Moving", "min": 0, "max": 10},
				{
					"id": "totale",
					"type": "score",
					"label": "Pain",
					"sources": ["a", "b"],
					"bands": [
						{"from": 0, "to": 6, "label": "Mild"},
						{"from": 7, "to": 20, "label": "Strong"},
					],
				},
			],
		}
	]
}


def compilato(nome, data, a, b, template="T1", schema=DOLORE, titolo="Pain diary"):
	return {
		"name": nome,
		"template": template,
		"title": titolo,
		"date": data,
		"schema": schema,
		"answers": {"a": a, "b": b},
	}


class LAndamento(UnitTestCase):
	def test_i_totali_in_ordine_di_data(self):
		serie = A.serie([compilato("F2", "2026-09-20", 2, 3), compilato("F1", "2026-08-01", 6, 6)])
		self.assertEqual(len(serie), 1)
		voce = serie[0]
		self.assertEqual((voce["title"], voce["label"], voce["field"]), ("Pain diary", "Pain", "totale"))
		self.assertEqual([p["value"] for p in voce["points"]], [12, 5])
		self.assertEqual([p["band"] for p in voce["points"]], ["Strong", "Mild"])
		self.assertEqual([p["name"] for p in voce["points"]], ["F1", "F2"])
		self.assertEqual(voce["bands"][1], {"from": 7, "to": 20, "label": "Strong"})

	def test_un_totale_che_manca_non_e_un_punto(self):
		# a question it counts left unanswered: no total, no point
		serie = A.serie([compilato("F1", "2026-08-01", 6, None), compilato("F2", "2026-09-01", 1, 1)])
		self.assertEqual([p["name"] for p in serie[0]["points"]], ["F2"])

	def test_un_modulo_senza_punteggio_non_ha_serie(self):
		senza = {"sections": [{"id": "s", "fields": [{"id": "n", "type": "text", "label": "Notes"}]}]}
		self.assertEqual(A.serie([compilato("F1", "2026-08-01", 1, 1, schema=senza)]), [])

	def test_ogni_modello_la_sua(self):
		serie = A.serie(
			[
				compilato("F1", "2026-08-01", 1, 1, template="T2", titolo="Back"),
				compilato("F2", "2026-08-02", 1, 2),
			]
		)
		self.assertEqual([v["title"] for v in serie], ["Back", "Pain diary"])

	def test_le_parole_della_versione_piu_nuova(self):
		nuova = {
			"sections": [
				{
					"id": "s",
					"fields": [
						*DOLORE["sections"][0]["fields"][:2],
						{**DOLORE["sections"][0]["fields"][2], "label": "Pain today", "bands": []},
					],
				}
			]
		}
		serie = A.serie(
			[compilato("F1", "2026-08-01", 1, 1), compilato("F2", "2026-09-01", 1, 1, schema=nuova)]
		)
		self.assertEqual(serie[0]["label"], "Pain today")
		self.assertEqual(serie[0]["bands"], [])
		# each point keeps the band it had when it was signed
		self.assertEqual([p["band"] for p in serie[0]["points"]], ["Mild", None])

	def test_un_totale_nascosto_non_conta(self):
		nascosto = {
			"sections": [
				{
					"id": "s",
					"fields": [
						{"id": "c", "type": "yesno", "label": "Pain?"},
						*[
							{**f, "show_if": [[{"field": "c", "operator": "equals", "value": "1"}]]}
							for f in DOLORE["sections"][0]["fields"]
						],
					],
				}
			]
		}
		punti = A.punteggi(nascosto, {"c": False, "a": 3, "b": 3})
		self.assertEqual(punti, [])
		self.assertEqual(A.punteggi(nascosto, {"c": True, "a": 3, "b": 3})[0]["value"], 6)
