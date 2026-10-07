# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""People brought over from the previous software: the sheet shown before
anything is written, nobody made twice, the billing details kept."""

import frappe
from frappe.tests import IntegrationTestCase

from crm.importazione import importa
from crm.permissions import livelli, utenti
from crm.permissions.test_org_hierarchy import make_user

MANAGER = "importa.manager@example.com"

FOGLIO = (
	"Cognome;Nome;Codice fiscale;Cellulare;E-mail;Note\n"
	"ROSSI;MARIA;RSSMRA80A41H501Y;333 765 4321;maria.importata@example.com;allergica al lattice\n"
	"Bianchi;Luca;;;luca.importato@example.com;\n"
	";;;;;solo una nota\n"
)


class LePersoneDalGestionaleDiPrima(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		utenti.sincronizza()
		make_user(MANAGER)
		utenti.assegna_livelli(MANAGER, ["manager"])
		livelli.dimentica_cache()
		frappe.cache.delete_value(importa.CHIAVE)
		# the job commits each person: what an earlier run left goes first
		for email in ("maria.importata@example.com", "luca.importato@example.com"):
			for nome in frappe.get_all("CRM Lead", filters={"email": email}, pluck="name"):
				frappe.db.delete("CRM Billing Profile", {"party_type": "CRM Lead", "party": nome})
				frappe.db.delete("FCRM Note", {"reference_docname": nome})
				frappe.delete_doc("CRM Lead", nome, force=True, ignore_permissions=True)
		# uploaded by whoever brings the people over: a private file of theirs
		frappe.set_user(MANAGER)
		self.file = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "pazienti.csv",
				"content": FOGLIO.encode("cp1252"),
				"is_private": 1,
			}
		).insert(ignore_permissions=True)
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.cache.delete_value(importa.CHIAVE)

	def test_prima_si_vede_poi_si_porta(self):
		# somebody already here, by email
		gia = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Luca",
				"last_name": "Bianchi",
				"email": "luca.importato@example.com",
			}
		).insert(ignore_permissions=True)

		frappe.set_user(MANAGER)
		visto = importa.preview(self.file.file_url)
		self.assertEqual(visto["total"], 3)
		self.assertEqual(visto["found"], 1)
		campi = {c["name"]: c["field"] for c in visto["columns"]}
		self.assertEqual(campi["Codice fiscale"], "fiscal_code")
		self.assertEqual(visto["rows"][0]["name"], "Maria Rossi")
		# nothing written yet
		self.assertFalse(frappe.db.exists("CRM Lead", {"email": "maria.importata@example.com"}))

		esito = importa.importa(self.file.file_url, MANAGER)
		self.assertEqual((esito["created"], esito["updated"], esito["skipped"]), (1, 1, 1))
		maria = frappe.db.get_value("CRM Lead", {"email": "maria.importata@example.com"}, "name")
		self.assertTrue(maria)
		self.assertEqual(frappe.db.get_value("CRM Lead", maria, "mobile_no"), "+393337654321")
		profilo = frappe.db.get_value(
			"CRM Billing Profile",
			{"party_type": "CRM Lead", "party": maria},
			["fiscal_code", "sex", "birth_date"],
			as_dict=True,
		)
		self.assertEqual(
			(profilo.fiscal_code, profilo.sex, str(profilo.birth_date)),
			("RSSMRA80A41H501Y", "F", "1980-01-01"),
		)
		self.assertTrue(frappe.db.exists("FCRM Note", {"reference_docname": maria}))
		# the same sheet again makes nobody twice
		esito = importa.importa(self.file.file_url, MANAGER)
		self.assertEqual(esito["created"], 0)
		self.assertEqual(frappe.db.count("CRM Lead", {"email": "luca.importato@example.com"}), 1)
		self.assertEqual(
			gia.name, frappe.db.get_value("CRM Lead", {"email": "luca.importato@example.com"}, "name")
		)

	def test_chi_non_importa_non_vede_il_foglio(self):
		make_user("importa.nessuno@example.com")
		frappe.set_user("importa.nessuno@example.com")
		with self.assertRaises(frappe.PermissionError):
			importa.preview(self.file.file_url)
