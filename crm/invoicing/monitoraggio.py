# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Watching the channel for silence.

The Sistema di Interscambio half. In invoicing, no news is not good news: an
invoice that left and was never answered looks exactly like one that went through,
and the five days to fix a rejection run from a notice nobody read.

The Sistema TS has its own watches, in its own module, for its own deadlines.
"""

from __future__ import annotations

import html

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
	from crm.notifiche.avvisi import avvisa as notifica

	testo = f"{titolo} - {azienda}"
	if frappe.db.exists(
		"CRM Notification",
		{
			"type": "Invoicing",
			"notification_text": html.escape(testo, quote=False),
			"creation": [">=", getdate()],
		},
	):
		return
	destinatari = frappe.get_all(
		"Has Role", filters={"role": "Invoicing Manager", "parenttype": "User"}, pluck="parent"
	)
	for utente in destinatari:
		notifica(
			utente,
			"Invoicing",
			testo=testo,
			oggetto=("CRM Invoicing Company", azienda),
			messaggio=dettaglio,
		)


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


def riconcilia_provider(rumoroso: bool = False) -> list[dict]:
	"""Ask the provider for what it is holding, for every company on that channel.

	Every ten minutes, because under the agency's account nothing calls a site back:
	an invoice that left sits in `inviato` until somebody asks. Quietly, since Itala
	down for ten minutes is no news; once a day, what it could not answer is logged.
	"""
	from crm.invoicing.api import reconcile_provider

	try:
		esiti = reconcile_provider()
	except Exception as errore:
		frappe.log_error(title="Provider reconciliation failed", message=str(errore))
		return []
	if rumoroso:
		for nome, esito in esiti.items():
			if esito.get("problems"):
				frappe.log_error(
					title="Provider reconciliation failed", message=f"{nome}: " + "; ".join(esito["problems"])
				)
	return [{"company": nome, **esito} for nome, esito in esiti.items()]


def riconcilia_provider_del_giorno() -> list[dict]:
	return riconcilia_provider(rumoroso=True)


def giornaliero() -> None:
	"""Everything invoicing watches, once a day. One failing never hides the rest."""
	for controllo in (leggi_ricevute, riconcilia_provider_del_giorno):
		try:
			controllo()
		except Exception:
			frappe.log_error(title=f"Invoicing watch failed: {controllo.__name__}")
