# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# Modifications copyright (c) 2026, NPM2 Solutions Srl
# For license information, please see license.txt

"""The calls the CRM's panel made before `crm.notifiche.api`: kept for whatever
still asks for them, answered by the new ones."""

import frappe

from crm.notifiche import api


@frappe.whitelist()
def get_notifications():
	return api.get_notifications(limit=api.PER_PAGINA)["rows"]


@frappe.whitelist()
def mark_as_read(doc: str | None = None):
	if doc:
		api.segna_lette_di(frappe.session.user, doc)
	else:
		api.mark_as_read()
