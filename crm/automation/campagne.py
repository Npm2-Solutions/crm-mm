# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A campaign: an automation started by hand, sent to a list of people.

From the People list the manager of automations («automazioni.gestisci») sends
an automation that starts "Started by Hand" to the view on screen (a saved view
or the filters set) or to the rows chosen. The list is read under the reader
(`frappe.get_list`): nobody they do not see gets in. Before confirming, the
dialog shows how many the list has and who would be left out and why
(`preview_campaign`, `campagne_regole.motivo`); the enrolment runs in a job
(`esegui`) through `engine.enroll`, which asks the consent again, and the engine
keeps STOP, the promotional hours and the time window at every step. The demo's
people are enrolled like anybody: the guards keep what would be written to them
in DottorCloud (`crm.demo.guardie`). What happened is kept on a `CRM Automation
Campaign`, read on the automation's Enrolments (`get_campaigns`).
"""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import cint, now_datetime

from crm.automation import campagne_regole as R
from crm.automation import engine
from crm.permissions.livelli import puo, verifica

CAMPAGNA = "CRM Automation Campaign"
PERSONA = "CRM Lead"
#: How many people are enrolled between two commits of the job.
A_GRUPPI = 100


def _verifica() -> None:
	verifica("automazioni.gestisci", messaggio=_("Only who manages automations sends a campaign"))


def _da_mandare() -> list[dict]:
	"""The automations a list can be sent to: switched on, started by hand."""
	trigger = frappe.qb.DocType("CRM Automation Trigger")
	automazione = frappe.qb.DocType("CRM Automation")
	return (
		frappe.qb.from_(automazione)
		.join(trigger)
		.on(trigger.parent == automazione.name)
		.select(automazione.name, automazione.title, automazione.marketing_consent, automazione.steps)
		.where(
			(trigger.parenttype == "CRM Automation")
			& (trigger.trigger_event == engine.A_MANO)
			& (automazione.enabled == 1)
		)
		.distinct()
		.orderby(automazione.title)
	).run(as_dict=True)


@frappe.whitelist()
def get_campaigns_to_send() -> list[dict]:
	"""The campaigns the dialog offers, each with the ways it writes by."""
	_verifica()
	return [
		{
			"name": riga.name,
			"title": riga.title,
			"marketing_consent": cint(riga.marketing_consent),
			"channels": sorted(R.canali(engine.parse_json(riga.steps))),
		}
		for riga in _da_mandare()
	]


def _automazione(nome: str):
	doc = frappe.get_doc("CRM Automation", nome)
	riga = next((r for r in doc.triggers if r.trigger_event == engine.A_MANO), None)
	if not doc.enabled or riga is None:
		frappe.throw(_("This automation is not a campaign: it does not start by hand, or it is off"))
	return doc, riga


def _con_me(filtri: dict) -> dict:
	"""The list's filters as the list reads them: «@me» is whoever reads it."""
	utente = frappe.session.user
	for chiave, valore in list(filtri.items()):
		if valore == "@me":
			filtri[chiave] = utente
		elif isinstance(valore, list):
			filtri[chiave] = [utente if v == "@me" else f"%{utente}%" if v == "%@me%" else v for v in valore]
	return filtri


def _parse(valore):
	if isinstance(valore, str):
		return frappe.parse_json(valore) if valore.strip() else None
	return valore


def persone_della_lista(filters=None, names=None) -> list[str]:
	"""The people of the list, as the reader sees them: the rows chosen, else the
	view's filters. A list larger than a campaign takes is refused, never cut."""
	filters = _parse(filters)
	names = _parse(names)
	if names:
		filtri = {"name": ["in", [str(n) for n in names]]}
	else:
		filtri = _con_me(dict(filters or {}))
	trovati = frappe.get_list(PERSONA, filters=filtri, pluck="name", limit=R.MASSIMO + 1, order_by="name asc")
	if len(trovati) > R.MASSIMO:
		frappe.throw(
			_("This list has more than {0} people: narrow it with a filter first").format(
				frappe.format_value(R.MASSIMO, {"fieldtype": "Int"})
			)
		)
	return trovati


