# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The product's brand - the vertical's - and the centre's: one mark in each place.

A vertical switched on by the plan brings its brand (`crm.verticali`): the clinic
DottorCloud. Its name, icon, favicon and colours are the product's everywhere: the
tab of every page, the framework's own (the login page, the desk, the emails), the
phone's home screen, the PDFs' producer. Where a person deals with the centre - the
top of DottorCloud's sidebar, the client area, the public pages (booking, forms,
documents) - the centre's own mark leads (Settings > The centre > General > Name &
logo): its logo as it is drawn, wide on its own or square beside its name
(`forma_del_logo`), or its name alone; the product signs at the foot, "Powered by
DottorCloud". The two never stand side by side. A centre with neither a logo nor a
name has the product's logo in their place. Without a vertical the base's brand
speaks (`BASE`).

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
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote

import frappe
from frappe import _, _lt


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
	#: The emails' marks, as PNG (no mail client shows an SVG everywhere): the
	#: horizontal logo, 56px high for 28px, and the icon, 48px for 24px.
	logo_email: str = ""
	icona_email: str = ""


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
	logo_email="/assets/crm/images/email/dottorcloud-orizzontale.png",
	icona_email="/assets/crm/images/email/dottorcloud-icona.png",
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
#: What the framework's own app is called in the desk: its tools, the desk's administration.
AMMINISTRAZIONE = "Administration"
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
	"""The centre's own logo (Settings > The centre > General > Name & logo)."""
	return frappe.db.get_single_value("FCRM Settings", "brand_logo") or ""


#: A logo this many times wider than high is drawn on its own, wide: it carries the
#: centre's name. Below it, square, it goes beside the name. As `utils/marchio.js`.
LARGO = 1.5


def forma_del_logo(larghezza, altezza) -> str:
	"""How a logo is drawn: "wide" on its own, "square" beside the centre's name; ""
	when its size is not known, and then it goes beside the name, which is never lost."""
	try:
		larghezza, altezza = float(larghezza or 0), float(altezza or 0)
	except (TypeError, ValueError):
		return ""
	if larghezza <= 0 or altezza <= 0:
		return ""
	return "wide" if larghezza >= LARGO * altezza else "square"


def misure_svg(testo: str) -> tuple[float, float] | None:
	"""An SVG's width and height: its own, in pixels, else its viewBox's."""
	radice = re.search(r"<svg\b[^>]*>", testo or "", re.IGNORECASE)
	if not radice:
		return None
	tag = radice.group(0)

	def misura(nome: str) -> float | None:
		trovata = re.search(rf"""\s{nome}\s*=\s*["']\s*([\d.]+)\s*(?:px)?\s*["']""", tag)
		return float(trovata.group(1)) if trovata else None

	larghezza, altezza = misura("width"), misura("height")
	if larghezza and altezza:
		return larghezza, altezza
	vista = re.search(r"""viewBox\s*=\s*["']([^"']+)["']""", tag, re.IGNORECASE)
	numeri = re.split(r"[\s,]+", vista.group(1).strip()) if vista else []
	try:
		return (float(numeri[2]), float(numeri[3])) if len(numeri) == 4 else None
	except ValueError:
		return None


def misure_del_logo(url: str | None) -> tuple[float, float] | None:
	"""A logo's width and height, from the file the site keeps: the head of an image,
	the size of an SVG. None for an address elsewhere, or a file it cannot read."""
	percorso = _file_del_sito(url)
	if not percorso:
		return None
	try:
		if percorso.suffix.lower() == ".svg":
			# nosemgrep: frappe-security-file-traversal — a file of the site's own folders, resolved inside them
			with open(percorso, encoding="utf-8", errors="ignore") as file:
				return misure_svg(file.read(16384))
		from PIL import Image

		with Image.open(percorso) as immagine:
			return immagine.size
	except Exception:
		return None


