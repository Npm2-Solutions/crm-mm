# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""How an appointment went: who arrived, who came, who did not.

The desk checks people in (the waiting room counts from there), the practitioner
or the desk says they came, and the appointment closes by itself once each of its
participants has an outcome (`CRMAppointment.close_from_attendance`). A visit
written for the appointment, or an invoice issued from it, says they came too.

At the end of the day whoever was checked in and never marked counts as came, and
the desk hears about the appointments nobody said anything of: "did they come?".
An agenda where last week's visits are still "booked" is one nobody can count on,
and the patients, the reminders and the invoices all read it.
"""

from __future__ import annotations

import datetime

import frappe
from frappe import _
from frappe.utils import add_to_date, get_datetime, getdate, now_datetime, nowdate

from crm.notifiche import regole as N
from crm.notifiche.avvisi import avvisa
from crm.permissions import livelli

#: What the desk and the practitioner may say of a participant.
ESITI = ("Booked", "Arrived", "Attended", "No Show")
#: Still waiting for somebody to say how it went.
APERTI = ("Booked", "Arrived")
#: After the last appointment of the day ends, how long before the desk is asked.
MARGINE = datetime.timedelta(minutes=30)
AVVISATO = "crm_sono_venuti"


def puo_segnare(doc, user: str | None = None) -> bool:
	"""`agenda.presenze` (doc 30): the desk and the manager every appointment, the
	practitioner the ones they work. Outside the levels, the roles decide."""
	user = user or frappe.session.user
	if not livelli.nel_crm(user):
		return frappe.has_permission("CRM Appointment", "write", doc=doc.name, user=user)
	ambito = livelli.ambito("agenda.presenze", user)
	if ambito == livelli.CENTRO:
		return True
	if ambito == livelli.SUOI:
		return user in {row.user for row in doc.get("staff") or []}
	return False


def segna(appuntamento: str, riga: str, esito: str) -> None:
	"""Say how it went for one participant."""
	if esito not in ESITI:
		frappe.throw(_("Unknown outcome {0}").format(esito))
	doc = frappe.get_doc("CRM Appointment", appuntamento)
	if not puo_segnare(doc):
		frappe.throw(_("You cannot say how this appointment went"), frappe.PermissionError)
	scrivi(doc, riga, esito)


def scrivi(doc, riga: str, esito: str) -> None:
	"""The outcome of one participant written, whoever said it: the desk (`segna`,
	which checks who may), or the person from their area («I'm here»,
	`crm.area.api.check_in`, which checks it is theirs)."""
	if doc.status == "Cancelled":
		frappe.throw(_("The appointment was cancelled"))
	for row in doc.participants:
		if row.name == riga:
			if esito == "Booked":
				# undone: they were not there after all
				row.arrived_at = None
			row.status = esito
			break
	else:
		frappe.throw(_("Participant not found"))
	if esito in APERTI and doc.status in ("Completed", "No Show"):
		# reopened: somebody took back what they said
		doc.status = "Confirmed"
	# how it went is said whatever else the appointment names: a professional
	# whose account is gone (an old import) does not stop the desk
	doc.flags.ignore_links = True
	doc.save(ignore_permissions=True)


def presente(appuntamento: str | None, persona: str | None) -> bool:
	"""The person came to ``appuntamento``: a visit was written or an invoice issued
	for it. Only once it has started: an invoice made in advance says nothing yet."""
	from crm.fcrm.doctype.crm_appointment.crm_appointment import person_of

	if not (appuntamento and persona and frappe.db.exists("CRM Appointment", appuntamento)):
		return False
	doc = frappe.get_doc("CRM Appointment", appuntamento)
	if doc.status == "Cancelled" or get_datetime(doc.starts_on) > now_datetime():
		return False
	cambiato = False
	for row in doc.participants:
		if row.status in APERTI and person_of(row.party_type, row.party) == persona:
			row.status = "Attended"
			cambiato = True
	if cambiato:
		doc.flags.ignore_links = True
		doc.save(ignore_permissions=True)
	return cambiato


def fattura_emessa(doc, method=None) -> None:
	"""`on_submit` of an invoice: issued from an appointment, the person came."""
	from crm.fcrm.doctype.crm_appointment.crm_appointment import person_of

	if not doc.get("appointment"):
		return
	frappe.db.savepoint("esito_fattura")
	try:
		presente(doc.appointment, person_of(doc.party_type, doc.party))
	except Exception:
		# the invoice is issued whatever the agenda says
		frappe.db.rollback(save_point="esito_fattura")
		frappe.log_error(
			title=_("Appointment not closed from invoice {0}").format(doc.name),
			reference_doctype=doc.doctype,
			reference_name=doc.name,
		)


# ---------------------------------------------------------------- the end of the day


def _di_oggi(giorno: datetime.date) -> list:
	inizio = datetime.datetime.combine(giorno, datetime.time.min)
	return frappe.get_all(
		"CRM Appointment",
		filters=[
			["starts_on", ">=", inizio],
			["starts_on", "<", inizio + datetime.timedelta(days=1)],
			["status", "!=", "Cancelled"],
		],
		fields=["name", "ends_on", "status"],
	)


def senza_esito(giorno: datetime.date) -> list[str]:
	"""The appointments of ``giorno`` with somebody nobody said anything of."""
	nomi = [riga.name for riga in _di_oggi(giorno)]
	if not nomi:
		return []
	return sorted(
		set(
			frappe.get_all(
				"CRM Appointment Participant",
				filters={"parenttype": "CRM Appointment", "parent": ["in", nomi], "status": "Booked"},
				pluck="parent",
			)
		)
	)


def chiudi_gli_arrivati(giorno: datetime.date, adesso: datetime.datetime) -> int:
	"""Whoever was checked in and never marked came: the appointment ended a while ago."""
	chiusi = 0
	for riga in _di_oggi(giorno):
		if get_datetime(riga.ends_on) + MARGINE > adesso:
			continue
		doc = frappe.get_doc("CRM Appointment", riga.name)
		arrivati = [row for row in doc.participants if row.status == "Arrived"]
		if not arrivati:
			continue
		for row in arrivati:
			row.status = "Attended"
		doc.save(ignore_permissions=True)
		chiusi += 1
	return chiusi


def chi_avvisare() -> list[str]:
	"""Who hears "did they come?": whoever marks every appointment, the desk first."""
	utenti = []
	for utente in frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"}, pluck="name"):
		if utente in ("Administrator", "Guest") or not livelli.nel_crm(utente):
			continue
		if livelli.ambito("agenda.presenze", utente) == livelli.CENTRO and not livelli.e_agenzia(utente):
			utenti.append(utente)
	return utenti


def fine_giornata() -> None:
	"""Hourly. Once a day's last appointment has ended: the checked in count as
	came, and the desk is asked about the rest, once a day. Yesterday too: a day
	whose last appointment ends late is over only after midnight."""
	adesso = now_datetime()
	oggi = getdate(adesso)
	for giorno in (oggi - datetime.timedelta(days=1), oggi):
		_chiudi_la_giornata(giorno, adesso, ieri=giorno < oggi)


def _chiudi_la_giornata(giorno: datetime.date, adesso: datetime.datetime, ieri: bool = False) -> None:
	appuntamenti = _di_oggi(giorno)
	if not appuntamenti:
		return
	chiudi_gli_arrivati(giorno, adesso)
	ultimo = max(get_datetime(riga.ends_on) for riga in appuntamenti)
	# the last day asked about: that day and the ones before it are done
	if adesso < ultimo + MARGINE or (frappe.db.get_default(AVVISATO) or "") >= str(giorno):
		return
	frappe.db.set_default(AVVISATO, str(giorno))
	aperti = senza_esito(giorno)
	if not aperti:
		return
	for utente in chi_avvisare():
		avvisa(
			utente,
			"Agenda",
			N.ESITI_IERI if ieri else N.ESITI_OGGI,
			[len(aperti)],
			oggetto=("CRM Appointment", aperti[0]),
			messaggio=", ".join(aperti),
		)


def giorni_indietro(giorni: int = 7) -> datetime.date:
	return getdate(add_to_date(nowdate(), days=-giorni))
