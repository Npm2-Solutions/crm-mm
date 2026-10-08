# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The demo's dentistry, through the clinic's own code.

A dentist joined the centre some weeks ago: his chair in Studio 4, his services, his
days. Whoever came to him had the first visit written on the dental sheet and signed,
their odontogram, and a care plan handed over after the visit - a quote with the teeth
and their surfaces on its rows. Some said yes: their treatments are booked, the first
already done for who said yes a while ago. One or two said no; the most recent are
still thinking about it. The dentist wrote on the board of who had a cleaning done.
"""

from __future__ import annotations

import datetime
import json

import frappe
from frappe import _
from frappe.utils import getdate

from crm.clinica.demo import dati as D
from crm.clinica.demo.cartelle import (
	consensi_alla_visita,
	decide_la_sintesi,
	pubblica_scheda,
	visita_sulla_scheda,
)
from crm.demo import dati as dati_demo
from crm.demo.base import collega
from crm.demo.contesto import Contesto, nome_del_giorno, nome_libero
from crm.demo.simulazione import date_del_preventivo, persone_della_demo

APPUNTAMENTO = "CRM Appointment"


def crea(ctx: Contesto) -> None:
	from crm import lingue

	ctx.avanza(_("Dentistry"))
	dentista = collega(ctx, *D.DENTISTA, turni=D.TURNI_DENTISTA, dal=ctx.giorno(-50))
	valuta = lingue.valuta()
	studio = _studio(ctx, valuta)
	servizi = _servizi(ctx, dentista, studio, valuta)
	chi_scrive = ctx.squadra("direttrice") or ctx.squadra("manager") or ctx.utente
	scheda = pubblica_scheda(
		ctx,
		chi_scrive,
		"dentista",
		"Visita odontoiatrica",
		D.SCHEDA_DENTISTA,
		"Odontoiatria",
		"La prima visita del dentista: l'anamnesi, l'esame, il piano di cura.",
	)
	ctx.salva()
	agenda = Agenda(ctx, dentista, studio, servizi)
	scritte = []
	for persona in _chi(ctx):
		scritta = _primo_incontro(ctx, agenda, scheda, persona)
		if scritta:
			scritte.append(scritta)
	ctx.salva()
	decide_la_sintesi(ctx, scritte)
	consensi_alla_visita(ctx, scritte)
	_di_cura(ctx, dentista, agenda.curati)


def _studio(ctx: Contesto, valuta: str) -> str:
	chiave, nome, tipo, posti, colore, descrizione = D.STUDIO_DENTISTICO
	doc = frappe.get_doc(
		{
			"doctype": "CRM Resource",
			"resource_name": nome_libero("CRM Resource", nome),
			"resource_type": tipo,
			"capacity": 1,
			"seats": posti,
			"color": colore,
			"description": descrizione,
			"currency": valuta,
			"enabled": 1,
		}
	).insert(ignore_permissions=True)
	ctx.ricorda("CRM Resource", doc.name, f"room.{chiave}")
	return doc.name


def _servizi(ctx: Contesto, dentista: str, studio: str, valuta: str) -> dict[str, dict]:
	"""The dentist's services in his room, as the services page makes them."""
	fatti = {}
	for chiave, nome, minuti, prezzo, colore, descrizione in D.SERVIZI_DENTISTA:
		online = chiave in ("prima_odonto", "igiene")
		doc = frappe.get_doc(
			{
				"doctype": "CRM Service",
				"service_name": nome_libero("CRM Service", nome),
				"category": "Odontoiatria",
				"enabled": 1,
				"color": colore,
				"description": descrizione,
				"duration": minuti,
				"default_price": prezzo,
				"price_per_participant": 0,
				"currency": valuta,
				"min_participants": 1,
				"max_participants": 1,
				"online_max_participants": 1,
				"bookable_online": 1 if online else 0,
				"staff_selection": "Any one",
				"staff": [{"user": dentista, "bookable_online": 1 if online else 0}],
				"resources": [{"resource": studio, "quantity": 1, "required": 1}],
			}
		).insert(ignore_permissions=True)
		ctx.ricorda("CRM Service", doc.name, f"service.{chiave}")
		fatti[chiave] = {"name": doc.name, "minuti": minuti, "prezzo": prezzo}
	return fatti


def _chi(ctx: Contesto) -> list[str]:
	"""Some of the centre's grown-up clients also came to the dentist."""
	persone = persone_della_demo(ctx)
	figlio = ctx.trova("family.child")
	clienti = frappe.get_all(
		"CRM Lead",
		filters={"name": ["in", persone or [""]], "client_since": ["is", "set"]},
		pluck="name",
		order_by="name",
	)
	clienti = [lead for lead in clienti if lead != figlio]
	return ctx.rng.sample(clienti, min(len(clienti), ctx.quanti(8)))


