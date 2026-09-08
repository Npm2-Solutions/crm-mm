# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Write what has already been imported from Meta into the ledger.

Until now the question "have we already taken this submission in?" was answered
by looking for a lead carrying the leadgen id. Delete that lead and the answer
became no, so the hourly reconciliation — which re-reads the last two days of
every form — imported it again within the hour: deleting a lead asked for it
back instead of removing it.

The ledger answers instead, and it outlives the person. This fills it with what
the CRM holds right now, so the leads that are here today can be deleted and
stay deleted. A submission whose lead was already deleted before this patch is
unknown to us and may come back once; from then on the ledger has it.
"""

import frappe


def execute():
	if not frappe.db.exists("DocType", "Facebook Lead Import"):
		return

	seen = set(frappe.get_all("Facebook Lead Import", pluck="name"))
	rows = []

	for lead in frappe.get_all(
		"CRM Lead",
		filters={"facebook_lead_id": ["is", "set"]},
		fields=["name", "facebook_lead_id", "facebook_form_id", "creation"],
	):
		if lead.facebook_lead_id not in seen:
			rows.append((lead.facebook_lead_id, lead.facebook_form_id, lead.name, "Created", lead.creation))
			seen.add(lead.facebook_lead_id)

	for row in frappe.get_all(
		"CRM Lead Facebook Submission",
		filters={"parenttype": "CRM Lead"},
		fields=["leadgen_id", "form", "parent", "submitted_on"],
	):
		if row.leadgen_id and row.leadgen_id not in seen:
			rows.append((row.leadgen_id, row.form, row.parent, "Merged", row.submitted_on))
			seen.add(row.leadgen_id)

	for leadgen_id, form, lead, outcome, imported_on in rows:
		try:
			frappe.get_doc(
				{
					"doctype": "Facebook Lead Import",
					"leadgen_id": leadgen_id,
					"form": form or "",
					"form_name": frappe.db.get_value("Facebook Lead Form", form, "form_name") or "",
					"lead": lead,
					"outcome": outcome,
					"imported_on": imported_on,
				}
			).insert(ignore_permissions=True)
		except Exception:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), f"Meta: could not remember import {leadgen_id}")
		else:
			frappe.db.commit()
