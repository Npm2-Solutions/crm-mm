# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""The booking page colour: pure, runs with plain unittest."""

import unittest

from crm.scheduling.branding import accent_vars, hex_colour, readable_ink


class TestBranding(unittest.TestCase):
	def test_hex_colour(self):
		self.assertEqual(hex_colour("#4C7EFF"), "#4c7eff")
		self.assertEqual(hex_colour("4c7eff"), "#4c7eff")
		self.assertEqual(hex_colour("#abc"), "#aabbcc")
		self.assertIsNone(hex_colour(""))
		self.assertIsNone(hex_colour(None))
		self.assertIsNone(hex_colour("red; } body { display:none"))

	def test_readable_ink(self):
		self.assertEqual(readable_ink("#000000"), "#ffffff")
		self.assertEqual(readable_ink("#1f3a93"), "#ffffff")
		self.assertEqual(readable_ink("#ffffff"), "#111111")
		self.assertEqual(readable_ink("#ffd60a"), "#111111")

	def test_accent_vars(self):
		self.assertEqual(accent_vars(""), {})
		css = accent_vars("#30A46C")
		self.assertEqual(css["--accent"], "#30a46c")
		self.assertIn(css["--accent-ink"], ("#ffffff", "#111111"))
		self.assertIn("#30a46c", css["--accent-soft"])


if __name__ == "__main__":
	unittest.main()
