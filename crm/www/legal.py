# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Shared context for the public privacy policy and terms pages.

Meta requires a reachable Privacy Policy and Terms of Service on every app
submitted for App Review, and a Data Deletion route. These live on the hub, the
one domain both apps point at.

The company's legal details are NOT hard-coded: they come from the site config
so the same code serves any agency running this CRM, and so nobody has to edit
a template to correct a VAT number.
"""

import frappe

# what the pages say about the operator, overridable per site
DEFAULTS = {
	"legal_name": "NPM2 Solutions",
	"legal_address": "",
	"legal_vat": "",
	"legal_email": "info@npm2solutions.com",
}


def legal_context(context):
	for key, fallback in DEFAULTS.items():
		context[key] = frappe.conf.get(key) or fallback
	context.no_cache = 1
	context.incomplete = not (context["legal_address"] and context["legal_vat"])
	context.deletion_url = frappe.utils.get_url("/api/method/crm.integrations.meta.webhook.data_deletion")
	context.updated_on = "settembre 2026"