def _gia_dentro(automazione, persone: list[str]) -> set[str]:
	stati = ["in", ["Active", "Waiting"]] if automazione.allow_reenrollment else ["!=", "Skipped"]
	return set(
		frappe.get_all(
			"CRM Automation Enrollment",
			filters={
				"automation": automazione.name,
				"reference_doctype": PERSONA,
				"reference_name": ["in", persone],
				"status": stati,
			},
			pluck="reference_name",
		)
	)


def _con_il_consenso(persone: list[str]) -> set[str]:
	"""Who of them agreed to marketing today: one query for the whole list."""
	from crm.moduli import consensi, registro

	risposte: dict[str, list[dict]] = {}
	for riga in frappe.get_all(
		consensi.REGISTRO,
		filters={"lead": ["in", persone], "consent_type": "marketing"},
		fields=["lead", "status", "answered_on", "creation"],
	):
		risposte.setdefault(riga.lead, []).append(riga)
	return {
		lead
		for lead, righe in risposte.items()
		if (registro.stato_attuale(righe) or {}).get("status") == registro.DATO
	}


def _recapiti(persone: list[str]) -> dict[str, dict]:
	"""Email, mobile and STOP as stored: masked for Marketing, they are only asked
	whether they are there."""
	DT = frappe.qb.DocType(PERSONA)
	righe = (
		frappe.qb.from_(DT)
		.select(DT.name, DT.email, DT.mobile_no, DT.sms_opt_out)
		.where(DT.name.isin(persone))
		.run(as_dict=True)
	)
	return {r.name: r for r in righe}


def esamina(automazione, riga_di_avvio, persone: list[str]) -> list[tuple[str, str | None]]:
	"""Each person of the list with why they are left out, or None."""
	if not persone:
		return []
	vie = R.canali(engine.parse_json(automazione.steps))
	marketing = bool(automazione.get("marketing_consent"))
	gia = _gia_dentro(automazione, persone)
	consenso = _con_il_consenso(persone) if marketing else set()
	recapiti = _recapiti(persone)
	gruppi = engine.condition_groups_of({"trigger_condition": riga_di_avvio.get("trigger_condition")})

	esito = []
	for nome in persone:
		dati = recapiti.get(nome) or {}
		persona = {
			"already": nome in gia,
			"consent": nome in consenso,
			"email": dati.get("email"),
			"mobile_no": dati.get("mobile_no"),
			"stop": bool(cint(dati.get("sms_opt_out"))),
			"conditions": None,
		}
		if gruppi and not persona["already"]:
			persona["conditions"] = engine.evaluate_condition_groups(gruppi, frappe.get_doc(PERSONA, nome))
		esito.append((nome, R.motivo(persona, marketing=marketing, vie=vie)))
	return esito


def _della_demo(persone: list[str]) -> int:
	from crm.demo import guardie, registro

	if not guardie.attiva():
		return 0
	return len(set(persone) & registro.nomi_di_prova(PERSONA))


@frappe.whitelist()
def preview_campaign(automation: str, filters=None, names=None) -> dict:
	"""What sending would do now: how many people, who would be left out and why."""
	_verifica()
	automazione, riga = _automazione(automation)
	persone = persone_della_lista(filters, names)
	conti = R.conta(motivo for _nome, motivo in esamina(automazione, riga, persone))
	return {
		**conti,
		"automation": automazione.name,
		"title": automazione.title,
		"channels": sorted(R.canali(engine.parse_json(automazione.steps))),
		"marketing_consent": cint(automazione.get("marketing_consent")),
		"demo": _della_demo(persone),
	}


