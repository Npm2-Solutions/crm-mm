# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's first opening: whoever sets it up chooses its language, Italian
or English, then writes its name and its clock. Two screens, in place of the
framework's setup wizard, which they mark done: the Desk never shows it after
them, and finishing it would load the demo data by itself
(`setup_wizard_complete` in hooks.py).

Due while the centre has no name and nobody finished it (`FATTO`): a centre that
already works has its name, and never sees it. Whoever may set the centre up
(`impostazioni.generali`) is taken to it before anything else (`per_il_boot`,
the router); the others use DottorCloud meanwhile.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint

from crm import lingue

#: The welcome finished on this site (a default).
FATTO = "crm_benvenuto_fatto"
#: Who is welcomed: whoever sets the centre up.
CAPACITA = "impostazioni.generali"


def da_fare() -> bool:
	"""Whether the centre is still to be welcomed: nobody finished it, and the
	centre has no name of its own."""
	from crm.moduli.richieste import nome_del_centro

	return frappe.db.get_default(FATTO) != "1" and not nome_del_centro()


def per_il_boot() -> bool:
	"""Whether this session is taken to the welcome. Never raises: the page opens
	whatever happens here."""
	try:
		from crm.permissions import livelli

		return frappe.session.user != "Guest" and da_fare() and livelli.puo(CAPACITA)
	except Exception:
		return False


def _verifica() -> None:
	from crm.permissions import livelli

	livelli.verifica(CAPACITA)


@frappe.whitelist()
def get_welcome() -> dict:
	"""What the two screens show: the languages, the centre's name and clock, and
	whether the demo data can be loaded from them."""
	_verifica()
	from crm.demo import registro
	from crm.moduli.richieste import nome_del_centro
	from crm.permissions import livelli

	return {
		**lingue.get_centre_language(),
		"centre_name": nome_del_centro(),
		"demo": livelli.puo("dati_prova.gestisci") and not registro.caricati(),
	}


@frappe.whitelist(methods=["POST"])
def choose_language(language: str) -> dict:
	"""The first screen: the centre's language. Whoever chose it reads it at once,
	their own language left for the centre's."""
	_verifica()
	stato = lingue.save_centre_language(language)
	utente = frappe.session.user
	if frappe.db.get_value("User", utente, "language") not in (None, "", language):
		frappe.db.set_value("User", utente, "language", "", update_modified=False)
	frappe.cache.hdel("lang", utente)
	return stato


@frappe.whitelist(methods=["POST"])
def finish(centre_name: str, time_zone: str | None = None, demo: bool | int | str = 0) -> dict:
	"""The second screen: the centre's name and clock, and maybe the demo data.
	The welcome is done."""
	_verifica()
	from crm.marchio import nome_scelto

	nome = (centre_name or "").strip()
	if not nome_scelto(nome):
		frappe.throw(_("Write the centre's name"))
	impostazioni = frappe.get_single("FCRM Settings")
	impostazioni.brand_name = nome
	impostazioni.flags.ignore_permissions = True
	impostazioni.save()
	if time_zone:
		lingue.save_centre_language(lingue.del_centro(), time_zone)
	il_framework_e_pronto()
	frappe.db.set_default(FATTO, "1")
	if cint(demo):
		from crm.demo.api import create_demo_data
		from crm.permissions import livelli

		if livelli.puo("dati_prova.gestisci"):
			create_demo_data()
	return {"done": True}


def il_framework_e_pronto() -> None:
	"""The framework's setup wizard marked done, as its own end marks it (its
	`enable_setup_wizard_complete` and `disable_future_access`)."""
	if frappe.is_setup_complete():
		return
	frappe.db.set_value("Installed Application", {"app_name": "frappe"}, "is_setup_complete", 1)
	frappe.db.set_single_value("System Settings", "setup_complete", 1)
	frappe.db.set_default("desktop:home_page", "workspace")
	# `is_setup_complete` is kept for the request
	frappe.local.request_cache.clear()
