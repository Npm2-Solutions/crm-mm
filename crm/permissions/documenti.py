# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Who writes what the screens keep for the manager: a capability, not a role.

Every level carries Sales User, and Sales User could write with the API services,
price lists, studio hours, shifts, rooms, pipeline stages, public views, the
WhatsApp templates and settings: things the screens keep for the manager (doc 30,
"Come stanno le cose oggi"). Writing them now asks for the capability the screen
asks for. Reading does not change, and somebody outside the levels - on the Desk
with roles only - keeps the rules of their roles.
"""

from __future__ import annotations

import json

import frappe
from frappe import _

from crm.permissions import condizioni as guidate
from crm.permissions import livelli

#: What writing each document asks for.
SCRITTURA = {
	# the agenda's rules: the manager's
	"CRM Service": "agenda.configura",
	"CRM Service Price": "agenda.configura",
	"CRM Price List": "agenda.configura",
	"CRM Scheduling Settings": "agenda.configura",
	"CRM Waiting List Settings": "agenda.configura",
	"CRM Subscription Type": "agenda.configura",
	"CRM Holiday List": "agenda.configura",
	# shifts, holidays and rooms: the front desk's too; a practitioner their own shifts
	"CRM Staff Schedule": "agenda.turni",
	"CRM Resource": "agenda.turni",
	"CRM Booking Calendar": "prenotazione_online.configura",
	# the pipeline
	"CRM Lead Status": "pipeline.configura",
	"CRM Deal Status": "pipeline.configura",
	"CRM Communication Status": "pipeline.configura",
	# which pipelines new clients and quotes move
	"CRM Client Settings": "pipeline.configura",
	"CRM Quote Settings": "pipeline.configura",
	# public views: everybody keeps their own
	"CRM View Settings": "viste.configura",
	# the channels: everybody uses the templates, the manager writes them
	"WhatsApp Templates": "modelli_messaggio.gestisci",
	"WhatsApp Settings": "canali.configura",
	# the phone: everybody their own line, the manager the others' and the caller IDs
	"CRM Telephony Agent": "telefono.configura",
	"CRM Caller ID": "telefono.configura",
	# the sales hierarchy: the Manager builds it (it was System Manager's)
	"CRM Sales Hierarchy": "gerarchia.gestisci",
	"CRM Service Level Agreement": "assegnazione.regole",
	# the agency's, the whole page (PR 3): the Manager no longer writes it
	"ERPNext CRM Settings": "tecnico.erpnext",
	# core documents the Manager's pages write (PR 3b): see DEL_CORE
	"Email Template": "modelli_messaggio.gestisci",
	"Assignment Rule": "assegnazione.regole",
	"Data Import": "persone.importa",
}

#: Core documents Frappe gives to System Manager only, which the Manager's pages
#: write, and the role that carries their rule: `SCRITTURA` narrows it to the
#: capability. Email Template is read by everybody already; the others are the
#: Manager's to read too. Email accounts go through `crm.api.settings` instead:
#: their servers and ports stay the agency's.
DEL_CORE = {
	"Email Template": "Sales User",
	"Assignment Rule": "Sales Manager",
	"Data Import": "Sales Manager",
}

#: The documents that belong to one user, and the field that says whose: one's own
#: needs no more than the level that shows the page.
DI_CHI = {
	"CRM Staff Schedule": "user",
	"CRM Telephony Agent": "user",
	"CRM View Settings": "user",
}

_LEGGE = ("read", "select", "print", "export", "report", "email", "share")


def puo_scrivere(doc, user: str) -> bool:
	"""Whether ``user`` may create, change or delete ``doc``, as the screens say."""
	capacita = SCRITTURA[doc.doctype]
	proprietario = DI_CHI.get(doc.doctype)
	propria = bool(proprietario and doc.get(proprietario) == user)

	if doc.doctype == "CRM View Settings":
		# one's own views, private or standard; a public one is everybody's
		return (propria and not doc.get("public")) or livelli.puo(capacita, user)
	if doc.doctype == "CRM Telephony Agent":
		return propria or livelli.puo(capacita, user)

	ambito = livelli.ambito(capacita, user)
	if ambito == livelli.SUOI:
		# a practitioner changes their own shifts and holidays, nobody else's
		return propria
	return ambito is not None


def has_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	if (ptype or "read") in _LEGGE:
		return True
	if not livelli.nel_crm(user):
		return True
	return puo_scrivere(doc, user)


# ---------------------------------------------------------------- assigning

#: Assigning a person or a deal hands it to somebody: it decides who sees it.
_ASSEGNABILI = ("CRM Lead", "CRM Deal")


def verifica_assegnazione(doctype: str | None) -> None:
	"""Assigning asks `persone.assegna` (doc 30), which Read only never has.

	Frappe lets whoever reads a document assign it. The assignment rules call its
	functions directly, so only what a person does from the screen or the API comes
	through here.
	"""
	if doctype in _ASSEGNABILI and livelli.nel_crm() and not livelli.puo("persone.assegna"):
		frappe.throw(_("Your level does not assign people"), frappe.PermissionError)


@frappe.whitelist()
def assegna(args: dict | None = None):
	from frappe.desk.form import assign_to

	args = args or frappe.local.form_dict
	verifica_assegnazione(args.get("doctype"))
	return assign_to.add(args)


@frappe.whitelist()
def assegna_a_molti(args: dict | None = None):
	from frappe.desk.form import assign_to

	args = args or frappe.local.form_dict
	verifica_assegnazione(args.get("doctype"))
	return assign_to.add_multiple(args)


@frappe.whitelist()
def togli_assegnazione(doctype: str, name: str | int, assign_to: str):
	from frappe.desk.form import assign_to as assegnazioni

	verifica_assegnazione(doctype)
	return assegnazioni.remove(doctype, name, assign_to)


@frappe.whitelist()
def togli_assegnazioni(doctype: str, names: str):
	from frappe.desk.form import assign_to

	verifica_assegnazione(doctype)
	return assign_to.remove_multiple(doctype, names)


# ---------------------------------------------------------------- read only

#: What someone with Read only may still change: what is theirs alone, and changes
#: nothing of the centre's.
_PROPRI = {"CRM Notification": "for_user", "User": "name", "CRM View Settings": "user"}
#: Reading, printing, exporting. Sharing hands the document to somebody else, and
#: emailing from it sends in the centre's name: both are writes.
_LEGGE_SOLTANTO = ("read", "select", "print", "export", "report")


def sola_lettura(doc, ptype: str | None = None, user: str | None = None) -> bool:
	"""`has_permission` for every document: Read only takes every write away (doc 30).

	Its capabilities never write, but the roles of the level it is added to could,
	with the API: here nothing is created, changed or deleted, but one's own
	notifications and profile.
	"""
	if (ptype or "read") in _LEGGE_SOLTANTO:
		return True
	user = user or frappe.session.user
	if not _in_sola_lettura(user):
		return True
	proprietario = _PROPRI.get(doc.doctype)
	return bool(proprietario and doc.get(proprietario) == user)


def sola_lettura_al_salvataggio(doc, method=None):
	"""`validate` of every document: Read only asks again when a save is on the user's
	behalf. What is shared with somebody is granted without the `has_permission`
	hooks, and the CRM shares every person and deal with its owner, for writing."""
	if doc.flags.ignore_permissions:
		return
	if not sola_lettura(doc, "write"):
		frappe.throw(_("Your level only reads"), frappe.PermissionError)


def _in_sola_lettura(user: str) -> bool:
	cache = getattr(frappe.local, "crm_sola_lettura", None)
	if cache is None:
		cache = frappe.local.crm_sola_lettura = {}
	if user not in cache:
		cache[user] = not livelli.e_agenzia(user) and livelli.SOLA_LETTURA_LIVELLO in livelli.livelli_di(user)
	return cache[user]


def concedi_documenti_del_core() -> None:
	"""Give `DEL_CORE`'s roles their rule on the core documents, once.

	A rule already there, the CRM's or one changed by hand, is left as it is.
	"""
	from frappe.permissions import add_permission, update_permission_property

	for doctype, ruolo in DEL_CORE.items():
		if not frappe.db.exists("DocType", doctype):
			continue
		if frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": ruolo, "permlevel": 0}):
			continue
		add_permission(doctype, ruolo, 0, "read")
		for ptype in ("write", "create", "delete"):
			update_permission_property(doctype, ruolo, 0, ptype, 1, validate=False)
		frappe.clear_cache(doctype=doctype)


# ------------------------------------------------------------ guided conditions

#: The documents that run a condition: the field naming the doctype it is about,
#: how the condition reaches that document, each Python condition with the guided
#: one the screen builds it from, and those only the agency writes.
CONDIZIONI = {
	"Assignment Rule": {
		"di": "document_type",
		"prefisso": None,
		"guidate": {
			"assign_condition": "assign_condition_json",
			"unassign_condition": "unassign_condition_json",
		},
		"solo_python": ("close_condition",),
		"documenti": ("CRM Lead", "CRM Deal"),
	},
	"CRM Service Level Agreement": {
		"di": "apply_on",
		"prefisso": "doc",
		"guidate": {"condition": "condition_json"},
		"solo_python": (),
		"documenti": None,
	},
}


def _cambiato(doc, campo: str) -> bool:
	"""Changed by this save; for a new document, given at all. (Frappe's
	`has_value_changed` answers True for every field of a new document.)"""
	if doc.get_doc_before_save() is None:
		return bool(doc.get(campo))
	return doc.has_value_changed(campo)


def scrivi_condizioni(doc, method=None) -> None:
	"""`before_validate`: conditions written in Python are the agency's (doc 30).

	For anybody else the server writes each condition from the guided one the
	screen built, before anything evaluates it: whatever Python came with the
	request is not kept. A condition the agency wrote from the Desk, with no guided
	one, stays as it is; changing it is the agency's.
	"""
	user = frappe.session.user
	if not livelli.nel_crm(user) or livelli.puo("tecnico.codice", user):
		return
	regole = CONDIZIONI[doc.doctype]
	solo_agenzia = _("Conditions written in Python are set by the agency.")

	riferimento = doc.get(regole["di"])
	if regole["documenti"] and riferimento not in regole["documenti"]:
		frappe.throw(_("Rules here are for people and deals."), frappe.PermissionError)
	for campo in regole["solo_python"]:
		if _cambiato(doc, campo):
			frappe.throw(solo_agenzia, frappe.PermissionError)

	campi = frappe.get_meta(riferimento).get_valid_columns() if riferimento else []
	for python, guidata in regole["guidate"].items():
		if not (_cambiato(doc, python) or _cambiato(doc, guidata)):
			continue
		try:
			condizioni = json.loads(doc.get(guidata) or "[]")
			scritta = guidate.in_python(condizioni, campi, regole["prefisso"])
		except (ValueError, guidate.CondizioneNonValida) as errore:
			frappe.throw(_("This condition cannot be saved: {0}").format(errore))
		if not scritta and doc.get(python):
			# Python with no guided condition behind it: the agency's, from the Desk
			frappe.throw(solo_agenzia, frappe.PermissionError)
		doc.set(python, scritta)
