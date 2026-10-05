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
from crm.fcrm.doctype.crm_plan.crm_plan import crediti_sdi
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
		self.assertEqual(plan.compresi(MODULI, None), {"base"})

	def test_la_base_comprende_quello_che_comprende(self):
		moduli = (ModuloPiano("base", "Base", comprende=("area",)), *MODULI[1:])
		self.assertEqual(plan.compresi(moduli, None), {"base", "area"})

	def test_un_verticale_che_nessuno_ha_registrato_non_aggiunge_niente(self):
		self.assertEqual(plan.compresi(MODULI, "altro"), {"base"})


class ICreditiSdI(TestCase):
	def test_uno_a_fattura_tre_alla_pa_niente_se_scartata(self):
		inviate = [
			("consegnata", "persona_fisica"),
			("inviato", "soggetto_iva"),
			("esito_pa", "pubblica_amministrazione"),
			("mancata_consegna", "persona_fisica"),
			# refused for its format, failed on the way, never sent: no credit
			("scartata", "soggetto_iva"),
			("errore", "persona_fisica"),
			("da_inviare", "persona_fisica"),
		]
		self.assertEqual(crediti_sdi(inviate, ricevute=4), 1 + 1 + 3 + 1 + 4)
		self.assertEqual(crediti_sdi([], 0), 0)


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

	def test_senza_la_clinica_l_area_c_e_lo_stesso(self):
		frappe.set_user("Administrator")
		piano = frappe.get_single("CRM Plan")
		piano.set("modules", [{"module": "area", "status": "Off"}])
		piano.save()
		livelli.dimentica_cache()
		frappe.set_user(MANAGER)
		area = self.moduli()["area"]
		# the base comprises it: a plan that says off does not take it away
		self.assertTrue(area["included"])
		self.assertEqual(area["state"], "active")
		self.assertIn("Base", area["comprised_by"])

	def test_gli_extra_si_provano(self):
		moduli = self.moduli()
		extra = {chiave for chiave, modulo in moduli.items() if not modulo["included"]}
		# the listino's extras (01/10/2026)
		self.assertEqual(extra, {"fatturazione", "marketing", "telefono", "assistente", "firma"})
		# invoicing was every site's before plans: on until the plan says otherwise
		self.assertEqual(moduli["fatturazione"]["state"], "active")
		# the assistant and the advanced signature are off until the centre wants them
		for chiave in ("assistente", "firma"):
			self.assertEqual(moduli[chiave]["state"], "off")
			self.assertTrue(moduli[chiave]["can_start_trial"])

	def test_la_taglia_conta_gli_ambulatori(self):
		frappe.set_user("Administrator")
		piano = frappe.get_single("CRM Plan")
		piano.size = "Solo"
		piano.save()
		prima = frappe.db.count("CRM Resource", {"resource_type": "Room", "enabled": 1})
		for nome in ("Ambulatorio 1 dei test", "Ambulatorio 2 dei test"):
			frappe.get_doc(
				{"doctype": "CRM Resource", "resource_name": nome, "resource_type": "Room"}
			).insert()
		# a machine is not an ambulatorio
		frappe.get_doc(
			{"doctype": "CRM Resource", "resource_name": "Ecografo dei test", "resource_type": "Equipment"}
		).insert()
		frappe.set_user(MANAGER)
		sale = plan.get_plan()["rooms"]
		self.assertEqual(sale, {"count": prima + 2, "included": 1, "over": True})

	def test_i_consumi_come_li_conta_il_listino(self):
		frappe.set_user("Administrator")
		piano = frappe.get_single("CRM Plan")
		piano.size = "Studio"
		piano.set(
			"modules",
			[
				{"module": "clinica", "status": "Active"},
				{"module": "telefono", "status": "Active"},
				{"module": "firma", "status": "Active"},
			],
		)
		piano.save()
		livelli.dimentica_cache()
		frappe.set_user(MANAGER)
		uso = plan.get_plan()["usage"]
		# WhatsApp is not counted, Meta bills the centre; nor calls and SMS,
		# Twilio bills them to whoever owns the account
		self.assertEqual(set(uso), {"sdi_credits", "signatures"})
		self.assertEqual(uso["sdi_credits"]["included"], 500)
		self.assertEqual(uso["signatures"]["included"], 2000)
		for voce in ("sdi_credits", "signatures"):
			self.assertIn("warn", uso[voce])
		# without invoicing there are no credits to count
		frappe.set_user("Administrator")
		piano.append("modules", {"module": "fatturazione", "status": "Off"})
		piano.save()
		livelli.dimentica_cache()
		frappe.set_user(MANAGER)
		self.assertIsNone(plan.get_plan()["usage"]["sdi_credits"])

	def test_ogni_modulo_dice_dove_si_imposta(self):
		moduli = self.moduli()
		self.assertEqual(moduli["telefono"]["settings"], ["Telephony", "Call Scripts"])
		self.assertEqual(moduli["area"]["settings"], ["News in the client area"])
		for chiave, modulo in moduli.items():
			self.assertTrue(modulo["settings"], f"{chiave} names no page to set it up")
