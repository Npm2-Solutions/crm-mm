# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What a plan is, without a site: its kinds, who writes each, what goes in it,
and how the patient's week reads (design.md, "I piani").

- **Five kinds**: a menu, an exchange diet (portions of a food group, the food
  chosen by the patient), a training, exercises at home, habits. Every kind is the
  same rows: moments (a day and a meal, a session) and items pointing to their
  moment - Frappe does not nest child tables.
- **Who writes which**: the practitioner's qualification decides. A diet is
  written by a doctor, a biologist nutritionist or a dietitian: a personal trainer
  who gives one practises a profession that is not theirs. Rehabilitation at home
  by a physiotherapist or a doctor. A training and habits by whoever writes plans.
- **The week**: a moment is every day or one weekday; an item may ask for "so
  many times a week", and the patient sees how many are left.
- **Following it**: one tap an item (done, partly, skipped), a missed day made
  up within two days; no red, no ranking - what is shown is what is left to do.
- **The shopping list** (design.md, "I piani": "Lista della spesa dal menù") is
  the menu's foods over the days to shop for: each food's grams every time its
  meal comes, as many times a week as it is asked; an exchange diet's portions
  by group, the food chosen by the patient.
- **The nutrients come from the tables** (design.md, "L'assistente", point 5): the
  targets are the nutritionist's, the totals are computed here from the library's
  values for 100 g, and the assistant proposes only recipes - which foods of the
  library, in which proportion. `frontend/src/utils/piani.js` computes the same
  totals, on the cases of `tests/casi_nutrienti.json`.
