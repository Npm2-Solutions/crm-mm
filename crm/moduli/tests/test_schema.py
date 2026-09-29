# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The form templates engine, proved without a site.

`casi_schema.json` holds the cases the browser has to agree on: the same file is
read by `frontend/tests/unit/moduli.test.js`, so the rules that decide what a
person sees while filling a form are the ones the server decides with.
"""

from __future__ import annotations

import copy
import json
import pathlib

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the engine is still fully testable
	from unittest import TestCase as UnitTestCase

from crm.moduli import schema as S

CASI = json.loads((pathlib.Path(__file__).parent / "casi_schema.json").read_text())


def _schema(caso):
	nome = caso["schema"]
	return copy.deepcopy(CASI["schemas"][nome] if isinstance(nome, str) else nome)


def _modulo(*campi, **sezione):
	return {"sections": [{"id": "s", "title": "S", **sezione, "fields": list(campi)}]}


class ICasiCondivisi(UnitTestCase):
	"""What the browser runs too."""

	def test_le_condizioni(self):
		for caso in CASI["conditions"]:
			with self.subTest(caso["name"]):
				self.assertEqual(S.soddisfatta(caso["groups"], caso["values"]), caso["expected"])

	def test_le_formule(self):
		for caso in CASI["formulas"]:
			with self.subTest(caso["formula"]):
				self.assertEqual(
					S.calcola(caso["formula"], caso["values"], caso.get("decimals")), caso["expected"]
				)

	def test_le_valutazioni(self):
		for caso in CASI["evaluations"]:
			with self.subTest(caso["name"]):
				self.assertEqual(S.valuta(_schema(caso), caso["values"]), caso["expected"])

	def test_le_validazioni(self):
		for caso in CASI["validations"]:
			with self.subTest(caso["name"]):
				self.assertEqual([e.codice for e in S.valida_schema(_schema(caso))], caso["expected"])


class LaPulizia(UnitTestCase):
	"""What is kept of the answers: server side only, on the way in."""

	def test_i_numeri_scritti_a_mano(self):
		modulo = _modulo({"id": "w", "type": "number", "label": "Weight", "decimals": 1})
		puliti, errori, _ = S.pulisci(modulo, {"w": "70,56"})
		self.assertEqual((puliti, errori), ({"w": 70.6}, []))
		puliti, _, _ = S.pulisci(modulo, {"w": 70.0})
		self.assertEqual(puliti, {"w": 70})

	def test_fuori_dai_limiti(self):
		modulo = _modulo({"id": "w", "type": "number", "label": "Weight", "min": 1, "max": 400})
		_, errori, _ = S.pulisci(modulo, {"w": 900})
		self.assertEqual([(e.codice, e.campo) for e in errori], [("above_max", "w")])
		self.assertEqual(errori[0].testo(), "Weight is at most 400")
		_, errori, _ = S.pulisci(modulo, {"w": "tanto"})
		self.assertEqual([e.codice for e in errori], ["not_a_number"])

	def test_le_scelte(self):
		modulo = _modulo(
			{
				"id": "a",
				"type": "choice",
				"label": "A",
				"multiple": True,
				"options": [{"label": "X"}, {"label": "Y"}],
			},
			{"id": "b", "type": "choice", "label": "B", "options": [{"label": "X"}]},
		)
		puliti, errori, _ = S.pulisci(modulo, {"a": ["Y", "X", "Y"], "b": "X"})
		self.assertEqual((puliti, errori), ({"a": ["X", "Y"], "b": "X"}, []))
		_, errori, _ = S.pulisci(modulo, {"a": ["Z"], "b": "Y"})
		self.assertEqual([e.codice for e in errori], ["invalid_option", "invalid_option"])

	def test_si_no_date_e_scale(self):
		modulo = _modulo(
			{"id": "y", "type": "yesno", "label": "Y"},
			{"id": "d", "type": "date", "label": "D"},
			{"id": "k", "type": "scale", "label": "K", "min": 0, "max": 10},
		)
		puliti, errori, _ = S.pulisci(modulo, {"y": "1", "d": "2026-02-28", "k": "7"})
		self.assertEqual((puliti, errori), ({"y": True, "d": "2026-02-28", "k": 7}, []))
		_, errori, _ = S.pulisci(modulo, {"y": "forse", "d": "2026-02-30", "k": 11})
		self.assertEqual([e.codice for e in errori], ["invalid_value", "invalid_value", "out_of_scale"])

	def test_tabelle_e_lati(self):
		modulo = _modulo(
			{
				"id": "t",
				"type": "table",
				"label": "T",
				"columns": [{"id": "name", "label": "Name"}, {"id": "mg", "label": "mg", "type": "number"}],
			},
			{"id": "k", "type": "sides", "label": "K"},
		)
		puliti, errori, _ = S.pulisci(
			modulo,
			{
				"t": [{"name": " Aspirin ", "mg": "100", "extra": "x"}, {"name": "", "mg": None}],
				"k": {"left": "120", "right": None, "up": 3},
			},
		)
		self.assertEqual(errori, [])
		self.assertEqual(puliti, {"t": [{"name": "Aspirin", "mg": 100}], "k": {"left": 120}})

	def test_le_risposte_nascoste_e_quelle_sconosciute_non_restano(self):
		modulo = _modulo(
			{"id": "smoker", "type": "yesno", "label": "Smoker"},
			{
				"id": "many",
				"type": "number",
				"label": "How many",
				"show_if": [[{"field": "smoker", "operator": "equals", "value": "1"}]],
			},
		)
		# a wrong answer to a hidden question is not an error: it is not asked
		puliti, errori, _ = S.pulisci(modulo, {"smoker": False, "many": "tante", "who": "me"})
		self.assertEqual((puliti, errori), ({"smoker": False}, []))

	def test_i_calcoli_sono_del_server(self):
		modulo = _modulo(
			{"id": "a", "type": "number", "label": "A"},
			{"id": "c", "type": "calc", "label": "C", "formula": "a * 2"},
		)
		# what the browser sent for a calculation is not taken: it is worked out
		puliti, _, _ = S.pulisci(modulo, {"a": 4, "c": 1000})
		self.assertEqual(puliti, {"a": 4, "c": 8})

	def test_una_riga_sola_non_va_a_capo(self):
		modulo = _modulo(
			{"id": "a", "type": "text", "label": "A"},
			{"id": "b", "type": "text", "label": "B", "multiline": True},
		)
		puliti, _, _ = S.pulisci(modulo, {"a": " Mario \n Rossi ", "b": " riga 1\nriga 2 "})
		self.assertEqual(puliti, {"a": "Mario Rossi", "b": "riga 1\nriga 2"})


class LaVersione(UnitTestCase):
	def test_normalizza_toglie_gli_avanzi(self):
		modulo = _modulo(
			{
				"id": "a",
				"type": "text",
				"label": "A",
				"required": False,
				"description": "",
				# left over from when it was a choice
				"options": [{"label": "X"}],
				"show_if": [[{"field": "", "operator": "equals", "value": ""}]],
			},
			{
				"id": "k",
				"type": "scale",
				"label": "K",
				"min": 0,
				"max": 5,
				"stop_if": [[{"field": "k", "operator": "greater_than", "value": "4", "ui": 1}], []],
			},
		)
		self.assertEqual(
			S.normalizza(modulo)["sections"][0]["fields"],
			[
				{"id": "a", "type": "text", "label": "A"},
				{
					"id": "k",
					"type": "scale",
					"label": "K",
					"stop_if": [[{"field": "k", "operator": "greater_than", "value": "4"}]],
					"min": 0,
					"max": 5,
				},
			],
		)

	def test_l_impronta(self):
		uno = {"sections": [{"id": "s", "title": "S", "fields": [{"id": "a", "type": "text", "label": "A"}]}]}
		due = {"sections": [{"fields": [{"label": "A", "type": "text", "id": "a"}], "title": "S", "id": "s"}]}
		self.assertEqual(S.impronta(uno), S.impronta(due))
		self.assertEqual(len(S.impronta(uno)), 64)
		due["sections"][0]["fields"][0]["label"] = "A."
		self.assertNotEqual(S.impronta(uno), S.impronta(due))

	def test_si_pubblica_quando_chiede_qualcosa(self):
		solo_testo = _modulo({"id": "p", "type": "paragraph", "text": "Hello"})
		self.assertEqual(S.valida_schema(solo_testo), [])
		self.assertEqual([e.codice for e in S.pronto_da_pubblicare(solo_testo)], ["empty"])
		self.assertEqual(S.pronto_da_pubblicare(_schema({"schema": "consents"})), [])


class IComponentiDiAltri(UnitTestCase):
	def setUp(self):
		S.registra_componente(
			S.Componente(
				"test_bodymap", "Body map", "points", condizione=S.SOLO_PRESENZA, proprieta=("view",)
			)
		)
		self.addCleanup(S._componenti.pop, "test_bodymap", None)

	def test_un_componente_registrato_vale_come_gli_altri(self):
		modulo = _modulo(
			{"id": "map", "type": "test_bodymap", "label": "Where it hurts", "view": "front", "other": 1},
			{
				"id": "a",
				"type": "text",
				"label": "A",
				"show_if": [[{"field": "map", "operator": "is_set"}]],
			},
		)
		self.assertEqual(S.valida_schema(modulo), [])
		self.assertEqual(
			S.normalizza(modulo)["sections"][0]["fields"][0],
			{"id": "map", "type": "test_bodymap", "label": "Where it hurts", "view": "front"},
		)
		# its answer is its module's to check: kept as it came
		puliti, _, stato = S.pulisci(modulo, {"map": [{"x": 1, "y": 2}]})
		self.assertEqual(puliti, {"map": [{"x": 1, "y": 2}]})
		self.assertTrue(stato["visible"]["a"])
