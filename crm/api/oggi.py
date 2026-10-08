# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The desk's day (docs/verticali/clinica, "La giornata della segreteria").

Who is coming today, who is in the waiting room and since when, what the last days
left without an outcome, and whether there is anything still to invoice. Saying
how it went is `crm.scheduling.esiti`: this reads, and hands the clicks over.
"""

from __future__ import annotations

import datetime

import frappe
from frappe.utils import get_datetime, getdate

from crm.permissions import livelli
from crm.scheduling import cicli, esiti, promemoria

#: How far back the appointments nobody closed are still asked about.
GIORNI_INDIETRO = 7


def _appuntamenti(dal: datetime.datetime, al: datetime.datetime, solo_aperti: bool = False) -> list[dict]:
	"""The appointments the session sees between two moments, with their people."""
	righe = frappe.get_list(
		"CRM Appointment",
		# from `dal` up to `al` excluded: the next day's midnight is the next day's
		filters=[["starts_on", ">=", dal], ["starts_on", "<", al], ["status", "!=", "Cancelled"]],
		fields=["name", "title", "service", "starts_on", "ends_on", "status", "color"],
		order_by="starts_on asc",
		limit_page_length=500,
	)
	if not righe:
		return []
	nomi = [riga.name for riga in righe]
	partecipanti: dict[str, list] = {}
	for riga in frappe.get_all(
		"CRM Appointment Participant",
		filters={"parenttype": "CRM Appointment", "parent": ["in", nomi], "status": ["!=", "Cancelled"]},
		fields=["name", "parent", "party_type", "party", "participant_name", "status", "arrived_at"],
		order_by="idx asc",
	):
		partecipanti.setdefault(riga.parent, []).append(riga)
	staff: dict[str, list] = {}
	for riga in frappe.get_all(
		"CRM Appointment Staff",
		filters={"parenttype": "CRM Appointment", "parent": ["in", nomi]},
		fields=["parent", "user"],
		order_by="idx asc",
	):
		staff.setdefault(riga.parent, []).append(riga.user)

	if solo_aperti:
		# the days before: only what nobody closed, before anything else is asked of them
		righe = [r for r in righe if any(p.status == "Booked" for p in partecipanti.get(r.name, []))]
		nomi = [riga.name for riga in righe]
	dovuti = _moduli_dovuti(righe, partecipanti)
	# "session 4 of 10": which session of its cycle it is
	sedute = cicli.numero_della_seduta(nomi)
	fuori = []
	for riga in righe:
		persone = partecipanti.get(riga.name, [])
		for persona in persone:
			# the forms they owe for this appointment: to sign while they wait
			persona["due_forms"] = dovuti.get((riga.name, persona.party), [])
		chi = staff.get(riga.name, [])
		fuori.append(
			{
				**riga,
				"participants": persone,
				"cycle": sedute.get(riga.name),
				"staff": [{"user": u, "full_name": frappe.utils.get_fullname(u)} for u in chi],
				"can_mark": esiti.puo_segnare(
					frappe._dict(name=riga.name, staff=[frappe._dict(user=u) for u in chi])
				),
			}
		)
	# what each of them answered the reminder of this time (docs/crm/59)
	promemoria.nelle_righe(fuori)
	return fuori


def _moduli_dovuti(righe: list, partecipanti: dict) -> dict[tuple[str, str], list[dict]]:
	"""For each appointment and person, the forms they owe for it - for whoever
	sees the forms."""
	if not livelli.puo("moduli.vedi"):
		return {}
	from crm.moduli import compilazioni, dovuti

	coppie = [
		(p.party, {"name": riga.name, "service": riga.service})
		for riga in righe
		for p in partecipanti.get(riga.name, [])
		if p.party_type == "CRM Lead" and p.party
	]
	if not coppie:
		return {}
	# the whole day in one go: the templates and each person's forms read once
	risposta = {}
	for (persona, appuntamento), voci in dovuti.per_appuntamenti(
		coppie, clinici=compilazioni.legge_dati_clinici()
	).items():
		if voci:
			risposta[(appuntamento, persona)] = [
				{"template": v["template"], "title": v["title"], "pending": v["pending"]} for v in voci
			]
	return risposta


@frappe.whitelist()
def get_day(date: str | None = None) -> dict:
	"""The day at the desk: its appointments, and the ones the last days left open."""
	livelli.verifica_nel_crm("agenda.presenze")
	giorno = getdate(date) if date else getdate()
	inizio = datetime.datetime.combine(giorno, datetime.time.min)
	return {
		"date": str(giorno),
		"today": str(getdate()),
		"appointments": _appuntamenti(inizio, inizio + datetime.timedelta(days=1)),
		# only before the day shown: the day itself is above
		"past_open": _appuntamenti(
			inizio - datetime.timedelta(days=GIORNI_INDIETRO), inizio, solo_aperti=True
		),
		"can_invoice": livelli.puo("fatture.emetti"),
	}


@frappe.whitelist(methods=["POST"])
def set_outcome(appointment: str, participant: str, outcome: str) -> dict:
	"""Checked in, came, did not come, or back to booked."""
	livelli.verifica_nel_crm("agenda.presenze")
	esiti.segna(appointment, participant, outcome)
	doc = frappe.get_doc("CRM Appointment", appointment)
	return {
		"status": doc.status,
		"participants": [
			{"name": row.name, "status": row.status, "arrived_at": row.arrived_at} for row in doc.participants
		],
		"now": str(get_datetime()),
	}


# ------------------------------------------------------------------ the cash closing


@frappe.whitelist()
def get_cash_summary(date: str | None = None) -> dict:
	"""The day's money at the desk: collected by way of paying and by who issued it,
	the credit notes, the cash the drawer should hold, and the closing if it was
	closed (`crm.invoicing.cassa`)."""
	livelli.verifica_nel_crm("fatture.incassi")
	from crm.invoicing import cassa

	return cassa.riepilogo_del_giorno(getdate(date) if date else getdate())


@frappe.whitelist(methods=["POST"])
def close_cash_day(date: str, counted_cash: float, note: str | None = None) -> dict:
	"""The day closed with the cash counted in the drawer."""
	livelli.verifica_nel_crm("fatture.incassi")
	from crm.invoicing import cassa

	return cassa.chiudi(date, counted_cash, note)
