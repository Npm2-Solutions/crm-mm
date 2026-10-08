# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The dental care plans become the CRM's quotes (docs/verticali/clinica/design.md,
"Tre strati"): a beauty centre's package and a gym's personal training are quotes
as a dentist's care plan is.

Before the models are synced, the DocTypes take the CRM's names and the
"Preventivi" module - renamed, so their tables and rows stay as they are. The
clinic's own fields on them (the tooth and its surfaces, who reads it, obscured)
come back as its customisations (`crm/clinica/custom`), on the same columns.
"""

import frappe
from frappe.model.rename_doc import rename_doc

NOMI = {
	"Clinic Care Plan Item": "CRM Quote Item",
	"Clinic Care Plan": "CRM Quote",
}
MODULO = "Preventivi"


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
