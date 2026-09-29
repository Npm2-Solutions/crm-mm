# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
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

import frappe

from crm.permissions import livelli

#: What writing each document asks for.
SCRITTURA = {
	# the agenda's rules: the manager's
	"CRM Service": "agenda.configura",
	"CRM Service Price": "agenda.configura",
	"CRM Price List": "agenda.configura",
	"CRM Scheduling Settings": "agenda.configura",
	"CRM Holiday List": "agenda.configura",
	# shifts, holidays and rooms: the front desk's too; a practitioner their own shifts
	"CRM Staff Schedule": "agenda.turni",
	"CRM Resource": "agenda.turni",
	"CRM Booking Calendar": "prenotazione_online.configura",
	# the pipeline
	"CRM Lead Status": "pipeline.configura",
	"CRM Deal Status": "pipeline.configura",
	"CRM Communication Status": "pipeline.configura",
	# public views: everybody keeps their own
	"CRM View Settings": "viste.configura",
	# the channels: everybody uses the templates, the manager writes them
	"WhatsApp Templates": "modelli_messaggio.gestisci",
	"WhatsApp Settings": "canali.configura",
	# the phone: everybody their own line, the manager the others'
	"CRM Telephony Agent": "telefono.configura",
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
