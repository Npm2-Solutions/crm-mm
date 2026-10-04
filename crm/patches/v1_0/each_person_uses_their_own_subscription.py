# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""An appointment kept the one subscription whose entry it used (04/10/2026): in a
class only one person could use theirs, and the others paid. Now each person's
place keeps their own (`CRM Appointment Participant.subscription`): the
subscription an appointment had goes to its person's place. The appointment's old
column stays in the table, unread."""

import frappe

APPUNTAMENTO = "CRM Appointment"
PARTECIPANTE = "CRM Appointment Participant"


def execute():
	if not frappe.db.has_column(APPUNTAMENTO, "subscription") or not frappe.db.has_column(
		PARTECIPANTE, "subscription"
	):
		return
	persone = dict(frappe.db.sql("select name, lead from `tabCRM Subscription`"))
	for appuntamento, abbonamento in frappe.db.sql(
		"""select name, subscription from `tabCRM Appointment`
		where ifnull(subscription, '') != ''"""
	):
		persona = persone.get(abbonamento)
		if not persona:
			continue
		posto = frappe.db.get_value(
			PARTECIPANTE,
			{"parenttype": APPUNTAMENTO, "parent": appuntamento, "party_type": "CRM Lead", "party": persona},
			"name",
			order_by="idx asc",
		)
		if posto:
			frappe.db.set_value(PARTECIPANTE, posto, "subscription", abbonamento, update_modified=False)
