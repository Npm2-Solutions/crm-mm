# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The clinic's new patients pipeline is the CRM's new clients pipeline.

- Which pipeline, and the stage after a booking, move from the clinic's settings -
  empty now, and gone with this release - to `CRM Client Settings`.
- The automations that listened to "Became Patient" listen to "Became Client":
  with the clinic on it is the same moment, in the clinic's words.
- A saved dashboard's "New patients" and "Cost per new patient" are the CRM's
  widgets, which say so with the clinic on.
"""

import json

import frappe

DA = "Clinic Settings"
A = "CRM Client Settings"
CAMPI = {"new_patients_pipeline": "new_clients_pipeline", "booked_stage": "booked_stage"}
WIDGET = {"new_patients": "new_clients", "meta_cost_per_patient": "meta_cost_per_client"}


def execute():
	# the settings as this release has them: never a silent skip
	frappe.reload_doc("clienti", "doctype", "crm_client_settings")
	for vecchio, nuovo in CAMPI.items():
		valore = frappe.db.sql("select value from `tabSingles` where doctype=%s and field=%s", (DA, vecchio))
		if valore and valore[0][0] and not frappe.db.get_single_value(A, nuovo):
			frappe.db.set_single_value(A, nuovo, valore[0][0])
	frappe.db.delete("Singles", {"doctype": DA})

	for doctype in ("CRM Automation", "CRM Automation Trigger"):
		tabella = frappe.qb.DocType(doctype)
		(
			frappe.qb.update(tabella)
			.set(tabella.trigger_event, "Became Client")
			.where(tabella.trigger_event == "Became Patient")
		).run()

	for nome, layout in frappe.get_all("CRM Dashboard", fields=["name", "layout"], as_list=True):
		try:
			elementi = json.loads(layout or "[]")
		except ValueError:
			continue
		cambiati = False
		for elemento in elementi if isinstance(elementi, list) else []:
			if isinstance(elemento, dict) and elemento.get("name") in WIDGET:
				elemento["name"] = WIDGET[elemento["name"]]
				cambiati = True
		if cambiati:
			frappe.db.set_value("CRM Dashboard", nome, "layout", json.dumps(elementi), update_modified=False)
