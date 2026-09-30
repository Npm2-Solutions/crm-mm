# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The clinical record on the person's page: who reads it, and the trace of who did.

**Who reads a record** (doc 30, "Vedere la cartella"): its author, always; the
medical director; the other practitioners who have the patient in care, only
when the patient has given the consent to the health dossier, and never an
episode the patient had obscured (`crm.clinica.dossier`). A note marked "only me"
stays its author's, and a draft too; "my discipline" is for the colleagues of the
same qualification. The front desk knows that a visit happened, not what was
said; the manager, sales and marketing do not see it at all.

**The access log.** Frappe writes a View Log only from its Desk form; the CRM reads
through these calls, which write one for every record they return, and the
archive's (`crm.clinica.archivio`) does the same for its documents; Frappe writes
an Access Log for every download of a private file. "Who opened it" shows them
together. The Garante wants those logs kept at least 24 months (Linee guida sul
dossier, 4/6/2015).
"""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import cint, get_fullname

from crm.clinica import dossier, paziente
from crm.permissions import livelli

DOCTYPE = "Clinic Record"
SOLO_IO = "Only me"
DOSSIER = "health_dossier"
#: Two years: the least the Garante asks the access logs to be kept.
GIORNI_REGISTRO = 730


def _col_dossier(lead: str) -> bool:
	return dossier.col_dossier(lead)


def _firmata(doc) -> bool:
	"""Signed as the database has it. Frappe checks "write" while signing, with the
	status already set in memory: a signature in flight is still its author's draft."""
	salvata = frappe.db.get_value(DOCTYPE, doc.get("name"), "docstatus") if doc.get("name") else None
	return cint(doc.get("docstatus") if salvata is None else salvata) >= 1


def puo_leggere(doc, user: str | None = None) -> bool:
	"""Its author, always; the others by the dossier's rules (`crm.clinica.dossier`),
	once it is signed."""
	user = user or frappe.session.user
	if doc.get("practitioner") == user:
		return True
	if doc.get("docstatus") != 1:
		return False
	return dossier.legge_le_altre(doc, user)


def has_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	ptype = ptype or "read"
	if ptype == "create":
		return livelli.puo("clinica.scrivi", user)
	if ptype == "submit":
		return doc.get("practitioner") == user
	if ptype in ("write", "delete"):
		# a draft is its author's; what is signed is not rewritten, it is added to
		return doc.get("practitioner") == user and not _firmata(doc)
	if ptype in ("cancel", "amend"):
		return False
	return puo_leggere(doc, user)


def get_permission_query_conditions(user: str | None = None) -> str:
	user = user or frappe.session.user
	cartella = frappe.qb.DocType(DOCTYPE)
	condizione = cartella.practitioner == user
	condivisa = dossier.condizione_condivisa(cartella, user)
	if condivisa is not None:
		condizione = condizione | ((cartella.docstatus == 1) & condivisa)
	return condizione.get_sql(with_namespace=True, quote_char="`", secondary_quote_char="'")


# ------------------------------------------------------------ the person's page


def _riga(doc) -> dict:
	return {
		"name": doc.name,
		"kind": doc.kind,
		"record_date": doc.record_date,
		"practitioner": doc.practitioner,
		"practitioner_name": get_fullname(doc.practitioner),
		"visibility": doc.visibility,
		"discipline": doc.get("discipline"),
		# shown only to who still reads it: its author and the medical director
		"obscured": cint(doc.get("obscured")),
		"content": doc.content,
		"docstatus": doc.docstatus,
		"signed_on": doc.signed_on,
		"addendum_to": doc.addendum_to,
		"appointment": doc.appointment,
		"mine": doc.practitioner == frappe.session.user,
		# a visit written on a clinical sheet: its questions, answers and report
		**_scheda(doc),
		"attachments": frappe.get_all(
			"File",
			# the report is shown as the report, not as one more attachment
			filters={
				"attached_to_doctype": DOCTYPE,
				"attached_to_name": doc.name,
				"attached_to_field": ("!=", "pdf_file"),
			},
			fields=["name", "file_name", "file_url"],
			order_by="creation asc",
		),
	}


