# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Settings > The centre > Your data: the appointments and their history brought
over from the previous software (`persone.importa`).

A sheet of appointments, read as the people's is (`foglio`, `appuntamenti_regole`):
the preview shows each row as an appointment and what is wrong with it, and asks
what each service, professional and room the sheet names is here - matched by
name where it is plain, else «Other» (a service made for what was brought over),
nobody, no room. Then a job brings them in: the person found as the people's
import finds them (fiscal code, email, mobile, name and birth date) or made when
the row says who they are; an appointment brought in once (`import_key`), never
twice. What is past was attended unless the sheet says it was cancelled or
missed, and makes clients (and, with the clinic, patients) the way the agenda
does, and their last visit; nothing is announced, nobody is written to, no
automation hears it, no deal moves, no subscription or cycle or quote is used
(`flags.importato`, `_in_silenzio`). One to come waits in the agenda as booked,
with the centre's reminders at its time.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager

import frappe
import frappe.utils.background_jobs as lavori
from frappe import _
from frappe.utils import now_datetime

from crm.importazione import appuntamenti_regole as R
from crm.importazione import importa, regole
from crm.permissions.livelli import richiede

EVENTO = "crm_importazione_appuntamenti"
ESITO = "crm:importazione:appuntamenti:esito"
#: The choice that sends a service the centre does not have to «Other».
ALTRO = "__other__"
APPUNTAMENTO = "CRM Appointment"


def _foglio(file_url: str):
	intestazione, righe = importa._foglio(file_url)
	return intestazione, righe, R.riconosci(intestazione)


def _in_parole(problemi: list[tuple[str, str]]) -> list[str]:
	return [_(frase).format(valore) for frase, valore in problemi]


def _scelte() -> dict:
	"""What a name of the sheet can be here: the services, the professionals (the
	centre's users), the rooms."""
	servizi = frappe.get_all(
		"CRM Service", filters={"enabled": 1}, fields=["name", "service_name"], order_by="service_name asc"
	)
	utenti = frappe.get_all(
		"User",
		filters={"enabled": 1, "user_type": "System User", "name": ["not in", ["Administrator", "Guest"]]},
		fields=["name", "full_name"],
		order_by="full_name asc",
	)
	stanze = frappe.get_all(
		"CRM Resource",
		filters={"enabled": 1, "resource_type": "Room"},
		fields=["name", "resource_name"],
		order_by="resource_name asc",
	)
	return {
		"services": [{"value": s.name, "label": s.service_name or s.name} for s in servizi],
		"professionals": [{"value": u.name, "label": u.full_name or u.name} for u in utenti],
		"rooms": [{"value": r.name, "label": r.resource_name or r.name} for r in stanze],
	}


def _abbina(nomi: Counter, opzioni: list[dict], altrimenti: str) -> list[dict]:
	"""Each name the sheet writes, how many rows, and what it is here by name."""
	candidati = {o["value"]: [o["label"], o["value"]] for o in opzioni}
	return [
		{"name": nome, "rows": quante, "choice": (R.abbina(nome, candidati) if nome else None) or altrimenti}
		for nome, quante in sorted(nomi.items(), key=lambda voce: (-voce[1], voce[0]))
	]


def _gia_portati(chiavi: list[str]) -> set[str]:
	trovati: set[str] = set()
	for inizio in range(0, len(chiavi), 1000):
		trovati.update(
			frappe.get_all(
				APPUNTAMENTO,
				filters={"import_key": ["in", chiavi[inizio : inizio + 1000]]},
				pluck="import_key",
			)
		)
	return trovati


def _leggi(file_url: str):
	"""Every row as an appointment, with its key and problems."""
	intestazione, righe, mappa = _foglio(file_url)
	adesso = now_datetime()
	lette = []
	for numero, riga in enumerate(righe, start=2):
		dati, problemi = R.appuntamento(riga, mappa, intestazione, adesso)
		lette.append((numero, dati, problemi, R.chiave(dati)))
	return intestazione, mappa, lette


