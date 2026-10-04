# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The demo's waiting list (Agenda > Waiting list): who waits for a place with the
osteopath, the dietitian, a Saturday morning, a seat in the class that is full.

Through the list's own engine: a person joins with the days that suit them; the
engine's look finds a free place and offers it (the offer goes to nobody:
`crm.demo.guardie`); one offer is still waiting for its answer, two were confirmed
and booked; one person found a place elsewhere and left the list, one's days ran
out. The next look of the centre's scheduler goes on from there, as it would.
"""

from __future__ import annotations

import datetime

import frappe
from frappe import _

from crm.demo import dati
from crm.demo.contesto import Contesto
from crm.demo.simulazione import persone_della_demo

VOCE = "CRM Waiting List Entry"
APPUNTAMENTO = "CRM Appointment"


def crea(ctx: Contesto) -> None:
	from crm.scheduling import attese

	desk = ctx.squadra("desk") or ctx.utente
	ctx.avanza(_("Waiting list"))
	conf = attese.impostazioni()
	canali = attese.canali_offerti(conf)
	liberi = _chi_puo_aspettare(ctx)
	for (
		servizio,
		chi,
		giorni,
		urgente,
		fonte,
		nota,
		fa,
		esito,
	) in dati.ATTESE[: ctx.quanti(len(dati.ATTESE))]:
		codice = ctx.trova(f"service.{servizio}")
		if not codice or not liberi:
			continue
		lead = liberi.pop(0)
		entrata = _entrata(ctx, fa)
		email, cellulare = frappe.db.get_value("CRM Lead", lead, ["email", "mobile_no"])
		with ctx.come(desk):
			voce = attese.entra(
				lead,
				codice,
				staff=ctx.squadra(chi) if chi else None,
				righe=[{"workday": g, "start_time": dalle, "end_time": alle} for g, dalle, alle in giorni],
				dal=entrata.date(),
				fino=entrata.date() + datetime.timedelta(days=conf.giorni_online if fonte != "Desk" else 45),
				canale=ctx.rng.choice(canali),
				fonte=fonte,
				urgente=urgente,
				note=nota,
				email=email,
				telefono=cellulare,
				ignora_permessi=True,
			)
		ctx.retrodata(VOCE, voce.name, entrata, desk if fonte == "Desk" else "Administrator")
		_come_e_andata(ctx, voce.name, esito, entrata, conf, desk)
	_la_lezione_piena(ctx, conf, canali, desk)


def _chi_puo_aspettare(ctx: Contesto) -> list[str]:
	"""People with nothing booked ahead: the requests not come yet first, then the
	clients - the ones a waiting list is for."""
	persone = persone_della_demo(ctx)
	if not persone:
		return []
	prenotati = {
		riga[0]
		for riga in frappe.db.sql(
			"""select distinct p.party from `tabCRM Appointment Participant` p
			join `tabCRM Appointment` a on a.name = p.parent
			where p.parenttype = 'CRM Appointment' and p.party in %(persone)s
				and a.starts_on >= %(adesso)s and a.status != 'Cancelled'""",
			{"persone": persone, "adesso": ctx.adesso},
		)
	}
	liberi = [p for p in persone if p not in prenotati]
	clienti = set(
		frappe.get_all(
			"CRM Lead", filters={"name": ["in", liberi or [""]], "client_since": ["is", "set"]}, pluck="name"
		)
	)
	richieste = [p for p in liberi if p not in clienti]
	ctx.rng.shuffle(richieste)
	gia = sorted(clienti)
	ctx.rng.shuffle(gia)
	# a request and a client in turn
	ordine = []
	while richieste or gia:
		for gruppo in (richieste, gia):
			if gruppo:
				ordine.append(gruppo.pop())
	return ordine


def _entrata(ctx: Contesto, fa: int) -> datetime.datetime:
	"""When somebody joined ``fa`` days ago: in the centre's hours, never in the future."""
	giorno = ctx.giorno(-fa)
	quando = ctx.alle(giorno, f"{ctx.rng.randint(9, 18):02d}:{ctx.rng.choice((5, 20, 35, 50)):02d}")
	return min(quando, ctx.adesso - datetime.timedelta(minutes=ctx.rng.randint(20, 90)))


