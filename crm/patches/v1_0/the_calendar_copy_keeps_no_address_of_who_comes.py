# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""An appointment's calendar copy keeps no address of the people who come.

The copy names them by their record, but the framework wrote on each of their rows
the address of a Contact when the Event was saved (`Event.set_participants_email`),
and a private Event reads to any user whose name is the address on one of its rows:
the client area's user of that address listed the copy and read its description,
the appointment's notes, and the events' reminders by email (crm/api/event.py) and
Google's invitations could go there. Older copies, from before the people were
named by their record, carry the address the appointment had for each of them. A
row of a copy keeps an address only where it names one of the appointment's
professionals, and then that professional's own, as every save of a copy keeps it
from now on (`copia_solo_ai_professionisti`). Only the rows that differ are
written, so it can run again.
"""

from collections import defaultdict

import frappe

from crm.fcrm.doctype.crm_appointment.crm_appointment import indirizzo_della_riga

#: How many appointments one query of their professionals names.
PEZZO = 500


def execute():
	Riga = frappe.qb.DocType("Event Participants")
	Evento = frappe.qb.DocType("Event")
	righe = (
		frappe.qb.from_(Riga)
		.join(Evento)
		.on(Evento.name == Riga.parent)
		.select(
			Riga.name,
			Riga.reference_doctype,
			Riga.reference_docname,
			Riga.email,
			Evento.reference_docname.as_("appuntamento"),
		)
		.where((Riga.parenttype == "Event") & (Evento.reference_doctype == "CRM Appointment"))
	).run(as_dict=True)
	if not righe:
		return

	professionisti = defaultdict(set)
	appuntamenti = sorted({riga.appuntamento for riga in righe if riga.appuntamento})
	for inizio in range(0, len(appuntamenti), PEZZO):
		for riga in frappe.get_all(
			"CRM Appointment Staff",
			filters={
				"parenttype": "CRM Appointment",
				"parent": ("in", appuntamenti[inizio : inizio + PEZZO]),
				"user": ("is", "set"),
			},
			fields=["parent", "user"],
		):
			professionisti[riga.parent].add(riga.user)

	for riga in righe:
		dovuto = indirizzo_della_riga(riga, professionisti[riga.appuntamento])
		if (riga.email or None) != dovuto:
			frappe.db.set_value("Event Participants", riga.name, "email", dovuto, update_modified=False)