@frappe.whitelist()
@richiede("persone.importa")
def preview(file_url: str) -> dict:
	"""What the sheet holds, before anything is written: which column is what, what
	each name it gives a service, a professional or a room is here, the first rows
	as appointments, what is wrong, what is here already."""
	intestazione, mappa, lette = _leggi(file_url)
	gia = _gia_portati([chiave for _n, _d, _p, chiave in lette])
	scelte = _scelte()
	servizi, professionisti, stanze = Counter(), Counter(), Counter()
	conti = Counter()
	persone: dict[tuple, str | None] = {}
	nuove: set[tuple] = set()
	anteprima = []
	for numero, dati, problemi, chiave in lette:
		if R.da_lasciare(dati, problemi):
			esito = "left_out"
		elif chiave in gia:
			esito = "already"
		else:
			identita = tuple(regole.chiavi(dati["person"])) or (
				dati["person"]["first_name"],
				dati["person"]["last_name"],
			)
			if identita not in persone:
				persone[identita] = importa._trova(dati["person"])
			if persone[identita]:
				esito = "found"
			elif regole.chiavi(dati["person"]):
				esito = "new_person"
				nuove.add(identita)
			else:
				esito = "nobody"
		conti[esito] += 1
		if problemi:
			conti["with_problems"] += 1
		if esito in ("found", "new_person"):
			servizi[dati["service"]] += 1
			if dati["professional"]:
				professionisti[dati["professional"]] += 1
			if dati["room"]:
				stanze[dati["room"]] += 1
		if len(anteprima) < importa.ANTEPRIMA:
			anteprima.append(
				{
					"row": numero,
					"name": " ".join(
						filter(None, (dati["person"]["first_name"], dati["person"]["last_name"]))
					),
					"starts_on": dati["starts_on"],
					"service": dati["service"],
					"professional": dati["professional"],
					"status": dati["status"],
					"outcome": esito,
					"problems": _in_parole(problemi),
				}
			)
	return {
		"columns": [{"name": str(nome or ""), "field": mappa.get(i)} for i, nome in enumerate(intestazione)],
		"total": len(lette),
		"to_bring": conti["found"] + conti["new_person"],
		"already": conti["already"],
		"left_out": conti["left_out"] + conti["nobody"],
		"nobody": conti["nobody"],
		"with_problems": conti["with_problems"],
		"new_people": len(nuove),
		"services": _abbina(servizi, scelte["services"], ALTRO),
		"professionals": _abbina(professionisti, scelte["professionals"], ""),
		"rooms": _abbina(stanze, scelte["rooms"], ""),
		"options": scelte,
		"rows": anteprima,
		"running": frappe.cache.get_value(importa.CHIAVE),
		"last": frappe.cache.get_value(ESITO),
	}


@frappe.whitelist()
@richiede("persone.importa")
def get_state() -> dict:
	"""Whether a sheet is being brought in, and how the last one of appointments went."""
	return {"running": frappe.cache.get_value(importa.CHIAVE), "last": frappe.cache.get_value(ESITO)}


def _pulisci(scelte, opzioni: dict) -> dict:
	"""The preview's choices, only what exists here: a service, a user, a room."""
	scelte = frappe.parse_json(scelte) if isinstance(scelte, str) else (scelte or {})
	validi = {chiave: {o["value"] for o in valori} for chiave, valori in opzioni.items()}
	pulite = {}
	for chiave, altrimenti in (("services", ALTRO), ("professionals", ""), ("rooms", "")):
		pulite[chiave] = {
			str(nome): (valore if valore in validi[chiave] else altrimenti)
			for nome, valore in (scelte.get(chiave) or {}).items()
		}
	return pulite


@frappe.whitelist(methods=["POST"])
@richiede("persone.importa")
def start(file_url: str, choices=None) -> dict:
	"""Bring the sheet's appointments in, in a job. One sheet at a time, of people
	or of appointments."""
	if frappe.cache.get_value(importa.CHIAVE):
		frappe.throw(_("A sheet is already being brought in"))
	_foglio(file_url)
	scelte = _pulisci(choices, _scelte())
	frappe.cache.set_value(
		importa.CHIAVE, {"by": frappe.session.user, "done": 0, "total": 0}, expires_in_sec=6 * 3600
	)
	frappe.cache.delete_value(ESITO)
	if frappe.flags.in_test:
		return importa_appuntamenti(file_url, scelte, frappe.session.user)
	frappe.enqueue(
		"crm.importazione.appuntamenti.importa_appuntamenti",
		queue="long",
		timeout=4 * 3600,
		file_url=file_url,
		scelte=scelte,
		utente=frappe.session.user,
		enqueue_after_commit=True,
	)
	return {"started": True}


def _conferma() -> None:
	"""Each appointment on its own; run inline by a test, the test's rollback undoes it."""
	if not frappe.flags.in_test:
		frappe.db.commit()  # nosemgrep: frappe-manual-commit — each appointment on its own


