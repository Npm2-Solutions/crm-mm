# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The first seam, from marketing to the centre: becoming a patient closes the deal.

A medical centre works with two pipelines (docs/gestionale-medico, "Due pipeline"):

- **New patients**: requests from ads, forms and calls, to call back until the
  first visit. A booking moves an open deal to "appointment booked"; becoming a
  patient wins it. The Meta report counts the won deals of each ad
  (`cost_per_won`), so it says what a new patient costs, with nobody doing
  anything more.
- **Quotes**: the costly treatments, from the quote delivered to accepted or
  declined.

A patient who books their own visits has no deal, and that is right: nothing here
opens one. And only somebody who becomes a patient now closes anything: the
patients found in last year's appointments when the clinic was switched on leave
the deals, and the automations, alone.
"""

from __future__ import annotations

import frappe
from frappe import _

IMPOSTAZIONI = "Clinic Settings"

#: The stages, in the site's language: they are data the board shows, not strings
#: of the interface. Name, description, then stage, colour, type, probability.
NUOVI_PAZIENTI = {
	"it": (
		"Nuovi pazienti",
		"Le richieste da pubblicità, moduli e telefonate, da richiamare fino alla prima visita.",
		(
			("Richiesta", "gray", "Open", 10),
			("Contattato", "orange", "Ongoing", 30),
			("Appuntamento fissato", "blue", "Ongoing", 60),
			("Venuto", "green", "Won", 100),
			("Non venuto", "red", "Lost", 0),
		),
	),
	"en": (
		"New patients",
		"Requests from ads, forms and calls, to call back until the first visit.",
		(
			("Request", "gray", "Open", 10),
			("Contacted", "orange", "Ongoing", 30),
			("Appointment booked", "blue", "Ongoing", 60),
			("Came", "green", "Won", 100),
			("Did not come", "red", "Lost", 0),
		),
	),
}
#: Which of the stages above a booking moves a deal to.
PRENOTATO = 2

PREVENTIVI = {
	"it": (
		"Preventivi",
		"Le cure costose, dal preventivo consegnato ad accettato o rifiutato.",
		(
			("Preventivo da fare", "gray", "Open", 10),
			("Preventivo consegnato", "blue", "Ongoing", 50),
			("Accettato", "green", "Won", 100),
			("Rifiutato", "red", "Lost", 0),
		),
	),
	"en": (
		"Quotes",
		"Costly treatments, from the quote delivered to accepted or declined.",
		(
			("Quote to prepare", "gray", "Open", 10),
			("Quote delivered", "blue", "Ongoing", 50),
			("Accepted", "green", "Won", 100),
			("Declined", "red", "Lost", 0),
		),
	),
}

CHIUSI = ("Won", "Lost")


def _lingua() -> str:
	lingua = (frappe.db.get_single_value("System Settings", "language") or "it")[:2]
	return lingua if lingua in NUOVI_PAZIENTI else "it"


def impostazioni() -> frappe._dict:
	valori = frappe.db.get_singles_dict(IMPOSTAZIONI)
	return frappe._dict(
		new_patients_pipeline=valori.get("new_patients_pipeline"),
		booked_stage=valori.get("booked_stage"),
		quotes_pipeline=valori.get("quotes_pipeline"),
	)


def _crea(definizione: dict) -> tuple[str, list[str] | None]:
	"""A pipeline and its stages; the stages' names, or None for one already there."""
	from crm.api.pipeline import _unique_stage_name

	nome, descrizione, stadi = definizione[_lingua()]
	# one the centre made by hand under this name is taken as it is: never a second
	if frappe.db.exists("CRM Pipeline", nome):
		return nome, None
	doc = frappe.new_doc("CRM Pipeline")
	doc.pipeline_name = nome
	doc.description = descrizione
	doc.insert(ignore_permissions=True)
	creati = []
	for posizione, (stadio, colore, tipo, probabilita) in enumerate(stadi, start=1):
		stato = frappe.get_doc(
			{
				"doctype": "CRM Deal Status",
				"deal_status": _unique_stage_name(stadio, doc.name),
				"pipeline": doc.name,
				"position": posizione,
				"color": colore,
				"type": tipo,
				"probability": probabilita,
			}
		).insert(ignore_permissions=True)
		creati.append(stato.name)
	return doc.name, creati


