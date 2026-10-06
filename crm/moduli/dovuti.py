# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Which forms a person owes, and when (docs/gestionale-medico, "quando si chiede").

A template says when it is asked (``ask_on``: by hand, at the first appointment,
for some services) and how long a signed one counts (``validity``: for ever, a
year, one appointment); a new version may ask again whoever signed an earlier
one, from a date (``asked_from``). `dovuto` answers for one template and one
person, pure; the rest reads the person's signed forms and appointments.

What is owed shows on the person's Forms tab and on the Today page; a template
that says so (``send_before``) is sent by link when an appointment is booked.
"""

from __future__ import annotations

import datetime

import frappe
from frappe.utils import add_years, get_datetime, getdate, now_datetime

from crm.demo import guardie

MODULO = "CRM Form"
MODELLO = "CRM Form Template"
VERSIONE = "CRM Form Template Version"
RICHIESTA = "CRM Form Request"
#: Only a form is asked of a person: a sheet is the operator's, written at the desk.
FORMA = "Form"

#: Why a form is owed, most telling first.
MOTIVI = ("never_signed", "new_version", "expired", "every_appointment")


def _non_conta(firmato: dict, modello: dict, appuntamento: dict | None, oggi: datetime.date) -> str | None:
	"""Why a signed form counts no more, or None when it still does."""
	chiesto_dal = modello.get("asked_from")
	if (
		chiesto_dal
		and oggi >= getdate(chiesto_dal)
		and (firmato.get("version") or 0) < (modello.get("version") or 0)
	):
		return "new_version"
	validita = modello.get("validity") or "Forever"
	if validita == "One year" and add_years(getdate(firmato.get("signed_on")), 1) <= oggi:
		return "expired"
	if validita == "Every appointment" and (
		not appuntamento or firmato.get("appointment") != appuntamento.get("name")
	):
		return "every_appointment"
	return None


def dovuto(
	modello: dict, firmati: list[dict], appuntamento: dict | None = None, oggi: datetime.date | None = None
) -> str | None:
	"""Why ``modello`` is owed now, or None. Pure.

	``modello``: ``ask_on``, ``validity``, ``services``, ``version`` (the current
	one), ``asked_from``. ``firmati``: the person's signed forms of it, each with
	``version``, ``signed_on``, ``appointment``. ``appuntamento``: the one it is
	asked for (``name``, ``service``), or None for the person in general.
	"""
	oggi = oggi or getdate()
	chiesto = modello.get("ask_on") or "By hand"
	if chiesto == "By hand":
		return None
	if chiesto == "Services" and (
		not appuntamento or appuntamento.get("service") not in set(modello.get("services") or ())
	):
		return None
	# one form for each appointment: without an appointment there is nothing to ask yet
	if (modello.get("validity") or "Forever") == "Every appointment" and not appuntamento:
		return None
	if not firmati:
		return "never_signed"
	motivi = [_non_conta(firmato, modello, appuntamento, oggi) for firmato in firmati]
	if any(motivo is None for motivo in motivi):
		return None
	return next(motivo for motivo in MOTIVI if motivo in motivi)


# ------------------------------------------------------------------ from the database


def modelli_che_si_chiedono() -> list[dict]:
	"""The published templates that are asked by themselves, with what `dovuto`
	needs: a handful, read in three queries."""
	righe = frappe.get_all(
		MODELLO,
		filters={
			"enabled": 1,
			"current_version": ("is", "set"),
			"ask_on": ("!=", "By hand"),
			"use": FORMA,
		},
		fields=["name", "title", "clinical", "ask_on", "validity", "current_version", "send_before"],
		order_by="title asc",
	)
	servizi: dict[str, list] = {}
	for riga in frappe.get_all(
		"CRM Form Template Service",
		filters={"parenttype": MODELLO, "parent": ("in", [r.name for r in righe] or [""])},
		fields=["parent", "service"],
	):
		servizi.setdefault(riga.parent, []).append(riga.service)
	versioni = {
		v.name: v
		for v in frappe.get_all(
			VERSIONE,
			filters={"name": ("in", [r.current_version for r in righe] or [""])},
			fields=["name", "version", "asked_from"],
		)
	}
	return [
		{
			"name": riga.name,
			"title": riga.title,
			"clinical": riga.clinical,
			"ask_on": riga.ask_on,
			"validity": riga.validity,
			"services": servizi.get(riga.name, []),
			"version": versioni[riga.current_version].version if riga.current_version in versioni else 0,
			"asked_from": versioni[riga.current_version].asked_from
			if riga.current_version in versioni
			else None,
			"send_before": riga.send_before,
		}
		for riga in righe
	]


def _firmati(persone: list[str]) -> dict[tuple[str, str], list[dict]]:
	"""Each person's signed forms, by template."""
	firmati: dict[tuple[str, str], list[dict]] = {}
	for riga in frappe.get_all(
		MODULO,
		filters={"lead": ("in", persone or [""]), "docstatus": 1},
		fields=["lead", "template", "version", "signed_on", "appointment"],
	):
		firmati.setdefault((riga.lead, riga.template), []).append(riga)
	return firmati


def _in_corso(persone: list[str]) -> dict[tuple[str, str], str]:
	"""What is already under way for a person and a template: a draft being
	filled, or a link sent and not yet back."""
	in_corso: dict[tuple[str, str], str] = {}
	for riga in frappe.get_all(
		MODULO, filters={"lead": ("in", persone or [""]), "docstatus": 0}, fields=["lead", "template"]
	):
		in_corso[(riga.lead, riga.template)] = "draft"
	for riga in frappe.get_all(
		RICHIESTA,
		filters={
			"lead": ("in", persone or [""]),
			"status": ("in", ("Sent", "Opened", "Filled")),
			"expires_on": (">", now_datetime()),
		},
		fields=["lead", "template", "status"],
	):
		in_corso[(riga.lead, riga.template)] = "to_sign_at_desk" if riga.status == "Filled" else "sent"
	return in_corso