class Agenda:
	"""The dentist's days: the free slots of his shifts, never over a holiday, nor over
	another appointment of the person's that day."""

	def __init__(self, ctx: Contesto, dentista: str, studio: str, servizi: dict[str, dict]):
		self.ctx = ctx
		self.dentista = dentista
		self.studio = studio
		self.servizi = servizi
		self.desk = ctx.squadra("desk") or ctx.utente
		self.presi: list[tuple[datetime.datetime, datetime.datetime]] = []
		lista = ctx.trova("agenda.festivita")
		self.festivi = (
			{
				getdate(riga.date)
				for riga in frappe.get_all(
					"CRM Holiday",
					filters={"parent": lista, "parenttype": "CRM Holiday List"},
					fields=["date"],
				)
			}
			if lista
			else set()
		)
		#: who had a treatment done: the dentist writes on their board
		self.curati: list[str] = []

	def _giorni_della_persona(self, persona: str) -> set[datetime.date]:
		return {
			getdate(inizio)
			for inizio in frappe.db.sql_list(
				"""select a.starts_on from `tabCRM Appointment` a
				join `tabCRM Appointment Participant` p on p.parent = a.name
				where p.party = %s and a.status != 'Cancelled'""",
				persona,
			)
		}

	def posto(
		self, persona: str, servizio: str, dal: datetime.date, al: datetime.date
	) -> datetime.datetime | None:
		"""A free start in the dentist's shifts between the two days, or None."""
		minuti = self.servizi[servizio]["minuti"]
		occupati = self._giorni_della_persona(persona)
		giorni = [dal + datetime.timedelta(days=n) for n in range(max(0, (al - dal).days) + 1)]
		self.ctx.rng.shuffle(giorni)
		for giorno in giorni:
			turni = D.TURNI_DENTISTA.get(nome_del_giorno(giorno))
			if not turni or giorno in self.festivi or giorno in occupati:
				continue
			inizi = []
			for apre, chiude in turni:
				ora = self.ctx.alle(giorno, apre)
				fine_turno = self.ctx.alle(giorno, chiude)
				while ora + datetime.timedelta(minutes=minuti) <= fine_turno:
					inizi.append(ora)
					ora += datetime.timedelta(minutes=30)
			self.ctx.rng.shuffle(inizi)
			for inizio in inizi:
				fine = inizio + datetime.timedelta(minutes=minuti)
				if all(fine <= a or inizio >= b for a, b in self.presi):
					return inizio
		return None

	def prenota(
		self, persona: str, servizio: str, inizio: datetime.datetime
	) -> tuple[str, datetime.datetime]:
		"""The desk books it: past, the person came; ahead, they are expected."""
		ctx = self.ctx
		fine = inizio + datetime.timedelta(minutes=self.servizi[servizio]["minuti"])
		passato = fine <= ctx.adesso
		nome = frappe.db.get_value("CRM Lead", persona, "lead_name")
		doc = frappe.get_doc(
			{
				"doctype": APPUNTAMENTO,
				"service": self.servizi[servizio]["name"],
				"status": "Confirmed",
				"starts_on": inizio,
				"ends_on": fine,
				"staff": [{"user": self.dentista, "status": "Confirmed"}],
				"participants": [
					{
						"party_type": "CRM Lead",
						"party": persona,
						"participant_name": nome,
						"status": "Attended" if passato else "Booked",
						"arrived_at": inizio - datetime.timedelta(minutes=ctx.rng.randint(3, 12))
						if passato
						else None,
					}
				],
				"resources": [{"resource": self.studio, "quantity": 1}],
				"source": "Internal",
			}
		)
		with ctx.come(self.desk):
			doc.insert(ignore_permissions=True)
		prenotato = min(
			inizio - datetime.timedelta(days=ctx.rng.randint(2, 9), hours=ctx.rng.randint(0, 5)),
			ctx.adesso - datetime.timedelta(minutes=5),
		)
		ctx.retrodata(APPUNTAMENTO, doc.name, prenotato, self.desk)
		self.presi.append((inizio, fine))
		return doc.name, fine


