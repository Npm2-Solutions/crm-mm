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
