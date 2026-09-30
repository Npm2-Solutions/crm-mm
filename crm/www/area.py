# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""/area - the client area: a page of its own, not the staff's app.

The app is built apart (`frontend/vite.area.config.js`, into `/assets/crm/area`):
a client never downloads the staff's code. What it shows comes from `crm.area`,
which derives the session's people on the server, and from the places other
modules add to it (`crm.area.sezioni`).
"""

import frappe

from crm import marchio

no_cache = 1


def get_context(context):
	context.no_cache = 1
	try:
		context.csrf_token = frappe.sessions.get_csrf_token()
	except Exception:
		context.csrf_token = ""
	try:
		from crm.api.service_booking import page_branding

		branding = page_branding()
	except Exception:
		branding = {"title": "", "logo": ""}
	from crm.moduli.richieste import nome_del_centro

	utente = frappe.session.user
	# the product's brand - the vertical's - is the page's; the centre's name and
	# logo go beside it
	context.marchio = marchio.per_le_pagine()
	centro = nome_del_centro()
	context.title = f"{centro} · {context.marchio['name']}" if centro else context.marchio["name"]
	context.boot = {
		"user": utente,
		# staff opening this page are told where their app is: the area is for clients
		"staff": utente != "Guest" and frappe.db.get_value("User", utente, "user_type") == "System User",
		"lang": (frappe.local.lang or "it")[:2],
		"centre": centro,
		"logo": branding.get("logo") or "",
		"brand": context.marchio,
		# the vertical the plan has on says some words its own way: the clinic's patients
		"words": _parole(),
	}
	return context


def _parole() -> dict:
	try:
		from crm import verticali

		return verticali.parole()
	except Exception:
		return {}
