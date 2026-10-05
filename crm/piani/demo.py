# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The demo's plans and programmes, through the plans' own code.

Davide, the kinesiologist, gave the regulars of his classes a training to do at home
between one class and the next; Elena, the dietitian, gave small habits to keep to
whoever came to her. Each plan was given at the person's last session with them.
This morning Davide wrote a programme to go back to running, at one's own pace, and
Elena one of three months by time. Who has the area open ticks there what they did:
today, and the two days before - as far back as the area lets one make up.

A plan is dated at the session it was given in, as the agenda's past is: it is the
practitioner's work. What the person ticked is ticked today, as the area records it.
"""

from __future__ import annotations

from dataclasses import dataclass

import frappe
from frappe import _
from frappe.utils import get_datetime

from crm.demo.contesto import Contesto
from crm.demo.simulazione import visti_da

PIANO = "CRM Personal Plan"

#: (exercise as the library names it, sets, reps, duration, rest)
Esercizio = tuple[str, int, str | None, str | None, str | None]
#: (the habit, times a week; None: every day)
Abitudine = tuple[str, int | None]

#: Davide's trainings to do at home: (title, instructions, exercises).
ALLENAMENTI: tuple[tuple[str, str, tuple[Esercizio, ...]], ...] = (
	(
		"Postura e core a casa",
		"Tre volte a settimana, nei giorni senza lezione. Movimenti lenti, respira senza "
		"trattenere il fiato; se un esercizio fa male, saltalo e dimmelo a lezione.",
		(
			("Pelvic tilt", 2, "12", None, "30 sec"),
			("Dead bug", 3, "10 per lato", None, "30 sec"),
			("Low glute bridge on floor", 3, "12", None, "45 sec"),
			("Bodyweight incline side plank", 2, None, "20 sec per lato", "30 sec"),
			("Power point plank", 3, None, "30 sec", "45 sec"),
		),
	),
	(
		"Schiena e anche, mobilità",
		"Due o tre volte a settimana, anche la sera. Prima la mobilità, poi il rinforzo: "
		"venti minuti bastano.",
		(
			("Standing pelvic tilt", 2, "10", None, "20 sec"),
			("Pelvic tilt into bridge", 3, "10", None, "40 sec"),
			("Glute bridge march", 3, "8 per gamba", None, "40 sec"),
			("Side plank hip adduction", 2, "8 per lato", None, "30 sec"),
			("All fours squad stretch", 1, None, "30 sec per lato", None),
		),
	),
)
#: What goes with every training, during the day.
MOVIMENTO: tuple[Abitudine, ...] = (
	("Una camminata di 30 minuti", 3),
	("In piedi e due passi ogni ora, alla scrivania", None),
)

#: Elena's habits, by moment of the day: (moment, time, habits).
ABITUDINI: tuple[tuple[str, str, tuple[Abitudine, ...]], ...] = (
	(
		"Al mattino",
		"08:00",
		(("Un bicchiere d'acqua appena svegli", None), ("Colazione seduti, con calma", None)),
	),
	("A pranzo", "13:00", (("Metà del piatto di verdura", None),)),
	(
		"La sera",
		"20:00",
		(("Cena entro le 20:30", None), ("Una passeggiata di 20 minuti dopo cena", 4)),
	),
)


@dataclass(frozen=True)
class Tappa:
	titolo: str
	descrizione: str
	giorni: int | None = None
	esercizi: tuple[Esercizio, ...] = ()
	abitudini: tuple[Abitudine, ...] = ()


#: Davide's programme, at one's own pace: the next stage opens when the person says so.
CORSA = (
	"Ritorno alla corsa",
	"Passa alla tappa dopo quando la fai senza fatica per una settimana intera.",
	(
		Tappa(
			"Rinforzo",
			"Gambe e piedi pronti: rinforzo tre volte a settimana e camminate veloci.",
			esercizi=(
				("Bodyweight standing calf raise", 3, "15", None, "30 sec"),
				("Split squats", 3, "10 per gamba", None, "45 sec"),
				("Glute bridge march", 3, "8 per gamba", None, "40 sec"),
				("Calf stretch with hands against wall", 1, None, "30 sec per lato", None),
			),
			abitudini=(("Una camminata veloce di 30 minuti", 3),),
		),
		Tappa(
			"Corsa e cammino",
			"Si torna a correre a intervalli: due minuti di corsa, uno di cammino.",
			esercizi=(
				("Walking lunge", 2, "10 per gamba", None, "45 sec"),
				("One leg floor calf raise", 3, "12 per gamba", None, "30 sec"),
				("Runners stretch", 1, None, "30 sec per lato", None),
			),
			abitudini=(("Corsa e cammino: 2 minuti e 1, per 24 minuti", 3),),
		),
		Tappa(
			"Corsa continua",
			"Venti minuti di corsa senza fermarsi, al ritmo in cui si riesce a parlare.",
			esercizi=(
				("Jump squat", 3, "8", None, "60 sec"),
				("Hamstring stretch", 1, None, "30 sec per lato", None),
			),
			abitudini=(("Corsa continua di 20 minuti", 3),),
		),
	),
)

#: Elena's programme, by time: each stage opens on its day by itself.
TRE_MESI = (
	"Tre mesi di abitudini",
	"Una tappa al mese: le abitudini di una tappa restano anche nella successiva.",
	(
		Tappa(
			"Le basi",
			"Acqua, colazione e verdura: le tre cose da cui partire.",
			giorni=30,
			abitudini=(
				("Otto bicchieri d'acqua nella giornata", None),
				("Colazione entro un'ora dal risveglio", None),
				("Verdura a pranzo e a cena", None),
			),
		),
		Tappa(
			"La spesa",
			"La lista della spesa scritta prima di uscire, e la frutta sempre in vista.",
			giorni=30,
			abitudini=(
				("La lista della spesa scritta a casa", 1),
				("Due frutti al giorno, come spuntino", None),
			),
		),
		Tappa(
			"Da soli",
			"Le abitudini restano: si torna al controllo per vedere come va.",
			abitudini=(("Un pasto preparato in casa con calma", 5),),
		),
	),
)

#: How a tick went, and a word on a few of the partial ones, by the kind of item.
ESITI = (("Done", 75), ("Partly", 15), ("Skipped", 10))
NOTE_A_META = {
	"Exercise": ("Fatte due serie su tre", "Un po' di fastidio al ginocchio"),
	"Habit": ("Poco tempo, ho fatto metà", "Ci ho provato: domani meglio"),
}


def crea(ctx: Contesto) -> None:
	ctx.avanza(_("Plans and programmes"))
	esercizi = _esercizi()
	davide, elena = ctx.squadra("davide"), ctx.squadra("elena")
	nell_area = set(
		frappe.get_all(
			"CRM Area Access",
			filters={"enabled": 1, "relation": "Self", "last_seen_on": ["is", "set"]},
			pluck="lead",
		)
	)
	dati = []
	if davide:
		allievi, corridori = divisi(ctx, visti_da(ctx, davide, 21), nell_area, ctx.quanti(10), ctx.quanti(2))
		for posizione, (persona, fine) in enumerate(allievi):
			titolo, istruzioni, del_piano = ALLENAMENTI[posizione % len(ALLENAMENTI)]
			momenti, voci = _allenamento(esercizi, del_piano, MOVIMENTO)
			dati.append((davide, persona, fine, "Training", titolo, istruzioni, momenti, voci))
		for persona, _fine in corridori:
			_programma(ctx, davide, persona, "At own pace", "Training", CORSA, esercizi)
	if elena:
		seguiti, a_tempo = divisi(ctx, visti_da(ctx, elena, 45), nell_area, ctx.quanti(6), ctx.quanti(1))
		for persona, fine in seguiti:
			momenti, voci = _abitudini(ABITUDINI)
			istruzioni = "Segna ogni sera come è andata: ne parliamo al prossimo controllo."
			dati.append(
				(elena, persona, fine, "Habits", "Le abitudini di questo mese", istruzioni, momenti, voci)
			)
		for persona, _fine in a_tempo:
			_programma(ctx, elena, persona, "By time", "Habits", TRE_MESI, esercizi)
	for autore, persona, fine, tipo, titolo, istruzioni, momenti, voci in dati:
		piano_alla_seduta(ctx, autore, persona, fine, tipo, titolo, istruzioni, momenti, voci)
	ctx.salva()
	spuntano(ctx)


def divisi(
	ctx: Contesto, visti: list, nell_area: set[str], quanti_primi: int, quanti_secondi: int
) -> tuple[list, list]:
	"""Two groups of different people among whom a colleague saw - a person follows
	one plan of a kind at a time -, who came into the area first: a plan is followed
	there, and one given at a session is ticked there already. The first group, the
	plans, takes them first; a programme opens today."""
	visti = list(visti)
	ctx.rng.shuffle(visti)
	visti.sort(key=lambda riga: riga[0] not in nell_area)
	return visti[:quanti_primi], visti[quanti_primi : quanti_primi + quanti_secondi]


def _esercizi() -> dict[str, str]:
	"""The library's exercises by their name, as written here: one the centre
	switched off is left out of the plans."""
	nomi = {esercizio[0] for _titolo, _istruzioni, del_piano in ALLENAMENTI for esercizio in del_piano} | {
		esercizio[0] for _t, _i, tappe in (CORSA, TRE_MESI) for tappa in tappe for esercizio in tappa.esercizi
	}
	trovati: dict[str, str] = {}
	for riga in frappe.get_all(
		"CRM Exercise",
		filters={"exercise_name": ["in", sorted(nomi)], "enabled": 1},
		fields=["name", "exercise_name"],
		order_by="exercise_name, name",
	):
		trovati.setdefault(riga.exercise_name.lower(), riga.name)
	return trovati


def _allenamento(
	esercizi: dict[str, str], del_piano: tuple[Esercizio, ...], abitudini: tuple[Abitudine, ...]
) -> tuple[list[dict], list[dict]]:
	momenti = [
		{"key": "casa", "label": "Allenamento a casa", "day": "Every day"},
		{"key": "giorno", "label": "Durante la giornata", "day": "Every day"},
	]
	voci = [
		{
			"kind": "Exercise",
			"moment": "casa",
			"exercise": esercizi[nome.lower()],
			"sets": serie,
			"reps": ripetizioni,
			"duration": durata,
			"rest": recupero,
			"times_per_week": 3,
		}
		for nome, serie, ripetizioni, durata, recupero in del_piano
		if nome.lower() in esercizi
	]
	voci += [
		{"kind": "Habit", "moment": "giorno", "text": testo, "times_per_week": volte}
		for testo, volte in abitudini
	]
	return momenti, voci


def _abitudini(per_momento) -> tuple[list[dict], list[dict]]:
	momenti, voci = [], []
	for posizione, (etichetta, ora, abitudini) in enumerate(per_momento, 1):
		chiave = f"m{posizione}"
		momenti.append({"key": chiave, "label": etichetta, "day": "Every day", "time": ora})
		voci += [
			{"kind": "Habit", "moment": chiave, "text": testo, "times_per_week": volte}
			for testo, volte in abitudini
		]
	return momenti, voci


def piano_alla_seduta(
	ctx: Contesto, autore, persona, fine, tipo, titolo, istruzioni, momenti, voci, **altro
) -> str | None:
	"""Written and published at the person's last session, as the author does it;
	``altro`` what a module's kind adds (a diet's targets). A module's part gives its
	plans so too - the clinic's diets and exercises at home."""
	from crm.piani import api

	if not voci:
		return None
	quando = get_datetime(fine)
	with ctx.come(autore):
		piano = api.save_plan(
			persona,
			{
				"plan_type": tipo,
				"title": titolo,
				"instructions": istruzioni,
				"starts_on": str(quando.date()),
				"moments": momenti,
				"items": voci,
				**altro,
			},
		)
		api.publish_plan(piano["name"])
	frappe.db.set_value(PIANO, piano["name"], "published_on", quando, update_modified=False)
	ctx.retrodata(PIANO, piano["name"], quando, autore)
	return piano["name"]


