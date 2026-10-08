# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A cycle of sessions, without a site (docs/verticali/clinica, phase 3: "cicli di
sedute (fisioterapia)"; the packages of a beauty centre are the same thing).

- **A cycle is N sessions of one service for one person**, from a day, maybe until
  a day: ten sessions of physiotherapy, six of laser.
- **Each appointment of the cycle is a session**: done when the person came (the
  arrival, the appointment completed), missed when they did not come and did not
  cancel - counted, when the cycle says a missed session is lost - booked when it
  is still to come or waits for its outcome; a cancelled one does not count.
- **What is left to book** is what is neither done, missed nor booked. A new
  appointment of the service joins the cycle while there is something left and
  the cycle is on; the cycle is over when every session is done or missed, and
  expired when its last day passed with sessions left.
"""

from __future__ import annotations

import datetime

FATTA, PERSA, PRENOTATA, ANNULLATA = "done", "missed", "booked", "cancelled"
ATTIVO, COMPLETATO, SCADUTO, CHIUSO = "Active", "Completed", "Expired", "Closed"
MAX_SEDUTE = 100


def seduta(stato_appuntamento: str | None, stato_partecipante: str | None) -> str:
	"""What one appointment is for the cycle, from its status and the person's."""
	if stato_appuntamento == "Cancelled" or stato_partecipante == "Cancelled":
		return ANNULLATA
	if stato_appuntamento == "No Show" or stato_partecipante == "No Show":
		return PERSA
	if stato_appuntamento == "Completed" or stato_partecipante in ("Arrived", "Attended"):
		return FATTA
	return PRENOTATA


def conta(sedute: list[str], totale: int, perse_contano: bool = True) -> dict[str, int]:
	"""How the cycle stands: done, missed, booked, and what is left to book. A
	missed session is used when the cycle says so; otherwise it is to book again."""
	fatte = sedute.count(FATTA)
	perse = sedute.count(PERSA)
	prenotate = sedute.count(PRENOTATA)
	usate = fatte + (perse if perse_contano else 0)
	return {
		"done": fatte,
		"missed": perse,
		"booked": prenotate,
		"used": usate,
		"left": max(int(totale or 0) - usate - prenotate, 0),
		"total": int(totale or 0),
	}


def stato(conti: dict[str, int], valido_fino: datetime.date | None, oggi: datetime.date, chiuso=False) -> str:
	"""Active, completed (every session used), expired (its last day passed with
	sessions not used), or closed by hand."""
	if chiuso:
		return CHIUSO
	if conti["total"] and conti["used"] >= conti["total"]:
		return COMPLETATO
	if valido_fino and oggi > valido_fino:
		return SCADUTO
	return ATTIVO


def si_aggiunge(
	stato_ciclo: str,
	conti: dict[str, int],
	inizio: datetime.date | None,
	valido_fino: datetime.date | None,
	giorno: datetime.date,
) -> bool:
	"""Whether a new appointment of the cycle's service, on ``giorno``, joins it:
	the cycle is on, the day is within its days, and a session is left to book."""
	if stato_ciclo != ATTIVO or conti["left"] <= 0:
		return False
	if inizio and giorno < inizio:
		return False
	if valido_fino and giorno > valido_fino:
		return False
	return True


def numeri(sedute: list[tuple[str, str]], perse_contano: bool = True) -> dict[str, int]:
	"""Which session each appointment is - "session 4 of 10" - in the order they
	come; a cancelled one has no number, nor a missed one the cycle does not count.
	``sedute`` is (appointment, state) by start."""
	numero = 0
	fatto: dict[str, int] = {}
	for appuntamento, stato_seduta in sedute:
		if stato_seduta == ANNULLATA or (stato_seduta == PERSA and not perse_contano):
			continue
		numero += 1
		fatto[appuntamento] = numero
	return fatto
