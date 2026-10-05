# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A patient says so on their page and in the lists: `CRM Lead.patient_since` and
the "Patient" step of their relationship with the centre, from the patient cards
already there.

The field is the clinic's customisation, which the framework syncs after the
patches: synced here first, so that it is there to be written.
"""

import frappe
from frappe.modules.utils import sync_customizations_for_doctype

from crm.clinica import paziente


def execute():
	if not frappe.db.table_exists(paziente.DOCTYPE):
		return
	cartella = frappe.get_app_path("crm", "clinica", "custom")
	sync_customizations_for_doctype(
		frappe.get_file_json(frappe.get_app_path("crm", "clinica", "custom", "crm_lead.json")),
		cartella,
		"crm_lead.json",
	)
	frappe.clear_cache(doctype="CRM Lead")
	for lead, dal in frappe.get_all(paziente.DOCTYPE, fields=["lead", "patient_since"], as_list=True):
		if lead and frappe.db.exists("CRM Lead", lead):
			frappe.db.set_value(
				"CRM Lead",
				lead,
				{paziente.CAMPO: dal, "relationship": paziente.PAZIENTE},
				update_modified=False,
			)
