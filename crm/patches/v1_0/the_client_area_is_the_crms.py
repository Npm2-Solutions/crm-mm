# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The client area moves from the clinic to the CRM (docs/verticali/clinica/design.md,
"Tre strati"): any centre gives its people their area, the clinic only adds to it.

Before the models are synced, its DocTypes take the CRM's names and the "Area"
module - renamed, so their tables and rows stay as they are - and the role of whoever
enters takes a name every centre can use.
"""

import frappe
from frappe.model.rename_doc import rename_doc

NOMI = {
	"Clinic Area Access": "CRM Area Access",
	"Clinic Area Passkey": "CRM Area Passkey",
	"Clinic Area Notice": "CRM Area Notice",
	"Clinic Message": "CRM Area Message",
}
RUOLI = {"Clinic Patient": "Client Area User"}
MODULO = "Area"


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
	for vecchio, nuovo in RUOLI.items():
		if frappe.db.exists("Role", vecchio) and not frappe.db.exists("Role", nuovo):
			rename_doc("Role", vecchio, nuovo, force=True)
