# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The pages a patient opens without signing in load nothing from another site: a
font from Google told Google every visitor of /prenota (the simulation of a week
found it, e2e/simulazione). And a finger's size where a finger taps. Pure: reads
the templates, runs with plain unittest."""

import re
import unittest
from pathlib import Path

WWW = Path(__file__).resolve().parents[1] / "www"
TEMPLATES = Path(__file__).resolve().parents[1] / "templates"
FUORI = re.compile(r"<(?:link|script|img|iframe)\b[^>]*\b(?:href|src)=[\"']https?://", re.IGNORECASE)


class TestPaginePubbliche(unittest.TestCase):
	def test_nothing_from_another_site(self):
		pagine = sorted(WWW.glob("*.html")) + sorted(TEMPLATES.rglob("*.html"))
		self.assertTrue(pagine)
		for pagina in pagine:
			with self.subTest(pagina=pagina.name):
				self.assertIsNone(FUORI.search(pagina.read_text(encoding="utf-8")))

	def test_booking_page_speaks_to_a_screen_reader(self):
		pagina = (WWW / "prenota.html").read_text(encoding="utf-8")
		# icon buttons named in words, a day read as a day
		for crudo in (
			'"aria-label": "prev"',
			'"aria-label": "next"',
			'"aria-label": "-"',
			'"aria-label": "+"',
		):
			self.assertNotIn(crudo, pagina)
		self.assertNotIn('"aria-label": key', pagina)
		self.assertIn("@media (pointer: coarse)", pagina)


if __name__ == "__main__":
	unittest.main()
