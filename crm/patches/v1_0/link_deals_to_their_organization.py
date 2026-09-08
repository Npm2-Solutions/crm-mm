# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Give a deal that names a company the company itself.

The deal's company fields are mirrors of `CRM Organization` now, so a deal that
carries a company name without being linked to one would show empty boxes the
first time it is saved. Those deals are the ones made before the link was
always set: the name they carry is the organization's own name — it is the
docname — so it is enough to find it, or create it, and point at it.
"""

import frappe


def execute():
	deals = frappe.get_all(
		"CRM Deal",
		filters={"organization": ["is", "not set"], "organization_name": ["is", "set"]},
		fields=["name", "organization_name", "website", "industry", "annual_revenue", "territory"],
	)
	for deal in deals:
		organization = frappe.db.get_value(
			"CRM Organization", {"organization_name": deal.organization_name}, "name"
		)
		if not organization:
			doc = frappe.get_doc(
				{
					"doctype": "CRM Organization",
					"organization_name": deal.organization_name,
					"website": deal.website,
					"industry": deal.industry,
					"annual_revenue": deal.annual_revenue,
					"territory": deal.territory,
				}
			)
			doc.flags.ignore_mandatory = True
			try:
				doc.insert(ignore_permissions=True)
			except Exception:
				frappe.db.rollback()
				frappe.log_error(
					frappe.get_traceback(), f"No organization could be made for deal {deal.name}"
				)
				continue
			organization = doc.name
		frappe.db.set_value("CRM Deal", deal.name, "organization", organization, update_modified=False)
	frappe.db.commit()
