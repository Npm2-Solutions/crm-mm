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

from crm.tessera_sanitaria.engine.tracciato import scadenza_invio


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
	from crm.tessera_sanitaria.engine.tracciato import Cifratore

	giorni = frappe.db.get_single_value("CRM Invoicing Settings", "certificate_warning_days") or 90
	rilievi: list[dict] = []
	for azienda in _aziende_sanitarie():
		if not azienda.get("ts_certificate"):
			rilievi.append({"company": azienda["name"], "issue": "missing"})
			continue
		try:
			from crm.tessera_sanitaria.documento import contenuto_allegato

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
	"""Nothing accepted for N days, while documents wait.

	The most dangerous check in the file, because the condition it looks for produces
	no error anywhere else.

	`inviato` counts as waiting. On the provider channel a document sits there from
	the moment the intermediary takes it until the real Sistema TS outcome comes
	back - and if that outcome never comes, nothing else in the system will say so.
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
				"ts_status": ["in", ("da_inviare", "pronto_export", "inviato")],
			},
		)
		if not in_attesa:
			continue
		ultimo = _ultimo_accolto(azienda["name"])
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


def _ultimo_accolto(azienda: str):
	"""When this company last had anything accepted by the Sistema TS.

	Both routes count. A batch leaves a submission behind; a synchronous send only
	moves the invoice, so looking at submissions alone would report silence at a
	practice that has been transmitting document by document all along.
	"""
	candidati = [
		frappe.db.get_value(
			"CRM TS Submission",
			{"company": azienda, "status": "accolto"},
			"sent_on",
			order_by="sent_on desc",
		),
		frappe.db.get_value(
			"CRM Invoice",
			{"company": azienda, "docstatus": 1, "ts_status": "accolto"},
			"modified",
			order_by="modified desc",
		),
	]
	visti = [c for c in candidati if c]
	return max(visti) if visti else None


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


def giornaliero() -> None:
	"""The daily sweep. Every check is independent: one failing does not hide the rest."""
	for controllo in (controlla_certificati, controlla_silenzio, controlla_scadenze):
		try:
			controllo()
		except Exception:
			frappe.log_error(
				title=f"Invoicing monitoring: {controllo.__name__}", message=frappe.get_traceback()
			)
