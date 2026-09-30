# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What the CRM itself brings to the registry: its plan modules, levels, roles and
capabilities.

The matrix is doc 30's (`docs/progetto-ghl/30-ruoli-e-permessi.md`), column by
column. Invoicing adds its own capabilities from `crm.invoicing`, and the clinic
will add its levels and capabilities from its own module: this file never names
them.

Pure data, so `test_livelli.py` proves the matrix with no site.
"""

from __future__ import annotations

from crm.permissions.livelli import (
	A_SCELTA,
	CENTRO,
	LIBERO_OCCUPATO,
	MASCHERATO,
	RUOLI_AGENZIA,
	RUOLI_AUTOMATICI,
	RUOLO_RECAPITI,
	SOLA_LETTURA_LIVELLO,
	SUOI,
	TEAM,
	Capacita,
	Livello,
	ModuloPiano,
	concedi,
	registra_capacita,
	registra_livello,
	registra_livello_implicito,
	registra_modulo_piano,
	registra_requisito,
	registra_ruolo,
	ruoli_del_livello,
	ruoli_registrati,
)

# Level keys, used across modules.
SEGRETERIA = "segreteria"
OPERATORE = "operatore"
MANAGER = "manager"
COMMERCIALE = "commerciale"
# the optional levels of PR 4. The Marketing level shares its key with the plan
# module it belongs to: they live in two registries
LIV_MARKETING = "marketing"
AMMINISTRAZIONE = "amministrazione"
SOLA_LETTURA = SOLA_LETTURA_LIVELLO

# Plan modules the CRM already had before plans existed: on unless the plan says
# otherwise, so no site loses anything the day plans arrive.
BASE = "base"
MARKETING = "marketing"
TELEFONO = "telefono"

MODULI = (
	ModuloPiano(
		BASE,
		"Base",
		descrizione="People and agenda with rooms, online booking and platforms, reminders, "
		"conversations, invoices and Sistema TS, dashboards, users and levels",
		ordine=1,
	),
	ModuloPiano(
		MARKETING,
		"Marketing",
		descrizione="Automations, campaigns, Meta leads and spend, social, tracking, "
		"cost per new client, the website",
		ordine=3,
	),
	ModuloPiano(
		TELEFONO,
		"Phone",
		descrizione="Calls from the browser, the dialer, recordings and transcripts",
		ordine=4,
	),
)

LIVELLI = (
	(
		Livello(
			SEGRETERIA,
			"CRM Front Desk",
			"Front Desk",
			"Front desk and phone: everyone's agenda, people, conversations, arrivals, "
			"invoices and payments.",
			ordine=1,
		),
		("Sales User", "Front Desk"),
	),
	(
		Livello(
			OPERATORE,
			"CRM Practitioner",
			"Practitioner",
			"Doctor, nutritionist, physiotherapist, trainer: their own agenda, their clients or "
			"patients, their messages. Does not see the settings or the centre's numbers.",
			ordine=2,
		),
		("Sales User", "Practitioner"),
	),
	(
		Livello(
			MANAGER,
			"CRM Manager",
			"Manager",
			"Owner or manager of the centre: all of its work, the settings, users and levels, "
			"the numbers. Does not touch the site itself: keys, domains, installed apps.",
			ordine=3,
			desk=True,
		),
		("Sales User", "Sales Manager"),
	),
	(
		Livello(
			COMMERCIALE,
			"CRM Sales",
			"Sales",
			"Sells packages, quotes and memberships: their requests and deals, or their team's.",
			base=False,
			ordine=4,
		),
		("Sales User",),
	),
	(
		Livello(
			LIV_MARKETING,
			"CRM Marketing",
			"Marketing",
			"Campaigns, social, ads, tracking and automations, also the agency's: people "
			"with email and phone masked, no conversations.",
			base=False,
			piano=MARKETING,
			ordine=5,
			recapiti=False,
		),
		("Sales User", "Marketing"),
	),
	(
		Livello(
			AMMINISTRAZIONE,
			"CRM Accounting",
			"Accounting",
			"Accounting, in house or outside: invoices, the Sistema TS, payments, exports; "
			"people and the agenda to read.",
			base=False,
			ordine=6,
		),
		("Sales User",),
	),
	(
		Livello(
			SOLA_LETTURA,
			"CRM Read Only",
			"Read only",
			"Added to another level, takes every write away: an auditor, a consultant, a "
			"trainee at the start.",
			base=False,
			ordine=9,
			recapiti=False,
			aggiuntivo=True,
		),
		(),
	),
)

#: Roles the CRM brings, and what they are for. The roles are never shown: people
#: get levels.
RUOLI = (
	# (role, what it is for, whether Frappe creates it by itself)
	("System Manager", "Manages the site: the agency.", True),
	("Sales Manager", "Configures the CRM: pipelines, views, services, users.", True),
	("Sales User", "Works on people, deals, conversations and the agenda.", True),
	("Front Desk", "Front desk: sees the whole centre's people and agenda.", False),
	("Practitioner", "Sees their own agenda, clients or patients.", False),
	("Marketing", "Configures automations, social, Meta, tracking and forms.", False),
)

#: Users from before levels, by their widest role. The migration gives them
#: explicit levels; until then, and for users it leaves alone, this is what counts.
IMPLICITI = (
	("Sales Manager", MANAGER),
	("Sales User", COMMERCIALE),
)


def _c(nome, piano=BASE, scrive=True, descrizione="", requisito=None, **livelli):
	return Capacita(nome, piano=piano, scrive=scrive, descrizione=descrizione, requisito=requisito), livelli


def builder_installato() -> bool:
	"""Whether Frappe Builder is on this bench: installing it is the agency's job, not
	a switch the centre has, so without it the site pages are nobody's."""
	import frappe

	return "builder" in frappe.get_installed_apps()


