# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Seed the invoicing roles and the qualification register.

Idempotent by design: it never touches a code that already has a record, so a
practice that corrected an entry keeps the correction across every migration.
"""

import frappe

from crm.invoicing.install import crea_ruoli, imposta_predefiniti, semina_qualifiche


def execute():
	if not frappe.db.exists("DocType", "CRM Professional Qualification"):
		return
	crea_ruoli()
	semina_qualifiche()
	imposta_predefiniti()
