# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The shipped register's words are DottorCloud's: a qualification's notes and the
points an accountant still has to check are written in the centre's language
(`crm.lingue`), and follow it while nobody changed them. The extraction never sees
them (they reach `_()` as variables), so their Italian is in it.po by hand: «Cassa
Forense contributo integrativo 4%: mandatory…» was what a lawyer's entry said in
an Italian practice.
"""

from __future__ import annotations

import unittest
from dataclasses import replace

import frappe
from frappe.tests import IntegrationTestCase

from crm.invoicing import install
from crm.invoicing.engine.professioni import Professione, elenco
from crm.tests.test_frasi_del_motore import _msgid


def parole(professioni: list[Professione]) -> set[str]:
	"""The notes and the points to check: always English in the code."""
	trovate: set[str] = set()
	for professione in professioni:
		if professione.note:
			trovate.add(professione.note)
		trovate.update(professione.da_verificare)
	return trovate


class LeParoleNelCatalogo(unittest.TestCase):
	def test_note_e_punti_da_verificare_hanno_il_loro_italiano(self):
		catalogo = _msgid()
		mancanti = sorted(parola for parola in parole(elenco()) if parola not in catalogo)
		self.assertEqual(mancanti, [], "not in crm/locale/it.po")

	def test_un_nome_con_parole_inglesi_ha_il_suo_italiano(self):
		catalogo = _msgid()
		inglesi = [p.etichetta for p in elenco() if "(non-" in p.etichetta]
		self.assertTrue(inglesi)
		self.assertEqual([nome for nome in inglesi if nome not in catalogo], [])


class LeParoleSeguonoLaLingua(IntegrationTestCase):
	def setUp(self):
		install.semina_qualifiche()
		self.consulente = next(p for p in elenco() if p.codice == "consulente")

	def _scrivi(self, valori: dict):
		frappe.db.set_value(install.QUALIFICA, "consulente", valori, update_modified=False)

	def _leggi(self) -> dict:
		return frappe.db.get_value(install.QUALIFICA, "consulente", list(install.PAROLE), as_dict=True)

	def test_le_parole_di_dottorcloud_prendono_la_lingua_del_centro(self):
		self._scrivi(install.parole_di(self.consulente, "en"))
		install.nella_lingua([self.consulente], "it")
		italiano = install.parole_di(self.consulente, "it")
		self.assertEqual(self._leggi()["qualification_name"], italiano["qualification_name"])
		self.assertEqual(self._leggi()["notes"], italiano["notes"])
		# and back, if the centre chose English
		install.nella_lingua([self.consulente], "en")
		self.assertEqual(self._leggi()["notes"], self.consulente.note)

	def test_le_parole_del_centro_restano(self):
		self._scrivi({"notes": "Scritta dallo studio, con il commercialista"})
		install.nella_lingua([self.consulente], "it")
		self.assertEqual(self._leggi()["notes"], "Scritta dallo studio, con il commercialista")

	def test_una_qualifica_tolta_non_torna(self):
		finta = replace(self.consulente, codice="qualifica_che_non_esiste")
		self.assertEqual(install.nella_lingua([finta], "it"), 0)
		self.assertFalse(frappe.db.exists(install.QUALIFICA, "qualifica_che_non_esiste"))