CAPACITA = (
	# People, requests and deals
	_c("persone.vedi", scrive=False, segreteria=CENTRO, operatore=SUOI, manager=CENTRO, commerciale=TEAM),
	_c("persone.scrivi", segreteria=CENTRO, operatore=SUOI, manager=CENTRO, commerciale=TEAM),
	_c("persone.dati_fiscali", segreteria=CENTRO, operatore=SUOI, manager=CENTRO),
	_c("persone.elimina", manager=CENTRO, descrizione="Also for the right to be forgotten"),
	_c("persone.assegna", segreteria=CENTRO, manager=CENTRO, commerciale=TEAM),
	_c("persone.unisci", segreteria=CENTRO, manager=CENTRO),
	_c("persone.importa", manager=CENTRO),
	_c("persone.esporta", scrive=False, manager=CENTRO),
	# Consents: who agreed to what. Whoever hears "stop writing to me" records it
	_c("consensi.vedi", scrive=False, segreteria=CENTRO, operatore=SUOI, manager=CENTRO, commerciale=TEAM),
	_c(
		"consensi.raccogli",
		segreteria=CENTRO,
		operatore=SUOI,
		manager=CENTRO,
		commerciale=TEAM,
		descrizione="Record an answer given at the desk, on paper, by phone; record a withdrawal",
	),
	_c("consensi.configura", manager=CENTRO, descrizione="The kinds of consent and their texts"),
	# Forms to fill and sign (docs/gestionale-medico, phase 2): what they ask, in versions
	_c("moduli.configura", manager=CENTRO, descrizione="The centre's form templates and their versions"),
	# a person's forms follow the person, like their consents
	_c("moduli.vedi", scrive=False, segreteria=CENTRO, operatore=SUOI, manager=CENTRO, commerciale=TEAM),
	_c(
		"moduli.compila",
		segreteria=CENTRO,
		operatore=SUOI,
		manager=CENTRO,
		commerciale=TEAM,
		descrizione="Fill a form with a person and have it signed",
	),
	_c("trattative.vedi", scrive=False, segreteria=CENTRO, operatore=SUOI, manager=CENTRO, commerciale=TEAM),
	_c("trattative.scrivi", segreteria=CENTRO, manager=CENTRO, commerciale=TEAM),
	_c("pipeline.configura", manager=CENTRO),
	_c("viste.configura", manager=CENTRO, descrizione="Public views, quick filters, card fields"),
	# Conversations
	# reading apart from writing, as for people and deals: Read only keeps the first
	_c(
		"conversazioni.vedi",
		scrive=False,
		segreteria=CENTRO,
		operatore=SUOI,
		manager=CENTRO,
		commerciale=TEAM,
		descrizione="Read email, WhatsApp and SMS",
	),
	_c(
		"conversazioni.usa",
		segreteria=CENTRO,
		operatore=SUOI,
		manager=CENTRO,
		commerciale=TEAM,
		descrizione="Write and answer email, WhatsApp and SMS",
	),
	_c(
		"note.vedi",
		scrive=False,
		segreteria=CENTRO,
		operatore=SUOI,
		manager=CENTRO,
		commerciale=TEAM,
		descrizione="Read internal notes",
	),
	_c("note.scrivi", segreteria=CENTRO, operatore=SUOI, manager=CENTRO, commerciale=TEAM),
	_c("conversazioni.stato", segreteria=CENTRO, operatore=SUOI, manager=CENTRO, commerciale=TEAM),
	_c(
		"modelli_messaggio.usa",
		scrive=False,
		segreteria=CENTRO,
		operatore=CENTRO,
		manager=CENTRO,
		commerciale=CENTRO,
	),
	_c("modelli_messaggio.gestisci", manager=CENTRO),
	# Agenda and booking
	_c(
		"agenda.vedi",
		scrive=False,
		segreteria=CENTRO,
		operatore=SUOI,
		manager=CENTRO,
		commerciale=LIBERO_OCCUPATO,
	),
	_c("agenda.prenota", segreteria=CENTRO, operatore=SUOI, manager=CENTRO, commerciale=CENTRO),
	_c("agenda.elimina", manager=CENTRO),
	_c("agenda.sovrapponi", segreteria=A_SCELTA, manager=CENTRO, descrizione="Book over a conflict"),
	_c(
		"agenda.presenze",
		segreteria=CENTRO,
		operatore=SUOI,
		manager=CENTRO,
		descrizione="Arrived, done, no-show",
	),
	_c(
		"agenda.turni", segreteria=CENTRO, operatore=SUOI, manager=CENTRO, descrizione="Rota, holidays, rooms"
	),
	_c(
		"agenda.cicli",
		segreteria=CENTRO,
		operatore=SUOI,
		manager=CENTRO,
		descrizione="Cycles of sessions: sell, follow, close",
	),
	_c("agenda.configura", manager=CENTRO, descrizione="Services, price lists, studio hours and rules"),
	_c("prenotazione_online.configura", manager=CENTRO),
	_c("piattaforme.configura", manager=CENTRO, descrizione="MioDottore, Treatwell and the others"),
	_c("google_calendar.proprio", segreteria=CENTRO, operatore=CENTRO, manager=CENTRO, commerciale=CENTRO),
	# Dashboards and numbers
	_c("dashboard.personali", segreteria=CENTRO, operatore=CENTRO, manager=CENTRO, commerciale=CENTRO),
	_c("dashboard.condivise", manager=CENTRO),
	# reading them: Read only on top of the Manager keeps the Manager's numbers
	_c(
		"dashboard.centro",
		scrive=False,
		manager=CENTRO,
		descrizione="The centre's numbers and the managers' dashboards",
	),
	_c("numeri.operativi", scrive=False, segreteria=CENTRO, operatore=SUOI, manager=CENTRO, commerciale=TEAM),
	_c("numeri.economici", scrive=False, operatore=SUOI, manager=CENTRO),
	_c("dashboard.filtro_persona", scrive=False, manager=CENTRO, commerciale=TEAM),
	# Users and the centre's settings
	_c("profilo.proprio", segreteria=CENTRO, operatore=CENTRO, manager=CENTRO, commerciale=CENTRO),
	_c("utenti.gestisci", manager=CENTRO, descrizione="Invite, change level, disable"),
	_c("gerarchia.gestisci", manager=CENTRO),
	_c(
		"impostazioni.generali", manager=CENTRO, descrizione="Brand, general settings, calendar and reminders"
	),
	_c("assegnazione.regole", manager=CENTRO, descrizione="Assignment rules and SLA, without code"),
	_c("menu_utente.gestisci", manager=CENTRO),
	_c("email.account_centro", manager=CENTRO),
	_c("canali.configura", manager=CENTRO, descrizione="WhatsApp numbers and the centre's other channels"),
	_c("dati_prova.gestisci", manager=CENTRO),
	_c(
		"piano.vedi", scrive=False, manager=CENTRO, descrizione="The plan, its modules and this month's usage"
	),
	_c("piano.amplia", manager=CENTRO, descrizione="Start the trial of a module"),
	# Phone
	_c(
		"telefono.chiama",
		piano=TELEFONO,
		segreteria=CENTRO,
		operatore=CENTRO,
		manager=CENTRO,
		commerciale=CENTRO,
	),
	_c(
		"telefono.registro",
		piano=TELEFONO,
		scrive=False,
		segreteria=CENTRO,
		operatore=SUOI,
		manager=CENTRO,
		commerciale=TEAM,
	),
	_c(
		"telefono.registrazioni",
		piano=TELEFONO,
		scrive=False,
		segreteria=SUOI,
		operatore=SUOI,
		manager=CENTRO,
		commerciale=SUOI,
	),
	_c(
		"telefono.copioni_usa",
		piano=TELEFONO,
		scrive=False,
		segreteria=CENTRO,
		operatore=CENTRO,
		manager=CENTRO,
		commerciale=CENTRO,
	),
	_c("telefono.copioni_scrivi", piano=TELEFONO, manager=CENTRO),
	_c("telefono.configura", piano=TELEFONO, manager=CENTRO, descrizione="Answering, numbers, caller ID"),
	# Marketing and automations
	_c("automazioni.vedi", piano=MARKETING, scrive=False, manager=CENTRO, commerciale=CENTRO),
	_c("automazioni.gestisci", piano=MARKETING, manager=CENTRO),
	_c(
		"social.bozze",
		piano=MARKETING,
		descrizione="Write social drafts, for a manager to approve",
		segreteria=A_SCELTA,
		manager=CENTRO,
		commerciale=CENTRO,
	),
	_c("social.pubblica", piano=MARKETING, manager=CENTRO),
	_c(
		"meta.gestisci", piano=MARKETING, manager=CENTRO, descrizione="Pages, lead forms, spend, lead quality"
	),
	_c("tracciamento.gestisci", piano=MARKETING, manager=CENTRO, descrizione="Tracked links and tracking"),
	_c(
		"moduli_lead.gestisci",
		piano=MARKETING,
		manager=CENTRO,
		descrizione="The forms on the website, which find the person or make them",
	),
	_c("campagne.gestisci", piano=MARKETING, manager=CENTRO),
	_c("numeri.marketing", piano=MARKETING, scrive=False, manager=CENTRO),
	_c(
		"sito.gestisci",
		piano=MARKETING,
		requisito="builder",
		manager=CENTRO,
		descrizione="Pages, showcase and site settings: only where the website builder is installed",
	),
)

