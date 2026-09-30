# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A person's documents, on their page: what they bring, what arrives in a
conversation, what the centre makes - a signed form, a contract; with the clinic
a report, a test, an image (docs/gestionale-medico/design.md, "Tre strati").

Each one has its type, its date, where it comes from and whom it is for; the file
private, its SHA-256 kept.

- **Who reads them**: whom a document is for and who added it, always; the others
  who read the person's documents (`documenti.vedi`) and see the person - the desk
  and the manager for the whole centre, a practitioner for their people. What
  carries the mark of health data (`clinical`: its kind's, or with the clinic on
  what is for a health professional) is read by the rule the clinic registers
  instead (`crm.permissions.sanitari`), every listing in the access log; with
  nobody registered, only whom it is for and who added it read it.
- **Who adds one** (`documenti.aggiungi`): the desk scans what the person brings,
  for somebody of the centre when it is theirs; a practitioner adds for themselves.
- **A document added by mistake** goes the same day by whoever added it, later by
  who takes documents away (`documenti.togli`, the manager), and the removal stays
  in the audit log with its reason and the SHA-256 of what it was.
- **What a module adds** (`registra_estensione`): its fields, read and written -
  the clinic's "who reads it", "never online", the visit a report comes from.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass

import frappe
from frappe import _
from frappe.utils import cint, get_fullname, getdate, nowdate

from crm.documenti import regole as R
from crm.marchio import con_nome
from crm.permissions import livelli, org_hierarchy, sanitari

DOCTYPE = "CRM Document"
MESSAGGIO = "WhatsApp Message"


# ------------------------------------------------------------------ what a module adds


@dataclass(frozen=True)
class Estensione:
	"""What a module keeps on a document besides the CRM's fields."""

	#: What a document's row adds for the page.
	legge: Callable[[object], dict]
	#: What a document takes from what was sent: (document, what was sent).
	scrive: Callable[[object, dict], None]
	#: What the page's choices add, for adding one.
	scelte: Callable[[], dict] | None = None
	#: Why a document stays as it is, not changed nor taken away: a signed visit's
	#: report belongs to the visit. None: it may.
	fisso: Callable[[object], str | None] | None = None
	#: What the person's documents add for the page: what the session may do more.
	pagina: Callable[[str], dict] | None = None
	#: Whom else a document can be for: {value, label} - the clinic's practitioners.
	per_chi: Callable[[], list[dict]] | None = None


_estensioni: list[Estensione] = []


def registra_estensione(estensione: Estensione) -> None:
	if estensione not in _estensioni:
		_estensioni.append(estensione)


def _fisso(doc) -> str | None:
	for estensione in _estensioni:
		if estensione.fisso and (motivo := estensione.fisso(doc)):
			return motivo
	return None


# ------------------------------------------------------------------ who reads, who writes


def qualifica_di(user: str) -> str | None:
	"""Somebody's qualification: the one of their provider record, if they have one."""
	return frappe.db.get_value("CRM Service Provider", {"user": user, "enabled": 1}, "qualification")


def e_suo(doc, user: str) -> bool:
	"""Whom it is for, and who added it."""
	return user in (doc.get("practitioner"), doc.get("added_by"))


def puo_leggere(doc, user: str | None = None) -> bool:
	user = user or frappe.session.user
	if e_suo(doc, user):
		return True
	if cint(doc.get("clinical")):
		return sanitari.legge(doc, user)
	return livelli.puo("documenti.vedi", user) and bool(
		frappe.has_permission("CRM Lead", "read", doc=doc.get("lead"), user=user)
	)


def _puo_togliere(doc, user: str) -> bool:
	"""The same day by whoever added it; later, who takes documents away - of what
	they read."""
	if _fisso(doc) or not puo_leggere(doc, user):
		return False
	if doc.get("added_by") == user and getdate(doc.get("added_on")) == getdate(nowdate()):
		return True
	return livelli.puo("documenti.togli", user)


def has_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	ptype = ptype or "read"
	if ptype == "create":
		return livelli.puo("documenti.aggiungi", user)
	if ptype == "write":
		# what it is and whom it is for can be put right; the file is never replaced
		return not _fisso(doc) and e_suo(doc, user) and livelli.puo("documenti.aggiungi", user)
	if ptype == "delete":
		return _puo_togliere(doc, user)
	if ptype in ("submit", "cancel", "amend"):
		return False
	return puo_leggere(doc, user)


def condizione(tabella, user: str):
	"""Who reads a document, as a condition on its table: the same rule."""
	proprio = (tabella.practitioner == user) | (tabella.added_by == user)
	altri = None
	if livelli.puo("documenti.vedi", user):
		visibili = org_hierarchy.visible_leads(user)
		altri = tabella.clinical == 0
		if visibili is not None:
			altri = altri & tabella.lead.isin(visibili)
	clinici = sanitari.condizione(tabella, user)
	if clinici is not None:
		clinici = (tabella.clinical == 1) & clinici
		altri = clinici if altri is None else (altri | clinici)
	return proprio if altri is None else (proprio | altri)


