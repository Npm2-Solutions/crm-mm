# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""/modulo/<link> - forms to fill and sign, at home or on the desk's tablet.

A static shell: what it shows comes from the guest calls in
`crm.moduli.richieste`, where the link, the code and the session are the
credentials. The rules that decide what shows and what is required are the CRM's
own engine (`/assets/crm/js/moduli_engine.js`, the same file as
`frontend/src/utils/moduli.js`), so the page and the server agree.
"""

import functools
import hashlib

import frappe

no_cache = 1


@functools.lru_cache(maxsize=1)
def versione_del_motore() -> str:
	"""A browser keeps the engine it downloaded: a new one gets a new address."""
	with open(frappe.get_app_path("crm", "public", "js", "moduli_engine.js"), "rb") as motore:
		return hashlib.sha256(motore.read()).hexdigest()[:12]


def get_context(context):
	context.no_cache = 1
	# guests POST without CSRF, but a logged-in user opening a link needs the token
	try:
		context.csrf_token = frappe.sessions.get_csrf_token()
	except Exception:
		context.csrf_token = ""
	context.engine_version = versione_del_motore()
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

	# the centre's logo beside the product's, with the centre's name: not the booking page's title
	context.branding["title"] = nome_del_centro()
	context.title = context.branding["title"] or "Moduli"
	return context
