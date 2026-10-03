# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt
"""Every line of the patient's summary reads in Italian. Its name is translated
from a constant (`_(voce.etichetta)`), which the catalog's extraction cannot
see: without its entry in `it.po` the Clinic tab said «Blood pressure»."""

import unittest

from crm.clinica.sintesi import VOCI
from crm.tests.test_frasi_costanti import _msgid


class LeVociDellaSintesi(unittest.TestCase):
	def test_ogni_voce_ha_il_suo_italiano(self):
		catalogo = _msgid()
		mancano = [voce.etichetta for voce in VOCI if voce.etichetta not in catalogo]
		self.assertEqual(mancano, [])
