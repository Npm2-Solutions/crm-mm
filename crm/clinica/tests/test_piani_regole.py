# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The clinic's plans, without a site: who writes its kinds, what goes in them, the
nutrients from the tables, the recipes, the shopping list. The engine's own rules
are `crm/piani/tests/test_regole.py`'s."""

from __future__ import annotations

import datetime
import json
import pathlib

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the rules are still testable
	from unittest import TestCase as UnitTestCase

from crm.clinica import piani_regole as p
from crm.piani import regole as r

LUNEDI = datetime.date(2026, 9, 28)
#: The cases the browser proves too (`frontend/tests/unit/piani.test.js`).
CASI = json.loads((pathlib.Path(__file__).parent / "casi_nutrienti.json").read_text())


def momento(key="colazione", label="Colazione", day=r.OGNI_GIORNO):
	return {"key": key, "label": label, "day": day}


class ChiScrive(UnitTestCase):
	def test_la_dieta_al_medico_al_biologo_e_al_dietista(self):
		for qualifica in ("medico_chirurgo", "biologo", "dietista"):
			self.assertIn(p.MENU, r.tipi_per(qualifica))
			self.assertIn(p.SCAMBI, r.tipi_per(qualifica))

	def test_il_trainer_allena_e_non_da_diete(self):
		# a personal trainer has no healthcare qualification, or one of its own
		for qualifica in (None, "chinesiologo", "consulente"):
			self.assertEqual(r.tipi_per(qualifica), [r.ALLENAMENTO, r.ABITUDINI])

	def test_la_riabilitazione_al_fisioterapista_e_al_medico(self):
		self.assertIn(p.ESERCIZI, r.tipi_per("fisioterapista"))
		self.assertNotIn(p.MENU, r.tipi_per("fisioterapista"))
		self.assertEqual(
			r.tipi_per("medico_chirurgo"), [p.MENU, p.SCAMBI, r.ALLENAMENTO, p.ESERCIZI, r.ABITUDINI]
		)
		self.assertNotIn(p.ESERCIZI, r.tipi_per("osteopata"))

	def test_i_tipi_della_clinica_sono_dati_sanitari_accesi_con_la_clinica(self):
		for chiave in p.TIPI:
			tipo = r.tipo(chiave)
			self.assertTrue(tipo.clinico)
			self.assertEqual(tipo.modulo, "clinica")
		self.assertIn("shopping", r.tipo(p.SCAMBI).funzioni)
		self.assertIn("targets", r.tipo(p.MENU).funzioni)
		self.assertNotIn("targets", r.tipo(p.SCAMBI).funzioni)


class LeRighe(UnitTestCase):
	def test_un_menu_in_regola(self):
		voci = [
			{"moment": "colazione", "kind": p.CIBO, "food": "yogurt"},
			{"moment": "colazione", "kind": r.ABITUDINE, "text": "Un bicchiere d'acqua"},
		]
		self.assertEqual(r.valida(p.MENU, [momento()], voci), [])

	def test_ogni_genere_con_quello_che_gli_serve(self):
		voci = [
			{"moment": "colazione", "kind": p.CIBO},
			{"moment": "colazione", "kind": p.GRUPPO, "food_group": "Cereals", "portions": 0},
			{"moment": "colazione", "kind": r.ABITUDINE, "text": "  "},
		]
		messaggi = [problema.messaggio for problema in r.valida(p.SCAMBI, [momento()], voci)]
		self.assertEqual(
			messaggi, ["Choose the food", "A food group comes with its portions", "Write the habit"]
		)

	def test_un_piano_tiene_solo_i_suoi_generi(self):
		[problema] = r.valida(
			r.ALLENAMENTO, [momento()], [{"moment": "colazione", "kind": p.CIBO, "food": "x"}]
		)
		self.assertEqual(problema.testo(), "A plan of this kind does not hold Food")


class LeCalorie(UnitTestCase):
	def test_le_calorie_dalla_tabella(self):
		self.assertEqual(p.calorie(360, 80), 288)
		self.assertIsNone(p.calorie(None, 80))


