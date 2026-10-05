# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Cycles of sessions on the site (docs/gestionale-medico, phase 3: "cicli di sedute
(fisioterapia)"): ten sessions of physiotherapy, six of laser. The rules are
`cicli_regole`; here, the appointments.

- **Sold and followed** by the desk, the manager, and the practitioner for their
  people (`agenda.cicli`): the service, how many sessions, from when and maybe
  until when, the price of the whole cycle if it has one, whether a missed session
  is used.
- **An appointment joins its cycle by itself**: booked for the person, of the
  cycle's service, within its days, while a session is left to book - the oldest
  cycle first. A new cycle takes the appointments already booked from its first
  day: the desk often books the sessions first and sells the cycle after. The
  appointment's panel moves one in or out by hand.
- **The cycle counts itself**: done, missed, booked, left; used up it is completed,
  a cancellation opens it again. Past its last day with sessions left it reads as
  expired; closed by hand, nothing joins it any more.
- **A session costs its share** of a cycle with a price: the price over the
  sessions, instead of the price list's. A cycle paid as a whole has one invoice,
  and its sessions leave the list of appointments to invoice.
- **What it is**: an agreement about appointments, not the care. What happened in
  each session is in the clinical record, where the clinic is on.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, fmt_money, get_datetime, get_fullname, getdate, now_datetime

from crm.permissions import livelli
from crm.scheduling import cicli_regole as C
from crm.scheduling import pricing

CICLO = "CRM Session Cycle"
APPUNTAMENTO = "CRM Appointment"
PARTECIPANTE = "CRM Appointment Participant"
PER_SEDUTA, INTERO = "Per session", "The whole cycle"


# ------------------------------------------------------------------ the sessions


def _persone(appuntamento, anche_annullati: bool = False) -> list[str]:
	"""The people an appointment is for, in their order."""
	return [
		riga.party
		for riga in appuntamento.get("participants") or []
		if riga.party_type == "CRM Lead" and riga.party and (anche_annullati or riga.status != "Cancelled")
	]


def sedute(ciclo: str) -> list[dict]:
	"""The appointments of a cycle in the order they come, each with what it is
	for the cycle: done, missed, booked, cancelled - from the cycle's person."""
	righe = frappe.get_all(
		APPUNTAMENTO,
		filters={"session_cycle": ciclo},
		fields=["name", "starts_on", "ends_on", "status"],
		order_by="starts_on asc",
	)
	if not righe:
		return []
	persona = frappe.db.get_value(CICLO, ciclo, "lead")
	stati = {
		riga.parent: riga.status
		for riga in frappe.get_all(
			PARTECIPANTE,
			filters={
				"parenttype": APPUNTAMENTO,
				"parent": ("in", [r.name for r in righe]),
				"party_type": "CRM Lead",
				"party": persona,
			},
			fields=["parent", "status"],
		)
	}
	return [{**riga, "state": C.seduta(riga.status, stati.get(riga.name))} for riga in righe]


def conti(doc, elenco: list[dict] | None = None) -> dict:
	elenco = sedute(doc.name) if elenco is None else elenco
	return C.conta([s["state"] for s in elenco], cint(doc.sessions), bool(cint(doc.missed_count)))


def stato(doc, conteggio: dict | None = None, oggi=None) -> str:
	return C.stato(
		conteggio or conti(doc),
		getdate(doc.valid_until) if doc.valid_until else None,
		oggi or getdate(),
		chiuso=doc.status == C.CHIUSO,
	)


def _aggiorna(nome: str) -> None:
	"""A cycle's status after one of its appointments changed: completed when used
	up, active again when a cancellation leaves a session to book."""
	doc = frappe.get_doc(CICLO, nome)
	if doc.status == C.CHIUSO:
		return
	conteggio = conti(doc)
	nuovo = C.COMPLETATO if conteggio["total"] and conteggio["used"] >= conteggio["total"] else C.ATTIVO
	if nuovo != doc.status:
		frappe.db.set_value(CICLO, nome, "status", nuovo)


