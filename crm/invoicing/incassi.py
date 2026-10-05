# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Whether the money of an invoice reached the centre (`CRM Invoice.collected_on`).

The invoice says how it was paid (`payment_method`, `payment_date`), which the
Sistema TS needs, but `payment_date` starts as the issue date whatever happened:
it cannot tell a paid invoice from one waiting. So collecting is a fact of its own:
a day, or nothing for an invoice still to collect.

An invoice to a person issued at the desk was paid there: it takes the payment
date the desk wrote in it (`alla_cassa`). One to a company or a public body, and
one issued by itself (a subscription's instalment), waits for somebody with
`fatture.incassi` to mark it. A credit note gives money back: it is never
collected.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import getdate

FATTURA = "CRM Invoice"
NOTE_DI_CREDITO = ("TD04", "TD08")


def da_incassare(doc) -> bool:
	"""Whether an invoice is one that is collected at all."""
	return doc.docstatus == 1 and (doc.document_type or "TD01") not in NOTE_DI_CREDITO


def alla_cassa(doc) -> None:
	"""An invoice to a person, issued at the desk, was paid at the desk."""
	if da_incassare(doc) and doc.recipient_type == "persona_fisica" and not doc.collected_on:
		doc.db_set("collected_on", doc.payment_date or doc.posting_date, update_modified=False)


@frappe.whitelist(methods=["POST"])
def set_collected(invoice: str, collected_on: str | None = None) -> dict:
	"""Collected on a day, or - no day - still to collect."""
	from crm.invoicing import documento
	from crm.permissions.livelli import verifica_nel_crm

	verifica_nel_crm("fatture.incassi", messaggio=_("You are not allowed to record payments"))
	doc = frappe.get_doc(FATTURA, invoice)
	doc.check_permission("read")
	if not da_incassare(doc):
		frappe.throw(_("Only an issued invoice is collected, and never a credit note"))
	giorno = getdate(collected_on) if collected_on else None
	if giorno and doc.posting_date and giorno < getdate(doc.posting_date) and not doc.advance_payment:
		frappe.throw(_("Collected before it was issued: mark it as paid before the invoice instead."))
	doc.db_set("collected_on", giorno, update_modified=False)
	documento.registra(
		doc,
		"collected",
		_("Collected on {0}").format(frappe.format(giorno, "Date")) if giorno else _("Back to collect"),
	)
	return {"collected_on": str(giorno) if giorno else None}
