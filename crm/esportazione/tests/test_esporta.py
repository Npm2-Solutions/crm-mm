# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre takes its data away: one archive, its records whole and as tables,
its files, the demo's left out; only for whoever may."""

import json
import os
import zipfile

import frappe
from frappe.tests import IntegrationTestCase

from crm.esportazione import esporta
from crm.permissions import livelli, utenti
from crm.permissions.test_org_hierarchy import make_user

MANAGER = "esporta.manager@example.com"
SEGRETERIA = "esporta.segreteria@example.com"


class LArchivioDelCentro(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		utenti.sincronizza()
		make_user(MANAGER)
		utenti.assegna_livelli(MANAGER, ["manager"])
		make_user(SEGRETERIA)
		utenti.assegna_livelli(SEGRETERIA, ["segreteria"])
		livelli.dimentica_cache()
		frappe.cache.delete_value(esporta.CHIAVE)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.cache.delete_value(esporta.CHIAVE)

	def test_solo_il_responsabile_porta_via_i_dati(self):
		frappe.set_user(SEGRETERIA)
		with self.assertRaises(frappe.PermissionError):
			esporta.get_exports()
		frappe.set_user(MANAGER)
		self.assertEqual(esporta.get_exports()["days"], esporta.GIORNI)

	def test_l_archivio_ha_i_documenti_interi_e_le_tabelle(self):
		persona = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Archivio", "last_name": "DelCentro"}
		).insert(ignore_permissions=True)
		della_demo = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Demo", "last_name": "DaLasciare"}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "CRM Demo Record",
				"ref_doctype": "CRM Lead",
				"ref_name": della_demo.name,
				"parte": "test",
			}
		).insert(ignore_permissions=True)
		allegato = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "referto di prova.txt",
				"content": b"un referto",
				"is_private": 1,
				"attached_to_doctype": "CRM Lead",
				"attached_to_name": persona.name,
			}
		).insert(ignore_permissions=True)

		nome = esporta.prepara(MANAGER, con_file=True)
		self.assertTrue(nome)
		file = frappe.get_doc("File", nome)
		self.assertEqual(file.owner, MANAGER)
		self.assertTrue(file.is_private)
		with zipfile.ZipFile(file.get_full_path()) as zf:
			nomi = zf.namelist()
			self.assertIn("LEGGIMI.txt", nomi)
			righe = [json.loads(r) for r in zf.read("dati/crm-lead.jsonl").decode().splitlines()]
			chi = {r["name"] for r in righe}
			self.assertIn(persona.name, chi)
			# what the demo made is not the centre's
			self.assertNotIn(della_demo.name, chi)
			self.assertIn("tabelle/crm-lead.csv", nomi)
			elenco = json.loads(zf.read("elenco.json"))
			self.assertGreaterEqual(elenco["file"], 1)
			percorsi = [n for n in nomi if n.startswith(f"file/crm-lead/{persona.name}/")]
			self.assertEqual(len(percorsi), 1)
			self.assertEqual(zf.read(percorsi[0]), b"un referto")
			# never a settings page, with its keys
			self.assertFalse([n for n in nomi if "fcrm-settings" in n])
		self.assertIsNone(frappe.cache.get_value(esporta.CHIAVE))
		allegato.delete(ignore_permissions=True)
		os.remove(file.get_full_path())
		frappe.delete_doc("File", nome, force=True, ignore_permissions=True)

	def test_un_archivio_alla_volta(self):
		frappe.set_user(MANAGER)
		frappe.cache.set_value(esporta.CHIAVE, {"by": MANAGER})
		with self.assertRaises(frappe.ValidationError):
			esporta.start_export()
