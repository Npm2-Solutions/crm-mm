# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Turn the company names written on people into companies.

`CRM Lead.organization` was free text while `CRM Deal.organization` was a Link:
two people of the same firm were two strings that looked alike, and the company
only became a real record at conversion. It is a Link on both now.

The values already in the column are the names of companies, and a
`CRM Organization` is named after itself — so the string a person carries IS the
link, as soon as the company exists. This creates the ones that do not, seeded
with what the person knows about them.
"""

import frappe


def execute():
	# a name with spaces around it would not match its own company
	frappe.db.sql("UPDATE `tabCRM Lead` SET organization = TRIM(organization) WHERE organization IS NOT NULL")
	frappe.db.commit()

	rows = frappe.get_all(
		"CRM Lead",
		filters={"organization": ["is", "set"]},
		fields=[
			"name",
			"organization",
			"website",
			"territory",
			"industry",
			"annual_revenue",
			"no_of_employees",
			"company_description",
		],
	)

	seen = set()
	for lead in rows:
		organization = (lead.organization or "").strip()
		if not organization or organization in seen:
			continue
		seen.add(organization)
		if frappe.db.exists("CRM Organization", organization):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "CRM Organization",
				"organization_name": organization,
				"website": lead.website,
				"territory": lead.territory,
				"industry": lead.industry,
				"annual_revenue": lead.annual_revenue,
				"no_of_employees": lead.no_of_employees,
				"company_description": lead.company_description,
			}
		)
		doc.flags.ignore_mandatory = True
		try:
			doc.insert(ignore_permissions=True)
		except Exception:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), f"No company could be made for {organization}")
		else:
			frappe.db.commit()
