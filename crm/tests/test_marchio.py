# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# See license.txt

"""The product's brand - the vertical's - everywhere a person looks (`crm.marchio`).

The vertical the plan has on brings its brand: its name, icon, logo, favicon and
colours are the product's on the framework's pages (the login page, the desk's
title, the line under every public page), in the desk, on the phone's home
screen and on the public pages, where the centre's logo goes at most beside it.
A patient never reads the software's name where the centre's belongs.
"""

import json
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import set_request
from frappe.website.serve import get_response_without_exception_handling

from crm import marchio, verticali
from crm.api import service_booking
from crm.moduli import richieste

PROVA = marchio.Marchio(
	"prova",
	"Marchio di Prova",
	icona="/assets/crm/images/prova-icona.svg",
	logo="/assets/crm/images/prova-orizzontale.svg",
	logo_negativo="/assets/crm/images/prova-negativo.svg",
	favicon="/assets/crm/images/prova.png",
	colore="#3355ff",
	colore_scuro="#1a2fa0",
	colore_tenue="#e8ecff",
	colore_su_scuro="#8fa2ff",
	icone_telefono={"180": "/p/180.png", "192": "/p/192.png", "512": "/p/512.png"},
	descrizione="Il gestionale di prova",
)


def con_il_verticale(chiave_marchio):
	"""The site as if the plan had on a vertical wearing this brand."""
	return patch.object(
		verticali, "attiva", return_value=verticali.Verticale("prova", "prova", marchio=chiave_marchio)
	)


