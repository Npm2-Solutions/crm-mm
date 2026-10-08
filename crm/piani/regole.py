# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What a plan is, without a site: its kinds, what goes in it, and how the person's
week reads (docs/verticali/clinica/design.md, "I piani").

- **The kinds are registered** (`TipoPiano`): the CRM's own - a training, habits -
  and the ones a module brings, with who writes them and what they hold: the
  clinic's diets and exercises at home (`crm.clinica.piani_regole`). Every kind is
  the same rows: moments (a session, a meal of a day) and items pointing to their
  moment - Frappe does not nest child tables.
- **So are the kinds of item** (`GenereVoce`): an exercise, a habit; the clinic's
  food and food group. Each says the fields it fills and what it cannot be without.
- **Who writes which**: a kind without qualifications is whoever writes plans'; one
  with them, of whoever has one of them - a diet: a doctor, a biologist
  nutritionist, a dietitian.
- **Health data**: a kind may carry the mark (`clinico`): its plans are read like
  the clinical record where the clinic says who reads it (`crm.piani.api`).
- **The week**: a moment is every day or one weekday; an item may ask for "so many
  times a week", and the person sees how many are left.
- **Following it**: one tap an item (done, partly, skipped), a missed day made up
  within two days; no red, no ranking - what is shown is what is left to do.
"""

from __future__ import annotations

import datetime
import re
from collections.abc import Callable
from dataclasses import dataclass

ALLENAMENTO = "Training"
ABITUDINI = "Habits"

ESERCIZIO = "Exercise"
ABITUDINE = "Habit"

OGNI_GIORNO = "Every day"
GIORNI = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

FATTO = "Done"
IN_PARTE = "Partly"
SALTATO = "Skipped"
ESITI = (FATTO, IN_PARTE, SALTATO)

#: A missed day is made up, not lost: how many days back a check-in is written.
GIORNI_RECUPERO = 2
MAX_MOMENTI = 60
MAX_VOCI = 400
_CHIAVE = re.compile(r"^[A-Za-z0-9_-]{1,40}$")

#: What every item keeps, whatever its kind: the rest is its kind's.
CAMPI_COMUNI = ("kind", "times_per_week", "note")


@dataclass(frozen=True)
class Problema:
	"""What is wrong, in English words to translate, with their arguments."""

	messaggio: str
	argomenti: tuple = ()

	def testo(self, traduci=lambda s: s) -> str:
		return traduci(self.messaggio).format(*self.argomenti)


@dataclass(frozen=True)
class GenereVoce:
	"""A kind of item: what it fills of the item's row, and what it cannot be without."""

	chiave: str
	#: The item's fields this kind fills, beyond the common ones.
	campi: tuple[str, ...] = ()
	#: What an item of this kind lacks, or None.
	manca: Callable[[dict], Problema | None] | None = None


@dataclass(frozen=True)
class TipoPiano:
	"""A kind of plan: what it holds, who writes it, what its screens offer."""

	chiave: str
	#: The kinds of item it holds, in the order they are offered.
	generi: tuple[str, ...]
	#: The codes of the qualifications that write it; empty: whoever writes plans.
	chi_scrive: frozenset[str] = frozenset()
	#: Health data: read like the clinical record.
	clinico: bool = False
	#: The plan's module that switches it on; None: on wherever plans are.
	modulo: str | None = None
	#: What the screens offer for it, by name: "meals" (it starts with the day's
	#: meals), "calories", "targets", "nutrients", "recipes", "shopping".
	funzioni: frozenset[str] = frozenset()
	ordine: int = 50
	#: One line on what it is, in English: whoever chooses which plan to write
	#: reads it.
	descrizione: str = ""
	#: How it shows to the person, in the client area: a category of the design
	#: system ("amber", "violet", "green", "blue", "rose"; empty, the brand's) and
	#: a Lucide icon's name.
	colore: str = ""
	icona: str = ""


_generi: dict[str, GenereVoce] = {}
_tipi: dict[str, TipoPiano] = {}


