# Copyright (c) 2026, NPM2 Solutions Srl and contributors
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


class FiduciaTest(UnitTestCase):
	"""The test door's certificate comes from Sogei's own test CA: only there, and only
	when the site names the file, is anything but the system's trust used."""

	def verifica(self, **conf):
		from unittest import mock

		import frappe

		from crm.tessera_sanitaria import trasporto

		with mock.patch.dict(frappe.local.conf, conf, clear=False):
			for chiave in ("sistema_ts_ambiente", "sistema_ts_ca"):
				if chiave not in conf:
					frappe.local.conf.pop(chiave, None)
			return trasporto._verifica()

	def test_in_produzione_sempre_il_sistema(self):
		self.assertIs(self.verifica(sistema_ts_ca="/x/sogei.pem"), True)
		self.assertIs(self.verifica(sistema_ts_ambiente="produzione", sistema_ts_ca="/x/sogei.pem"), True)

	def test_in_prova_il_file_del_sito(self):
		self.assertEqual(
			self.verifica(sistema_ts_ambiente="test", sistema_ts_ca="/x/sogei.pem"), "/x/sogei.pem"
		)
		# nothing named: the system's, never verification off
		self.assertIs(self.verifica(sistema_ts_ambiente="test"), True)

	def test_una_risposta_persa_non_si_rimanda(self):
		# the document may have arrived: sent again it would be a duplicate
		from types import SimpleNamespace
		from unittest import mock

		import requests

		from crm.tessera_sanitaria import trasporto

		sessione = mock.Mock()
		sessione.post.side_effect = requests.exceptions.ReadTimeout()
		credenziali = SimpleNamespace(utente="u", password="p")
		with mock.patch("frappe.utils.get_request_session", return_value=sessione):
			with self.assertRaises(trasporto.ErroreTrasporto) as preso:
				trasporto._post("https://x", b"", {}, credenziali)
		self.assertEqual(sessione.post.call_count, 1)
		self.assertIn("may have arrived", str(preso.exception))
