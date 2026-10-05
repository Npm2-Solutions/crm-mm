# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A person and their deal said «1-10 employees»: the framework gives a choice
its first option when nothing was chosen, and a person with no company has
nobody to count. Where there is no company, the count the framework chose goes;
a company's, and one somebody chose, stay."""

import frappe
from frappe.query_builder.functions import IfNull


def execute():
	for doctype in ("CRM Lead", "CRM Deal"):
		tabella = frappe.qb.DocType(doctype)
		(
			frappe.qb.update(tabella)
			.set(tabella.no_of_employees, "")
			.where(tabella.no_of_employees == "1-10")
			.where(IfNull(tabella.organization, "") == "")
		).run()