def get_permission_query_conditions(user: str | None = None) -> str:
	user = user or frappe.session.user
	return condizione(frappe.qb.DocType(DOCTYPE), user).get_sql(
		with_namespace=True, quote_char="`", secondary_quote_char="'"
	)


def marca(doc) -> None:
	"""The mark "health data" a document carries: its kind's, or whom it is for."""
	tipo = R.tipo(doc.document_type)
	doc.clinical = 1 if (tipo and tipo.clinico) or sanitari.per_chi_scrive(doc) else 0


def aperto(doc) -> None:
	"""A document with health data read: in the access log, with the record's."""
	if cint(doc.get("clinical")):
		doc.add_viewed()


# ------------------------------------------------------------------ the person's page


def tipi_accesi() -> list[R.TipoDocumento]:
	"""The kinds switched on here: the CRM's, and a module's where it is on."""
	livelli.carica()
	moduli = livelli.moduli_attivi()
	return [
		tipo
		for tipo in R.tipi()
		if not tipo.modulo or livelli.stato_modulo(tipo.modulo, moduli) != livelli.SPENTO
	]


def _riga(doc) -> dict:
	from crm.documenti import consegna

	riga = {
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
		"clinical": cint(doc.clinical),
		"file": doc.file,
		"file_name": doc.file.rsplit("/", 1)[-1] if doc.file else None,
		"file_hash": doc.file_hash,
		"appointment": doc.appointment,
		"notes": doc.notes,
		# how it was given to the person: by hand, or online until when
		"deliveries": consegna.consegne(doc.name),
		"can_edit": has_permission(doc, "write"),
		"can_remove": has_permission(doc, "delete"),
	}
	for estensione in _estensioni:
		riga.update(estensione.legge(doc))
	return riga


def _della_persona(lead: str) -> None:
	if not (livelli.puo("documenti.vedi") or livelli.puo("documenti.aggiungi")):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)


@frappe.whitelist()
def get_documents(lead: str) -> dict:
	"""The person's documents the session reads, the most recent first. Each one with
	health data listed is logged, as the record's entries are."""
	_della_persona(lead)
	righe = []
	for nome in frappe.get_list(
		DOCTYPE, filters={"lead": lead}, pluck="name", order_by="document_date desc, creation desc"
	):
		doc = frappe.get_doc(DOCTYPE, nome)
		aperto(doc)
		righe.append(_riga(doc))
	pagina = {
		"documents": righe,
		"can_add": livelli.puo("documenti.aggiungi"),
		"can_deliver": livelli.puo("documenti.consegna"),
	}
	for estensione in _estensioni:
		if estensione.pagina:
			pagina.update(estensione.pagina(lead))
	return pagina


def _per_chi() -> list[dict]:
	"""Whom a document can be for: the people of the centre who provide its services,
	and whom a module adds - the clinic's practitioners."""
	utenti = frappe.get_all(
		"CRM Service Provider", filters={"enabled": 1, "user": ("is", "set")}, pluck="user"
	)
	righe = frappe.get_all(
		"User",
		filters={"name": ("in", list(set(utenti)) or [""]), "enabled": 1},
		fields=["name", "full_name"],
	)
	chi = {utente.name: utente.full_name or utente.name for utente in righe}
	for estensione in _estensioni:
		if estensione.per_chi:
			chi.update({riga["value"]: riga["label"] for riga in estensione.per_chi()})
	return [
		{"value": nome, "label": etichetta} for nome, etichetta in sorted(chi.items(), key=lambda v: v[1])
	]


def aggiungibili() -> list[R.TipoDocumento]:
	"""The kinds the session adds from the page: switched on, added by hand, and of
	a capability it has."""
	return [
		tipo
		for tipo in tipi_accesi()
		if tipo.da_aggiungere and (not tipo.capacita or livelli.puo(tipo.capacita))
	]


@frappe.whitelist()
def get_choices() -> dict:
	"""What a document can be, and whom it can be for."""
	livelli.verifica("documenti.aggiungi")
	scelte = {
		"types": [
			{"value": tipo.chiave, "label": _(tipo.chiave), "clinical": tipo.clinico}
			for tipo in aggiungibili()
		],
		"practitioners": _per_chi(),
	}
	for estensione in _estensioni:
		if estensione.scelte:
			scelte.update(estensione.scelte())
	return scelte


def _campi(doc, dati: dict) -> None:
	titolo = (dati.get("title") or "").strip()
	if not titolo:
		frappe.throw(_("A document needs a title"))
	tipo = R.tipo(dati.get("document_type"))
	if not tipo or not tipo.da_aggiungere or tipo not in tipi_accesi():
		frappe.throw(_("{0} is not a kind of document").format(dati.get("document_type")))
	if tipo.capacita:
		livelli.verifica(tipo.capacita)
	practitioner = dati.get("practitioner") or None
	if (
		practitioner
		and practitioner != frappe.session.user
		and practitioner not in {riga["value"] for riga in _per_chi()}
	):
		frappe.throw(_("{0} does not provide the centre's services").format(get_fullname(practitioner)))
	doc.update(
		{
			"title": titolo[:140],
			"document_type": tipo.chiave,
			"document_date": getdate(dati.get("document_date")) if dati.get("document_date") else None,
			"source": (dati.get("source") or "").strip() or None,
			"practitioner": practitioner,
			"notes": (dati.get("notes") or "").strip() or None,
		}
	)
	for estensione in _estensioni:
		estensione.scrive(doc, dati)
	# the discipline of whom it is for, once a module had its say on whom: a health
	# professional's makes it health data
	doc.discipline = qualifica_di(doc.practitioner) if doc.practitioner else None


