# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The product's brand - the vertical's - everywhere a person looks.

A vertical switched on by the plan brings its brand (`crm.verticali`): the clinic
DottorCloud. Its name, icon, logo, favicon and colours are the product's in every
place: DottorCloud's pages and the client area, the public pages (booking, forms,
reports), the framework's own (the login page, the desk, the emails), the phone's
home screen. A centre's own logo goes at most beside it (Settings > General > Name & logo); it never
takes its place. Without a vertical the base's brand speaks (`BASE`).

- **Where it is read**: `attivo()`, on the server; the boots of DottorCloud's page
  and of the area (`per_il_boot`), the public pages (`per_le_pagine`), the phone's
  manifest (`manifest`); the framework's settings, written by `applica()` at install,
  by the patch, and again whenever the plan changes (`piano_aggiornato`), and its web
  pages through `contesto` (the `update_website_context` hook).
- **Its words**: a string that names the product says `{brand}`, and the pages put
  the brand's name there; the server passes `nome()`.

The framework's own: the desk names the apps after the hooks' titles (`boot`), its
help menu links to the framework's support, its workspace was named after the old
product - `applica` takes care of them once. The notices the licence asks for stay:
the copyright lines in the sources and the licence file.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import frappe
from frappe import _lt


@dataclass(frozen=True)
class Marchio:
	chiave: str
	nome: str
	#: The app's icon, square: the sidebar, the desk, the login page.
	icona: str
	#: The horizontal logo, on light and on dark backgrounds.
	logo: str
	logo_negativo: str
	#: The browser tab's icon.
	favicon: str
	#: The brand's colour; darker, for pressed buttons and words on its tint; its
	#: soft tint; the colour it takes on dark backgrounds.
	colore: str
	colore_scuro: str
	colore_tenue: str
	colore_su_scuro: str
	#: The phone's home screen: its icons by size (the maskable ones for Android).
	icone_telefono: dict[str, str] = field(default_factory=dict)
	#: The phone's splash screens are named after their size in this folder.
	schermate_avvio: str = ""
	#: One line: the phone's install sheet, the About.
	descrizione: str = ""


DOTTORCLOUD = Marchio(
	"dottorcloud",
	"DottorCloud",
	icona="/assets/crm/images/dottorcloud-icona.svg",
	logo="/assets/crm/images/dottorcloud-orizzontale.svg",
	logo_negativo="/assets/crm/images/dottorcloud-orizzontale-negativo.svg",
	favicon="/assets/crm/images/favicon.png",
	colore="#12a594",
	colore_scuro="#0b6f64",
	colore_tenue="#e1f5f1",
	colore_su_scuro="#5fe0cc",
	icone_telefono={
		"180": "/assets/crm/manifest/apple-icon-180.png",
		"192": "/assets/crm/manifest/manifest-icon-192.maskable.png",
		"512": "/assets/crm/manifest/manifest-icon-512.maskable.png",
	},
	schermate_avvio="/assets/crm/manifest",
	descrizione="Il gestionale per i centri medici",
)

#: The base's brand, where no vertical is on. NPM2 has not chosen one yet: until it
#: does, the first vertical's speaks for the base too.
BASE = DOTTORCLOUD

_marchi: dict[str, Marchio] = {DOTTORCLOUD.chiave: DOTTORCLOUD}


def registra_marchio(marchio: Marchio) -> None:
	_marchi[marchio.chiave] = marchio


def marchi() -> list[Marchio]:
	return list(_marchi.values())


def attivo() -> Marchio:
	"""The brand of the vertical this site's plan has on, or the base's."""
	from crm import verticali

	try:
		verticale = verticali.attiva()
	except Exception:
		# before the plan exists (install, a migration): the base's
		verticale = None
	chiave = getattr(verticale, "marchio", None) if verticale else None
	return _marchi.get(chiave, BASE) if chiave else BASE


def nome() -> str:
	return attivo().nome


def con_nome(testo) -> str:
	"""A sentence that names the product says "{brand}": here it gets the brand's
	name. Before any `.format()`, which would take "{brand}" for its own."""
	return str(testo).replace("{brand}", nome())