def registra_genere(genere: GenereVoce) -> None:
	_generi[genere.chiave] = genere


def registra_tipo(tipo: TipoPiano) -> None:
	_tipi[tipo.chiave] = tipo


def genere(chiave: str | None) -> GenereVoce | None:
	return _generi.get(chiave or "")


def tipo(chiave: str | None) -> TipoPiano | None:
	return _tipi.get(chiave or "")


def tipi() -> list[TipoPiano]:
	"""Every kind registered, in their order."""
	return sorted(_tipi.values(), key=lambda t: (t.ordine, t.chiave))


def campi_voce() -> tuple[str, ...]:
	"""What an item's row keeps: the common fields and every kind's own."""
	campi = list(CAMPI_COMUNI)
	for g in _generi.values():
		campi += [c for c in g.campi if c not in campi]
	return tuple(campi)


def tipi_per(qualifica: str | None, tra: list[TipoPiano] | None = None) -> list[str]:
	"""The kinds of plan a person with this qualification writes, among ``tra``
	(every kind registered, if not said)."""
	return [
		t.chiave for t in (tipi() if tra is None else tra) if not t.chi_scrive or qualifica in t.chi_scrive
	]


def _numero(valore) -> float | None:
	try:
		return float(valore)
	except (TypeError, ValueError):
		return None


def valida(chiave_tipo: str, momenti: list[dict], voci: list[dict]) -> list[Problema]:
	"""What is wrong with a plan's rows: nothing, or the list.

	A moment has its own key, a name and a day; an item points to a moment and is
	of a kind the plan holds, with what that kind needs.
	"""
	del_tipo = tipo(chiave_tipo)
	if not del_tipo:
		return [Problema("{0} is not a kind of plan", (chiave_tipo,))]
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
		del_genere = genere(voce.get("kind"))
		if not del_genere or del_genere.chiave not in del_tipo.generi:
			problemi.append(Problema("A plan of this kind does not hold {0}", (voce.get("kind") or "",)))
			continue
		if voce.get("moment") not in chiavi:
			problemi.append(Problema("An item belongs to a moment of the plan"))
		manca = del_genere.manca(voce) if del_genere.manca else None
		if manca:
			problemi.append(manca)
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
	"""How the days went, counted: for its author, not a score."""
	return {esito: sum(1 for e in esiti if e == esito) for esito in ESITI}


def fatica(valori: list) -> dict | None:
	"""How hard or painful the person said the exercises were, 1 to 10, in the
	order they said it (0 is not said): the average to one decimal, the last one
	and how many times; None when they said nothing."""
	detti = [int(v) for v in valori if v and 1 <= int(v) <= 10]
	if not detti:
		return None
	return {"average": round(sum(detti) / len(detti), 1), "last": detti[-1], "said": len(detti)}


# ------------------------------------------------------------------ the CRM's own


def _esercizio(voce: dict) -> Problema | None:
	return None if voce.get("exercise") else Problema("Choose the exercise")


def _abitudine(voce: dict) -> Problema | None:
	return None if (voce.get("text") or "").strip() else Problema("Write the habit")


registra_genere(
	GenereVoce(ESERCIZIO, ("exercise", "sets", "reps", "duration", "rest", "load", "side"), _esercizio)
)
#: A habit fits in any plan: water, a walk, sleep.
registra_genere(GenereVoce(ABITUDINE, ("text",), _abitudine))
registra_tipo(
	TipoPiano(
		ALLENAMENTO,
		(ESERCIZIO, ABITUDINE),
		ordine=30,
		descrizione="Exercises for the days of the week, with sets, reps and rest.",
		colore="violet",
		icona="dumbbell",
	)
)
registra_tipo(
	TipoPiano(
		ABITUDINI,
		(ABITUDINE,),
		ordine=50,
		descrizione="Small things to keep up every day: water, a walk, sleep.",
		colore="green",
		icona="sprout",
	)
)