"""

from __future__ import annotations

import datetime
import math
import re
from dataclasses import dataclass

MENU = "Meal plan"
SCAMBI = "Exchange diet"
ALLENAMENTO = "Training"
ESERCIZI = "Home exercises"
ABITUDINI = "Habits"
TIPI = (MENU, SCAMBI, ALLENAMENTO, ESERCIZI, ABITUDINI)

CIBO = "Food"
GRUPPO = "Food group"
ESERCIZIO = "Exercise"
ABITUDINE = "Habit"
GENERI = (CIBO, GRUPPO, ESERCIZIO, ABITUDINE)

DIETE = frozenset({"medico_chirurgo", "biologo", "dietista"})
RIABILITAZIONE = frozenset({"fisioterapista", "medico_chirurgo"})

#: Who writes each kind, by the code of their `CRM Professional Qualification`;
#: None is whoever writes plans at all.
CHI_SCRIVE: dict[str, frozenset | None] = {
	MENU: DIETE,
	SCAMBI: DIETE,
	ALLENAMENTO: None,
	ESERCIZI: RIABILITAZIONE,
	ABITUDINI: None,
}

#: What each kind holds. A habit fits anywhere: water, a walk, sleep.
VOCI: dict[str, frozenset] = {
	MENU: frozenset({CIBO, ABITUDINE}),
	SCAMBI: frozenset({GRUPPO, CIBO, ABITUDINE}),
	ALLENAMENTO: frozenset({ESERCIZIO, ABITUDINE}),
	ESERCIZI: frozenset({ESERCIZIO, ABITUDINE}),
	ABITUDINI: frozenset({ABITUDINE}),
}

OGNI_GIORNO = "Every day"
GIORNI = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

#: The groups of the library's foods, in the order a list shows them.
GRUPPI = (
	"Cereals and tubers",
	"Legumes",
	"Meat",
	"Fish",
	"Eggs",
	"Milk and dairy",
	"Vegetables",
	"Fruit",
	"Oils and fats",
	"Nuts and seeds",
	"Sweets",
	"Drinks",
	"Other",
)

FATTO = "Done"
IN_PARTE = "Partly"
SALTATO = "Skipped"
ESITI = (FATTO, IN_PARTE, SALTATO)

#: A missed day is made up, not lost: how many days back a check-in is written.
GIORNI_RECUPERO = 2
MAX_MOMENTI = 60
MAX_VOCI = 400
_CHIAVE = re.compile(r"^[A-Za-z0-9_-]{1,40}$")


@dataclass(frozen=True)
class Problema:
	"""What is wrong, in English words to translate, with their arguments."""

	messaggio: str
	argomenti: tuple = ()

	def testo(self, traduci=lambda s: s) -> str:
		return traduci(self.messaggio).format(*self.argomenti)


def tipi_per(qualifica: str | None) -> list[str]:
	"""The kinds of plan a practitioner with this qualification writes."""
	return [tipo for tipo in TIPI if CHI_SCRIVE[tipo] is None or qualifica in CHI_SCRIVE[tipo]]


def _numero(valore) -> float | None:
	try:
		return float(valore)
	except (TypeError, ValueError):
		return None


def valida(tipo: str, momenti: list[dict], voci: list[dict]) -> list[Problema]:
	"""What is wrong with a plan's rows: nothing, or the list.

	A moment has its own key, a name and a day; an item points to a moment and is
	of a kind the plan holds, with what that kind needs: the food, the group and
	its portions, the exercise, the habit's words.
	"""
	if tipo not in TIPI:
		return [Problema("{0} is not a kind of plan", (tipo,))]
	problemi: list[Problema] = []
	if len(momenti) > MAX_MOMENTI:
		problemi.append(Problema("At most {0} moments", (MAX_MOMENTI,)))
	if len(voci) > MAX_VOCI:
		problemi.append(Problema("At most {0} items", (MAX_VOCI,)))
	chiavi: set[str] = set()
	for momento in momenti:
		chiave = momento.get("key")
		if not isinstance(chiave, str) or not _CHIAVE.match(chiave) or chiave in chiavi:
			problemi.append(Problema("Every moment has its own key ({0})", (chiave or "",)))
		chiavi.add(chiave)
		if not (momento.get("label") or "").strip():
			problemi.append(Problema("Every moment has a name"))
		if momento.get("day") not in (OGNI_GIORNO, *GIORNI):
			problemi.append(Problema("{0} is not a day", (momento.get("day") or "",)))
	for voce in voci:
		genere = voce.get("kind")
		if genere not in VOCI[tipo]:
			problemi.append(Problema("A plan of this kind does not hold {0}", (genere or "",)))
			continue
		if voce.get("moment") not in chiavi:
			problemi.append(Problema("An item belongs to a moment of the plan"))
		if genere == CIBO and not voce.get("food"):
			problemi.append(Problema("Choose the food"))
		if genere == GRUPPO and (not voce.get("food_group") or (_numero(voce.get("portions")) or 0) <= 0):
			problemi.append(Problema("A food group comes with its portions"))
		if genere == ESERCIZIO and not voce.get("exercise"):
			problemi.append(Problema("Choose the exercise"))
		if genere == ABITUDINE and not (voce.get("text") or "").strip():
			problemi.append(Problema("Write the habit"))
		volte = voce.get("times_per_week")
		if volte not in (None, "", 0) and not (1 <= (_numero(volte) or 0) <= 7):
			problemi.append(Problema("A week has at most seven days"))
	return problemi


def momenti_del_giorno(momenti: list[dict], giorno: datetime.date) -> list[dict]:
	"""The moments of a day: every day's, and that weekday's, in their order."""
	nome = GIORNI[giorno.weekday()]
	return [momento for momento in momenti if momento.get("day") in (OGNI_GIORNO, nome)]


def settimana(giorno: datetime.date) -> tuple[datetime.date, datetime.date]:
	"""Monday to Sunday of the week of ``giorno``."""
	lunedi = giorno - datetime.timedelta(days=giorno.weekday())
	return lunedi, lunedi + datetime.timedelta(days=6)


def restano(volte: int | None, esiti: list[str]) -> int | None:
	"""How many times are left this week: a partial one counts, a skipped one does not."""
	if not volte:
		return None
	fatte = sum(1 for esito in esiti if esito in (FATTO, IN_PARTE))
	return max(int(volte) - fatte, 0)


def si_segna(giorno: datetime.date, oggi: datetime.date) -> bool:
	"""A check-in is for today, or a day just missed; never ahead."""
	return 0 <= (oggi - giorno).days <= GIORNI_RECUPERO


def in_corso(inizio: datetime.date | None, fine: datetime.date | None, oggi: datetime.date) -> bool:
	"""Whether a published plan is followed on ``oggi``."""
	return (inizio is None or inizio <= oggi) and (fine is None or oggi <= fine)


def riepilogo(esiti: list[str]) -> dict[str, int]:
	"""How the days went, counted: for the practitioner, not a score."""
	return {esito: sum(1 for e in esiti if e == esito) for esito in ESITI}


def calorie(per_cento_grammi, grammi) -> int | None:
	"""The calories of a quantity, from the table's value for 100 g."""
	kcal, peso = _numero(per_cento_grammi), _numero(grammi)
	if kcal is None or peso is None:
		return None
	return round(kcal * peso / 100)


