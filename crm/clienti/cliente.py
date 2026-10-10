# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Becoming a client: one door for every rule, and the clients already there.

Every rule calls `diventa_cliente`, and its first line is "already a client? then
leave": the first fact writes `CRM Lead.client_since`, when it happened and never
in the future, and the person's relationship with the centre becomes "Client"; the
ones after do nothing. Written straight to the table, as the agenda writes the
last visit: nobody edited the person.

The CRM's rules decide in every centre, whatever its trade: whoever came, or
bought, is a client - the Pilates class as much as the visit. A module adds a step
above (the clinic: a patient, `RAPPORTO`) and the door never takes it back down.
"""

from __future__ import annotations

import datetime

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

#: Who the person is to the centre (`CRM Lead.relationship`): a contact until the
#: first fact, then a client. A module writes a step of its own above them (the
#: clinic's "Patient"), which nothing here takes back down.
RAPPORTO = "relationship"
CONTATTO = "Contact"
CLIENTE = "Client"


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
	gia, rapporto = frappe.db.get_value("CRM Lead", lead, [CAMPO, RAPPORTO], for_update=True)
	if gia:
		return False
	adesso = now_datetime()
	valori = {
		# when it happened, not when somebody noticed; never in the future
		CAMPO: min(get_datetime(quando), adesso) if quando else adesso,
	}
	if rapporto in (None, "", CONTATTO):
		valori[RAPPORTO] = CLIENTE
	frappe.db.set_value("CRM Lead", lead, valori, update_modified=False)
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
	"""Every confirmed invoice that sold something, with whom it was made out to. A
	test invoice sold nothing, nor did a deposit's advance (`regole.vendita`)."""
	Invoice = frappe.qb.DocType("CRM Invoice")
	return (
		frappe.qb.from_(Invoice)
		.select(Invoice.name, Invoice.party_type, Invoice.party, Invoice.posting_date)
		.where(
			(Invoice.docstatus == 1)
			& (Invoice.test_document == 0)
			& IfNull(Invoice.document_type, "").notin(regole.NOTE_DI_CREDITO)
			& (IfNull(Invoice.advance_for, "") == "")
		)
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
	clients are not news, and close no deal."""
	return sum(
		diventa_cliente(lead, regola, quando=quando, annuncia=False)
		for lead, (quando, regola) in primi_fatti().items()
	)


# ------------------------------------------------------------ an advance is no sale


def ricalcola_dagli_acconti() -> int:
	"""The people a deposit's advance invoice made clients, before the rules left it
	out (`regole.vendita`): their first real fact is when, and with none they are a
	contact again. Quietly, as `recupera`: no deal moves, no automation hears. A step
	a module put above the client (the clinic's patient) is the module's to recount.
	How many people changed."""
	Invoice = frappe.qb.DocType("CRM Invoice")
	giorni: dict[str, set[datetime.date]] = {}
	for acconto in (
		frappe.qb.from_(Invoice)
		.select(Invoice.party_type, Invoice.party, Invoice.posting_date)
		.where(
			(Invoice.docstatus == 1) & (Invoice.test_document == 0) & (IfNull(Invoice.advance_for, "") != "")
		)
		.run(as_dict=True)
	):
		persona = person_of(acconto.party_type, acconto.party)
		if persona and acconto.posting_date:
			giorni.setdefault(persona, set()).add(get_datetime(acconto.posting_date).date())
	if not giorni:
		return 0
	fatti = primi_fatti()
	cambiati = 0
	for lead, quali in giorni.items():
		dal, rapporto = frappe.db.get_value("CRM Lead", lead, [CAMPO, RAPPORTO]) or (None, None)
		# an advance wrote the midnight of its day: any other moment is a real fact's
		dal = get_datetime(dal) if dal else None
		if not dal or dal.time() != datetime.time.min or dal.date() not in quali:
			continue
		primo = fatti.get(lead)
		if primo and primo[0] <= dal:
			continue
		valori = {CAMPO: primo[0] if primo else None}
		if not primo and rapporto == CLIENTE:
			valori[RAPPORTO] = CONTATTO
		frappe.db.set_value("CRM Lead", lead, valori, update_modified=False)
		cambiati += 1
	return cambiati
