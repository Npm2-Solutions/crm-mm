# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""/prenota — the public service booking page (menu → professional → slot → details).

The page is a single static shell; everything it shows comes from the guest API
in ``crm.api.service_booking``, so the same endpoints can back an embed or an app.
"""

import frappe

no_cache = 1


def get_context(context):
	context.no_cache = 1
	# guests POST without CSRF, but a logged-in user browsing the page needs the token
	try:
		context.csrf_token = frappe.sessions.get_csrf_token()
	except Exception:
		context.csrf_token = ""
	form = frappe.form_dict
	path = path_filters(form.get("prenota_path") or _request_path())
	context.boot = {
		# deep links, as query or path: /prenota?servizio=<slug> or /prenota/<slug>,
		# ?professionista=<id> or /prenota/p/<id>, ?categoria=<name> or /prenota/c/<name>,
		# ?token=... to manage a booking
		"service": form.get("servizio") or form.get("service") or path.get("service", ""),
		"staff": form.get("professionista") or form.get("staff") or path.get("staff", ""),
		"category": form.get("categoria") or form.get("category") or path.get("category", ""),
		"token": form.get("token") or "",
		"embed": bool(form.get("embed")),
		"lang": (form.get("lang") or frappe.local.lang or "it")[:2],
		# campaigns and the CRM itself can open the page with the client already known
		"prefill": {
			"full_name": (form.get("nome") or form.get("name") or "")[:140],
			"email": (form.get("email") or "")[:140],
			"phone": (form.get("telefono") or form.get("phone") or "")[:40],
		},
	}
	try:
		title = frappe.db.get_single_value("CRM Scheduling Settings", "booking_page_title")
	except Exception:
		title = None
	context.title = title or "Prenota"
	return context


def _request_path() -> str:
	try:
		parts = [p for p in (frappe.local.request.path or "").split("/") if p]
	except Exception:
		return ""
	return "/".join(parts[1:]) if parts and parts[0] in ("prenota", "booking") else ""


def path_filters(path: str) -> dict:
	"""``p/<id>`` → staff, ``c/<name>`` → category, ``<slug>`` → service."""
	from urllib.parse import unquote

	parts = [unquote(p) for p in (path or "").strip("/").split("/") if p]
	if len(parts) >= 2 and parts[0] in ("p", "professionista"):
		return {"staff": parts[1]}
	if len(parts) >= 2 and parts[0] in ("c", "categoria"):
		return {"category": parts[1]}
	if parts:
		return {"service": parts[0]}
	return {}
