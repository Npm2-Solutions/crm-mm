# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A number the centre already has, into DottorCloud's space, without a site (doc 52,
sixth part)."""

import unittest

from crm.telephony import trasloco_regole as R


class IlTrasloco(unittest.TestCase):
	def test_un_tronco_resta(self):
		self.assertEqual(R.perche_resta({"trunk_sid": None}), "")
		self.assertIn("SIP trunk", R.perche_resta({"trunk_sid": "TK0"}))

	def test_che_cosa_serve_allo_spazio(self):
		self.assertEqual(R.cosa_serve({"bundle_sid": "BU1", "address_sid": "AD1"}), (True, True))
		self.assertEqual(R.cosa_serve({}), (False, False))

	def test_quelli_che_si_spostano_prima(self):
		righe = R.da_spostare(
			[
				{"phone_number": "+390299", "trunk_sid": "TK0"},
				{"phone_number": "+390233", "trunk_sid": None},
				{"phone_number": "+390211", "trunk_sid": None},
			]
		)
		self.assertEqual([r["phone_number"] for r in righe], ["+390211", "+390233", "+390299"])
		self.assertTrue(righe[-1]["reason"])
