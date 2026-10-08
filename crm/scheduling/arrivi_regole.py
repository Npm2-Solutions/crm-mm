# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""«I'm here» from the person's phone, without a site: when the client area offers
it. The engine is `crm.area.api.check_in`, which marks the person arrived the way
the desk does (`crm.scheduling.esiti`).

- **On the day, around the time**: from half an hour before the appointment
  starts until it ends - earlier is still on the way, later is over.
- **Only a place still waiting**: an appointment cancelled, or a place cancelled,
  already arrived or with its outcome said, has nothing to check in.

Pure: tested with plain `unittest` (`crm/tests/test_arrivi_regole.py`).
"""

from __future__ import annotations

import datetime

#: How long before the start the person may say they are here.
ANTICIPO = datetime.timedelta(minutes=30)
#: The appointments that are still to come, and a place still waiting for its outcome.
ATTIVI = ("Scheduled", "Confirmed")
IN_ATTESA = "Booked"

#: Why «I'm here» is not offered: too early, over, cancelled, already said.
PRESTO, FINITO, ANNULLATO, GIA_DETTO = "early", "over", "cancelled", "already"


def finestra(
	inizio: datetime.datetime, fine: datetime.datetime | None
) -> tuple[datetime.datetime, datetime.datetime]:
	"""From when to when the person may say they are here: an appointment without
	its end counts as over when it starts."""
	return inizio - ANTICIPO, fine if fine and fine > inizio else inizio


def perche_no(
	inizio: datetime.datetime,
	fine: datetime.datetime | None,
	adesso: datetime.datetime,
	stato: str | None,
	stato_del_posto: str | None,
) -> str | None:
	"""Why the person may not say they are here now, or None when they may."""
	if stato not in ATTIVI or stato_del_posto == "Cancelled":
		return ANNULLATO
	if stato_del_posto != IN_ATTESA:
		return GIA_DETTO
	dal, al = finestra(inizio, fine)
	if adesso < dal:
		return PRESTO
	if adesso >= al:
		return FINITO
	return None


def tra_quanto(inizio: datetime.datetime, fine: datetime.datetime | None, adesso: datetime.datetime) -> dict:
	"""For the area's screen: in how many seconds «I'm here» opens and closes,
	from now - the phone's clock may not be the centre's."""
	dal, al = finestra(inizio, fine)
	return {
		"opens_in": max(int((dal - adesso).total_seconds()), 0),
		"closes_in": max(int((al - adesso).total_seconds()), 0),
	}
