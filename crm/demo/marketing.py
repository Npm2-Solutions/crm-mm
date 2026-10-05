# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The demo's marketing (doc 53), with the plan's "marketing" module: the
automations, the social planner, the tracked links. Meta's ads are a part of their
own (`crm.demo.meta`), made before the people they bring.

- Four automations, written by the manager through the builder's own call
  (`crm.api.automation.save_automation`) and switched off: switched on, an
  automation listens to everything the centre does and would write to its real
  people, so the centre switches on the ones it keeps. What they did in the story is
  there, at the moment it happened, through the engine (`enroll`,
  `advance_enrollment`): the welcome to each new client; the recall of who has not
  come back in two months, if they said yes to marketing (the others skipped, as the
  engine skips them); the call back to who filled a form; the email after a missed
  appointment. The tasks they left are done, but the last days'.
- The centre's Instagram and Facebook profiles, with the posts of the last weeks
  published and the next ones scheduled, and a draft. Made only where the centre has
  no profile of its own; a demo post is never handed to a network
  (`guardie.mai_fuori`): at its time it is marked published, as a demo SMS is kept
  as sent.
- Two tracked links and their clicks.
"""

from __future__ import annotations

import datetime

import frappe
from frappe import _

from crm.demo import dati, registro
from crm.demo.contesto import Contesto, nome_libero
from crm.demo.simulazione import GIORNI_INDIETRO, persone_della_demo

AUTOMAZIONE = "CRM Automation"
ISCRIZIONE = "CRM Automation Enrollment"
PASSO = "CRM Automation Step Log"
COMPITO = "CRM Task"
PROFILO = "CRM Social Account"
POST = "CRM Social Post"
LINK = "CRM Tracked Link"
#: A task an automation left is still to do when it is this recent; the older ones
#: the desk has done.
GIORNI_DA_FARE = 3


def crea(ctx: Contesto) -> None:
	ctx.avanza(_("Marketing"))
	manager = ctx.squadra("manager") or ctx.utente
	desk = ctx.squadra("desk") or ctx.utente
	automazioni = {}
	with ctx.come(manager):
		for chiave, titolo, descrizione, evento, impostazioni, consenso, passi in dati.AUTOMAZIONI:
			automazioni[chiave] = _automazione(
				ctx, manager, chiave, titolo, descrizione, evento, impostazioni, consenso, passi
			)
	ctx.salva()
	_storia(ctx, automazioni, desk)
	ctx.salva()
	_social(ctx, manager)
	ctx.salva()
	_link(ctx, manager)


# -- the automations ----------------------------------------------------------------------------


def _automazione(
	ctx: Contesto,
	manager: str,
	chiave: str,
	titolo: str,
	descrizione: str,
	evento: str,
	impostazioni: dict | None,
	consenso: bool,
	passi: tuple[dict, ...],
) -> str:
	"""Written in the builder, and left switched off."""
	from crm.api import automation

	fatta = ctx.trova(f"automation.{chiave}")
	if fatta:
		# made again after a try that stopped half-way: the same automation goes on
		return fatta
	esito = automation.save_automation(
		{
			"title": nome_libero(AUTOMAZIONE, titolo),
			"description": descrizione,
			"trigger_event": evento,
			"trigger_config": impostazioni,
			"marketing_consent": consenso,
			"steps": [dict(passo) for passo in passi],
		}
	)
	nome = esito.get("name")
	ctx.ricorda(AUTOMAZIONE, nome, f"automation.{chiave}")
	ctx.retrodata(AUTOMAZIONE, nome, ctx.alle(ctx.giorno(-GIORNI_INDIETRO - 10), "11:00"), manager)
	return nome


def _storia(ctx: Contesto, automazioni: dict[str, str], desk: str) -> None:
	"""Whoever went through each automation in the story, when they did."""
	persone = persone_della_demo(ctx)
	if not persone:
		return
	passaggi: list[tuple[datetime.datetime, str, str]] = []
	if automazioni.get("benvenuto"):
		for persona, momento in frappe.get_all(
			"CRM Lead",
			filters={"name": ["in", persone], "client_since": ["is", "set"]},
			fields=["name", "client_since"],
			as_list=True,
		):
			# an hour after the visit that made them a client
			quando = frappe.utils.get_datetime(momento) + datetime.timedelta(hours=1)
			passaggi.append((quando, automazioni["benvenuto"], persona))
	if automazioni.get("richiamo"):
		for persona, giorno in frappe.get_all(
			"CRM Lead",
			# an empty date counts as the smallest: who never came is not recalled
			filters=[
				["name", "in", persone],
				["last_visit", "is", "set"],
				["last_visit", "<=", ctx.giorno(-60)],
			],
			fields=["name", "last_visit"],
			as_list=True,
		):
			passaggi.append(
				(ctx.alle(giorno + datetime.timedelta(days=60), "09:15"), automazioni["richiamo"], persona)
			)
	if automazioni.get("richiesta"):
		for persona, creata in _da_un_modulo(ctx, persone):
			passaggi.append((creata + datetime.timedelta(minutes=1), automazioni["richiesta"], persona))
	if automazioni.get("assenza"):
		for persona, fine in _assenti(persone):
			passaggi.append((fine + datetime.timedelta(minutes=40), automazioni["assenza"], persona))
	inizi = {}
	for quando, automazione, persona in sorted(passaggi):
		quando = min(quando, ctx.adesso - datetime.timedelta(minutes=5)).replace(microsecond=0)
		_passa(ctx, automazione, persona, quando, desk, inizi)


def _da_un_modulo(ctx: Contesto, persone: list[str]) -> list[tuple[str, datetime.datetime]]:
	"""Who filled a lead form of Meta or a form of the website, when they did."""
	trovati = {
		riga.name: riga.creation
		for riga in frappe.get_all(
			"CRM Lead",
			filters={"name": ["in", persone], "facebook_lead_id": ["is", "set"]},
			fields=["name", "creation"],
		)
	}
	for riga in frappe.get_all(
		"CRM Form",
		filters={"lead": ["in", persone], "channel": "Website"},
		fields=["lead", "creation"],
	):
		trovati.setdefault(riga.lead, riga.creation)
	return sorted(trovati.items())


def _assenti(persone: list[str]) -> list[tuple[str, datetime.datetime]]:
	"""Who missed an appointment, at its end: each person once, the last time."""
	assenze = {}
	for riga in frappe.db.sql(
		"""select p.party, a.ends_on from `tabCRM Appointment` a
		join `tabCRM Appointment Participant` p on p.parent = a.name and p.parenttype = 'CRM Appointment'
		where p.party_type = 'CRM Lead' and p.party in %(persone)s and p.status = 'No Show'
		order by a.ends_on""",
		{"persone": persone},
		as_dict=True,
	):
		assenze[riga.party] = riga.ends_on
	return sorted(assenze.items())


def _passa(
	ctx: Contesto, automazione: str, persona: str, quando: datetime.datetime, desk: str, inizi: dict
) -> None:
	"""``persona`` goes through ``automazione`` at ``quando``: the engine enrolls them
	and runs the steps; what they made is dated then."""
	from crm.automation import engine

	if automazione not in inizi:
		inizi[automazione] = frappe.get_doc(AUTOMAZIONE, automazione).triggers[0]
	prima = frappe.utils.now_datetime()
	iscrizione = engine.enroll(automazione, "CRM Lead", persona, payload={}, trigger_row=inizi[automazione])
	if not iscrizione:
		# skipped for want of the yes: the engine wrote it down already
		iscrizione = frappe.db.get_value(
			ISCRIZIONE,
			{"automation": automazione, "reference_name": persona, "creation": [">=", prima]},
			"name",
		)
		if iscrizione:
			_data(ctx, iscrizione, quando)
		return
	engine.advance_enrollment(iscrizione)
	_data(ctx, iscrizione, quando)
	for compito in frappe.get_all(
		COMPITO,
		filters={"reference_docname": persona, "creation": [">=", prima]},
		fields=["name", "due_date", "creation"],
	):
		_compito(ctx, compito, quando, desk)


def _data(ctx: Contesto, iscrizione: str, quando: datetime.datetime) -> None:
	ctx.retrodata(ISCRIZIONE, iscrizione, quando)
	frappe.db.sql(
		"update `tabCRM Automation Step Log` set creation=%s, modified=%s where parent=%s",
		(quando, quando, iscrizione),
	)


def _compito(ctx: Contesto, compito, quando: datetime.datetime, desk: str) -> None:
	"""A task the automation left: due when it said, done by the desk unless recent."""
	# the engine gives it its days from the moment it ran
	giorni = round(
		(
			frappe.utils.get_datetime(compito.due_date) - frappe.utils.get_datetime(compito.creation)
		).total_seconds()
		/ 86400
	)
	scadenza = quando + datetime.timedelta(days=giorni)
	ctx.retrodata(COMPITO, compito.name, quando)
	frappe.db.set_value(COMPITO, compito.name, "due_date", scadenza, update_modified=False)
	if quando.date() < ctx.giorno(-GIORNI_DA_FARE):
		doc = frappe.get_doc(COMPITO, compito.name)
		doc.status = "Done"
		with ctx.come(desk):
			doc.save(ignore_permissions=True)
		frappe.db.set_value(
			COMPITO,
			compito.name,
			"modified",
			min(scadenza, ctx.adesso),
			update_modified=False,
		)


# -- the social planner -------------------------------------------------------------------------


def _social(ctx: Contesto, manager: str) -> None:
	"""The centre's profiles and their posts, where the centre has none of its own."""
	from crm.api import social
	from crm.moduli.richieste import nome_del_centro
	from crm.social import accounts, publisher

	if _profili_del_centro():
		# the centre posts on its own profiles: the demo writes on none of them
		return
	if ctx.trova("social.instagram") or ctx.trova("social.facebook"):
		# made by a try that stopped half-way, which got this far
		return
	centro = nome_del_centro() or "Centro"
	pagina = ctx.trova("meta.pagina")
	profili = {}
	for piattaforma in dati.PROFILI_SOCIAL:
		codice = str(ctx.rng.randint(10**15, 10**16 - 1))
		accounts.upsert_account(piattaforma, codice, f"{centro} · {piattaforma} (dati di prova)", pagina)
		profilo = frappe.db.get_value(
			PROFILO, {"platform": piattaforma, "provider_account_id": codice}, "name"
		)
		ctx.ricorda(PROFILO, profilo, f"social.{piattaforma.lower()}")
		ctx.retrodata(PROFILO, profilo, ctx.alle(ctx.giorno(-GIORNI_INDIETRO - 10), "11:30"), manager)
		profili[piattaforma] = profilo
	with ctx.come(manager):
		for giorni, ora, parole, dove in dati.POST_SOCIAL:
			quando = ctx.alle(ctx.giorno(giorni), ora)
			post = social.save_post(
				{
					"content": parole,
					"scheduled_at": str(quando),
					"status": "Scheduled",
					"targets": [{"account": profili[p]} for p in dove if p in profili],
				}
			)["name"]
			ctx.ricorda(POST, post, f"social.post.{giorni}")
			scritto = min(quando - datetime.timedelta(days=4), ctx.adesso - datetime.timedelta(hours=2))
			ctx.retrodata(POST, post, scritto, manager)
			if quando < ctx.adesso:
				# its time came: the planner published it, as it publishes a demo post
				publisher.publish_post(post)
				frappe.db.set_value(
					POST, post, {"published_at": quando, "modified": quando}, update_modified=False
				)
		bozza = social.save_post(
			{
				"content": dati.POST_BOZZA,
				"status": "Draft",
				"targets": [{"account": profilo} for profilo in profili.values()],
			}
		)["name"]
		ctx.ricorda(POST, bozza, "social.bozza")
		ctx.retrodata(POST, bozza, ctx.adesso - datetime.timedelta(hours=3), manager)


def _profili_del_centro() -> bool:
	"""Whether the centre has a social profile of its own."""
	return bool(set(frappe.get_all(PROFILO, pluck="name")) - registro.nomi_di_prova(PROFILO))


# -- the tracked links --------------------------------------------------------------------------


def _link(ctx: Contesto, manager: str) -> None:
	"""The links whose clicks the centre counts, clicked as people clicked them."""
	from crm.api import links

	fatti = []
	for slug, dove, descrizione, clic in dati.LINK_TRACCIATI:
		if frappe.db.exists(LINK, slug):
			# the centre's own: the demo never counts on it
			continue
		with ctx.come(manager):
			frappe.get_doc(
				{
					"doctype": LINK,
					"slug": slug,
					"target_url": frappe.utils.get_url(dove),
					"description": descrizione,
				}
			).insert()
		ctx.ricorda(LINK, slug, f"link.{slug}")
		ctx.retrodata(LINK, slug, ctx.alle(ctx.giorno(-GIORNI_INDIETRO + 10), "10:00"), manager)
		fatti.append((slug, clic))
	# a click is counted and committed by itself: the links are written down first
	ctx.salva()
	for slug, clic in fatti:
		for _volta in range(ctx.quanti(clic)):
			links.r(slug)
