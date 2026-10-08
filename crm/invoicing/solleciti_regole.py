# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The payment reminders' rules without a site: when an invoice still to collect
is due, when its next reminder leaves, by which way.

- **Due** on the last day of its payment schedule (`CRM Invoice Payment.due_date`),
  else on the day it was issued: a reminder never comes before the whole amount
  was owed.
- **The first** reminder leaves ``primo`` days after that, each next one ``ogni``
  days after the one before, at most ``massimo``; an amount under ``minimo`` is
  never reminded.
- **By email**, and **by SMS** where the centre wants it too, never to a person who
  wrote STOP to the centre's SMS.
"""

from __future__ import annotations

import datetime
from collections.abc import Iterable

EMAIL, SMS = "email", "sms"

#: What a centre starts from (Settings > Invoicing > Payments and reminders).
PRIMO, OGNI, MASSIMO, MINIMO = 7, 14, 2, 10.0

#: How the invoice's log says how a reminder went.
INVIATO, NON_INVIATO, FALLITO = "sent", "not_sent", "failed"


def numeri(primo, ogni, massimo, minimo) -> tuple[int, int, int, float]:
	"""The settings as the rules read them: whole days of at least one, at most a
	year; one to ten reminders; an amount never below zero. Nothing set is the
	default."""

	def intero(valore, predefinito: int, basso: int, alto: int) -> int:
		try:
			numero = int(valore) if valore not in (None, "") else predefinito
		except (TypeError, ValueError):
			numero = predefinito
		return max(basso, min(alto, numero))

	try:
		soglia = float(minimo) if minimo not in (None, "") else MINIMO
	except (TypeError, ValueError):
		soglia = MINIMO
	return (
		intero(primo, PRIMO, 1, 365),
		intero(ogni, OGNI, 1, 365),
		intero(massimo, MASSIMO, 1, 10),
		max(0.0, soglia),
	)


def scadenza(emessa: datetime.date, scadenze: Iterable[datetime.date | None] = ()) -> datetime.date:
	"""The day the whole invoice was owed: its schedule's last due date, else the
	day it was issued."""
	giorni = [giorno for giorno in scadenze if giorno]
	return max(giorni) if giorni else emessa


def prossimo(
	scade: datetime.date, inviati: Iterable[datetime.date], primo: int, ogni: int, massimo: int
) -> datetime.date | None:
	"""The day the next reminder is due, or None once ``massimo`` were tried."""
	giorni = sorted(inviati)
	if len(giorni) >= massimo:
		return None
	if not giorni:
		return scade + datetime.timedelta(days=primo)
	return giorni[-1] + datetime.timedelta(days=ogni)


def da_sollecitare(
	oggi: datetime.date,
	scade: datetime.date,
	inviati: Iterable[datetime.date],
	importo: float,
	*,
	primo: int = PRIMO,
	ogni: int = OGNI,
	massimo: int = MASSIMO,
	minimo: float = MINIMO,
) -> bool:
	"""Whether an invoice still to collect gets a reminder today."""
	if not importo or importo <= 0 or importo < minimo:
		return False
	giorno = prossimo(scade, inviati, primo, ogni, massimo)
	return giorno is not None and giorno <= oggi


def canali(per_email: bool, per_sms: bool, ha_email: bool, ha_numero: bool, fermato: bool) -> list[str]:
	"""The ways a reminder goes, in this order: each one the centre wants that
	reaches the person; an SMS never to who wrote STOP."""
	vie = []
	if per_email and ha_email:
		vie.append(EMAIL)
	if per_sms and ha_numero and not fermato:
		vie.append(SMS)
	return vie


def quanti(righe: Iterable[dict]) -> dict:
	"""What the screens say of an invoice's reminders: how many reached the person
	and the last day one did, from its log's rows (``status``, ``occurred_on``)."""
	giorni = sorted(str(riga["occurred_on"])[:10] for riga in righe if riga.get("status") == INVIATO)
	return {"count": len(giorni), "last": giorni[-1] if giorni else None}
