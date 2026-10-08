# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A call nobody answered is still a missed call.

When a call counts as missed became the centre's (Settings > Phone > Answering
service, «Missed calls», doc 52): a call everyone rang and nobody picked up counts
from the start, as it always did. A new field of a single document takes no
default by itself, so a centre that saved its answering settings before would
have read it switched off: it gets its default where nothing is written.
"""

import frappe

DOCTYPE = "CRM Answering Settings"
CAMPO = "missed_when_nobody_answers"


def execute():
	scritto = frappe.db.sql("select 1 from `tabSingles` where doctype=%s and field=%s", (DOCTYPE, CAMPO))
	salvato = frappe.db.sql("select 1 from `tabSingles` where doctype=%s limit 1", DOCTYPE)
	if salvato and not scritto:
		frappe.db.set_single_value(DOCTYPE, CAMPO, 1)
