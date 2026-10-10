# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The panel's calls: a page of one's notifications as the panel draws them, and
reading them.

A row says what it is (`kind`), who it comes from (nobody when it is DottorCloud
itself), its sentence in the reader's language with the names in bold, the first
words of the message it is about where the reader may read them, how many messages
it gathers, and where it opens: the route is decided here, from what the
notification is about, so the phone and the computer open the same place and a
person deleted since opens nothing.

Read, all read, unread again: one query, and one signal for the reader's other
tabs. Only one's own: every call filters on the session's user.
"""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import cint

from crm.notifiche import regole as R
from crm.notifiche.avvisi import NOTIFICA, SISTEMA

PER_PAGINA = 30
#: The most a page asks for, however far one scrolls.
AL_PIU = 300

CAMPI = [
	"name",
	"type",
	"from_user",
	"read",
	"creation",
	"sentence",
	"sentence_args",
	"count",
	"notification_text",
	"message",
	"reference_doctype",
	"reference_name",
	"notification_type_doctype",
	"notification_type_doc",
]

#: The kinds whose message the panel shows the first words of.
CON_ANTEPRIMA = frozenset({"mention", "whatsapp", "sms", "email", "invoicing"})
#: The kinds that are a person's message on a channel: read by who reads conversations.
MESSAGGI = ("whatsapp", "sms", "email")
#: The record pages a notification opens, and the name of their parameter.
PAGINE = {"CRM Lead": ("Lead", "leadId"), "CRM Deal": ("Deal", "dealId")}
#: The kinds that open a page of the settings instead: the page, and the step of it
#: (the carrier's page, `_del_telefono`).
IMPOSTAZIONI = {"phone": {"page": "Telephony", "step": "twilio-settings"}}
#: What a notification is about, when it opens another step of that page.
IMPOSTAZIONI_DI = {"CRM Caller ID": {"page": "Telephony", "step": "caller-id-settings"}}


@frappe.whitelist()
def get_notifications(limit: int = PER_PAGINA, unread: int = 0) -> dict:
	"""The newest of the session's notifications - only the unread ones with
	`unread` - with how many are unread and whether there are more."""
	utente = frappe.session.user
	quante = min(max(cint(limit) or PER_PAGINA, 1), AL_PIU)
	filtri = {"to_user": utente}
	if cint(unread):
		filtri["read"] = 0
	righe = frappe.get_all(NOTIFICA, filters=filtri, fields=CAMPI, order_by="creation desc", limit=quante + 1)
	return {
		"rows": righe_del_pannello(righe[:quante], utente),
		"unread": da_leggere(utente),
		"more": len(righe) > quante,
	}


def da_leggere(utente: str) -> int:
	return frappe.db.count(NOTIFICA, {"to_user": utente, "read": 0})


def righe_del_pannello(righe: list, utente: str) -> list[dict]:
	"""The rows as the panel draws them: the names, the routes and what is still
	there asked once for the whole page."""
	mittenti = _mittenti({r.from_user for r in righe if r.from_user and r.from_user not in SISTEMA})
	esistenti = _esistenti(righe)
	compiti_aperti = _compiti_aperti(righe, utente)
	conversazioni = _legge_le_conversazioni(utente)
	chiamate = _legge_le_chiamate(utente)
	pannello = []
	for riga in righe:
		genere = R.genere(riga.type, riga.notification_type_doctype, riga.sentence)
		pannello.append(
			{
				"name": riga.name,
				"kind": genere,
				"text": testo(riga),
				"excerpt": _anteprima(riga, genere, conversazioni),
				"from": mittenti.get(riga.from_user),
				"read": bool(riga.read),
				"count": cint(riga.count) or 1,
				"creation": riga.creation,
				"route": percorso(riga, genere, esistenti, compiti_aperti, chiamate),
				"settings": IMPOSTAZIONI.get(genere)
				and IMPOSTAZIONI_DI.get(riga.notification_type_doctype, _del_telefono(riga, genere)),
			}
		)
	return pannello


def _del_telefono(riga, genere: str) -> dict:
	"""The carrier's page a notification about the phone opens (doc 64): Telnyx's
	for a sentence about Telnyx or a number asked of it, Twilio's for Twilio's,
	else the centre's carrier's."""
	from crm.telephony import operatore

	impostazioni = IMPOSTAZIONI[genere]
	if genere != "phone":
		return impostazioni
	if riga.sentence in R.DI_TELNYX:
		via = operatore.TELNYX
	elif riga.notification_type_doctype == "CRM Phone Number Request" and riga.notification_type_doc:
		via = (
			frappe.db.get_value("CRM Phone Number Request", riga.notification_type_doc, "provider")
			or operatore.TWILIO
		)
	elif riga.sentence in (R.SPESA_TWILIO, R.NUMERO_APPROVATO, R.NUMERO_RIFIUTATO):
		via = operatore.TWILIO
	else:
		via = operatore.attivo() or operatore.TWILIO
	return {**impostazioni, "step": operatore.pagina(via)}


def testo(riga) -> str:
	"""The sentence in the reader's language, the names in bold; the words of one
	written before the sentences were kept apart, the same way."""
	if riga.sentence:
		try:
			nomi = json.loads(riga.sentence_args or "[]")
		except ValueError:
			nomi = []
		return R.frase(_(riga.sentence), nomi if isinstance(nomi, list) else [], riga.sentence)
	return R.testo_vecchio(riga.notification_text)


def _anteprima(riga, genere: str, conversazioni: bool) -> str:
	if genere not in CON_ANTEPRIMA:
		return ""
	# a message of a channel is read by who reads the conversations
	if genere in MESSAGGI and not conversazioni:
		return ""
	return R.anteprima(riga.message)


def percorso(riga, genere: str, esistenti: dict, compiti_aperti: set, chiamate: bool = False) -> dict | None:
	"""Where the notification opens: the desk's day, the invoices, the person or
	deal it is about, on the tab or the message it names, a task with nobody behind
	it in the tasks, a call nobody knows the caller of in the register. Nothing when
	what it opened is no longer there."""
	if genere == "agenda":
		# a reminder answered: the agenda, on the appointment
		if riga.sentence in R.PROMEMORIA and riga.notification_type_doc:
			return {"name": "Calendar", "query": {"appointment": riga.notification_type_doc}}
		return {"name": "Today"}
	if genere == "invoicing":
		# a supplier's invoice opens on itself, in the «Received» tab
		if riga.notification_type_doctype == "CRM Supplier Invoice" and riga.notification_type_doc:
			return {"name": "Invoices", "query": {"ricevuta": riga.notification_type_doc}}
		# one of the centre's invoices (paid online, or stayed a draft): open on it
		if riga.notification_type_doctype == "CRM Invoice" and riga.notification_type_doc:
			return {"name": "Invoices", "query": {"open": riga.notification_type_doc}}
		return {"name": "Invoices"}
	pagina = PAGINE.get(riga.reference_doctype)
	if not pagina and genere == "task" and riga.notification_type_doc in compiti_aperti:
		# a task given with nobody behind it: the tasks, on it, while it is the reader's
		return {"name": "Tasks", "query": {"open": riga.notification_type_doc}}
	if (
		not pagina
		and genere == "call"
		and chiamate
		and riga.notification_type_doctype == "CRM Call Log"
		and riga.notification_type_doc
	):
		# a message left by a number nobody knows: the call itself, with its recording
		return {"name": "Call Logs", "query": {"open": riga.notification_type_doc}}
	if not pagina or riga.reference_name not in esistenti.get(riga.reference_doctype, ()):
		return None
	nome_pagina, parametro = pagina
	segno = ""
	if genere in ("mention", *MESSAGGI) and riga.notification_type_doc:
		# the comment or the message itself, in the person's history
		segno = "#" + riga.notification_type_doc
	elif genere in MESSAGGI:
		# a message opens the chat, the person's other door: their summary is
		# where a page opens that says nothing (docs/crm/54)
		segno = "#activity"
	elif genere == "area" and riga.notification_type_doctype == "CRM Quote":
		# a quote answered in the area: the person's quotes
		segno = "#quotes"
	elif genere == "area":
		segno = "#area"
	elif genere == "call":
		# the message is a call of the person's: their activity has it
		segno = "#activity"
	elif genere == "task" and riga.notification_type_doc in compiti_aperti:
		segno = "#tasks"
	return {"name": nome_pagina, "params": {parametro: riga.reference_name}, "hash": segno}


def _mittenti(utenti: set) -> dict:
	if not utenti:
		return {}
	return {
		u.name: {"name": u.name, "full_name": u.full_name or u.name, "image": u.user_image}
		for u in frappe.get_all(
			"User", filters={"name": ("in", list(utenti))}, fields=["name", "full_name", "user_image"]
		)
	}


def _esistenti(righe: list) -> dict[str, set]:
	"""The people and deals the page names that are still there."""
	per_tipo: dict[str, set] = {}
	for riga in righe:
		if riga.reference_doctype in PAGINE and riga.reference_name:
			per_tipo.setdefault(riga.reference_doctype, set()).add(riga.reference_name)
	return {
		doctype: set(frappe.get_all(doctype, filters={"name": ("in", list(nomi))}, pluck="name"))
		for doctype, nomi in per_tipo.items()
	}


def _compiti_aperti(righe: list, utente: str) -> set:
	"""The tasks of the page still assigned to the reader: their notification opens
	the person's tasks."""
	compiti = [
		r.notification_type_doc
		for r in righe
		if r.notification_type_doctype == "CRM Task" and r.notification_type_doc
	]
	if not compiti:
		return set()
	return set(
		frappe.get_all(
			"ToDo",
			filters={
				"reference_type": "CRM Task",
				"reference_name": ("in", compiti),
				"allocated_to": utente,
				"status": ("!=", "Cancelled"),
			},
			pluck="reference_name",
		)
	)


