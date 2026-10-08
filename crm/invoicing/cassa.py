# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The desk's cash closing (`CRM Cash Closing`): at the end of the day, what was
collected by each way of paying and by who issued it, the credit notes that gave
money back, the cash the drawer should hold against the cash counted.

Read and written by whoever records payments (`fatture.incassi`), through the
reception desk (`crm.api.oggi`). A test invoice is never money: it stays out. The
arithmetic is `cassa_regole`.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import get_fullname, getdate, now_datetime

from crm.invoicing import cassa_regole as R
from crm.invoicing import incassi
from crm.invoicing.engine import voci

FATTURA = "CRM Invoice"
CHIUSURA = "CRM Cash Closing"
FAMIGLIA = "modalita_pagamento"


def nome_del_metodo(codice: str | None) -> str:
	"""A payment method by its name, never its code: «Cash», «Card or app»."""
	return _(voci.etichetta(FAMIGLIA, codice)) if codice else _("Not said")


def _chi_ha_emesso(nomi: list[str], proprietari: dict[str, str]) -> dict[str, str]:
	"""Who issued each invoice: its log's «issued», else who made it."""
	chi = dict(proprietari)
	if nomi:
		for riga in frappe.get_all(
			"CRM Invoice Log",
			filters={"invoice": ["in", nomi], "event": "issued"},
			fields=["invoice", "actor"],
			order_by="occurred_on asc",
		):
			if riga.actor:
				chi[riga.invoice] = riga.actor
	return chi


def _righe(filtri: dict) -> list:
	righe = frappe.get_list(
		FATTURA,
		filters={"docstatus": 1, "test_document": 0, **filtri},
		fields=["name", "document_number", "payment_method", "grand_total", "net_payable", "owner"],
		order_by="creation asc",
		limit_page_length=0,
	)
	chi = _chi_ha_emesso([r.name for r in righe], {r.name: r.owner for r in righe})
	return [
		{
			"name": riga.name,
			"payment_method": riga.payment_method,
			"amount": incassi.da_pagare(riga),
			"issued_by": chi.get(riga.name) or "",
		}
		for riga in righe
	]


def riepilogo_del_giorno(giorno) -> dict:
	"""The day as the closing reads it, with names for the screen, and its closing
	if it was closed."""
	giorno = getdate(giorno)
	incassate = _righe({"collected_on": giorno, "document_type": ["not in", incassi.NOTE_DI_CREDITO]})
	restituite = _righe({"posting_date": giorno, "document_type": ["in", incassi.NOTE_DI_CREDITO]})
	conti = R.riepilogo(incassate, restituite)
	for voce in conti["methods"]:
		voce["name"] = nome_del_metodo(voce["method"])
		voce["cash"] = voce["method"] == R.CONTANTI
	for chi in conti["by_user"]:
		chi["full_name"] = get_fullname(chi["user"]) if chi["user"] else _("Nobody")
	return {"date": str(giorno), **conti, "closing": chiusura_del(giorno)}


def chiusura_del(giorno) -> dict | None:
	nome = frappe.db.get_value(CHIUSURA, {"date": getdate(giorno)}, "name")
	if not nome:
		return None
	doc = frappe.get_doc(CHIUSURA, nome)
	return {
		"name": doc.name,
		"closed_by": doc.closed_by,
		"closed_by_name": get_fullname(doc.closed_by) if doc.closed_by else "",
		"closed_on": str(doc.closed_on) if doc.closed_on else None,
		"counted_cash": doc.counted_cash,
		"expected_cash": doc.expected_cash,
		"difference": doc.difference,
		"note": doc.note or "",
	}


def chiudi(giorno, contati, nota: str | None = None) -> dict:
	"""The day closed with the cash counted: what the day says now, kept. A day
	closed again is counted again, on the same closing."""
	giorno = getdate(giorno)
	if giorno > getdate():
		frappe.throw(_("A day that has not come yet cannot be closed"))
	try:
		contati = float(contati)
	except (TypeError, ValueError):
		frappe.throw(_("Write the cash counted in the drawer"))
	if contati < 0:
		frappe.throw(_("The cash counted cannot be below zero"))
	conti = riepilogo_del_giorno(giorno)
	nome = frappe.db.get_value(CHIUSURA, {"date": giorno}, "name")
	doc = frappe.get_doc(CHIUSURA, nome) if nome else frappe.new_doc(CHIUSURA)
	doc.update(
		{
			"date": giorno,
			"closed_by": frappe.session.user,
			"closed_on": now_datetime(),
			"collected_total": conti["collected"],
			"refunded_total": conti["refunded"],
			"expected_cash": conti["expected_cash"],
			"counted_cash": R.centesimi(contati),
			"difference": R.differenza(contati, conti["expected_cash"]),
			# closed again with nothing written, the day keeps what was written
			"note": (nota or "").strip() or doc.get("note") or "",
		}
	)
	doc.set(
		"methods",
		[
			{
				"payment_method": voce["method"],
				"method_name": voce["name"],
				"collected": voce["collected"],
				"refunded": voce["refunded"],
				"invoices": voce["count"],
			}
			for voce in conti["methods"]
		],
	)
	# only this door writes a closing: its numbers are the day's, never typed
	doc.flags.dalla_cassa = True
	doc.save(ignore_permissions=True)
	return riepilogo_del_giorno(giorno)
