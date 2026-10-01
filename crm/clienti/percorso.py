# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The person's journey in five steps (the design system's PatientJourney): they
arrive, they book, they come, what follows the visit, what they keep doing at
home. Read from what the centre's data already holds: a step is done when its
fact is there, and the first one not done is the one under way.

`percorso()` is pure; `get_journey()` gathers the facts for the person's page.
It says when and through what, never what: no service, no title of a plan or a
document - the person's page shows those to whoever may read them.
"""

from __future__ import annotations

from datetime import date, datetime

import frappe
from frappe.utils import get_datetime, getdate, now_datetime

from crm.clienti import regole

ARRIVA = "arrived"
PRENOTA = "booked"
VIENE = "came"
DOPO = "after"
A_CASA = "home"
TAPPE = (ARRIVA, PRENOTA, VIENE, DOPO, A_CASA)

FATTA = "done"
IN_CORSO = "current"
DA_FARE = "next"

#: How a booking reached the agenda (`CRM Appointment.source`), in words.
CANALI = {"Online": "Online", "Internal": "At the desk"}


def percorso(fatti: dict) -> list[dict]:
	"""The five steps, each with its state and what to say under it.

	`fatti` holds, each when known: `arrivato` and `fonte` (the record, where it
	came from), `prenotato` and `canale` (the first booking), `venuto` (the first
	appointment they came to), `prossimo` (the next one, while they have not come
	yet), `dopo` and `dopo_cosa` (an invoice or a document after the visit),
	`a_casa` and `a_casa_cosa` (the client area, a plan to follow).
	"""
	quando = {
		ARRIVA: fatti.get("arrivato"),
		PRENOTA: fatti.get("prenotato"),
		VIENE: fatti.get("venuto"),
		DOPO: fatti.get("dopo"),
		A_CASA: fatti.get("a_casa"),
	}
	cosa = {
		ARRIVA: fatti.get("fonte"),
		PRENOTA: fatti.get("canale"),
		DOPO: fatti.get("dopo_cosa"),
		A_CASA: fatti.get("a_casa_cosa"),
	}
	tappe = []
	corrente = False
	for chiave in TAPPE:
		if quando[chiave]:
			stato = FATTA
		elif not corrente:
			stato, corrente = IN_CORSO, True
		else:
			stato = DA_FARE
		tappa = {"key": chiave, "state": stato, "on": _iso(quando[chiave]), "detail": cosa.get(chiave)}
		# not come yet: when they are expected
		if chiave == VIENE and stato != FATTA and fatti.get("prossimo"):
			tappa["expected"] = _iso(fatti["prossimo"])
		tappe.append(tappa)
	return tappe


def primo_arrivo(appuntamenti: list[dict]) -> datetime | None:
	"""When they first came: the earliest appointment they attended or were
	checked in at (`regole.presente`, `regole.accolto`)."""
	venuti = [
		get_datetime(a["starts_on"])
		for a in appuntamenti
		if regole.presente(a.get("status"), a.get("participant_status"))
		or regole.accolto(a.get("arrived_at"), a.get("participant_status"))
	]
	return min(venuti) if venuti else None


def prima_prenotazione(appuntamenti: list[dict]) -> dict | None:
	"""The first booking not cancelled: when it was made, through which channel."""
	valide = [
		a
		for a in appuntamenti
		if a.get("status") != "Cancelled" and a.get("participant_status") != "Cancelled"
	]
	if not valide:
		return None
	prima = min(valide, key=lambda a: get_datetime(a["creation"]))
	canale = CANALI.get(prima.get("source")) or prima.get("external_platform") or None
	return {"il": get_datetime(prima["creation"]), "canale": canale}


def prossimo(appuntamenti: list[dict], adesso: datetime) -> datetime | None:
	"""The next appointment still to come, not cancelled."""
	futuri = [
		get_datetime(a["starts_on"])
		for a in appuntamenti
		if a.get("status") != "Cancelled"
		and a.get("participant_status") not in regole.PARTECIPANTE_ASSENTE
		and get_datetime(a["starts_on"]) >= adesso
	]
	return min(futuri) if futuri else None


def _iso(valore) -> str | None:
	if not valore:
		return None
	if isinstance(valore, datetime):
		return valore.isoformat(sep=" ", timespec="minutes")
	if isinstance(valore, date):
		return valore.isoformat()
	return str(valore)


@frappe.whitelist()
def get_journey(lead: str) -> dict:
	"""The journey of a person the session reads."""
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	persona = frappe.db.get_value(
		"CRM Lead", lead, ["creation", "source", "first_touch_source"], as_dict=True
	)
	appuntamenti = _appuntamenti(lead)
	prenotazione = prima_prenotazione(appuntamenti)
	venuto = primo_arrivo(appuntamenti)
	dopo = _dopo(lead, venuto)
	a_casa = _a_casa(lead)
	fatti = {
		"arrivato": persona.creation,
		"fonte": persona.source or persona.first_touch_source or None,
		"prenotato": prenotazione and prenotazione["il"],
		"canale": prenotazione and prenotazione["canale"],
		"venuto": venuto,
		"prossimo": None if venuto else prossimo(appuntamenti, now_datetime()),
		"dopo": dopo and dopo[0],
		"dopo_cosa": dopo and dopo[1],
		"a_casa": a_casa and a_casa[0],
		"a_casa_cosa": a_casa and a_casa[1],
	}
	return {"steps": percorso(fatti)}


def _appuntamenti(lead: str) -> list[dict]:
	appuntamento = frappe.qb.DocType("CRM Appointment")
	partecipante = frappe.qb.DocType("CRM Appointment Participant")
	return (
		frappe.qb.from_(partecipante)
		.join(appuntamento)
		.on(appuntamento.name == partecipante.parent)
		.select(
			appuntamento.name,
			appuntamento.status,
			appuntamento.starts_on,
			appuntamento.creation,
			appuntamento.source,
			appuntamento.external_platform,
			partecipante.status.as_("participant_status"),
			partecipante.arrived_at,
		)
		.where(
			(partecipante.parenttype == "CRM Appointment")
			& (partecipante.party_type == "CRM Lead")
			& (partecipante.party == lead)
		)
	).run(as_dict=True)


def _dopo(lead: str, venuto: datetime | None) -> tuple[date, str] | None:
	"""What followed the first visit: an invoice that sold something, or a
	document of theirs, from that day on."""
	if not venuto:
		return None
	giorno = getdate(venuto)
	trovati = []
	if frappe.db.exists("DocType", "CRM Invoice"):
		for fattura in frappe.get_all(
			"CRM Invoice",
			filters={
				"party_type": "CRM Lead",
				"party": lead,
				"docstatus": 1,
				"posting_date": [">=", giorno],
			},
			fields=["posting_date", "document_type"],
			order_by="posting_date asc",
		):
			if regole.vendita(fattura.document_type):
				trovati.append((getdate(fattura.posting_date), "Invoice"))
				break
	documento = frappe.get_all(
		"CRM Document",
		filters={"lead": lead, "added_on": [">=", giorno]},
		fields=["added_on"],
		order_by="added_on asc",
		limit=1,
	)
	if documento:
		trovati.append((getdate(documento[0].added_on), "Document"))
	return min(trovati) if trovati else None


def _a_casa(lead: str) -> tuple[date, str] | None:
	"""What they follow from home: the client area they enter, a plan published."""
	trovati = []
	accesso = frappe.get_all(
		"CRM Area Access",
		filters={"lead": lead, "enabled": 1},
		fields=["granted_on"],
		order_by="granted_on asc",
		limit=1,
	)
	if accesso and accesso[0].granted_on:
		trovati.append((getdate(accesso[0].granted_on), "Client area"))
	piano = frappe.get_all(
		"CRM Personal Plan",
		filters={"lead": lead, "status": ["in", ["Published", "Closed"]], "published_on": ["is", "set"]},
		fields=["published_on"],
		order_by="published_on asc",
		limit=1,
	)
	if piano:
		trovati.append((getdate(piano[0].published_on), "Plan"))
	return min(trovati) if trovati else None
