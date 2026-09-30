# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Becoming a client: one door for every rule, and the clients already there.

Every rule calls `diventa_cliente`, and its first line is "already a client? then
leave": the first fact writes `CRM Lead.client_since`, when it happened and never
in the future; the ones after do nothing. Written straight to the table, as the
agenda writes the last visit: nobody edited the person.

Where a module with rules of its own is on (`registra_regole`: the clinic), the
CRM's rules give way, and the module calls `diventa_cliente` from its own.
"""

from __future__ import annotations

import datetime
from collections.abc import Callable

import frappe
from frappe import _
from frappe.query_builder.functions import IfNull
from frappe.utils import get_datetime, now_datetime

from crm.clienti import regole
from crm.fcrm.doctype.crm_appointment.crm_appointment import person_of

CAMPO = "client_since"
#: The event, and the trigger the automations listen to it by (`crm.automation.engine`).
EVENTO = "client_created"
TRIGGER = "Became Client"

#: For each module with rules of its own, whether it is on here.
_regole_proprie: list[Callable[[], bool]] = []


def registra_regole(accese: Callable[[], bool]) -> None:
	"""A module that says itself who becomes a client (the clinic: whoever becomes a
	patient). Where it is on, the CRM's rules give way."""
	if accese not in _regole_proprie:
		_regole_proprie.append(accese)


def regole_del_crm() -> bool:
	"""Whether the CRM's own rules decide here: no module with its own is on."""
	from crm.permissions import livelli

	livelli.carica()
	return not any(accese() for accese in _regole_proprie)


def cliente_da(lead: str | None) -> datetime.datetime | None:
	return frappe.db.get_value("CRM Lead", lead, CAMPO) if lead else None


def diventa_cliente(
	lead: str | None,
	regola: regole.Regola,
	*,
	quando: datetime.datetime | datetime.date | str | None = None,
	annuncia: bool = True,
) -> bool:
	"""``lead`` is a client from ``quando`` because of ``regola``; True when it became
	one now.

	False when nothing happened: nobody, or a client already. With ``annuncia`` the
	sales side hears it: the new clients deal is won and the automations hear
	"Became Client". The clients found in the data already there are not news.
	"""
	if not lead or not frappe.db.exists("CRM Lead", lead):
		return False
	# the row held until the end of the transaction: of two facts at the same
	# moment, from two requests, the second finds the first one's date
	if frappe.db.get_value("CRM Lead", lead, CAMPO, for_update=True):
		return False
	adesso = now_datetime()
	frappe.db.set_value(
		"CRM Lead",
		lead,
		CAMPO,
		# when it happened, not when somebody noticed; never in the future
		min(get_datetime(quando), adesso) if quando else adesso,
		update_modified=False,
	)
	if annuncia:
		_annuncia(lead, regola)
	return True


def _annuncia(lead: str, regola: regole.Regola) -> None:
	"""The new clients deal is won, and the automations hear it. A deal that cannot
	be saved never stops the client: logged, and the rest goes on."""
	from crm.automation import engine
	from crm.clienti import pipeline

	frappe.db.savepoint("clienti_trattativa")
	try:
		pipeline.vinci(lead)
	except Exception:
		frappe.db.rollback(save_point="clienti_trattativa")
		frappe.log_error(
			title=_("New clients deal not closed for {0}").format(lead),
			reference_doctype="CRM Lead",
			reference_name=lead,
		)
	engine.process_event(EVENTO, frappe.get_doc("CRM Lead", lead), {"rule": regola.valore})


# ------------------------------------------------------------ the facts


def presenze() -> list[dict]:
	"""Every participant who came or was checked in, with the appointment's service
	and start."""
	Appt = frappe.qb.DocType("CRM Appointment")
	Part = frappe.qb.DocType("CRM Appointment Participant")
	return (
		frappe.qb.from_(Part)
		.join(Appt)
		.on(Part.parent == Appt.name)
		.select(
			Appt.name,
			Appt.status,
			Appt.starts_on,
			Appt.service,
			Part.status.as_("participant_status"),
			Part.party_type,
			Part.party,
			Part.arrived_at,
		)
		.where(
			(Part.parenttype == "CRM Appointment")
			& (
				(Appt.status == regole.APPUNTAMENTO_COMPLETATO)
				| (Part.status == regole.PARTECIPANTE_PRESENTE)
				| Part.arrived_at.isnotnull()
			)
		)
		.run(as_dict=True)
	)


def _vendite() -> list[dict]:
	"""Every confirmed invoice that sold something, with whom it was made out to."""
	Invoice = frappe.qb.DocType("CRM Invoice")
	return (
		frappe.qb.from_(Invoice)
		.select(Invoice.name, Invoice.party_type, Invoice.party, Invoice.posting_date)
		.where((Invoice.docstatus == 1) & IfNull(Invoice.document_type, "").notin(regole.NOTE_DI_CREDITO))
		.run(as_dict=True)
	)


def primi_fatti() -> dict[str, tuple[datetime.datetime, regole.Regola]]:
	"""For each person, the fact of the CRM's rules that came first."""
	fatti: dict[str, list[tuple[datetime.datetime, regole.Regola]]] = {}

	def annota(lead: str | None, quando, regola: regole.Regola) -> None:
		if lead and quando:
			fatti.setdefault(lead, []).append((get_datetime(quando), regola))

	for riga in presenze():
		persona = person_of(riga.party_type, riga.party)
		if regole.accolto(riga.arrived_at, riga.participant_status):
			annota(persona, riga.arrived_at, regole.ACCETTAZIONE)
		if regole.presente(riga.status, riga.participant_status):
			annota(persona, riga.starts_on, regole.APPUNTAMENTO_SVOLTO)
	for fattura in _vendite():
		annota(person_of(fattura.party_type, fattura.party), fattura.posting_date, regole.FATTURA)
	return {lead: regole.primo(elenco) for lead, elenco in fatti.items()}


def recupera() -> int:
	"""The clients already there: for everybody, the first time they came or their
	first invoice is when they became a client. Announces nothing: last year's
	clients are not news, and close no deal. Where a module's own rules decide, it
	finds its clients itself."""
	if not regole_del_crm():
		return 0
	return sum(
		diventa_cliente(lead, regola, quando=quando, annuncia=False)
		for lead, (quando, regola) in primi_fatti().items()
	)
