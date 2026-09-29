# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The invoices already issued fill the billing details they carry.

A patient invoiced last month should not be asked for their codice fiscale again
the day the fiscal profile arrives. Every confirmed invoice gives back what it
knows, newest first, only where the profile is still empty: the most recent
address wins, and nothing somebody wrote is overwritten. Invoices made out to
somebody else - a parent paying for a child - give back nothing, as they will from
now on.
"""

import frappe


def execute():
	from crm.invoicing.anagrafica import completa_da_fattura

	for numero, nome in enumerate(
		frappe.get_all(
			"CRM Invoice",
			filters={"docstatus": 1, "party": ("is", "set")},
			order_by="posting_date desc, creation desc",
			pluck="name",
		),
		start=1,
	):
		completa_da_fattura(frappe.get_doc("CRM Invoice", nome))
		if numero % 200 == 0:
			frappe.db.commit()