def _programma(ctx: Contesto, autore, persona, modo, tipo, programma, esercizi) -> None:
	"""Written this morning: its stages, the plan of each, then published - its first
	stage opens today."""
	from crm.piani import api, programmi

	titolo, istruzioni, tappe = programma
	with ctx.come(autore):
		fatto = programmi.save_programme(
			persona,
			{
				"title": titolo,
				"mode": modo,
				"instructions": istruzioni,
				"starts_on": str(ctx.oggi) if modo == "By time" else None,
				"stages": [
					{
						"key": f"t{posizione}",
						"title": tappa.titolo,
						"description": tappa.descrizione,
						"days": tappa.giorni,
					}
					for posizione, tappa in enumerate(tappe, 1)
				],
			},
		)
		for posizione, tappa in enumerate(tappe, 1):
			momenti, voci = (
				_allenamento(esercizi, tappa.esercizi, tappa.abitudini)
				if tipo == "Training"
				else _abitudini((("Ogni giorno", "", tappa.abitudini),))
			)
			piano = programmi.stage_plan(fatto["name"], f"t{posizione}", tipo)["plan"]
			api.save_plan(
				persona,
				{"plan_type": tipo, "title": tappa.titolo, "moments": momenti, "items": voci},
				name=piano,
			)
		programmi.publish_programme(fatto["name"])


