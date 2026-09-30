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
