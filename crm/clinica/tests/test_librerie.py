# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The libraries on a real site: the foods and the exercises DottorCloud ships,
put in the centre's words, loaded again without losing them.

The foods come with their names in Italian, ANSES's English beside them, and the
plans find them by either. The dietitian renames one; the next version of the
library brings new numbers and keeps the name, while a name nobody touched follows
the library's - a table a centre imported before included. The centre adds its own
foods, with their numbers. The exercises come with their steps in Italian; loaded
again, they keep the centre's words; their pictures appear, with whose they are,
once the agency says where it hosts them. The centre adds its own.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import frappe

from crm import lingue
from crm.clinica import librerie
from crm.clinica import piani as piani_clinica
from crm.clinica import piani_regole as R
from crm.clinica.area import piani as area_clinica
from crm.clinica.tests.test_cartella import DESK, DIRECTOR, DOC1, DOC2, MANAGER
from crm.clinica.tests.test_piani import PianiCase
from crm.permissions import livelli, utenti
from crm.piani import api as piani
from crm.piani import area as area_piani
from crm.piani import dataset as T
from crm.piani import librerie as librerie_crm
from crm.piani import regole as r

CIBI = [
	{
		"code": "T20047",
		"name": "Carota, cruda",
		"name_en": "Carrot, raw",
		"group": "Vegetables",
		"kcal": 36.5,
		"protein_g": 0.63,
		"carbs_g": 6.6,
		"fat_g": 0,
		"fibre_g": 2.7,
		"kcal_computed": 0,
	},
	{
		"code": "T11014",
		"name": "Basilico, fresco",
		"name_en": "Basil, fresh",
		"group": "Other",
		"kcal": 30.4,
		"protein_g": 3.15,
		"carbs_g": 1.05,
		"fat_g": 0.64,
		"fibre_g": 3.9,
		"kcal_computed": 1,
	},
	{"code": "T9999", "name": "Senza valori", "name_en": "No values", "group": "Other"},
	"not a food",
]
DATASET = [
	{
		"id": "T001",
		"name": "3/4 sit-up",
		"body_part": "waist",
		"equipment": "body weight",
		"instructions": {"it": "Sdraiati sulla schiena.", "en": "Lie flat on your back."},
		"instruction_steps": {"it": ["Sdraiati sulla schiena.", "Solleva il busto."], "en": ["Lie flat."]},
		"secondary_muscles": ["hip flexors"],
		"target": "abs",
		"image": "images/0001-2gPfomN.jpg",
		"gif_url": "videos/0001-2gPfomN.gif",
		"attribution": "© Gym visual — https://gymvisual.com/",
	},
	{
		"id": "T002",
		"name": "barbell curl",
		"body_part": "upper arms",
		"equipment": "barbell",
		"instructions": {"it": "Afferra il bilanciere."},
		"instruction_steps": {"it": ["Afferra il bilanciere."]},
		"secondary_muscles": ["forearms"],
		"target": "biceps",
		"image": "images/0002-x.jpg",
		"gif_url": "videos/0002-x.gif",
		"attribution": "© Gym visual — https://gymvisual.com/",
	},
	"not an exercise",
]