def numero_della_seduta(appuntamenti: list[str]) -> dict[str, dict]:
	"""Which session of its cycle each appointment is: "4 of 10"."""
	fatto: dict[str, dict] = {}
	if not appuntamenti:
		return fatto
	cicli = {
		riga.name: riga.session_cycle
		for riga in frappe.get_all(
			APPUNTAMENTO,
			filters={"name": ("in", appuntamenti), "session_cycle": ("is", "set")},
			fields=["name", "session_cycle"],
		)
	}
	for ciclo in set(cicli.values()):
		riga = frappe.db.get_value(CICLO, ciclo, ["sessions", "missed_count"], as_dict=True)
		if not riga:
			continue
		numeri = C.numeri(
			[(s["name"], s["state"]) for s in sedute(ciclo)], perse_contano=bool(cint(riga.missed_count))
		)
		for appuntamento, suo in cicli.items():
			if suo == ciclo:
				fatto[appuntamento] = {
					"cycle": ciclo,
					"number": numeri.get(appuntamento),
					"total": cint(riga.sessions),
				}
	return fatto


# ------------------------------------------------------------------ an appointment joins


def _ciclo_per(persone: list[str], servizio: str, giorno) -> str | None:
	"""The cycle a new appointment of ``servizio`` on ``giorno`` joins: of its
	people in their order, the oldest that is on, within its days, with a session
	left to book."""
	for persona in persone:
		for riga in frappe.get_all(
			CICLO,
			filters={"lead": persona, "service": servizio, "status": C.ATTIVO},
			fields=["name", "sessions", "missed_count", "starts_on", "valid_until"],
			order_by="creation asc",
		):
			if C.si_aggiunge(
				C.ATTIVO,
				conti(riga),
				getdate(riga.starts_on) if riga.starts_on else None,
				getdate(riga.valid_until) if riga.valid_until else None,
				giorno,
			):
				return riga.name
	return None


def _lascia(appuntamento, persona: str | None) -> None:
	"""Out of its cycle: the share of the cycle goes with it, and the price list
	prices it again."""
	appuntamento.session_cycle = None
	for riga in appuntamento.get("participants") or []:
		if riga.party_type == "CRM Lead" and riga.party == persona:
			riga.amount = 0


def aggancia(appuntamento) -> None:
	"""`validate` of an appointment, before its price: a new one of a cycle's service
	joins the cycle; one whose service or person changed leaves it."""
	ciclo = appuntamento.get("session_cycle")
	if ciclo:
		riga = frappe.db.get_value(CICLO, ciclo, ["service", "lead"], as_dict=True)
		if not (
			riga
			and riga.service == appuntamento.service
			and riga.lead in _persone(appuntamento, anche_annullati=True)
		):
			_lascia(appuntamento, riga.lead if riga else None)
		return
	if (
		not appuntamento.is_new()
		or appuntamento.status == "Cancelled"
		or not appuntamento.service
		or not appuntamento.starts_on
	):
		return
	appuntamento.session_cycle = _ciclo_per(
		_persone(appuntamento), appuntamento.service, getdate(appuntamento.starts_on)
	)


def prezzo(appuntamento) -> None:
	"""`validate` of an appointment, after the price list: a session of a cycle with
	a price costs its share, the price over the sessions."""
	ciclo = appuntamento.get("session_cycle")
	if not ciclo:
		return
	riga = frappe.db.get_value(CICLO, ciclo, ["price", "sessions", "lead", "currency"], as_dict=True)
	if not riga or not flt(riga.price) or not cint(riga.sessions):
		return
	quota = flt(flt(riga.price) / cint(riga.sessions), 2)
	attivi = [r for r in appuntamento.get("participants") or [] if r.status != "Cancelled"]
	for r in attivi:
		if r.party_type == "CRM Lead" and r.party == riga.lead:
			r.amount = quota
	if cint(appuntamento.per_participant):
		appuntamento.total_amount = sum(flt(r.amount) for r in attivi)
	elif len(attivi) <= 1:
		appuntamento.unit_price = appuntamento.total_amount = quota
	else:
		# one price for a group: the cycle's person does not set it
		return
	if riga.currency:
		appuntamento.currency = riga.currency
	appuntamento.price_source = _("A cycle of {0} sessions for {1}").format(
		cint(riga.sessions), fmt_money(riga.price, currency=riga.currency)
	)


