# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Server-rendered fragments the website blocks drop into a page.

These are registered as Jinja methods (see `hooks.jinja`), so a Builder block can call
them straight from its markup — `{{ crm_form_html(props.form) }}` — and Builder's
renderer, which passes every page through `render_template`, resolves them at render
time. That is what lets a CRM form sit *inside* a page instead of inside an iframe: same
document, same fonts, same styles, visible to search engines, and the visitor's tracking
ids travel with the submission exactly as they do on the standalone form page.

Nothing here trusts its caller: an unpublished form or a disabled calendar renders as
nothing rather than leaking a draft onto a live page.
"""

import json

import frappe
from frappe import _
from frappe.utils import escape_html

from crm.api.form import ALLOWED_DOCTYPES

FIELD_INPUT_TYPES = {
	"Data": "text",
	"Phone": "tel",
	"Int": "number",
	"Float": "number",
	"Currency": "number",
	"Percent": "number",
	"Date": "date",
	"Datetime": "datetime-local",
	"Time": "time",
	"Color": "color",
}

TEXTAREA_TYPES = {"Small Text", "Text", "Long Text", "Text Editor", "HTML Editor", "Markdown Editor"}


def crm_form_html(route: str | None = None, title: str | None = None, button: str | None = None) -> str:
	"""A published CRM form, rendered inline.

	`route` is the form's public route — the same one `/crm-form/<route>` serves.
	"""
	if not route:
		return _placeholder(_("Pick a form in the block settings."))

	name = frappe.db.get_value(
		"Web Form",
		{"route": str(route).strip("/"), "crm_published": 1, "doc_type": ["in", ALLOWED_DOCTYPES]},
		"name",
	)
	if not name:
		return _placeholder(_("This form is not published."))

	doc = frappe.get_cached_doc("Web Form", name)
	from crm.www.crm_form import _link_field_options, build_layout

	fields = [
		{
			"fieldname": f.fieldname,
			"label": f.label or ("" if f.fieldtype in ("Section Break", "Column Break") else f.fieldname),
			"fieldtype": f.fieldtype,
			"options": f.options or "",
			"reqd": int(f.reqd or 0),
			"placeholder": f.placeholder or "",
			"description": f.description or "",
		}
		for f in doc.web_form_fields
	]
	link_options = {
		f["fieldname"]: _link_field_options(f["options"])
		for f in fields
		if f["fieldtype"] == "Link" and f["options"]
	}
	try:
		csrf_token = frappe.sessions.get_csrf_token()
	except Exception:
		csrf_token = ""

	return frappe.render_template(
		"crm/templates/site/form_inline.html",
		{
			"web_form_name": doc.name,
			"form_title": title or doc.title,
			"form_description": doc.introduction_text or "",
			"submit_label": button or doc.button_label or _("Send"),
			"success_message": doc.success_message or _("Thank you!"),
			"success_url": doc.success_url or "",
			"layout": build_layout(fields),
			"link_options": link_options,
			"csrf_token": csrf_token,
			"input_types": FIELD_INPUT_TYPES,
			"textarea_types": TEXTAREA_TYPES,
			"uid": frappe.generate_hash(length=8),
		},
	)


def crm_booking_html(route: str | None = None, label: str | None = None) -> str:
	"""A call to action for a booking calendar, with what the visitor needs to decide."""
	if not route:
		return _placeholder(_("Pick a booking calendar in the block settings."))

	cal = frappe.db.get_value(
		"CRM Booking Calendar",
		{"route": str(route).strip("/"), "enabled": 1},
		["calendar_name", "description", "duration", "location", "price", "currency", "route"],
		as_dict=True,
	)
	if not cal:
		return _placeholder(_("This booking calendar is off."))

	return frappe.render_template(
		"crm/templates/site/booking_cta.html",
		{
			"cal": cal,
			"label": label or _("Book now"),
			"price": frappe.utils.fmt_money(cal.price, currency=cal.currency or "EUR") if cal.price else "",
			"url": f"/book/{cal.route}",
		},
	)


def crm_contact_html() -> str:
	"""Address, phone, email and WhatsApp, from the site settings — never retyped."""
	s = frappe.get_cached_doc("CRM Website Settings")
	if not (s.address or s.phone or s.email or s.whatsapp_number):
		return _placeholder(_("Fill in the contact details under Settings → Website."))
	return frappe.render_template(
		"crm/templates/site/contacts.html",
		{
			"settings": s,
			"whatsapp_url": f"https://wa.me/{s.whatsapp_number}" if s.whatsapp_number else "",
		},
	)


def _placeholder(message: str) -> str:
	"""What an unconfigured block shows: visible to the author, harmless to a visitor."""
	return (
		'<div style="padding:16px;border:1px dashed #d4d4d4;border-radius:8px;'
		'color:#737373;font-size:14px;text-align:center">' + escape_html(message) + "</div>"
	)


# ---------------------------------------------------------------- site-wide head

CRM_HEAD_START = "<!-- crm:site:start -->"
CRM_HEAD_END = "<!-- crm:site:end -->"


def build_head_html(settings) -> str:
	"""The markup the CRM owns in every Builder page's <head>.

	Builder applies `Builder Settings.head_html` to every page it renders, which is the
	only place a site-wide tag can live — its page template does not include the
	framework's `web_include_js`, so `hooks.web_include_js` would never fire.

	Three things go in: the brand tokens, the tracker (so a visit to a page feeds the
	attribution the CRM already has), and the analytics tags — the last two gated behind
	consent when the banner is on, because loading a pixel before consent is the thing
	the banner exists to prevent.
	"""
	parts = []

	tokens = []
	if settings.primary_color:
		tokens.append(f"--crm-primary:{settings.primary_color}")
	if settings.font_family:
		tokens.append(f'--crm-font:"{settings.font_family}"')
	if tokens:
		parts.append("<style>:root{" + ";".join(tokens) + "}</style>")
	if settings.font_family:
		family = settings.font_family.replace(" ", "+")
		parts.append(
			f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={family}'
			':wght@400;500;600;700&display=swap">'
		)

	parts.append('<script src="/assets/crm/js/tracker.js" defer></script>')

	analytics = _analytics_tags(settings)
	if analytics:
		if settings.consent_banner:
			parts.append(_consent_banner(settings, analytics))
		else:
			parts.extend(analytics)

	return "\n".join(parts)


def _analytics_tags(settings) -> list[str]:
	tags = []
	if settings.ga4_id:
		gid = escape_html(settings.ga4_id)
		tags.append(f'<script async src="https://www.googletagmanager.com/gtag/js?id={gid}"></script>')
		tags.append(
			"<script>window.dataLayer=window.dataLayer||[];"
			"function gtag(){dataLayer.push(arguments)}gtag('js',new Date());"
			f"gtag('config','{gid}')</script>"
		)
	if settings.meta_pixel_id:
		pid = escape_html(settings.meta_pixel_id)
		tags.append(
			"<script>!function(f,b,e,v,n,t,s)"
			"{if(f.fbq)return;n=f.fbq=function(){n.callMethod?"
			"n.callMethod.apply(n,arguments):n.queue.push(arguments)};"
			"if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];"
			"t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];"
			"s.parentNode.insertBefore(t,s)}(window,document,'script',"
			"'https://connect.facebook.net/en_US/fbevents.js');"
			f"fbq('init','{pid}');fbq('track','PageView')</script>"
		)
	return tags


def _consent_banner(settings, analytics: list[str]) -> str:
	"""A banner that actually gates the tags, rather than decorating a page that already
	loaded them. The scripts are held as inert text and only injected on accept."""
	text = escape_html(
		settings.consent_text
		or _("We use cookies to measure how the site is used. You choose whether to allow it.")
	)
	payload = json.dumps("\n".join(analytics))
	reject_label = json.dumps(_("Reject"))
	accept_label = json.dumps(_("Accept"))
	privacy = (settings.privacy_route or "").strip("/")
	link = f'<a href="/{privacy}" style="color:inherit">{escape_html(_("Privacy"))}</a>' if privacy else ""
	message = json.dumps(f'<span style="flex:1;min-width:220px">{text} {link}</span>')

	return (
		"<script>\n(function () {\n"
		'  var KEY = "crm_consent";\n'
		f"  var TAGS = {payload};\n"
		f"  var MESSAGE = {message};\n"
		"  function load() {\n"
		'    var holder = document.createElement("div");\n'
		"    holder.innerHTML = TAGS;\n"
		'    Array.prototype.forEach.call(holder.querySelectorAll("script"), function (old) {\n'
		'      var s = document.createElement("script");\n'
		"      Array.prototype.forEach.call(old.attributes, function (a) { s.setAttribute(a.name, a.value); });\n"
		"      s.text = old.text;\n"
		"      document.head.appendChild(s);\n"
		"    });\n"
		"  }\n"
		"  function decide(value) {\n"
		"    try { localStorage.setItem(KEY, value); } catch (e) {}\n"
		'    var bar = document.getElementById("crm-consent");\n'
		"    if (bar) bar.remove();\n"
		'    if (value === "yes") load();\n'
		"  }\n"
		"  var saved = null;\n"
		"  try { saved = localStorage.getItem(KEY); } catch (e) {}\n"
		'  if (saved === "yes") { load(); return; }\n'
		'  if (saved === "no") return;\n'
		'  document.addEventListener("DOMContentLoaded", function () {\n'
		'    var bar = document.createElement("div");\n'
		'    bar.id = "crm-consent";\n'
		'    bar.setAttribute("role", "dialog");\n'
		'    bar.style.cssText = "position:fixed;left:16px;right:16px;bottom:16px;z-index:2147483000;" +\n'
		'      "display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between;" +\n'
		'      "padding:14px 18px;border-radius:12px;background:#171717;color:#fafafa;font-size:14px;" +\n'
		'      "box-shadow:0 8px 30px rgba(0,0,0,.25);max-width:720px;margin:0 auto";\n'
		"    bar.innerHTML = MESSAGE;\n"
		'    var no = document.createElement("button");\n'
		'    var yes = document.createElement("button");\n'
		f"    no.textContent = {reject_label};\n"
		f"    yes.textContent = {accept_label};\n"
		'    no.style.cssText = "font:inherit;padding:8px 14px;border-radius:8px;border:1px solid #525252;" +\n'
		'      "background:transparent;color:inherit;cursor:pointer";\n'
		'    yes.style.cssText = "font:inherit;font-weight:600;padding:8px 14px;border-radius:8px;border:0;" +\n'
		'      "background:#fafafa;color:#171717;cursor:pointer";\n'
		'    no.onclick = function () { decide("no"); };\n'
		'    yes.onclick = function () { decide("yes"); };\n'
		"    bar.appendChild(no);\n"
		"    bar.appendChild(yes);\n"
		"    document.body.appendChild(bar);\n"
		"  });\n"
		"})();\n</script>"
	)


def sync_builder_head(settings) -> None:
	"""Write our block into Builder's site-wide head, leaving anyone else's alone.

	Delimited by markers so an author can add their own tags around ours and keep them
	across every save.
	"""
	if not frappe.db.exists("DocType", "Builder Settings"):
		return
	current = frappe.db.get_single_value("Builder Settings", "head_html") or ""
	ours = f"{CRM_HEAD_START}\n{build_head_html(settings)}\n{CRM_HEAD_END}" if settings.enabled else ""

	if CRM_HEAD_START in current and CRM_HEAD_END in current:
		head, _sep, rest = current.partition(CRM_HEAD_START)
		_ours, _sep2, tail = rest.partition(CRM_HEAD_END)
		updated = (head + ours + tail).strip()
	else:
		updated = (current + "\n" + ours).strip() if ours else current.strip()

	if updated != current:
		frappe.db.set_single_value("Builder Settings", "head_html", updated)
		frappe.clear_cache()
