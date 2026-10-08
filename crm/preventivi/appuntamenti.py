# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""An accepted quote is done service by service, by the agenda.

An appointment of a service still to do, for the person of an accepted quote,
takes its row at the price agreed - the ones already booked too, when the quote is
accepted - and when the person came, the row is done. A cancellation, a no-show or
another service gives it back. Every row done or cancelled, the quote is completed;
one to do again opens it.
"""

from __future__ import annotations

import datetime

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate

from crm.fcrm.doctype.crm_appointment.crm_appointment import person_of
from crm.preventivi import regole as R
from crm.preventivi.api import DOCTYPE, VOCE

APPUNTAMENTO = "CRM Appointment"
PARTECIPANTE = "CRM Appointment Participant"


def _persone(appuntamento, anche_annullati: bool = False) -> list[str]:
	persone = []
	for riga in appuntamento.get("participants") or []:
		if riga.status == "Cancelled" and not anche_annullati:
			continue
		persona = person_of(riga.party_type, riga.party)
		if persona:
			persone.append(persona)
	return persone


def _voci(preventivo: str) -> list[frappe._dict]:
	return frappe.get_all(
		VOCE,
		filters={"parent": preventivo, "parenttype": DOCTYPE},
		fields=["name", "service", "phase", "status", "amount", "appointment"],
		order_by="idx asc",
	)


def _da_prendere(persone: list[str], servizio: str) -> tuple | None:
	"""The row an appointment of ``servizio`` takes: of its people in order, in their
	accepted quotes from the oldest, the first still to do."""
	for persona in persone:
		for preventivo in frappe.get_all(
			DOCTYPE,
			filters={"lead": persona, "status": R.ACCETTATO},
			pluck="name",
			order_by="accepted_on asc",
		):
			voci = _voci(preventivo)
			n = R.voce_per(voci, servizio)
			if n is not None:
				return preventivo, voci[n].name, flt(voci[n].amount), persona
	return None


def _della_voce(appuntamento: str) -> frappe._dict | None:
	righe = frappe.get_all(
		VOCE,
		filters={"parenttype": DOCTYPE, "appointment": appuntamento},
		fields=["name", "parent", "service", "amount"],
		limit=1,
	)
	return righe[0] if righe else None


def _prezzo(appuntamento, importo: float, persona: str) -> None:
	"""The price agreed in the quote, for the quote's person."""
	attivi = [riga for riga in appuntamento.participants if riga.status != "Cancelled"]
	for riga in attivi:
		if person_of(riga.party_type, riga.party) == persona:
			riga.amount = importo
	if cint(appuntamento.per_participant):
		appuntamento.total_amount = sum(flt(riga.amount) for riga in attivi)
	elif len(attivi) <= 1:
		appuntamento.unit_price = appuntamento.total_amount = importo
	else:
		return
	appuntamento.price_source = _("As agreed in the quote")


def _senza_fermare(titolo: str, doc, funzione) -> None:
	"""The agenda never stops for a quote: what fails is logged."""
	frappe.db.savepoint("preventivo_appuntamento")
	try:
		funzione()
	except Exception:
		frappe.db.rollback(save_point="preventivo_appuntamento")
		frappe.log_error(title=titolo, reference_doctype=doc.doctype, reference_name=doc.name)


def in_validazione(doc, method=None) -> None:
	"""`validate` of an appointment: a new one of a service still to do, for the
	person of an accepted quote, will take it at the price agreed; one that has it
	keeps the price. One brought over from the previous software takes none."""
	if not doc.service or doc.status == "Cancelled" or doc.flags.get("importato"):
		return
	try:
		if doc.is_new():
			scelta = _da_prendere(_persone(doc), doc.service)
			if scelta:
				doc.flags.voce_del_preventivo = scelta
				_prezzo(doc, scelta[2], scelta[3])
			return
		voce = _della_voce(doc.name)
		if voce and voce.service == doc.service:
			persona = frappe.db.get_value(DOCTYPE, voce.parent, "lead")
			if persona in _persone(doc, anche_annullati=True):
				_prezzo(doc, flt(voce.amount), persona)
	except Exception:
		frappe.log_error(title=_("Quote price not applied"), reference_doctype=doc.doctype)


