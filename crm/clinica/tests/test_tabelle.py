# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The food tables as the clinic's library reads them, without a site: the columns
by their names in Italian, French and English, the numbers as the tables write
them, the categories into the library's groups, the energy a table leaves out. The
exercises dataset is the CRM's (`crm/piani/tests/test_dataset.py`)."""

from __future__ import annotations

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the tables are still readable
	from unittest import TestCase as UnitTestCase

from crm.clinica import tabelle as T

CIQUAL_EN = [
	"alim_grp_code",
	"alim_ssgrp_code",
	"alim_ssssgrp_code",
	"alim_grp_nom_eng",
	"alim_ssgrp_nom_eng",
	"alim_ssssgrp_nom_eng",
	"alim_code",
	"alim_nom_eng",
	"alim_nom_sci",
	"Energy, Regulation EU No 1169/2011 (kJ/100g)",
	"Energy, Regulation EU No 1169/2011 (kcal/100g)",
	"Energy, N x Jones' factor, with fibres (kcal/100g)",
	"Water (g/100g)",
	"Protein (g/100g)",
	"Protein, crude, N x 6.25 (g/100g)",
	"Carbohydrate (g/100g)",
	"Fat (g/100g)",
	"Sugars (g/100g)",
	"Fibres (g/100g)",
	"Alcohol (g/100g)",
	"FA saturated (g/100g)",
]
CIQUAL_FR = [
	"alim_grp_nom_fr",
	"alim_ssgrp_nom_fr",
	"alim_code",
	"alim_nom_fr",
	"Energie, Règlement UE N° 1169/2011 (kcal/100 g)",
	"Protéines, N x facteur de Jones (g/100 g)",
	"Protéines, N x 6.25 (g/100 g)",
	"Glucides (g/100 g)",
	"Lipides (g/100 g)",
	"Fibres alimentaires (g/100 g)",
	"AG saturés (g/100 g)",
]
ITALIANA = [
	"Codice",
	"Nome",
	"Categoria",
	"Energia (kcal)",
	"Energia (kJ)",
	"Proteine totali (g)",
	"Proteine animali (g)",
	"Lipidi totali (g)",
	"Lipidi vegetali (g)",
	"Carboidrati disponibili (g)",
	"Fibra alimentare totale (g)",
]


def colonna(intestazioni, mappa, campo):
	indice = mappa[campo]
	if isinstance(indice, list):
		return [intestazioni[i] for i in indice]
	return intestazioni[indice]


class INumeri(UnitTestCase):
	def test_come_li_scrivono_le_tabelle(self):
		for scritto, letto in (
			("4,63", 4.63),
			("12.5", 12.5),
			(" 290 ", 290.0),
			("1.234,5", 1234.5),
			("1,234.5", 1234.5),
			(36, 36.0),
			(0.53, 0.53),
		):
			self.assertEqual(T.numero(scritto), letto, scritto)

	def test_non_saputo_non_conta_le_tracce_sono_zero(self):
		for scritto in ("-", "", None, "n.d.", "ND", "?", True, -3, "-2", "abc"):
			self.assertIsNone(T.numero(scritto), scritto)
		for scritto in ("traces", "tracce", "tr", "< 0,15", "<0.5"):
			self.assertEqual(T.numero(scritto), 0.0, scritto)