def dovuti(
	persone: list[str], appuntamenti: dict[str, dict | None], *, clinici: bool
) -> dict[str, list[dict]]:
	"""What each person owes: for the appointment given for them (or in general),
	with why, and whether something is already under way. The forms with health
	data only for whoever reads them (``clinici``)."""
	modelli = [m for m in modelli_che_si_chiedono() if clinici or not m["clinical"]]
	if not modelli or not persone:
		return {persona: [] for persona in persone}
	firmati = _firmati(persone)
	in_corso = _in_corso(persone)
	oggi = getdate()
	risposta: dict[str, list[dict]] = {}
	for persona in persone:
		appuntamento = appuntamenti.get(persona)
		voci = []
		for modello in modelli:
			if guardie.solo_per_la_demo(MODELLO, modello["name"], persona):
				continue
			motivo = dovuto(modello, firmati.get((persona, modello["name"]), []), appuntamento, oggi)
			if motivo:
				voci.append(
					{
						"template": modello["name"],
						"title": modello["title"],
						"clinical": modello["clinical"],
						"reason": motivo,
						"pending": in_corso.get((persona, modello["name"])),
						"appointment": appuntamento.get("name") if appuntamento else None,
					}
				)
		risposta[persona] = voci
	return risposta


def prossimo_appuntamento(lead: str) -> dict | None:
	"""The person's next appointment, from today: what their forms are asked for."""
	inizio = datetime.datetime.combine(getdate(), datetime.time.min)
	righe = frappe.db.sql(
		"""
		select a.name, a.service, a.starts_on
		from `tabCRM Appointment` a
		join `tabCRM Appointment Participant` p on p.parent = a.name and p.parenttype = 'CRM Appointment'
		where p.party_type = 'CRM Lead' and p.party = %(lead)s and p.status != 'Cancelled'
			and a.status != 'Cancelled' and a.starts_on >= %(inizio)s
		order by a.starts_on asc
		limit 1
		""",
		{"lead": lead, "inizio": inizio},
		as_dict=True,
	)
	return righe[0] if righe else None


def della_persona(lead: str) -> dict:
	"""The person's owed forms, for their next appointment (or in general)."""
	from crm.moduli import compilazioni

	appuntamento = prossimo_appuntamento(lead)
	voci = dovuti([lead], {lead: appuntamento}, clinici=compilazioni.legge_dati_clinici())[lead]
	return {
		"appointment": {"name": appuntamento.name, "starts_on": get_datetime(appuntamento.starts_on)}
		if appuntamento
		else None,
		"forms": voci,
	}


def nel_riepilogo(lead: str) -> dict | None:
	"""For the person's summary (`crm.persone.riepilogo`): the forms they owe for
	their next appointment, or in general - for whoever reads a person's forms."""
	from crm.permissions import livelli

	if not livelli.puo("moduli.vedi"):
		return None
	ora = della_persona(lead)
	return ora if ora["forms"] else None


# ------------------------------------------------------------------ with the booking

#: A link that leaves this close to the visit would not be filled at home.
ORE_PRIMA = 1


def appuntamento_prenotato(doc, method=None) -> None:
	"""An appointment was booked: the forms the templates say to send go by link,
	once the booking is saved (and in a job: the booking does not wait for mail)."""
	if doc.get("status") == "Cancelled" or not any(m["send_before"] for m in modelli_che_si_chiedono()):
		return
	frappe.enqueue(
		"crm.moduli.dovuti.manda_con_la_prenotazione",
		appuntamento=doc.name,
		enqueue_after_commit=True,
		now=frappe.in_test,
	)


def manda_con_la_prenotazione(appuntamento: str) -> None:
	"""The link to the forms each person of the appointment owes for it, of the
	templates that send it: one email a person, until the visit starts. What was
	sent already and is still open is not sent again; nobody without an address
	gets anything."""
	from crm.moduli import richieste

	doc = frappe.get_doc("CRM Appointment", appuntamento)
	if doc.status == "Cancelled":
		return
	if get_datetime(doc.starts_on) < frappe.utils.add_to_date(now_datetime(), hours=ORE_PRIMA):
		return
	da_mandare = {m["name"] for m in modelli_che_si_chiedono() if m["send_before"]}
	persone = [
		p.party
		for p in doc.participants
		if p.party_type == "CRM Lead" and p.party and p.status != "Cancelled"
	]
	# whoever booked it, when a person of the centre did; else the centre itself
	mittente = doc.owner if doc.owner not in ("Guest", "Administrator") else "Administrator"
	per_chi = {persona: {"name": doc.name, "service": doc.service} for persona in persone}
	for persona, voci in dovuti(persone, per_chi, clinici=True).items():
		modelli = [v["template"] for v in voci if v["template"] in da_mandare and not v["pending"]]
		if not modelli:
			continue
		dove = richieste.destinatario(persona)
		if not dove.get("email"):
			continue
		try:
			richieste.manda_il_link(
				persona,
				modelli,
				dove,
				scadenza=get_datetime(doc.starts_on),
				appointment=doc.name,
				mittente=mittente,
				dal_centro=True,
			)
		except Exception:
			frappe.log_error(
				title=f"Forms not sent with appointment {doc.name}",
				reference_doctype="CRM Appointment",
				reference_name=doc.name,
			)