def forma_di(url: str | None) -> str:
	"""The shape of the logo at an address: "wide", "square" or "" (`forma_del_logo`)."""
	return forma_del_logo(*(misure_del_logo(url) or (0, 0))) if url else ""


def _file_del_sito(url: str | None) -> Path | None:
	# only the site's own files, and never a step out of their folder
	url = (url or "").split("?", 1)[0].split("#", 1)[0]
	for prefisso, cartella in (("/files/", "public"), ("/private/files/", "private")):
		if url.startswith(prefisso):
			base = Path(frappe.get_site_path(cartella, "files")).resolve()
			percorso = (base / unquote(url[len(prefisso) :])).resolve()
			if percorso.is_relative_to(base) and percorso.is_file():
				return percorso
	return None


def _dati(marchio: Marchio, logo_centro: str = "", nome_centro: str = "") -> dict:
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
		"centre_logo_shape": forma_di(logo_centro),
		"centre_name": nome_centro,
	}


def _del_centro() -> tuple[str, str]:
	from crm.moduli.richieste import nome_del_centro

	return logo_del_centro(), nome_del_centro()


def per_il_boot() -> dict:
	"""What DottorCloud's page and the area need of the brand, and the centre's mark
	that leads at the top of the sidebar: its logo, the logo's shape, its name."""
	return _dati(attivo(), *_del_centro())


def per_le_pagine() -> dict:
	"""The public pages' branding: the product's name, icon, logo, favicon, colours
	and accent (`accento`), and the centre's mark that leads at the top. Never
	raises: a page without it still opens, in the base's brand."""
	try:
		marchio = attivo()
		dati = _dati(marchio, *_del_centro())
	except Exception:
		marchio = BASE
		dati = _dati(marchio)
	dati["accent"] = accento(marchio)
	return dati


#: The framework's own pages a person opens without DottorCloud around them: they
#: get the brand's colour and a phone's sizes (`marchio_framework.html`).
PAGINE_DEL_FRAMEWORK = frozenset({"login", "update-password", "message"})


def contesto(context) -> dict:
	"""`update_website_context`: every web page - the framework's (the login page,
	the portal, the errors) and the CRM's public ones - with the brand's favicon and
	splash, and `marchio` for the pages that draw its marks
	(`templates/includes/marchio_*.html`). The framework's sign-in and new password
	add its colour and a phone's sizes to the website's own head."""
	dati = context.get("marchio") or per_le_pagine()
	valori = {"favicon": dati["favicon"], "splash_image": dati["icon"], "marchio": dati}
	if getattr(frappe.local, "path", None) in PAGINE_DEL_FRAMEWORK:
		stile = frappe.render_template(  # nosemgrep: frappe-ssti — literal template path
			"templates/includes/marchio_framework.html", {"marchio": dati}
		)
		valori["head_html"] = (context.get("head_html") or "") + stile
	return valori


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
	"""`extend_bootinfo`: the desk names the apps by their hooks' titles - the
	framework's "Frappe Framework" - in its apps screen and the header's switcher.
	The framework's tools (users, settings, printing) are the desk's administration,
	under the gear its desktop icon wears: never a second app named after the product."""
	marchio = attivo()
	titoli = {"frappe": _("Administration"), "crm": marchio.nome, "frappe_whatsapp": "WhatsApp"}
	loghi = {"frappe": ICONA_AMMINISTRAZIONE, "crm": marchio.icona}
	for app in bootinfo.get("app_data") or []:
		titolo = titoli.get(app.get("app_name"))
		if titolo:
			app["app_title"] = titolo
		elif "Frappe" in (app.get("app_title") or ""):
			app["app_title"] = app["app_title"].replace("Frappe", "").strip() or marchio.nome
		if app.get("app_name") in loghi:
			app["app_logo_url"] = loghi[app["app_name"]]
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
	# the name an authenticator app shows beside its codes, and the two-step
	# login's emails' «from»: the framework's own («Frappe Framework») unless the
	# centre chose one
	if not nome_scelto(frappe.db.get_single_value("System Settings", "otp_issuer_name")):
		frappe.db.set_single_value("System Settings", "otp_issuer_name", marchio.nome)


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
		# the framework's app icon is named after its hooks' title, "Frappe Framework"
		del_framework = frappe.get_meta("Desktop Icon").has_field("icon_type") and frappe.db.get_value(
			"Desktop Icon", {"icon_type": "App", "app": "frappe"}
		)
		if (
			del_framework
			and del_framework != AMMINISTRAZIONE
			and not frappe.db.exists("Desktop Icon", AMMINISTRAZIONE)
		):
			frappe.rename_doc("Desktop Icon", del_framework, AMMINISTRAZIONE, force=True)
			frappe.db.set_value(
				"Desktop Icon",
				AMMINISTRAZIONE,
				{"label": AMMINISTRAZIONE, "logo_url": ICONA_AMMINISTRAZIONE},
			)
		frappe.cache.delete_key("desktop_icons")
		frappe.cache.delete_key("bootinfo")

	_navigazione_del_desk(marchio)