#: The framework's name where a setting falls back to it.
NOMI_DEL_FRAMEWORK = ("", "Frappe", "Frappe Framework")

#: The framework's own words that name it, in the app's catalogue so that each
#: language says them with the product's name (`locale/*.po`, English in `en.po`):
#: the desk's light theme, and the welcome of an onboarding without a title.
PAROLE_DEL_FRAMEWORK = (_lt("Frappe Light"), _lt("Welcome to Frappe!"))

VECCHIO_SPAZIO = "Frappe CRM"
#: The desk's own tools (users, settings, printing) under a gear, not the framework's logo.
ICONA_AMMINISTRAZIONE = "/assets/crm/images/amministrazione.svg"
#: The desk's workspace of the product, as the app ships it.
SPAZIO = "DottorCloud"


def nome_scelto(nome: str | None) -> str:
	"""A name a centre chose for itself, or empty where it is the software's own:
	a patient must not read the product's name where the centre's belongs."""
	nome = (nome or "").strip()
	software = {n.lower() for n in NOMI_DEL_FRAMEWORK} | {"frappe crm"} | {m.nome.lower() for m in marchi()}
	return "" if nome.lower() in software else nome


# ------------------------------------------------------------------ what the pages read


def colori(marchio: Marchio | None = None) -> dict[str, str]:
	"""The brand's colours as the pages' CSS variables."""
	marchio = marchio or attivo()
	return {
		"--brand": marchio.colore,
		"--brand-strong": marchio.colore_scuro,
		"--brand-soft": marchio.colore_tenue,
		"--brand-on-dark": marchio.colore_su_scuro,
	}


def accento(marchio: Marchio | None = None) -> dict[str, dict[str, str]]:
	"""The public pages' accent - their buttons, what is chosen, the steps - in the
	brand's colours: on light its darker shade under white words (the lighter one is
	under the 4.5:1 contrast of text), on dark the lighter one under dark words."""
	from crm.scheduling.branding import accent_vars

	marchio = marchio or attivo()
	chiaro = {
		**accent_vars(marchio.colore_scuro),
		"--accent-soft": marchio.colore_tenue,
		"--accent-hover": f"color-mix(in srgb, {marchio.colore_scuro} 86%, black)",
	}
	scuro = {
		**accent_vars(marchio.colore),
		"--accent-soft": f"color-mix(in srgb, {marchio.colore} 22%, transparent)",
		"--accent-hover": f"color-mix(in srgb, {marchio.colore} 86%, white)",
	}
	return {"light": chiaro, "dark": scuro}


def logo_del_centro() -> str:
	"""The centre's own logo (Settings > General > Name & logo): at most beside the product's."""
	return frappe.db.get_single_value("FCRM Settings", "brand_logo") or ""


def _dati(marchio: Marchio, logo_centro: str = "") -> dict:
	return {
		"key": marchio.chiave,
		"name": marchio.nome,
		"icon": marchio.icona,
		"logo": marchio.logo,
		"logo_dark": marchio.logo_negativo,
		"favicon": marchio.favicon,
		"description": marchio.descrizione,
		"colors": colori(marchio),
		"touch_icon": marchio.icone_telefono.get("180") or marchio.icona,
		"centre_logo": logo_centro,
	}


def per_il_boot() -> dict:
	"""What DottorCloud's page and the area need of the brand, and the centre's logo
	that goes beside it."""
	return _dati(attivo(), logo_del_centro())


def per_le_pagine() -> dict:
	"""The public pages' branding: the product's name, icon, logo, favicon, colours
	and accent (`accento`), and the centre's logo beside them. Never raises: a page
	without it still opens, in the base's brand."""
	try:
		marchio = attivo()
		dati = _dati(marchio, logo_del_centro())
	except Exception:
		marchio = BASE
		dati = _dati(marchio)
	dati["accent"] = accento(marchio)
	return dati