def _legge_le_chiamate(utente: str) -> bool:
	"""Whether the reader opens the register of calls: a message left by a number
	nobody knows opens there."""
	from crm.permissions.livelli import nel_crm, puo

	return not nel_crm(utente) or puo("telefono.registro", utente)


def _legge_le_conversazioni(utente: str | None = None) -> bool:
	"""Whether whoever reads - the session, or the person an email goes to - reads
	the conversations: the first words of a message are theirs only then."""
	from crm.permissions.livelli import nel_crm, puo

	return not nel_crm(utente) or puo("conversazioni.vedi", utente)


# ------------------------------------------------------------------ reading them


@frappe.whitelist(methods=["POST"])
def mark_as_read(names: list | str | None = None) -> dict:
	"""These notifications read - all of them without names."""
	return _segna(names, letta=1)


@frappe.whitelist(methods=["POST"])
def mark_as_unread(names: list | str | None = None) -> dict:
	"""These notifications to read again."""
	if not names:
		frappe.throw(_("Choose the notification to read again"))
	return _segna(names, letta=0)


def _segna(names, letta: int) -> dict:
	"""Read or unread: these names, or all of one's own without names. An empty list
	is no notification, never all of them."""
	utente = frappe.session.user
	nomi = frappe.parse_json(names) if isinstance(names, str) and names.startswith("[") else names
	if isinstance(nomi, str):
		nomi = [nomi] if nomi else None
	filtri = {"to_user": utente, "read": 1 - letta}
	if nomi is not None:
		if not nomi:
			return {"unread": da_leggere(utente)}
		filtri["name"] = ("in", [str(n) for n in nomi])
	# read, it no longer goes by email
	cambi = {"read": letta, "email_due": 0} if letta else {"read": letta}
	frappe.db.set_value(NOTIFICA, filtri, cambi, update_modified=False)
	frappe.publish_realtime("crm_notification", {"event": "read"}, user=utente, after_commit=True)
	return {"unread": da_leggere(utente)}


def segna_lette_di(utente: str, documento: str) -> None:
	"""The notifications about a comment or a message read, once it is open: what
	the CRM's pages asked before (`crm.api.notifications.mark_as_read`)."""
	nomi = frappe.get_all(
		NOTIFICA,
		filters={"to_user": utente, "read": 0},
		or_filters={"comment": documento, "notification_type_doc": documento},
		pluck="name",
	)
	if nomi:
		_segna(nomi, letta=1)
