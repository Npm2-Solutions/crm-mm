# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What the first Itala reconciliation wrote wrong, put right (02/10/2026).

- Without a notice it wrote Itala's state in words the invoice does not have
  (`consegnato`, `accettato`, `rifiutato`): the guard on cancelling did not see a
  delivered invoice. They become the invoice's own (`consegnata`, `esito_pa`).
- It kept Itala's own id as the SdI's identifier. Where the two are the same the
  identifier is cleared: the real one comes with the next update, or when the
  invoice is asked about.
"""

import frappe

FATTURA = "CRM Invoice"
STATI = {"consegnato": "consegnata", "accettato": "esito_pa", "rifiutato": "esito_pa"}


def execute():
	for prima, dopo in STATI.items():
		frappe.db.set_value(FATTURA, {"sdi_status": prima}, "sdi_status", dopo, update_modified=False)
	for nome in frappe.get_all(
		FATTURA,
		filters={"sdi_provider_id": ["is", "set"], "sdi_identifier": ["is", "set"]},
		fields=["name", "sdi_provider_id", "sdi_identifier"],
	):
		if str(nome.sdi_identifier).strip() == str(nome.sdi_provider_id).strip():
			frappe.db.set_value(FATTURA, nome.name, "sdi_identifier", None, update_modified=False)
