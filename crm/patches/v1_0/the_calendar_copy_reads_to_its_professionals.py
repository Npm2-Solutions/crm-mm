# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The calendar copy of an appointment reads to its professionals, never to its client.

The framework made a new Event its session's - a guest's for a booking from
/prenota, the desk's for one booked there - and the first professional was left
off its participants: a private Event, the practitioner could not read the copy
of their own appointment. The people who came were participants by their email,
which reads the copy to the client area's user of that address and which the
framework's reminders and Google's invitations write to. Every copy is made again
by its appointment (`CRMAppointment.sync_event`).
"""

import frappe


def execute():
	for nome in frappe.get_all(
		"CRM Appointment",
		filters={"event": ("is", "set"), "status": ("!=", "Cancelled")},
		pluck="name",
	):
		frappe.get_doc("CRM Appointment", nome).sync_event()
