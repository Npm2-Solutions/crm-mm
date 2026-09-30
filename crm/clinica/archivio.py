# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The clinical archive: the patient's documents, beside the record.

What the patient brings (a report of another doctor, a test, an image, a
prescription), what arrives in a conversation, and the report the centre makes
when a visit is signed: each one a document with its type, its date, where it
comes from and whom it is for, the file private and its SHA-256 kept
(requisiti.md §5).

**Who reads it**, as the record (`crm.clinica.dossier`): whom it is for and
whoever added it; the medical director; the other practitioners who have the
patient in care, once the patient consented to the health dossier, and never a
document the patient had obscured. "Only me" stays its practitioner's; "my
discipline" is for the colleagues of the same qualification.

**Who adds one**: a practitioner, for their patients; the front desk, which scans
what the patient brings, for a practitioner it names, and then sees only what it
added. A document added by mistake (the wrong person, the wrong file) goes the
same day by whoever added it, later only by the medical director, and the
removal stays in the audit log with its reason. A report is the signed visit's
own PDF, and stays with it.

**The access log**: listing the archive writes a View Log for each document, and
Frappe writes an Access Log for every download of a private file; "Who opened it"
shows them with the record's.
"""

from __future__ import annotations

import hashlib

import frappe
from frappe import _
from frappe.utils import cint, get_fullname, getdate, nowdate

from crm.clinica import cartella, dossier, paziente
from crm.permissions import livelli

DOCTYPE = "Clinic Document"
SOLO_IO = "Only me"
TUTTI = "Care team"
REFERTO = "Report"
TIPI = ("Report", "External report", "Test result", "Imaging", "Prescription", "Signed form", "Other")
#: A report of the centre comes from a signed visit; everything else is added.
DA_AGGIUNGERE = TIPI[1:]
MESSAGGIO = "WhatsApp Message"


# ------------------------------------------------------------------ who sees them


def puo_leggere(doc, user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user in (doc.get("practitioner"), doc.get("added_by")):
		return True
	return dossier.legge_le_altre(doc, user)


def _puo_togliere(doc, user: str) -> bool:
	"""The same day by whoever added it; later, the medical director. A report
	belongs to the signed visit it comes from."""
	if doc.get("record"):
		return False
	if livelli.ambito("clinica.vedi", user) == livelli.CENTRO:
		return True
	return doc.get("added_by") == user and getdate(doc.get("added_on")) == getdate(nowdate())


def has_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	ptype = ptype or "read"
	if ptype == "create":
		return livelli.puo("clinica.archivia", user)
	if ptype == "write":
		# what it is and whom it is for can be put right; the file is never replaced
		return (
			not doc.get("record")
			and user in (doc.get("added_by"), doc.get("practitioner"))
			and livelli.puo("clinica.archivia", user)
		)
	if ptype == "delete":
		return _puo_togliere(doc, user)
	if ptype in ("submit", "cancel", "amend"):
		return False
	return puo_leggere(doc, user)


def get_permission_query_conditions(user: str | None = None) -> str:
	user = user or frappe.session.user
	archivio = frappe.qb.DocType(DOCTYPE)
	condizione = (archivio.practitioner == user) | (archivio.added_by == user)
	condivisa = dossier.condizione_condivisa(archivio, user)
	if condivisa is not None:
		condizione = condizione | condivisa
	return condizione.get_sql(with_namespace=True, quote_char="`", secondary_quote_char="'")


# ------------------------------------------------------------------ the person's page


def _file_di(doc) -> str | None:
	# a report of the centre is the signed visit's own PDF, served as the visit's
	if doc.file:
		return doc.file
	return frappe.db.get_value(cartella.DOCTYPE, doc.record, "pdf_file") if doc.record else None


def _riga(doc) -> dict:
	file = _file_di(doc)
	return {
		"name": doc.name,
		"title": doc.title,
		"document_type": doc.document_type,
		"document_date": doc.document_date,
		"source": doc.source,
		"practitioner": doc.practitioner,
		"practitioner_name": get_fullname(doc.practitioner) if doc.practitioner else None,
		"added_by": doc.added_by,
		"added_by_name": get_fullname(doc.added_by) if doc.added_by else None,
		"added_on": doc.added_on,
		"visibility": doc.visibility,
		# shown only to who still reads it: whom it is for, who added it, the director
		"obscured": cint(doc.obscured),
		"file": file,
		"file_name": file.rsplit("/", 1)[-1] if file else None,
		"file_hash": doc.file_hash,
		"record": doc.record,
		"appointment": doc.appointment,
		"notes": doc.notes,
		"not_online": cint(doc.get("not_online")),
		# how it was given to the patient: by hand, or online until when
		"deliveries": _consegne(doc.name),
		"can_edit": has_permission(doc, "write"),
		"can_remove": has_permission(doc, "delete"),
	}


def _consegne(nome: str) -> list[dict]:
	from crm.clinica import consegna

	return consegna.consegne(nome)


def _operatori() -> list[dict]:
	"""Whom a document can be for: the users who write the clinical record."""
	utenti = frappe.get_all(
		"User",
		filters={
			"enabled": 1,
			"user_type": "System User",
			"name": ("not in", ("Administrator", "Guest")),
		},
		fields=["name", "full_name"],
		order_by="full_name asc",
	)
	return [
		{"value": utente.name, "label": utente.full_name or utente.name}
		for utente in utenti
		if livelli.puo("clinica.scrivi", utente.name)
	]


def _della_persona(lead: str) -> None:
	if not (livelli.puo("clinica.vedi") or livelli.puo("clinica.scrivi") or livelli.puo("clinica.archivia")):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)


@frappe.whitelist()
def get_documents(lead: str) -> dict:
	"""The archive the session may read, the most recent first. Each document
	listed is logged, as the record's entries are."""
	_della_persona(lead)
	righe = []
	for nome in frappe.get_list(
		DOCTYPE, filters={"lead": lead}, pluck="name", order_by="document_date desc, creation desc"
	):
		doc = frappe.get_doc(DOCTYPE, nome)
		doc.add_viewed()
		righe.append(_riga(doc))
	return {
		"documents": righe,
		"can_add": livelli.puo("clinica.archivia"),
		"can_obscure": livelli.puo("clinica.oscura"),
		"can_deliver": livelli.puo("clinica.consegna"),
	}


