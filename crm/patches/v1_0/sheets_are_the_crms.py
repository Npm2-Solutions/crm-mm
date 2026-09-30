# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The clinic's "Clinical sheet" is the CRM's "Sheet" with the mark of health data:
a beauty centre's treatment sheet and a practitioner's visit are written the same
way. The templates and their versions keep the mark; only the use changes name."""

import frappe


def execute():
	for doctype in ("CRM Form Template", "CRM Form Template Version"):
		tabella = frappe.qb.DocType(doctype)
		(
			frappe.qb.update(tabella)
			.set(tabella.use, "Sheet")
			.set(tabella.clinical, 1)
			.where(tabella.use == "Clinical sheet")
		).run()
