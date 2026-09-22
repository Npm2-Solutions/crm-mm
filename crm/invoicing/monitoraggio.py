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


def giornaliero() -> None:
	"""Everything invoicing watches, once a day."""
	leggi_ricevute()
