# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The deals' side panel keeps the lost reason once (crm/fcrm/doctype/utils.py):
it was added and taken away by whichever deal last changed stage."""

import json

import frappe

from crm.fcrm.doctype.utils import with_lost_reason_section

LAYOUT = "CRM Deal-Side Panel"


def execute():
	if not frappe.db.exists("CRM Fields Layout", LAYOUT):
		return
	layout = frappe.db.get_value("CRM Fields Layout", LAYOUT, "layout")
	try:
		sections = json.loads(layout or "[]")
	except ValueError:
		return
	if not isinstance(sections, list):
		return
	kept = with_lost_reason_section(sections)
	if kept is not sections:
		frappe.db.set_value("CRM Fields Layout", LAYOUT, "layout", json.dumps(kept), update_modified=False)