class INutrienti(UnitTestCase):
	"""The totals come from the tables, the same in the browser and here."""

	def test_i_casi_condivisi(self):
		for caso in CASI["nutrients"]:
			with self.subTest(caso["name"]):
				self.assertEqual(p.nutrienti(caso["items"], CASI["foods"]), caso["expected"])
		for caso in CASI["days"]:
			with self.subTest(caso["name"]):
				self.assertEqual(
					p.per_giorno(caso["moments"], caso["items"], CASI["foods"]), caso["expected"]
				)
		for grammi, atteso in CASI["grams"]:
			with self.subTest(grammi=grammi):
				self.assertEqual(p.arrotonda_grammi(grammi), atteso)

	def test_scalare_tiene_le_proporzioni(self):
		voci = [
			{"kind": p.CIBO, "food": "pasta", "quantity_g": 80},
			{"kind": p.CIBO, "food": "piselli", "quantity_g": 100},
			{"kind": r.ABITUDINE, "text": "Acqua"},
		]
		scalate = p.scala(voci, CASI["foods"], 538)
		# 358 kcal become about 538: one and a half, in grams a person weighs
		self.assertEqual([v.get("quantity_g") for v in scalate], [120, 150, None])
		self.assertEqual(p.nutrienti(scalate, CASI["foods"])["kcal"], 538)
		self.assertEqual(voci[0]["quantity_g"], 80)

	def test_senza_obiettivo_o_senza_calorie_non_si_scala(self):
		voci = [{"kind": p.CIBO, "food": "pasta", "quantity_g": 80}]
		self.assertEqual(p.scala(voci, CASI["foods"], None), voci)
		self.assertEqual(p.scala(voci, CASI["foods"], "0"), voci)
		self.assertEqual(
			p.scala([{"kind": p.CIBO, "food": "senza_valori", "quantity_g": 5}], CASI["foods"], 500)[0][
				"quantity_g"
			],
			5,
		)


class LaRicettaProposta(UnitTestCase):
	"""Of a recipe the assistant proposed the engine keeps the foods of the library
	and their grams: nothing else of its numbers."""

	def test_solo_alimenti_della_libreria_e_grammi_leggibili(self):
		proposta = {
			"title": " Pasta e piselli ",
			"method": "Cuoci i piselli, poi la pasta.",
			"kcal": 9999,
			"foods": [
				{"id": "pasta", "grams": 78},
				{"id": "piselli", "grams": "100"},
				{"id": "burro", "grams": 20},
				{"id": "olio", "grams": 0},
				{"id": "olio", "grams": 5000},
				{"id": "pasta", "grams": 2},
				"sale",
			],
		}
		self.assertEqual(
			p.ricetta(proposta, CASI["foods"]),
			{
				"title": "Pasta e piselli",
				"method": "Cuoci i piselli, poi la pasta.",
				"items": [
					{"kind": p.CIBO, "food": "pasta", "quantity_g": 80},
					{"kind": p.CIBO, "food": "piselli", "quantity_g": 100},
				],
			},
		)

	def test_senza_titolo_o_senza_alimenti_non_c_e_ricetta(self):
		self.assertIsNone(
			p.ricetta({"title": "Niente", "foods": [{"id": "burro", "grams": 20}]}, CASI["foods"])
		)
		self.assertIsNone(p.ricetta({"foods": [{"id": "pasta", "grams": 80}]}, CASI["foods"]))
		self.assertIsNone(p.ricetta("pasta", CASI["foods"]))


SPESA_CIBI = {
	"latte": {"food_name": "Latte parzialmente scremato", "food_group": "Milk and dairy"},
	"pasta": {"food_name": "Pasta di semola", "food_group": "Cereals and tubers"},
	"merluzzo": {"food_name": "Merluzzo", "food_group": "Fish"},
	"olio": {"food_name": "Olio extravergine", "food_group": "Oils and fats"},
}


