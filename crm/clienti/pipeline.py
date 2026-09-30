# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The new clients pipeline: from the request to the first time the person comes.

Requests from ads, forms and calls, to call back until they come. A booking moves
an open deal of it to "appointment booked"; becoming a client wins it. The Meta
report counts the won deals of each ad (`cost_per_won`), so it says what a new
client costs, with nobody doing anything more.

A person who books by themselves has no deal, and that is right: nothing here opens
one. Which pipeline it is, and the stage after a booking, the manager says in the
settings (`CRM Client Settings`); with none chosen, nothing moves. A vertical names
it in its words (`registra_nomi`): with the clinic, "New patients".
"""

from __future__ import annotations

import frappe
from frappe import _

from crm.permissions import livelli
from crm.verticali import parola

IMPOSTAZIONI = "CRM Client Settings"

#: The stages, in the site's language: they are data the board shows, not strings
#: of the interface. Name, description, then stage, colour, type, probability.
NUOVI_CLIENTI = {
	"it": (
		"Nuovi clienti",
		"Le richieste da pubblicità, moduli e telefonate, da richiamare fino alla prima volta che vengono.",
		(
			("Richiesta", "gray", "Open", 10),
			("Contattato", "orange", "Ongoing", 30),
			("Appuntamento fissato", "blue", "Ongoing", 60),
			("Venuto", "green", "Won", 100),
			("Non venuto", "red", "Lost", 0),
		),
	),
	"en": (
		"New clients",
		"Requests from ads, forms and calls, to call back until they first come.",
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
CHIUSI = ("Won", "Lost")

#: The vertical's names for the same pipeline, by the vertical's key.
_nomi: dict[str, dict] = {}


def registra_nomi(verticale: str, definizione: dict) -> None:
	"""A vertical names the pipeline in its words, in the same shape as
	`NUOVI_CLIENTI`: with the clinic, "Nuovi pazienti"."""
	_nomi[verticale] = definizione


def _definizione() -> tuple:
	from crm import verticali

	attiva = verticali.attiva()
	definizione = _nomi.get(attiva.chiave, NUOVI_CLIENTI) if attiva else NUOVI_CLIENTI
	lingua = (frappe.db.get_single_value("System Settings", "language") or "it")[:2]
	return definizione.get(lingua) or definizione["it"]


def impostazioni() -> frappe._dict:
	valori = frappe.db.get_singles_dict(IMPOSTAZIONI)
	return frappe._dict(
		new_clients_pipeline=valori.get("new_clients_pipeline"),
		booked_stage=valori.get("booked_stage"),
	)


def quale() -> str | None:
	"""The new clients pipeline, if the centre has one."""
	nome = impostazioni().new_clients_pipeline
	return nome if nome and frappe.db.exists("CRM Pipeline", nome) else None


def crea() -> frappe._dict:
	"""The new clients pipeline, where the settings do not point at one yet.
	Idempotent: one the centre made by hand under this name is taken as it is, and
	the manager says which of its stages comes after a booking."""
	from crm.api.pipeline import _unique_stage_name

	if quale():
		return impostazioni()
	nome, descrizione, stadi = _definizione()
	prenotato = None
	if not frappe.db.exists("CRM Pipeline", nome):
		doc = frappe.new_doc("CRM Pipeline")
		doc.pipeline_name = nome
		doc.description = descrizione
		doc.insert(ignore_permissions=True)
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
			if posizione == PRENOTATO + 1:
				prenotato = stato.name
		nome = doc.name
	conf = frappe.get_single(IMPOSTAZIONI)
	conf.new_clients_pipeline = nome
	conf.booked_stage = prenotato
	conf.save(ignore_permissions=True)
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
	"""Becoming a client wins the person's open deals in the new clients pipeline."""
	pipeline = quale()
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
	"""A booking moves the open new clients deals that are further back to the booked
	stage. One already past it (somebody moved it by hand) stays."""
	conf = impostazioni()
	if not (quale() and conf.booked_stage):
		return []
	soglia = frappe.get_cached_value("CRM Deal Status", conf.booked_stage, "position") or 0
	spostate = []
	for riga in _aperte(lead, conf.new_clients_pipeline):
		if (frappe.get_cached_value("CRM Deal Status", riga.status, "position") or 0) >= soglia:
			continue
		_sposta(riga.name, conf.booked_stage)
		spostate.append(riga.name)
	return spostate


# ---------------------------------------------------------------- the settings page


@frappe.whitelist()
def get_settings() -> dict:
	"""Which pipeline is the new clients', for the Pipelines settings."""
	livelli.verifica("pipeline.configura")
	return dict(impostazioni())


@frappe.whitelist(methods=["POST"])
def save_settings(new_clients_pipeline: str | None = None, booked_stage: str | None = None) -> dict:
	livelli.verifica("pipeline.configura")
	doc = frappe.get_single(IMPOSTAZIONI)
	doc.new_clients_pipeline = new_clients_pipeline or None
	doc.booked_stage = booked_stage or None
	doc.save(ignore_permissions=True)
	return get_settings()


@frappe.whitelist(methods=["POST"])
def create_pipeline() -> dict:
	livelli.verifica("pipeline.configura")
	crea()
	return get_settings()


def controlla(doc) -> None:
	"""The settings hold together: the stage after a booking is one of the
	pipeline's, and quotes move deals in a pipeline of their own."""
	if doc.booked_stage and doc.new_clients_pipeline:
		pipeline = frappe.db.get_value("CRM Deal Status", doc.booked_stage, "pipeline")
		if pipeline != doc.new_clients_pipeline:
			frappe.throw(
				parola("The stage after a booking has to be one of the new clients pipeline's stages")
			)
	preventivi = frappe.db.get_single_value("CRM Quote Settings", "quotes_pipeline")
	if doc.new_clients_pipeline and doc.new_clients_pipeline == preventivi:
		frappe.throw(parola("New clients and quotes need two different pipelines"))