class TestMarchio(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		marchio.registra_marchio(PROVA)

	@classmethod
	def tearDownClass(cls):
		marchio._marchi.pop(PROVA.chiave, None)
		super().tearDownClass()

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

	# ------------------------------------------------------------ which brand

	def test_il_marchio_e_quello_del_verticale_acceso(self):
		with con_il_verticale(PROVA.chiave):
			self.assertEqual(marchio.attivo(), PROVA)
			self.assertEqual(marchio.nome(), "Marchio di Prova")
			self.assertEqual(marchio.con_nome("Apri {brand}"), "Apri Marchio di Prova")
		# no vertical, or one without a brand: the base's
		with patch.object(verticali, "attiva", return_value=None):
			self.assertEqual(marchio.attivo(), marchio.BASE)
		with con_il_verticale(None):
			self.assertEqual(marchio.attivo(), marchio.BASE)
		# a plan that cannot be read yet (install, a migration): the base's
		with patch.object(verticali, "attiva", side_effect=Exception("no plan")):
			self.assertEqual(marchio.attivo(), marchio.BASE)

	# ------------------------------------------------------------ the framework's settings

	def test_le_impostazioni_prendono_il_marchio_anche_sopra_un_altro_nome(self):
		# a name somebody wrote is not the product's: the product's is, everywhere
		frappe.db.set_single_value(
			"Website Settings", {"app_name": "Centro Aurora", "footer_powered": "Centro Aurora srl"}
		)
		frappe.db.set_single_value("System Settings", {"app_name": "", "disable_product_suggestion": 0})
		with con_il_verticale(PROVA.chiave):
			marchio.applica()
		for doctype in ("Website Settings", "System Settings"):
			self.assertEqual(frappe.db.get_single_value(doctype, "app_name"), PROVA.nome)
		self.assertEqual(frappe.db.get_single_value("Website Settings", "footer_powered"), PROVA.nome)
		self.assertEqual(frappe.db.get_single_value("Website Settings", "app_logo"), PROVA.icona)
		self.assertEqual(frappe.db.get_single_value("Website Settings", "favicon"), PROVA.favicon)
		self.assertEqual(frappe.db.get_single_value("Navbar Settings", "app_logo"), PROVA.icona)
		self.assertEqual(frappe.db.get_single_value("System Settings", "disable_product_suggestion"), 1)
		# the framework's about page and support link leave the desk's help menu
		aiuto = self.aiuto()
		self.assertEqual((aiuto.get("About"), aiuto.get("Frappe Support")), (1, 1))
		self.assertEqual(aiuto.get("Keyboard Shortcuts"), 0)
		marchio.applica()
		self.assertEqual(frappe.db.get_single_value("Website Settings", "app_name"), marchio.nome())

	def test_il_piano_che_cambia_riveste_il_framework(self):
		marchio.applica()
		with con_il_verticale(PROVA.chiave):
			marchio.piano_aggiornato()
			self.assertEqual(frappe.db.get_single_value("Website Settings", "app_name"), PROVA.nome)
		marchio.piano_aggiornato()
		self.assertEqual(frappe.db.get_single_value("Website Settings", "app_name"), marchio.nome())
		self.assertEqual(frappe.db.get_single_value("Website Settings", "favicon"), marchio.attivo().favicon)

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
		with con_il_verticale(PROVA.chiave):
			marchio.boot(bootinfo)
		self.assertEqual(
			[app["app_title"] for app in bootinfo.app_data],
			[PROVA.nome, PROVA.nome, "WhatsApp", "Helpdesk"],
		)
		self.assertEqual(bootinfo.app_data[0]["app_logo_url"], PROVA.icona)
		self.assertEqual(bootinfo.app_logo_url, PROVA.icona)

	def test_il_nome_del_software_non_e_quello_del_centro(self):
		for nome in ("", "Frappe", "frappe crm", "DottorCloud", "  dottorcloud "):
			self.assertEqual(marchio.nome_scelto(nome), "")
		self.assertEqual(marchio.nome_scelto(" Centro Aurora "), "Centro Aurora")
		# every brand registered is the software's, whichever is on
		self.assertEqual(marchio.nome_scelto("Marchio di prova"), "")

		frappe.db.set_single_value("FCRM Settings", "brand_name", "")
		frappe.db.set_single_value("Website Settings", "app_name", marchio.nome())
		self.assertEqual(richieste.nome_del_centro(), "")
		self.assertEqual(service_booking.page_title({}), "Book an appointment")
		frappe.db.set_single_value("FCRM Settings", "brand_name", "Centro Aurora")
		self.assertEqual(richieste.nome_del_centro(), "Centro Aurora")
		self.assertEqual(service_booking.page_title({}), "Centro Aurora")

	# ------------------------------------------------------------ what the pages read

	def test_i_dati_per_le_pagine_e_il_logo_del_centro_accanto(self):
		frappe.db.set_single_value("FCRM Settings", "brand_logo", "/files/aurora.png")
		with con_il_verticale(PROVA.chiave):
			dati = marchio.per_le_pagine()
		self.assertEqual(
			(dati["name"], dati["icon"], dati["logo"], dati["logo_dark"], dati["favicon"]),
			(PROVA.nome, PROVA.icona, PROVA.logo, PROVA.logo_negativo, PROVA.favicon),
		)
		self.assertEqual(dati["touch_icon"], "/p/180.png")
		self.assertEqual(dati["centre_logo"], "/files/aurora.png")
		self.assertEqual(dati["colors"]["--brand"], "#3355ff")
		# on light its darker shade under white words, on dark its own under dark ones
		self.assertEqual(dati["accent"]["light"]["--accent"], "#1a2fa0")
		self.assertEqual(dati["accent"]["light"]["--accent-ink"], "#ffffff")
		self.assertEqual(dati["accent"]["light"]["--accent-soft"], "#e8ecff")
		self.assertEqual(dati["accent"]["dark"]["--accent"], "#3355ff")
		# the centre's page gives only its title and its logo
		self.assertEqual(set(service_booking.page_branding({})), {"title", "logo"})
		frappe.db.set_single_value("FCRM Settings", "brand_logo", "")

	def test_dottorcloud_ha_i_colori_leggibili(self):
		accento = marchio.accento(marchio.DOTTORCLOUD)
		self.assertEqual(accento["light"]["--accent"], "#0b6f64")
		self.assertEqual(accento["light"]["--accent-ink"], "#ffffff")
		self.assertEqual(accento["dark"]["--accent"], "#12a594")
		self.assertEqual(accento["dark"]["--accent-ink"], "#111111")

	def test_le_pagine_del_framework_prendono_favicon_e_marchio(self):
		with con_il_verticale(PROVA.chiave):
			valori = marchio.contesto(frappe._dict())
		self.assertEqual(valori["favicon"], PROVA.favicon)
		self.assertEqual(valori["splash_image"], PROVA.icona)
		self.assertEqual(valori["marchio"]["name"], PROVA.nome)
		# a page that set its own keeps it
		proprio = marchio.per_le_pagine()
		self.assertIs(marchio.contesto(frappe._dict(marchio=proprio))["marchio"], proprio)

	def test_il_manifest_del_telefono_e_del_marchio(self):
		with con_il_verticale(PROVA.chiave):
			marchio.manifest(app="area")
		risposta = frappe.local.response
		self.assertEqual(risposta["content_type"], "application/manifest+json")
		dati = json.loads(risposta["filecontent"])
		self.assertEqual((dati["name"], dati["short_name"]), (PROVA.nome, PROVA.nome))
		self.assertEqual((dati["scope"], dati["start_url"]), ("/area", "/area"))
		self.assertIn(
			{"src": "/p/512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
			dati["icons"],
		)
		marchio.manifest()
		self.assertEqual(json.loads(frappe.local.response["filecontent"])["scope"], "/crm")

	def test_le_pagine_pubbliche_portano_il_marchio_e_il_logo_del_centro_accanto(self):
		frappe.db.set_single_value(
			"FCRM Settings", {"brand_logo": "/files/aurora.png", "brand_name": "Centro Aurora"}
		)
		frappe.set_user("Guest")
		try:
			with con_il_verticale(PROVA.chiave):
				for pagina in ("prenota", "modulo", "referto", "area"):
					set_request(method="GET", path=f"/{pagina}")
					html = get_response_without_exception_handling(f"/{pagina}").get_data(as_text=True)
					self.assertIn(f'href="{PROVA.favicon}"', html, pagina)
					self.assertIn("Marchio di Prova", html, pagina)
					if pagina != "area":
						# the product's logo, then the centre's beside it; its colour
						self.assertLess(html.index(PROVA.logo), html.index("/files/aurora.png"), pagina)
						self.assertIn("--accent: #1a2fa0", html, pagina)
					self.assertNotIn("frappe-favicon", html, pagina)
		finally:
			frappe.set_user("Administrator")
			frappe.db.set_single_value("FCRM Settings", {"brand_logo": "", "brand_name": ""})
