# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""A patient's parent or guardian becomes a link between two people.

The patient card had a guardian field of its own. Who looks after whom is a matter
of the people, not of the clinic - a gym has children booked by their parents too
- and it now lives in `CRM Related Person`, read by the booking pages, the invoice
and the consent register. What the old field held is moved there, as somebody who
acts for the patient; the column stays in the table until it is trimmed.
"""

import frappe

_RELAZIONE = {"Parent": "Parent", "Legal guardian": "Legal guardian"}


def execute():
	if not frappe.db.table_exists("Clinic Patient") or not frappe.db.has_column("Clinic Patient", "guardian"):
		return
	from crm.persone.collegate import assicura_legame

	has_relation = frappe.db.has_column("Clinic Patient", "guardian_relation")
	righe = frappe.db.sql(
		f"""select lead, guardian{", guardian_relation" if has_relation else ""}
		from `tabClinic Patient` where ifnull(guardian, '') != '' and guardian != lead""",
		as_dict=True,
	)
	for riga in righe:
		if not (frappe.db.exists("CRM Lead", riga.lead) and frappe.db.exists("CRM Lead", riga.guardian)):
			continue
		relazione = _RELAZIONE.get(riga.get("guardian_relation"), "Other")
		assicura_legame(riga.lead, riga.guardian, relazione, represents=1)