def _metti(nome: str, ciclo: str | None) -> None:
	"""An appointment into a cycle or out of it without saving it again: its day,
	people and rooms do not change - only the cycle, and the price with it."""
	doc = frappe.get_doc(APPUNTAMENTO, nome)
	if doc.session_cycle and doc.session_cycle != ciclo:
		_lascia(doc, frappe.db.get_value(CICLO, doc.session_cycle, "lead"))
	doc.session_cycle = ciclo
	pricing.apply_to(doc)
	prezzo(doc)
	frappe.db.set_value(
		APPUNTAMENTO,
		nome,
		{
			"session_cycle": ciclo,
			"unit_price": doc.unit_price,
			"total_amount": doc.total_amount,
			"currency": doc.currency,
			"per_participant": doc.per_participant,
			"price_source": doc.price_source,
		},
		update_modified=False,
	)
	for riga in doc.participants:
		frappe.db.set_value(PARTECIPANTE, riga.name, "amount", riga.amount, update_modified=False)


def _riprezza(ciclo: str) -> None:
	"""The price or the sessions changed: the sessions not invoiced yet cost the new
	share; an invoiced one keeps what it was invoiced at."""
	elenco = [s["name"] for s in sedute(ciclo)]
	fatturati = set(
		frappe.get_all(
			"CRM Invoice",
			filters={"appointment": ("in", elenco or [""]), "docstatus": ("<", 2)},
			pluck="appointment",
		)
	)
	for nome in elenco:
		if nome not in fatturati:
			_metti(nome, ciclo)


def raccogli(doc) -> int:
	"""A new cycle takes the person's appointments of its service booked from its
	first day, in the order they come, while sessions are left."""
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
		return 0
	filtri = [
		["name", "in", list(set(prenotati))],
		["service", "=", doc.service],
		["status", "!=", "Cancelled"],
		["session_cycle", "is", "not set"],
		["starts_on", ">=", get_datetime(doc.starts_on)],
	]
	if doc.valid_until:
		filtri.append(["starts_on", "<", get_datetime(add_days(doc.valid_until, 1))])
	presi = 0
	for nome in frappe.get_all(APPUNTAMENTO, filters=filtri, pluck="name", order_by="starts_on asc"):
		if conti(doc)["left"] <= 0:
			break
		_metti(nome, doc.name)
		presi += 1
	return presi


def appuntamento_aggiornato(appuntamento) -> None:
	"""`on_update` of an appointment: its cycle counts again, and the one it left."""
	prima = appuntamento.get_doc_before_save()
	for nome in {appuntamento.get("session_cycle"), prima.get("session_cycle") if prima else None}:
		if nome and frappe.db.exists(CICLO, nome):
			_aggiorna(nome)


def appuntamento_eliminato(appuntamento) -> None:
	"""`after_delete` of an appointment: one session less in its cycle."""
	if appuntamento.get("session_cycle") and frappe.db.exists(CICLO, appuntamento.session_cycle):
		_aggiorna(appuntamento.session_cycle)


def al_cestino(doc) -> None:
	"""`on_trash` of a cycle: deleted only while none of its sessions is used; the
	booked ones leave it."""
	elenco = sedute(doc.name)
	if any(s["state"] in (C.FATTA, C.PERSA) for s in elenco):
		frappe.throw(_("Sessions of this cycle are used already: close it instead"))
	for s in elenco:
		_metti(s["name"], None)


# ------------------------------------------------------------------ who


def _la_persona(lead: str) -> None:
	if not livelli.puo("agenda.vedi"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)


def _ciclo(nome: str):
	doc = frappe.get_doc(CICLO, nome)
	_la_persona(doc.lead)
	doc.check_permission("read")
	return doc


def _gestisce() -> None:
	livelli.verifica("agenda.cicli")


# ------------------------------------------------------------------ reading


def _fatturato(nome: str) -> str | None:
	return frappe.db.get_value("CRM Invoice", {"session_cycle": nome, "docstatus": ("<", 2)}, "name")