#: The optional levels, column by column (doc 30, PR 4). Marketing sees people with
#: email and phone masked and reads no conversation; Accounting reads people, deals
#: and the agenda, and does the invoices (invoicing gives it its own column).
DEL_MARKETING = {
	"persone.vedi": MASCHERATO,
	"persone.esporta": MASCHERATO,
	"trattative.vedi": CENTRO,
	"modelli_messaggio.usa": CENTRO,
	"modelli_messaggio.gestisci": CENTRO,
	"google_calendar.proprio": CENTRO,
	"automazioni.vedi": CENTRO,
	"automazioni.gestisci": CENTRO,
	"social.bozze": CENTRO,
	"social.pubblica": CENTRO,
	"meta.gestisci": CENTRO,
	"tracciamento.gestisci": CENTRO,
	"moduli_lead.gestisci": CENTRO,
	"campagne.gestisci": CENTRO,
	"dashboard.personali": CENTRO,
	"numeri.marketing": CENTRO,
	"sito.gestisci": CENTRO,
	"profilo.proprio": CENTRO,
}
DELL_AMMINISTRAZIONE = {
	"persone.vedi": CENTRO,
	"persone.dati_fiscali": CENTRO,
	"trattative.vedi": CENTRO,
	"agenda.vedi": CENTRO,
	"google_calendar.proprio": CENTRO,
	"dashboard.personali": CENTRO,
	"numeri.economici": CENTRO,
	"numeri.marketing": CENTRO,
	"profilo.proprio": CENTRO,
}

