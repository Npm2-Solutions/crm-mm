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
