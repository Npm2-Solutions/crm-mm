# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""More than one location in one centre (docs/crm/62), without a site.

- **One location is no location.** Every screen that names a location shows it
  only where the centre has two or more switched on (`piu_sedi`): a centre with
  one, or none, works as it always did.
- **Where a room is.** A room names its location; a room that names none (a
  portable ultrasound, a room of a centre with one location) serves them all.
- **Where a professional works.** Each line of their week, and each date
  override, may name a location; one that names none is good anywhere - the
  room decides.
- **Where an appointment is.** Its rooms' location first; else the location of
  the professional's shift it falls in; else the one the desk chose; else, with
  a single location switched on, that one.
- **A service tied to a room.** Booked in another location, it takes a room of
  the same kind there: «Studio 2» in Milan is «a room» in Monza.
- **The address** the person reads: street, postcode, city and province, as
  an Italian envelope writes it.

Pure: tested with plain `unittest` (`crm/tests/test_sedi_regole.py`).
"""

from __future__ import annotations

from collections.abc import Iterable
from urllib.parse import urlsplit


def piu_sedi(attive: Iterable) -> bool:
	"""Whether the centre has more than one location switched on."""
	return len(list(attive or [])) > 1


def serve(sede_della_cosa: str | None, sede: str | None) -> bool:
	"""Whether a room, or a line of a shift, of `sede_della_cosa` serves `sede`:
	one that names no location serves them all, and no location asked takes all."""
	return not sede or not sede_della_cosa or sede_della_cosa == sede


def della_sede(righe: Iterable, sede: str | None, campo: str = "centre_location") -> list:
	"""The lines (of a week, of overrides) good at `sede`."""
	return [riga for riga in righe or [] if serve(_valore(riga, campo), sede)]


def stanze_al_posto(
	richiesta: str | None,
	tipo: str | None,
	stanze: Iterable[dict],
	sede: str | None,
) -> list[str]:
	"""The rooms that can satisfy a service's requirement at `sede`.

	`stanze` are the enabled ones, each `{name, resource_type, centre_location}`.
	A requirement for one room keeps it where it serves the location; a room of
	another location gives way to the location's rooms of its kind. A requirement
	by kind takes the kind's rooms of the location."""
	stanze = list(stanze or [])
	if richiesta:
		propria = next((s for s in stanze if s["name"] == richiesta), None)
		if not propria:
			return []
		if serve(propria.get("centre_location"), sede):
			return [richiesta]
		tipo = propria.get("resource_type")
	return [
		s["name"]
		for s in stanze
		if (not tipo or s.get("resource_type") == tipo) and serve(s.get("centre_location"), sede)
	]


def sede_dell_appuntamento(
	delle_stanze: Iterable[str | None],
	del_turno: str | None = None,
	scelta: str | None = None,
	attive: Iterable[str] = (),
) -> str | None:
	"""Where an appointment is: its rooms', else its professional's shift's, else
	the one chosen, else the only location switched on."""
	for sede in delle_stanze or []:
		if sede:
			return sede
	if del_turno:
		return del_turno
	if scelta:
		return scelta
	attive = list(attive or [])
	return attive[0] if len(attive) == 1 else None


def in_conflitto(sede_del_turno: str | None, sedi_delle_stanze: Iterable[str | None]) -> str | None:
	"""The room's location where a professional's shift is at another one: an
	appointment cannot be in two places."""
	if not sede_del_turno:
		return None
	for sede in sedi_delle_stanze or []:
		if sede and sede != sede_del_turno:
			return sede
	return None


def sedi_del_servizio(
	richieste: Iterable[dict],
	stanze: Iterable[dict],
	sedi_dei_professionisti: Iterable[Iterable[str | None]],
	attive: Iterable[str],
) -> list[str] | None:
	"""The locations a service can be held in, for the booking page; None where
	it can be held in any.

	`richieste` are its required rooms (`{resource, resource_type}`), `stanze`
	the enabled ones, `sedi_dei_professionisti` the locations each of its
	professionals' shifts name ('' or None for a line good anywhere)."""
	attive = list(attive or [])
	stanze = list(stanze or [])
	richieste = [r for r in richieste or [] if r.get("resource") or r.get("resource_type")]
	possibili = set(attive)
	for richiesta in richieste:
		dove = {
			sede
			for sede in attive
			if stanze_al_posto(richiesta.get("resource"), richiesta.get("resource_type"), stanze, sede)
		}
		possibili &= dove
	persone = [set(sedi) for sedi in sedi_dei_professionisti or []]
	if persone:
		dove = set()
		for sedi in persone:
			if not sedi or any(not s for s in sedi):
				dove |= set(attive)
			else:
				dove |= sedi & set(attive)
		possibili &= dove
	if possibili == set(attive):
		return None
	return [sede for sede in attive if sede in possibili]


def indirizzo(sede: dict | None) -> str:
	"""«Via Roma 1, 20900 Monza (MB)»: what a person reads to find it."""
	if not sede:
		return ""
	via = " ".join(str(sede.get("address_line") or "").split())
	citta = " ".join(
		parte
		for parte in (
			str(sede.get("pincode") or "").strip(),
			str(sede.get("city") or "").strip(),
			f"({str(sede.get('province')).strip().upper()})" if sede.get("province") else "",
		)
		if parte
	)
	return ", ".join(parte for parte in (via, citta) if parte)


def dove(sede: dict | None) -> str:
	"""The location named and found: «Sede di Monza, Via Roma 1, 20900 Monza (MB)»."""
	if not sede:
		return ""
	nome = " ".join(str(sede.get("location_name") or "").split())
	resto = indirizzo(sede)
	if nome and resto:
		return f"{nome}, {resto}"
	return nome or resto


def link_valido(valore: str | None) -> bool:
	"""A map link is an https address."""
	try:
		parti = urlsplit(str(valore or "").strip())
	except ValueError:
		return False
	return parti.scheme == "https" and bool(parti.netloc)


def _valore(riga, campo: str):
	if isinstance(riga, dict):
		return riga.get(campo)
	return getattr(riga, campo, None)