def _scheda(doc) -> dict:
	if not doc.get("template_version"):
		# a visit written freely has its report too, once signed
		return {"template": None, "pdf_file": doc.get("pdf_file"), "pdf_hash": doc.get("pdf_hash")}
	from crm.moduli import modelli

	versione = frappe.get_cached_doc(modelli.VERSIONE, doc.template_version)
	risposte = json.loads(doc.answers or "{}") if isinstance(doc.answers, str) else (doc.answers or {})
	return {
		"template": doc.template,
		"title": doc.title or versione.title,
		"version": versione.version,
		"schema": modelli.carica_schema(versione.schema),
		"answers": risposte,
		"alerts": json.loads(doc.alerts or "[]") if isinstance(doc.alerts, str) else (doc.alerts or []),
		"answers_hash": doc.answers_hash,
		"pdf_file": doc.pdf_file,
		"pdf_hash": doc.pdf_hash,
	}


def _schede() -> list[dict]:
	"""The clinical sheets a practitioner can write a visit on."""
	return frappe.get_all(
		"CRM Form Template",
		filters={"enabled": 1, "current_version": ("is", "set"), "use": "Clinical sheet"},
		fields=["name", "title", "specialty"],
		order_by="title asc",
	)


def _legge() -> bool:
	return livelli.puo("clinica.vedi") or livelli.puo("clinica.scrivi")


def _della_persona(lead: str) -> None:
	if not (_legge() or livelli.puo("clinica.accessi") or livelli.puo("clinica.archivia")):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)


@frappe.whitelist()
def get_record(lead: str) -> dict:
	"""The clinical record the session may read, newest first. Every read is logged.

	The manager comes here for the access log alone: who opened the record, not
	what it says; the front desk to add to the archive what the patient brings.
	They get no record, and nothing is logged for them.
	"""
	_della_persona(lead)
	legge = _legge()
	righe = []
	if legge:
		for nome in frappe.get_list(
			DOCTYPE, filters={"lead": lead}, pluck="name", order_by="record_date desc"
		):
			doc = frappe.get_doc(DOCTYPE, nome)
			doc.add_viewed()
			righe.append(_riga(doc))
	return {
		"records": righe,
		"can_read": legge,
		"can_write": livelli.puo("clinica.scrivi"),
		"sheets": _schede() if livelli.puo("clinica.scrivi") else [],
		"can_see_log": livelli.puo("clinica.accessi"),
		"can_archive": livelli.puo("clinica.archivia"),
		# the patient area: who opens it to the person
		"can_invite": livelli.puo("area.invita"),
		# the medical director obscures an episode at the patient's request
		"can_obscure": livelli.puo("clinica.oscura"),
		"dossier": _col_dossier(lead),
		# "my discipline" is offered to who has one
		"discipline": dossier.disciplina_di(frappe.session.user) if livelli.puo("clinica.scrivi") else None,
		# opened out of the care team: until when, and why
		"out_of_care": dossier.apertura_in_corso(lead),
	}


@frappe.whitelist(methods=["POST"])
def save_record(
	lead: str,
	content: str | None = None,
	name: str | None = None,
	kind: str = "Visit",
	visibility: str = "Care team",
	record_date: str | None = None,
	addendum_to: str | None = None,
	sign: int = 0,
	answers: dict | str | None = None,
) -> dict:
	"""Write a visit or a note; signing makes it final. The first one makes a patient.
	A visit on a clinical sheet keeps its ``answers``: what converts, as a form does."""
	livelli.verifica("clinica.scrivi")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	if name:
		doc = frappe.get_doc(DOCTYPE, name)
		if doc.lead != lead:
			frappe.throw(_("This record belongs to somebody else"))
		doc.check_permission("write")
	else:
		doc = frappe.new_doc(DOCTYPE)
		doc.lead = lead
		doc.practitioner = frappe.session.user
		doc.addendum_to = addendum_to
	if visibility not in dossier.VISIBILITA:
		frappe.throw(_("{0} is not who reads a record").format(visibility))
	doc.update({"kind": kind, "visibility": visibility, "content": content})
	if answers is not None and doc.template_version:
		from crm.moduli import modelli
		from crm.moduli import schema as S

		schema = modelli.carica_schema(frappe.get_cached_doc(modelli.VERSIONE, doc.template_version).schema)
		letti = frappe.parse_json(answers) if isinstance(answers, str) else answers
		puliti, _errori, _stato = S.pulisci(schema, letti or {})
		doc.answers = json.dumps(puliti, ensure_ascii=False)
	if record_date:
		doc.record_date = record_date
	doc.save()
	if cint(sign):
		doc.submit()
	return _riga(doc)


