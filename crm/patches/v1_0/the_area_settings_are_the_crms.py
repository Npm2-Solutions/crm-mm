# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What the client area offers besides the email - the WhatsApp template of the news,
the number SMS leave from - moves from the clinic's settings to the area's own."""

import frappe

DA = "Clinic Settings"
A = "CRM Area Settings"
CAMPI = {"area_whatsapp_template": "whatsapp_template", "area_sms_number": "sms_number"}


def execute():
	for vecchio, nuovo in CAMPI.items():
		valore = frappe.db.sql(
			"select value from `tabSingles` where doctype=%s and field=%s", (DA, vecchio)
		)
		if valore and valore[0][0] and not frappe.db.get_single_value(A, nuovo):
			frappe.db.set_single_value(A, nuovo, valore[0][0])
	frappe.db.sql(
		"delete from `tabSingles` where doctype=%s and field in %s", (DA, tuple(CAMPI))
	)