def riga(doc, elenco: list[dict] | None = None) -> dict:
	elenco = sedute(doc.name) if elenco is None else elenco
	conteggio = conti(doc, elenco)
	adesso = now_datetime()
	prossima = next(
		(s for s in elenco if s["state"] == C.PRENOTATA and get_datetime(s["starts_on"]) >= adesso), None
	)
	return {
		"name": doc.name,
		"lead": doc.lead,
		"lead_name": doc.lead_name,
		"service": doc.service,
		"sessions": cint(doc.sessions),
		"starts_on": str(doc.starts_on) if doc.starts_on else None,
		"valid_until": str(doc.valid_until) if doc.valid_until else None,
		"status": stato(doc, conteggio),
		"counts": conteggio,
		"next": str(prossima["starts_on"]) if prossima else None,
		"price": flt(doc.price) or None,
		"currency": doc.currency,
		"billing": doc.billing,
		"invoice": _fatturato(doc.name),
		"missed_count": cint(doc.missed_count),
		"practitioner": doc.practitioner,
		"practitioner_name": get_fullname(doc.practitioner) if doc.practitioner else None,
		"notes": doc.notes,
	}


def _potere() -> dict:
	return {"can_manage": livelli.puo("agenda.cicli"), "can_invoice": livelli.puo("fatture.emetti")}


@frappe.whitelist()
def get_cycles(lead: str) -> dict:
	"""The person's cycles, the ones going on first."""
	_la_persona(lead)
	righe = [
		riga(frappe.get_doc(CICLO, nome))
		for nome in frappe.get_list(CICLO, filters={"lead": lead}, pluck="name", order_by="creation desc")
	]
	ordine = {C.ATTIVO: 0, C.SCADUTO: 1, C.COMPLETATO: 2, C.CHIUSO: 3}
	righe.sort(key=lambda r: ordine.get(r["status"], 9))
	return {"cycles": righe, **_potere()}


@frappe.whitelist()
def get_cycle(name: str) -> dict:
	"""A cycle with its sessions: which one each appointment is, and how it went."""
	doc = _ciclo(name)
	elenco = sedute(doc.name)
	numeri = C.numeri([(s["name"], s["state"]) for s in elenco], perse_contano=bool(cint(doc.missed_count)))
	return {
		**riga(doc, elenco),
		"appointments": [
			{
				"name": s["name"],
				"starts_on": str(s["starts_on"]),
				"ends_on": str(s["ends_on"]),
				"state": s["state"],
				"status": s["status"],
				"number": numeri.get(s["name"]),
			}
			for s in elenco
		],
		**_potere(),
	}


def della_persona(persona: str) -> list[dict]:
	"""For the person's own area: the cycles going on, in the words they read -
	no price, no notes, no invoice."""
	fatto = []
	for nome in frappe.get_all(
		CICLO, filters={"lead": persona, "status": C.ATTIVO}, pluck="name", order_by="creation asc"
	):
		dati = riga(frappe.get_doc(CICLO, nome))
		if dati["status"] != C.ATTIVO:
			continue
		fatto.append(
			{
				"name": dati["name"],
				"service": frappe.db.get_value("CRM Service", dati["service"], "service_name")
				or dati["service"],
				"counts": dati["counts"],
				"valid_until": dati["valid_until"],
				"next": dati["next"],
			}
		)
	return fatto


def della_seduta(appuntamento) -> dict | None:
	"""For the appointment's panel: which session of its cycle it is, and the cycles
	of its people and service it could join."""
	if not livelli.puo("agenda.vedi") or not appuntamento.service:
		return None
	persone = _persone(appuntamento, anche_annullati=True)
	if not persone:
		return None
	opzioni = []
	for nome in frappe.get_list(
		CICLO,
		filters={"lead": ("in", persone), "service": appuntamento.service},
		pluck="name",
		order_by="creation asc",
	):
		doc = frappe.get_doc(CICLO, nome)
		conteggio = conti(doc)
		suo_stato = stato(doc, conteggio)
		if nome != appuntamento.session_cycle and (suo_stato != C.ATTIVO or conteggio["left"] <= 0):
			continue
		opzioni.append(
			{
				"name": nome,
				"lead_name": doc.lead_name,
				"sessions": cint(doc.sessions),
				"starts_on": str(doc.starts_on),
				"status": suo_stato,
				"left": conteggio["left"],
			}
		)
	if not opzioni and not appuntamento.session_cycle:
		return None
	numero = numero_della_seduta([appuntamento.name]).get(appuntamento.name) if appuntamento.name else None
	return {
		"cycle": appuntamento.session_cycle,
		"number": numero["number"] if numero else None,
		"total": numero["total"] if numero else None,
		"options": opzioni,
		"can_manage": livelli.puo("agenda.cicli"),
	}


# ------------------------------------------------------------------ writing


