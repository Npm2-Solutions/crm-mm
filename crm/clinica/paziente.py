# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Becoming a patient: one door for every rule, and the search for the patients
that were already there.

Every rule calls `assicura_paziente`, and its first line is "already a patient?
then leave": the first rule to arrive writes the card, which rule it was, when and
by whose hand; the ones after do nothing. With the clinic off in the plan no rule
converts anybody: it is a module the centre does not have.
"""

from __future__ import annotations

import datetime
from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime

from crm.clinica import PIANO, regole
from crm.permissions import livelli

DOCTYPE = "Clinic Patient"

#: Set once the patients already in the agenda and the invoices have been found.
RECUPERO_FATTO = "crm_clinica_recupero"


def clinica_accesa() -> bool:
	"""Whether the plan has the clinic on (or in trial).

	Registration first: the registry counts a module nobody declared as on, and a
	worker that never imported the hooks would otherwise switch the clinic on for
	every site.
	"""
	livelli.carica()
	return livelli.stato_modulo(PIANO, livelli.moduli_attivi()) in (livelli.ATTIVO, livelli.PROVA)


def persona_di(party_type: str | None, party: str | None) -> str | None:
	"""The person a row of the agenda or an invoice points at."""
	if not (party_type and party):
		return None
	if party_type == "CRM Lead":
		return party if frappe.db.exists("CRM Lead", party) else None
	if party_type == "Contact":
		return frappe.db.get_value("CRM Lead", {"contact": party}, "name")
	if party_type == "CRM Deal":
		return frappe.db.get_value("CRM Deal", party, "lead")
	return None


def dimentica_fonte(doctype: str, name: str) -> None:
	"""What made somebody a patient is gone (a draft thrown away): the card keeps
	the rule and the moment, and no longer points to it."""
	for scheda in frappe.get_all(
		DOCTYPE, filters={"source_doctype": doctype, "source_name": name}, pluck="name"
	):
		frappe.db.set_value(DOCTYPE, scheda, {"source_doctype": None, "source_name": None})


def e_paziente(lead: str) -> bool:
	return bool(frappe.db.exists(DOCTYPE, lead))


def assicura_paziente(
	lead: str | None,
	regola: regole.Regola,
	*,
	quando: datetime.datetime | None = None,
	fonte: tuple[str, str] | None = None,
	da: str | None = None,
	nota: str | None = None,
	annuncia: bool = True,
) -> str | None:
	"""Make ``lead`` a patient because of ``regola``; the card's name when it did.

	None when nothing happened: already a patient, or the clinic is off. With
	``annuncia`` the sales side hears it (`pipeline.diventato_paziente`): the new
	patients deal is won and the automations run. The patients found in the data
	already there are not news, and are not announced.
	"""
	if not lead or not clinica_accesa() or e_paziente(lead):
		return None
	adesso = now_datetime()
	scheda = frappe.get_doc(
		{
			"doctype": DOCTYPE,
			"lead": lead,
			# when it happened, not when somebody noticed; never in the future
			"patient_since": min(get_datetime(quando), adesso) if quando else adesso,
			"rule": regola.valore,
			"source_doctype": fonte[0] if fonte else None,
			"source_name": fonte[1] if fonte else None,
			"recorded_by": da if da is not None else _chi(),
			"note": nota,
		}
	)
	scheda.flags.ignore_permissions = True
	frappe.db.savepoint("clinica_paziente")
	try:
		scheda.insert()
	except frappe.DuplicateEntryError:
		# two rules at the same moment, from two requests: the other one won
		frappe.db.rollback(save_point="clinica_paziente")
		return None
	if annuncia:
		from crm.clinica import pipeline

		pipeline.diventato_paziente(lead, regola)
	return scheda.name


def _chi() -> str | None:
	return None if frappe.session.user in ("Guest", "Administrator") else frappe.session.user


# ------------------------------------------------------------ the rules' facts


def appuntamento_per_la_clinica(servizio: str | None) -> bool:
	"""Whether an appointment of this service can make somebody a patient.

	A service the centre invoices as not healthcare - a course, a membership - does
	not, as an invoice for it does not. One without a fiscal card counts: a small
	practice that does not invoice through the CRM still sees patients.
	"""
	if not servizio:
		return True
	sanitario = frappe.db.get_value(
		"CRM Billable Service", {"crm_service": servizio, "enabled": 1}, "is_healthcare"
	)
	return sanitario is None or bool(sanitario)


def _presenze() -> list[dict]:
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


def _fatture_sanitarie() -> list[dict]:
	Invoice = frappe.qb.DocType("CRM Invoice")
	Item = frappe.qb.DocType("CRM Invoice Item")
	sanitarie = (
		frappe.qb.from_(Item)
		.select(Item.parent)
		.where((Item.parenttype == "CRM Invoice") & (Item.is_healthcare == 1))
	)
	return (
		frappe.qb.from_(Invoice)
		.select(Invoice.name, Invoice.party_type, Invoice.party, Invoice.posting_date)
		.where((Invoice.docstatus == 1) & Invoice.name.isin(sanitarie))
		.run(as_dict=True)
	)


def fatti_esistenti() -> dict[str, dict[str, tuple[datetime.datetime, tuple[str, str]]]]:
	"""For each person, the first fact of each rule found in the data already there."""
	fatti: dict[str, dict[str, tuple[datetime.datetime, tuple[str, str]]]] = defaultdict(dict)

	def annota(lead, regola, quando, fonte):
		if not (lead and quando):
			return
		quando = get_datetime(quando)
		visto = fatti[lead].get(regola.valore)
		if visto is None or quando < visto[0]:
			fatti[lead][regola.valore] = (quando, fonte)

	servizi: dict[str | None, bool] = {}
	for riga in _presenze():
		accolto = riga.arrived_at and riga.participant_status not in regole.PARTECIPANTE_ASSENTE
		if not (accolto or regole.presente(riga.status, riga.participant_status)):
			continue
		if riga.service not in servizi:
			servizi[riga.service] = appuntamento_per_la_clinica(riga.service)
		if not servizi[riga.service]:
			continue
		persona = persona_di(riga.party_type, riga.party)
		if accolto:
			annota(persona, regole.ACCETTAZIONE, riga.arrived_at, ("CRM Appointment", riga.name))
		if regole.presente(riga.status, riga.participant_status):
			annota(persona, regole.APPUNTAMENTO_SVOLTO, riga.starts_on, ("CRM Appointment", riga.name))
	for fattura in _fatture_sanitarie():
		annota(
			persona_di(fattura.party_type, fattura.party),
			regole.FATTURA_SANITARIA,
			fattura.posting_date,
			("CRM Invoice", fattura.name),
		)
	return fatti


def recupera() -> int:
	"""Find the patients in what the centre already has: once, when the clinic is on.

	For every person, the rule that would have fired first had the clinic been on
	all along: the earliest fact wins, and "patient since" is its date. Nobody has
	to mark last year's patients by hand.
	"""
	if not clinica_accesa():
		return 0
	creati = 0
	for lead, fatti in fatti_esistenti().items():
		if e_paziente(lead):
			continue
		trovata = regole.prima_regola({valore: quando for valore, (quando, _fonte) in fatti.items()})
		if not trovata:
			continue
		regola, quando = trovata
		if assicura_paziente(
			lead,
			regola,
			quando=quando,
			fonte=fatti[regola.valore][1],
			da="",
			nota=_("Found in the existing data when the clinic was switched on"),
			annuncia=False,
		):
			creati += 1
			if creati % 200 == 0:
				frappe.db.commit()
	frappe.db.set_default(RECUPERO_FATTO, str(now_datetime()))
	return creati


# ------------------------------------------------------------------ the page


def _stato(lead: str) -> dict:
	scheda = frappe.db.get_value(
		DOCTYPE,
		lead,
		["patient_since", "rule", "source_doctype", "source_name", "recorded_by", "note"],
		as_dict=True,
	)
	if scheda and scheda.recorded_by:
		scheda["recorded_by_name"] = frappe.utils.get_fullname(scheda.recorded_by)
	return {
		"patient": scheda,
		"can_mark": not scheda and livelli.puo("pazienti.segna"),
		**_chi_decide(lead),
	}


def _chi_decide(lead: str) -> dict:
	"""Who signs and decides for them, and whether they are a minor who needs somebody.

	The age comes from the codice fiscale, in the billing details: never typed.
	"""
	from crm.persone import collegate, legami

	nascita = frappe.db.get_value(
		"CRM Billing Profile", {"party_type": "CRM Lead", "party": lead}, "birth_date"
	)
	rappresentanti = collegate.rappresentanti_di(lead)
	return {
		"minor": legami.minorenne(frappe.utils.getdate(nascita) if nascita else None, frappe.utils.getdate()),
		"representatives": [
			{"name": persona, "label": frappe.db.get_value("CRM Lead", persona, "lead_name") or persona}
			for persona in rappresentanti
		],
	}


@frappe.whitelist()
def patient_status(lead: str) -> dict:
	"""Whether the person is a patient, since when and because of what."""
	livelli.verifica("pazienti.vedi")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	return _stato(lead)


@frappe.whitelist(methods=["POST"])
def mark_as_patient(lead: str, note: str | None = None) -> dict:
	"""The rule nobody else sees: somebody knows, and says so."""
	livelli.verifica("pazienti.segna")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	assicura_paziente(lead, regole.A_MANO, nota=(note or "").strip() or None)
	return _stato(lead)


@frappe.whitelist(methods=["POST"])
def find_patients() -> dict:
	"""Look again through the appointments and the invoices, in the background."""
	livelli.verifica("pazienti.recupera")
	frappe.enqueue(
		"crm.clinica.paziente.recupera", queue="long", job_id="crm-clinica-recupero", deduplicate=True
	)
	return {"queued": True}