def contesto(context) -> dict:
	"""`update_website_context`: every web page - the framework's (the login page,
	the portal, the errors) and the CRM's public ones - with the brand's favicon and
	splash, and `marchio` for the pages that draw its marks
	(`templates/includes/marchio_*.html`)."""
	dati = context.get("marchio") or per_le_pagine()
	return {"favicon": dati["favicon"], "splash_image": dati["icon"], "marchio": dati}


# nosemgrep: guest-whitelisted-method — the brand's public manifest, nothing about anybody
@frappe.whitelist(allow_guest=True, methods=["GET"])
def manifest(app: str = "crm") -> None:
	"""The phone's manifest, in the brand of the vertical that is on: its name, its
	icons, its colour. DottorCloud's page and the area link here."""
	marchio = attivo()
	ambito = "/area" if app == "area" else "/crm"
	icone = []
	for misura in ("192", "512"):
		icona = marchio.icone_telefono.get(misura)
		if icona:
			for scopo in ("any", "maskable"):
				icone.append(
					{"src": icona, "sizes": f"{misura}x{misura}", "type": "image/png", "purpose": scopo}
				)
	dati = {
		"name": marchio.nome,
		"short_name": marchio.nome,
		"description": marchio.descrizione,
		"display": "standalone",
		# both, and matching: without a scope the browser works one out from where
		# the manifest is served, and then refuses a start url outside it
		"scope": ambito,
		"start_url": ambito,
		"lang": (frappe.local.lang or "it")[:2],
		"theme_color": "#ffffff",
		"background_color": "#ffffff",
		"icons": icone,
	}
	frappe.local.response.update(
		{
			"type": "download",
			"filename": "manifest.webmanifest",
			"filecontent": json.dumps(dati, ensure_ascii=False),
			"content_type": "application/manifest+json",
			"display_content_as": "inline",
		}
	)


# ------------------------------------------------------------------ the framework's own


def boot(bootinfo) -> None:
	"""`extend_bootinfo`: the desk's sidebar names the app a page belongs to by its
	hooks' title - "Frappe Framework" for users and settings - and draws its logo."""
	marchio = attivo()
	titoli = {"frappe": marchio.nome, "crm": marchio.nome, "frappe_whatsapp": "WhatsApp"}
	for app in bootinfo.get("app_data") or []:
		titolo = titoli.get(app.get("app_name"))
		if titolo:
			app["app_title"] = titolo
		elif "Frappe" in (app.get("app_title") or ""):
			app["app_title"] = app["app_title"].replace("Frappe", "").strip() or marchio.nome
		if app.get("app_name") in ("frappe", "crm"):
			app["app_logo_url"] = marchio.icona
	# the desk's own logo is the brand's, whatever the hooks or a third app say
	bootinfo["app_logo_url"] = marchio.icona


def applica() -> None:
	"""The framework's settings in the brand of the vertical that is on: at install,
	by the patch, and whenever the plan changes."""
	marchio = attivo()
	_nome_e_piede(marchio)
	_loghi(marchio)
	_senza_suggerimenti()
	_aiuto_senza_il_framework()
	_scrivania(marchio)
	_autori()
	frappe.clear_cache()


def piano_aggiornato(doc=None, method=None) -> None:
	"""The plan changed: a vertical switched on or off changes the brand, and the
	framework's settings follow it."""
	if (frappe.db.get_single_value("Website Settings", "app_name") or "") != nome():
		applica()


def _nome_e_piede(marchio: Marchio) -> None:
	# the name the login page, the desk's title and the emails' "Log in to" say, and
	# the line under every public page: the product's, always
	for doctype in ("Website Settings", "System Settings"):
		frappe.db.set_single_value(doctype, "app_name", marchio.nome)
	frappe.db.set_single_value("Website Settings", "footer_powered", marchio.nome)


def _loghi(marchio: Marchio) -> None:
	# the login page's and the desk's logo (`get_app_logo` reads these first), the
	# favicon and the splash of every page the framework serves
	frappe.db.set_single_value(
		"Website Settings",
		{"app_logo": marchio.icona, "favicon": marchio.favicon, "splash_image": marchio.icona},
	)
	frappe.db.set_single_value("Navbar Settings", "app_logo", marchio.icona)