class LaSpesa(UnitTestCase):
	"""The shopping list: the menu's foods over the days to shop for, as many times
	a week as they are asked, and an exchange diet's portions by group."""

	def menu(self):
		momenti = [
			momento("colazione", "Colazione"),
			momento("pranzo", "Pranzo", day="Monday"),
			momento("cena", "Cena"),
		]
		voci = [
			{"key": "latte", "moment": "colazione", "kind": p.CIBO, "food": "latte", "quantity_g": 200},
			{"key": "pasta", "moment": "pranzo", "kind": p.CIBO, "food": "pasta", "quantity_g": "80"},
			# fish at dinner, but only twice a week
			{
				"key": "pesce",
				"moment": "cena",
				"kind": p.CIBO,
				"food": "merluzzo",
				"quantity_g": 150,
				"times_per_week": 2,
			},
			{"key": "olio", "moment": "cena", "kind": p.CIBO, "food": "olio"},
			{"key": "acqua", "moment": "cena", "kind": r.ABITUDINE, "text": "Acqua"},
		]
		return momenti, voci

	def test_una_settimana_da_lunedi(self):
		momenti, voci = self.menu()
		giorni = p.giorni_del_periodo(LUNEDI, 7)
		lista = p.spesa(momenti, voci, SPESA_CIBI, giorni)
		self.assertEqual(lista["days"], 7)
		self.assertEqual(
			[(r["food"], r["grams"], r["times"], r["each"]) for r in lista["foods"]],
			[
				("pasta", 80, 1, 80),
				("merluzzo", 300, 2, 150),
				("latte", 1400, 7, 200),
				# no grams: to buy all the same, without a number
				("olio", None, 7, None),
			],
		)
		self.assertEqual(lista["groups"], [])

	def test_le_volte_a_settimana_ricominciano_il_lunedi(self):
		momenti, voci = self.menu()
		# from Thursday for a week: two dinners of fish this week, two the next
		giorni = p.giorni_del_periodo(LUNEDI + datetime.timedelta(days=3), 7)
		pesce = next(
			r for r in p.spesa(momenti, voci, SPESA_CIBI, giorni)["foods"] if r["food"] == "merluzzo"
		)
		self.assertEqual((pesce["times"], pesce["grams"]), (4, 600))

	def test_solo_i_giorni_del_piano(self):
		giorni = p.giorni_del_periodo(LUNEDI, 14, fine=LUNEDI + datetime.timedelta(days=2))
		self.assertEqual(giorni, [LUNEDI + datetime.timedelta(days=n) for n in range(3)])
		self.assertEqual(len(p.giorni_del_periodo(LUNEDI, 90)), p.MAX_GIORNI_SPESA)
		self.assertEqual(p.giorni_del_periodo(LUNEDI, 7, inizio=LUNEDI + datetime.timedelta(days=10)), [])

	def test_quantita_diverse_non_hanno_un_ogni_volta(self):
		momenti = [momento("colazione", "Colazione"), momento("merenda", "Merenda")]
		voci = [
			{"key": "a", "moment": "colazione", "kind": p.CIBO, "food": "latte", "quantity_g": 200},
			{"key": "b", "moment": "merenda", "kind": p.CIBO, "food": "latte", "quantity_g": 125},
		]
		[latte] = p.spesa(momenti, voci, SPESA_CIBI, p.giorni_del_periodo(LUNEDI, 2))["foods"]
		self.assertEqual((latte["grams"], latte["times"], latte["each"]), (650, 4, None))

	def test_gli_scambi_per_gruppo(self):
		momenti = [momento("pranzo", "Pranzo")]
		voci = [
			{
				"key": "c",
				"moment": "pranzo",
				"kind": p.GRUPPO,
				"food_group": "Cereals and tubers",
				"portions": 1,
			},
			{
				"key": "f",
				"moment": "pranzo",
				"kind": p.GRUPPO,
				"food_group": "Fish",
				"portions": 1.5,
				"times_per_week": 3,
			},
		]
		lista = p.spesa(momenti, voci, {}, p.giorni_del_periodo(LUNEDI, 7))
		self.assertEqual(
			lista["groups"],
			[{"food_group": "Cereals and tubers", "portions": 7}, {"food_group": "Fish", "portions": 4.5}],
		)
		self.assertEqual(lista["foods"], [])
