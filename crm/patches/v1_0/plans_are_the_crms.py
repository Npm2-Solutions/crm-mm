# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Plans, programmes and exercises move from the clinic to the CRM
(docs/verticali/clinica/design.md, "Tre strati"): a gym's trainer writes plans as a
nutritionist does, the clinic only adds its kinds.

Before the models are synced, their DocTypes take the CRM's names and the "Piani"
module - renamed, so their tables and rows stay as they are. The clinic's own fields
on them (a diet's foods and targets, the dossier's visibility) come back as its
customisations (`crm/clinica/custom`), on the same columns.
"""

import frappe
from frappe.model.rename_doc import rename_doc

NOMI = {
	"Clinic Plan Moment": "CRM Personal Plan Moment",
	"Clinic Plan Item": "CRM Personal Plan Item",
	"Clinic Plan Log": "CRM Personal Plan Log",
	"Clinic Programme Stage": "CRM Programme Stage",
	"Clinic Library Import": "CRM Library Import",
	"Clinic Programme": "CRM Programme",
	"Clinic Exercise": "CRM Exercise",
	"Clinic Plan": "CRM Personal Plan",
}
MODULO = "Piani"


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
