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
	context.boot = {
		# deep links: /prenota?servizio=<slug>&professionista=<id>, or ?token=... to manage
		"service": form.get("servizio") or form.get("service") or "",
		"staff": form.get("professionista") or form.get("staff") or "",
		"token": form.get("token") or "",
		"embed": bool(form.get("embed")),
		"lang": (form.get("lang") or frappe.local.lang or "it")[:2],
	}
	try:
		title = frappe.db.get_single_value("CRM Scheduling Settings", "booking_page_title")
	except Exception:
		title = None
	context.title = title or "Prenota"
	return context
