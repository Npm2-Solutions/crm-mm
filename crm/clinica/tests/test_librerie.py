# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The libraries on a real site: a food table in, the exercises of the dataset in,
corrected in the centre's words, imported again without losing them.

The manager uploads a table in CIQUAL's shape: the columns and the categories are
recognised, "herbs" goes to the vegetables because the manager says so, and only
the two foods chosen come in. The dietitian renames one in Italian; the next
version of the table brings new numbers and keeps the name. CREA and BDA-IEO come
in only when somebody declares the centre may use them, and the import says who.
The exercises of the library DottorCloud ships come with their steps in Italian;
loaded again, they keep the centre's words; their pictures appear, with whose they
are, once the agency says where it hosts them. The centre adds its own.
"""

import json

import frappe

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

INTESTAZIONE = (
	"alim_grp_nom_eng;alim_ssgrp_nom_eng;alim_code;alim_nom_eng;"
	"Energy, Regulation EU No 1169/2011 (kcal/100g);Protein (g/100g);Carbohydrate (g/100g);"
	"Fat (g/100g);Fibres (g/100g)"
)
RIGHE = (
	"fruits, vegetables, legumes and nuts;vegetables;T20047;Carrot, raw;36,5;0,63;6,6;traces;2,7",
	"miscellaneous;herbs;T11014;Basil, fresh;-;3,15;1,05;0,64;3,9",
	"cereal products;pasta, rice and grains;T9811;Pasta, cooked;157;5,6;30,3;0,9;1,8",
	"cereal products;pasta, rice and grains;T9999;;100;1;1;1;1",
)
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

	def carica(self, user, nome, contenuto) -> str:
		"""A file as the session uploads it: private, its own."""
		self.come(user)
		file = frappe.get_doc(
			{"doctype": "File", "file_name": nome, "content": contenuto, "is_private": 1}
		).insert(ignore_permissions=True)
		return file.file_url

	def tabella(self, user=MANAGER, righe=RIGHE) -> str:
		testo = "\n".join((INTESTAZIONE, *righe)) + "\n"
		return self.carica(user, "ciqual.csv", testo.encode("utf-8"))

	def importa(self, url, **altro):
		altro.setdefault("source", "CIQUAL")
		return librerie.import_foods(url, **altro)

	def cibo(self, codice):
		return frappe.get_doc(librerie.CIBO, {"source": "CIQUAL", "source_code": codice})


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


class UnaTabella(LibrerieCase):
	def test_l_anteprima_dice_colonne_categorie_e_cibi(self):
		url = self.tabella()
		vista = librerie.preview_foods(url)
		self.assertEqual((vista["source"], vista["language"]), ("CIQUAL", "en"))
		self.assertEqual(vista["columns"][vista["mapping"]["name"]], "alim_nom_eng")
		self.assertEqual(
			[(c["category"], c["group"], c["count"]) for c in vista["categories"]],
			[
				("vegetables", "Vegetables", 1),
				("herbs", "Other", 1),
				("pasta, rice and grains", "Cereals and tubers", 1),
			],
		)
		self.assertEqual(vista["total"], 3)
		self.assertEqual(vista["without_name"], 1)
		# basil has no energy in the table: computed from its nutrients, and said
		basilico = next(c for c in vista["foods"] if c["code"] == "T11014")
		self.assertEqual((basilico["kcal"], basilico["kcal_computed"]), (30.4, True))
		self.assertEqual(vista["computed"], 1)
		self.assertFalse(any(c["known"] for c in vista["foods"]))

	def test_solo_i_cibi_scelti_con_i_gruppi_scelti(self):
		url = self.tabella()
		fatto = self.importa(
			url, groups=json.dumps({"herbs": "Vegetables"}), keys=json.dumps(["T20047", "T11014"])
		)
		self.assertEqual((fatto["created"], fatto["updated"]), (2, 0))
		basilico = self.cibo("T11014")
		self.assertEqual((basilico.food_group, basilico.name_in_source), ("Vegetables", "Basil, fresh"))
		self.assertEqual((basilico.kcal, basilico.kcal_computed), (30.4, 1))
		self.assertEqual(basilico.source_note, librerie.ATTRIBUZIONI["CIQUAL"])
		self.assertFalse(frappe.db.exists(librerie.CIBO, {"source_code": "T9811"}))
		registro = frappe.get_doc(librerie_crm.IMPORTAZIONE, fatto["import"])
		self.assertEqual(
			(registro.library, registro.source, registro.imported_by, registro.created_count),
			("Foods", "CIQUAL", MANAGER, 2),
		)
		# the plans find them
		self.come(DOC1)
		self.assertIn("Carrot, raw", [c.food_name for c in piani_clinica.search_foods("carrot")])

	def test_di_nuovo_i_numeri_nuovi_il_nome_del_centro(self):
		self.importa(self.tabella())
		self.come(MANAGER)
		carota = self.cibo("T20047")
		librerie.save_food(
			carota.name,
			{"food_name": "Carota cruda", "food_group": "Vegetables", "portion_g": 100, "kcal": 999},
		)
		carota.reload()
		# a table's numbers are the table's: the name is the centre's
		self.assertEqual((carota.food_name, carota.portion_g, carota.kcal), ("Carota cruda", 100, 36.5))
		nuova = tuple(r.replace("36,5", "41") for r in RIGHE)
		fatto = self.importa(self.tabella(righe=nuova), attribution="ANSES-CIQUAL 2025")
		self.assertEqual((fatto["created"], fatto["updated"]), (0, 3))
		carota.reload()
		self.assertEqual(
			(carota.food_name, carota.kcal, carota.source_note), ("Carota cruda", 41, "ANSES-CIQUAL 2025")
		)
		self.assertTrue(librerie.preview_foods(self.tabella())["foods"][0]["known"])

	def test_crea_e_bda_ieo_solo_con_la_licenza(self):
		url = self.tabella()
		for fonte in ("CREA", "BDA-IEO"):
			with self.assertRaises(frappe.ValidationError):
				self.importa(url, source=fonte)
		fatto = self.importa(url, source="BDA-IEO", licence=1)
		registro = frappe.get_doc(librerie_crm.IMPORTAZIONE, fatto["import"])
		self.assertIn("BDA-IEO", registro.licence)
		self.assertEqual(frappe.db.get_value(librerie.CIBO, {"source_code": "T9811"}, "source"), "BDA-IEO")

	def test_un_file_che_non_e_una_tabella(self):
		url = self.carica(MANAGER, "note.csv", b"una nota\nqualcosa\n")
		with self.assertRaises(frappe.ValidationError):
			librerie.preview_foods(url)
		# the columns said by hand: the first is the name, the second the kcal
		url = self.carica(MANAGER, "t.csv", b"cibo;energia\nMela;52\n")
		with self.assertRaises(frappe.ValidationError):
			librerie.preview_foods(url)

	def test_il_file_di_un_altro_non_si_legge(self):
		url = self.tabella(user=DOC1)
		self.come(MANAGER)
		with self.assertRaises(frappe.PermissionError):
			librerie.preview_foods(url)


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