def _contenuto(allegato) -> bytes:
	contenuto = allegato.get_content(encodings=[])
	return contenuto.encode() if isinstance(contenuto, str) else contenuto


def _archivia(lead: str, allegato, dati: dict, appointment: str | None = None) -> dict:
	if appointment:
		frappe.has_permission("CRM Appointment", "read", doc=appointment, throw=True)
	doc = frappe.new_doc(DOCTYPE)
	doc.lead = lead
	_campi(doc, dati)
	doc.update(
		{
			"file": allegato.file_url,
			"file_hash": hashlib.sha256(_contenuto(allegato)).hexdigest(),
			"appointment": appointment,
		}
	)
	doc.flags.allegato = allegato.name
	marca(doc)
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
	notes: str | None = None,
	appointment: str | None = None,
	**altro,
) -> dict:
	"""A file the session uploaded, private and attached to nothing yet, filed among
	the person's documents. ``file`` is the File's name; what a module adds comes
	with the rest (the clinic's "who reads it", "never online")."""
	livelli.verifica("documenti.aggiungi")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	allegato = frappe.get_doc("File", file)
	if allegato.owner != frappe.session.user or allegato.attached_to_doctype or not cint(allegato.is_private):
		frappe.throw(_("Upload the file again: it has to be private, and just uploaded by you"))
	dati = {
		**altro,
		"title": title,
		"document_type": document_type,
		"document_date": document_date,
		"source": source,
		"practitioner": practitioner,
		"notes": notes,
	}
	return _archivia(lead, allegato, dati, appointment)


@frappe.whitelist(methods=["POST"])
def update_document(
	name: str,
	title: str,
	document_type: str,
	document_date: str | None = None,
	source: str | None = None,
	practitioner: str | None = None,
	notes: str | None = None,
	**altro,
) -> dict:
	"""What a document is, when, where it comes from, whom it is for: the file stays."""
	doc = frappe.get_doc(DOCTYPE, name)
	doc.check_permission("write")
	_campi(
		doc,
		{
			**altro,
			"title": title,
			"document_type": document_type,
			"document_date": document_date,
			"source": source,
			"practitioner": practitioner,
			"notes": notes,
		},
	)
	marca(doc)
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


def allegato_privato(doc, method=None) -> None:
	"""A file attached to a person's document is private, or it is not attached.

	Frappe serves a private file only to whoever may read the document it is attached
	to; a public one to anybody with the link. The file is already written when this
	runs, so it is refused rather than quietly relabelled."""
	if doc.attached_to_doctype != DOCTYPE:
		return
	if not (cint(doc.is_private) or (doc.file_url or "").startswith("/private/")):
		frappe.throw(_("A document's file is private"))


# ------------------------------------------------------------------ from a conversation


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


def persona_di(reference_doctype: str | None, reference_name: str | None) -> str | None:
	"""The person a conversation is with: the person, their contact, or their deal."""
	if not (reference_doctype and reference_name):
		return None
	if reference_doctype == "CRM Lead":
		return reference_name if frappe.db.exists("CRM Lead", reference_name) else None
	if reference_doctype == "Contact":
		return frappe.db.get_value("CRM Lead", {"contact": reference_name}, "name")
	if reference_doctype == "CRM Deal":
		return frappe.db.get_value("CRM Deal", reference_name, "lead")
	return None


@frappe.whitelist(methods=["POST"])
def archive_from_message(
	message: str,
	title: str,
	document_type: str,
	document_date: str | None = None,
	source: str | None = None,
	practitioner: str | None = None,
	notes: str | None = None,
	**altro,
) -> dict:
	"""A file received in a conversation, filed among the documents of the person who
	sent it."""
	livelli.verifica("documenti.aggiungi")
	if not frappe.db.exists("DocType", MESSAGGIO):
		frappe.throw(_("There are no conversations on this site"))
	messaggio = frappe.get_doc(MESSAGGIO, message)
	messaggio.check_permission("read")
	lead = persona_di(messaggio.reference_doctype, messaggio.reference_name)
	if not lead:
		frappe.throw(con_nome(_("This conversation is not with a person in {brand}")))
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	originale = _file_del_messaggio(messaggio)
	if not originale or originale.is_remote_file:
		frappe.throw(con_nome(_("This message has no file kept by {brand}")))
	dati = {
		**altro,
		"title": title,
		"document_type": document_type,
		"document_date": document_date,
		"source": source,
		"practitioner": practitioner,
		"notes": notes,
	}
	# checked before the file is copied: a wrong kind leaves nothing behind
	_campi(frappe.new_doc(DOCTYPE), dati)
	# a file received is private first, so the documents' copy shares it, private
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
	return _archivia(lead, copia, dati)
