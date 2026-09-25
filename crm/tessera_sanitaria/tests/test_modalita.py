# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# See license.txt

"""Who transmits, and who holds the credentials to do it.

The distinction earns its own file because getting it wrong is expensive in both
directions: asking a centre on the provider channel for a PINCODE it does not have
blocks a save on a field that can never be filled, and quietly paying per document
for a channel that is free turns unlimited healthcare invoicing from a product
into a loss.
"""

from __future__ import annotations

from crm.invoicing.tests.base import UnitTestCase
from crm.tessera_sanitaria.engine.tracciato import MODALITA_CON_CREDENZIALI, richiede_credenziali


class ModalitaTest(UnitTestCase):
	def test_il_centro_che_trasmette_da_se_tiene_le_proprie_credenziali(self):
		self.assertTrue(richiede_credenziali("credenziali_studio"))

	def test_e_cosi_l_intermediario_entratel(self):
		self.assertTrue(richiede_credenziali("intermediario"))

	def test_il_provider_trasmette_sotto_il_proprio_accreditamento(self):
		# The centre has no Sistema TS credentials at all on this route. Asking for
		# them asks for something that does not exist.
		self.assertFalse(richiede_credenziali("provider"))

	def test_export_consegna_un_file_e_basta(self):
		self.assertFalse(richiede_credenziali("export"))

	def test_non_detto_non_pretende_credenziali(self):
		self.assertFalse(richiede_credenziali(None))
		self.assertFalse(richiede_credenziali(""))

	def test_sono_esattamente_due_le_modalita_con_credenziali(self):
		"""Pinned deliberately: adding a third is a decision, not a detail.

		Every mode in this set makes a centre hand over its fiscal identity, which is
		a liability that should never grow by accident.
		"""
		self.assertEqual(set(MODALITA_CON_CREDENZIALI), {"credenziali_studio", "intermediario"})
