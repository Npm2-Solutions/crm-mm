# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's messages on the person's board, read in their area.

Not a chat: a board, one per person, and the person does not answer here.
design.md leaves that open ("Da decidere" 7): a chat would be one more inbox.
The desk writes administrative messages (a reminder, a document to bring); a
question the person passed on from the area's chat is on the board too, for the
desk to answer there. The email that follows says only that there is news in the
area: the content stays inside it.

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
from frappe.utils import cint, escape_html, get_fullname, get_url, now_datetime

from crm.area import accesso
from crm.permissions import livelli

MESSAGGIO = "CRM Area Message"
AMMINISTRATIVO = "Administrative"
#: A question the person passed to the centre from the chat: read and answered
#: here by whoever writes to the person.
DOMANDA = "Question"


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
	# the person's questions are read by who opens the board: the person sees it
	for riga in righe:
		if riga["kind"] == DOMANDA and not riga["read_on"]:
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
	from crm.moduli.richieste import nome_del_centro

	indirizzi = sorted({riga.user for riga in accesso.accessi_aperti(lead)})
	if not indirizzi:
		return
	from crm.posta.aspetto import pulsante

	centro = nome_del_centro() or _("your centre")
	try:
		frappe.sendmail(
			recipients=indirizzi,
			subject=_("News in your area at {0}").format(centro),
			header=_("News in your area"),
			with_container=True,
			message="<p>{}</p>{}".format(
				escape_html(_("There is news for you in your area at {0}.").format(centro)),
				pulsante(get_url("/area"), _("Open your area")),
			),
		)
	except frappe.OutgoingEmailError:
		frappe.clear_last_message()
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
		filters={"lead": person, "read_on": ("is", "not set"), "kind": ("!=", DOMANDA)},
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
	"""The centre's messages the person has not opened: their own questions are not news."""
	return cint(
		frappe.db.count(MESSAGGIO, {"lead": person, "read_on": ("is", "not set"), "kind": ("!=", DOMANDA)})
	)
