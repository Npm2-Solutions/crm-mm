# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The last visit and its service, from the appointments already there.

Recalls pick people by when they last came (docs/gestionale-medico, the second
seam): the agenda keeps it from now on, and this finds it in the past. Written
straight to the table, as the agenda writes it: nobody edited the person.
"""

import frappe

from crm.fcrm.doctype.crm_appointment.crm_appointment import person_of


def execute():
	Appt = frappe.qb.DocType("CRM Appointment")
	Part = frappe.qb.DocType("CRM Appointment Participant")
	righe = (
		frappe.qb.from_(Part)
		.join(Appt)
		.on(Part.parent == Appt.name)
		.select(Appt.starts_on, Appt.service, Part.party_type, Part.party)
		.where(
			(Part.parenttype == "CRM Appointment")
			& (Appt.status != "Cancelled")
			& (
				(Part.status == "Attended")
				| ((Appt.status == "Completed") & Part.status.notin(["No Show", "Cancelled"]))
			)
		)
		.orderby(Appt.starts_on)
		.run(as_dict=True)
	)
	ultime: dict[str, tuple] = {}
	for riga in righe:
		persona = person_of(riga.party_type, riga.party)
		if persona:
			# ordered by start: the last one wins
			ultime[persona] = (frappe.utils.getdate(riga.starts_on), riga.service)
	for persona, (giorno, servizio) in ultime.items():
		frappe.db.set_value(
			"CRM Lead", persona, {"last_visit": giorno, "last_service": servizio}, update_modified=False
		)
