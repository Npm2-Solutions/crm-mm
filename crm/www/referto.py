# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""/referto/<link> - a report the centre put online, opened with its code.

A static shell: the link says which delivery, the code the centre gave opens a
ten-minute session, the session downloads the PDF (`crm.clinica.consegna`). The
page shows nothing of the report until the code is right: not even its title.
"""

import frappe

no_cache = 1


def get_context(context):
	context.no_cache = 1
	try:
		context.csrf_token = frappe.sessions.get_csrf_token()
	except Exception:
		context.csrf_token = ""
	context.boot = {
		"token": (frappe.form_dict.get("token") or "")[:120],
		"lang": (frappe.local.lang or "it")[:2],
	}
	try:
		from crm.api.service_booking import page_branding

		context.branding = page_branding()
	except Exception:
		context.branding = {"title": "", "logo": ""}
	from crm.moduli.richieste import nome_del_centro

	context.branding["title"] = nome_del_centro()
	context.title = context.branding["title"] or "Referto"
	return context