def _primo_incontro(ctx: Contesto, agenda: Agenda, scheda: str, persona: str) -> dict | None:
	"""The first visit, the odontogram, the care plan; what the person said of it."""
	from crm.clinica import cure

	inizio = agenda.posto(persona, "prima_odonto", ctx.giorno(-30), ctx.giorno(-1))
	if not inizio:
		return None
	appuntamento, fine = agenda.prenota(persona, "prima_odonto", inizio)
	motivo = ctx.rng.choice(D.MOTIVI_DENTISTA)
	stati, righe = _denti(ctx, motivo)
	igiene = ctx.rng.choice(D.IGIENE)
	gengive = "Sane" if igiene == "Buona" else ctx.rng.choice(D.GENGIVE)
	risposte = {
		"allergie": ctx.scegli_pesato(D.ALLERGIE),
		"farmaci": ctx.scegli_pesato(D.FARMACI),
		"patologie": ctx.scegli_pesato(D.PATOLOGIE),
		"motivo": motivo,
		"igiene": igiene,
		"gengive": gengive,
		"esame": _esame(stati),
		"piano": _piano(righe),
	}
	with ctx.come(agenda.dentista):
		record = visita_sulla_scheda(persona, scheda, appuntamento, fine, risposte)
		cure.save_chart(persona, json.dumps(stati), dentition="Permanent")
	_piano_di_cura(ctx, agenda, persona, fine, righe)
	return {
		"lead": persona,
		"chi": "dentista",
		"utente": agenda.dentista,
		"record": record,
		"quando": fine,
		"motivo": motivo,
	}


def _denti(ctx: Contesto, motivo: str) -> tuple[list[dict], list[tuple]]:
	"""The odontogram, and the rows of the care plan it asks for: (service, tooth,
	surfaces, phase)."""
	liberi = list(D.DENTI_POSTERIORI)
	ctx.rng.shuffle(liberi)
	stati, righe = [], [("igiene", None, None, 1)]
	for dente in liberi[: ctx.rng.randint(0, 2)]:
		stati.append({"tooth": dente, "condition": "Filling", "surfaces": ctx.rng.choice(D.SUPERFICI)})
	liberi = liberi[len(stati) :]
	for dente in liberi[: ctx.rng.randint(1, 3)]:
		superfici = ctx.rng.choice(D.SUPERFICI)
		stati.append({"tooth": dente, "condition": "Caries", "surfaces": superfici})
		righe.append(("otturazione", dente, superfici, 1))
	liberi = liberi[len(stati) :]
	if motivo == "Dolore a un dente" and liberi:
		dente = liberi.pop(0)
		stati.append(
			{"tooth": dente, "condition": "Caries", "surfaces": "OD", "note": "Profonda, vicina alla polpa"}
		)
		righe += [("devitalizzazione", dente, None, 1), ("corona", dente, None, 2)]
	if motivo == "Dente mancante":
		dente = ctx.rng.choice(("36", "46", "26"))
		stati = [s for s in stati if s["tooth"] != dente]
		righe = [r for r in righe if r[1] != dente]
		stati.append({"tooth": dente, "condition": "Missing"})
		righe.append(("impianto", dente, None, 2))
	if ctx.rng.random() < 0.3:
		stati.append({"tooth": ctx.rng.choice(("38", "48")), "condition": "Impacted"})
	return stati, righe


def _esame(stati: list[dict]) -> str:
	parole = {"Caries": "carie", "Filling": "otturazione", "Missing": "mancante", "Impacted": "incluso"}
	return (
		"; ".join(
			f"{stato['tooth']}: {parole.get(stato['condition'], stato['condition'].lower())}"
			+ (f" {stato['surfaces']}" if stato.get("surfaces") else "")
			for stato in sorted(stati, key=lambda s: s["tooth"])
		).capitalize()
		+ "."
	)


def _piano(righe: list[tuple]) -> str:
	nomi = {chiave: nome for chiave, nome, *_resto in D.SERVIZI_DENTISTA}
	fasi = {}
	for servizio, dente, _superfici, fase in righe:
		fasi.setdefault(fase, []).append(f"{nomi[servizio].lower()}" + (f" del {dente}" if dente else ""))
	return " ".join(f"Fase {fase}: {', '.join(voci)}." for fase, voci in sorted(fasi.items()))


