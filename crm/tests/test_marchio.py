# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# See license.txt

"""The product's brand - the vertical's - and the centre's: one mark in each place
(`crm.marchio`).

The vertical the plan has on brings its brand: its name, icon, favicon and colours
are the product's on the framework's pages (the login page, the desk's title), in
the desk, on the phone's home screen. Where a person deals with the centre - the
top of the sidebar, the client area, the public pages - the centre's mark leads,
its logo drawn as it is (wide on its own, square beside its name), and the product
signs at the foot: never the two side by side. A patient never reads the
software's name where the centre's belongs.
"""

import json
import os
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
		del_framework = ("About", "Frappe Support")
		prima = self.aiuto()
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
		# the framework's about page and support link leave the desk's help menu;
		# the rest of it stays as the framework ships it, whatever it holds
		aiuto = self.aiuto()
		self.assertEqual(tuple(aiuto.get(voce) for voce in del_framework), (1, 1))
		self.assertEqual(
			{voce: nascosta for voce, nascosta in aiuto.items() if voce not in del_framework},
			{voce: nascosta for voce, nascosta in prima.items() if voce not in del_framework},
		)
		marchio.applica()
		self.assertEqual(frappe.db.get_single_value("Website Settings", "app_name"), marchio.nome())

	def test_i_codici_d_accesso_vengono_dal_prodotto(self):
		# an authenticator app shows the issuer beside its codes, the two-step
		# login's emails say it: never the framework's
		frappe.db.set_single_value("System Settings", "otp_issuer_name", "Frappe Framework")
		with con_il_verticale(PROVA.chiave):
			marchio.applica()
			self.assertEqual(frappe.db.get_single_value("System Settings", "otp_issuer_name"), PROVA.nome)
		marchio.applica()
		self.assertEqual(frappe.db.get_single_value("System Settings", "otp_issuer_name"), marchio.nome())
		# the centre's own name stays
		frappe.db.set_single_value("System Settings", "otp_issuer_name", "Centro Aurora")
		marchio.applica()
		self.assertEqual(frappe.db.get_single_value("System Settings", "otp_issuer_name"), "Centro Aurora")

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
		# the framework's tools are the desk's administration, never a second product
		self.assertEqual(
			[app["app_title"] for app in bootinfo.app_data],
			[frappe._("Administration"), PROVA.nome, "WhatsApp", "Helpdesk"],
		)
		self.assertEqual(
			[app.get("app_logo_url") for app in bootinfo.app_data[:2]],
			[marchio.ICONA_AMMINISTRAZIONE, PROVA.icona],
		)
		self.assertEqual(bootinfo.app_logo_url, PROVA.icona)

	def test_l_icona_del_framework_e_l_amministrazione(self):
		if not frappe.get_meta("Desktop Icon").has_field("icon_type"):
			self.skipTest("the desk's icons before Frappe 16.50")
		if not frappe.db.exists("Desktop Icon", {"icon_type": "App", "app": "frappe"}):
			frappe.get_doc(
				{
					"doctype": "Desktop Icon",
					"label": "Frappe Framework",
					"icon_type": "App",
					"app": "frappe",
					"link_type": "External",
					"link": "/desk",
				}
			).insert(ignore_permissions=True, ignore_links=True)
		marchio.applica()
		icona = frappe.db.get_value(
			"Desktop Icon", {"icon_type": "App", "app": "frappe"}, ["name", "label", "logo_url"], as_dict=True
		)
		self.assertEqual(
			(icona.name, icona.label, icona.logo_url),
			(marchio.AMMINISTRAZIONE, marchio.AMMINISTRAZIONE, marchio.ICONA_AMMINISTRAZIONE),
		)

	def test_il_desk_apre_il_crm_nel_guscio_del_prodotto(self):
		if not frappe.db.exists("DocType", "Sidebar"):
			self.skipTest("the desk's navigation before Frappe 16.50")
		# the app ships it: the desk's address of the CRM's module is the product's
		guscio = frappe.get_doc("Sidebar", marchio.SPAZIO)
		self.assertEqual((guscio.module, guscio.title, guscio.standard), ("FCRM", marchio.SPAZIO, 1))
		self.assertIn("CRM Lead", [riga.link_to for riga in guscio.items])

		# what the conversion of the old Workspace Sidebars made besides it
		frappe.flags.in_patch = True
		try:
			for titolo, modulo in (("Frappe CRM", "Invoicing"), ("Vendite", "FCRM")):
				frappe.get_doc(
					{"doctype": "Sidebar", "module": modulo, "title": titolo, "standard": 0}
				).insert(ignore_permissions=True, ignore_links=True)
		finally:
			frappe.flags.in_patch = False
		dock = None
		if frappe.db.exists("DocType", "Dock"):
			dock = frappe.get_doc(
				{
					"doctype": "Dock",
					"app": "crm",
					"user": "",
					"standard": 0,
					"items": [
						{"link_type": "Sidebar", "link_to": "FCRM", "title": "Frappe CRM", "icon": "x"},
						{"link_type": "Sidebar", "link_to": "Vendite", "title": "Vendite", "icon": "x"},
					],
				}
			).insert(ignore_permissions=True, ignore_links=True)

		marchio._navigazione_del_desk(marchio.attivo())

		self.assertFalse(frappe.db.exists("Sidebar", "Frappe CRM"))
		self.assertFalse(frappe.db.exists("Sidebar", "Vendite"))
		self.assertTrue(frappe.db.exists("Sidebar", marchio.SPAZIO))
		if dock:
			righe = frappe.get_doc("Dock", dock.name).items
			self.assertEqual(
				[(riga.link_to, riga.title) for riga in righe],
				[(marchio.SPAZIO, marchio.nome()), (marchio.SPAZIO, "Vendite")],
			)
			frappe.delete_doc("Dock", dock.name, force=True, ignore_permissions=True)

	def test_il_desk_si_apre_sulle_app_col_dock_di_dottorcloud(self):
		if not frappe.db.exists("DocType", "Dock"):
			self.skipTest("the desk's navigation before Frappe 16.50")
		# the app ships its rail: the product's shell first, then its modules
		dock = frappe.get_doc("Dock", "crm")
		self.assertEqual((dock.app, dock.standard), ("crm", 1))
		self.assertEqual((dock.items[0].link_type, dock.items[0].link_to), ("Sidebar", marchio.SPAZIO))
		moduli = set(frappe.get_all("Module Def", filters={"app_name": "crm"}, pluck="name"))
		self.assertLessEqual({riga.link_to for riga in dock.items[1:]}, moduli)

		# a site that kept the grid of icons opens on the apps, and is invited to nothing
		frappe.db.set_single_value("Desktop Settings", "desktop_page", "Desktop Icons")
		marchio.desktop_ad_app()
		self.assertEqual(frappe.db.get_single_value("Desktop Settings", "desktop_page"), "Apps")
		self.assertTrue(frappe.utils.cint(frappe.defaults.get_global_default("skip_new_navigation_prompt")))

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

	def test_i_dati_per_le_pagine_e_il_segno_del_centro(self):
		frappe.db.set_single_value(
			"FCRM Settings", {"brand_logo": "/files/aurora.png", "brand_name": "Centro Aurora"}
		)
		with con_il_verticale(PROVA.chiave):
			dati = marchio.per_le_pagine()
		self.assertEqual(
			(dati["name"], dati["icon"], dati["logo"], dati["logo_dark"], dati["favicon"]),
			(PROVA.nome, PROVA.icona, PROVA.logo, PROVA.logo_negativo, PROVA.favicon),
		)
		self.assertEqual(dati["touch_icon"], "/p/180.png")
		# the centre's mark: its logo, the logo's shape (no such file: not known), its name
		self.assertEqual(
			(dati["centre_logo"], dati["centre_logo_shape"], dati["centre_name"]),
			("/files/aurora.png", "", "Centro Aurora"),
		)
		self.assertEqual(dati["colors"]["--brand"], "#3355ff")
		# on light its darker shade under white words, on dark its own under dark ones
		self.assertEqual(dati["accent"]["light"]["--accent"], "#1a2fa0")
		self.assertEqual(dati["accent"]["light"]["--accent-ink"], "#ffffff")
		self.assertEqual(dati["accent"]["light"]["--accent-soft"], "#e8ecff")
		self.assertEqual(dati["accent"]["dark"]["--accent"], "#3355ff")
		# the centre's page gives its title, its logo and the logo's shape
		self.assertEqual(set(service_booking.page_branding({})), {"title", "logo", "logo_shape"})
		frappe.db.set_single_value("FCRM Settings", {"brand_logo": "", "brand_name": ""})

	# ------------------------------------------------------------ the logo's shape

	def test_la_forma_del_logo(self):
		# wide from one and a half times as wide as high: it carries the name
		for misure, forma in (
			((220, 60), "wide"),
			((150, 100), "wide"),
			((149, 100), "square"),
			((64, 64), "square"),
			((80, 120), "square"),
			((0, 60), ""),
			((None, None), ""),
			(("x", 3), ""),
		):
			self.assertEqual(marchio.forma_del_logo(*misure), forma, misure)

	def test_le_misure_di_un_svg(self):
		for testo, misure in (
			('<svg xmlns="http://www.w3.org/2000/svg" width="220" height="60">', (220, 60)),
			("<?xml version='1.0'?><svg viewBox='0,0,64,48'>", (64, 48)),
			# a size in percent says nothing: the viewBox does
			('<svg width="100%" height="100%" viewBox="0 0 300 100">', (300, 100)),
			# a stroke's width is not the drawing's
			('<svg stroke-width="2" width="48px" height="40px">', (48, 40)),
			("<svg><rect width='10' height='90'/></svg>", None),
			("not an svg", None),
		):
			self.assertEqual(marchio.misure_svg(testo), misure, testo)

	def test_le_misure_si_leggono_dai_file_del_sito(self):
		from PIL import Image

		cartella = frappe.get_site_path("public", "files")
		largo, quadrato = "prova-logo-largo.svg", "prova-logo-quadrato.png"
		with open(os.path.join(cartella, largo), "w") as file:
			file.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 60"></svg>')
		Image.new("RGB", (96, 90), "white").save(os.path.join(cartella, quadrato))
		try:
			self.assertEqual(marchio.misure_del_logo(f"/files/{largo}"), (220, 60))
			self.assertEqual(marchio.forma_di(f"/files/{largo}?v=2"), "wide")
			self.assertEqual(marchio.forma_di(f"/files/{quadrato}"), "square")
			# an address elsewhere, a file that is not there, a step out of the folder
			for url in (
				"https://example.com/logo.png",
				"/files/non-ce.png",
				"/files/../../site_config.json",
				"/files/%2e%2e/%2e%2e/site_config.json",
				"",
				None,
			):
				self.assertIsNone(marchio.misure_del_logo(url), url)
				self.assertEqual(marchio.forma_di(url), "", url)
		finally:
			os.remove(os.path.join(cartella, largo))
			os.remove(os.path.join(cartella, quadrato))

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

	def test_l_accesso_del_framework_ha_il_colore_del_marchio(self):
		# the framework drew its sign-in in its darkest gray, with fields an iPhone
		# zooms into; DottorCloud's own pages draw themselves
		accento = marchio.accento()["light"]["--accent"]
		utente = frappe.session.user
		frappe.set_user("Guest")
		try:
			pagine = {}
			for pagina in ("login", "prenota"):
				set_request(method="GET", path=f"/{pagina}")
				pagine[pagina] = get_response_without_exception_handling(f"/{pagina}").get_data(as_text=True)
		finally:
			frappe.set_user(utente)
		self.assertIn(f"--accent: {accento}", pagine["login"])
		self.assertIn("font-size: 16px !important", pagine["login"])
		# the button the framework draws now is a solid «es-button»: dressed too
		# (the simulation of a week found the sign-in black again after Frappe 16.50)
		if 'class="es-button' in pagine["login"]:
			self.assertIn('.es-button[data-variant="solid"]', pagine["login"])
		self.assertNotIn("font-size: 16px !important", pagine["prenota"])

	def test_il_rifiuto_del_framework_ha_il_colore_del_marchio(self):
		# «Not permitted» is the framework's message page drawn at the address it
		# refuses: its button was black at /crm
		from frappe.website.serve import get_response

		accento = marchio.accento()["light"]["--accent"]
		estraneo = "marchio.estraneo@example.com"
		if not frappe.db.exists("User", estraneo):
			frappe.get_doc(
				{"doctype": "User", "email": estraneo, "first_name": "Estraneo", "user_type": "Website User"}
			).insert(ignore_permissions=True)
		utente = frappe.session.user
		frappe.set_user(estraneo)
		try:
			set_request(method="GET", path="/crm")
			risposta = get_response("/crm")
		finally:
			frappe.set_user(utente)
		self.assertEqual(risposta.status_code, 403)
		self.assertIn(f"--accent: {accento}", risposta.get_data(as_text=True))

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

	def test_le_pagine_pubbliche_portano_il_centro_in_alto_e_il_marchio_in_fondo(self):
		frappe.db.set_single_value(
			"FCRM Settings", {"brand_logo": "/files/aurora.png", "brand_name": "Centro Aurora"}
		)
		app_name = frappe.db.get_single_value("Website Settings", "app_name")
		frappe.set_user("Guest")
		try:
			with con_il_verticale(PROVA.chiave):
				for pagina in ("prenota", "modulo", "documento", "area"):
					set_request(method="GET", path=f"/{pagina}")
					html = get_response_without_exception_handling(f"/{pagina}").get_data(as_text=True)
					self.assertIn(f'href="{PROVA.favicon}"', html, pagina)
					self.assertIn("Marchio di Prova", html, pagina)
					if pagina != "area":
						# the centre's logo at the top, the product's signature at the
						# foot, its colour; the product's logo nowhere beside the centre's
						self.assertIn('class="marchio-logo" src="/files/aurora.png"', html, pagina)
						self.assertLess(
							html.index("/files/aurora.png"), html.index('class="marchio-piede"'), pagina
						)
						self.assertIn(f'<img src="{PROVA.icona}" alt="" />', html, pagina)
						self.assertNotIn(f'src="{PROVA.logo}"', html, pagina)
						self.assertIn("--accent: #1a2fa0", html, pagina)
					self.assertNotIn("frappe-favicon", html, pagina)
				# the booking page names the centre in its title: the logo alone at the
				# top; the others put the name beside a logo that is not wide
				set_request(method="GET", path="/modulo")
				html = get_response_without_exception_handling("/modulo").get_data(as_text=True)
				self.assertIn('<span class="marchio-nome">Centro Aurora</span>', html)
				set_request(method="GET", path="/prenota")
				html = get_response_without_exception_handling("/prenota").get_data(as_text=True)
				self.assertNotIn('class="marchio-nome"', html)
				# a centre with neither a logo nor a name: the product's logo stands in
				# at the top, and the product does not sign twice
				frappe.db.set_single_value("FCRM Settings", {"brand_logo": "", "brand_name": ""})
				frappe.db.set_single_value("Website Settings", "app_name", PROVA.nome)
				set_request(method="GET", path="/modulo")
				html = get_response_without_exception_handling("/modulo").get_data(as_text=True)
				self.assertIn(f'class="marchio-prodotto" src="{PROVA.logo}"', html)
				self.assertNotIn('class="marchio-logo', html)
				self.assertNotIn('class="marchio-piede"', html)
				# the booking page names the centre in its title, and so still signs
				set_request(method="GET", path="/prenota")
				html = get_response_without_exception_handling("/prenota").get_data(as_text=True)
				self.assertNotIn('class="marchio-prodotto"', html)
				self.assertIn('class="marchio-piede"', html)
		finally:
			frappe.set_user("Administrator")
			frappe.db.set_single_value("FCRM Settings", {"brand_logo": "", "brand_name": ""})
			frappe.db.set_single_value("Website Settings", "app_name", app_name)
