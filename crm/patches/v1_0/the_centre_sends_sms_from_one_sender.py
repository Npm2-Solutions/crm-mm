# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's SMS leave from one sender (doc 52, 02/10/2026).

The client area and the waiting list each had their own "SMS from" number; now
every SMS of the centre leaves from the sender on Twilio's page. The number a
centre had written in one of them becomes that sender, so nothing it sent
before comes from somewhere else now. The two fields are gone from their
DocTypes: what they held is read where Frappe keeps a single's values.
"""

import frappe
from frappe.query_builder import DocType

TWILIO = "CRM Twilio Settings"
VECCHI = (("CRM Area Settings", "sms_number"), ("CRM Waiting List Settings", "sms_number"))


def execute():
	if frappe.db.get_single_value(TWILIO, "sms_from"):
		return
	for doctype, campo in VECCHI:
		numero = _valore(doctype, campo)
		if numero:
			frappe.db.set_single_value(TWILIO, {"sms_from": "Number", "sms_sender_number": numero})
			return


def _valore(doctype: str, campo: str) -> str:
	singoli = DocType("Singles")
	righe = (
		frappe.qb.from_(singoli)
		.select(singoli.value)
		.where((singoli.doctype == doctype) & (singoli.field == campo))
		.run()
	)
	return ((righe[0][0] if righe else "") or "").strip()