#: The agency's: keys, webhooks, raw logs, code, the plan. Never a level's.
TECNICHE = (
	Capacita("piano.gestisci", agenzia=True, descrizione="The centre's plan"),
	Capacita("tecnico.integrazioni", agenzia=True, descrizione="App credentials, webhooks, IDs, raw logs"),
	Capacita("tecnico.utenti_agenzia", agenzia=True, descrizione="The agency's own users"),
	Capacita("tecnico.erpnext", agenzia=True),
	Capacita("tecnico.predefiniti", agenzia=True, descrizione="Site currency and formats"),
	Capacita(
		"tecnico.codice",
		agenzia=True,
		descrizione="Conditions written in Python, for assignment rules and SLAs",
	),
	Capacita(
		"automazioni.webhook", piano=MARKETING, agenzia=True, descrizione="Steps that call an outside address"
	),
)


def livelli_iniziali(ruoli: set[str], gerarchia: bool) -> list[str] | None:
	"""The levels a user from before levels gets when the site migrates, or None to
	leave them as they are.

	- The agency (System Manager) is left alone: its users hold no centre level.
	- So is anyone with a role no module registered - another app's: Frappe rebuilds
	  a profiled user's roles from the profiles, and that role would be gone.
	- Sales Manager becomes Manager. Sales User becomes Front Desk, or Sales where
	  the site turned the sales hierarchy on: there people see their team only.
	- And only when the levels carry every role the user had. Nobody loses anything
	  to the migration; whoever does not fit keeps their roles, and the Users page
	  shows them as they are.
	"""
	ruoli = set(ruoli) - RUOLI_AUTOMATICI
	if ruoli & RUOLI_AGENZIA or ruoli - set(ruoli_registrati()):
		return None
	if "Sales Manager" in ruoli:
		scelti = [MANAGER]
	elif "Sales User" in ruoli:
		scelti = [COMMERCIALE if gerarchia else SEGRETERIA]
	else:
		return None
	coperti = set().union(*(ruoli_del_livello(chiave) for chiave in scelti))
	if ruoli - coperti:
		return None
	return scelti


def registra() -> None:
	for modulo in MODULI:
		registra_modulo_piano(modulo)
	for nome, descrizione, di_frappe in RUOLI:
		registra_ruolo(nome, descrizione, di_frappe=di_frappe)
	# every level carries it but Marketing (`Livello.recapiti`); alone it opens nothing
	registra_ruolo(
		RUOLO_RECAPITI,
		"Sees people's email and phone numbers in full: every level but Marketing.",
		accesso=False,
	)
	for livello, ruoli in LIVELLI:
		registra_livello(livello, ruoli)
	for ruolo, livello in IMPLICITI:
		registra_livello_implicito(ruolo, livello)
	for capacita, livelli in CAPACITA:
		registra_capacita(capacita, livelli)
	for nome, ambito in DEL_MARKETING.items():
		concedi(nome, {LIV_MARKETING: ambito})
	for nome, ambito in DELL_AMMINISTRAZIONE.items():
		concedi(nome, {AMMINISTRAZIONE: ambito})
	for capacita in TECNICHE:
		registra_capacita(capacita)
	registra_requisito("builder", builder_installato)