@frappe.whitelist(methods=["POST"])
def start_sheet(lead: str, template: str, appointment: str | None = None) -> dict:
	"""A visit written on a clinical sheet: the version published now, a draft of
	its author's until it is signed."""
	livelli.verifica("clinica.scrivi")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	from crm.moduli import modelli

	modello = frappe.get_doc(modelli.MODELLO, template)
	if modello.use != "Clinical sheet" or not modello.enabled or not modello.current_version:
		frappe.throw(_("{0} is not a clinical sheet in use").format(frappe.bold(modello.title)))
	versione = frappe.get_doc(modelli.VERSIONE, modello.current_version)
	doc = frappe.get_doc(
		{
			"doctype": DOCTYPE,
			"lead": lead,
			"kind": "Visit",
			"practitioner": frappe.session.user,
			"record_date": frappe.utils.now_datetime(),
			"appointment": appointment,
			"template": modello.name,
			"template_version": versione.name,
			"title": versione.title,
			"schema_hash": versione.schema_hash,
			"answers": "{}",
		}
	).insert()
	return _riga(doc)


@frappe.whitelist(methods=["POST"])
def delete_draft(name: str) -> None:
	"""A draft can be thrown away by whoever wrote it; a signed record never."""
	doc = frappe.get_doc(DOCTYPE, name)
	doc.check_permission("delete")
	frappe.delete_doc(DOCTYPE, name)


#: What a line of the access log says was opened: never what it contains.
APERTO = {"Clinic Record": "record", "Clinic Document": "archive", "File": "file"}


@frappe.whitelist()
def access_log(lead: str) -> list[dict]:
	"""Who opened this person's record and archive, and when: not what they read.

	The record and the archive listed (a View Log for each entry they showed) and
	every file downloaded (Frappe's Access Log), one line for each person, minute
	and kind of opening."""
	livelli.verifica("clinica.accessi")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	voci = {
		doctype: frappe.get_all(doctype, filters={"lead": lead}, pluck="name")
		for doctype in ("Clinic Record", "Clinic Document")
	}
	righe = []
	for doctype, nomi in voci.items():
		if nomi:
			righe += [
				frappe._dict(viewed_by=riga.viewed_by, kind=doctype, creation=riga.creation)
				for riga in frappe.get_all(
					"View Log",
					filters={"reference_doctype": doctype, "reference_name": ("in", nomi)},
					fields=["viewed_by", "creation"],
					order_by="creation desc",
					limit=1000,
				)
			]
	file = [
		nome
		for doctype, nomi in voci.items()
		if nomi
		for nome in frappe.get_all(
			"File",
			filters={"attached_to_doctype": doctype, "attached_to_name": ("in", nomi)},
			pluck="name",
		)
	]
	if file:
		righe += [
			frappe._dict(viewed_by=riga.user, kind="File", creation=riga.creation)
			for riga in frappe.get_all(
				"Access Log",
				filters={"export_from": "File", "reference_document": ("in", file)},
				fields=["user", "creation"],
				order_by="creation desc",
				limit=1000,
			)
		]
	# the openings out of the care team, each with its reason
	aperture = dossier.aperture(lead)
	return sorted(_per_minuto(righe) + aperture, key=lambda riga: riga.creation, reverse=True)[:300]


def _per_minuto(righe: list[dict]) -> list[dict]:
	"""One line for each person, minute and kind: opening the Clinic tab lists
	every entry at once, and that is one opening."""
	gruppi: dict[tuple, frappe._dict] = {}
	for riga in sorted(righe, key=lambda r: r.creation, reverse=True):
		chiave = (riga.viewed_by, riga.creation.replace(second=0, microsecond=0), riga.kind)
		gruppo = gruppi.get(chiave)
		if gruppo:
			gruppo.count += 1
			continue
		gruppi[chiave] = frappe._dict(
			viewed_by=riga.viewed_by,
			viewed_by_name=get_fullname(riga.viewed_by),
			creation=riga.creation,
			kind=APERTO.get(riga.kind, riga.kind),
			count=1,
		)
	return list(gruppi.values())


