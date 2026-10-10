# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's locations (`CRM Location`, docs/crm/62): which are on, where an
appointment is, the address the person reads, the issuing company a location
names, and the usual location of whoever works at the desk.

A centre with one location, or none, is a centre as it always was: whatever a
screen shows of the locations asks `piu_sedi()` first. The rules are
`sedi_regole`.
"""

from __future__ import annotations

import frappe
from frappe.utils import cint

from crm.scheduling import sedi_regole as R

SEDE = "CRM Location"
CAMPI = (
	"name",
	"location_name",
	"enabled",
	"address_line",
	"city",
	"pincode",
	"province",
	"phone",
	"email",
	"map_link",
	"opening_hours",
	"company",
)
#: The user's default that keeps where they usually work.
ABITUALE = "crm_sede_abituale"


def attive() -> list[dict]:
	"""The locations switched on, by name; kept for the request."""
	if not hasattr(frappe.local, "crm_sedi_attive"):
		frappe.local.crm_sedi_attive = (
			frappe.get_all(SEDE, filters={"enabled": 1}, fields=list(CAMPI), order_by="location_name asc")
			if frappe.db.table_exists(SEDE)
			else []
		)
	return frappe.local.crm_sedi_attive


def dimentica() -> None:
	"""A location changed in this request: asked again."""
	if hasattr(frappe.local, "crm_sedi_attive"):
		del frappe.local.crm_sedi_attive


def nomi() -> list[str]:
	return [sede["name"] for sede in attive()]


def piu_sedi() -> bool:
	return R.piu_sedi(attive())


def sede(nome: str | None) -> dict | None:
	"""A location by its name, on or off: an old appointment's may be off now."""
	if not nome:
		return None
	for riga in attive():
		if riga["name"] == nome:
			return riga
	return frappe.db.get_value(SEDE, nome, list(CAMPI), as_dict=True)


def nome_di(nome: str | None) -> str:
	riga = sede(nome)
	return (riga or {}).get("location_name") or ""


def per_il_boot() -> list[dict]:
	"""What every screen needs to know of the locations: nothing with one."""
	if not piu_sedi():
		return []
	return [
		{"name": riga["name"], "title": riga["location_name"], "city": riga["city"] or ""}
		for riga in attive()
	]


def valida(nome: str | None) -> str | None:
	"""A location asked by a screen: one that is on, else none."""
	return nome if nome and nome in nomi() else None


def esistente(nome: str | None) -> str | None:
	"""A location written on a room or a shift: one that exists, on or off - a
	location switched off for a while keeps its rooms and shifts."""
	return nome if nome and frappe.db.exists(SEDE, nome) else None


# ------------------------------------------------------------------ the appointment


def _sedi_delle_stanze(stanze: list[str]) -> list[str | None]:
	if not stanze:
		return []
	sedi = dict(
		frappe.get_all(
			"CRM Resource",
			filters={"name": ["in", stanze]},
			fields=["name", "centre_location"],
			as_list=True,
		)
	)
	return [sedi.get(stanza) for stanza in stanze]


def sede_del_turno(utente: str, momento) -> str | None:
	"""The location of the shift a professional works at that moment."""
	from crm.scheduling.availability import staff_working_hours
	from crm.scheduling.timeutils import from_system_naive, scheduling_tz

	return staff_working_hours(utente).sede_at(from_system_naive(momento), scheduling_tz())


def assegna(doc) -> None:
	"""Where an appointment is (`CRM Appointment.centre_location`), kept for the
	lists and filters: its rooms', else its professional's shift's, else what was
	chosen, else the only location."""
	if not doc.meta.has_field("centre_location") or not attive():
		# no location at all: nothing to say, nothing asked
		return
	stanze = [row.resource for row in doc.resources if row.resource]
	del_turno = None
	if doc.starts_on:
		for row in doc.staff:
			if row.user:
				del_turno = sede_del_turno(row.user, doc.starts_on)
				if del_turno:
					break
	doc.centre_location = R.sede_dell_appuntamento(
		_sedi_delle_stanze(stanze), del_turno, valida(doc.centre_location) or doc.centre_location, nomi()
	)


def stanza_aggiornata(doc, method=None) -> None:
	"""A room given a location: the appointments held in it that named none are
	there - the history of a centre that opens its second location, set apart."""
	if not doc.get("centre_location") or not doc.has_value_changed("centre_location"):
		return
	appuntamento = frappe.qb.DocType("CRM Appointment")
	stanza = frappe.qb.DocType("CRM Appointment Resource")
	nomi = (
		frappe.qb.from_(stanza)
		.select(stanza.parent)
		.where((stanza.parenttype == "CRM Appointment") & (stanza.resource == doc.name))
	)
	(
		frappe.qb.update(appuntamento)
		.set(appuntamento.centre_location, doc.centre_location)
		.where(appuntamento.centre_location.isnull() | (appuntamento.centre_location == ""))
		.where(appuntamento.name.isin(nomi))
		.run()
	)