def importa_appuntamenti(file_url: str, scelte: dict, utente: str) -> dict:
	"""Bring every row in; one that fails is said, the others go on."""
	esito = {"created": 0, "already": 0, "left_out": 0, "nobody": 0, "new_people": 0, "errors": []}
	try:
		_intestazione, _mappa, lette = _leggi(file_url)
		gia = _gia_portati([chiave for _n, _d, _p, chiave in lette])
		altro = None
		for numero, dati, problemi, chiave in lette:
			if R.da_lasciare(dati, problemi):
				esito["left_out"] += 1
				continue
			if chiave in gia:
				esito["already"] += 1
				continue
			try:
				persona = importa._trova(dati["person"])
				if not persona and not regole.chiavi(dati["person"]):
					esito["nobody"] += 1
					continue
				if not persona:
					importa._porta(dati["person"])
					persona = importa._trova(dati["person"])
					esito["new_people"] += 1
				servizio = scelte["services"].get(dati["service"]) or ALTRO
				if servizio == ALTRO:
					altro = altro or _servizio_altro(scelte, utente)
					servizio = altro
				_porta(dati, chiave, persona, servizio, scelte)
				_conferma()
			except Exception as errore:
				if not frappe.flags.in_test:
					frappe.db.rollback()
				esito["errors"].append({"row": numero, "error": _messaggio(errore)})
				continue
			gia.add(chiave)
			esito["created"] += 1
			if numero % 50 == 0:
				_avanza(utente, numero - 1, len(lette))
		return esito
	finally:
		frappe.cache.delete_value(importa.CHIAVE)
		frappe.cache.set_value(ESITO, esito, expires_in_sec=7 * 24 * 3600)
		frappe.publish_realtime(EVENTO, {"state": "done", **esito}, user=utente, after_commit=False)


def _messaggio(errore: Exception) -> str:
	testo = frappe.utils.strip_html(str(errore)) or errore.__class__.__name__
	return " ".join(testo.split())[:200]


def _servizio_altro(scelte: dict, utente: str) -> str:
	"""The service a sheet's appointment of no service the centre has goes to, made
	once in the centre's language, never offered online: delivered by the
	professionals the sheet names (a service has at least one), else by whoever
	brings the sheet in."""
	from crm import lingue

	nome = _("Other", lang=lingue.del_centro(), context="A service brought over")
	if not frappe.db.exists("CRM Service", nome):
		chi = sorted({u for u in scelte["professionals"].values() if u}) or [utente]
		frappe.get_doc(
			{
				"doctype": "CRM Service",
				"service_name": nome,
				"enabled": 1,
				"bookable_online": 0,
				"duration": 30,
				"staff": [{"user": u} for u in chi],
			}
		).insert(ignore_permissions=True)
	return nome


def _niente(*args, **kwargs):
	return None


@contextmanager
def _in_silenzio() -> Iterator[None]:
	"""While an appointment brought over is saved, nothing leaves: the automations,
	the calendar's mirror, the platforms, emails, jobs and messages to the browser
	(the flags the demo's parts mute them by, `crm.demo.modo.SILENZI`)."""
	from crm.demo.modo import SILENZI

	prima = {flag: frappe.flags.get(flag) for flag in SILENZI}
	originali = {
		(frappe, "enqueue"): frappe.enqueue,
		(lavori, "enqueue"): lavori.enqueue,
		(frappe, "publish_realtime"): frappe.publish_realtime,
	}
	for flag in SILENZI:
		frappe.flags[flag] = True
	for (modulo, nome), _f in originali.items():
		setattr(modulo, nome, _niente)
	try:
		yield
	finally:
		for (modulo, nome), funzione in originali.items():
			setattr(modulo, nome, funzione)
		for flag, valore in prima.items():
			frappe.flags[flag] = valore


def _porta(dati: dict, chiave: str, persona: str, servizio: str, scelte: dict) -> str:
	"""One appointment in, as it went."""
	nome_persona = frappe.db.get_value("CRM Lead", persona, "lead_name") or " ".join(
		filter(None, (dati["person"]["first_name"], dati["person"]["last_name"]))
	)
	doc = frappe.get_doc(
		{
			"doctype": APPUNTAMENTO,
			"service": servizio,
			"status": dati["status"],
			"starts_on": dati["starts_on"],
			"ends_on": dati["ends_on"],
			"notes": dati["notes"] or None,
			"import_key": chiave,
			"participants": [
				{
					"party_type": "CRM Lead",
					"party": persona,
					"participant_name": nome_persona,
					"status": R.PARTECIPANTE[dati["status"]],
				}
			],
		}
	)
	utente = scelte["professionals"].get(dati["professional"]) if dati["professional"] else None
	if utente:
		doc.append("staff", {"user": utente})
	stanza = scelte["rooms"].get(dati["room"]) if dati["room"] else None
	if stanza:
		doc.append("resources", {"resource": stanza, "quantity": 1})
	doc.flags.importato = True
	with _in_silenzio():
		doc.insert(ignore_permissions=True)
	return doc.name


def _avanza(utente: str, fatti: int, totale: int) -> None:
	stato = {"by": utente, "done": fatti, "total": totale}
	frappe.cache.set_value(importa.CHIAVE, stato, expires_in_sec=6 * 3600)
	frappe.publish_realtime(EVENTO, {"state": "running", **stato}, user=utente, after_commit=False)