# ------------------------------------------------------------------ nutrients

#: What the tables give for 100 g, and a total is made of.
NUTRIENTI = ("kcal", "protein_g", "carbs_g", "fat_g", "fibre_g")
#: The grams of one food in a recipe the engine reads: a proposal outside is dropped.
GRAMMI_MAX = 2000


def _mezzo_su(valore: float, decimali: int = 0) -> float:
	"""Rounded half up, as the browser rounds: Python's own rounds half to even."""
	scala = 10**decimali
	return math.floor(valore * scala + 0.5) / scala


def arrotonda_grammi(grammi) -> int | None:
	"""A quantity as a person weighs it: to 5 g, to the gram under 10 g, never 0."""
	valore = _numero(grammi)
	if valore is None or valore <= 0:
		return None
	if valore < 10:
		return max(1, int(_mezzo_su(valore)))
	return int(5 * _mezzo_su(valore / 5))


def _totali(voci: list[dict], cibi: dict) -> tuple[dict[str, float], list[str]]:
	totali = dict.fromkeys(NUTRIENTI, 0.0)
	mancano = []
	for voce in voci:
		if (voce.get("kind") or CIBO) != CIBO or not voce.get("food"):
			continue
		cibo = cibi.get(voce["food"])
		grammi = _numero(voce.get("quantity_g"))
		if not cibo or not grammi or grammi <= 0:
			mancano.append(voce["food"])
			continue
		for nome in NUTRIENTI:
			valore = _numero(cibo.get(nome))
			if valore is not None:
				totali[nome] += valore * grammi / 100
	return totali, mancano


def nutrienti(voci: list[dict], cibi: dict) -> dict:
	"""What the foods give, from the tables' values for 100 g: kcal to the unit,
	grams to one decimal. A food without grams, or not in the tables, counts
	nothing and is named in ``missing``."""
	totali, mancano = _totali(voci, cibi)
	return {
		"kcal": int(_mezzo_su(totali["kcal"])),
		**{nome: _mezzo_su(totali[nome], 1) for nome in NUTRIENTI[1:]},
		"missing": mancano,
	}


def per_giorno(momenti: list[dict], voci: list[dict], cibi: dict) -> list[dict]:
	"""The totals of each day: the every-day moments and that weekday's. One row,
	every day, when no moment is on a weekday of its own."""
	ogni_giorno = {m["key"] for m in momenti if (m.get("day") or OGNI_GIORNO) == OGNI_GIORNO}
	giorni = [g for g in GIORNI if any(m.get("day") == g for m in momenti)]
	if not giorni:
		return [{"day": OGNI_GIORNO, **nutrienti([v for v in voci if v.get("moment") in ogni_giorno], cibi)}]
	righe = []
	for giorno in GIORNI:
		chiavi = ogni_giorno | {m["key"] for m in momenti if m.get("day") == giorno}
		righe.append({"day": giorno, **nutrienti([v for v in voci if v.get("moment") in chiavi], cibi)})
	return righe


def scala(voci: list[dict], cibi: dict, kcal) -> list[dict]:
	"""The same foods, their grams scaled so the meal gives about ``kcal``: the
	proportions are the recipe's, the quantities the tables'."""
	obiettivo = _numero(kcal)
	attuali = _totali(voci, cibi)[0]["kcal"]
	if not obiettivo or obiettivo <= 0 or attuali <= 0:
		return [dict(voce) for voce in voci]
	fattore = obiettivo / attuali
	scalate = []
	for voce in voci:
		nuova = dict(voce)
		grammi = _numero(voce.get("quantity_g"))
		if (voce.get("kind") or CIBO) == CIBO and grammi:
			nuova["quantity_g"] = arrotonda_grammi(grammi * fattore)
		scalate.append(nuova)
	return scalate


