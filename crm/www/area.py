# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""/area - the patient area: a page of its own, not the CRM's.

The app is built apart (`frontend/vite.area.config.js`, into `/assets/crm/area`):
a patient never downloads the staff's code. What it shows comes from
`crm.clinica.area`, which derives the session's people on the server.
"""

import frappe

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
		branding = {"logo": "", "favicon": "", "css": {}}
	from crm.moduli.richieste import nome_del_centro

	utente = frappe.session.user
	context.branding = branding
	context.title = nome_del_centro() or "Area"
	context.boot = {
		"user": utente,
		# staff opening this page are told where their app is: the area is for patients
		"staff": utente != "Guest" and frappe.db.get_value("User", utente, "user_type") == "System User",
		"lang": (frappe.local.lang or "it")[:2],
		"centre": nome_del_centro(),
		"logo": branding.get("logo") or "",
	}
	return context
