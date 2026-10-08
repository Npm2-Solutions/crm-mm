# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The first steps: what a centre does to start working with the product, each
ticked by itself when it is done (docs/crm/37).

Every module registers its own steps (`registra_passo`), as it does its
capabilities: the base the centre's name, its services and hours, the colleagues,
online booking, the email, the first person and the first appointment; the forms
their forms and consents. A step is offered to whoever may take it - one of its
capabilities is theirs - while its module is on, and it says whether it is done by
looking at the centre's data, never at what somebody clicked: a centre that
already works has nothing left to do, and a step done another way counts.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

import frappe
from frappe.utils import cint


@dataclass(frozen=True)
class Passo:
	chiave: str
	#: In English, in the base's words: the vertical's replace them, the session's
	#: language translates them.
	titolo: str
	#: One line on what it is for.
	perche: str
	#: Whether the centre has done it, from its data.
	fatto: Callable[[], bool]
	#: Who takes it: whoever has one of these capabilities.
	capacita: tuple[str, ...]
	#: Where one does it: a page of the settings (a key of their menu, as
	#: frontend/src/utils/impostazioni.js has it)...
	pagina: str | None = None
	#: ...or a page of the app (a route's name), and what to open there.
	rotta: str | None = None
	azione: str | None = None
	#: The plan's module it belongs to: off, its steps are not offered.
	modulo: str = "base"
	ordine: int = 0


_passi: dict[str, Passo] = {}


def registra_passo(passo: Passo) -> None:
	_passi[passo.chiave] = passo


def passi() -> list[Passo]:
	return sorted(_passi.values(), key=lambda passo: (passo.ordine, passo.chiave))


def da_offrire(
	tutti: Iterable[Passo], puo: Callable[[str], bool], acceso: Callable[[str], bool]
) -> list[Passo]:
	"""The steps a person is offered: one of their capabilities takes it, and its
	module is on. Pure."""
	return [passo for passo in tutti if acceso(passo.modulo) and any(puo(nome) for nome in passo.capacita)]


@frappe.whitelist()
def get_first_steps() -> dict:
	"""The steps this person may take, each with whether the centre has done it."""
	from crm import verticali
	from crm.permissions import livelli

	livelli.carica()
	stati = livelli.moduli_attivi()
	traduci = verticali.traduttore()

	def acceso(modulo: str) -> bool:
		return livelli.stato_modulo(modulo, stati) in (livelli.ATTIVO, livelli.PROVA)

	righe = [
		{
			"key": passo.chiave,
			"title": traduci(passo.titolo),
			"why": traduci(passo.perche),
			"done": bool(passo.fatto()),
			"page": passo.pagina,
			"route": passo.rotta,
			"action": passo.azione,
		}
		for passo in da_offrire(passi(), livelli.puo, acceso)
	]
	return {"steps": righe, "done": sum(riga["done"] for riga in righe), "total": len(righe)}


# ---------------------------------------------------------------------------
# The base's steps.


def c_e(doctype: str, filtri: dict | None = None) -> bool:
	"""Whether the centre has at least one of its own, whoever may read it: what the
	demo data made does not take a step for the centre."""
	from crm.demo import registro

	condizioni = [
		[campo, *valore] if isinstance(valore, list | tuple) else [campo, "=", valore]
		for campo, valore in (filtri or {}).items()
	]
	if della_demo := registro.nomi_di_prova(doctype):
		condizioni.append(["name", "not in", sorted(della_demo)])
	return bool(frappe.get_all(doctype, filters=condizioni, limit=1, pluck="name"))


def _promemoria_accesi() -> bool:
	return bool(cint(frappe.db.get_single_value("CRM Reminder Settings", "enabled")))


def _ha_un_nome() -> bool:
	from crm.moduli.richieste import nome_del_centro

	return bool(nome_del_centro())


def _ha_gli_orari() -> bool:
	orari = frappe.get_single("CRM Scheduling Settings").default_availability
	return bool(orari) or c_e("CRM Staff Schedule", {"enabled": 1})


def _ha_dei_colleghi() -> bool:
	"""An invitation sent, or somebody else working in the centre: more than one
	user with a level, the agency apart."""
	if c_e("CRM Invitation"):
		return True
	from crm.permissions import livelli

	utenti = set(
		frappe.get_all(
			"Has Role",
			filters={"role": ["in", list(livelli.ruoli_di_accesso())], "parenttype": "User"},
			pluck="parent",
			distinct=True,
		)
	)
	from crm.demo import registro

	utenti -= {"Administrator", "Guest"} | registro.nomi_di_prova("User")
	attivi = frappe.get_all(
		"User", filters={"name": ["in", list(utenti) or [""]], "enabled": 1}, pluck="name"
	)
	return len([user for user in attivi if not livelli.e_agenzia(user)]) > 1


def _ha_l_email() -> bool:
	return c_e("Email Account", {"enable_outgoing": 1}) or c_e("Email Account", {"enable_incoming": 1})


PASSI_DELLA_BASE = (
	Passo(
		"nome",
		"Your centre's name and logo",
		"They head the booking page, the forms and the emails people receive.",
		_ha_un_nome,
		("impostazioni.generali",),
		pagina="Brand",
		ordine=10,
	),
	Passo(
		"servizi",
		"The services you offer",
		"What can be booked, how long it takes, what it costs.",
		lambda: c_e("CRM Service", {"enabled": 1}),
		("agenda.configura",),
		pagina="Services",
		ordine=20,
	),
	Passo(
		"orari",
		"Opening hours and shifts",
		"When the centre is open and who works when: the agenda books only then.",
		_ha_gli_orari,
		("agenda.configura",),
		pagina="Hours & shifts",
		ordine=30,
	),
	Passo(
		"colleghi",
		"Your colleagues",
		"Invite whoever works in the centre, each at their level.",
		_ha_dei_colleghi,
		("utenti.gestisci",),
		pagina="Invite User",
		ordine=40,
	),
	Passo(
		"prenotazione",
		"Online booking",
		"People book by themselves, from your website or a link.",
		lambda: c_e("CRM Service", {"enabled": 1, "bookable_online": 1}),
		("prenotazione_online.configura",),
		pagina="Online booking",
		ordine=60,
	),
	Passo(
		"email",
		"The centre's email",
		"Send and receive the centre's emails without leaving the page.",
		_ha_l_email,
		("email.account_centro",),
		pagina="Accounts",
		ordine=70,
	),
	Passo(
		"persona",
		"Your first client",
		"Their details, their appointments, their story: all in one place.",
		lambda: c_e("CRM Lead"),
		("persone.scrivi",),
		rotta="Leads",
		azione="new",
		ordine=80,
	),
	Passo(
		"appuntamento",
		"Your first appointment",
		"Book it in the agenda, for one person or for a class.",
		lambda: c_e("CRM Appointment"),
		("agenda.prenota",),
		rotta="Calendar",
		ordine=90,
	),
	Passo(
		"promemoria",
		"Reminders of the appointments",
		"The day before, by WhatsApp with a tap to confirm, by SMS or by email.",
		_promemoria_accesi,
		("agenda.configura",),
		pagina="Appointment reminders",
		ordine=95,
	),
)


def registra() -> None:
	for passo in PASSI_DELLA_BASE:
		registra_passo(passo)
