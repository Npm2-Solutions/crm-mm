# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Who came and booked again, without a site.

A person seen is counted once, by their last visit: they booked again when an
appointment of theirs, not cancelled, starts after it - with anybody at the
centre, and whatever became of it later (a no-show was booked all the same).
By professional, a person counts once for each professional who saw them, by
their last visit with that one. Nothing ahead is no appointment from now on.
"""

from __future__ import annotations

import datetime
from collections.abc import Iterable


def ultime_visite(visite: Iterable[tuple[str, datetime.datetime, str | None]]) -> dict[str, tuple]:
	"""Each person's last visit, ``(person, starts_on, professional)`` in,
	``{person: (starts_on, professional)}`` out."""
	ultime: dict[str, tuple] = {}
	for persona, inizio, chi in visite:
		if persona and (persona not in ultime or inizio > ultime[persona][0]):
			ultime[persona] = (inizio, chi)
	return ultime


def riprenotato(inizio: datetime.datetime, prossimo: datetime.datetime | None) -> bool:
	"""``prossimo`` is the person's latest appointment, not cancelled."""
	return bool(prossimo) and prossimo > inizio


def tasso(
	visite: Iterable[tuple[str, datetime.datetime, str | None]], prossimi: dict[str, datetime.datetime]
) -> tuple[int, int]:
	"""How many of the people seen booked again, and how many were seen."""
	ultime = ultime_visite(visite)
	tornati = sum(
		1 for persona, (inizio, _chi) in ultime.items() if riprenotato(inizio, prossimi.get(persona))
	)
	return tornati, len(ultime)


def per_professionista(
	visite: Iterable[tuple[str, datetime.datetime, str | None]], prossimi: dict[str, datetime.datetime]
) -> dict[str, tuple[int, int]]:
	"""``{professional: (booked again, seen)}``, each person by their last visit with them."""
	ultime: dict[tuple[str, str], datetime.datetime] = {}
	for persona, inizio, chi in visite:
		if persona and chi and ((persona, chi) not in ultime or inizio > ultime[(persona, chi)]):
			ultime[(persona, chi)] = inizio
	conti: dict[str, list[int]] = {}
	for (persona, chi), inizio in ultime.items():
		conto = conti.setdefault(chi, [0, 0])
		conto[1] += 1
		if riprenotato(inizio, prossimi.get(persona)):
			conto[0] += 1
	return {chi: (tornati, visti) for chi, (tornati, visti) in conti.items()}


def senza_prossimo(
	visite: Iterable[tuple[str, datetime.datetime, str | None]],
	prossimi: dict[str, datetime.datetime],
	adesso: datetime.datetime,
) -> list[tuple[str, datetime.datetime, str | None]]:
	"""The people seen with nothing booked from ``adesso`` on, the longest ago first:
	``(person, last visit, its professional)``."""
	fuori = [
		(persona, inizio, chi)
		for persona, (inizio, chi) in ultime_visite(visite).items()
		if not (prossimi.get(persona) and prossimi[persona] >= adesso)
	]
	fuori.sort(key=lambda riga: riga[1])
	return fuori
