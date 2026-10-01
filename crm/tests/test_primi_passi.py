# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The first steps: each module's own, offered to whoever may take them, ticked by
the centre's data.

The manager has the centre's whole set-up; the front desk the first person and the
first appointment; with the clinic on, the first one is a patient. A step done
another way - a service written by hand - is done.
"""

from unittest import TestCase

import frappe
from frappe.tests import IntegrationTestCase

from crm import primi_passi
from crm.permissions import livelli, utenti
from crm.permissions.test_org_hierarchy import make_user
from crm.primi_passi import Passo, da_offrire

MANAGER = "steps.manager@example.com"
DESK = "steps.desk@example.com"


class AChiSiOffrono(TestCase):
	def test_a_chi_ha_una_delle_capacita_se_il_modulo_e_acceso(self):
		passi = [
			Passo("a", "A", "", lambda: True, ("x.uno",)),
			Passo("b", "B", "", lambda: False, ("x.due", "x.tre")),
			Passo("c", "C", "", lambda: False, ("x.uno",), modulo="spento"),
			Passo("d", "D", "", lambda: False, ("x.quattro",)),
		]
		offerti = da_offrire(
			passi, lambda nome: nome in {"x.uno", "x.tre"}, lambda modulo: modulo != "spento"
		)
		self.assertEqual([passo.chiave for passo in offerti], ["a", "b"])


class IPrimiPassi(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		piano = frappe.get_single("CRM Plan")
		piano.set("modules", [{"module": "clinica", "status": "Active"}])
		piano.save()
		livelli.dimentica_cache()
		utenti.sincronizza()
		for user, livello in ((MANAGER, "manager"), (DESK, "segreteria")):
			make_user(user)
			utenti.assegna_livelli(user, [livello])
		self.lingua = frappe.local.lang
		frappe.local.lang = "en"

	def tearDown(self):
		frappe.local.lang = self.lingua
		frappe.set_user("Administrator")
		livelli.dimentica_cache()

	def passi(self, user):
		frappe.set_user(user)
		livelli.dimentica_cache()
		return primi_passi.get_first_steps()

	def test_il_manager_ha_tutto_quello_che_mette_in_piedi_il_centro(self):
		fatto = self.passi(MANAGER)
		self.assertEqual(
			[passo["key"] for passo in fatto["steps"]],
			[
				"nome",
				"servizi",
				"orari",
				"colleghi",
				"moduli",
				"prenotazione",
				"email",
				"fatture",
				"persona",
				"appuntamento",
			],
		)
		self.assertEqual(fatto["total"], 10)
		self.assertEqual(fatto["done"], sum(passo["done"] for passo in fatto["steps"]))

	def test_senza_la_fatturazione_niente_passo_delle_fatture(self):
		frappe.set_user("Administrator")
		piano = frappe.get_single("CRM Plan")
		piano.append("modules", {"module": "fatturazione", "status": "Off"})
		piano.save()
		self.assertNotIn("fatture", [passo["key"] for passo in self.passi(MANAGER)["steps"]])

	def test_la_segreteria_ha_i_suoi(self):
		fatto = self.passi(DESK)
		self.assertEqual([passo["key"] for passo in fatto["steps"]], ["persona", "appuntamento"])

	def test_con_la_clinica_il_primo_e_un_paziente(self):
		[persona] = [passo for passo in self.passi(MANAGER)["steps"] if passo["key"] == "persona"]
		self.assertEqual(persona["title"], "Your first patient")
		self.assertEqual((persona["route"], persona["action"]), ("Leads", "new"))

	def test_un_passo_fatto_in_un_altro_modo_e_fatto(self):
		frappe.get_doc(
			{
				"doctype": "CRM Service",
				"service_name": "Prima visita dei primi passi",
				"enabled": 1,
				"bookable_online": 1,
				"duration": 30,
				"staff_selection": "Any one",
				"staff": [{"user": MANAGER}],
			}
		).insert(ignore_permissions=True)
		fatti = {passo["key"]: passo["done"] for passo in self.passi(MANAGER)["steps"]}
		self.assertTrue(fatti["servizi"])
		self.assertTrue(fatti["prenotazione"])

	def test_ogni_passo_porta_da_qualche_parte(self):
		for passo in primi_passi.passi():
			self.assertTrue(passo.pagina or passo.rotta, passo.chiave)
