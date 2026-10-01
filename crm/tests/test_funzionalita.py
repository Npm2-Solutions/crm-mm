# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Settings > The centre > Features: what the product comprises, then the extras.

A centre that signed up for DottorCloud has the base and the clinic, with the
patient area the clinic comprises: on, nothing to switch, set up from the pages
each one names. Marketing, the phone and the assistant are extras: each says what
it adds, and one the centre does not have is tried for free.
"""

from unittest import TestCase

import frappe
from frappe.tests import IntegrationTestCase

from crm.api import plan
from crm.permissions import livelli, utenti
from crm.permissions.livelli import ModuloPiano
from crm.permissions.test_org_hierarchy import make_user

MANAGER = "features.manager@example.com"


MODULI = (
	ModuloPiano("base", "Base"),
	ModuloPiano("verticale", "Vertical", predefinito=False, comprende=("area",)),
	ModuloPiano("area", "Area", predefinito=False),
	ModuloPiano("extra", "Extra", predefinito=False),
)


class CosaComprendeIlProdotto(TestCase):
	def test_la_base_il_verticale_e_quello_che_comprende(self):
		self.assertEqual(plan.compresi(MODULI, "verticale"), {"base", "verticale", "area"})

	def test_senza_verticale_il_prodotto_e_la_base(self):
		# the area is an extra then, as any other
		self.assertEqual(plan.compresi(MODULI, None), {"base"})

	def test_un_verticale_che_nessuno_ha_registrato_non_aggiunge_niente(self):
		self.assertEqual(plan.compresi(MODULI, "altro"), {"base"})


class LaPaginaDelleFunzionalita(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		piano = frappe.get_single("CRM Plan")
		piano.set("modules", [{"module": "clinica", "status": "Active"}])
		piano.save()
		livelli.dimentica_cache()
		utenti.sincronizza()
		make_user(MANAGER)
		utenti.assegna_livelli(MANAGER, ["manager"])
		frappe.set_user(MANAGER)
		livelli.dimentica_cache()

	def tearDown(self):
		frappe.set_user("Administrator")
		livelli.dimentica_cache()

	def moduli(self):
		return {modulo["key"]: modulo for modulo in plan.get_plan()["modules"]}

	def test_con_la_clinica_il_prodotto_e_la_base_la_clinica_e_l_area(self):
		moduli = self.moduli()
		compresi = {chiave for chiave, modulo in moduli.items() if modulo["included"]}
		self.assertEqual(compresi, {"base", "clinica", "area"})
		# included is on: nothing to try
		for chiave in compresi:
			self.assertEqual(moduli[chiave]["state"], "active")
			self.assertFalse(moduli[chiave]["can_start_trial"])

	def test_gli_extra_si_provano(self):
		moduli = self.moduli()
		extra = {chiave for chiave, modulo in moduli.items() if not modulo["included"]}
		self.assertEqual(extra, {"marketing", "telefono", "assistente"})
		# the assistant is off until the centre wants it: the manager tries it
		self.assertEqual(moduli["assistente"]["state"], "off")
		self.assertTrue(moduli["assistente"]["can_start_trial"])

	def test_ogni_modulo_dice_dove_si_imposta(self):
		moduli = self.moduli()
		self.assertEqual(moduli["telefono"]["settings"], ["Telephony", "Call Scripts"])
		self.assertEqual(moduli["area"]["settings"], ["News in the client area"])
		for chiave, modulo in moduli.items():
			self.assertTrue(modulo["settings"], f"{chiave} names no page to set it up")