def _senza_suggerimenti() -> None:
	# the desk's sidebar advertises the framework's other products to System Managers
	frappe.db.set_single_value("System Settings", "disable_product_suggestion", 1)


def _aiuto_senza_il_framework() -> None:
	"""The desk's help menu: its "About" is the framework's page, its support link
	the framework's support. Both hidden; shortcuts and system health stay."""
	for riga in frappe.get_all(
		"Navbar Item",
		filters={"parent": "Navbar Settings", "parentfield": "help_dropdown", "hidden": 0},
		fields=["name", "item_label", "route", "action"],
	):
		if "frappe.io" in (riga.route or "") or "show_about" in (riga.action or ""):
			frappe.db.set_value("Navbar Item", riga.name, "hidden", 1)


def _scrivania(marchio: Marchio) -> None:
	"""The desk's desktop and sidebar: the CRM's workspace, its sidebar and its
	app icon were named after the old product; they say the brand's name, and the
	framework's app icon is a gear."""
	if frappe.db.exists("Workspace", VECCHIO_SPAZIO):
		# the new one comes with the app (fcrm/workspace/dottorcloud)
		if frappe.db.exists("Workspace", SPAZIO):
			frappe.delete_doc("Workspace", VECCHIO_SPAZIO, force=True, ignore_permissions=True)
		else:
			frappe.rename_doc("Workspace", VECCHIO_SPAZIO, SPAZIO, force=True)
	if frappe.db.exists("Workspace", SPAZIO):
		frappe.db.set_value("Workspace", SPAZIO, {"label": marchio.nome, "title": marchio.nome})

	if frappe.db.exists("DocType", "Workspace Sidebar") and frappe.db.exists(
		"Workspace Sidebar", VECCHIO_SPAZIO
	):
		if frappe.db.exists("Workspace Sidebar", SPAZIO):
			frappe.delete_doc("Workspace Sidebar", VECCHIO_SPAZIO, force=True, ignore_permissions=True)
		else:
			frappe.rename_doc("Workspace Sidebar", VECCHIO_SPAZIO, SPAZIO, force=True)
		# its first item opens the workspace by name
		frappe.db.set_value(
			"Workspace Sidebar Item",
			{"parent": SPAZIO, "link_type": "Workspace", "link_to": VECCHIO_SPAZIO},
			"link_to",
			SPAZIO,
		)
	if frappe.db.exists("DocType", "Workspace Sidebar") and frappe.db.exists("Workspace Sidebar", SPAZIO):
		frappe.db.set_value("Workspace Sidebar", SPAZIO, "title", marchio.nome)

	if frappe.db.exists("DocType", "Desktop Icon"):
		if frappe.db.exists("Desktop Icon", VECCHIO_SPAZIO):
			if frappe.db.exists("Desktop Icon", SPAZIO):
				frappe.delete_doc("Desktop Icon", VECCHIO_SPAZIO, force=True, ignore_permissions=True)
			else:
				frappe.rename_doc("Desktop Icon", VECCHIO_SPAZIO, SPAZIO, force=True)
		if frappe.db.exists("Desktop Icon", SPAZIO):
			frappe.db.set_value("Desktop Icon", SPAZIO, {"logo_url": marchio.icona, "label": marchio.nome})
		for icona in frappe.get_all(
			"Desktop Icon", filters={"logo_url": ["like", "%frappe-framework%"]}, pluck="name"
		):
			frappe.db.set_value("Desktop Icon", icona, "logo_url", ICONA_AMMINISTRAZIONE)
		frappe.cache.delete_key("desktop_icons")
		frappe.cache.delete_key("bootinfo")


def _autori() -> None:
	"""The desk shows who created and last changed a DocType: some of the CRM's came
	with the old product's authors' addresses."""
	for campo in ("owner", "modified_by"):
		frappe.db.sql(
			f"""update `tabDocType` set `{campo}` = 'Administrator'
			where `{campo}` like %s and module in (select name from `tabModule Def` where app_name = 'crm')""",
			("%@frappe.io",),
		)
