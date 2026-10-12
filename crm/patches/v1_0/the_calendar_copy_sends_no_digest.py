# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""An appointment's calendar copy is left out of the framework's nightly digest.

An Event is made with «Send reminder» on, and every night the framework mails each
user the events of their day that have it (`send_event_digest`, «Upcoming Events
for Today», in English and on a 12-hour clock): the first professional, who owns
the copy, got its subject - the service and the people - and its description, the
appointment's notes. The copies sync_event makes from now on say no
(`send_reminder` 0); this switches off the ones made before, and only those: an
Event the centre makes itself keeps the framework's digest. It can run again.
"""

import frappe


def execute():
	Evento = frappe.qb.DocType("Event")
	(
		frappe.qb.update(Evento)
		.set(Evento.send_reminder, 0)
		.where((Evento.reference_doctype == "CRM Appointment") & (Evento.send_reminder == 1))
	).run()
