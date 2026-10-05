# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What a migrate needs before it syncs anything.

Frappe reads the map of the apps' modules once, when the process starts, and from
the cache first: a worker still running the previous release may have written it
there. `clear_cache()` then empties the cache but leaves the map the process holds.
A module this release adds (`modules.txt`) would be missing from it: its DocTypes
would not sync in this migrate, and a patch that works on them would find nothing -
the marks of health data on the documents, plans and quotes moved to the CRM among
them. So before the migrate syncs, the map comes from the files of this release.

The same for the words: `bench update` migrates before it builds, and the build is
what compiles the catalogues. A migrate translated with the previous release's, and
every word new in this one that it wrote into the site - a qualification's points
to check, a consent's text, a pipeline's stage - stayed in English until the migrate
after. So before the migrate, DottorCloud's catalogue is this release's.
"""

from __future__ import annotations

import frappe


def mappa_dei_moduli() -> None:
	"""`before_migrate`: the module map from each app's `modules.txt`, never the cache."""
	app_modules = {
		app: [frappe.scrub(modulo) for modulo in frappe.get_module_list(app)]
		for app in frappe.get_all_apps(with_internal_apps=True)
	}
	frappe.local.app_modules = app_modules
	frappe.local.module_app = {modulo: app for app, moduli in app_modules.items() for modulo in moduli}
	frappe.cache.set_value("app_modules", app_modules)
	frappe.client_cache.delete_value("installed_app_modules")


def il_catalogo_del_rilascio() -> None:
	"""`before_migrate`: DottorCloud's words compiled from this release's catalogue
	(`crm/locale/*.po`) where what was compiled is older, so what the patches and
	`after_migrate` write in the centre's language is in it. Only crm's, and never
	stopping the migrate: at worst the words wait for the next one, as before."""
	try:
		from frappe.gettext.translate import (
			get_catalog,
			get_locales,
			get_mo_path,
			get_po_path,
			write_binary,
		)
		from frappe.translate import clear_cache

		compilati = 0
		for lingua in get_locales("crm"):
			catalogo, compilato = get_po_path("crm", lingua), get_mo_path("crm", lingua)
			if not catalogo.exists():
				continue
			if compilato.exists() and compilato.stat().st_mtime >= catalogo.stat().st_mtime:
				continue
			write_binary("crm", get_catalog("crm", lingua), lingua)
			compilati += 1
		if compilati:
			clear_cache()
	except Exception:
		frappe.log_error(title="DottorCloud's words not compiled before the migrate")