@frappe.whitelist()
def get_choices() -> dict:
	"""What a document can be, and whom it can be for: a practitioner adds for
	themselves by default, the desk says for whom."""
	livelli.verifica("clinica.archivia")
	return {
		"types": [{"value": tipo, "label": _(tipo)} for tipo in DA_AGGIUNGERE],
		"for_me": livelli.puo("clinica.scrivi"),
		# "my discipline" is offered to a practitioner who has one
		"discipline": dossier.disciplina_di(frappe.session.user) if livelli.puo("clinica.scrivi") else None,
		"practitioners": _operatori(),
	}


def _campi(
	title: str | None,
	document_type: str | None,
	document_date: str | None,
	source: str | None,
	practitioner: str | None,
	visibility: str | None,
	notes: str | None,
	not_online: int | None = None,
) -> dict:
	titolo = (title or "").strip()
	if not titolo:
		frappe.throw(_("A document needs a title"))
	if document_type not in DA_AGGIUNGERE:
		frappe.throw(_("{0} is not a kind of document of the archive").format(document_type))
	scrive = livelli.puo("clinica.scrivi")
	practitioner = practitioner or (frappe.session.user if scrive else None)
	if not practitioner:
		frappe.throw(_("Say which practitioner the document is for"))
	if practitioner != frappe.session.user and not livelli.puo("clinica.scrivi", practitioner):
		frappe.throw(_("{0} does not write clinical records").format(get_fullname(practitioner)))
	# "only me" and "my discipline" are a practitioner's choices about their own document
	proprio = scrive and practitioner == frappe.session.user
	return {
		"title": titolo[:140],
		"document_type": document_type,
		"document_date": getdate(document_date) if document_date else None,
		"source": (source or "").strip() or None,
		"practitioner": practitioner,
		"visibility": visibility if proprio and visibility in dossier.VISIBILITA else TUTTI,
		"notes": (notes or "").strip() or None,
		# genetic tests, HIV, or what the patient left out: given by hand only
		"not_online": cint(not_online),
	}


def _contenuto(allegato) -> bytes:
	contenuto = allegato.get_content(encodings=[])
	return contenuto.encode() if isinstance(contenuto, str) else contenuto


def _archivia(lead: str, allegato, campi: dict, appointment: str | None = None) -> dict:
	if appointment:
		frappe.has_permission("CRM Appointment", "read", doc=appointment, throw=True)
	doc = frappe.get_doc(
		{
			"doctype": DOCTYPE,
			"lead": lead,
			**campi,
			"file": allegato.file_url,
			"file_hash": hashlib.sha256(_contenuto(allegato)).hexdigest(),
			"appointment": appointment,
		}
	)
	doc.flags.allegato = allegato.name
	doc.insert()
	return _riga(doc)


@frappe.whitelist(methods=["POST"])
def add_document(
	lead: str,
	file: str,
	title: str,
	document_type: str,
	document_date: str | None = None,
	source: str | None = None,
	practitioner: str | None = None,
	visibility: str | None = None,
	notes: str | None = None,
	not_online: int | None = None,
	appointment: str | None = None,
) -> dict:
	"""A file the session uploaded, private and attached to nothing yet, filed in
	the person's archive. ``file`` is the File's name."""
	livelli.verifica("clinica.archivia")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	allegato = frappe.get_doc("File", file)
	if allegato.owner != frappe.session.user or allegato.attached_to_doctype or not cint(allegato.is_private):
		frappe.throw(_("Upload the file again: it has to be private, and just uploaded by you"))
	campi = _campi(title, document_type, document_date, source, practitioner, visibility, notes, not_online)
	return _archivia(lead, allegato, campi, appointment)