class LeColonne(UnitTestCase):
	def test_ciqual_in_inglese(self):
		mappa = T.riconosci(CIQUAL_EN)
		self.assertEqual(colonna(CIQUAL_EN, mappa, "code"), "alim_code")
		self.assertEqual(colonna(CIQUAL_EN, mappa, "name"), "alim_nom_eng")
		# the sub-group first: "vegetables" says more than "fruits, vegetables…"
		self.assertEqual(colonna(CIQUAL_EN, mappa, "group"), ["alim_ssgrp_nom_eng", "alim_grp_nom_eng"])
		self.assertEqual(colonna(CIQUAL_EN, mappa, "kcal"), "Energy, Regulation EU No 1169/2011 (kcal/100g)")
		self.assertEqual(colonna(CIQUAL_EN, mappa, "protein_g"), "Protein (g/100g)")
		self.assertEqual(colonna(CIQUAL_EN, mappa, "carbs_g"), "Carbohydrate (g/100g)")
		self.assertEqual(colonna(CIQUAL_EN, mappa, "fat_g"), "Fat (g/100g)")
		self.assertEqual(colonna(CIQUAL_EN, mappa, "fibre_g"), "Fibres (g/100g)")
		self.assertEqual(colonna(CIQUAL_EN, mappa, "alcohol_g"), "Alcohol (g/100g)")
		self.assertEqual((T.lingua_delle_colonne(CIQUAL_EN), T.fonte_probabile(CIQUAL_EN)), ("en", "CIQUAL"))

	def test_ciqual_in_francese(self):
		mappa = T.riconosci(CIQUAL_FR)
		self.assertEqual(colonna(CIQUAL_FR, mappa, "name"), "alim_nom_fr")
		self.assertEqual(colonna(CIQUAL_FR, mappa, "protein_g"), "Protéines, N x facteur de Jones (g/100 g)")
		self.assertEqual(colonna(CIQUAL_FR, mappa, "carbs_g"), "Glucides (g/100 g)")
		self.assertEqual(colonna(CIQUAL_FR, mappa, "fat_g"), "Lipides (g/100 g)")
		self.assertEqual(T.lingua_delle_colonne(CIQUAL_FR), "fr")

	def test_una_tabella_italiana(self):
		mappa = T.riconosci(ITALIANA)
		self.assertEqual(
			{campo: colonna(ITALIANA, mappa, campo) for campo in ("code", "name", "kcal", "kj", "protein_g")},
			{
				"code": "Codice",
				"name": "Nome",
				"kcal": "Energia (kcal)",
				"kj": "Energia (kJ)",
				"protein_g": "Proteine totali (g)",
			},
		)
		self.assertEqual(colonna(ITALIANA, mappa, "fat_g"), "Lipidi totali (g)")
		self.assertEqual(colonna(ITALIANA, mappa, "group"), ["Categoria"])
		self.assertEqual(T.lingua_delle_colonne(ITALIANA), "it")
		self.assertIsNone(T.fonte_probabile(ITALIANA))

	def test_i_carboidrati_per_differenza_perdono_la_fibra(self):
		usda = ["Description", "Energy (KCAL)", "Protein (G)", "Total lipid (fat) (G)"]
		usda += ["Carbohydrate, by difference (G)", "Fiber, total dietary (G)"]
		mappa = T.riconosci(usda)
		self.assertTrue(mappa["carbs_with_fibre"])
		cibo = T.alimenti([["Oats", 389, 16.9, 6.9, 66.3, 10.6]], mappa, "en")["foods"][0]
		self.assertAlmostEqual(cibo["carbs_g"], 55.7)

	def test_l_intestazione_dopo_un_titolo(self):
		righe = [["Tabella di composizione"], [], ITALIANA, ["1", "Pane", "Cereali", "275"]]
		self.assertEqual(T.trova_intestazione(righe), 2)
		self.assertIsNone(T.trova_intestazione([["a", "b"], [1, 2]]))


class IGruppi(UnitTestCase):
	def test_le_parole_della_categoria(self):
		for testi, lingua, gruppo in (
			(["vegetable oils", "fats and oils"], "en", "Oils and fats"),
			(["fish oils"], "en", "Oils and fats"),
			(["fruit juices"], "en", "Drinks"),
			(["nuts and seeds", "fruits, vegetables, legumes and nuts"], "en", "Nuts and seeds"),
			(["legumes"], "en", "Legumes"),
			(["légumes"], "fr", "Vegetables"),
			(["légumineuses"], "fr", "Legumes"),
			(["œufs"], "fr", "Eggs"),
			(["biscuits apéritifs"], "fr", "Cereals and tubers"),
			(["biscuits sucrés"], "fr", "Sweets"),
			(["meat substitute", "meat, egg and fish"], "en", "Other"),
			(["baby milk and beverages"], "en", "Other"),
			(["Frutta secca a guscio e semi oleaginosi"], "it", "Nuts and seeds"),
			(["Oli e grassi"], "it", "Oils and fats"),
			(["Latte e yogurt"], "it", "Milk and dairy"),
			(["Prodotti della pesca"], "it", "Fish"),
			(["Cereali e derivati"], "it", "Cereals and tubers"),
			(["Verdure e ortaggi"], "it", "Vegetables"),
			(["Ricette italiane"], "it", "Other"),
			(["", "-", "sauces"], "en", "Other"),
		):
			self.assertEqual(T.gruppo_da(testi, lingua), gruppo, testi)

	def test_il_piu_preciso_prima(self):
		# a sub-group that says nothing leaves the word to the group
		self.assertEqual(T.gruppo_da(["cream and similar", "milk and milk products"], "en"), "Milk and dairy")
		self.assertEqual(T.gruppo_da(["-", "ice cream and sorbet"], "en"), "Sweets")

	def test_chi_importa_sceglie_per_categoria(self):
		cibi = [
			{"name": "a", "category": "herbs", "group": "Other"},
			{"name": "b", "category": "herbs", "group": "Other"},
			{"name": "c", "category": "fruits", "group": "Fruit"},
		]
		self.assertEqual(
			T.categorie(cibi),
			[
				{"category": "herbs", "group": "Other", "count": 2},
				{"category": "fruits", "group": "Fruit", "count": 1},
			],
		)
		T.applica_gruppi(cibi, {"herbs": "Vegetables", "fruits": "not a group"})
		self.assertEqual([c["group"] for c in cibi], ["Vegetables", "Vegetables", "Fruit"])


