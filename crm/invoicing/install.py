# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Seeding: the roles, and the qualification register.

The register ships as data, not as a fixture that a `bench migrate` overwrites: a
practice that corrects an entry has to keep the correction. So a code that already
exists is left alone, and only a missing one is created.
"""

from __future__ import annotations

import frappe

RUOLI = (
	("Invoicing Manager", "Issues, cancels and transmits invoices, and configures the register."),
	("Invoicing User", "Reads invoices and the register."),
)


def crea_ruoli() -> None:
	for nome, descrizione in RUOLI:
		if frappe.db.exists("Role", nome):
			continue
		frappe.get_doc(
			{
				"doctype": "Role",
				"role_name": nome,
				"desk_access": 1,
				"is_custom": 1,
				"search_bar": 1,
				"notifications": 1,
				"list_sidebar": 1,
				"form_sidebar": 1,
				"report": 1,
				"dashboard": 1,
				"description": descrizione,
			}
		).insert(ignore_permissions=True)


def imposta_predefiniti() -> None:
	impostazioni = frappe.get_single("CRM Invoicing Settings")
	if impostazioni.ts_silence_days:
		return
	impostazioni.ts_silence_days = 30
	impostazioni.certificate_warning_days = 90
	impostazioni.advances_in_stamp_base = 1
	impostazioni.attach_pdf = 1
	impostazioni.save(ignore_permissions=True)


def dopo_installazione() -> None:
	crea_ruoli()
	imposta_predefiniti()
	frappe.db.commit()
