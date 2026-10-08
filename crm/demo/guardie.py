# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Nothing the demo made reaches anybody.

The demo's people have addresses at a domain that receives no email and numbers
that look like anybody's: while the demo is in, an automation the centre writes, a
reminder, an offer of the waiting list would write to them like to anybody else.
So, while the demo data are in (or being made):

- an email to a demo address leaves the queue before it is sent (`posta_in_coda`);
- a WhatsApp or an SMS to a demo person's number is kept in the conversation and
  never handed to Meta or Twilio (`trattenuto`, read where they are sent), and so is
  any while a part of the demo is being made;
- a call to one does not leave (`crm.telephony.uscita.perche_no`);
- a notification about a demo record stays in the panel, never by email;
- no outside service hears of a demo record (`mai_fuori`): Meta's conversions are
  never told of a demo person, a demo ad's preview is never asked of Meta, a demo
  post is marked published at its time, never handed to a network - as a demo SMS
  is kept as sent -, a demo invoice never reaches Fatture in Cloud and a demo
  appointment is never reminded, nor a demo person of what they owe;
- the public booking page offers the demo's services only to somebody signed in,
  who is trying the page out: never to a visitor;
- a message or a call that comes in from a number a demo person has too is never
  filed on them (`persona_vera`): the demo's go with it, a real message stays.

Each check costs one cached read when no demo is in.
"""

from __future__ import annotations

import re

import frappe
from frappe import _

from crm.demo import dati, registro

#: Domains that receive nothing by their own rule (RFC 2606): never written to
#: while a demo is in.
RISERVATI = (dati.DOMINIO, "example.net", "example.org")
SUFFISSI_RISERVATI = (".example", ".invalid", ".test", ".localhost")

CHIAVE_NUMERI = "crm_demo_numeri"
#: What an email the guard kept from leaving says, and how the removal finds it.
NON_INVIATA = "DottorCloud: written to a person of the demo data, never sent."


def attiva() -> bool:
	"""Whether the demo data are in, or being made right now."""
	return registro.raccolta() is not None or registro.caricati()


def indirizzo_di_prova(email: str | None) -> bool:
	if not email:
		return False
	dominio = email.strip().lower().rpartition("@")[2].rstrip(">").strip()
	return dominio in RISERVATI or dominio.endswith(SUFFISSI_RISERVATI)


def _cifre(numero: str | None) -> str:
	"""The last nine digits: a number written any way, the same."""
	return re.sub(r"\D", "", numero or "")[-9:]


def numero_di_prova(numero: str | None) -> bool:
	"""Whether ``numero`` is one of the demo's people's or colleagues' numbers."""
	if not numero or not attiva():
		return False
	cifre = _cifre(numero)
	return len(cifre) == 9 and cifre in _numeri_della_demo()


def trattenuto(numero: str | None) -> bool:
	"""Whether a WhatsApp or an SMS to ``numero`` stays in the conversation: anything
	while a part of the demo is being made - its people are written down as it goes,
	after the numbers were read - and a demo person's or colleague's after."""
	return registro.raccolta() is not None or numero_di_prova(numero)


def _numeri_della_demo() -> frozenset[str]:
	return frappe.cache.get_value(CHIAVE_NUMERI, generator=_leggi_i_numeri)


def _leggi_i_numeri() -> frozenset[str]:
	nomi = registro.registrati()
	numeri = set()
	for doctype, campi in (("CRM Lead", ("mobile_no", "phone")), ("User", ("mobile_no", "phone"))):
		if nomi.get(doctype):
			for riga in frappe.get_all(
				doctype, filters={"name": ["in", sorted(nomi[doctype])]}, fields=list(campi)
			):
				numeri.update(_cifre(riga.get(campo)) for campo in campi)
	if nomi.get("Contact"):
		numeri.update(
			_cifre(numero)
			for numero in frappe.get_all(
				"Contact Phone",
				filters={"parenttype": "Contact", "parent": ["in", sorted(nomi["Contact"])]},
				pluck="phone",
			)
		)
	return frozenset(cifre for cifre in numeri if len(cifre) == 9)


