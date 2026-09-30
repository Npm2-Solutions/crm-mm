# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The plans and programmes written before they were the CRM's were written as
health data, read like the clinical record: they keep the mark (`clinical`), and
so does whoever reads them. From now on the kind decides: a diet or exercises at
home carry it, a training or habits do not.

And where the agency hosts the exercises' pictures moves from the clinic's settings
to the area's, with the exercises.
"""

import frappe


def execute():
	for doctype in ("CRM Personal Plan", "CRM Programme"):
		if frappe.db.has_column(doctype, "clinical"):
			frappe.db.sql(f"update `tab{doctype}` set clinical = 1")  # nosemgrep
	valore = frappe.db.sql(
		"select value from tabSingles where doctype = 'Clinic Settings' and field = 'exercise_media_url'"
	)
	if valore and valore[0][0] and not frappe.db.get_single_value("CRM Area Settings", "exercise_media_url"):
		frappe.db.set_single_value("CRM Area Settings", "exercise_media_url", valore[0][0])
	frappe.db.sql("delete from tabSingles where doctype = 'Clinic Settings' and field = 'exercise_media_url'")
