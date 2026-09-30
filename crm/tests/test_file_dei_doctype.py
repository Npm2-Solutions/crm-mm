# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Frappe reads every JSON under a DocType's folder as a document: at the end of a
migrate it maps them by name, and one that is not a document stops the migrate
(the Feather icons' list did, on a newer Frappe v16). A list of anything else
lives outside the folder."""

import json
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1]


class NellaCartellaDiUnDocType(unittest.TestCase):
	def test_ogni_json_e_un_documento(self):
		for file in APP.glob("**/doctype/**/*.json"):
			dati = json.loads(file.read_text())
			for documento in dati if isinstance(dati, list) else [dati]:
				self.assertIsInstance(documento, dict, str(file.relative_to(APP)))