@frappe.whitelist(methods=["POST"])
def send_campaign(automation: str, filters=None, names=None, source: str | None = None) -> dict:
	"""Send the campaign: written down, then enrolled in a job under the reader."""
	_verifica()
	_automazione(automation)
	filters = _parse(filters)
	names = _parse(names)
	# the list as the reader sees it now: an empty one or a too large one says so here
	if not persone_della_lista(filters, names):
		frappe.throw(_("Nobody in this list"))
	campagna = frappe.get_doc(
		{
			"doctype": CAMPAGNA,
			"automation": automation,
			"status": "Queued",
			"source": (source or "").strip()[:140],
			"filters": json.dumps(filters or {}),
			"names": json.dumps(names or []),
		}
	).insert(ignore_permissions=True)
	if frappe.flags.in_test:
		esegui(campagna.name)
	else:
		frappe.enqueue(
			"crm.automation.campagne.esegui",
			queue="long",
			timeout=3600,
			enqueue_after_commit=True,
			campagna=campagna.name,
		)
	return {"name": campagna.name}


def esegui(campagna: str) -> None:
	"""The job: the list read again under whoever sent it, each person enrolled or
	left out with the reason, the counts kept as it goes."""
	doc = frappe.get_doc(CAMPAGNA, campagna)
	if doc.status not in ("Queued", "Running"):
		return
	doc.db_set({"status": "Running", "started_on": now_datetime()})
	_conferma()
	try:
		automazione, riga = _automazione(doc.automation)
		persone = persone_della_lista(
			engine.parse_json(doc.filters) or {}, engine.parse_json(doc.names) or None
		)
		motivi: list[str | None] = []
		for indice, (nome, motivo) in enumerate(esamina(automazione, riga, persone), start=1):
			if motivo is None and not engine.enroll(
				automazione.name, PERSONA, nome, {"campaign": doc.name}, trigger_row=riga
			):
				# in it meanwhile, or the consent was taken back since the look
				motivo = R.SENZA_CONSENSO if _saltato_ora(automazione.name, nome) else R.GIA_DENTRO
			elif motivo == R.SENZA_CONSENSO:
				# not let in, and the runs say so, once: as an event's would
				engine.salta_per_il_consenso(automazione.name, PERSONA, nome)
			motivi.append(motivo)
			if indice % A_GRUPPI == 0:
				_conta(doc, motivi)
				_conferma()
		_conta(doc, motivi)
		doc.db_set({"status": "Done", "finished_on": now_datetime()})
	except Exception:
		if not frappe.flags.in_test:
			frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "CRM Automation: campaign failed")
		doc.reload()
		doc.db_set({"status": "Failed", "finished_on": now_datetime(), "error": _("See error log")})
	_conferma()
	frappe.publish_realtime(
		"crm_campaign_done", {"name": doc.name, "automation": doc.automation}, user=doc.owner
	)


def _conferma() -> None:
	"""The job commits as it goes; run inline by a test, the test's rollback undoes it."""
	if not frappe.flags.in_test:
		frappe.db.commit()


def _saltato_ora(automazione: str, persona: str) -> bool:
	return bool(
		frappe.db.exists(
			"CRM Automation Enrollment",
			{
				"automation": automazione,
				"reference_doctype": PERSONA,
				"reference_name": persona,
				"status": "Skipped",
			},
		)
	)


def _conta(doc, motivi: list[str | None]) -> None:
	conti = R.conta(motivi)
	doc.db_set(
		{"total": conti["total"], "enrolled": conti["enrolled"], "skipped": json.dumps(conti["skipped"])}
	)


@frappe.whitelist()
def get_campaigns(automation: str) -> list[dict]:
	"""The campaigns sent with an automation, the latest first, for its Enrolments."""
	if not (puo("automazioni.vedi") or puo("automazioni.gestisci")):
		return []
	righe = frappe.get_all(
		CAMPAGNA,
		filters={"automation": automation},
		fields=[
			"name",
			"status",
			"source",
			"owner",
			"creation",
			"started_on",
			"finished_on",
			"total",
			"enrolled",
			"skipped",
		],
		order_by="creation desc",
		limit=20,
	)
	for riga in righe:
		riga["skipped"] = engine.parse_json(riga.skipped) or {}
		riga["sent_by"] = frappe.db.get_value("User", riga.owner, "full_name") or riga.owner
	return righe