def dimentica() -> None:
	"""The demo came in or went: what was read of it is read again."""
	frappe.cache.delete_value(CHIAVE_NUMERI)
	frappe.local.crm_demo_nomi = None


# -- email ---------------------------------------------------------------------------------


def posta_in_coda(doc, method=None) -> None:
	"""`Email Queue` before_insert: a demo address leaves the queue; with nobody else
	in it, the email is never sent, and says why."""
	if not attiva():
		return
	righe = list(doc.get("recipients") or [])
	restano = [riga for riga in righe if not indirizzo_di_prova(riga.recipient)]
	if len(restano) == len(righe):
		return
	doc.set("recipients", restano)
	if not restano:
		doc.status = "Error"
		doc.error = NON_INVIATA


# -- notifications ----------------------------------------------------------------------------


def solo_nel_pannello(*riferimenti: tuple[str | None, str | None]) -> bool:
	"""A notification about a demo record is read in the panel, never sent by email."""
	if not attiva():
		return False
	return any(doctype and name and registro.di_prova(doctype, name) for doctype, name in riferimenti)


# -- outside services ---------------------------------------------------------------------------


def mai_fuori(doctype: str, nome: str | None) -> bool:
	"""Whether a record is the demo's, which no outside service hears about (Meta,
	the social networks). While a part is made, everything is."""
	if not nome:
		return False
	return registro.raccolta() is not None or str(nome) in registro.nomi_di_prova(doctype)


# -- the public pages -------------------------------------------------------------------------


def nascosto_al_pubblico(doctype: str, name: str | None) -> bool:
	"""A demo record is never offered to a visitor of the public pages; somebody
	signed in, trying the page out, sees it."""
	if frappe.session.user != "Guest" or not name:
		return False
	return name in registro.nomi_di_prova(doctype)


# -- what the demo set up -----------------------------------------------------------------------


def solo_per_la_demo(doctype: str, nome: str | None, persona: str | None) -> bool:
	"""Whether a piece of the demo's setup that asks something of people by itself (a
	form owed at a booking) is kept from ``persona``: it is asked of the demo's people
	only. A real person booked while the demo is in is never sent the demo's privacy
	notice, nor owes it at the desk; the centre uses it by choosing it."""
	if not nome or not persona or registro.raccolta() is not None:
		return False
	return str(nome) in registro.nomi_di_prova(doctype) and str(persona) not in registro.nomi_di_prova(
		"CRM Lead"
	)


# -- what comes in ------------------------------------------------------------------------------


def della_demo_per_chi_arriva(doctype: str, nome: str | None) -> bool:
	"""Whether a record found for somebody who just wrote or called is one of the
	demo's, while the demo is in and not being made. The demo's numbers look like
	anybody's: a real one may be a demo person's too, and what is filed on a demo
	person goes with the demo."""
	if not nome or registro.raccolta() is not None or not registro.caricati():
		return False
	return str(nome) in registro.nomi_di_prova(doctype)


def contatto_della_demo(contatto: dict | None) -> bool:
	"""Whether the person, deal or address book entry found for a number is the demo's."""
	contatto = contatto or {}
	return any(
		della_demo_per_chi_arriva(doctype, contatto.get(chiave))
		for doctype, chiave in (("CRM Lead", "lead"), ("CRM Deal", "deal"), ("Contact", "name"))
	)


def persona_vera(numero: str | None) -> str | None:
	"""The person of the centre's with ``numero``, not the demo's: the oldest, as
	the number was theirs first."""
	cifre = _cifre(numero)
	if len(cifre) < 9:
		return None
	for (persona,) in frappe.db.sql(
		"""select name from `tabCRM Lead`
		where replace(replace(replace(mobile_no, ' ', ''), '-', ''), '.', '') like %(fine)s
		order by creation asc""",
		{"fine": f"%{cifre}"},
	):
		if not della_demo_per_chi_arriva("CRM Lead", persona):
			return persona
	return None


# -- calls ---------------------------------------------------------------------------------------


def perche_non_chiamare(numero: str | None) -> str:
	if numero_di_prova(numero):
		from crm.marchio import con_nome

		return con_nome(_("This is a person of the demo data: {brand} does not call them."))
	return ""
