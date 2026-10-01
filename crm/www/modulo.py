# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""/modulo/<link> - forms to fill and sign, at home or on the desk's tablet.

A static shell: what it shows comes from the guest calls in
`crm.moduli.richieste`, where the link, the code and the session are the
credentials. The rules that decide what shows and what is required are the CRM's
own engine (`/assets/crm/js/moduli_engine.js`, the same file as
`frontend/src/utils/moduli.js`), so the page and the server agree; the questions
are drawn by `moduli_campi.js`, as on the website's forms.
"""

import functools
import hashlib

import frappe

no_cache = 1


#: The engine, the questions drawn on it and their styles: they change together.
MOTORE = (("js", "moduli_engine.js"), ("js", "moduli_campi.js"), ("css", "moduli_campi.css"))


@functools.lru_cache(maxsize=1)
def versione_del_motore() -> str:
	"""A browser keeps the engine it downloaded: a new one gets a new address."""
	impronta = hashlib.sha256()
	for cartella, nome in MOTORE:
		# nosemgrep: frappe-security-file-traversal — the three files above, the app's own
		with open(frappe.get_app_path("crm", "public", cartella, nome), "rb") as file:
			impronta.update(file.read())
	return impronta.hexdigest()[:12]


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
		context.branding = {"title": "", "logo": "", "logo_shape": ""}
	from crm.moduli.richieste import nome_del_centro

	# the centre's mark at the top names the centre: not the booking page's title
	context.branding["title"] = nome_del_centro()
	context.title = context.branding["title"] or "Moduli"
	return context