def ricetta(proposta, cibi: dict) -> dict | None:
	"""A recipe the assistant proposed, as the engine keeps it: only foods of the
	library, by their id, with grams it can read; the same food once. Nothing else
	of the proposal is taken - no numbers but the grams."""
	if not isinstance(proposta, dict):
		return None
	titolo = str(proposta.get("title") or "").strip()[:140]
	metodo = str(proposta.get("method") or "").strip()[:2000]
	grammi: dict[str, float] = {}
	for voce in proposta.get("foods") or []:
		if not isinstance(voce, dict):
			continue
		cibo = str(voce.get("id") or voce.get("food") or "")
		quanto = _numero(voce.get("grams"))
		if cibo not in cibi or quanto is None or not 0 < quanto <= GRAMMI_MAX:
			continue
		grammi[cibo] = grammi.get(cibo, 0) + quanto
	if not titolo or not grammi:
		return None
	return {
		"title": titolo,
		"method": metodo,
		"items": [
			{"kind": CIBO, "food": cibo, "quantity_g": arrotonda_grammi(g)} for cibo, g in grammi.items()
		],
	}


# ------------------------------------------------------------------ the shopping list

#: How far a shopping list looks: five weeks at most.
MAX_GIORNI_SPESA = 35


def giorni_del_periodo(
	dal: datetime.date,
	giorni: int,
	inizio: datetime.date | None = None,
	fine: datetime.date | None = None,
) -> list[datetime.date]:
	"""The days from ``dal`` for ``giorni`` days that fall in the plan's period."""
	quanti = max(1, min(int(giorni or 1), MAX_GIORNI_SPESA))
	return [
		giorno
		for giorno in (dal + datetime.timedelta(days=n) for n in range(quanti))
		if in_corso(inizio, fine, giorno)
	]


def spesa(momenti: list[dict], voci: list[dict], cibi: dict, giorni: list[datetime.date]) -> dict:
	"""What to buy for these days.

	Each food of the menu with its grams summed over the days its moment comes -
	every day's moments every day, a weekday's on that weekday - and only as many
	times a week as the item asks. A food without grams is listed, to buy, without
	a number. The portions of an exchange diet are summed by group: the food is the
	patient's choice. Foods in the library's group order, then by name.
	"""
	per_cibo: dict[str, dict] = {}
	per_gruppo: dict[str, float] = {}
	volte_nella_settimana: dict[tuple, int] = {}
	for giorno in giorni:
		lunedi = settimana(giorno)[0]
		chiavi = [m["key"] for m in momenti_del_giorno(momenti, giorno)]
		for chiave_momento in chiavi:
			for voce in voci:
				if voce.get("moment") != chiave_momento:
					continue
				genere = voce.get("kind") or CIBO
				if genere not in (CIBO, GRUPPO):
					continue
				volte = int(_numero(voce.get("times_per_week")) or 0)
				if volte:
					conto = (lunedi, voce.get("key"))
					if volte_nella_settimana.get(conto, 0) >= volte:
						continue
					volte_nella_settimana[conto] = volte_nella_settimana.get(conto, 0) + 1
				if genere == GRUPPO:
					gruppo = voce.get("food_group") or "Other"
					per_gruppo[gruppo] = per_gruppo.get(gruppo, 0) + (_numero(voce.get("portions")) or 0)
					continue
				cibo = voce.get("food")
				if not cibo:
					continue
				riga = per_cibo.setdefault(cibo, {"food": cibo, "grams": 0.0, "times": 0, "each": set()})
				grammi = _numero(voce.get("quantity_g"))
				riga["times"] += 1
				if grammi and grammi > 0:
					riga["grams"] += grammi
					riga["each"].add(grammi)
				else:
					riga["each"].add(None)
	righe = []
	for riga in per_cibo.values():
		dati = cibi.get(riga["food"]) or {}
		ogni_volta = riga["each"].pop() if len(riga["each"]) == 1 else None
		righe.append(
			{
				"food": riga["food"],
				"food_name": dati.get("food_name") or riga["food"],
				"food_group": dati.get("food_group") or "Other",
				"grams": _mezzo_su(riga["grams"], 1) if riga["grams"] else None,
				"times": riga["times"],
				# the same quantity each time: "80 g, 7 times"
				"each": ogni_volta,
			}
		)
	ordine = {gruppo: n for n, gruppo in enumerate(GRUPPI)}
	righe.sort(key=lambda r: (ordine.get(r["food_group"], len(GRUPPI)), r["food_name"].lower()))
	gruppi = [
		{"food_group": gruppo, "portions": _mezzo_su(porzioni, 1)}
		for gruppo, porzioni in sorted(per_gruppo.items(), key=lambda g: ordine.get(g[0], len(GRUPPI)))
		if porzioni > 0
	]
	return {"foods": righe, "groups": gruppi, "days": len(giorni)}