@frappe.whitelist(methods=["POST"])
def save_cycle(lead: str, data: str | dict, name: str | None = None) -> dict:
	"""A cycle, new or put right. The service does not change once sessions are
	booked, nor the sessions go below the ones used."""
	_gestisce()
	_la_persona(lead)
	dati = frappe.parse_json(data) if isinstance(data, str) else (data or {})
	if name:
		doc = frappe.get_doc(CICLO, name)
		doc.check_permission("write")
		if doc.lead != lead:
			frappe.throw(_("This cycle belongs to somebody else"))
		if doc.status == C.CHIUSO:
			frappe.throw(_("A closed cycle is not changed: open it again first"))
	else:
		doc = frappe.new_doc(CICLO)
		doc.lead = lead
		doc.status = C.ATTIVO
	sedute_ora = cint(dati.get("sessions"))
	servizio = dati.get("service")
	prima = None
	if not doc.is_new():
		gia = conti(doc)
		if servizio != doc.service and gia["used"] + gia["booked"]:
			frappe.throw(_("The service does not change once sessions are booked"))
		if sedute_ora < gia["used"]:
			frappe.throw(_("{0} sessions are used already").format(gia["used"]))
		prima = (flt(doc.price), cint(doc.sessions))
	doc.service = servizio
	doc.sessions = sedute_ora
	doc.starts_on = dati.get("starts_on") or getdate()
	doc.valid_until = dati.get("valid_until") or None
	doc.price = flt(dati.get("price")) or None
	doc.billing = INTERO if dati.get("billing") == INTERO else PER_SEDUTA
	doc.missed_count = 1 if cint(dati.get("missed_count", 1)) else 0
	doc.practitioner = dati.get("practitioner") or None
	doc.notes = (dati.get("notes") or "").strip() or None
	if doc.is_new():
		doc.insert()
		raccogli(doc)
	else:
		doc.save()
		if prima != (flt(doc.price), cint(doc.sessions)):
			_riprezza(doc.name)
	_aggiorna(doc.name)
	return get_cycle(doc.name)


@frappe.whitelist(methods=["POST"])
def close_cycle(name: str) -> dict:
	"""Closed by hand: what was booked stays booked, nothing new joins it."""
	_gestisce()
	doc = _ciclo(name)
	doc.check_permission("write")
	doc.status = C.CHIUSO
	doc.closed_on = now_datetime()
	doc.save()
	return get_cycle(doc.name)


@frappe.whitelist(methods=["POST"])
def reopen_cycle(name: str) -> dict:
	_gestisce()
	doc = _ciclo(name)
	doc.check_permission("write")
	if doc.status == C.CHIUSO:
		doc.status = C.ATTIVO
		doc.closed_on = None
		doc.save()
		_aggiorna(doc.name)
	return get_cycle(doc.name)


@frappe.whitelist(methods=["POST"])
def delete_cycle(name: str) -> None:
	"""A cycle sold by mistake: gone while none of its sessions is used."""
	_gestisce()
	doc = _ciclo(name)
	doc.check_permission("write")
	if _fatturato(doc.name):
		frappe.throw(_("This cycle is invoiced: close it instead"))
	frappe.delete_doc(CICLO, doc.name, ignore_permissions=True)


@frappe.whitelist(methods=["POST"])
def attach(appointment: str, cycle: str | None = None) -> dict:
	"""An appointment into a cycle, or out of it (``cycle`` empty), by hand."""
	_gestisce()
	appuntamento = frappe.get_doc(APPUNTAMENTO, appointment)
	appuntamento.check_permission("write")
	prima = appuntamento.session_cycle
	if cycle and cycle != prima:
		doc = _ciclo(cycle)
		if doc.service != appuntamento.service or doc.lead not in _persone(appuntamento):
			frappe.throw(_("The cycle is of another service, or of somebody else"))
		conteggio = conti(doc)
		if stato(doc, conteggio) != C.ATTIVO:
			frappe.throw(_("This cycle takes no more sessions"))
		if conteggio["left"] <= 0:
			frappe.throw(_("Every session of this cycle is booked already"))
	_metti(appointment, cycle or None)
	for nome in {prima, cycle}:
		if nome:
			_aggiorna(nome)
	return della_seduta(frappe.get_doc(APPUNTAMENTO, appointment)) or {}