class GliAlimenti(UnitTestCase):
	def riga(self, **valori):
		riga = [""] * len(CIQUAL_EN)
		for campo, valore in valori.items():
			riga[CIQUAL_EN.index(campo)] = valore
		return riga

	def test_una_riga_di_ciqual(self):
		riga = self.riga(
			alim_code=20047.0,
			alim_nom_eng="Carrot, raw",
			alim_ssgrp_nom_eng="vegetables",
			alim_grp_nom_eng="fruits, vegetables, legumes and nuts",
			**{
				"Energy, Regulation EU No 1169/2011 (kcal/100g)": "36,5",
				"Protein (g/100g)": "0,63",
				"Carbohydrate (g/100g)": "6,6",
				"Fat (g/100g)": "traces",
				"Fibres (g/100g)": "2,7",
			},
		)
		letti = T.alimenti([riga], T.riconosci(CIQUAL_EN), "en")
		self.assertEqual(
			letti["foods"],
			[
				{
					"code": "20047",
					"name": "Carrot, raw",
					"category": "vegetables",
					"group": "Vegetables",
					"kcal": 36.5,
					"protein_g": 0.63,
					"carbs_g": 6.6,
					"fat_g": 0.0,
					"fibre_g": 2.7,
					"kcal_computed": False,
				}
			],
		)

	def test_l_energia_che_la_tabella_non_da(self):
		# the Regulation EU 1169/2011 factors: 4 proteins, 4 carbohydrates, 9 fats,
		# 2 fibre, 7 alcohol
		riga = self.riga(
			alim_code="18067",
			alim_nom_eng="Red wine",
			**{
				"Energy, Regulation EU No 1169/2011 (kcal/100g)": "-",
				"Protein (g/100g)": "0,07",
				"Carbohydrate (g/100g)": "0,2",
				"Fat (g/100g)": "0",
				"Fibres (g/100g)": "-",
				"Alcohol (g/100g)": "10,2",
			},
		)
		cibo = T.alimenti([riga], T.riconosci(CIQUAL_EN), "en")["foods"][0]
		self.assertEqual((cibo["kcal"], cibo["kcal_computed"]), (72.5, True))
		# a fat not known: no energy is guessed
		riga[CIQUAL_EN.index("Fat (g/100g)")] = "-"
		cibo = T.alimenti([riga], T.riconosci(CIQUAL_EN), "en")["foods"][0]
		self.assertEqual((cibo["kcal"], cibo["kcal_computed"]), (None, False))

	def test_i_kilojoule_e_i_valori_impossibili(self):
		mappa = T.riconosci(ITALIANA)
		righe = [["1", "Olio", "Oli e grassi", "", "3700", "0", "", "140", "", "0", "0"]]
		cibo = T.alimenti(righe, mappa, "it")
		self.assertEqual(cibo["foods"][0]["kcal"], 884.3)
		# 140 g of fat in 100 g is not a food's
		self.assertIsNone(cibo["foods"][0]["fat_g"])
		self.assertEqual(cibo["dropped_values"], 1)

	def test_cosa_resta_fuori(self):
		mappa = T.riconosci(ITALIANA)
		righe = [
			["1", "Pane", "Cereali", "275", "", "8", "", "0,5", "", "58", "3"],
			["2", "", "Cereali", "300", "", "", "", "", "", "", ""],
			["3", "Mistero", "Varie", "-", "", "-", "", "-", "", "-", "-"],
			["1", "Pane di nuovo", "Cereali", "280", "", "", "", "", "", "", ""],
			[],
		]
		letti = T.alimenti(righe, mappa, "it")
		self.assertEqual([c["name"] for c in letti["foods"]], ["Pane"])
		self.assertEqual((letti["without_name"], letti["without_values"], letti["twice"]), (1, 1, 1))


class IlFoglio(UnitTestCase):
	def test_un_csv_con_il_punto_e_virgola_e_le_virgole(self):
		testo = "Codice;Nome;Energia (kcal);Proteine totali (g)\r\n7;Caffè;2;0,1\r\n"
		righe = T.leggi_foglio("tabella.csv", testo.encode("cp1252"))
		self.assertEqual(
			righe, [["Codice", "Nome", "Energia (kcal)", "Proteine totali (g)"], ["7", "Caffè", "2", "0,1"]]
		)

	def test_un_csv_in_utf8_con_le_virgole(self):
		testo = "﻿name,kcal,protein\nOats,389,16.9\n"
		self.assertEqual(T.leggi_foglio("t.csv", testo.encode("utf-8"))[1], ["Oats", "389", "16.9"])
