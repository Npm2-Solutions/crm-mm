# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# See license.txt

"""The product's name where the framework shows its own (`crm.marchio`).

A new site says "Frappe" on its login page, in the desk's title, under every
public page and in the desk's help menu: the settings take DottorCloud once, and a
name the centre wrote stays. The desk calls the apps by the product's name, and a
patient never reads the software's name where the centre's belongs.
"""

import frappe
from frappe.tests import IntegrationTestCase

from crm import marchio
from crm.api import service_booking
from crm.moduli import richieste


class TestMarchio(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def aiuto(self):
		return {
			riga.item_label: riga.hidden
			for riga in frappe.get_all(
				"Navbar Item",
				filters={"parent": "Navbar Settings", "parentfield": "help_dropdown"},
				fields=["item_label", "hidden"],
			)
		}

	def test_le_impostazioni_prendono_il_nome_del_prodotto(self):
		frappe.db.set_single_value("Website Settings", {"app_name": "Frappe", "footer_powered": ""})
		frappe.db.set_single_value("System Settings", {"app_name": "", "disable_product_suggestion": 0})
		marchio.applica()
		self.assertEqual(frappe.db.get_single_value("Website Settings", "app_name"), marchio.NOME)
		self.assertEqual(frappe.db.get_single_value("System Settings", "app_name"), marchio.NOME)
		self.assertEqual(frappe.db.get_single_value("Website Settings", "footer_powered"), marchio.NOME)
		self.assertEqual(frappe.db.get_single_value("System Settings", "disable_product_suggestion"), 1)
		# the framework's about page and support link leave the desk's help menu
		aiuto = self.aiuto()
		self.assertEqual((aiuto.get("About"), aiuto.get("Frappe Support")), (1, 1))
		self.assertEqual(aiuto.get("Keyboard Shortcuts"), 0)

	def test_quello_che_il_centro_ha_scritto_resta(self):
		frappe.db.set_single_value(
			"Website Settings", {"app_name": "Centro Aurora", "footer_powered": "Centro Aurora srl"}
		)
		marchio.applica()
		self.assertEqual(frappe.db.get_single_value("Website Settings", "app_name"), "Centro Aurora")
		self.assertEqual(
			frappe.db.get_single_value("Website Settings", "footer_powered"), "Centro Aurora srl"
		)

	def test_la_scrivania_chiama_le_app_col_nome_del_prodotto(self):
		bootinfo = frappe._dict(
			app_data=[
				{"app_name": "frappe", "app_title": "Frappe Framework", "app_logo_url": "x"},
				{"app_name": "crm", "app_title": "Frappe CRM", "app_logo_url": "y"},
				{"app_name": "frappe_whatsapp", "app_title": "Frappe Whatsapp"},
				{"app_name": "altro", "app_title": "Frappe Helpdesk"},
			],
			app_logo_url="/assets/frappe/images/frappe-framework-logo.svg",
		)
		marchio.boot(bootinfo)
		self.assertEqual(
			[app["app_title"] for app in bootinfo.app_data],
			[marchio.NOME, marchio.NOME, "WhatsApp", "Helpdesk"],
		)
		self.assertEqual(bootinfo.app_data[0]["app_logo_url"], marchio.ICONA)
		self.assertEqual(bootinfo.app_logo_url, marchio.ICONA)

	def test_il_nome_del_software_non_e_quello_del_centro(self):
		for nome in ("", "Frappe", "frappe crm", "DottorCloud", "  dottorcloud "):
			self.assertEqual(marchio.nome_scelto(nome), "")
		self.assertEqual(marchio.nome_scelto(" Centro Aurora "), "Centro Aurora")

		frappe.db.set_single_value("FCRM Settings", "brand_name", "")
		frappe.db.set_single_value("Website Settings", "app_name", marchio.NOME)
		self.assertEqual(richieste.nome_del_centro(), "")
		self.assertEqual(service_booking.page_title({}), "Book an appointment")
		frappe.db.set_single_value("FCRM Settings", "brand_name", "Centro Aurora")
		self.assertEqual(richieste.nome_del_centro(), "Centro Aurora")
		self.assertEqual(service_booking.page_title({}), "Centro Aurora")
