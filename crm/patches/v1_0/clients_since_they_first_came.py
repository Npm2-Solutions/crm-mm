# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Who was a client already: the first time they came, or their first invoice.

The CRM keeps it from now on (`crm.clienti`); this finds it in the past, once, and
announces nothing: last year's clients are not news, and close no deal. Where a
module with rules of its own is on, it finds its own (the clinic: its patients).
"""

import frappe


def execute():
	from crm.clienti import cliente

	# the field as this release has it: never a silent skip
	frappe.reload_doc("fcrm", "doctype", "crm_lead")
	cliente.recupera()
