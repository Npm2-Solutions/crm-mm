# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The person's board: the centre's messages read in their area, and what the
person writes back.

One board per person, both ways, on the person's Client area tab - not one more
inbox. The desk writes administrative messages (a reminder, a document to bring)
and answers there; the email that follows says only that there is news in the
area: the content stays inside it. The person writes from the Messages of their
area (`send_message`): words and maybe a photo or a PDF (`messaggi_regole`), kept
private with the message, read by whoever reads the board; a question passed on
from the area's chat is theirs too. Whoever follows the person hears of it
(`avvisa`) by the person's name only: the words stay on the board, which may say
something about their health. Never from the centre's preview.

**Other kinds come from other modules** (`registra_tipo`), each with who writes
it and who reads it in DottorCloud: the clinic's "Care", written by a practitioner
and read like a visit. A message goes out as the kind of the highest priority its
author writes.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import cint, get_fullname, now_datetime

from crm.area import accesso
from crm.area import messaggi_regole as R
from crm.permissions import livelli

MESSAGGIO = "CRM Area Message"
AMMINISTRATIVO = "Administrative"
#: A question the person passed to the centre from the chat: read and answered
#: here by whoever writes to the person.
DOMANDA = "Question"
#: What the person wrote from the Messages of their area.
DALLA_PERSONA = "From the person"
#: The kinds that come from the person: read by whoever opens the board, never
#: news for the person.
DELLA_PERSONA = (DOMANDA, DALLA_PERSONA)


@dataclass(frozen=True)
class TipoMessaggio:
	chiave: str
	#: Whether this user writes messages of this kind; None: nobody writes it from
	#: DottorCloud (a question comes from the area's chat).
	scrive: Callable[[str], bool] | None
	#: Whether this user, not its author, reads a message of this kind.
	legge: Callable[[object, str], bool]
	#: What a new message of this kind also carries (the clinic: whose care it is).
	campi: Callable[[str], dict] | None = None
	#: Of the kinds a user writes, the highest goes out.
	priorita: int = 0


_tipi: dict[str, TipoMessaggio] = {}


def registra_tipo(tipo: TipoMessaggio) -> None:
	_tipi[tipo.chiave] = tipo


def _scrive_al_board(user: str) -> bool:
	return livelli.puo("area.messaggi", user)


def _legge_il_board(doc, user: str) -> bool:
	return livelli.puo("area.messaggi", user)


def registra() -> None:
	registra_tipo(TipoMessaggio(AMMINISTRATIVO, scrive=_scrive_al_board, legge=_legge_il_board))
	registra_tipo(TipoMessaggio(DOMANDA, scrive=None, legge=_legge_il_board))
	registra_tipo(TipoMessaggio(DALLA_PERSONA, scrive=None, legge=_legge_il_board))


def tipo_di(user: str | None = None) -> TipoMessaggio:
	"""The kind a message of this user goes out as."""
	livelli.carica()
	user = user or frappe.session.user
	scritti = [tipo for tipo in _tipi.values() if tipo.scrive and tipo.scrive(user)]
	if not scritti:
		return _tipi[AMMINISTRATIVO]
	return max(scritti, key=lambda tipo: tipo.priorita)


def _legge(doc, user: str) -> bool:
	"""In DottorCloud: its author; the others as its kind says."""
	if doc.get("author") == user:
		return True
	livelli.carica()
	tipo = _tipi.get(doc.get("kind"))
	return bool(tipo and tipo.legge(doc, user))


def _riga(doc, nell_area: bool = False) -> dict:
	riga = {
		"name": doc.name,
		"kind": doc.kind,
		"body": doc.body,
		"author_name": get_fullname(doc.author),
		"posted_on": doc.posted_on,
		"read_on": doc.read_on,
		# the person's own, from the area, and the file they attached
		"from_person": doc.kind in DELLA_PERSONA,
		"attachment_name": doc.attachment_name if doc.attachment else None,
	}
	if not nell_area:
		riga["mine"] = doc.author == frappe.session.user
	return riga


