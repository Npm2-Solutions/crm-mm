# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The clinic's plans, without a site: the diets and the exercises at home, who
writes them, the foods, and what the tables say of them (design.md, "I piani").

- **Three kinds of its own** in the CRM's engine (`crm.piani.regole`): a menu, an
  exchange diet (portions of a food group, the food chosen by the patient),
  exercises at home. Health data: read like the record, switched on with the
  clinic.
- **Who writes which**: the practitioner's qualification decides. A diet is
  written by a doctor, a biologist nutritionist or a dietitian: a personal trainer
  who gives one practises a profession that is not theirs. Rehabilitation at home
  by a physiotherapist or a doctor. A training and habits are the CRM's, for
  whoever writes plans.
- **Two kinds of item**: a food and how much, with what instead; a food group and
  its portions.
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

from crm.piani.regole import (
	ABITUDINE,
	ESERCIZIO,
	GIORNI,
	OGNI_GIORNO,
	GenereVoce,
	Problema,
	TipoPiano,
	in_corso,
	momenti_del_giorno,
	registra_genere,
	registra_tipo,
	settimana,
)

#: The plan's module that switches the clinic's kinds on.
MODULO = "clinica"

MENU = "Meal plan"
SCAMBI = "Exchange diet"
ESERCIZI = "Home exercises"
#: The clinic's kinds; the CRM's own are a training and habits.
TIPI = (MENU, SCAMBI, ESERCIZI)
DIETE_TIPI = (MENU, SCAMBI)

CIBO = "Food"
GRUPPO = "Food group"

DIETE = frozenset({"medico_chirurgo", "biologo", "dietista"})
RIABILITAZIONE = frozenset({"fisioterapista", "medico_chirurgo"})

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


def _numero(valore) -> float | None:
	try:
		return float(valore)
	except (TypeError, ValueError):
		return None


def _cibo(voce: dict) -> Problema | None:
	return None if voce.get("food") else Problema("Choose the food")


def _gruppo(voce: dict) -> Problema | None:
	if voce.get("food_group") and (_numero(voce.get("portions")) or 0) > 0:
		return None
	return Problema("A food group comes with its portions")


registra_genere(GenereVoce(CIBO, ("food", "quantity_g", "alternatives"), _cibo))
registra_genere(GenereVoce(GRUPPO, ("food_group", "portions", "alternatives"), _gruppo))
registra_tipo(
	TipoPiano(
		MENU,
		(CIBO, ABITUDINE),
		chi_scrive=DIETE,
		clinico=True,
		modulo=MODULO,
		funzioni=frozenset({"meals", "calories", "targets", "nutrients", "recipes", "shopping"}),
		ordine=10,
		descrizione="The day's meals with foods and grams: calories and nutrients counted, the shopping list ready.",
		colore="amber",
		icona="apple",
	)
)
registra_tipo(
	TipoPiano(
		SCAMBI,
		(GRUPPO, CIBO, ABITUDINE),
		chi_scrive=DIETE,
		clinico=True,
		modulo=MODULO,
		funzioni=frozenset({"meals", "calories", "shopping"}),
		ordine=20,
		descrizione="Food groups in portions, to swap freely within each group.",
		colore="amber",
		icona="salad",
	)
)
registra_tipo(
	TipoPiano(
		ESERCIZI,
		(ESERCIZIO, ABITUDINE),
		chi_scrive=RIABILITAZIONE,
		clinico=True,
		modulo=MODULO,
		ordine=40,
		descrizione="Exercises to do at home between sessions, and how often.",
		colore="violet",
		icona="dumbbell",
	)
)


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
