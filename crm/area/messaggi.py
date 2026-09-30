# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's messages on the person's board, read in their area.

Not a chat: a board, one per person, and the patient does not answer here.
design.md leaves that open ("Da decidere" 7): a chat would be one more inbox
for the doctors. The desk writes administrative messages (a reminder, a
document to bring); a practitioner writes about the care, and those are read in
the CRM like a visit (`crm.clinica.dossier`). The email that follows says only
that there is news in the area: the content stays inside it.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, get_fullname, get_url, now_datetime

from crm.clinica.area import accesso
from crm.permissions import livelli

MESSAGGIO = "Clinic Message"
AMMINISTRATIVO, CURA = "Administrative", "Care"
#: A question the patient passed to the centre from the chat: read and answered
#: here by whoever writes to the person.
DOMANDA = "Question"


def _legge(doc, user: str) -> bool:
	"""In the CRM: its author; an administrative one whoever writes to the
	person; one about the care by the dossier's rules."""
	if doc.get("author") == user:
		return True
	if doc.get("kind") in (AMMINISTRATIVO, DOMANDA):
		return livelli.puo("area.messaggi", user)
	from crm.clinica import dossier

	return dossier.legge_le_altre(doc, user)


def _riga(doc, per_il_paziente: bool = False) -> dict:
	riga = {
		"name": doc.name,
		"kind": doc.kind,
		"body": doc.body,
		"author_name": get_fullname(doc.author),
		"posted_on": doc.posted_on,
		"read_on": doc.read_on,
	}
	if not per_il_paziente:
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
	# the patient's questions are read by who opens the board: the patient sees it
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
		# a practitioner writes about the care; the desk, administration
		"kind": CURA if livelli.puo("clinica.scrivi") else AMMINISTRATIVO,
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
	cura = livelli.puo("clinica.scrivi")
	doc = frappe.get_doc(
		{
			"doctype": MESSAGGIO,
			"lead": lead,
			"kind": CURA if cura else AMMINISTRATIVO,
			"author": frappe.session.user,
			"posted_on": now_datetime(),
			"body": testo[:4000],
			# read in the CRM like a visit of its author
			"practitioner": frappe.session.user if cura else None,
			"visibility": "Care team",
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
	centro = nome_del_centro() or _("your centre")
	try:
		frappe.sendmail(
			recipients=indirizzi,
			subject=_("News in your area at {0}").format(centro),
			message=_(
				'<p>There is news for you in your area.</p><p><a href="{0}">Open it here</a>.</p>'
			).format(get_url("/area")),
		)
	except frappe.OutgoingEmailError:
		frappe.clear_last_message()
	# WhatsApp or SMS to who asked for them, with the same words
	from crm.clinica.area import avvisi

	avvisi.avvisa_fuori(lead)


# ------------------------------------------------------------------ the patient's side


@frappe.whitelist()
def area_messages(person: str) -> dict:
	"""The board, in the area: every message to the person."""
	from crm.clinica.area.api import _mia

	_mia(person)
	return {
		"messages": [
			_riga(frappe.get_doc(MESSAGGIO, nome), per_il_paziente=True)
			for nome in frappe.get_all(
				MESSAGGIO, filters={"lead": person}, pluck="name", order_by="posted_on desc", limit=100
			)
		]
	}


@frappe.whitelist(methods=["POST"])
def mark_read(person: str) -> dict:
	"""Opened in the area: what was new is read, by whom and when."""
	from crm.clinica.area.api import _mia

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