def creato(doc, method=None) -> None:
	"""`after_insert`: the row is booked with it."""
	scelta = doc.flags.get("voce_del_preventivo")
	if not scelta:
		return

	def prenota():
		frappe.db.set_value(VOCE, scelta[1], {"appointment": doc.name, "status": R.PRENOTATA})

	_senza_fermare(_("Quote row not booked for {0}").format(doc.name), doc, prenota)


def _libera(voce) -> None:
	frappe.db.set_value(
		VOCE, voce.name, {"appointment": None, "status": R.DA_FARE, "done_on": None, "done_by": None}
	)


def aggiornato(doc, method=None) -> None:
	"""`on_update`: the person came, the row is done; cancelled, missed, or of
	another service now, it is to do again."""
	voce = _della_voce(doc.name)
	if not voce:
		return

	def segui():
		persona = frappe.db.get_value(DOCTYPE, voce.parent, "lead")
		riga = next((r for r in doc.participants if person_of(r.party_type, r.party) == persona), None)
		if (
			doc.status in ("Cancelled", "No Show")
			or riga is None
			or riga.status in ("Cancelled", "No Show")
			or voce.service != doc.service
		):
			_libera(voce)
		elif doc.status == "Completed" or riga.status == "Attended":
			chi = next((r.user for r in doc.staff or [] if r.user), None)
			frappe.db.set_value(
				VOCE, voce.name, {"status": R.FATTA, "done_on": getdate(doc.starts_on), "done_by": chi}
			)
		completa(voce.parent)

	_senza_fermare(_("Quote not followed for appointment {0}").format(doc.name), doc, segui)


def eliminato(doc, method=None) -> None:
	"""`on_trash`: the row is to do again, before the link would stop the delete."""
	voce = _della_voce(doc.name)
	if voce:
		_libera(voce)
		completa(voce.parent)


def completa(preventivo: str) -> None:
	"""The sums again; every row done or cancelled, the quote is completed, and one
	to do again opens it."""
	doc = frappe.get_doc(DOCTYPE, preventivo)
	voci = [voce.as_dict() for voce in doc.items]
	somme = R.totali(voci)
	stato = doc.status
	if stato == R.ACCETTATO and R.completato(voci):
		stato = R.COMPLETATO
	elif stato == R.COMPLETATO and not R.completato(voci):
		stato = R.ACCETTATO
	frappe.db.set_value(
		DOCTYPE,
		preventivo,
		{"status": stato, "total_net": somme["net"], "total_done": somme["done"]},
		update_modified=False,
	)


def _scrivi_prezzo(appuntamento: str, importo: float, persona: str) -> None:
	doc = frappe.get_doc(APPUNTAMENTO, appuntamento)
	_prezzo(doc, importo, persona)
	frappe.db.set_value(
		APPUNTAMENTO,
		appuntamento,
		{"unit_price": doc.unit_price, "total_amount": doc.total_amount, "price_source": doc.price_source},
		update_modified=False,
	)
	for riga in doc.participants:
		frappe.db.set_value(PARTECIPANTE, riga.name, "amount", riga.amount, update_modified=False)


def raccogli(preventivo: str) -> None:
	"""Accepted: the person's appointments already booked from today, of a row's
	service and of no row yet, take theirs in order."""
	doc = frappe.get_doc(DOCTYPE, preventivo)
	servizi = {voce.service for voce in doc.items if voce.status == R.DA_FARE}
	if not servizi:
		return
	prenotati = frappe.get_all(
		PARTECIPANTE,
		filters={
			"parenttype": APPUNTAMENTO,
			"party_type": "CRM Lead",
			"party": doc.lead,
			"status": ("!=", "Cancelled"),
		},
		pluck="parent",
	)
	if not prenotati:
		return
	oggi = datetime.datetime.combine(getdate(), datetime.time.min)
	for appuntamento in frappe.get_all(
		APPUNTAMENTO,
		filters=[
			["name", "in", list(set(prenotati))],
			["service", "in", list(servizi)],
			["status", "not in", ("Cancelled", "No Show")],
			["starts_on", ">=", oggi],
		],
		fields=["name", "service"],
		order_by="starts_on asc",
	):
		if _della_voce(appuntamento.name):
			continue
		voci = _voci(preventivo)
		n = R.voce_per(voci, appuntamento.service)
		if n is None:
			continue
		frappe.db.set_value(VOCE, voci[n].name, {"appointment": appuntamento.name, "status": R.PRENOTATA})
		_scrivi_prezzo(appuntamento.name, flt(voci[n].amount), doc.lead)
