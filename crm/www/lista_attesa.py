# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""/lista-attesa/<link> - a place offered from a waiting list, or the list one
joined: confirm it, let it go, or leave the list.

A static shell: everything it shows comes from `crm.scheduling.attese_pubblico`
with the link, which is the credential. Nothing about the person is in the page
until the link is read.
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
	context.title = context.branding["title"] or "Lista d'attesa"
	return context