def _come_e_andata(ctx: Contesto, nome: str, esito: str | None, entrata, conf, desk: str) -> None:
	from crm.scheduling import attese
	from crm.scheduling import attese_regole as R

	if not esito:
		return
	voce = frappe.get_doc(VOCE, nome)
	if esito == "removed":
		with ctx.come(desk):
			attese.togli(voce)
		_chiusa_il(nome, entrata + datetime.timedelta(days=ctx.rng.randint(2, 6), hours=2), ctx)
		return
	if esito == "expired":
		voce.db_set("until", ctx.giorno(-3), update_modified=False)
		attese._chiudi(frappe.get_doc(VOCE, nome), R.SCADUTA)
		_chiusa_il(nome, ctx.alle(ctx.giorno(-2), "00:10"), ctx)
		return
	# the engine's look: the first free place that suits them
	oggi = attese._oggi()
	posti = attese.Sguardo(conf, oggi, oggi + datetime.timedelta(days=conf.giorni)).posti(voce)
	if not posti:
		return
	with ctx.come(desk), ctx.nella_lingua_del_centro():
		attese.offri(voce, posti[0], da=None, conf=conf)
	if esito != "booked":
		return
	voce = frappe.get_doc(VOCE, nome)
	riga = next(r for r in voce.offers if r.status == R.INVIATA)
	with ctx.nella_lingua_del_centro():
		esito_conferma = attese.conferma(voce, riga, fonte=R.ONLINE)
	appuntamento = esito_conferma.get("appointment")
	# offered last night, confirmed a few minutes later
	inviata = min(ctx.alle(ctx.giorno(-1), "18:40"), ctx.adesso - datetime.timedelta(hours=2))
	risposta = inviata + datetime.timedelta(minutes=ctx.rng.randint(6, 40))
	frappe.db.set_value(
		"CRM Waiting List Offer",
		riga.name,
		{"sent_on": inviata, "answered_on": risposta},
		update_modified=False,
	)
	_chiusa_il(nome, risposta, ctx)
	if appuntamento:
		ctx.retrodata(APPUNTAMENTO, appuntamento, risposta, "Administrator")


def _chiusa_il(nome: str, quando: datetime.datetime, ctx: Contesto) -> None:
	quando = min(quando, ctx.adesso)
	frappe.db.set_value(VOCE, nome, {"closed_on": quando, "modified": quando}, update_modified=False)


def _la_lezione_piena(ctx: Contesto, conf, canali: list[str], desk: str) -> None:
	"""The busiest class of the coming week fills up with the regulars of the others,
	and two people wait for a seat in it."""
	from crm.scheduling import attese

	pilates = ctx.trova("service.pilates")
	persone = persone_della_demo(ctx)
	if not pilates or not persone:
		return
	posti = frappe.db.get_value("CRM Service", pilates, "max_participants") or 0
	lezioni = frappe.get_all(
		APPUNTAMENTO,
		filters={
			"service": pilates,
			"status": ["!=", "Cancelled"],
			"starts_on": [
				"between",
				[ctx.adesso + datetime.timedelta(hours=20), ctx.adesso + datetime.timedelta(days=7)],
			],
		},
		pluck="name",
		order_by="starts_on asc",
	)
	if not lezioni or posti < 2:
		return
	lezione = max(lezioni, key=lambda nome: len(_presenti(nome)))
	dentro = set(_presenti(lezione))
	# who else comes to Pilates on other days
	altri = [
		riga[0]
		for riga in frappe.db.sql(
			"""select p.party from `tabCRM Appointment Participant` p
			join `tabCRM Appointment` a on a.name = p.parent
			where p.parenttype = 'CRM Appointment' and a.service = %(pilates)s
				and p.party in %(persone)s and p.status != 'Cancelled'
			group by p.party order by count(*) desc, p.party""",
			{"pilates": pilates, "persone": persone},
		)
		if riga[0] not in dentro
	]
	doc = frappe.get_doc(APPUNTAMENTO, lezione)
	while len(dentro) < posti and altri:
		lead = altri.pop(0)
		doc.append(
			"participants",
			{
				"party_type": "CRM Lead",
				"party": lead,
				"participant_name": frappe.db.get_value("CRM Lead", lead, "lead_name") or lead,
				"status": "Booked",
			},
		)
		dentro.add(lead)
	with ctx.come(desk):
		doc.save(ignore_permissions=True)
	for _volta in range(ctx.quanti(dati.IN_ATTESA_DELLA_LEZIONE)):
		if not altri:
			break
		lead = altri.pop(0)
		email, cellulare = frappe.db.get_value("CRM Lead", lead, ["email", "mobile_no"])
		with ctx.come(desk):
			voce = attese.entra(
				lead,
				pilates,
				lezione=lezione,
				canale=ctx.rng.choice(canali),
				fonte=ctx.rng.choice(("Online", "Client area")),
				email=email,
				telefono=cellulare,
				ignora_permessi=True,
			)
		ctx.retrodata(VOCE, voce.name, _entrata(ctx, ctx.rng.randint(0, 2)), "Administrator")


def _presenti(appuntamento: str) -> list[str]:
	return frappe.get_all(
		"CRM Appointment Participant",
		filters={
			"parenttype": APPUNTAMENTO,
			"parent": appuntamento,
			"party_type": "CRM Lead",
			"status": ["!=", "Cancelled"],
		},
		pluck="party",
	)
