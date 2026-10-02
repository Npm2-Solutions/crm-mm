# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Invoicing tries before it goes live, through Itala.

A company that has issued real invoices is live: its numbering is a fiscal fact,
and in test its next invoice would be numbered PROVA. It is live from the day of
its first invoice. A company that has issued nothing starts in test, on Itala, the
one channel offered to every centre - unless the agency chose its PEC. A Sistema TS
sent "through the provider" never had a provider to reach: it goes back to the
centre's own credentials.
"""

import frappe

AZIENDA = "CRM Invoicing Company"


def execute():
	for azienda in frappe.get_all(AZIENDA, fields=["name", "sdi_mode", "ts_mode", "live_since"]):
		prima = frappe.db.get_value(
			"CRM Invoice",
			{"company": azienda.name, "docstatus": 1},
			"posting_date",
			order_by="posting_date asc",
		)
		valori = {}
		if prima:
			valori["provider_environment"] = "production"
			if not azienda.live_since:
				valori["live_since"] = prima
		else:
			valori["provider_environment"] = "sandbox"
			if (azienda.sdi_mode or "export") == "export":
				valori["sdi_mode"] = "provider"
		if azienda.ts_mode == "provider":
			valori["ts_mode"] = "credenziali_studio"
		frappe.db.set_value(AZIENDA, azienda.name, valori, update_modified=False)