def turni_aggiornati(doc, method=None) -> None:
	"""A professional's shifts that name a location: their appointments from today
	on that named none, and hold in no room that does, are where the shift is."""
	if not attive() or not doc.get("user") or not doc.get("enabled"):
		return
	from crm.scheduling.availability import WorkingHours, holiday_dates
	from crm.scheduling.timeutils import from_system_naive, scheduling_tz

	if not any(riga.get("centre_location") for riga in [*doc.availability, *doc.exceptions]):
		return
	ore = WorkingHours(
		rows=doc.availability, holidays=holiday_dates(doc.holiday_list), exceptions=doc.exceptions
	)
	tz = scheduling_tz()
	righe = frappe.db.sql(
		"""select a.name, a.starts_on from `tabCRM Appointment` a
		join `tabCRM Appointment Staff` s on s.parent = a.name and s.parenttype = 'CRM Appointment'
		where s.user = %(utente)s and a.starts_on >= curdate()
			and ifnull(a.centre_location, '') = ''""",
		{"utente": doc.user},
		as_dict=True,
	)
	for riga in righe:
		dove = ore.sede_at(from_system_naive(riga.starts_on), tz)
		if dove:
			frappe.db.set_value("CRM Appointment", riga.name, "centre_location", dove, update_modified=False)


def conflitti(doc) -> list[str]:
	"""A professional whose shift at that time is in another location than the
	room: an appointment cannot be in two places."""
	from frappe import _

	if not doc.starts_on or not piu_sedi():
		return []
	stanze = [row.resource for row in doc.resources if row.resource]
	sedi_stanze = _sedi_delle_stanze(stanze)
	fuori = []
	for row in doc.staff:
		if not row.user:
			continue
		del_turno = sede_del_turno(row.user, doc.starts_on)
		altrove = R.in_conflitto(del_turno, sedi_stanze)
		if altrove:
			fuori.append(
				_("{0} works at {1} at this time, the room is at {2}").format(
					frappe.utils.get_fullname(row.user), nome_di(del_turno), nome_di(altrove)
				)
			)
	return fuori


def indirizzo_di(appuntamento) -> str:
	"""Where the person goes, as the confirmation, the reminders, the area and the
	calendar file say it: the location's name and address where the appointment
	has one, else the place written on it (an address, a meeting link)."""
	get = appuntamento.get if hasattr(appuntamento, "get") else lambda k: getattr(appuntamento, k, None)
	nome = get("centre_location")
	from crm.scheduling import visite_online

	if nome and not visite_online.del_servizio(get("service")):
		testo = R.dove(sede(nome))
		if testo:
			return testo
	return get("location") or ""


# ------------------------------------------------------------------ the desk and invoicing


def sede_abituale(utente: str | None = None) -> str | None:
	"""Where somebody usually works: the reception desk opens on it."""
	utente = utente or frappe.session.user
	return valida(frappe.defaults.get_user_default(ABITUALE, utente))


def imposta_sede_abituale(nome: str | None, utente: str | None = None) -> None:
	utente = utente or frappe.session.user
	nome = valida(nome)
	if nome:
		frappe.defaults.set_user_default(ABITUALE, nome, utente)
	else:
		frappe.defaults.clear_user_default(ABITUALE, utente)


def della_fattura(fattura) -> str | None:
	"""Where an invoice belongs, for the cash closing and the dashboard: its
	appointment's location - the one it closes, or the one whose deposit it is -,
	else the location where whoever makes it works."""
	appuntamento = fattura.get("appointment") or fattura.get("advance_for")
	if appuntamento:
		dell_appuntamento = frappe.db.get_value("CRM Appointment", appuntamento, "centre_location")
		if dell_appuntamento:
			return dell_appuntamento
	if fattura.get("centre_location"):
		return fattura.centre_location
	if fattura.is_new() and frappe.session.user not in ("Guest", "Administrator"):
		return sede_abituale(frappe.session.user)
	return None


def azienda_per(fattura) -> str | None:
	"""The issuing company the invoice's location names, if it names one that is on."""
	nome = della_fattura(fattura)
	azienda = (sede(nome) or {}).get("company") if nome else None
	if azienda and cint(frappe.db.get_value("CRM Invoicing Company", azienda, "enabled")):
		return azienda
	return None
