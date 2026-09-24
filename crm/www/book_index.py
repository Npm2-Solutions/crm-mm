# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe

from crm.api.booking import list_services

no_cache = 1


def get_context(context):
	# one booking system: the directory of services is /prenota
	if frappe.get_all(
		"CRM Booking Calendar", filters={"migrated_service": ["is", "set"]}, limit=1
	) or not frappe.get_all("CRM Booking Calendar", filters={"enabled": 1, "show_in_menu": 1}, limit=1):
		frappe.local.flags.redirect_location = "/prenota"
		raise frappe.Redirect(301)
	context.no_cache = 1
	context.services = list_services()
	from crm.api.service_booking import page_title

	context.org_name = page_title()
	return context