def crea_pipeline() -> frappe._dict:
	"""The two pipelines, wherever the settings do not point at one yet. Idempotent."""
	attuali = impostazioni()
	valori = {}
	if not (
		attuali.new_patients_pipeline and frappe.db.exists("CRM Pipeline", attuali.new_patients_pipeline)
	):
		nome, stadi = _crea(NUOVI_PAZIENTI)
		valori["new_patients_pipeline"] = nome
		# a pipeline that was already there: the Manager says which stage it is
		valori["booked_stage"] = stadi[PRENOTATO] if stadi else None
	if not (attuali.quotes_pipeline and frappe.db.exists("CRM Pipeline", attuali.quotes_pipeline)):
		valori["quotes_pipeline"] = _crea(PREVENTIVI)[0]
	if valori:
		doc = frappe.get_single(IMPOSTAZIONI)
		doc.update(valori)
		doc.save(ignore_permissions=True)
	return impostazioni()


def _aperte(lead: str, pipeline: str) -> list[frappe._dict]:
	"""The person's deals still open in ``pipeline``, the most recent first."""
	from crm.api.lead import deal_names_of

	nomi = deal_names_of(lead)
	if not nomi:
		return []
	return [
		riga
		for riga in frappe.get_all(
			"CRM Deal",
			filters={"name": ["in", sorted(nomi)], "pipeline": pipeline},
			fields=["name", "status"],
			order_by="modified desc",
		)
		if frappe.get_cached_value("CRM Deal Status", riga.status, "type") not in CHIUSI
	]


def _sposta(nome: str, stadio: str) -> None:
	deal = frappe.get_doc("CRM Deal", nome)
	deal.status = stadio
	# nobody to ask a forecast of: the server moves it, as for an inquiry
	deal.flags.from_inquiry = True
	deal.save(ignore_permissions=True)


def vinci(lead: str) -> list[str]:
	"""Becoming a patient wins the person's open deals in the new patients pipeline."""
	pipeline = impostazioni().new_patients_pipeline
	if not pipeline:
		return []
	vinto = frappe.db.get_value(
		"CRM Deal Status", {"pipeline": pipeline, "type": "Won"}, "name", order_by="position asc"
	)
	if not vinto:
		return []
	vinte = []
	for riga in _aperte(lead, pipeline):
		_sposta(riga.name, vinto)
		vinte.append(riga.name)
	return vinte


def prenotata(lead: str) -> list[str]:
	"""A booking moves the open new-patients deals that are further back to the
	booked stage. One already past it (somebody moved it by hand) stays."""
	conf = impostazioni()
	if not (conf.new_patients_pipeline and conf.booked_stage):
		return []
	soglia = frappe.get_cached_value("CRM Deal Status", conf.booked_stage, "position") or 0
	spostate = []
	for riga in _aperte(lead, conf.new_patients_pipeline):
		if (frappe.get_cached_value("CRM Deal Status", riga.status, "position") or 0) >= soglia:
			continue
		_sposta(riga.name, conf.booked_stage)
		spostate.append(riga.name)
	return spostate


def diventato_paziente(lead: str, regola) -> None:
	"""What becoming a patient does to the sales side: the new patients deal is won,
	and the automations hear "Became Patient". Never stops the conversion: a card
	that cannot be written because a deal could not be saved would be backwards."""
	from crm.automation import engine

	frappe.db.savepoint("clinica_cucitura")
	try:
		vinci(lead)
	except Exception:
		frappe.db.rollback(save_point="clinica_cucitura")
		frappe.log_error(
			title=_("New patients deal not closed for {0}").format(lead),
			reference_doctype="CRM Lead",
			reference_name=lead,
		)
	engine.process_event(EVENTO, frappe.get_doc("CRM Lead", lead), {"rule": regola.valore})


# ---------------------------------------------------------------- quotes

