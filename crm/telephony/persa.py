# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A call nobody answered (`persa_regole`): the automations hear it when the caller
is somebody the centre knows; a number nobody knows gets one SMS of service, where
the centre wants it (`CRM Answering Settings.sms_to_missed_callers`, off to start
with). Neither ever costs the caller what they hear."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, get_url, nowdate

from crm.telephony import answering
from crm.telephony import persa_regole as R

EVENTO = "call_missed"
TRIGGER = "Missed Call"


def chiamata_persa(call_log, numero: str | None) -> None:
	"""Called wherever a call ends with nobody picking up. Never raises."""
	try:
		if not call_log:
			return
		if call_log.get("reference_doctype") in ("CRM Lead", "CRM Deal") and call_log.get(
			"reference_docname"
		):
			from crm.telephony.callbacks import _emit

			_emit(EVENTO, call_log, {"number": numero})
			return
		if cint(answering.settings().get("sms_to_missed_callers")) and numero:
			frappe.enqueue(
				"crm.telephony.persa.scrivi_a_chi_ha_chiamato",
				numero=numero,
				enqueue_after_commit=True,
			)
	except Exception:
		frappe.log_error(title="CRM Telephony: missed call")


def scrivi_a_chi_ha_chiamato(numero: str) -> bool:
	"""One SMS to a number nobody knows that found no answer: once a day, to a mobile
	of the countries the centre calls, from the centre's sender, never for the demo."""
	from crm.api.sms import create_sms, deliver_via_twilio
	from crm.demo import guardie
	from crm.scheduling.availability import settings as agenda
	from crm.scheduling.promemoria import _nella_lingua_del_centro, _nome_del_centro
	from crm.telephony import sms, uscita

	a = R.a_chi_scrivere(numero, uscita.consentiti())
	da = sms.mittente()
	if not a or not da or guardie.sms_dopo_una_chiamata_persa(a):
		return False
	chiave = frappe.cache.make_key(R.chiave_del_giorno(a, frappe.utils.getdate(nowdate())))
	if not frappe.cache.set(chiave, 1, nx=True, ex=2 * 24 * 3600):
		return False
	link = get_url("/prenota") if cint(agenda().get("online_booking_enabled")) else None
	with _nella_lingua_del_centro():
		messaggio = testo(_nome_del_centro(), link)
	doc = create_sms(type="Outgoing", from_number=da, to=a, message=messaggio)
	deliver_via_twilio(doc)
	return doc.status == "Sent"


def testo(centro: str, link: str | None) -> str:
	"""What the caller reads: who the centre is, that it will call back, and the
	booking page when the centre takes bookings online."""
	if link:
		return _("{0}: sorry we missed your call. We will call you back; to book now: {1}").format(
			centro, link
		)
	return _("{0}: sorry we missed your call. We will call you back as soon as we can.").format(centro)
