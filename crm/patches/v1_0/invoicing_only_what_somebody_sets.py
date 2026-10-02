# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The issuing company, only with what somebody has to set (02/10/2026).

The invoices leave through Itala on the agency's account and come back the same way,
in both directions; the Agenzia's free service keeps the SdI documents; a healthcare
invoice to a person stays a paper original with its copy. Nobody chooses any of it
any more, and every company is put so. A company that had chosen the Agenzia's
service had joined it: it is ticked. A numbering left empty gets its series and the
first format of the examples.
"""

import frappe

from crm.invoicing.doctype.crm_invoicing_company.crm_invoicing_company import SEMPRE, SERIE
from crm.invoicing.engine.numerazione import FORMATO_DEFAULT

AZIENDA = "CRM Invoicing Company"


def execute():
	campi = ["name", "conservation_service", "number_format", *SERIE]
	for azienda in frappe.get_all(AZIENDA, fields=campi):
		valori = dict(SEMPRE)
		if azienda.conservation_service == "agenzia_entrate":
			valori["conservation_joined"] = 1
		for campo, serie in SERIE.items():
			if not (azienda.get(campo) or "").strip():
				valori[campo] = serie
		if not (azienda.number_format or "").strip():
			valori["number_format"] = FORMATO_DEFAULT
		frappe.db.set_value(AZIENDA, azienda.name, valori, update_modified=False)