#: The stage of the quotes pipeline a care plan handed over moves its deal to.
CONSEGNATO = 2
ALTRO_MOTIVO = "Other"


def _stadio(pipeline: str, posizione: int | None = None, tipo: str | None = None) -> str | None:
	filtri = {"pipeline": pipeline}
	if posizione:
		filtri["position"] = posizione
	if tipo:
		filtri["type"] = tipo
	return frappe.db.get_value("CRM Deal Status", filtri, "name", order_by="position asc")


def preventivo_consegnato(lead: str, valore: float, deal: str | None = None) -> str | None:
	"""A care plan handed to the person: its deal - the one it had, else the person's
	open one in the quotes pipeline, else a new one - to "quote delivered", worth the
	quote. None where the centre has no quotes pipeline."""
	pipeline = impostazioni().quotes_pipeline
	stadio = _stadio(pipeline, posizione=CONSEGNATO) if pipeline else None
	if not stadio:
		return None
	if not (deal and frappe.db.exists("CRM Deal", deal)):
		deal = next((riga.name for riga in _aperte(lead, pipeline)), None)
	if deal:
		doc = frappe.get_doc("CRM Deal", deal)
	else:
		persona = frappe.get_cached_doc("CRM Lead", lead)
		doc = frappe.new_doc("CRM Deal")
		doc.lead = lead
		doc.organization = persona.organization
		doc.source = persona.source
		doc.deal_owner = persona.lead_owner
		if persona.contact:
			doc.append("contacts", {"contact": persona.contact, "is_primary": 1})
	doc.status = stadio
	doc.expected_deal_value = valore
	# the server moves it, as for an inquiry: nobody to ask a forecast of
	doc.flags.from_inquiry = True
	doc.save(ignore_permissions=True)
	frappe.db.set_value("CRM Lead", lead, "converted", 1, update_modified=False)
	return doc.name


def preventivo_chiuso(
	deal: str | None, accettato: bool, motivo: str | None = None, note: str | None = None
) -> None:
	"""Accepted, the quote's deal is won; declined, lost - with the reason given, or
	"Other" and the words."""
	if not (deal and frappe.db.exists("CRM Deal", deal)):
		return
	doc = frappe.get_doc("CRM Deal", deal)
	stadio = _stadio(doc.pipeline, tipo="Won" if accettato else "Lost")
	if not stadio or doc.status == stadio:
		return
	doc.status = stadio
	if not accettato:
		doc.lost_reason = motivo if motivo and frappe.db.exists("CRM Lost Reason", motivo) else ALTRO_MOTIVO
		doc.lost_notes = note or _("Quote declined")
	doc.flags.from_inquiry = True
	doc.save(ignore_permissions=True)


# ---------------------------------------------------------------- automations

#: The event, and the trigger the automation builder offers: only where the clinic
#: is on (`crm.clinica.registra`).
EVENTO = "patient_created"
TRIGGER = "Became Patient"


# ---------------------------------------------------------------- the settings page


@frappe.whitelist()
def get_settings() -> dict:
	"""Which pipelines are the centre's, for the Pipelines settings."""
	from crm.clinica.paziente import clinica_accesa
	from crm.permissions import livelli

	livelli.verifica("pipeline.configura")
	return {"clinic_on": clinica_accesa(), **impostazioni()}


@frappe.whitelist(methods=["POST"])
def save_settings(
	new_patients_pipeline: str | None = None,
	booked_stage: str | None = None,
	quotes_pipeline: str | None = None,
) -> dict:
	from crm.permissions import livelli

	livelli.verifica("pipeline.configura")
	doc = frappe.get_single(IMPOSTAZIONI)
	doc.update(
		{
			"new_patients_pipeline": new_patients_pipeline or None,
			"booked_stage": booked_stage or None,
			"quotes_pipeline": quotes_pipeline or None,
		}
	)
	doc.save(ignore_permissions=True)
	return get_settings()


@frappe.whitelist(methods=["POST"])
def create_pipelines() -> dict:
	from crm.permissions import livelli

	livelli.verifica("pipeline.configura")
	crea_pipeline()
	return get_settings()
