# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""What the Sistema TS module adds to the interface.

These endpoints exist only where healthcare expenses are reported. An installation
that issues ordinary invoices never loads this file, and `crm.invoicing` never
imports it - the traffic goes the other way, through `crm.invoicing.estensioni`.
"""

from __future__ import annotations

import frappe
from frappe import _

from crm.tessera_sanitaria import documento as ts
from crm.tessera_sanitaria.engine.professioni import elenco as professioni_di_serie


@frappe.whitelist(methods=["POST"])
def send_to_ts(invoice: str, operation: str = "") -> dict:
	"""Report one issued invoice to the Sistema TS, synchronously.

	Synchronous on purpose: the answer comes back the same day, not on 20 January
	with four thousand rows behind it. On `export` companies this refuses and points
	at the file instead - and a failure here never touches the invoice, which the
	patient already has.
	"""
	from crm.tessera_sanitaria import trasporto as trasporto_ts

	return trasporto_ts.invia_documento(invoice, operation or None)


@frappe.whitelist(methods=["POST"])
def probe_delegation(company: str) -> dict:
	"""Find out whether an Entratel mandate exists, by sending one real document.

	The alternative is asking, and practices answer that question wrong without
	meaning to - they do not know. Rejection 105 means there is no mandate, 106 means
	there is one, and the company is moved to match.
	"""
	from crm.tessera_sanitaria import trasporto as trasporto_ts

	frappe.has_permission("CRM Invoicing Company", "write", throw=True)
	return trasporto_ts.sonda_delega(company)


@frappe.whitelist(methods=["POST"])
def record_ts_outcome(submission: str, code: str, message: str = "", protocol: str = "") -> dict:
	"""Record the outcome of a Sistema TS submission."""
	frappe.has_permission("CRM TS Submission", "write", throw=True)
	ts.segna_esito(submission, code, message, protocol)
	return {"submission": submission, "code": code}


@frappe.whitelist()
def ts_status(company: str, year: int) -> dict:
	"""What is still outstanding for a year, and how long there is left."""
	frappe.has_permission("CRM TS Submission", "read", throw=True)
	return ts.stato(company, int(year))


@frappe.whitelist(methods=["POST"])
def prepare_ts_submission(company: str, year: int) -> dict:
	"""Build the Sistema TS file for a year.

	Invoices that do not validate are listed and left behind rather than holding the
	whole year hostage: a single broken row must not cost the deadline.
	"""
	frappe.has_permission("CRM TS Submission", "create", throw=True)
	return ts.prepara_invio(company, int(year))


@frappe.whitelist()
def shipped_qualifications() -> list[dict]:
	"""The register as it ships, for comparison with what is stored.

	Useful when a rule moves: the file is where the research lives, the records are
	what the practice runs on, and seeing them side by side is how a change gets
	noticed instead of silently diverging.
	"""
	frappe.has_permission("CRM Professional Qualification", "read", throw=True)
	return [
		{
			"code": p.codice,
			"label": p.etichetta,
			"category": p.categoria,
			"vat_exempt": p.esente_iva,
			"sdi_rule": p.regola_sdi,
			"ts_required": p.obbligo_ts,
			"needs_verification": list(p.da_verificare),
			"stored": bool(frappe.db.exists("CRM Professional Qualification", p.codice)),
		}
		for p in professioni_di_serie()
	]
