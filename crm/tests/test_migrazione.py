# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A migrate syncs every module of this release, even when a worker still running
the previous one left an old map of the modules in the cache: the map the process
holds and the one in the cache come from `modules.txt` again."""

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
