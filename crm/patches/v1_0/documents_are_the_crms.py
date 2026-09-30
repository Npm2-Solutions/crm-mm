# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A person's documents and their deliveries move from the clinic to the CRM
(docs/gestionale-medico/design.md, "Tre strati"): a beauty centre keeps a signed
consent, a gym a contract, as a medical centre keeps a report.

Before the models are synced, the DocTypes take the CRM's names and the
"Documenti" module - renamed, so their tables and rows stay as they are. The
clinic's own fields on them (who reads it, obscured, the visit, never online)
come back as its customisations (`crm/clinica/custom`), on the same columns.
"""

import frappe
from frappe.model.rename_doc import rename_doc

NOMI = {
	"Clinic Report Delivery": "CRM Document Delivery",
	"Clinic Document": "CRM Document",
}
MODULO = "Documenti"


def execute():
	if not frappe.db.exists("Module Def", MODULO):
		frappe.get_doc({"doctype": "Module Def", "module_name": MODULO, "app_name": "crm"}).insert(
			ignore_permissions=True
		)
	frappe.flags.ignore_route_conflict_validation = True
	try:
		for vecchio, nuovo in NOMI.items():
			if frappe.db.exists("DocType", vecchio) and not frappe.db.exists("DocType", nuovo):
				rename_doc("DocType", vecchio, nuovo, force=True)
			if frappe.db.exists("DocType", nuovo):
				frappe.db.set_value("DocType", nuovo, "module", MODULO, update_modified=False)
	finally:
		frappe.flags.ignore_route_conflict_validation = False