class LibrerieCase(PianiCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		frappe.db.set_single_value(librerie_crm.IMPOSTAZIONI, "exercise_media_url", None)

	def cibo(self, codice):
		return frappe.get_doc(librerie.CIBO, {"source": librerie.FONTE, "source_code": codice})


class ChiLeTiene(LibrerieCase):
	def test_il_manager_e_la_direzione_non_la_segreteria(self):
		for user in (MANAGER, DIRECTOR):
			self.come(user)
			self.assertIn("rows", librerie.get_foods())
		for user in (DESK, DOC1):
			self.come(user)
			with self.assertRaises(frappe.PermissionError):
				librerie.get_foods()

	def test_la_nutrizionista_quando_il_manager_la_sceglie(self):
		frappe.set_user("Administrator")
		utenti.imposta_capacita(DOC1, "piani.librerie", True)
		self.come(DOC1)
		self.assertTrue(livelli.puo("piani.librerie"))
		self.assertIn("rows", librerie_crm.get_exercises())


class LaLibreriaDegliAlimenti(LibrerieCase):
	def test_i_nomi_in_italiano_e_l_inglese_della_tabella(self):
		fatto = librerie.carica(CIBI, "it")
		self.assertEqual((fatto["created"], fatto["updated"], fatto["skipped"]), (2, 0, 2))
		basilico = self.cibo("T11014")
		self.assertEqual(
			(basilico.food_name, basilico.name_in_source, basilico.food_group),
			("Basilico, fresco", "Basil, fresh", "Other"),
		)
		# the table gave no energy: computed from its nutrients, and said
		self.assertEqual((basilico.kcal, basilico.kcal_computed), (30.4, 1))
		self.assertEqual(basilico.source_note, librerie.ATTRIBUZIONE)
		# the plans find it by the centre's words, and by the table's
		self.come(DOC1)
		self.assertIn("Carota, cruda", [c.food_name for c in piani_clinica.search_foods("carota")])
		self.assertIn("Carota, cruda", [c.food_name for c in piani_clinica.search_foods("carrot")])

	def test_di_nuovo_i_numeri_nuovi_il_nome_del_centro(self):
		librerie.carica(CIBI, "it")
		self.come(MANAGER)
		carota = self.cibo("T20047")
		librerie.save_food(
			carota.name,
			{"food_name": "Carote del centro", "food_group": "Vegetables", "portion_g": 100, "kcal": 999},
		)
		carota.reload()
		# the library's numbers are the library's: the name is the centre's
		self.assertEqual((carota.food_name, carota.portion_g, carota.kcal), ("Carote del centro", 100, 36.5))
		nuova = [dict(CIBI[0], kcal=41), dict(CIBI[1], name="Basilico fresco, foglie")]
		frappe.set_user("Administrator")
		fatto = librerie.carica(nuova, "it")
		self.assertEqual((fatto["created"], fatto["updated"]), (0, 2))
		carota.reload()
		self.assertEqual((carota.food_name, carota.kcal), ("Carote del centro", 41))
		# nobody renamed the basil: it follows the library
		self.assertEqual(self.cibo("T11014").food_name, "Basilico fresco, foglie")

	def test_una_tabella_importata_prima_prende_i_nomi_italiani(self):
		# a centre imported CIQUAL in French before the library came
		frappe.get_doc(
			{
				"doctype": librerie.CIBO,
				"food_name": "Carotte, crue",
				"food_group": "Vegetables",
				"kcal": 36,
				"source": librerie.FONTE,
				"source_code": "T20047",
				"name_in_source": "Carotte, crue",
			}
		).insert(ignore_permissions=True)
		fatto = librerie.carica(CIBI, "it")
		self.assertEqual((fatto["created"], fatto["updated"]), (1, 1))
		carota = self.cibo("T20047")
		self.assertEqual(
			(carota.food_name, carota.name_in_source, carota.kcal), ("Carota, cruda", "Carrot, raw", 36.5)
		)

	def test_in_un_sito_inglese_i_nomi_della_tabella(self):
		librerie.carica(CIBI, "en")
		self.assertEqual(self.cibo("T20047").food_name, "Carrot, raw")

	def test_un_sito_caricato_in_inglese_passa_all_italiano(self):
		# a site that spoke the framework's English before it said it is in Italy
		with tempfile.TemporaryDirectory() as cartella:
			file = Path(cartella) / "alimenti.json"
			file.write_text(json.dumps(CIBI))
			self.addCleanup(
				frappe.db.set_default,
				librerie.VERSIONE_CARICATA,
				frappe.db.get_default(librerie.VERSIONE_CARICATA),
			)
			with patch.object(librerie, "LIBRERIA", file):
				with patch.object(lingue, "del_centro", return_value="en"):
					self.assertIsNotNone(librerie.carica_libreria())
					self.assertIsNone(librerie.carica_libreria())
				self.assertEqual(self.cibo("T20047").food_name, "Carrot, raw")
				self.come(MANAGER)
				basilico = self.cibo("T11014")
				librerie.save_food(basilico.name, {"food_name": "Basilico dell'orto", "food_group": "Other"})
				frappe.set_user("Administrator")
				# the same file, wanted in Italian: loaded again, and the names nobody
				# touched follow; the centre's stays
				self.assertIsNotNone(librerie.carica_libreria())
		self.assertEqual(self.cibo("T20047").food_name, "Carota, cruda")
		self.assertEqual(self.cibo("T11014").food_name, "Basilico dell'orto")

	def test_la_libreria_si_carica_una_volta_per_versione(self):
		# the site loaded the shipped file at install: the same file is not loaded again
		librerie.carica_libreria()
		self.assertIsNone(librerie.carica_libreria())
		self.assertTrue(frappe.db.exists(librerie.CIBO, {"source": librerie.FONTE, "source_code": "20009"}))

	def test_il_centro_aggiunge_i_suoi(self):
		self.come(MANAGER)
		fatto = librerie.save_food(
			None,
			{"food_name": "Pane del forno di via Roma", "food_group": "Cereals and tubers", "kcal": 270},
		)
		self.assertEqual(
			(fatto["food_name"], fatto["kcal"], fatto["source"]),
			("Pane del forno di via Roma", 270, librerie.CENTRO),
		)
		self.assertIn(
			"Pane del forno di via Roma",
			[r["food_name"] for r in librerie.get_foods(text="via Roma", source="Centre")["rows"]],
		)
		with self.assertRaises(frappe.ValidationError):
			librerie.save_food(None, {"food_name": " ", "food_group": "Cereals and tubers"})


class IlCiboDelCentro(LibrerieCase):
	def test_i_suoi_numeri_si_scrivono_qui(self):
		self.come(MANAGER)
		fatto = librerie.save_food(
			self.pasta.name,
			{
				"food_name": "Pasta di semola",
				"food_group": "Cereals and tubers",
				"kcal": 350,
				"protein_g": 12,
			},
		)
		self.assertEqual((fatto["kcal"], fatto["protein_g"]), (350, 12))
		spento = librerie.save_food(self.pasta.name, {**fatto, "enabled": 0})
		self.assertEqual(spento["enabled"], 0)
		self.come(DOC1)
		self.assertNotIn(self.pasta.name, [c.name for c in piani_clinica.search_foods("pasta")])
		with self.assertRaises(frappe.ValidationError):
			self.come(MANAGER)
			librerie.save_food(self.pasta.name, {"food_name": "", "food_group": "Cereals and tubers"})


class GliEsercizi(LibrerieCase):
	def test_la_libreria_con_i_passi_in_italiano(self):
		fatto = librerie_crm.carica(DATASET, "it")
		self.assertEqual((fatto["created"], fatto["updated"], fatto["skipped"]), (2, 0, 1))
		curl = frappe.get_doc(librerie_crm.ESERCIZIO, {"source": T.DATASET, "source_code": "T002"})
		self.assertEqual(
			(curl.exercise_name, curl.body_part, curl.equipment, curl.primary_muscles),
			("Barbell curl", "Arms", "bilanciere", "bicipiti"),
		)
		self.assertEqual(curl.instructions, "1. Afferra il bilanciere.")
		self.assertEqual((curl.media_path, curl.animation_path), ("images/0002-x.jpg", "videos/0002-x.gif"))

	def test_di_nuovo_le_immagini_nuove_le_parole_del_centro(self):
		librerie_crm.carica(DATASET, "it")
		self.come(MANAGER)
		addome = frappe.get_doc(librerie_crm.ESERCIZIO, {"source": T.DATASET, "source_code": "T001"})
		librerie_crm.save_exercise(addome.name, {"exercise_name": "Crunch a tre quarti", "body_part": "Core"})
		DATASET[0]["gif_url"] = "videos/0001-nuovo.gif"
		try:
			frappe.set_user("Administrator")
			fatto = librerie_crm.carica(DATASET, "it")
		finally:
			DATASET[0]["gif_url"] = "videos/0001-2gPfomN.gif"
		self.assertEqual((fatto["created"], fatto["updated"]), (0, 2))
		addome.reload()
		self.assertEqual(
			(addome.exercise_name, addome.animation_path), ("Crunch a tre quarti", "videos/0001-nuovo.gif")
		)

	def test_un_sito_caricato_in_inglese_passa_all_italiano(self):
		librerie_crm.carica(DATASET, "en")
		addome = frappe.get_doc(librerie_crm.ESERCIZIO, {"source": T.DATASET, "source_code": "T001"})
		self.assertEqual(
			(addome.equipment, addome.instructions, addome.primary_muscles),
			("body weight", "1. Lie flat.", "abs"),
		)
		# the centre wrote how the curl is done, and kept the library's equipment
		self.come(MANAGER)
		curl = frappe.get_doc(librerie_crm.ESERCIZIO, {"source": T.DATASET, "source_code": "T002"})
		librerie_crm.save_exercise(
			curl.name,
			{
				"exercise_name": curl.exercise_name,
				"body_part": curl.body_part,
				"equipment": curl.equipment,
				"instructions": "Gomiti fermi.",
			},
		)
		frappe.set_user("Administrator")
		librerie_crm.carica(DATASET, "it")
		addome.reload()
		curl.reload()
		self.assertEqual(
			(addome.equipment, addome.instructions, addome.primary_muscles),
			("corpo libero", "1. Sdraiati sulla schiena.\n2. Solleva il busto.", "addominali"),
		)
		self.assertEqual((curl.equipment, curl.instructions), ("bilanciere", "Gomiti fermi."))

	def test_la_libreria_si_carica_una_volta_per_versione(self):
		# the site loaded the shipped file at install: the same file is not loaded again
		librerie_crm.carica_libreria()
		self.assertIsNone(librerie_crm.carica_libreria())
		self.assertTrue(
			frappe.db.exists(librerie_crm.ESERCIZIO, {"source": T.DATASET, "source_code": "0001"})
		)

	def test_il_centro_aggiunge_i_suoi(self):
		self.come(MANAGER)
		fatto = librerie_crm.save_exercise(
			None, {"exercise_name": "Ponte su una gamba", "body_part": "Legs", "instructions": "Piano."}
		)
		self.assertEqual(
			(fatto["exercise_name"], fatto["body_part"], fatto["source"]),
			("Ponte su una gamba", "Legs", librerie_crm.CENTRO),
		)
		self.assertIn(
			"Ponte su una gamba",
			[
				riga["exercise_name"]
				for riga in librerie_crm.get_exercises(text="Ponte su", source="Centre")["rows"]
			],
		)
		with self.assertRaises(frappe.ValidationError):
			librerie_crm.save_exercise(None, {"exercise_name": "  "})

	def test_le_immagini_dove_le_tiene_l_agenzia_con_il_loro_autore(self):
		librerie_crm.carica(DATASET, "it")
		frappe.set_user("Administrator")
		addome = frappe.db.get_value(
			librerie_crm.ESERCIZIO, {"source": T.DATASET, "source_code": "T001"}, "name"
		)
		dati = {
			"plan_type": R.ESERCIZI,
			"title": "Esercizi a casa",
			"moments": [{"key": "sera", "label": "Sera", "day": r.OGNI_GIORNO}],
			"items": [
				{"key": "addome", "moment": "sera", "kind": r.ESERCIZIO, "exercise": addome, "sets": 3}
			],
		}
		scritto = self.scrive(user=DOC2, dati=dati)

		def figura():
			# what the patient's area shows of it
			piano = frappe.get_doc(piani.PIANO, scritto["name"])
			_momenti, voci = piani.righe_del_piano(piano)
			voce = area_piani.per_la_persona(voci[0], piano, {})
			return voce["image"], voce["attribution"]

		# no address yet: no picture, and no owner of a picture to name
		self.assertEqual(figura(), (None, None))
		self.come(MANAGER)
		with self.assertRaises(frappe.PermissionError):
			librerie_crm.save_media_url("https://cdn.example.com/esercizi")
		frappe.set_user("Administrator")
		with self.assertRaises(frappe.ValidationError):
			librerie_crm.save_media_url("http://cdn.example.com/esercizi")
		librerie_crm.save_media_url("https://cdn.example.com/esercizi/")
		self.assertEqual(
			figura(),
			(
				"https://cdn.example.com/esercizi/videos/0001-2gPfomN.gif",
				"© Gym visual — https://gymvisual.com/",
			),
		)
		# the centre's own picture wins, and it is not Gym visual's
		frappe.db.set_value(librerie_crm.ESERCIZIO, addome, "image", "/files/ponte.jpg")
		self.assertEqual(figura(), ("/files/ponte.jpg", None))
