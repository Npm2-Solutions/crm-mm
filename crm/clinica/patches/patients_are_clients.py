# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A patient is a client of the centre from the moment they became a patient
(`crm.clienti`): the patients already there get it, once, announcing nothing."""

import frappe
from frappe.utils import get_datetime


def execute():
	if not frappe.db.table_exists("Clinic Patient"):
		return
	for lead, dal in frappe.get_all("Clinic Patient", fields=["lead", "patient_since"], as_list=True):
		if not (lead and dal) or not frappe.db.exists("CRM Lead", lead):
			continue
		cliente_da = frappe.db.get_value("CRM Lead", lead, "client_since")
		if not cliente_da or get_datetime(dal) < get_datetime(cliente_da):
			frappe.db.set_value("CRM Lead", lead, "client_since", dal, update_modified=False)