def _navigazione_del_desk(marchio: Marchio) -> None:
	"""The desk's navigation from Frappe 16.50: a module opens in its shell, a `Sidebar`
	whose title is its address (`/desk/dottorcloud`); the old Workspace Sidebars are
	only the archive it was converted from. The CRM's module ships its own
	(`fcrm/sidebar/dottorcloud`): a sidebar the conversion made for it besides, named
	after the old product or the module, would be a second shell of the same things,
	and a rail entry that named one opens the product's."""
	if not frappe.db.exists("DocType", "Sidebar") or not frappe.db.exists("Sidebar", SPAZIO):
		return
	convertite = frappe.get_all(
		"Sidebar",
		filters={"standard": 0, "name": ("!=", SPAZIO)},
		or_filters={"module": "FCRM", "title": ("like", "%Frappe CRM%")},
		pluck="name",
	)
	for sidebar in convertite:
		frappe.delete_doc("Sidebar", sidebar, force=True, ignore_permissions=True)
	if frappe.db.exists("DocType", "Dock Item"):
		# the module's own name was its shell while no sidebar was shipped for it
		for sidebar in [*convertite, "FCRM"]:
			frappe.db.set_value("Dock Item", {"link_type": "Sidebar", "link_to": sidebar}, "link_to", SPAZIO)
		frappe.db.set_value("Dock Item", {"title": ("like", "%Frappe CRM%")}, "title", marchio.nome)
		frappe.cache.delete_key("dock_layers")


def desktop_ad_app() -> None:
	"""The desk's desktop as DottorCloud ships it: the apps' screen, each app with its
	dock and each module with its sidebar (`dock/crm`, `fcrm/sidebar/dottorcloud`),
	not the grid of icons Frappe 16.50 keeps for a site that had one. At install and
	once by the patch: a later choice in Desktop Settings stays, and nobody is
	invited to try what is already on."""
	if not frappe.db.exists("DocType", "Desktop Settings"):
		return
	if not frappe.get_meta("Desktop Settings").has_field("desktop_page"):
		return
	if frappe.db.get_single_value("Desktop Settings", "desktop_page") != "Apps":
		frappe.db.set_single_value("Desktop Settings", "desktop_page", "Apps")
		frappe.clear_cache()
	frappe.defaults.set_global_default("skip_new_navigation_prompt", 1)


def _autori() -> None:
	"""The desk shows who created and last changed a DocType: some of the CRM's came
	with the old product's authors' addresses."""
	moduli = frappe.get_all("Module Def", filters={"app_name": "crm"}, pluck="name")
	for campo in ("owner", "modified_by"):
		for doctype in frappe.get_all(
			"DocType", filters={campo: ("like", "%@frappe.io"), "module": ("in", moduli)}, pluck="name"
		):
			frappe.db.set_value("DocType", doctype, campo, "Administrator", update_modified=False)
