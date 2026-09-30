# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# Modifications copyright (c) 2026, NPM2 Solutions Srl
# For license information, please see license.txt

"""/crm-form/<route> - a form of the centre's website (`crm.moduli.sito`).

Its questions are a published template's, drawn by the renderer of the forms
sent by link (`moduli_campi.js`) on the CRM's engine, the rules the server
applies too; what is sent goes to `crm.moduli.sito.submit_site_form`. Embedded
in another site with ``?embed=1`` it drops its page, and the browser shows it
only on the sites its template lists.
"""

import re

import frappe

from crm.moduli import sito
from crm.www.modulo import versione_del_motore

no_cache = 1

# bare host, optional scheme/port, optional leading "*." wildcard — rejects any
# token containing CSP metacharacters like ";" so admin-entered domains can't
# inject extra directives into the Content-Security-Policy header
ALLOWED_EMBEDDING_DOMAIN_RE = re.compile(
	r"^(https?://)?(\*\.)?[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?(?::\d+)?$"
)


def get_context(context):
	# whoever builds the website's forms sees a draft before it is published
	modello = sito.modello_del_sito(resolve_route(), anteprima=frappe.session.user != "Guest")
	if not modello:
		raise frappe.DoesNotExistError
	set_embedding_headers(modello)
	context.no_cache = 1
	try:
		context.csrf_token = frappe.sessions.get_csrf_token()
	except Exception:
		context.csrf_token = ""
	# ?embed=1 (the iframe's address) drops the page around the form
	context.embed = frappe.form_dict.get("embed") in ("1", "true", "yes")
	context.engine_version = versione_del_motore()
	context.form = sito.per_la_pagina(modello)
	context.boot = {
		"lang": (frappe.local.lang or "it")[:2],
		"embed": context.embed,
		# When the form is embedded in an iframe the tracker on the host page appends
		# the visitor ids to the frame's address, because the frame cannot read the
		# host page's storage. Opened directly, the cookies have them instead.
		"crm_vid": _tracking_id("crm_vid"),
		"crm_sid": _tracking_id("crm_sid"),
	}
	context.title = context.form["title"]
	return context


def _tracking_id(key: str) -> str:
	"""A visitor/session id from the query string, or the cookie set by an earlier
	visit. Validated to the minted shape so nothing else reaches the database."""
	value = str(frappe.form_dict.get(key) or frappe.request.cookies.get(key) or "").strip()
	is_id = len(value) == 32 and all(c in "0123456789abcdef" for c in value)
	return value if is_id else ""


def set_embedding_headers(doc):
	"""Allow this page to be embedded as an iframe on the form's allow-listed origins.

	Emits a Content-Security-Policy `frame-ancestors` header. Modern browsers ignore
	the default `X-Frame-Options: SAMEORIGIN` (set by nginx) whenever `frame-ancestors`
	is present, so this is what makes cross-origin embedding work — without it a form
	can only be embedded on its own site.
	"""
	raw_domains = (doc.allowed_embedding_domains or "").split()
	domains = [d for d in raw_domains if ALLOWED_EMBEDDING_DOMAIN_RE.match(d)]
	if not domains:
		return
	frappe.local.response_headers["Content-Security-Policy"] = "frame-ancestors 'self' " + " ".join(domains)


def resolve_route() -> str:
	"""The public slug, from the /crm-form/<route> path rule (with a path fallback)."""
	route = (frappe.form_dict.get("route") or "").strip("/")
	if route and route != "crm-form":
		return route
	path = (getattr(frappe.request, "path", "") or "").strip("/")
	prefix = "crm-form/"
	return path[len(prefix) :] if path.startswith(prefix) else path