# -- what the person ticks in the area ------------------------------------------------


def spuntano(ctx: Contesto) -> None:
	"""Who came into the area ticks the plans the part being made gave them, day by
	day, as far back as it lets them: some days all, some days part, a day forgotten
	now and then. A module's part with plans of its own ticks them so too."""
	from crm.piani import api, area
	from crm.piani import regole as R

	giorni = [ctx.giorno(-indietro) for indietro in range(R.GIORNI_RECUPERO, -1, -1)]
	# today is ticked once the day has gone some way
	if ctx.adesso.hour < 14:
		giorni = giorni[:-1]
	piani = frappe.get_all(
		PIANO,
		filters={"name": ["in", _fatti_qui() or [""]], "status": "Published"},
		fields=["name", "lead", "starts_on"],
		order_by="name",
	)
	for piano in piani:
		utente = frappe.db.get_value(
			"CRM Area Access",
			{"lead": piano.lead, "enabled": 1, "relation": "Self", "last_seen_on": ["is", "set"]},
			"user",
		)
		if not utente:
			continue
		momenti, voci = api.righe_del_piano(frappe.get_doc(PIANO, piano.name))
		with ctx.come(utente):
			for giorno in giorni:
				# a plan starts on its day; and a day forgotten now and then
				if (piano.starts_on and giorno < piano.starts_on) or ctx.rng.random() < 0.15:
					continue
				del_giorno = {momento["key"] for momento in R.momenti_del_giorno(momenti, giorno)}
				for voce in voci:
					if voce["moment"] not in del_giorno:
						continue
					volte = voce.get("times_per_week")
					if ctx.rng.random() >= (volte / 7 + 0.15 if volte else 0.85):
						continue
					esito = ctx.scegli_pesato(ESITI)
					note = NOTE_A_META.get(voce.get("kind"), NOTE_A_META["Habit"])
					nota = ctx.rng.choice(note) if esito == "Partly" and ctx.rng.random() < 0.4 else None
					area.log_item(piano.lead, piano.name, voce["key"], esito, str(giorno), note=nota)


def _fatti_qui() -> list[str]:
	"""The plans this part made: the stages' ones too."""
	from crm.demo import registro

	corrente = registro.raccolta()
	return sorted({nome for doctype, nome in (corrente.creati if corrente else ()) if doctype == PIANO})