@frappe.whitelist()
def get_messages(lead: str) -> dict:
	"""The person's board, as the session may read it."""
	livelli.verifica("area.messaggi")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	utente = frappe.session.user
	righe = [
		_riga(doc)
		for doc in (
			frappe.get_doc(MESSAGGIO, nome)
			for nome in frappe.get_all(
				MESSAGGIO, filters={"lead": lead}, pluck="name", order_by="posted_on desc", limit=100
			)
		)
		if _legge(doc, utente)
	]
	# what the person wrote is read by who opens the board: the person sees it
	for riga in righe:
		if riga["kind"] in DELLA_PERSONA and not riga["read_on"]:
			riga["read_on"] = now_datetime()
			frappe.db.set_value(
				MESSAGGIO,
				riga["name"],
				{"read_on": riga["read_on"], "read_by": utente},
				update_modified=False,
			)
	return {
		"messages": righe,
		# the kind the session writes: the desk administration, the clinic's
		# practitioner the care
		"kind": tipo_di(utente).chiave,
		"has_area": bool(accesso.accessi_aperti(lead)),
	}


@frappe.whitelist(methods=["POST"])
def post_message(lead: str, body: str) -> dict:
	"""A message on the board; who enters the area gets an email that says only
	that there is news."""
	livelli.verifica("area.messaggi")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	testo = (body or "").strip()
	if not testo:
		frappe.throw(_("Write the message"))
	tipo = tipo_di()
	doc = frappe.get_doc(
		{
			"doctype": MESSAGGIO,
			"lead": lead,
			"kind": tipo.chiave,
			"author": frappe.session.user,
			"posted_on": now_datetime(),
			"body": testo[:4000],
			**(tipo.campi(frappe.session.user) if tipo.campi else {}),
		}
	)
	doc.insert(ignore_permissions=True)
	_avvisa(lead)
	return get_messages(lead)


def _avvisa(lead: str) -> None:
	from crm.area import collegamento

	# each who enters the area gets the email with a link of their own
	for utente in sorted({riga.user for riga in accesso.accessi_aperti(lead)}):
		collegamento.manda(utente, lead, "message", "messages")
	# WhatsApp or SMS to who asked for them, with the same words
	from crm.area import avvisi

	avvisi.avvisa_fuori(lead)


# ------------------------------------------------------------------ the person's side


@frappe.whitelist()
def area_messages(person: str) -> dict:
	"""The board, in the area: every message to the person. In the centre's
	preview, a message whoever previews does not read keeps its place, with
	nothing of it: the clinic's care is read as the clinic says."""
	from crm.area import anteprima
	from crm.area.api import _mia

	_mia(person, anche_in_anteprima=True)
	vista = anteprima.in_anteprima()
	righe = []
	for nome in frappe.get_all(
		MESSAGGIO, filters={"lead": person}, pluck="name", order_by="posted_on desc", limit=100
	):
		doc = frappe.get_doc(MESSAGGIO, nome)
		if vista and not _legge(doc, vista.user):
			righe.append(anteprima.coperta(doc))
			continue
		righe.append(_riga(doc, nell_area=True))
	return {"messages": righe}


@frappe.whitelist(methods=["POST"])
def mark_read(person: str) -> dict:
	"""Opened in the area: what was new is read, by whom and when."""
	from crm.area.api import _mia

	_mia(person)
	for nome in frappe.get_all(
		MESSAGGIO,
		filters={"lead": person, "read_on": ("is", "not set"), "kind": ("not in", DELLA_PERSONA)},
		pluck="name",
	):
		frappe.db.set_value(
			MESSAGGIO,
			nome,
			{"read_on": now_datetime(), "read_by": frappe.session.user},
			update_modified=False,
		)
	return {"unread": 0}


def da_leggere(person: str) -> int:
	"""The centre's messages the person has not opened: what they wrote is not news."""
	return cint(
		frappe.db.count(
			MESSAGGIO, {"lead": person, "read_on": ("is", "not set"), "kind": ("not in", DELLA_PERSONA)}
		)
	)


