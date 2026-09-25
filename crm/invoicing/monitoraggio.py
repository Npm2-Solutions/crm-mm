# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Watching the channel for silence.

The Sistema di Interscambio half. In invoicing, no news is not good news: an
invoice that left and was never answered looks exactly like one that went through,
and the five days to fix a rejection run from a notice nobody read.

The Sistema TS has its own watches, in its own module, for its own deadlines.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import getdate


def avvisa(titolo: str, azienda: str, dettaglio: str) -> None:
	"""One notification per condition, per company, per day.

	`notification_text` carries the stable half - the condition and who it is about -
	so it can be deduplicated; the detail, which moves as documents are added, goes
	in the message. An alert repeated every hour is noise, and noise is how the one
	that mattered gets scrolled past.
	"""
	testo = f"{titolo} - {azienda}"
	if frappe.db.exists(
		"CRM Notification",
		{"type": "Invoicing", "notification_text": testo, "creation": [">=", getdate()]},
	):
		return
	destinatari = frappe.get_all(
		"Has Role", filters={"role": "Invoicing Manager", "parenttype": "User"}, pluck="parent"
	)
	for utente in destinatari:
		if not frappe.db.get_value("User", utente, "enabled"):
			continue
		frappe.get_doc(
			{
				"doctype": "CRM Notification",
				"from_user": "Administrator",
				"to_user": utente,
				"type": "Invoicing",
				"notification_text": testo,
				"message": dettaglio,
				"notification_type_doctype": "CRM Invoicing Company",
				"notification_type_doc": azienda,
			}
		).insert(ignore_permissions=True)


def leggi_ricevute() -> list[dict]:
	"""Apply the SdI notices sitting in the mailbox.

	Not a monitoring check but it belongs in the same sweep: the PEC route has no
	webhook, and an unread mailbox leaves every invoice in `inviato` - which looks
	exactly like nothing being wrong.
	"""
	from crm.invoicing.sdi import ricezione

	if not frappe.db.exists("CRM Invoicing Company", {"sdi_mode": "pec", "enabled": 1}):
		return []
	return ricezione.scansiona_posta()


def riconcilia_provider() -> list[dict]:
	"""Ask the provider for what it is holding, for every company on that channel.

	The webhook is the fast path and this is the one that catches what it missed: a
	delivery that never arrived leaves no trace anywhere, and the invoice it was
	about sits in `inviato` looking exactly like one that went through.
	"""
	from crm.invoicing.api import reconcile_provider

	try:
		esiti = reconcile_provider()
	except Exception as errore:
		frappe.log_error(title="Provider reconciliation failed", message=str(errore))
		return []
	return [{"company": nome, **esito} for nome, esito in esiti.items()]


def giornaliero() -> None:
	"""Everything invoicing watches, once a day. One failing never hides the rest."""
	for controllo in (leggi_ricevute, riconcilia_provider):
		try:
			controllo()
		except Exception:
			frappe.log_error(title=f"Invoicing watch failed: {controllo.__name__}")
