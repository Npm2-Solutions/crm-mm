# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The body chart drawn, without a site: the outlines, a stroke, the picture the
signed PDF carries. What an answer may hold is in the shared cases
(`casi_schema.json`, «body_charts»), proved here and in the browser."""

from __future__ import annotations

import base64

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the drawing is still fully testable
	from unittest import TestCase as UnitTestCase

from crm.moduli import corpo

PAROLE = {"front": "Davanti", "back": "Dietro", "right": "D", "left": "S"}
RISPOSTA = {
	"marks": [
		{"view": "back", "x": 0.5, "y": 0.4, "label": "<b>schiena</b>", "intensity": 7},
		{"view": "front", "x": 0.25, "y": 0.5},
	],
	"strokes": [{"view": "back", "points": [[0.4, 0.3], [0.45, 0.32], [0.5, 0.36]]}],
}


class IlDisegno(UnitTestCase):
	def test_le_sagome_ci_sono_tutte(self):
		sagome = corpo.sagome()
		self.assertEqual(sagome["viewBox"], "0 0 200 460")
		for chiave in ("head", "body", "front", "back"):
			self.assertTrue(sagome[chiave])

	def test_un_tratto_passa_per_i_punti_di_mezzo(self):
		self.assertEqual(corpo.percorso([]), "")
		self.assertEqual(corpo.percorso([[0.5, 0.5]]), "M100 230l0.1 0")
		# the browser draws the same line (`smoothPath`)
		self.assertEqual(corpo.percorso([[0, 0], [0.5, 0.5], [1, 1]]), "M0 0Q100 230 150 345L200 460")

	def test_i_punti_hanno_il_loro_numero(self):
		self.assertEqual([s["number"] for s in corpo.numerati(RISPOSTA)], [1, 2])
		self.assertEqual(corpo.numerati(None), [])

	def test_le_due_sagome_con_i_segni(self):
		disegno = corpo.svg({}, RISPOSTA, PAROLE)
		self.assertTrue(disegno.startswith('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 484"'))
		self.assertEqual(disegno.count("<circle"), 2)
		self.assertIn("Davanti", disegno)
		self.assertIn("Dietro", disegno)
		# the words of a point are never in the picture: only its number
		self.assertNotIn("schiena", disegno)

	def test_una_sagoma_sola(self):
		disegno = corpo.svg({"views": ["back"]}, RISPOSTA, PAROLE)
		self.assertIn('viewBox="0 0 200 484"', disegno)
		# the front's point is not drawn on the back
		self.assertEqual(disegno.count("<circle"), 1)
		self.assertNotIn("Davanti", disegno)

	def test_vuota_per_chi_segna_a_mano(self):
		disegno = corpo.svg({}, None, PAROLE)
		self.assertNotIn("<circle", disegno)

	def test_un_immagine_dentro_la_pagina(self):
		dati = corpo.come_immagine({}, RISPOSTA, PAROLE)
		self.assertTrue(dati.startswith("data:image/svg+xml;base64,"))
		self.assertIn(b"<svg", base64.b64decode(dati.split(",", 1)[1]))

	def test_le_parole_sono_scritte_come_testo(self):
		disegno = corpo.svg({}, None, {**PAROLE, "front": "<script>"})
		self.assertIn("&lt;script&gt;", disegno)
