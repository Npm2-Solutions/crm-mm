# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Online visits, without a site: where the room is and when the person enters.
The engine is `crm.scheduling.visite_online`; the area's door is
`crm.area.api.enter_online_visit`.

- **A room nobody guesses.** On the agency's video server (a Jitsi Meet) each
  appointment gets a room of its own, its name random: 120 bits, never the
  person's name nor the appointment's code. Made once, kept on the appointment.
- **Which link.** The one the appointment already has (made before, or pasted by
  the desk) first; then a room on the agency's server; then the professional's
  own fixed room (Meet, Zoom, Teams). Only an https address.
- **When the person enters.** From a quarter of an hour before the start until
  the end, by the server's clock; earlier the area says when it opens.

Pure: tested with plain `unittest` (`crm/tests/test_visite_online_regole.py`).
"""

from __future__ import annotations

import base64
import datetime
import secrets
from urllib.parse import urlsplit

#: How long before the start the person may enter.
ANTICIPO = datetime.timedelta(minutes=15)
#: The appointments one still enters - one marked done while it runs too, its
#: person may have dropped out of the room -, and the places that still count.
ATTIVI = ("Scheduled", "Confirmed", "Completed")
POSTI_ATTIVI = ("Booked", "Arrived", "Attended")

#: Why the person may not enter now: too early, over, cancelled, no room.
PRESTO, FINITO, ANNULLATO, SENZA_STANZA = "early", "over", "cancelled", "no_room"


def nome_della_stanza() -> str:
	"""A room's name: 24 small letters and digits, 120 random bits."""
	return base64.b32encode(secrets.token_bytes(15)).decode("ascii").lower()


def link_valido(valore: str | None) -> bool:
	"""An https address with a host: what a room's link may be."""
	if not valore or any(c.isspace() for c in valore.strip()):
		return False
	parti = urlsplit(valore.strip())
	return parti.scheme == "https" and bool(parti.hostname)


def base_del_server(valore) -> str | None:
	"""The video server's address, as the agency wrote it: a string or ``{"url": …}``
	(`dottorcloud_video` in the site's configuration), https only, no query, without
	the trailing slash. Anything else is no server."""
	if isinstance(valore, dict):
		valore = valore.get("url")
	if not isinstance(valore, str) or not link_valido(valore):
		return None
	parti = urlsplit(valore.strip())
	if parti.query or parti.fragment:
		return None
	return f"https://{parti.netloc}{parti.path.rstrip('/')}"


def stanza(base: str, nome: str) -> str:
	"""The room's address on the server."""
	return f"{base.rstrip('/')}/{nome}"


def link_da_dare(
	gia: str | None, server: str | None, del_professionista: str | None, nome: str | None = None
) -> str | None:
	"""The link an online visit gets: the one it has, a new room on the agency's
	server, the professional's own room, or none."""
	if gia and gia.strip():
		return gia.strip()
	if server:
		return stanza(server, nome or nome_della_stanza())
	if del_professionista and link_valido(del_professionista):
		return del_professionista.strip()
	return None


def finestra(
	inizio: datetime.datetime, fine: datetime.datetime | None
) -> tuple[datetime.datetime, datetime.datetime]:
	"""From when to when the person may enter: an appointment without its end
	closes when it starts."""
	return inizio - ANTICIPO, fine if fine and fine > inizio else inizio


def perche_no(
	inizio: datetime.datetime,
	fine: datetime.datetime | None,
	adesso: datetime.datetime,
	stato: str | None,
	stato_del_posto: str | None,
	link: str | None,
) -> str | None:
	"""Why the person may not enter now, or None when they may."""
	if stato == "Cancelled" or stato_del_posto == "Cancelled":
		return ANNULLATO
	if stato not in ATTIVI or stato_del_posto not in POSTI_ATTIVI:
		# its outcome said: done, or nobody came
		return FINITO
	if not link:
		return SENZA_STANZA
	dal, al = finestra(inizio, fine)
	if adesso < dal:
		return PRESTO
	if adesso >= al:
		return FINITO
	return None


def tra_quanto(inizio: datetime.datetime, fine: datetime.datetime | None, adesso: datetime.datetime) -> dict:
	"""For the area's screen: in how many seconds the door opens and closes, from
	now - the phone's clock may not be the centre's - and at what time it opens."""
	dal, al = finestra(inizio, fine)
	return {
		"opens_in": max(int((dal - adesso).total_seconds()), 0),
		"closes_in": max(int((al - adesso).total_seconds()), 0),
		"opens_at": dal.strftime("%H:%M"),
	}
