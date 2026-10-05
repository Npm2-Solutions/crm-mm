# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The company doctor shipped as «Medico competente (invoices to the employer)»,
half in English, until the register spoke Italian (1 October 2026). A register
made before kept that name, and the language follower (`nella_lingua`) does not
know it for DottorCloud's: it is in neither language the register ships now. A
name still as it was shipped is written again, in the centre's language; one the
practice changed stays."""

import frappe

CODICE = "medico_competente"
COME_ERA = "Medico competente (invoices to the employer)"


def execute():
	from crm import lingue
	from crm.invoicing.install import parole_di
	from crm.tessera_sanitaria.engine.professioni import elenco

	professione = next((p for p in elenco() if p.codice == CODICE), None)
	if not professione:
		return
	frappe.db.set_value(
		"CRM Professional Qualification",
		{"name": CODICE, "qualification_name": COME_ERA},
		"qualification_name",
		parole_di(professione, lingue.del_centro())["qualification_name"],
		update_modified=False,
	)
