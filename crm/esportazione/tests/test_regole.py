# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

import datetime
import decimal
import json
import unittest

from crm.esportazione import regole as R


class CosaVaNellArchivio(unittest.TestCase):
	def test_i_tipi_del_centro_e_quelli_del_framework_che_li_accompagnano(self):
		tipi = [
			{"name": "CRM Lead", "module_app": "crm"},
			{"name": "CRM Contacts", "module_app": "crm", "istable": 1},
			{"name": "FCRM Settings", "module_app": "crm", "issingle": 1},
			{"name": "CRM Push Subscription", "module_app": "crm"},
			{"name": "Contact", "module_app": "frappe"},
			{"name": "User", "module_app": "frappe"},
			{"name": "Virtuale", "module_app": "crm", "is_virtual": 1},
		]
		self.assertEqual(R.da_esportare(tipi), ["CRM Lead", "Contact"])

	def test_un_nome_che_ogni_sistema_prende(self):
		self.assertEqual(R.nome_del_tipo("CRM Lead"), "crm-lead")
		self.assertEqual(R.nome_di_file("Rossi/Maria 1.pdf"), "Rossi_Maria_1.pdf")
		self.assertEqual(R.nome_di_file("../../etc/passwd"), "etc_passwd")
		self.assertEqual(R.nome_di_file(""), "senza-nome")
		self.assertEqual(
			R.percorso_del_file("CRM Lead", "CRM-LEAD-0001", "referto.pdf", "abc123def4567"),
			"file/crm-lead/CRM-LEAD-0001/abc123def456-referto.pdf",
		)
		self.assertTrue(R.percorso_del_file(None, None, "x.pdf", "f1").startswith("file/non-allegati/"))


class UnDocumentoNellArchivio(unittest.TestCase):
	def test_i_suoi_campi_e_le_sue_tabelle_senza_quelli_del_framework(self):
		record = {
			"name": "L1",
			"creation": datetime.datetime(2026, 10, 7, 9, 30),
			"owner": "a@example.com",
			"modified": datetime.datetime(2026, 10, 7, 10, 0),
			"modified_by": "a@example.com",
			"docstatus": 0,
			"_assign": "[]",
			"first_name": "Maria",
			"amount": decimal.Decimal("65.50"),
			"born": datetime.date(1980, 1, 2),
			"items": [{"name": "r1", "parent": "L1", "parenttype": "X", "idx": 1, "service": "Visita"}],
		}
		r = R.riga(record, ["first_name", "amount", "born", "items", "_assign"], {"items"})
		self.assertEqual(r["first_name"], "Maria")
		self.assertEqual(r["amount"], 65.5)
		self.assertEqual(r["born"], "1980-01-02")
		self.assertEqual(r["creation"], "2026-10-07T09:30:00")
		self.assertEqual(r["items"], [{"name": "r1", "service": "Visita"}])
		self.assertNotIn("_assign", r)
		self.assertNotIn("docstatus", r)
		# one record a line
		self.assertEqual(json.loads(R.jsonl([r]).splitlines()[0])["first_name"], "Maria")

	def test_la_tabella_si_apre_con_excel(self):
		testo = R.tabella(
			[{"name": "L1", "first_name": "Maria; Rosa", "items": [1, 2], "x": None}],
			["name", "first_name", "items", "x"],
		)
		self.assertTrue(testo.startswith("﻿name;first_name;items;x\r\n"))
		self.assertIn('L1;"Maria; Rosa";2;\r\n', testo)


if __name__ == "__main__":
	unittest.main()
