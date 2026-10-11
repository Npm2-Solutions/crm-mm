# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A call nobody answered (`persa_regole`): the automations hear it when the caller
is somebody the centre knows; a number nobody knows gets one SMS of service, where
the centre wants it (`CRM Answering Settings.sms_to_missed_callers`, off to start
with). Which calls count as missed is the centre's too (`persa_regole.conta`).
Neither ever costs the caller what they hear."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, cint, get_url, getdate, nowdate

from crm.telephony import answering
from crm.telephony import persa_regole as R

EVENTO = "call_missed"
TRIGGER = "Missed Call"
PERSONE = ("CRM Lead", "CRM Deal")


def chiamata_persa(call_log, numero: str | None, caso: str = R.NESSUNO_RISPONDE) -> None:
	"""Called wherever a call ends with nobody picking up, saying how. Never raises."""
	try:
		config = answering.settings()
		if not call_log or not R.conta(caso, config):
			return
		chi = chi_ha_chiamato(call_log, numero)
		if chi:
			from crm.telephony.callbacks import _emit

			_emit(EVENTO, frappe.get_doc(*chi), {"number": numero, "call_log": call_log.name})
			return
		if cint(config.get("sms_to_missed_callers")) and numero:
			frappe.enqueue(
				"crm.telephony.persa.scrivi_a_chi_ha_chiamato",
				numero=numero,
				call_log=call_log.name,
				enqueue_after_commit=True,
			)
	except Exception:
		frappe.log_error(title="CRM Telephony: missed call")


def chi_ha_chiamato(call_log, numero: str | None) -> tuple[str, str] | None:
	"""The person (or deal) behind a call, as the rest of telephony files it: what the
	call names, the person or deal Twilio linked it to (`twilio.api.link`), a
	contact's person, else whose number it is."""
	if call_log.get("reference_doctype") in PERSONE and call_log.get("reference_docname"):
		return call_log.reference_doctype, call_log.reference_docname
	righe = call_log.get("links") or []
	for riga in righe:
		if riga.get("link_doctype") in PERSONE and riga.get("link_name"):
			return riga.link_doctype, riga.link_name
	for riga in righe:
		if riga.get("link_doctype") == "Contact" and riga.get("link_name"):
			persona = frappe.db.get_value(
				"CRM Lead", {"contact": riga.link_name}, "name", order_by="creation asc"
			)
			if persona:
				return "CRM Lead", persona
	if not numero:
		return None
	from crm.integrations.api import get_contact_lead_or_deal_from_number

	nome, doctype = get_contact_lead_or_deal_from_number(numero)
	return (doctype, nome) if doctype and nome else None


def gia_scritto(numero: str, giorno=None) -> bool:
	"""Whether the centre's day already sent this number its missed-call SMS: every SMS
	DottorCloud sends is in the register, this one on the call that caused it."""
	inizio = getdate(giorno or nowdate())
	return bool(
		frappe.get_all(
			"CRM SMS Message",
			filters=[
				["type", "=", "Outgoing"],
				["to", "=", numero],
				["reference_doctype", "=", "CRM Call Log"],
				["status", "!=", "Failed"],
				["creation", ">=", inizio],
				["creation", "<", add_days(inizio, 1)],
			],
			limit=1,
		)
	)


def scrivi_a_chi_ha_chiamato(numero: str, call_log: str | None = None) -> bool:
	"""One SMS to a number nobody knows that found no answer: once a day, to a mobile
	of the countries the centre calls, from the centre's sender, never for the demo."""
	from crm.api.sms import create_sms, deliver_sms
	from crm.demo import guardie
	from crm.scheduling.availability import settings as agenda
	from crm.scheduling.promemoria import _nella_lingua_del_centro, _nome_del_centro
	from crm.telephony import sms, uscita

	a = R.a_chi_scrivere(numero, uscita.consentiti())
	da = sms.mittente()
	if not a or not da or guardie.sms_dopo_una_chiamata_persa(a):
		return False
	oggi = getdate(nowdate())
	# the cache only keeps two jobs of the same moment from both writing
	chiave = frappe.cache.make_key(R.chiave_del_giorno(a, oggi))
	if not frappe.cache.set(chiave, 1, nx=True, ex=120):
		return False
	if gia_scritto(a, oggi):
		return False
	link = get_url("/prenota") if cint(agenda().get("online_booking_enabled")) else None
	with _nella_lingua_del_centro():
		messaggio = testo(_nome_del_centro(), link)
	doc = create_sms(
		type="Outgoing",
		from_number=da,
		to=a,
		message=messaggio,
		reference_doctype="CRM Call Log" if call_log else None,
		reference_name=call_log,
	)
	deliver_sms(doc)
	return doc.status == "Sent"


def testo(centro: str, link: str | None) -> str:
	"""What the caller reads: who the centre is, that it will call back, and the
	booking page when the centre takes bookings online."""
	if link:
		return _("{0}: sorry we missed your call. We will call you back; to book now: {1}").format(
			centro, link
		)
	return _("{0}: sorry we missed your call. We will call you back as soon as we can.").format(centro)
