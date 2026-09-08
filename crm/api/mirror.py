# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Keep the deal's copy of the person and the company honest.

A deal used to receive a full copy of the lead at conversion — name, job title,
company, industry, revenue, socials — and then the two were free to disagree
forever. Every other CRM stores that once and associates: Salesforce hangs the
Opportunity off the Account and reaches the people through Contact Roles,
HubSpot and Pipedrive associate a Deal with a Contact and a Company.

Here the fields stay on the deal, because lists, boards and templates read them,
but they are `fetch_from` mirrors now: the lead and the organization are the
source, the deal only shows what they say. Frappe fills a mirror when the deal
itself is saved, which is not enough — the person is edited on their own page,
not on the deal — so these hooks push a change out to the deals that show it.
"""

import frappe

# deal fieldname → source fieldname, per source document
FROM_LEAD = {
	"first_name": "first_name",
	"last_name": "last_name",
	"lead_name": "lead_name",
	"salutation": "salutation",
	"gender": "gender",
	"job_title": "job_title",
}

FROM_ORGANIZATION = {
	"organization_name": "organization_name",
	"website": "website",
	"organization_logo": "organization_logo",
	"no_of_employees": "no_of_employees",
	"annual_revenue": "annual_revenue",
	"industry": "industry",
	"company_description": "company_description",
	"linkedin": "linkedin",
	"twitter": "twitter",
	"facebook": "facebook",
}


def _changed(doc, fieldmap: dict) -> dict:
	"""What the deals showing this document have to be told about."""
	previous = doc.get_doc_before_save()
	if not previous:
		return {}
	return {
		deal_field: doc.get(source_field)
		for deal_field, source_field in fieldmap.items()
		if previous.get(source_field) != doc.get(source_field)
	}


def _push(link_field: str, name: str, values: dict) -> None:
	if not values:
		return
	for deal in frappe.get_all("CRM Deal", filters={link_field: name}, pluck="name"):
		# no save: these are mirrors, and re-running the deal's own validation
		# on somebody else's edit would be a surprise (and an SLA recompute)
		frappe.db.set_value("CRM Deal", deal, values, update_modified=False)


def on_lead_updated(doc, method=None):
	_push("lead", doc.name, _changed(doc, FROM_LEAD))


def on_organization_updated(doc, method=None):
	_push("organization", doc.name, _changed(doc, FROM_ORGANIZATION))
