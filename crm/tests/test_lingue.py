# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The language of DottorCloud's own words on a site, without a site."""

from __future__ import annotations

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the rule is still testable
	from unittest import TestCase as UnitTestCase

from crm import lingue


class LaLinguaDelCentro(UnitTestCase):
	def test_in_italiano_se_il_sito_non_ha_scelto(self):
		# English is the framework's default, not a choice of a centre in Italy
		self.assertEqual(lingue.scegli("en", "Italy"), "it")
		self.assertEqual(lingue.scegli("en", None), "it")
		self.assertEqual(lingue.scegli("en-US", ""), "it")
		self.assertEqual(lingue.scegli(None, None), "it")
		self.assertEqual(lingue.scegli("it", "Italy"), "it")

	def test_la_lingua_scelta_altrove_resta(self):
		self.assertEqual(lingue.scegli("en-GB", "United Kingdom"), "en")
		self.assertEqual(lingue.scegli("de", "Germany"), "de")
		# a language other than English is a choice, wherever the centre is
		self.assertEqual(lingue.scegli("fr", "Italy"), "fr")


class LApostrofoDavantiAUnaData(UnitTestCase):
	"""«fino all'11 ottobre»: the server's filled sentences elide as the SPA's do
	(`conLApostrofo`, utils/locale.js)."""

	def test_davanti_al_giorno_1_8_11_di_una_data(self):
		c = lingue.con_l_apostrofo
		self.assertEqual(
			c("Il link vale fino al 1 ottobre, 14:00.", "it"), "Il link vale fino all'1 ottobre, 14:00."
		)
		self.assertEqual(c("Puoi aprirlo fino al 11/10/2026.", "it"), "Puoi aprirlo fino all'11/10/2026.")
		self.assertEqual(c("Fino al 8-10-2026", "it"), "Fino all'8-10-2026")
		self.assertEqual(c("prima del 1/1/2021", "it"), "prima dell'1/1/2021")
		self.assertEqual(c("Il 11 ott", "it"), "L'11 ott")

	def test_altrimenti_resta_com_e(self):
		c = lingue.con_l_apostrofo
		# another day, a day without a date, a rate, a year, a day written 08
		for testo in ("al 12 ottobre", "il 11", "il riepilogo IVA al 10%", "nel 2026", "il 08/10/2026"):
			self.assertEqual(c(testo, "it"), testo)
		# other languages, and what is not a sentence
		self.assertEqual(c("until al 11/10", "en"), "until al 11/10")
		self.assertIsNone(c(None, "it"))