@frappe.whitelist(methods=["POST"])
def update_document(
	name: str,
	title: str,
	document_type: str,
	document_date: str | None = None,
	source: str | None = None,
	practitioner: str | None = None,
	visibility: str | None = None,
	notes: str | None = None,
	not_online: int | None = None,
) -> dict:
	"""What a document is, when, where it comes from, whom it is for: the file stays."""
	doc = frappe.get_doc(DOCTYPE, name)
	doc.check_permission("write")
	doc.update(
		_campi(title, document_type, document_date, source, practitioner, visibility, notes, not_online)
	)
	doc.save()
	return _riga(doc)


@frappe.whitelist(methods=["POST"])
def remove_document(name: str, reason: str) -> None:
	"""A document added by mistake goes; the audit log keeps who took it away, why,
	and the SHA-256 of what it was."""
	from crm.moduli import traccia

	doc = frappe.get_doc(DOCTYPE, name)
	doc.check_permission("delete")
	motivo = (reason or "").strip()
	if not motivo:
		frappe.throw(_("Say why the document goes"))
	traccia.traccia(
		DOCTYPE,
		doc.name,
		"removed",
		motivo,
		{
			"lead": doc.lead,
			"title": doc.title,
			"document_type": doc.document_type,
			"file_hash": doc.file_hash,
			"added_by": doc.added_by,
			"added_on": str(doc.added_on),
		},
	)
	frappe.delete_doc(DOCTYPE, doc.name, ignore_permissions=True)


# ------------------------------------------------------------------ from elsewhere


def dal_referto(visita) -> str | None:
	"""The report of a signed visit, filed in the archive: the visit's own PDF, for
	the practitioner who signed it, read by whoever reads the visit."""
	if not visita.get("pdf_file") or frappe.db.exists(DOCTYPE, {"record": visita.name}):
		return None
	doc = frappe.get_doc(
		{
			"doctype": DOCTYPE,
			"lead": visita.lead,
			"title": visita.get("title") or _("Visit"),
			"document_type": REFERTO,
			"document_date": getdate(visita.record_date or visita.signed_on),
			"practitioner": visita.practitioner,
			"visibility": visita.visibility or TUTTI,
			"discipline": visita.get("discipline"),
			"obscured": cint(visita.get("obscured")),
			"record": visita.name,
			"file_hash": visita.get("pdf_hash"),
			"appointment": visita.get("appointment"),
			"added_by": visita.practitioner,
			"added_on": visita.signed_on,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _file_del_messaggio(messaggio):
	if not messaggio.attach:
		return None
	nome = frappe.db.get_value(
		"File",
		{"file_url": messaggio.attach, "attached_to_doctype": MESSAGGIO, "attached_to_name": messaggio.name},
		"name",
	) or frappe.db.get_value("File", {"file_url": messaggio.attach}, "name")
	return frappe.get_doc("File", nome) if nome else None


def _rendi_privato(originale, messaggio) -> None:
	"""What the person sent stays in the conversation, private: reachable by who
	reads the conversation, no longer by its address alone. Left alone when another
	document points at the same file."""
	if frappe.db.count("File", {"file_url": originale.file_url}) > 1:
		return
	originale.is_private = 1
	originale.save(ignore_permissions=True)
	frappe.db.set_value(MESSAGGIO, messaggio.name, "attach", originale.file_url, update_modified=False)


@frappe.whitelist(methods=["POST"])
def archive_from_message(
	message: str,
	title: str,
	document_type: str,
	document_date: str | None = None,
	source: str | None = None,
	practitioner: str | None = None,
	visibility: str | None = None,
	notes: str | None = None,
	not_online: int | None = None,
) -> dict:
	"""A file received in a conversation, filed in the archive of the person who sent it."""
	livelli.verifica("clinica.archivia")
	if not frappe.db.exists("DocType", MESSAGGIO):
		frappe.throw(_("There are no conversations on this site"))
	messaggio = frappe.get_doc(MESSAGGIO, message)
	messaggio.check_permission("read")
	lead = paziente.persona_di(messaggio.reference_doctype, messaggio.reference_name)
	if not lead:
		frappe.throw(_("This conversation is not with a person in DottorCloud"))
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	campi = _campi(title, document_type, document_date, source, practitioner, visibility, notes, not_online)
	originale = _file_del_messaggio(messaggio)
	if not originale or originale.is_remote_file:
		frappe.throw(_("This message has no file kept by DottorCloud"))
	# a file received is private first, so the archive's copy shares it, private
	if messaggio.type == "Incoming" and not cint(originale.is_private):
		_rendi_privato(originale, messaggio)
	copia = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": originale.file_name,
			"is_private": 1,
			"content": _contenuto(originale),
		}
	).insert(ignore_permissions=True)
	return _archivia(lead, copia, campi)
