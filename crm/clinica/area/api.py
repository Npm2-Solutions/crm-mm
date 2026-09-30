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
from frappe.rate_limiter import rate_limit
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
	from crm.clinica.area import messaggi, piani
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
		"people": [
			{
				"name": p.lead,
				"lead_name": p.lead_name,
				"relation": p.relation,
				"unread": messaggi.da_leggere(p.lead),
				# the area shows "Plans" to who follows one now
				"plans": piani.piani_in_corso(p.lead),
			}
			for p in persone
		],
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


# ------------------------------------------------------------------ preparing the visit

#: In the trace of a link: made, or taken up, from the area.
DALL_AREA = "Patient area"
#: How long the forms opened from the area stay open.
ORE_MODULI = 4
#: A form filled at home that is signed at the desk (`dovuti._in_corso`).
A_STUDIO = "to_sign_at_desk"


#: Why who is in does not sign: the page says it in its own words.
PERCHE = {
	"parent": "Your forms are answered by a parent or guardian, from their area",
	"not_linked": "To sign for them, ask the centre to add you to their related people",
	"follows": "The person signs their own forms",
}


def _chi_firma(person: str, riga) -> tuple[dict | None, str | None]:
	"""Who signs the person's forms from the area, as a link by email would go
	(`richieste.destinatario`): the person, if nobody answers for them; else the
	parent or guardian who is in. Who only follows them sees, and does not sign
	(design.md, "Familiari"). Else, why not (`PERCHE`)."""
	from crm.moduli import richieste

	rappresentanti = richieste._rappresentanti(person)
	if riga.relation == accesso.SE_STESSO:
		if rappresentanti or richieste._minorenne(person):
			return None, "parent"
		return {"lead": person, "given_by": None}, None
	if riga.relation == accesso.TUTORE:
		for chi in rappresentanti:
			if accesso._normalizza(frappe.db.get_value("CRM Lead", chi, "email")) == frappe.session.user:
				return {"lead": chi, "given_by": chi}, None
		return None, "not_linked"
	return None, "follows"


@frappe.whitelist()
def get_forms(person: str) -> dict:
	"""What to prepare for the next appointment: the forms the centre asks, which
	are under way, and whether who is in signs them (design.md, "Prepara la visita")."""
	from crm.moduli import dovuti

	riga = _mia(person)
	prossimo = dovuti.prossimo_appuntamento(person)
	# the person's own forms, clinical ones too: they are theirs to fill
	voci = dovuti.dovuti([person], {person: prossimo}, clinici=True)[person]
	firma, perche = _chi_firma(person, riga)
	# today's forms count for today's visit, but "before your appointment" only
	# while it is still ahead, as the appointments say
	davanti = prossimo and get_datetime(prossimo.starts_on) >= now_datetime()
	return {
		"appointment": {"name": prossimo.name, "starts_on": prossimo.starts_on} if davanti else None,
		"forms": [
			{
				"template": voce["template"],
				"title": voce["title"],
				"reason": voce["reason"],
				"pending": voce["pending"],
				# filled already, it waits for its signature at the desk
				"fill": bool(firma) and voce["pending"] != A_STUDIO,
			}
			for voce in voci
		],
		"can_fill": bool(firma),
		"why_not": perche,
	}


def _da_riprendere(person: str, firma: dict, scelti: set[str]):
	"""An open link for these forms, signed by the same person: taken up again with
	its answers so far rather than started twice - made by the area, or sent by
	email (whose link then gives way to the area's, as a new link would)."""
	from crm.moduli import richieste

	for nome in frappe.get_all(
		richieste.RICHIESTA,
		filters={
			"lead": person,
			"channel": "Link",
			"via": ("is", "not set"),
			"status": ("in", richieste.APERTE),
			"expires_on": (">", now_datetime()),
		},
		pluck="name",
		order_by="creation desc",
	):
		capo = frappe.get_doc(richieste.RICHIESTA, nome)
		if (capo.given_by or None) != firma["given_by"]:
			continue
		aperti = {r.template for r in richieste._gruppo(capo) if r.status in richieste.APERTE}
		if scelti <= aperti:
			return capo
	return None


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=30, seconds=60 * 60)
def fill_forms(person: str, templates) -> dict:
	"""The forms page for these forms, already open: who is in came with a code, so
	the page asks for none. Returns its link and its session."""
	from frappe.utils import add_to_date

	from crm.moduli import dovuti, richieste, traccia

	riga = _mia(person)
	firma, perche = _chi_firma(person, riga)
	if not firma:
		frappe.throw(_(PERCHE[perche]), frappe.PermissionError)
	chiesti = {voce["template"] for voce in get_forms(person)["forms"] if voce["fill"]}
	elenco = frappe.parse_json(templates) if isinstance(templates, str) else (templates or [])
	scelti = [nome for nome in elenco if nome in chiesti]
	if not scelti:
		frappe.throw(_("There is nothing to fill here"))
	capo = _da_riprendere(person, firma, set(scelti))
	if capo:
		token = richieste._segreto()
		capo.db_set("token_hash", richieste._impronta(token))
		traccia.traccia(richieste.RICHIESTA, capo.name, "taken up", DALL_AREA)
	else:
		prossimo = dovuti.prossimo_appuntamento(person)
		# where a code goes if the page asks for one again: the signer's address
		indirizzo = frappe.db.get_value("CRM Lead", firma["lead"], "email") or frappe.session.user
		gruppo, token = richieste._crea(
			person,
			scelti,
			"Link",
			scadenza=add_to_date(now_datetime(), hours=ORE_MODULI),
			appointment=prossimo.name if prossimo else None,
			given_by=firma["given_by"],
			recipient=firma["lead"],
			sent_to=richieste._nascosta(indirizzo),
			# asked for by who is in: nobody of the centre sent it, and the forms
			# are the person's own, clinical ones too
			mittente=frappe.session.user,
			dal_centro=True,
		)
		capo = gruppo[0]
		traccia.traccia(
			richieste.RICHIESTA, capo.name, "sent", DALL_AREA, {"forms": [r.name for r in gruppo]}
		)
	sessione = richieste._apri_sessione(capo)
	return {"url": f"/modulo/{token}", "token": token, "session": sessione}


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