def persone_in_cura(user: str):
	"""The people ``user`` wrote a clinical record for: in their care, and so theirs
	to see on the CRM's side too (`crm_people_in_care`)."""
	if not paziente.clinica_accesa():
		return None
	cartella = frappe.qb.DocType(DOCTYPE).as_("_in_cura")
	return frappe.qb.from_(cartella).select(cartella.lead).where(cartella.practitioner == user)


# ---------------------------------------------------------------- the history


def visite_su(doctype: str, name: str) -> list[dict]:
	"""The visits in the person's history: a padlock for whoever may only know of them.

	The front desk and the practitioners see that a visit happened and who did it;
	what was said stays in the Clinic tab, for who may read it. A note "only me"
	and a draft are nobody else's business, not even as a padlock; nor is an
	episode the patient had obscured, but for its author and the medical director.
	"""
	if doctype != "CRM Lead" or not paziente.clinica_accesa():
		return []
	legge = livelli.puo("clinica.vedi")
	if not (legge or livelli.puo("clinica.traccia")):
		return []
	utente = frappe.session.user
	leggibili = set(frappe.get_list(DOCTYPE, filters={"lead": name}, pluck="name")) if legge else set()
	nodi = []
	for riga in frappe.get_all(
		DOCTYPE,
		filters={"lead": name},
		fields=[
			"name",
			"kind",
			"record_date",
			"practitioner",
			"visibility",
			"docstatus",
			"obscured",
			"creation",
		],
	):
		mio = riga.practitioner == utente
		if not mio and (riga.docstatus != 1 or riga.visibility == SOLO_IO):
			continue
		if not mio and riga.obscured and not dossier.vede_gli_oscurati(utente):
			continue
		nodi.append(
			{
				"name": riga.name,
				"activity_type": "clinical",
				"creation": riga.record_date or riga.creation,
				"owner": riga.practitioner,
				"data": {
					"kind": riga.kind,
					"practitioner_name": get_fullname(riga.practitioner),
					"locked": riga.name not in leggibili,
					"draft": riga.docstatus == 0,
				},
				"is_lead": True,
			}
		)
	return nodi


#: The logs "Who opened it" reads: the openings, and the downloads of the files.
REGISTRI = ("View Log", "Access Log")


def proteggi_registro_accessi() -> None:
	"""Keep the access logs two years at least, whatever Log Settings was told.

	Frappe keeps View Logs and Access Logs until somebody adds them to Log
	Settings, whose defaults for them are 180 and 30 days: that would quietly throw
	away what the Garante asks to keep for 24 months.
	"""
	if not frappe.db.exists("DocType", "Log Settings"):
		return
	impostazioni = frappe.get_single("Log Settings")
	cambiate = False
	for riga in impostazioni.get("logs_to_clear") or []:
		if riga.ref_doctype in REGISTRI and cint(riga.days) < GIORNI_REGISTRO:
			riga.days = GIORNI_REGISTRO
			cambiate = True
	if cambiate:
		impostazioni.save(ignore_permissions=True)


def valida_impostazioni_log(doc, method=None) -> None:
	"""Whoever edits Log Settings later meets the same floor."""
	for riga in doc.get("logs_to_clear") or []:
		if riga.ref_doctype in REGISTRI and cint(riga.days) < GIORNI_REGISTRO:
			riga.days = GIORNI_REGISTRO
			frappe.msgprint(
				_(
					"Views of the clinical record are kept {0} days at least: the Garante asks for 24 months"
				).format(GIORNI_REGISTRO),
				alert=True,
			)


def allegato_privato(doc, method=None) -> None:
	"""An attachment to the clinical record or archive is private, or it is not attached.

	Frappe serves a private file only to whoever may read the record it is attached
	to; a public one to anybody with the link. The file is already written when
	this runs, so it is refused rather than quietly relabelled: the CRM uploads them
	private, and anything else asking for public is a mistake to stop.
	"""
	if doc.attached_to_doctype not in (DOCTYPE, "Clinic Document"):
		return
	if not (cint(doc.is_private) or (doc.file_url or "").startswith("/private/")):
		frappe.throw(_("An attachment to the clinical record is private"))
