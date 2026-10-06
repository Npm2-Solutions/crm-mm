# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What the lists offer to filter, sort, group by and show as a column, on the
documents DottorCloud keeps: each field once, told apart, never what only the
machine reads, never what the session cannot read."""

from collections import Counter
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.api import doc as D
from crm.liste import campi as C
from crm.liste import regole as R

LISTE = ("CRM Lead", "CRM Deal", "CRM Organization", "Contact", "CRM Task", "FCRM Note", "CRM Call Log")


class LeScelteDelleListe(IntegrationTestCase):
	def setUp(self):
		self.lingua_di_prima = frappe.local.lang

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.local.lang = self.lingua_di_prima

	def test_ogni_campo_una_volta_e_con_un_nome_suo(self):
		for doctype in LISTE:
			for uso in R.USI:
				scelti = C.della_lista(doctype, uso)
				ripetuti = [n for n, quanti in Counter(s["label"] for s in scelti).items() if quanti > 1]
				self.assertFalse(ripetuti, f"{doctype} {uso}: {ripetuti}")
				nomi = [s["fieldname"] for s in scelti]
				self.assertEqual(len(nomi), len(set(nomi)), f"{doctype} {uso}")

	def test_mai_quello_della_macchina(self):
		for doctype in LISTE:
			togli = R.DELLA_MACCHINA | C.SOLO_PER_LA_MACCHINA.get(doctype, frozenset())
			for uso in R.USI:
				offerti = {s["fieldname"] for s in C.della_lista(doctype, uso)}
				self.assertFalse(offerti & togli, f"{doctype} {uso}: {offerti & togli}")

	def test_una_persona_si_raggruppa_per_rapporto_e_stato(self):
		gruppi = {s["fieldname"]: s for s in D.get_group_by_fields("CRM Lead")}
		self.assertIn("relationship", gruppi)
		self.assertIn("status", gruppi)
		self.assertIn("owner", gruppi)
		# never a moment to the second, an amount, whom it is assigned to
		for fuori in ("creation", "modified", "annual_revenue", "_assign", "client_since"):
			self.assertNotIn(fuori, gruppi)

	def test_i_due_contatti_si_distinguono(self):
		frappe.local.lang = "it"
		filtri = {s["fieldname"]: s["label"] for s in D.get_filterable_fields("CRM Lead")}
		self.assertEqual(filtri["source"], "Sorgente")
		self.assertEqual(filtri["first_touch_source"], "Sorgente (Primo contatto)")
		self.assertEqual(filtri["last_touch_source"], "Sorgente (Ultimo contatto)")
		self.assertEqual(filtri["owner"], "Creato da")

	def test_le_forme_che_le_liste_leggono(self):
		ordine = D.sort_options("CRM Deal")
		self.assertTrue(all(s["value"] == s["fieldname"] for s in ordine))
		self.assertNotIn("name", {s["fieldname"] for s in ordine})
		filtri = D.get_filterable_fields("CRM Task")
		self.assertTrue(all(s["name"] == s["value"] == s["fieldname"] for s in filtri))
		# a task's own «Assigned To», once
		self.assertIn("assigned_to", {s["fieldname"] for s in filtri})
		self.assertNotIn("_assign", {s["fieldname"] for s in filtri})
		colonne = {s["fieldname"]: s for s in D.get_list_fields("CRM Lead")}
		self.assertIn("_liked_by", colonne)
		self.assertTrue(all(s["value"] == s["fieldname"] for s in colonne.values()))

	def test_quello_che_un_filtro_non_prende_resta_fuori(self):
		# the controller's own word: whether a person has a deal is not a filter
		self.assertNotIn("converted", {s["fieldname"] for s in D.get_filterable_fields("CRM Lead")})
		self.assertIn("converted", {s["fieldname"] for s in D.get_group_by_fields("CRM Lead")})

	def test_mai_quello_che_la_sessione_non_legge(self):
		campi = [
			frappe._dict(fieldname="first_name", fieldtype="Data", label="First Name", permlevel=0),
			frappe._dict(fieldname="agency_key", fieldtype="Data", label="Agency Key", permlevel=1),
		]
		finto = frappe._dict(fields=campi, istable=0, get_permlevel_access=lambda permission_type: [0])
		frappe.set_user("Guest")
		with patch.object(C.frappe, "get_meta", return_value=finto):
			offerti = {s["fieldname"] for s in C.della_lista("CRM Lead", "filtro")}
		self.assertIn("first_name", offerti)
		self.assertNotIn("agency_key", offerti)

	def test_il_gruppo_si_intitola_come_la_lista_lo_offre(self):
		frappe.local.lang = "it"
		dati = D.get_data(
			doctype="CRM Lead",
			filters={},
			order_by="modified desc",
			page_length=1,
			view={"view_type": "group_by", "group_by_field": "owner"},
		)
		self.assertEqual(dati["group_by_field"]["label"], "Creato da")

	def test_la_scheda_offre_anche_le_tabelle_e_mai_i_codici(self):
		scheda = {s["fieldname"]: s for s in D.get_list_fields("Contact", "scheda")}
		self.assertIn("email_ids", scheda)
		self.assertNotIn("google_contacts_id", scheda)
		self.assertNotIn("owner", scheda)
		# an unknown use reads as the columns'
		self.assertEqual(D.get_list_fields("Contact", "altro"), D.get_list_fields("Contact"))
