# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A sheet of appointments from another program, without a site: which column is
what, a row as an appointment, what is wrong with it, the key that keeps it from
being brought in twice. Tested with plain `unittest`.

The person is read as the people's sheet reads them (`regole.persona`): the same
columns, the same Italian ways of writing a date or a number. The appointment's
day and hours as an Italian sheet writes them too (02/03/2025, 9.30, «45 min»);
how it went from the words a program uses («eseguito», «disdetto», «assente»),
else by the clock: what is past was attended, what is to come is booked. The
service, the professional and the room are matched by name to what the centre
has, and the person's eye on the preview decides the rest.
"""

from __future__ import annotations

import datetime
import hashlib
import re

from crm.importazione import regole

#: The person's fields an appointments' sheet may carry, as the people's sheet names them.
CAMPI_DELLA_PERSONA = (
	"full_name",
	"first_name",
	"last_name",
	"email",
	"mobile_no",
	"phone",
	"fiscal_code",
	"birth_date",
)

#: An appointment's field and the names its column goes by, written plain (`regole.semplice`).
COLONNE = {
	"date": (
		"data",
		"data appuntamento",
		"data visita",
		"data prestazione",
		"giorno",
		"date",
		"appointment date",
		"day",
	),
	"start": (
		"ora",
		"ora inizio",
		"ora di inizio",
		"inizio",
		"orario",
		"ora appuntamento",
		"dalle",
		"start",
		"start time",
		"time",
	),
	"end": ("ora fine", "ora di fine", "fine", "alle", "end", "end time"),
	"duration": ("durata", "durata min", "durata minuti", "minuti", "duration", "minutes", "length"),
	"service": (
		"prestazione",
		"servizio",
		"trattamento",
		"tipo visita",
		"tipo di visita",
		"tipo appuntamento",
		"visita",
		"service",
		"treatment",
		"appointment type",
	),
	"professional": (
		"professionista",
		"operatore",
		"medico",
		"dottore",
		"terapista",
		"specialista",
		"terapeuta",
		"professional",
		"practitioner",
		"doctor",
		"staff",
	),
	"room": ("ambulatorio", "stanza", "sala", "studio", "box", "room"),
	"status": ("stato", "esito", "stato appuntamento", "status", "outcome"),
	"notes": ("note", "annotazioni", "osservazioni", "notes"),
	"external_id": (
		"id",
		"id appuntamento",
		"codice appuntamento",
		"n appuntamento",
		"numero appuntamento",
		"codice",
		"appointment id",
	),
}

#: How it went, in DottorCloud's states.
SVOLTO = "Completed"
ASSENTE = "No Show"
ANNULLATO = "Cancelled"
PRENOTATO = "Scheduled"

#: The words a program says how it went with, written plain.
PAROLE_DELLO_STATO = {
	ANNULLATO: (
		"annullato",
		"annullata",
		"disdetto",
		"disdetta",
		"cancellato",
		"cancellata",
		"spostato",
		"spostata",
		"cancelled",
		"canceled",
	),
	ASSENTE: (
		"assente",
		"non presentato",
		"non presentata",
		"non si e presentato",
		"non si e presentata",
		"non venuto",
		"non venuta",
		"mancato",
		"mancata",
		"no show",
		"noshow",
		"missed",
	),
	SVOLTO: (
		"eseguito",
		"eseguita",
		"svolto",
		"svolta",
		"effettuato",
		"effettuata",
		"completato",
		"completata",
		"concluso",
		"conclusa",
		"presente",
		"fatto",
		"fatta",
		"completed",
		"attended",
		"done",
	),
	PRENOTATO: (
		"prenotato",
		"prenotata",
		"confermato",
		"confermata",
		"da fare",
		"scheduled",
		"booked",
		"confirmed",
	),
}

#: How a participant came, by the appointment's state.
PARTECIPANTE = {SVOLTO: "Attended", ASSENTE: "No Show", ANNULLATO: "Cancelled", PRENOTATO: "Booked"}

#: The titles a sheet writes before a professional's name.
TITOLI = ("dott ssa", "dottssa", "dott", "dr ssa", "dr", "dssa", "prof ssa", "prof", "ft", "sig ra", "sig")

#: Problems, in English, said in the centre's language by whoever shows them.
SENZA_DATA = "No date"
SENZA_ORA = "No start time"
ORA_SBAGLIATA = "The time {0} is not a time"
DURATA_SBAGLIATA = "The duration {0} is not a duration"
FINE_PRIMA = "It ends before it starts"


def riconosci(intestazione: list) -> dict[int, str]:
	"""Which column is which field: the appointment's first, then the person's,
	each field once, the first column that says it."""
	per_nome = {alias: campo for campo, nomi in COLONNE.items() for alias in nomi}
	for campo in CAMPI_DELLA_PERSONA:
		for alias in regole.COLONNE[campo]:
			per_nome.setdefault(alias, campo)
	mappa: dict[int, str] = {}
	presi: set[str] = set()
	for indice, nome in enumerate(intestazione):
		campo = per_nome.get(regole.semplice(nome))
		if campo and campo not in presi:
			mappa[indice] = campo
			presi.add(campo)
	return mappa


def ora(valore) -> datetime.time | None:
	"""A time as a sheet gives it: a time, a date with its hour, Excel's fraction of
	a day, «9:30», «09.30», «9,30», «9h30», «930», «9». None when it is empty;
	ValueError when it is not one."""
	if valore in (None, ""):
		return None
	if isinstance(valore, datetime.datetime):
		return valore.time().replace(second=0, microsecond=0)
	if isinstance(valore, datetime.time):
		return valore.replace(second=0, microsecond=0)
	if isinstance(valore, datetime.timedelta):
		minuti = round(valore.total_seconds() / 60)
		return _da_minuti(minuti, valore)
	if isinstance(valore, (int, float)) and not isinstance(valore, bool):
		if 0 <= valore < 1:
			# Excel keeps a time as the part of the day gone
			return _da_minuti(round(valore * 24 * 60), valore)
		if float(valore).is_integer() and 0 <= valore <= 23:
			return datetime.time(int(valore), 0)
		raise ValueError(str(valore))
	testo = str(valore).strip().lower().replace(" ", "")
	trovato = re.fullmatch(r"(\d{1,2})(?:[:.,h](\d{2}))?(?::\d{2})?h?", testo) or re.fullmatch(
		r"(\d{1,2})(\d{2})", testo
	)
	if not trovato:
		raise ValueError(str(valore).strip())
	ore, minuti = int(trovato.group(1)), int(trovato.group(2) or 0)
	if ore > 23 or minuti > 59:
		raise ValueError(str(valore).strip())
	return datetime.time(ore, minuti)


def _da_minuti(minuti: int, valore) -> datetime.time:
	if not 0 <= minuti < 24 * 60:
		raise ValueError(str(valore))
	return datetime.time(minuti // 60, minuti % 60)


def durata(valore) -> int | None:
	"""Minutes, as a sheet writes them: «45», «45 min», «45'», «1h», «1h30»,
	«1:30», «1 ora», Excel's fraction of a day. None when empty; ValueError when
	it is not a length."""
	if valore in (None, ""):
		return None
	if isinstance(valore, datetime.timedelta):
		minuti = round(valore.total_seconds() / 60)
	elif isinstance(valore, datetime.time):
		minuti = valore.hour * 60 + valore.minute
	elif isinstance(valore, (int, float)) and not isinstance(valore, bool):
		minuti = round(valore * 24 * 60) if 0 < valore < 1 else round(valore)
	else:
		testo = regole.semplice(str(valore).replace("'", " min").replace(":", " h ").replace(".", " h "))
		trovato = re.fullmatch(
			r"(?:(\d+) ?(?:h|ora|ore|hr|hours?) ?)?(?:(\d+) ?(?:m|min|mins|minuti|minutes?)?)?", testo
		)
		if not testo or not trovato or not (trovato.group(1) or trovato.group(2)):
			raise ValueError(str(valore).strip())
		minuti = int(trovato.group(1) or 0) * 60 + int(trovato.group(2) or 0)
	if minuti <= 0 or minuti > 24 * 60:
		raise ValueError(str(valore).strip())
	return minuti


def stato(valore, passato: bool) -> str:
	"""How it went: a cancellation or an absence the sheet says stays; the rest is
	attended when it is past and booked when it is to come."""
	parola = regole.semplice(valore)
	for chiave in (ANNULLATO, ASSENTE):
		if parola and any(parola == p or parola.startswith(p + " ") for p in PAROLE_DELLO_STATO[chiave]):
			return chiave
	return SVOLTO if passato else PRENOTATO


def appuntamento(
	riga: list, mappa: dict[int, str], intestazione: list, adesso: datetime.datetime
) -> tuple[dict, list[tuple[str, str]]]:
	"""A row as an appointment: the person (as the people's sheet reads them), when,
	for how long, what and by whom as the sheet names them, how it went; and what is
	wrong with it (a sentence and its value). Without a person, a day or an hour it
	is not an appointment."""
	della_persona = {i: c for i, c in mappa.items() if c in CAMPI_DELLA_PERSONA}
	persona, problemi = regole.persona(riga, della_persona, intestazione)
	grezzi = {campo: riga[indice] for indice, campo in mappa.items() if indice < len(riga)}

	giorno = inizio_letto = None
	try:
		giorno = regole.data(grezzi.get("date"), anche_futura=True)
	except ValueError as errore:
		problemi.append((regole.DATA_SBAGLIATA, str(errore)))
	else:
		if giorno is None:
			problemi.append((SENZA_DATA, ""))
	# a date with its hour, in one column
	if isinstance(grezzi.get("date"), datetime.datetime):
		inizio_letto = grezzi["date"].time()
	elif isinstance(grezzi.get("date"), str) and " " in grezzi["date"].strip():
		try:
			inizio_letto = ora(grezzi["date"].strip().split(" ", 1)[1])
		except ValueError:
			inizio_letto = None

	alle = fine = None
	try:
		alle = ora(grezzi.get("start")) or (inizio_letto if inizio_letto and inizio_letto.hour else None)
	except ValueError as errore:
		problemi.append((ORA_SBAGLIATA, str(errore)))
	else:
		if alle is None:
			problemi.append((SENZA_ORA, ""))
	try:
		fine = ora(grezzi.get("end"))
	except ValueError as errore:
		problemi.append((ORA_SBAGLIATA, str(errore)))
	minuti = None
	try:
		minuti = durata(grezzi.get("duration"))
	except ValueError as errore:
		problemi.append((DURATA_SBAGLIATA, str(errore)))

	inizio = datetime.datetime.combine(giorno, alle) if giorno and alle else None
	finisce = None
	if inizio and fine:
		finisce = datetime.datetime.combine(giorno, fine)
		if finisce <= inizio:
			problemi.append((FINE_PRIMA, ""))
			finisce = None
	elif inizio and minuti:
		finisce = inizio + datetime.timedelta(minutes=minuti)

	testo = lambda campo: " ".join(str(grezzi.get(campo) or "").split())  # noqa: E731
	codice = testo("external_id")
	if codice.endswith(".0"):
		codice = codice[:-2]
	dati = {
		"person": persona,
		"starts_on": inizio,
		"ends_on": finisce,
		"service": testo("service"),
		"professional": testo("professional"),
		"room": testo("room"),
		"status": stato(grezzi.get("status"), bool(inizio and inizio < adesso)),
		"notes": testo("notes"),
		"external_id": codice,
	}
	return dati, problemi


def da_lasciare(dati: dict, problemi: list[tuple[str, str]]) -> bool:
	"""Whether a row is left out: without a person or the moment it starts. A wrong
	end or length only lets the service say how long it lasts."""
	return not dati.get("starts_on") or (regole.SENZA_NOME, "") in problemi


def chiave(dati: dict) -> str:
	"""What an appointment brought over is known by, to bring it in once: the
	previous software's own code, else the person, the moment and the service."""
	if dati.get("external_id"):
		base = "id|" + regole.semplice(dati["external_id"])
	else:
		persona = dati.get("person") or {}
		chi = next((valore for _campo, valore in regole.chiavi(persona)), "") or "|".join(
			regole.semplice(persona.get(campo)) for campo in ("first_name", "last_name")
		)
		quando = dati["starts_on"].isoformat(timespec="minutes") if dati.get("starts_on") else ""
		base = "|".join((chi, quando, regole.semplice(dati.get("service"))))
	return hashlib.sha256(base.encode()).hexdigest()[:32]


def nome_semplice(testo: str) -> str:
	"""A professional's name without its title: «Dott.ssa Rossi» is «rossi»."""
	parole = regole.semplice(testo)
	for titolo in sorted(TITOLI, key=len, reverse=True):
		if parole == titolo:
			return ""
		if parole.startswith(titolo + " "):
			parole = parole[len(titolo) + 1 :]
			break
	return parole


def abbina(testo: str, candidati: dict[str, list[str]]) -> str | None:
	"""The one candidate a name in the sheet stands for, or None.

	``candidati`` maps what is chosen (a user, a service, a room) to the names it
	goes by. The same name whole wins; else the one candidate whose name holds
	every word written («Rossi» for «Mario Rossi»); never a guess between two."""
	cercato = nome_semplice(testo)
	if not cercato:
		return None
	uguali = [chi for chi, nomi in candidati.items() if any(nome_semplice(n) == cercato for n in nomi if n)]
	if len(uguali) == 1:
		return uguali[0]
	if uguali:
		return None
	parole = set(cercato.split())
	contengono = [
		chi
		for chi, nomi in candidati.items()
		if any(parole <= set(nome_semplice(n).split()) for n in nomi if n)
	]
	return contengono[0] if len(contengono) == 1 else None
