# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The agenda's settings say what the agenda does.

The grid's step came with the agenda drawn again (docs/crm/56): where
nothing is written the agenda moves by the field's default, 15 minutes. A
centre whose settings were saved before had nothing written, as a new field of
a single document takes no default by itself, so Settings > Agenda > Agenda &
reminders showed «Choose…» over a grid that moved by 15. The same for the
opening view of a centre that never saved one: the agenda opens on the day.
Each takes its default from the DocType, where nothing is written.
"""

import frappe

CAMPI = ("calendar_grid_step", "default_calendar_view")


def execute():
	meta = frappe.get_meta("FCRM Settings")
	for campo in CAMPI:
		definizione = meta.get_field(campo)
		if not definizione or not definizione.default:
			continue
		if not frappe.db.get_single_value("FCRM Settings", campo):
			frappe.db.set_single_value("FCRM Settings", campo, definizione.default)
