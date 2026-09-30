# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""What the patient area shows: only the session's people, derived on the server.

Every call takes a ``person`` and first checks it is one of the session's
(`accesso.persone_di`): a person the session was not given is a refusal, never an
empty answer that could be probed. The rest reads the CRM as the centre does and
gives the patient only what is theirs to see:

- **appointments**, upcoming and past, each with the booking page's own link to
  move or cancel it by the centre's rules;
- **documents** the centre gave online (`crm.clinica.consegna`), downloaded after
  a code verified in the last minutes, and logged like the page `/referto`;
- **invoices**, with their PDF.
"""

from __future__ import annotations

import secrets

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime

from crm.clinica.area import accesso

CONSEGNA = "Clinic Report Delivery"


def _paziente() -> str:
	utente = frappe.session.user
	if utente == "Guest" or not accesso.e_paziente_dell_area(utente):
		frappe.throw(_("Enter the area first"), frappe.PermissionError)
	return utente


def _mia(person: str) -> dict:
	utente = _paziente()
	for riga in accesso.persone_di(utente):
		if riga.lead == person:
			return riga
	frappe.throw(_("This is not your area"), frappe.PermissionError)


@frappe.whitelist()
def get_me() -> dict:
	"""Who is in, whose areas they see, and the centre's name."""
	from crm.moduli.richieste import nome_del_centro

	utente = _paziente()
	persone = accesso.persone_di(utente)
	frappe.db.set_value(
		accesso.ACCESSO,
		{"user": utente, "enabled": 1},
		"last_seen_on",
		now_datetime(),
		update_modified=False,
	)
	return {
		"user": utente,
		"full_name": frappe.utils.get_fullname(utente),
		"people": [{"name": p.lead, "lead_name": p.lead_name, "relation": p.relation} for p in persone],
		"centre": nome_del_centro(),
	}


# ------------------------------------------------------------------ appointments


def _link_di_gestione(riga) -> str | None:
	"""The booking page's own link for this seat: made the first time it is needed."""
	from crm.api.service_booking import manage_url

	token = riga.access_token
	if not token:
		token = secrets.token_urlsafe(24)
		frappe.db.set_value("CRM Appointment Participant", riga.name, "access_token", token)
		# asked with a GET too: the link has to last
		frappe.local.flags.commit = True
	return manage_url(token)


@frappe.whitelist()
def get_appointments(person: str) -> dict:
	"""The person's appointments: the next ones, and the last ones."""
	_mia(person)
	righe = frappe.get_all(
		"CRM Appointment Participant",
		filters={"parenttype": "CRM Appointment", "party_type": "CRM Lead", "party": person},
		fields=["name", "parent", "status", "access_token"],
	)
	adesso = now_datetime()
	prossimi, passati = [], []
	for riga in righe:
		appuntamento = frappe.db.get_value(
			"CRM Appointment",
			riga.parent,
			["name", "title", "service", "starts_on", "ends_on", "status", "location"],
			as_dict=True,
		)
		if not appuntamento:
			continue
		annullato = "Cancelled" in (appuntamento.status, riga.status)
		voce = {
			"name": appuntamento.name,
			"service": frappe.db.get_value("CRM Service", appuntamento.service, "service_name")
			if appuntamento.service
			else appuntamento.title,
			"starts_on": appuntamento.starts_on,
			"ends_on": appuntamento.ends_on,
			"location": appuntamento.location,
			"status": "Cancelled" if annullato else appuntamento.status,
			"staff": [
				frappe.utils.get_fullname(u)
				for u in frappe.get_all(
					"CRM Appointment Staff",
					filters={"parent": appuntamento.name, "parenttype": "CRM Appointment"},
					pluck="user",
				)
			],
		}
		if get_datetime(appuntamento.starts_on) >= adesso and not annullato:
			# moved or cancelled on the booking page, by the service's own rules
			if appuntamento.service:
				voce["manage_url"] = _link_di_gestione(riga)
			prossimi.append(voce)
		else:
			passati.append(voce)
	prossimi.sort(key=lambda v: v["starts_on"])
	passati.sort(key=lambda v: v["starts_on"], reverse=True)
	return {"upcoming": prossimi, "past": passati[:20]}


