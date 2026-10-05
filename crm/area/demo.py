# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The demo's client area, through the area's own code.

This morning the desk opened the area to the centre's regulars - whoever has a
subscription or a cycle going on, whoever comes to Davide's classes or to Elena -
and to a few who come in the next days; a mother got her child's area beside her
own. The invitation went by email - kept in the demo, nothing leaves - and most of
them came in already. The desk wrote on the board of some: the next closing day, the
socks for the gym, the forms before a first visit; some have read it.

Opened today, as the forms are signed today: who was let in, when they came in and
what they read is the area's own record, never dated back.
"""

from __future__ import annotations

import datetime

import frappe
from babel.dates import format_date
from frappe import _

from crm.demo import dati
from crm.demo.contesto import Contesto
from crm.demo.simulazione import persone_della_demo, visti_da

#: Of the invited, who came in already; of those, who read what the desk wrote.
ENTRATI = 0.8
LETTI = 0.6

#: What the desk wrote on the board, by whom it is for: the person's first name in
#: ``{nome}``, the next closing day in ``{chiusura}``.
AI_REGOLARI = (
	"Buongiorno {nome}, da questa settimana in palestra si entra con le calze antiscivolo: "
	"se le dimentica, le trova allo sportello.",
	"Buongiorno {nome}, {chiusura} il centro resta chiuso: le lezioni di quel giorno non si "
	"tengono e l'ingresso non si scala dall'abbonamento.",
)
AI_CICLI = (
	"Buongiorno {nome}, le sedute che restano del suo ciclo sono già in agenda: se un giorno "
	"non le va bene, ci scriva qui o ci chiami.",
)
A_CHI_ARRIVA = (
	"Buongiorno {nome}, prima della visita trova qui i moduli da compilare: bastano cinque "
	"minuti, così in sala d'attesa non deve scrivere nulla.",
)


def crea(ctx: Contesto) -> None:
	from crm.area import accesso

	ctx.avanza(_("Client area"))
	persone = persone_della_demo(ctx)
	desk = ctx.squadra("desk") or ctx.utente
	if not persone:
		return
	regolari, in_ciclo = _regolari(ctx, persone)
	in_arrivo = [p for p in _in_arrivo(ctx, persone) if p not in regolari]
	invitati = []
	with ctx.come(desk):
		for persona in regolari + in_arrivo[: ctx.quanti(6)]:
			if _invita(persona, accesso.SE_STESSO):
				invitati.append(persona)
		# the child booked by their mother: her own area shows the child's too
		figlio = ctx.trova("family.child")
		if figlio and _invita(figlio, accesso.TUTORE):
			invitati.append(figlio)
	ctx.salva()
	entrati = _entrano(ctx, invitati)
	_bacheca(ctx, desk, entrati, regolari, in_ciclo, in_arrivo)


def _regolari(ctx: Contesto, persone: list[str]) -> tuple[list[str], set[str]]:
	"""Whoever comes back: a subscription or a cycle going on, Davide's classes,
	Elena's visits - at most a few dozen, the same ones every time."""
	abbonati = frappe.get_all(
		"CRM Subscription",
		filters={"lead": ["in", persone], "status": ["in", ["Active", "Suspended"]]},
		pluck="lead",
	)
	in_ciclo = set(
		frappe.get_all(
			"CRM Session Cycle", filters={"lead": ["in", persone], "status": "Active"}, pluck="lead"
		)
	)
	seguiti = list(
		dict.fromkeys(
			lead
			for chiave, giorni in (("davide", 21), ("elena", 45))
			for lead, _fine in visti_da(ctx, ctx.squadra(chiave), giorni)
		)
	)
	altri = sorted((set(abbonati) | in_ciclo) - set(seguiti))
	ctx.rng.shuffle(seguiti)
	ctx.rng.shuffle(altri)
	# two in three follow Davide or Elena, who give plans to follow in the area
	quanti = ctx.quanti(30)
	primi = quanti * 2 // 3
	return sorted((seguiti[:primi] + altri + seguiti[primi:])[:quanti]), in_ciclo


def _in_arrivo(ctx: Contesto, persone: list[str]) -> list[str]:
	"""Who comes in the next week, the first first."""
	righe = frappe.db.sql(
		"""select p.party, min(a.starts_on) from `tabCRM Appointment` a
		join `tabCRM Appointment Participant` p on p.parent = a.name
		where p.party_type = 'CRM Lead' and p.party in %(persone)s
		and p.status not in ('Cancelled', 'No Show') and a.status != 'Cancelled'
		and a.starts_on between %(adesso)s and %(fine)s
		group by p.party order by min(a.starts_on), p.party""",
		{"persone": persone, "adesso": ctx.adesso, "fine": ctx.giorno(7)},
	)
	return [riga[0] for riga in righe]


def _invita(persona: str, relazione: str) -> bool:
	"""The desk opens the area: the invitation goes by email, kept in the demo."""
	from crm.area import accesso

	try:
		accesso.invite(persona, relation=relazione)
	except frappe.ValidationError:
		# nobody to send it to - a person without an email - stays without an area
		frappe.clear_last_message()
		return False
	return True


def _entrano(ctx: Contesto, invitati: list[str]) -> dict[str, str]:
	"""Most come in after the invitation: the area records when, as it does for
	anybody who opens it. Who came in, by the person whose area it is."""
	from crm.area import accesso, api

	utenti = sorted({riga.user for p in invitati for riga in accesso.accessi_aperti(p)})
	entrati = {}
	for utente in sorted(ctx.rng.sample(utenti, round(len(utenti) * ENTRATI))):
		with ctx.come(utente):
			for persona in api.get_me()["people"]:
				entrati[persona["name"]] = utente
	return entrati


def _bacheca(
	ctx: Contesto,
	desk: str,
	entrati: dict[str, str],
	regolari: list[str],
	in_ciclo: set[str],
	in_arrivo: list[str],
) -> None:
	"""The desk writes on a few boards; some read it, in the area."""
	from crm.area import messaggi

	chiusura = _prossima_chiusura(ctx.oggi)
	scritti = []
	with ctx.come(desk):
		for persona in sorted({riga.lead for riga in _accessi(regolari + in_arrivo)}):
			if persona in in_arrivo:
				parole = A_CHI_ARRIVA
			elif persona in in_ciclo:
				parole = AI_CICLI
			elif ctx.rng.random() < 0.5:
				parole = AI_REGOLARI
			else:
				continue
			nome = frappe.db.get_value("CRM Lead", persona, "first_name")
			messaggi.post_message(persona, ctx.rng.choice(parole).format(nome=nome, chiusura=chiusura))
			scritti.append(persona)
	for persona in scritti:
		utente = entrati.get(persona)
		if utente and ctx.rng.random() < LETTI:
			with ctx.come(utente):
				messaggi.mark_read(persona)


def _accessi(persone: list[str]) -> list:
	return frappe.get_all(
		"CRM Area Access",
		filters={"lead": ["in", persone or [""]], "enabled": 1},
		fields=["lead", "user"],
	)


def _prossima_chiusura(oggi: datetime.date) -> str:
	"""The next holiday, in words: "domenica 1 novembre (Ognissanti)"."""
	for anno in (oggi.year, oggi.year + 1):
		for giorno_mese, festa in dati.FESTIVITA:
			mese, giorno = (int(parte) for parte in giorno_mese.split("-"))
			data = datetime.date(anno, mese, giorno)
			if data > oggi:
				return f"{format_date(data, 'EEEE d MMMM', locale='it')} ({festa})"
	return "il prossimo giorno festivo"
