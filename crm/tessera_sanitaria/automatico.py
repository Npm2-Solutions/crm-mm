# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The night's reports to the Sistema TS, where the centre switched them on
(`CRM Invoicing Settings.auto_send_ts`, off to start with).

Each expense issued and not reported yet leaves as «Report» would send it, one by
one, with the company's own credentials or its accountant's mandate. Not a test
invoice, never a company that submits a file by hand (`export`), and never one
already refused: a rejection is corrected by somebody, and sending the same
document again every night would only repeat the refusal. Whoever manages
invoicing reads in the morning what did not leave and why.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint

#: A night does not report a backlog of years: the rest leaves the night after.
PER_NOTTE = 500


def attivo() -> bool:
	return bool(cint(frappe.db.get_single_value("CRM Invoicing Settings", "auto_send_ts")))


def da_comunicare(azienda: str) -> list[str]:
	"""The company's expenses to report tonight, the oldest first."""
	return frappe.get_all(
		"CRM Invoice",
		filters={
			"company": azienda,
			"docstatus": 1,
			"test_document": 0,
			"ts_status": "da_inviare",
		},
		order_by="posting_date asc, creation asc",
		pluck="name",
		limit=PER_NOTTE,
	)


def aziende() -> list[dict]:
	"""The companies that report healthcare expenses through the web service."""
	return frappe.get_all(
		"CRM Invoicing Company",
		filters={
			"enabled": 1,
			"sender_category": ["not in", ("", "non_sanitario")],
			"ts_mode": ["!=", "export"],
		},
		fields=["name", "company_name"],
	)


def ogni_notte() -> dict:
	"""The scheduled job. Returns, per company, how many left and what stopped."""
	if not attivo():
		return {}
	from crm.invoicing import monitoraggio
	from crm.tessera_sanitaria import trasporto

	esiti: dict[str, dict] = {}
	for azienda in aziende():
		inviate, fermate = 0, []
		for fattura in da_comunicare(azienda["name"]):
			try:
				esito = trasporto.invia_documento(fattura)
			except Exception as errore:
				frappe.db.rollback()
				fermate.append(f"{_numero(fattura)}: {frappe.utils.strip_html(str(errore))}")
				continue
			frappe.db.commit()  # nosemgrep: frappe-manual-commit — one report, one answer kept
			if esito.get("accepted"):
				inviate += 1
			else:
				fermate.append(f"{_numero(fattura)}: {esito.get('summary') or ''}")
		if fermate:
			monitoraggio.avvisa(
				_("Expenses the Sistema TS did not take tonight"),
				azienda["name"],
				"\n".join(fermate[:20]),
			)
		esiti[azienda["name"]] = {"sent": inviate, "stopped": fermate}
	return esiti


def _numero(fattura: str) -> str:
	return frappe.db.get_value("CRM Invoice", fattura, "document_number") or fattura