def _piano_di_cura(
	ctx: Contesto, agenda: Agenda, persona: str, fine: datetime.datetime, righe: list[tuple]
) -> None:
	"""The care plan handed over after the visit: yes, no, or still thinking about it.
	Who said yes has the treatments booked, the first already done if a while ago."""
	from crm.preventivi import api as preventivi

	voci = [
		{
			"service": agenda.servizi[servizio]["name"],
			"tooth": dente,
			"surfaces": superfici,
			"phase": fase,
			"qty": 1,
			"rate": agenda.servizi[servizio]["prezzo"],
			"discount": 0,
		}
		for servizio, dente, superfici, fase in righe
	]
	proposto = min(
		fine + datetime.timedelta(minutes=ctx.rng.randint(5, 20)), ctx.adesso - datetime.timedelta(minutes=30)
	)
	dati = {"title": "Piano di cura", "patient_notes": ctx.rng.choice(D.NOTE_PIANO), "items": voci}
	caso = ctx.rng.random()
	if (ctx.oggi - fine.date()).days <= 6 and caso < 0.5:
		esito, quando = None, None
	elif caso < 0.8:
		esito, quando = "si", proposto + datetime.timedelta(hours=ctx.rng.choice((0, 2, 20, 26, 50)))
	else:
		esito, quando = "no", proposto + datetime.timedelta(days=ctx.rng.randint(2, 6))
	if quando:
		quando = min(quando, ctx.adesso - datetime.timedelta(minutes=10))
	# the first who said yes a while ago pays in instalments, written so in the editor
	a_rate = esito == "si" and (ctx.oggi - quando.date()).days >= GIORNI_RATE and not ctx.trova(CHIAVE_RATE)
	if a_rate:
		dati.update(RATE, first_due_on=str(ctx.giorno(30)))
	with ctx.come(agenda.dentista):
		bozza = preventivi.save_quote(persona, dati)
		preventivi.propose_quote(bozza["name"])
	nome = bozza["name"]
	if a_rate:
		ctx.ricorda(preventivi.DOCTYPE, nome, CHIAVE_RATE)
	with ctx.come(agenda.desk):
		if esito == "si":
			preventivi.accept_quote(nome, ctx.rng.choice(dati_demo.SI_AL_PREVENTIVO))
		elif esito == "no":
			motivo, nota = ctx.rng.choice(dati_demo.NO_AL_PREVENTIVO)
			preventivi.decline_quote(
				nome, motivo if frappe.db.exists("CRM Lost Reason", motivo) else None, nota
			)
	date_del_preventivo(ctx, nome, agenda.dentista, proposto, esito, quando, agenda.desk)
	if a_rate:
		_date_delle_rate(nome, quando.date())
	if esito == "si":
		_cure(ctx, agenda, persona, quando, righe)


#: The care plan paid in instalments (docs/crm/63): a fifth on acceptance and ten a
#: month from the day after; accepted at least this many days ago, so that the
#: deposit and the first instalment at least are due, invoiced and paid by
#: invoicing's part (three, for one accepted over a month ago).
RATE = {
	"payment": "Instalments",
	"deposit_type": "Percent",
	"deposit_value": 20,
	"instalments_count": 10,
	"every_months": 1,
}
GIORNI_RATE = 10
CHIAVE_RATE = "quote.instalments"


def _date_delle_rate(nome: str, accettato: datetime.date) -> None:
	"""The plan put back at its moments, as the quote was: the deposit on the day it
	was accepted, the instalments from the day after."""
	from crm.scheduling.abbonamenti_regole import piu_mesi

	primo = accettato + datetime.timedelta(days=1)
	frappe.db.set_value("CRM Quote", nome, "first_due_on", primo, update_modified=False)
	for riga in frappe.get_all(
		"CRM Quote Instalment", filters={"parent": nome}, fields=["name", "kind", "number"]
	):
		giorno = accettato if riga.kind == "Deposit" else piu_mesi(primo, int(riga.number) - 1)
		frappe.db.set_value("CRM Quote Instalment", riga.name, "due_on", giorno, update_modified=False)


def _cure(
	ctx: Contesto, agenda: Agenda, persona: str, accettato: datetime.datetime, righe: list[tuple]
) -> None:
	"""The first phase booked: done already when the plan was accepted a while ago,
	ahead in the next weeks the rest; each takes its row of the plan."""
	prima_fase = [servizio for servizio, _dente, _superfici, fase in righe if fase == 1]
	dal = accettato.date() + datetime.timedelta(days=2)
	for posizione, servizio in enumerate(prima_fase[:3]):
		fatto = posizione == 0 and dal <= ctx.giorno(-2)
		inizio = (
			agenda.posto(persona, servizio, dal, ctx.giorno(-1))
			if fatto
			else agenda.posto(persona, servizio, max(dal, ctx.giorno(1)), ctx.giorno(28))
		)
		if not inizio:
			continue
		agenda.prenota(persona, servizio, inizio)
		if fatto:
			agenda.curati.append(persona)


def _di_cura(ctx: Contesto, dentista: str, curati: list[str]) -> None:
	"""A word from the dentist on the board of who had a treatment and has the area."""
	from crm.area import messaggi

	nell_area = set(
		frappe.get_all("CRM Area Access", filters={"enabled": 1, "relation": "Self"}, pluck="lead")
	)
	for persona in curati:
		if persona in nell_area:
			nome = frappe.db.get_value("CRM Lead", persona, "first_name")
			with ctx.come(dentista):
				messaggi.post_message(persona, D.DI_CURA["dentista"].format(nome=nome))
			return
