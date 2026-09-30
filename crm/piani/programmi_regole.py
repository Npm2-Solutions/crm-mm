# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A programme of stages, without a site (design.md, "I piani": "Programmi a tappe:
contenuti che si aprono col tempo o finita la tappa prima, per i percorsi di
nutrizione e di allenamento"; ricerca-design.md §2.1, Practice Better's programmes
at fixed dates or at one's own pace, Trainerize's phases).

- **Stages in order**, each with what the patient reads and, if the practitioner
  writes one, a plan to follow while it is open: a menu, a training, exercises at
  home, habits.
- **By time**: each stage opens after the days of the one before, from the day
  the programme starts. The last may have no days: it stays open until the
  programme is closed.
- **At one's own pace**: the next stage opens when the one before is finished -
  the patient says so from their area, or the practitioner from the CRM.
- **One stage at a time is open**: what is behind is done, what is ahead is
  locked, and says when it opens.
"""

from __future__ import annotations

import datetime
import re

from crm.piani.regole import Problema

TEMPO = "By time"
RITMO = "At own pace"
MODI = (TEMPO, RITMO)

FATTA, APERTA, CHIUSA = "done", "open", "locked"
MAX_TAPPE = 24
MAX_GIORNI = 365
_CHIAVE = re.compile(r"^[A-Za-z0-9_-]{1,40}$")


def _giorni(valore) -> int | None:
	try:
		giorni = int(valore)
	except (TypeError, ValueError):
		return None
	return giorni if giorni > 0 else None


def valida(modo: str, tappe: list[dict]) -> list[Problema]:
	"""What is wrong with a programme's stages: nothing, or the list.

	A stage has its own key and a title. By time, every stage but the last says
	how many days it lasts; at one's own pace, the days mean nothing."""
	if modo not in MODI:
		return [Problema("{0} is not a way a programme goes on", (modo or "",))]
	problemi: list[Problema] = []
	if not tappe:
		problemi.append(Problema("A programme has at least one stage"))
	if len(tappe) > MAX_TAPPE:
		problemi.append(Problema("At most {0} stages", (MAX_TAPPE,)))
	chiavi: set = set()
	for posizione, tappa in enumerate(tappe):
		chiave = tappa.get("key")
		if not isinstance(chiave, str) or not _CHIAVE.match(chiave) or chiave in chiavi:
			problemi.append(Problema("Every stage has its own key ({0})", (chiave or "",)))
		chiavi.add(chiave)
		if not (tappa.get("title") or "").strip():
			problemi.append(Problema("Every stage has a title"))
		if modo != TEMPO:
			continue
		giorni = tappa.get("days")
		ultima = posizione == len(tappe) - 1
		if giorni in (None, "", 0) and ultima:
			continue
		giorni = _giorni(giorni)
		if giorni is None or giorni > MAX_GIORNI:
			problemi.append(Problema("Stage {0} lasts from 1 to {1} days", (posizione + 1, MAX_GIORNI)))
	return problemi


def finestre(inizio: datetime.date, tappe: list[dict]) -> list[tuple[datetime.date, datetime.date | None]]:
	"""By time, when each stage is open: from its first day to its last, the last
	stage without an end when it has no days."""
	righe = []
	dal = inizio
	for tappa in tappe:
		giorni = _giorni(tappa.get("days"))
		if giorni is None:
			righe.append((dal, None))
			# a stage without days is the last one: nothing comes after it
			break
		al = dal + datetime.timedelta(days=giorni - 1)
		righe.append((dal, al))
		dal = al + datetime.timedelta(days=1)
	return righe


def tappa_del_giorno(inizio: datetime.date | None, tappe: list[dict], giorno: datetime.date) -> int | None:
	"""By time, which stage is open on ``giorno``: its position; None before the
	programme starts; ``len(tappe)`` once the last one is over."""
	if inizio is None or giorno < inizio:
		return None
	for posizione, (_dal, al) in enumerate(finestre(inizio, tappe)):
		if al is None or giorno <= al:
			return posizione
	return len(tappe)


def stati(modo: str, inizio: datetime.date | None, tappe: list[dict], oggi: datetime.date) -> list[dict]:
	"""Each stage as the patient reads it: done, open or locked, with the day it
	opened, it was finished, or - by time - it opens."""
	date = finestre(inizio, tappe) if (modo == TEMPO and inizio) else []
	righe = []
	for posizione, tappa in enumerate(tappe):
		if tappa.get("completed_on"):
			stato = FATTA
		elif tappa.get("opened_on"):
			stato = APERTA
		else:
			stato = CHIUSA
		apre = date[posizione][0] if posizione < len(date) else None
		righe.append(
			{
				"key": tappa.get("key"),
				"state": stato,
				"opened_on": tappa.get("opened_on"),
				"completed_on": tappa.get("completed_on"),
				# by time a locked stage says its day; at one's own pace, "after the one before"
				"opens_on": apre if stato == CHIUSA else None,
				"ends_on": date[posizione][1] if posizione < len(date) else None,
			}
		)
	return righe


def aperta(tappe: list[dict]) -> int | None:
	"""The stage open now: its position, or None."""
	for posizione, tappa in enumerate(tappe):
		if tappa.get("opened_on") and not tappa.get("completed_on"):
			return posizione
	return None


def prossima(tappe: list[dict]) -> int | None:
	"""The stage that opens next: the first never opened, or None when all were."""
	for posizione, tappa in enumerate(tappe):
		if not tappa.get("opened_on"):
			return posizione
	return None
