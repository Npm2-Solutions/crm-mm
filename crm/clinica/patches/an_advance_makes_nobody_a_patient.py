# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A deposit's advance invoice makes nobody a patient (doc 60).

A deposit paid for a health service at /prenota made its person a patient the day
they booked («Paziente dal…» before any visit), by the rule of the healthcare
invoice. The rules now leave the advance out; the cards it wrote go to the
person's first real fact - a visit, a check-in, the health data the centre keeps -
or are taken away, quietly (`paziente.ricalcola_dagli_acconti`).
"""

import frappe

from crm.clinica import paziente


def execute():
	if not frappe.db.table_exists(paziente.DOCTYPE):
		return
	paziente.ricalcola_dagli_acconti()
