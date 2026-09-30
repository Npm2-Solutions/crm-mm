# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Waiting lists without a site (design.md, "Cosa si aggiunge al CRM": "le liste
d'attesa"). The engine is `crm.scheduling.attese`; here, what it decides.

- **Who waits for what**: a service, maybe with one professional, on some days
  and in some parts of the day, from a day and until a day; or a place in a class
  that is full.
- **What frees up goes to who waits, in their order**: the urgent first, then who
  joined first. A place goes to a few at once (the centre says how many), and the
  first who confirms takes it; the others keep their place in the line.
- **An offer waits for its answer** the hours the centre gives, never until the
  place is about to start: past its time the next ones get it.
- **A place is offered once** to the same person: no again after "no thanks", nor
  after silence.

Pure: tested with plain `unittest` (`crm/tests/test_attese_regole.py`).
"""

from __future__ import annotations

import datetime
from collections.abc import Iterable
from dataclasses import dataclass, field

# ------------------------------------------------------------------ the words

#: An entry in the list.
IN_ATTESA, PROPOSTA, PRENOTATA, SCADUTA, TOLTA = "Waiting", "Offered", "Booked", "Expired", "Removed"
STATI = (IN_ATTESA, PROPOSTA, PRENOTATA, SCADUTA, TOLTA)
#: The ones still in the line.
APERTE = (IN_ATTESA, PROPOSTA)

#: An offer of a place.
INVIATA, ACCETTATA, RIFIUTATA, SENZA_RISPOSTA, PRESA = "Sent", "Accepted", "Declined", "Expired", "Taken"
STATI_PROPOSTA = (INVIATA, ACCETTATA, RIFIUTATA, SENZA_RISPOSTA, PRESA)

#: Where one joins the list.
DAL_BANCO, ONLINE, DALL_AREA = "Desk", "Online", "Client area"
FONTI = (DAL_BANCO, ONLINE, DALL_AREA)

#: How the offers go: the email is always there.
WHATSAPP, SMS, EMAIL = "WhatsApp", "SMS", "Email"
CANALI = (WHATSAPP, SMS, EMAIL)

GIORNI = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

#: The parts of the day a person picks: /prenota groups its times the same way.
PARTI = {
	"morning": (datetime.time(0, 0), datetime.time(13, 0)),
	"afternoon": (datetime.time(13, 0), datetime.time(18, 0)),
	"evening": (datetime.time(18, 0), datetime.time(23, 59, 59)),
}

#: An offer is never answered in less than this, nor closer than this to its start.
MINIMO_PER_RISPONDERE = datetime.timedelta(minutes=15)
MARGINE_PRIMA_DELL_INIZIO = datetime.timedelta(hours=1)

#: What the centre may choose, and what it gets if it chooses nothing.
PER_VOLTA = (1, 10, 3)
ORE_PER_RISPONDERE = (1, 72, 2)
GIORNI_AVANTI = (1, 90, 30)
#: How long an entry made online waits, unless the person says until when.
GIORNI_IN_LISTA = (1, 365, 30)


def entro(valore, limiti: tuple[int, int, int]) -> int:
	"""A number the centre chose, kept within what makes sense: ``limiti`` is
	(least, most, default)."""
	minimo, massimo, predefinito = limiti
	try:
		numero = int(valore or 0)
	except (TypeError, ValueError):
		numero = 0
	return min(max(numero, minimo), massimo) if numero else predefinito


# ------------------------------------------------------------------ when the person can


def _minuti(ora) -> int:
	"""Minutes from midnight; the last second of the day is its end."""
	if isinstance(ora, datetime.timedelta):
		secondi = int(ora.total_seconds())
	elif isinstance(ora, datetime.time):
		secondi = ora.hour * 3600 + ora.minute * 60 + ora.second
	else:
		parti = [int(float(p)) for p in str(ora).split(":")]
		secondi = (
			parti[0] * 3600 + (parti[1] if len(parti) > 1 else 0) * 60 + (parti[2] if len(parti) > 2 else 0)
		)
	return 24 * 60 if secondi >= 24 * 3600 - 1 else secondi // 60


def fasce(righe: Iterable) -> dict[int, list[tuple[int, int]]]:
	"""The person's rows (workday, start, end) as windows per weekday (0 is Monday),
	in minutes, the ones that touch joined: "morning" and "afternoon" are one window."""
	per_giorno: dict[int, list[tuple[int, int]]] = {}
	for riga in righe or []:
		giorno = riga.get("workday") if isinstance(riga, dict) else getattr(riga, "workday", None)
		inizio = riga.get("start_time") if isinstance(riga, dict) else getattr(riga, "start_time", None)
		fine = riga.get("end_time") if isinstance(riga, dict) else getattr(riga, "end_time", None)
		if giorno not in GIORNI or inizio is None or fine is None:
			continue
		da, a = _minuti(inizio), _minuti(fine)
		if a > da:
			per_giorno.setdefault(GIORNI.index(giorno), []).append((da, a))
	for giorno, finestre in per_giorno.items():
		finestre.sort()
		unite = [finestre[0]]
		for da, a in finestre[1:]:
			if da <= unite[-1][1]:
				unite[-1] = (unite[-1][0], max(unite[-1][1], a))
			else:
				unite.append((da, a))
		per_giorno[giorno] = unite
	return per_giorno


def adatto(
	finestre: dict[int, list[tuple[int, int]]], inizio: datetime.datetime, fine: datetime.datetime
) -> bool:
	"""Whether a place, in the centre's own time, falls within what the person can:
	the whole of it, on one of their days. No days chosen: any time the centre is open."""
	if not finestre:
		return True
	giorno = inizio.weekday()
	da = inizio.hour * 60 + inizio.minute
	durata = int((fine - inizio).total_seconds() // 60)
	return any(s <= da and da + durata <= e for s, e in finestre.get(giorno, []))


def righe_da(giorni: Iterable[str], parti: Iterable[str]) -> list[dict]:
	"""Days and parts of the day, as a person picks them, into rows. No days: every
	day; no parts: the whole day."""
	giorni = [g for g in GIORNI if g in set(giorni or [])] or list(GIORNI)
	parti = [p for p in PARTI if p in set(parti or [])]
	if not parti and len(giorni) == len(GIORNI):
		return []
	finestre = [PARTI[p] for p in parti] or [(datetime.time(0, 0), datetime.time(23, 59, 59))]
	return [
		{"workday": g, "start_time": da.strftime("%H:%M:%S"), "end_time": a.strftime("%H:%M:%S")}
		for g in giorni
		for da, a in finestre
	]


def scelte_da(righe: Iterable) -> dict | None:
	"""The rows back as days and parts, when they were made that way; ``None`` for
	hours written by hand, which are shown as they are."""
	righe = list(righe or [])
	if not righe:
		return {"days": [], "parts": []}
	per_giorno: dict[str, set[str]] = {}
	for riga in righe:
		giorno = riga.get("workday") if isinstance(riga, dict) else getattr(riga, "workday", None)
		inizio = riga.get("start_time") if isinstance(riga, dict) else getattr(riga, "start_time", None)
		fine = riga.get("end_time") if isinstance(riga, dict) else getattr(riga, "end_time", None)
		finestra = (_minuti(inizio), _minuti(fine))
		parte = next(
			(nome for nome, (da, a) in PARTI.items() if (_minuti(da), _minuti(a)) == finestra),
			"all" if finestra == (0, 24 * 60) else None,
		)
		if parte is None or giorno not in GIORNI:
			return None
		per_giorno.setdefault(giorno, set()).add(parte)
	insiemi = {frozenset(p) for p in per_giorno.values()}
	if len(insiemi) != 1:
		return None
	parti = next(iter(insiemi))
	if "all" in parti:
		if len(parti) > 1:
			return None
		parti = frozenset()
	return {
		"days": [g for g in GIORNI if g in per_giorno],
		"parts": [p for p in PARTI if p in parti],
	}


# ------------------------------------------------------------------ the places


@dataclass(frozen=True)
class Posto:
	"""A place: when, with whom, or a seat in a class that is on already."""

	inizio: datetime.datetime
	fine: datetime.datetime
	staff: tuple[str, ...] = ()
	sessione: str | None = None
	#: How many people it takes: the seats left in a class, one otherwise.
	capienza: int = 1

	@property
	def chiave(self) -> str:
		inizio = self.inizio.astimezone(datetime.UTC).isoformat()
		return "|".join([inizio, self.sessione or "", ",".join(sorted(self.staff))])


def si_toccano(a: Posto, b: Posto) -> bool:
	"""Whether two places are the same room for the same people: a seat in the same
	class, or the same professional at the same time."""
	if a.sessione or b.sessione:
		return a.sessione == b.sessione
	return a.inizio < b.fine and b.inizio < a.fine and bool(set(a.staff) & set(b.staff))


@dataclass
class Attesa:
	"""An entry as the choice sees it: its name, the places that fit it (earliest
	first), and the ones it was offered already."""

	nome: str
	posti: list[Posto] = field(default_factory=list)
	gia: set[str] = field(default_factory=set)


def scegli(attese: Iterable[Attesa], in_sospeso: Iterable[Posto], per_volta: int) -> list[tuple[str, Posto]]:
	"""Who gets which place now. The entries come in their order; each gets the
	first place that fits it and was not offered to it before, while fewer than
	``per_volta`` wait on that place for each person it takes (the ones waiting
	already count). An entry with nothing that fits gets nothing."""
	per_volta = max(int(per_volta or 1), 1)
	aperte = list(in_sospeso)
	fatto: list[tuple[str, Posto]] = []
	for attesa in attese:
		for posto in attesa.posti:
			if posto.chiave in attesa.gia:
				continue
			gia_offerto = sum(1 for altro in aperte if si_toccano(altro, posto))
			if gia_offerto >= per_volta * max(posto.capienza, 1):
				continue
			fatto.append((attesa.nome, posto))
			aperte.append(posto)
			break
	return fatto


# ------------------------------------------------------------------ time


def finestra(
	oggi: datetime.date,
	giorni_avanti: int,
	dal: datetime.date | None = None,
	fino: datetime.date | None = None,
) -> tuple[datetime.date, datetime.date] | None:
	"""The days an entry looks at: from today, or its first day, to the days the
	centre looks ahead, or its last day. ``None`` when nothing is left."""
	primo = max(oggi, dal) if dal else oggi
	ultimo = oggi + datetime.timedelta(days=max(int(giorni_avanti or 0), 0))
	if fino:
		ultimo = min(ultimo, fino)
	return (primo, ultimo) if ultimo >= primo else None


def scaduta(fino: datetime.date | None, oggi: datetime.date) -> bool:
	"""An entry whose last day has gone waits no more."""
	return bool(fino) and fino < oggi


def scadenza(adesso: datetime.datetime, inizio: datetime.datetime, ore: int) -> datetime.datetime | None:
	"""Until when an offer waits for its answer: the hours the centre gives, and
	never past an hour before the place starts. ``None`` when that leaves too little
	to answer: the place is too close to offer."""
	fine = min(adesso + datetime.timedelta(hours=max(int(ore or 0), 1)), inizio - MARGINE_PRIMA_DELL_INIZIO)
	return fine if fine - adesso >= MINIMO_PER_RISPONDERE else None


# ------------------------------------------------------------------ what frees a place

#: The appointments still to happen.
ATTIVI = ("Scheduled", "Confirmed")


def libera(prima: dict | None, dopo: dict | None, adesso: datetime.datetime) -> bool:
	"""Whether a change to an appointment frees time or a seat somebody could wait
	for: it was going to happen, and now it is cancelled or gone, somewhere else,
	with another professional or room, or with fewer people. ``dopo`` is ``None``
	for one deleted. Each holds status, inizio, fine, staff, risorse, persone."""
	if not prima or prima.get("status") not in ATTIVI or prima["inizio"] <= adesso:
		return False
	if dopo is None or dopo.get("status") not in ATTIVI:
		return True
	return (
		dopo["inizio"] != prima["inizio"]
		or dopo["fine"] != prima["fine"]
		or set(dopo.get("staff") or ()) != set(prima.get("staff") or ())
		or set(dopo.get("risorse") or ()) != set(prima.get("risorse") or ())
		or int(dopo.get("persone") or 0) < int(prima.get("persone") or 0)
	)


# ------------------------------------------------------------------ telling


def canali_offerti(whatsapp: bool, sms: bool) -> list[str]:
	"""The ways the centre sends an offer: WhatsApp and SMS where it set them up,
	the email always."""
	return [c for c, si in ((WHATSAPP, whatsapp), (SMS, sms), (EMAIL, True)) if si]


def come_mandare(scelto: str | None, offerti: Iterable[str], email: bool, numero: bool) -> list[str]:
	"""The channels to try, in order: the one chosen, if the centre offers it and
	the person has what it needs; then the email."""
	offerti = list(offerti)
	possibili = [c for c in offerti if (c == EMAIL and email) or (c != EMAIL and numero)]
	ordine = ([scelto] if scelto in possibili else []) + ([EMAIL] if EMAIL in possibili else [])
	return list(dict.fromkeys(ordine))


def variabili(quante: int, nome: str, servizio: str, quando: str, link: str) -> list[str]:
	"""A WhatsApp template's variables, in their order: the name, the service, the
	day and time, the link. A template with fewer takes the first ones."""
	return [nome, servizio, quando, link][: max(int(quante or 0), 0)]
