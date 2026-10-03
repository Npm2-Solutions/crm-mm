# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The exercise library as the CRM reads it, without a site: the exercises with
their steps in the centre's language and their pictures' paths, and the file
DottorCloud ships."""

from __future__ import annotations

import json
from pathlib import Path

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the dataset is still readable
	from unittest import TestCase as UnitTestCase

from crm.piani import dataset as T

RECORD = {
	"id": "0001",
	"name": "3/4 sit-up",
	"category": "waist",
	"body_part": "waist",
	"equipment": "body weight",
	"instructions": {"it": "Sdraiati sulla schiena.", "en": "Lie flat on your back."},
	"instruction_steps": {
		"it": ["Sdraiati sulla schiena.", "Solleva il busto."],
		"en": ["Lie flat on your back.", "Lift your torso."],
	},
	"muscle_group": "hip flexors",
	"secondary_muscles": ["hip flexors", "lower back", "abs"],
	"target": "abs",
	"image": "images/0001-2gPfomN.jpg",
	"gif_url": "videos/0001-2gPfomN.gif",
	"media_id": "2gPfomN",
	"attribution": "© Gym visual — https://gymvisual.com/",
}


class GliEsercizi(UnitTestCase):
	def test_un_esercizio_del_dataset(self):
		self.assertEqual(
			T.esercizio(RECORD, "it"),
			{
				"code": "0001",
				"name": "3/4 sit-up",
				"name_in_source": "3/4 sit-up",
				"body_part": "Core",
				"equipment": "corpo libero",
				"primary_muscles": "addominali",
				"secondary_muscles": "flessori dell'anca, zona lombare",
				"instructions": "1. Sdraiati sulla schiena.\n2. Solleva il busto.",
				"media_path": "images/0001-2gPfomN.jpg",
				"animation_path": "videos/0001-2gPfomN.gif",
				"attribution": "© Gym visual — https://gymvisual.com/",
			},
		)

	def test_le_parole_della_libreria_nella_lingua_del_centro(self):
		inglese = T.esercizio(RECORD, "en")
		# a site loaded in English before it said it is in Italy
		self.assertEqual(
			T.nella_lingua(RECORD, "it", inglese),
			{"equipment": "corpo libero", "instructions": "1. Sdraiati sulla schiena.\n2. Solleva il busto."},
		)
		# words already right, or the centre's own: nothing to do
		self.assertEqual(T.nella_lingua(RECORD, "it", T.esercizio(RECORD, "it")), {})
		self.assertEqual(
			T.nella_lingua(RECORD, "it", {**inglese, "instructions": "Piano, guardando avanti."}),
			{"equipment": "corpo libero"},
		)
		self.assertEqual(
			T.nella_lingua(RECORD, "it", {**inglese, "equipment": None}),
			{"instructions": T.esercizio(RECORD, "it")["instructions"]},
		)
		# and back, on a site that chose English
		self.assertEqual(T.nella_lingua(RECORD, "en", T.esercizio(RECORD, "it"))["equipment"], "body weight")

	def test_in_inglese_e_senza_passi(self):
		record = {**RECORD, "name": "barbell curl", "instruction_steps": {}}
		fatto = T.esercizio(record, "en")
		self.assertEqual((fatto["name"], fatto["equipment"]), ("Barbell curl", "body weight"))
		self.assertEqual(fatto["instructions"], "Lie flat on your back.")

	def test_percorsi_e_indirizzi_delle_immagini(self):
		self.assertIsNone(T.esercizio({**RECORD, "gif_url": "../../etc/passwd"}, "it")["animation_path"])
		self.assertIsNone(T.esercizio({"id": "9", "name": ""}, "it"))
		self.assertIsNone(T.esercizio("not a record", "it"))
		self.assertEqual(
			T.indirizzo_media("https://cdn.example.com/esercizi/", "videos/0001-2gPfomN.gif"),
			"https://cdn.example.com/esercizi/videos/0001-2gPfomN.gif",
		)
		self.assertEqual(
			T.indirizzo_media("/assets/esercizi", "images/0001-2gPfomN.jpg"),
			"/assets/esercizi/images/0001-2gPfomN.jpg",
		)
		for base in (None, "", "http://cdn.example.com", "//cdn.example.com", "javascript:alert(1)"):
			self.assertIsNone(T.indirizzo_media(base, "images/0001-2gPfomN.jpg"), base)
		self.assertIsNone(T.indirizzo_media("https://cdn.example.com", "images/../../x.jpg"))


class LaLibreriaNelCodice(UnitTestCase):
	"""The file DottorCloud ships (`dati/esercizi.json`): every record an exercise,
	once, how it is done in Italian, its pictures with whose they are. An exercise
	NPM2 adds to the library has to be the same."""

	def test_ogni_voce_e_un_esercizio_completo(self):
		file = Path(T.__file__).parent / "dati" / "esercizi.json"
		record = json.loads(file.read_text(encoding="utf-8"))
		self.assertGreaterEqual(len(record), 1324)
		codici = set()
		for voce in record:
			esercizio = T.esercizio(voce, "it")
			self.assertIsNotNone(esercizio, voce)
			self.assertNotIn(esercizio["code"], codici, voce)
			codici.add(esercizio["code"])
			self.assertTrue(voce["instruction_steps"]["it"], voce["id"])
			self.assertTrue(esercizio["instructions"], voce["id"])
			if voce.get("image") or voce.get("gif_url"):
				self.assertTrue(esercizio["media_path"] or esercizio["animation_path"], voce["id"])
				self.assertEqual(voce["attribution"], "© Gym visual — https://gymvisual.com/")

	def test_la_licenza_viaggia_con_i_dati(self):
		licenza = (Path(T.__file__).parent / "dati" / "esercizi.LICENSE.txt").read_text(encoding="utf-8")
		self.assertIn("MIT License", licenza)
		self.assertIn("Gym visual", licenza)
