# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The product's name and marks where the framework shows its own.

The CRM's screens say DottorCloud by themselves. The framework's - the login page,
the desk, its public pages, the emails it writes - take a name, a logo and a footer
from their settings, and fall back to the framework's own where those are empty:
"Frappe" in the title, its logo on the login page, "Built on Frappe" under every
public page, its support link in the help menu, its apps advertised in the sidebar.

So the hooks give the logo, the favicon and the splash (`hooks.py`), `boot` renames
the apps the desk lists, and `applica` fills the settings once - at install and by
the patch - leaving whatever a centre wrote there itself. The notices the licence
asks for stay: the copyright lines in the sources and the licence file.
"""

from __future__ import annotations

import frappe
from frappe import _lt

NOME = "DottorCloud"
#: the app's icon: the mark on the teal square
ICONA = "/assets/crm/images/dottorcloud-icona.svg"
#: the desk's own tools (users, settings, printing) under a gear, not the framework's logo
ICONA_AMMINISTRAZIONE = "/assets/crm/images/amministrazione.svg"

#: the titles the desk shows for the apps, in place of their hooks' own
TITOLI = {"frappe": NOME, "crm": NOME, "frappe_whatsapp": "WhatsApp"}

#: the framework's name where a setting falls back to it
NOMI_DEL_FRAMEWORK = ("", "Frappe", "Frappe Framework")
#: names that are the software's, never a centre's
NOMI_DEL_SOFTWARE = ("", "frappe", "frappe framework", "frappe crm", NOME.lower())

VECCHIO_SPAZIO = "Frappe CRM"

#: The framework's own words that name it, in the app's catalogue so that each
#: language says them with the product's name (`locale/*.po`, English in `en.po`):
#: the desk's light theme, and the welcome of an onboarding without a title.
PAROLE_DEL_FRAMEWORK = (_lt("Frappe Light"), _lt("Welcome to Frappe!"))


def nome_scelto(nome: str | None) -> str:
	"""A name a centre chose for itself, or empty where it is the software's own:
	the site's name is DottorCloud until the centre writes its own, and a patient
	must not read the software's name where the centre's belongs."""
	nome = (nome or "").strip()
	return "" if nome.lower() in NOMI_DEL_SOFTWARE else nome


def boot(bootinfo) -> None:
	"""`extend_bootinfo`: the desk's sidebar names the app a page belongs to by its
	hooks' title - "Frappe Framework" for users and settings - and draws its logo."""
	for app in bootinfo.get("app_data") or []:
		titolo = TITOLI.get(app.get("app_name"))
		if titolo:
			app["app_title"] = titolo
		elif "Frappe" in (app.get("app_title") or ""):
			app["app_title"] = app["app_title"].replace("Frappe", "").strip() or NOME
		if app.get("app_name") in ("frappe", "crm"):
			app["app_logo_url"] = ICONA
	# with a third app naming a logo the framework goes back to its own
	if "frappe-framework" in str(bootinfo.get("app_logo_url") or ""):
		bootinfo["app_logo_url"] = ICONA


def applica() -> None:
	"""Fill the framework's settings with the product: once, keeping what a centre set."""
	_nome_e_piede()
	_senza_suggerimenti()
	_aiuto_senza_il_framework()
	_scrivania()
	_autori()
	frappe.clear_cache()


def _nome_e_piede() -> None:
	# the name the login page, the desk's title and the emails' "Log in to" say
	for doctype in ("Website Settings", "System Settings"):
		if (frappe.db.get_single_value(doctype, "app_name") or "") in NOMI_DEL_FRAMEWORK:
			frappe.db.set_single_value(doctype, "app_name", NOME)
	# empty, every public page ends with "Built on Frappe"
	if not frappe.db.get_single_value("Website Settings", "footer_powered"):
		frappe.db.set_single_value("Website Settings", "footer_powered", NOME)


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


def _scrivania() -> None:
	"""The desk's desktop and sidebar: the CRM's workspace, its sidebar and its
	app icon were named after the old product; the framework's app icon is its logo."""
	if frappe.db.exists("Workspace", VECCHIO_SPAZIO):
		# the new one comes with the app (fcrm/workspace/dottorcloud)
		if frappe.db.exists("Workspace", NOME):
			frappe.delete_doc("Workspace", VECCHIO_SPAZIO, force=True, ignore_permissions=True)
		else:
			frappe.rename_doc("Workspace", VECCHIO_SPAZIO, NOME, force=True)
			frappe.db.set_value("Workspace", NOME, {"label": NOME, "title": NOME})

	if frappe.db.exists("DocType", "Workspace Sidebar") and frappe.db.exists(
		"Workspace Sidebar", VECCHIO_SPAZIO
	):
		if frappe.db.exists("Workspace Sidebar", NOME):
			frappe.delete_doc("Workspace Sidebar", VECCHIO_SPAZIO, force=True, ignore_permissions=True)
		else:
			frappe.rename_doc("Workspace Sidebar", VECCHIO_SPAZIO, NOME, force=True)
			frappe.db.set_value("Workspace Sidebar", NOME, "title", NOME)
		# its first item opens the workspace by name
		frappe.db.set_value(
			"Workspace Sidebar Item",
			{"parent": NOME, "link_type": "Workspace", "link_to": VECCHIO_SPAZIO},
			"link_to",
			NOME,
		)

	if frappe.db.exists("DocType", "Desktop Icon"):
		if frappe.db.exists("Desktop Icon", VECCHIO_SPAZIO):
			if frappe.db.exists("Desktop Icon", NOME):
				frappe.delete_doc("Desktop Icon", VECCHIO_SPAZIO, force=True, ignore_permissions=True)
			else:
				frappe.rename_doc("Desktop Icon", VECCHIO_SPAZIO, NOME, force=True)
		if frappe.db.exists("Desktop Icon", NOME):
			frappe.db.set_value("Desktop Icon", NOME, "logo_url", ICONA)
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
