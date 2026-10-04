# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The demo's subscriptions: the regulars of the classes pay for them, as a studio's
clients do.

Three types are on sale (Settings > Agenda > Services > Subscriptions): eight
Pilates classes a month renewed by itself, three months of postural gymnastics that
can be suspended, six months of every class paid by the month. The most faithful
regular of each weekly class bought one on their first class; the product does the
rest - the classes already booked use its entries, a month that ends renews, a
suspension moves the end, the reminder of the end goes (to nobody: `crm.demo.guardie`).

One subscriber per class, for now: a class is one appointment, and an appointment
uses the entry of one subscription only.
"""

from __future__ import annotations

import datetime
import itertools

import frappe
from frappe import _
from frappe.utils import get_datetime, getdate

from crm import lingue
from crm.demo import dati
from crm.demo.contesto import Contesto, nome_libero
from crm.demo.simulazione import persone_della_demo

ABBONAMENTO = "CRM Subscription"
TIPO = "CRM Subscription Type"
#: A regular comes to a class this many times at least.
VOLTE = 3


def crea(ctx: Contesto) -> None:
	from crm.scheduling import abbonamenti

	davide = ctx.squadra("davide")
	desk = ctx.squadra("desk") or ctx.utente
	ctx.avanza(_("Subscriptions"))
	tipi = _tipi(ctx)
	if not tipi:
		return
	presi: set = set()
	venduti = 0
	for regolare in _regolari(ctx):
		if venduti >= ctx.quanti(12):
			break
		# one subscriber per class (see above): no class of theirs is somebody else's
		if regolare["tutte"] & presi:
			continue
		tipo = _tipo_per(ctx, regolare["servizi"])
		if tipo not in tipi:
			continue
		presi |= regolare["tutte"]
		dal = regolare["primo"]
		with ctx.come(desk):
			venduto = abbonamenti.sell_subscription(
				regolare["lead"],
				{"subscription_type": tipi[tipo], "starts_on": str(dal), "practitioner": davide},
			)
		catena = _i_mesi_passano(ctx, venduto["name"])
		_retrodata(ctx, catena, regolare["ora"], desk)
		if tipo == "posturale":
			_sospendi(ctx, catena[-1], regolare["giorni"], desk)
		venduti += 1


def _tipi(ctx: Contesto) -> dict[str, str]:
	"""The types on sale, by their key."""
	servizi = {chiave: ctx.trova(f"service.{chiave}") for chiave, *_resto in dati.SERVIZI}
	valuta = lingue.valuta()
	tipi = {}
	for (
		chiave,
		nome,
		mesi,
		pagamento,
		prezzo,
		ingressi,
		quanti,
		comprende,
		sospensione,
		promemoria,
		rinnova,
		descrizione,
	) in dati.ABBONAMENTI:
		compresi = [servizi[s] for s in comprende if servizi.get(s)]
		if not compresi:
			continue
		doc = frappe.get_doc(
			{
				"doctype": TIPO,
				"type_name": nome_libero(TIPO, nome),
				"enabled": 1,
				"description": descrizione,
				"months": mesi,
				"payment": pagamento,
				"price": prezzo,
				"currency": valuta,
				"entries": ingressi,
				"entries_count": quanti or None,
				"missed_count": 1,
				"can_suspend": 1 if sospensione else 0,
				"max_suspension_days": sospensione or None,
				"remind_days": promemoria,
				"auto_renew": 1 if rinnova else 0,
				"services": [{"service": s} for s in compresi],
			}
		).insert(ignore_permissions=True)
		ctx.retrodata(TIPO, doc.name, ctx.adesso - datetime.timedelta(days=90), ctx.squadra("manager"))
		ctx.ricorda(TIPO, doc.name, f"subscription_type.{chiave}")
		tipi[chiave] = doc.name
	return tipi


def _regolari(ctx: Contesto) -> list[dict]:
	"""The people who come to the classes, the most faithful first: their weekly
	classes, the services, their first class and the days they came."""
	persone = persone_della_demo(ctx)
	lezioni = [ctx.trova(f"service.{chiave}") for chiave in {riga[2] for riga in dati.LEZIONI}]
	lezioni = [s for s in lezioni if s]
	if not persone or not lezioni:
		return []
	per_persona: dict[str, dict] = {}
	for riga in frappe.db.sql(
		"""select p.party, a.service, a.starts_on, a.ends_on
		from `tabCRM Appointment Participant` p
		join `tabCRM Appointment` a on a.name = p.parent
		where p.parenttype = 'CRM Appointment' and p.party_type = 'CRM Lead'
			and p.party in %(persone)s and a.service in %(lezioni)s
			and a.status != 'Cancelled' and p.status != 'Cancelled'
		order by a.starts_on""",
		{"persone": persone, "lezioni": lezioni},
		as_dict=True,
	):
		inizio = get_datetime(riga.starts_on)
		lezione = (riga.service, inizio.weekday(), inizio.strftime("%H:%M"))
		voce = per_persona.setdefault(
			riga.party, {"lead": riga.party, "volte": {}, "servizi": set(), "giorni": [], "primo": None}
		)
		voce["volte"][lezione] = voce["volte"].get(lezione, 0) + 1
		voce["servizi"].add(riga.service)
		voce["giorni"].append(inizio.date())
		if voce["primo"] is None:
			voce["primo"] = inizio.date()
			voce["ora"] = get_datetime(riga.ends_on)
	regolari = []
	for voce in per_persona.values():
		voce["lezioni"] = {lezione for lezione, volte in voce["volte"].items() if volte >= VOLTE}
		voce["tutte"] = set(voce["volte"])
		ultima = max(voce["giorni"])
		# still coming: their last class is in the last ten days, or booked ahead
		if voce["lezioni"] and ultima >= ctx.giorno(-10):
			voce["quante"] = sum(voce["volte"].values())
			regolari.append(voce)
	regolari.sort(key=lambda voce: (-voce["quante"], voce["lead"]))
	return regolari


def _tipo_per(ctx: Contesto, servizi: set[str]) -> str:
	pilates = ctx.trova("service.pilates")
	posturale = ctx.trova("service.posturale")
	if servizi == {posturale}:
		return "posturale"
	if servizi == {pilates}:
		return "open" if ctx.rng.random() < 0.25 else "pilates8"
	return "open"


def _i_mesi_passano(ctx: Contesto, nome: str) -> list[str]:
	"""The days the subscription lived through, as the daily round saw them: a month
	that ended renewed itself, the reminder of the end went, the ones past are
	expired."""
	from crm.scheduling import abbonamenti

	catena = [nome]
	for _volta in range(12):
		doc = frappe.get_doc(ABBONAMENTO, catena[-1])
		with ctx.nella_lingua_del_centro():
			abbonamenti._il_giorno(doc, ctx.oggi)
		rinnovo = frappe.db.get_value(ABBONAMENTO, doc.name, "renewed_by")
		if not rinnovo:
			break
		catena.append(rinnovo)
	return catena


def _retrodata(ctx: Contesto, catena: list[str], venduto: datetime.datetime, desk: str) -> None:
	"""Sold at the end of the first class; each renewal made by the night's round, the
	day it starts."""
	for indice, nome in enumerate(catena):
		if indice == 0:
			quando = min(get_datetime(venduto) + datetime.timedelta(minutes=10), ctx.adesso)
			chi = desk
		else:
			inizio = getdate(frappe.db.get_value(ABBONAMENTO, nome, "starts_on"))
			quando = min(datetime.datetime.combine(inizio, datetime.time(6, 0)), ctx.adesso)
			chi = "Administrator"
		ctx.retrodata(ABBONAMENTO, nome, quando, chi)


def _sospendi(ctx: Contesto, nome: str, giorni: list[datetime.date], desk: str) -> None:
	"""A week the person skipped was a suspension (flu); a person who never skipped
	one goes on holiday after their last class booked. Either way the end moves by
	those days, and no class of theirs falls in them."""
	from crm.scheduling import abbonamenti

	doc = frappe.get_doc(ABBONAMENTO, nome)
	inizio, fine = getdate(doc.starts_on), getdate(doc.ends_on)
	massimo = int(doc.max_suspension_days or 0) or 14
	venuti = sorted({g for g in giorni if inizio <= g <= fine})
	finestra = None
	for prima, dopo in itertools.pairwise(venuti):
		if (dopo - prima).days >= 12:
			finestra = (prima + datetime.timedelta(days=1), dopo - datetime.timedelta(days=1), "Influenza")
			break
	if not finestra and venuti and venuti[-1] + datetime.timedelta(days=10) < fine:
		dal = max(venuti[-1], ctx.oggi) + datetime.timedelta(days=1)
		finestra = (dal, dal + datetime.timedelta(days=9), "Vacanza")
	if not finestra:
		return
	dal, al, motivo = finestra
	al = min(al, dal + datetime.timedelta(days=massimo - 1))
	try:
		with ctx.come(desk):
			abbonamenti.suspend_subscription(nome, str(dal), str(al), motivo)
	except frappe.ValidationError:
		frappe.clear_last_message()
