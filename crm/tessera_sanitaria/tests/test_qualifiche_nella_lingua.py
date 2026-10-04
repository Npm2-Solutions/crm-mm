# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The healthcare half of the register writes its notes and points to check in the
centre's language too (`crm.invoicing.install.nella_lingua`): their Italian is in
it.po by hand, as invoicing's half is."""

from __future__ import annotations

import unittest

from crm.tessera_sanitaria.engine.professioni import elenco
from crm.tests.test_frasi_del_motore import _msgid


class LeParoleSanitarieNelCatalogo(unittest.TestCase):
	def test_note_e_punti_da_verificare_hanno_il_loro_italiano(self):
		catalogo = _msgid()
		parole = set()
		for professione in elenco():
			if professione.note:
				parole.add(professione.note)
			parole.update(professione.da_verificare)
		self.assertTrue(parole)
		self.assertEqual(sorted(parola for parola in parole if parola not in catalogo), [])
