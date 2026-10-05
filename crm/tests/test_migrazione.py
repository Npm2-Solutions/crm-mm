# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A migrate syncs every module of this release, even when a worker still running
the previous one left an old map of the modules in the cache: the map the process
holds and the one in the cache come from `modules.txt` again. And it writes the
release's words: the catalogue is compiled before it, where it is newer."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm import migrazione


class LaMappaDeiModuli(IntegrationTestCase):
	def setUp(self):
		self.prima = (frappe.local.app_modules, frappe.local.module_app)
		self.addCleanup(self.rimetti)

	def rimetti(self):
		frappe.local.app_modules, frappe.local.module_app = self.prima
		frappe.cache.delete_value("app_modules")

	def test_una_mappa_vecchia_non_nasconde_un_modulo_nuovo(self):
		vecchia = {app: list(moduli) for app, moduli in frappe.local.app_modules.items()}
		vecchia["crm"] = [modulo for modulo in vecchia["crm"] if modulo != "documenti"]
		frappe.local.app_modules = vecchia
		frappe.local.module_app = {m: app for app, moduli in vecchia.items() for m in moduli}
		frappe.cache.set_value("app_modules", vecchia)
		migrazione.mappa_dei_moduli()
		self.assertIn("documenti", frappe.local.app_modules["crm"])
		self.assertEqual(frappe.local.module_app["documenti"], "crm")
		self.assertIn("documenti", frappe.cache.get_value("app_modules")["crm"])

	def test_e_un_hook_della_migrazione(self):
		self.assertIn("crm.migrazione.mappa_dei_moduli", frappe.get_hooks("before_migrate", app_name="crm"))


class IlCatalogoDelRilascio(IntegrationTestCase):
	"""`bench update` migrates before it builds: the words the migrate writes are the
	release's only if the catalogue is compiled first."""

	def setUp(self):
		self.cartella = Path(tempfile.mkdtemp())
		self.addCleanup(shutil.rmtree, self.cartella, True)
		self.catalogo = self.cartella / "it.po"
		self.catalogo.write_text(
			'msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n\n'
			'msgid "Verify"\nmsgstr "Verifica"\n',
			encoding="utf-8",
		)
		self.compilato = self.cartella / "it" / "LC_MESSAGES" / "crm.mo"
		for nome, valore in (
			("get_locales", lambda app: ["it"]),
			("get_po_path", lambda app, lingua: self.catalogo),
			("get_mo_path", lambda app, lingua: self.compilato),
		):
			incolla = patch(f"frappe.gettext.translate.{nome}", valore)
			incolla.start()
			self.addCleanup(incolla.stop)
		self.pulita = patch("frappe.translate.clear_cache")
		self.cache = self.pulita.start()
		self.addCleanup(self.pulita.stop)

	def test_un_catalogo_nuovo_si_compila_prima_del_migrate(self):
		migrazione.il_catalogo_del_rilascio()
		self.assertTrue(self.compilato.exists())
		self.cache.assert_called_once()

	def test_un_catalogo_gia_compilato_resta_com_e(self):
		self.compilato.parent.mkdir(parents=True)
		self.compilato.write_bytes(b"gia compilato")
		ora = self.catalogo.stat().st_mtime
		os.utime(self.compilato, (ora + 60, ora + 60))
		migrazione.il_catalogo_del_rilascio()
		self.assertEqual(self.compilato.read_bytes(), b"gia compilato")
		self.cache.assert_not_called()

	def test_un_errore_non_ferma_il_migrate(self):
		with (
			patch("frappe.gettext.translate.write_binary", side_effect=OSError("sola lettura")),
			patch("frappe.log_error") as registrato,
		):
			migrazione.il_catalogo_del_rilascio()
		registrato.assert_called_once()

	def test_viene_prima_degli_hook_che_scrivono_parole(self):
		self.assertIn(
			"crm.migrazione.il_catalogo_del_rilascio", frappe.get_hooks("before_migrate", app_name="crm")
		)
