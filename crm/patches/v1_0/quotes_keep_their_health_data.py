# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The quotes written before they were the CRM's were a dentist's care plans: they
keep the mark of health data (`clinical`), and so does whoever reads them. From now
on who writes a quote decides: a health professional's carries the mark.

And which pipeline quotes move goes from the clinic's settings to the quotes' own.
"""

import frappe

DOCTYPE = "CRM Quote"
IMPOSTAZIONI = "CRM Quote Settings"


def execute():
	# the DocTypes as this release has them, with the mark: never a silent skip
	frappe.reload_doc("preventivi", "doctype", "crm_quote")
	frappe.reload_doc("preventivi", "doctype", "crm_quote_settings")
	frappe.db.sql(f"update `tab{DOCTYPE}` set clinical = 1")  # nosemgrep
	valore = frappe.db.sql(
		"select value from tabSingles where doctype = 'Clinic Settings' and field = 'quotes_pipeline'"
	)
	if (
		valore
		and valore[0][0]
		and frappe.db.exists("CRM Pipeline", valore[0][0])
		and not frappe.db.get_single_value(IMPOSTAZIONI, "quotes_pipeline")
	):
		frappe.db.set_single_value(IMPOSTAZIONI, "quotes_pipeline", valore[0][0])
	frappe.db.sql("delete from tabSingles where doctype = 'Clinic Settings' and field = 'quotes_pipeline'")
