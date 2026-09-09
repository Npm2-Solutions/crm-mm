# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Watching for silence.

In invoicing, no news is not good news. The failures of this domain are quiet and
annual: an expired certificate makes every submission fail with code 002 and says
nothing; a button nobody pressed produces no error at all - it produces absence,
and absence is found in January with the deadline a week away.

So the daily job looks for absence rather than for errors.
"""

from __future__ import annotations

from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import getdate, now_datetime

from crm.invoicing.engine.sistema_ts import scadenza_invio


def _aziende_sanitarie() -> list[dict]:
	return frappe.get_all(
		"CRM Invoicing Company",
		filters={"enabled": 1, "sender_category": ["not in", ("", "non_sanitario")]},
		fields=["name", "sender_category", "ts_certificate", "ts_mode"],
	)


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


def controlla_certificati() -> list[dict]:
	"""The Sistema TS certificate expires and is reissued.

	Once it has, every submission fails with code 002 - and it fails silently until
	somebody reads a response. Ninety days of warning is the point of this check.
	"""
	from crm.invoicing.engine.sistema_ts import Cifratore

	giorni = frappe.db.get_single_value("CRM Invoicing Settings", "certificate_warning_days") or 90
	rilievi: list[dict] = []
	for azienda in _aziende_sanitarie():
		if not azienda.get("ts_certificate"):
			rilievi.append({"company": azienda["name"], "issue": "missing"})
			continue
		try:
			from crm.invoicing.ts import contenuto_allegato

			cifratore = Cifratore.da_certificato(contenuto_allegato(azienda["ts_certificate"]))
		except Exception as errore:
			rilievi.append({"company": azienda["name"], "issue": "unreadable", "detail": str(errore)})
			avvisa(
				_("Sistema TS certificate unusable"),
				azienda["name"],
				_("The certificate cannot be read: every submission would fail with code 002."),
			)
			continue
		if cifratore.scadenza and (cifratore.scadenza - getdate()).days <= giorni:
			rilievi.append(
				{
					"company": azienda["name"],
					"issue": "expiring",
					"expires_on": str(cifratore.scadenza),
				}
			)
			avvisa(
				_("Sistema TS certificate expiring"),
				azienda["name"],
				_("It expires on {0}. Download the current kit before then.").format(cifratore.scadenza),
			)
	return rilievi


def controlla_silenzio() -> list[dict]:
	"""No accepted submission for N days.

	The most dangerous check in the file, because the condition it looks for
	produces no error anywhere else.
	"""
	giorni = frappe.db.get_single_value("CRM Invoicing Settings", "ts_silence_days") or 30
	soglia = now_datetime() - timedelta(days=giorni)
	rilievi: list[dict] = []
	for azienda in _aziende_sanitarie():
		in_attesa = frappe.db.count(
			"CRM Invoice",
			{
				"company": azienda["name"],
				"docstatus": 1,
				"ts_status": ["in", ("da_inviare", "pronto_export")],
			},
		)
		if not in_attesa:
			continue
		ultimo = frappe.db.get_value(
			"CRM TS Submission",
			{"company": azienda["name"], "status": "accolto"},
			"sent_on",
			order_by="sent_on desc",
		)
		if ultimo and ultimo >= soglia:
			continue
		rilievi.append(
			{"company": azienda["name"], "pending": in_attesa, "last_accepted": str(ultimo or "never")}
		)
		avvisa(
			_("No accepted Sistema TS submission"),
			azienda["name"],
			_("{0} documents are waiting and nothing has been accepted for {1} days.").format(
				in_attesa, giorni
			),
		)
	return rilievi


def controlla_scadenze() -> list[dict]:
	"""How close the annual deadline is, with something still outstanding.

	Vets have their own deadline in mid-March, which is why they get their own
	batch: merging the two is how a vet practice finds out in February that it is
	late.
	"""
	oggi = getdate()
	anno = oggi.year - 1 if oggi.month <= 3 else oggi.year
	rilievi: list[dict] = []
	for azienda in _aziende_sanitarie():
		in_attesa = frappe.db.count(
			"CRM Invoice",
			{
				"company": azienda["name"],
				"docstatus": 1,
				"ts_year": anno,
				"ts_status": ["in", ("da_inviare", "pronto_export", "scartato")],
			},
		)
		if not in_attesa:
			continue
		scadenza = scadenza_invio(anno, azienda.get("sender_category") == "veterinario")
		mancano = (scadenza - oggi).days
		if mancano > 30:
			continue
		rilievi.append({"company": azienda["name"], "pending": in_attesa, "days_left": mancano})
		avvisa(
			_("Sistema TS deadline approaching"),
			azienda["name"],
			_("{0} documents for {1} are still to report, {2} days left.").format(in_attesa, anno, mancano),
		)
	return rilievi


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
	"""The daily sweep. Every check is independent: one failing does not hide the rest."""
	for controllo in (leggi_ricevute, controlla_certificati, controlla_silenzio, controlla_scadenze):
		try:
			controllo()
		except Exception:
			frappe.log_error(
				title=f"Invoicing monitoring: {controllo.__name__}", message=frappe.get_traceback()
			)
