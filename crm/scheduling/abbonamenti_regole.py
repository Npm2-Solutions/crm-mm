# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A subscription, without a site (design.md, "Cosa si aggiunge al CRM": "gli
abbonamenti"): a gym's month, a beauty centre's three months of treatments, a year
of physiotherapy in the pool.

- **A type says** how many months, the price and whether it is paid at once or by
  the month, which services it comprises and how many entries: any number, or so
  many a week or a month; whether it can be suspended.
- **A subscription** is a type sold to a person from a day. It ends the day before
  the same day so many months later, and later by the days it was suspended.
- **An appointment of a comprised service** within its days uses an entry, as a
  session uses a cycle: done when the person came, missed when they did not come
  and did not cancel (used when the type says so), booked while it is to come. A
  cancelled one gives its entry back. Entries are counted in the week, Monday to
  Sunday, or in the subscription's month, from its first day.
- **Paid by the month**, an instalment falls on the same day of each month from the
  first; the last one takes the cents the others could not.
- **A cycle counts sessions, a subscription time**: an appointment that joins a
  cycle does not use an entry.
"""

from __future__ import annotations

import calendar
import datetime

from crm.scheduling.cicli_regole import FATTA, PERSA, PRENOTATA, seduta

ATTIVO, SOSPESO, SCADUTO, CHIUSO = "Active", "Suspended", "Expired", "Closed"
STATI = (ATTIVO, SOSPESO, SCADUTO, CHIUSO)
#: How a subscription is paid.
SUBITO, MENSILE = "Upfront", "Monthly"
PAGAMENTI = (SUBITO, MENSILE)
#: How its entries are counted.
ILLIMITATI, A_SETTIMANA, AL_MESE = "Unlimited", "Per week", "Per month"
INGRESSI = (ILLIMITATI, A_SETTIMANA, AL_MESE)
#: What the centre may choose, and what it gets if it chooses nothing: (least, most, default).
MESI = (1, 36, 1)
PROMEMORIA = (0, 60, 7)

UN_GIORNO = datetime.timedelta(days=1)

#: What an appointment is for the subscription: the same as for a cycle.
ingresso = seduta


def entro(valore, limiti: tuple[int, int, int]) -> int:
	"""A number the centre chose, kept within what makes sense."""
	minimo, massimo, predefinito = limiti
	try:
		numero = int(valore or 0)
	except (TypeError, ValueError):
		numero = 0
	return min(max(numero, minimo), massimo) if numero else predefinito


def piu_mesi(giorno: datetime.date, mesi: int) -> datetime.date:
	"""The same day ``mesi`` months later; the last of the month when that month is
	shorter (31 January and a month: 28 or 29 February)."""
	totale = giorno.month - 1 + mesi
	anno, mese = giorno.year + totale // 12, totale % 12 + 1
	return datetime.date(anno, mese, min(giorno.day, calendar.monthrange(anno, mese)[1]))


def giorni_sospesi(sospensioni: list[tuple[datetime.date, datetime.date]]) -> int:
	"""How many days the subscription stood still: each suspension counts its first
	and its last day."""
	return sum(max((a - da).days + 1, 0) for da, a in sospensioni)


def fine(inizio: datetime.date, mesi: int, sospensioni=()) -> datetime.date:
	"""The last day: the day before the same day ``mesi`` months later, later by the
	days it was suspended."""
	return piu_mesi(inizio, mesi) - UN_GIORNO + datetime.timedelta(days=giorni_sospesi(list(sospensioni)))


def sospesa(giorno: datetime.date, sospensioni) -> bool:
	return any(da <= giorno <= a for da, a in sospensioni)


def problema_della_sospensione(
	da: datetime.date | None,
	a: datetime.date | None,
	inizio: datetime.date,
	ultimo: datetime.date,
	gia: list[tuple[datetime.date, datetime.date]],
	massimo_giorni: int = 0,
) -> str | None:
	"""Why a suspension from ``da`` to ``a`` cannot be: both days, in order, within
	the subscription, not over another one, within the days the type allows.
	``None`` when it can."""
	if not da or not a:
		return "Both days are needed"
	if a < da:
		return "The suspension ends before it starts"
	if da < inizio or da > ultimo:
		return "The suspension starts outside the subscription"
	if any(da <= sua_a and suo_da <= a for suo_da, sua_a in gia):
		return "It overlaps another suspension"
	if massimo_giorni and giorni_sospesi([*gia, (da, a)]) > massimo_giorni:
		return "More days than the type allows"
	return None


def rate(
	inizio: datetime.date, mesi: int, prezzo: float, pagamento: str
) -> list[tuple[datetime.date, float]]:
	"""When it is paid and how much: all on the first day, or one instalment a month
	on the same day; the last instalment takes what rounding left over."""
	prezzo = round(float(prezzo or 0), 2)
	if pagamento != MENSILE or mesi <= 1:
		return [(inizio, prezzo)]
	quota = round(prezzo / mesi, 2)
	fatto = [(piu_mesi(inizio, i), quota) for i in range(mesi)]
	fatto[-1] = (fatto[-1][0], round(prezzo - quota * (mesi - 1), 2))
	return fatto


def periodo(
	giorno: datetime.date, inizio: datetime.date, come: str
) -> tuple[datetime.date, datetime.date] | None:
	"""The days within which ``giorno``'s entries are counted: its week, Monday to
	Sunday, or the subscription's month it falls in. ``None`` when entries are not
	counted."""
	if come == A_SETTIMANA:
		lunedi = giorno - datetime.timedelta(days=giorno.weekday())
		return lunedi, lunedi + datetime.timedelta(days=6)
	if come == AL_MESE:
		mesi = (giorno.year - inizio.year) * 12 + giorno.month - inizio.month
		if piu_mesi(inizio, mesi) > giorno:
			mesi -= 1
		mesi = max(mesi, 0)
		return piu_mesi(inizio, mesi), piu_mesi(inizio, mesi + 1) - UN_GIORNO
	return None


def usati(ingressi: list[str], perse_contano: bool = True) -> int:
	"""How many entries the appointments take: done and booked; missed ones when the
	type says so; a cancelled one none."""
	return ingressi.count(FATTA) + ingressi.count(PRENOTATA) + (ingressi.count(PERSA) if perse_contano else 0)


def stato(
	oggi: datetime.date,
	ultimo: datetime.date,
	sospensioni=(),
	chiuso: bool = False,
) -> str:
	"""Closed by hand, expired past its last day, suspended today, or active - also
	when it is sold to start later."""
	if chiuso:
		return CHIUSO
	if oggi > ultimo:
		return SCADUTO
	if sospesa(oggi, sospensioni):
		return SOSPESO
	return ATTIVO


def si_aggiunge(
	chiuso: bool,
	giorno: datetime.date,
	inizio: datetime.date,
	ultimo: datetime.date,
	sospensioni,
	usati_nel_periodo: int,
	quanti: int,
	come: str,
) -> bool:
	"""Whether an appointment of a comprised service on ``giorno`` uses an entry: the
	subscription is not closed, the day is within its days and not suspended, and an
	entry is left in that week or month."""
	if chiuso or giorno < inizio or giorno > ultimo or sospesa(giorno, sospensioni):
		return False
	if come == ILLIMITATI:
		return True
	return usati_nel_periodo < max(int(quanti or 0), 0)


def da_ricordare(oggi: datetime.date, ultimo: datetime.date, giorni_prima: int) -> bool:
	"""Whether the reminder of the end is due: from ``giorni_prima`` days before the
	last day, until it."""
	return ultimo - datetime.timedelta(days=max(int(giorni_prima or 0), 0)) <= oggi <= ultimo


def rinnovo_da(ultimo: datetime.date) -> datetime.date:
	"""The renewal starts the day after the last one."""
	return ultimo + UN_GIORNO