# ------------------------------------------------------------------ documents


def _online(person: str) -> list:
	from crm.clinica import consegna

	adesso = now_datetime()
	return [
		riga
		for riga in frappe.get_all(
			CONSEGNA,
			filters={
				"lead": person,
				"channel": consegna.ONLINE,
				"status": ("in", (consegna.DISPONIBILE, consegna.SCARICATO)),
			},
			fields=["name", "document", "given_on", "expires_on", "downloads"],
			order_by="given_on desc",
		)
		if get_datetime(riga.expires_on) > adesso
	]


@frappe.whitelist()
def get_documents(person: str) -> dict:
	"""What the centre gave online, while it is online."""
	_mia(person)
	voci = []
	for riga in _online(person):
		documento = frappe.db.get_value(
			"Clinic Document", riga.document, ["title", "document_type", "document_date"], as_dict=True
		)
		if not documento:
			continue
		voci.append(
			{
				"name": riga.name,
				"title": documento.title,
				"document_type": documento.document_type,
				"document_date": documento.document_date,
				"given_on": riga.given_on,
				"expires_on": riga.expires_on,
				"downloaded": bool(riga.downloads),
			}
		)
	return {"documents": voci, "verified": accesso.verificato_da_poco()}


@frappe.whitelist(methods=["GET"])
def download_document(person: str, delivery: str) -> None:
	"""A document, after a code verified in the last minutes; logged like /referto."""
	from crm.clinica import archivio, consegna
	from crm.moduli import traccia

	_mia(person)
	if not accesso.verificato_da_poco():
		frappe.throw(_("Enter your code again to download it"), frappe.PermissionError)
	riga = next((r for r in _online(person) if r.name == delivery), None)
	if not riga:
		frappe.throw(_("This document is no longer online: ask the centre"), frappe.PermissionError)
	documento = frappe.get_doc("Clinic Document", riga.document)
	file_url = archivio._file_di(documento)
	contenuto = frappe.get_doc("File", {"file_url": file_url}).get_content(encodings=[])
	frappe.local.flags.commit = True
	frappe.db.set_value(
		CONSEGNA,
		riga.name,
		{
			"status": consegna.SCARICATO,
			"downloads": (riga.downloads or 0) + 1,
			"last_download_on": now_datetime(),
		},
	)
	traccia.traccia(CONSEGNA, riga.name, "downloaded", _("From the patient area"))
	frappe.local.response.filename = file_url.rsplit("/", 1)[-1]
	frappe.local.response.filecontent = contenuto
	frappe.local.response.type = "download"


# ------------------------------------------------------------------ invoices


def _fatture(person: str) -> list:
	return frappe.get_all(
		"CRM Invoice",
		filters={"party_type": "CRM Lead", "party": person, "docstatus": 1},
		fields=["name", "document_number", "posting_date", "grand_total", "pdf_file"],
		order_by="posting_date desc",
		limit=50,
	)


@frappe.whitelist()
def get_invoices(person: str) -> dict:
	_mia(person)
	return {
		"invoices": [
			{
				"name": f.name,
				"number": f.document_number or f.name,
				"date": f.posting_date,
				"total": f.grand_total,
				"has_pdf": bool(f.pdf_file),
			}
			for f in _fatture(person)
		]
	}


@frappe.whitelist(methods=["GET"])
def download_invoice(person: str, invoice: str) -> None:
	_mia(person)
	fattura = next((f for f in _fatture(person) if f.name == invoice), None)
	if not fattura or not fattura.pdf_file:
		frappe.throw(_("There is no PDF of this invoice"), frappe.PermissionError)
	contenuto = frappe.get_doc("File", {"file_url": fattura.pdf_file}).get_content(encodings=[])
	frappe.local.response.filename = f"{fattura.document_number or fattura.name}.pdf".replace("/", "-")
	frappe.local.response.filecontent = contenuto
	frappe.local.response.type = "download"
