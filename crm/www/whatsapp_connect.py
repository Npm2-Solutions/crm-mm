# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Hub-hosted WhatsApp Embedded Signup page.

Reached from a client CRM with a signed `state`; the page itself is public
because the visitor is logged into their own site, not into the hub. Nothing
sensitive is rendered: the state only says which site started the flow, and
`complete_signup` verifies its signature again server-side.

The same page is also where Meta lands when the pop-up was suppressed and the
JavaScript SDK fell back to a full-page redirect. That leg arrives with a
`code` and **no state** — Strict Mode strips everything the registered redirect
URI does not spell out — so the page must not mistake it for a broken link.
"""

import frappe
from frappe import _

from crm.integrations.meta.client import get_whatsapp_app_id
from crm.integrations.whatsapp.signup import (
	allowed_site,
	config_id,
	connect_url,
	login_url,
	parse_state,
)

no_cache = 1


def get_context(context):
	context.no_cache = 1
	context.state = frappe.form_dict.get("state") or ""
	context.code = frappe.form_dict.get("code") or ""
	# Meta reports a refusal on the redirect leg the same way it reports one on
	# any OAuth redirect: in the query string, not by staying silent.
	context.denied = frappe.form_dict.get("error") or frappe.form_dict.get("error_reason") or ""
	# Everything Meta says about a refusal, not just that there was one. These
	# are the names it uses on an OAuth redirect; the page hands them to the
	# session log under the same fields the in-flow errors use.
	context.error_query = {
		key: frappe.form_dict.get(key)
		for key in ("error", "error_code", "error_reason", "error_description")
		if frappe.form_dict.get(key)
	}
	context.returning = bool(context.code or context.denied)
	parsed = parse_state(context.state)

	context.app_id = get_whatsapp_app_id()
	context.config_id = config_id()
	context.connect_url = connect_url()
	context.site_label = ""
	context.return_url = ""
	context.error = ""

	context.launch = ""

	if context.returning:
		# Everything this leg needs was kept in the tab that started the flow;
		# the page picks it up from sessionStorage, or from the state Facebook
		# hands back, instead of from a fresh link.
		return context
	if not parsed:
		context.error = _(
			"This connection link is invalid or has expired. Go back to your CRM and press Connect again."
		)
	elif not allowed_site(parsed["site"]):
		context.error = _("This site is not allowed to connect WhatsApp.")
	elif not context.app_id or not context.config_id:
		context.error = _("WhatsApp signup is not configured on this hub yet.")
	else:
		context.site_label = parsed["site"]
		context.return_url = parsed["site"] + "/crm?settings=WhatsApp"
		# `go` says the CRM sent the person here to connect, not to read about
		# connecting. Then this page is a waypoint, not a screen: it hands the
		# browser on to Facebook without waiting for a second click. The card
		# below stays as the fallback for anyone who lands here without it.
		if frappe.form_dict.get("go"):
			context.launch = login_url(context.state)
	return context