# ------------------------------------------------------------------ the person writes


def _problemi(problemi: list) -> None:
	if problemi:
		frappe.throw("<br>".join(p.testo(_) for p in problemi))


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=20, seconds=60 * 60)
def send_message(
	person: str, body: str | None = None, attachment: str | None = None, attachment_name: str | None = None
) -> dict:
	"""The person writes to the centre from their area: words, and maybe one photo
	or PDF, private with the message. Whoever follows them hears of it by name."""
	from crm.area.api import _mia

	_mia(person)
	testo = (body or "").strip()
	contenuto = R.dal_data_url(attachment)
	_problemi(R.problemi(testo, contenuto, c_era_un_file=bool(attachment)))
	frappe.db.savepoint("messaggio_dell_area")
	doc = frappe.get_doc(
		{
			"doctype": MESSAGGIO,
			"lead": person,
			"kind": DALLA_PERSONA,
			"author": frappe.session.user,
			"posted_on": now_datetime(),
			"body": testo,
		}
	).insert(ignore_permissions=True)
	if contenuto:
		nome = R.nome_del_file(attachment_name, R.tipo_del_file(contenuto))
		try:
			allegato = frappe.get_doc(
				{
					"doctype": "File",
					"file_name": nome,
					"attached_to_doctype": MESSAGGIO,
					"attached_to_name": doc.name,
					"attached_to_field": "attachment",
					"is_private": 1,
					"content": contenuto,
				}
			).insert(ignore_permissions=True)
		except Exception:
			# a PDF the framework cannot read (broken, or with scripts in it): the
			# message goes with it, and the person is told
			frappe.db.rollback(save_point="messaggio_dell_area")
			frappe.clear_last_message()
			frappe.throw(_("The file could not be read: attach it again"))
		doc.db_set({"attachment": allegato.file_url, "attachment_name": nome}, update_modified=False)
	_avvisa_chi_segue(person, doc.name)
	return area_messages(person)


def chi_sente(lead: str) -> list[str]:
	"""Who hears of what the person wrote: whoever follows them and reads the
	board; nobody does, the desk (`chat.chi_avvisare`). Only who may open them."""
	from crm.area import chat
	from crm.notifiche.avvisi import chi_segue

	def legge(utente: str) -> bool:
		return livelli.puo("area.messaggi", utente) and bool(
			frappe.has_permission("CRM Lead", "read", doc=lead, user=utente)
		)

	seguono = [utente for utente in chi_segue("CRM Lead", lead, banco=False) if legge(utente)]
	return seguono or [utente for utente in chat.chi_avvisare() if legge(utente)]


def _avvisa_chi_segue(lead: str, messaggio: str) -> None:
	from crm.notifiche import regole as N
	from crm.notifiche.avvisi import avvisa

	nome = frappe.db.get_value("CRM Lead", lead, "lead_name") or lead
	for utente in chi_sente(lead):
		# the words stay on the board: the notification says only who wrote
		avvisa(
			utente,
			"Area",
			N.MESSAGGIO_AREA,
			[nome],
			riguarda=("CRM Lead", lead),
			oggetto=(MESSAGGIO, messaggio),
			frase_molti=N.MESSAGGIO_AREA_MOLTI,
		)


@frappe.whitelist(methods=["GET"])
def attachment(message: str) -> None:
	"""The file the person attached, for whoever reads the board in DottorCloud."""
	livelli.verifica("area.messaggi")
	doc = frappe.get_doc(MESSAGGIO, message)
	frappe.has_permission("CRM Lead", "read", doc=doc.lead, throw=True)
	if not _legge(doc, frappe.session.user) or not doc.attachment:
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	nome = frappe.db.get_value("File", {"file_url": doc.attachment}, "name")
	if not nome:
		frappe.throw(_("The file is no longer there"))
	frappe.local.response.filename = doc.attachment_name or doc.attachment.rsplit("/", 1)[-1]
	frappe.local.response.filecontent = frappe.get_doc("File", nome).get_content(encodings=[])
	frappe.local.response.type = "download"
