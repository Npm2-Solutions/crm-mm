# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The reminders of the appointments without a site (docs/crm/59). The
engine is `crm.scheduling.promemoria`; here, what it decides.

- **The day before, never at night**: a reminder leaves the hours before its
  appointment the centre chose (24 to start with). A moment in the night (21 to 8,
  the centre's clock) moves to the morning, or - when the morning is too close to
  the appointment - to the evening before.
- **Never for what was just booked**, nor in the last hour: a booking made after
  its reminder would have left was its own reminder.
- **One way**: WhatsApp with the centre's template and its buttons, else SMS, else
  the email - the first the centre has and the person can receive; a STOP to the
  centre's SMS leaves the SMS out.
- **An answer**: a button's words, or an SMS that says nothing else, mean
  confirmed, cannot come or would like to move it. Anything else is a message,
  which the desk reads.

Pure: tested with plain `unittest` (`crm/tests/test_promemoria_regole.py`).
"""

from __future__ import annotations

import datetime
import re
import unicodedata

from crm.scheduling.attese_regole import entro

# ------------------------------------------------------------------ the words

#: What the person answered.
CONFERMA, NON_VIENE, SPOSTA = "Confirmed", "Cannot come", "Wants to move"
RISPOSTE = (CONFERMA, NON_VIENE, SPOSTA)

#: How a reminder went.
INVIATO, NON_INVIATO, NON_CONSEGNATO = "Sent", "Not sent", "Not delivered"
STATI = (INVIATO, NON_INVIATO, NON_CONSEGNATO)

#: The ways a reminder goes, and the booking page an answer may come from too.
WHATSAPP, SMS, EMAIL = "WhatsApp", "SMS", "Email"
CANALI = (WHATSAPP, SMS, EMAIL)
DALLA_PAGINA = "Booking page"

# ------------------------------------------------------------------ the time

#: The hours before, as the centre may choose them: (least, most, default).
ORE_PRIMA = (2, 72, 24)
#: The night, in the centre's clock: nobody is written to from 21 to 8.
NOTTE_DALLE = datetime.time(21, 0)
NOTTE_ALLE = datetime.time(8, 0)
#: Where a moment of the night goes: the morning, else the evening before.
SERA = datetime.time(20, 0)
#: No reminder in the last hour before the appointment.
ULTIMA_ORA = datetime.timedelta(hours=1)
#: Booked this close to its reminder's moment, the booking is the reminder.
APPENA_PRENOTATO = datetime.timedelta(hours=2)
#: How long a WhatsApp that left is watched, in case it did not arrive.
GUARDA_INDIETRO = datetime.timedelta(hours=6)


def ore_prima(valore) -> int:
	return entro(valore, ORE_PRIMA)


def di_notte(momento: datetime.datetime) -> bool:
	ora = momento.time()
	return ora >= NOTTE_DALLE or ora < NOTTE_ALLE


def momento_di_invio(inizio: datetime.datetime, ore: int) -> datetime.datetime:
	"""When the reminder of an appointment starting at ``inizio`` leaves: ``ore``
	before it, out of the night - in the morning, or the evening before when the
	morning would be within the last hour."""
	momento = inizio - datetime.timedelta(hours=ore)
	if not di_notte(momento):
		return momento
	giorno = momento.date() if momento.time() < NOTTE_ALLE else momento.date() + datetime.timedelta(days=1)
	mattina = datetime.datetime.combine(giorno, NOTTE_ALLE)
	if inizio - mattina >= ULTIMA_ORA:
		return mattina
	return datetime.datetime.combine(giorno - datetime.timedelta(days=1), SERA)


def dovuto(
	inizio: datetime.datetime,
	adesso: datetime.datetime,
	ore: int,
	prenotato_il: datetime.datetime | None = None,
) -> bool:
	"""Whether the reminder of an appointment leaves now: its moment has come, the
	appointment is not within the hour, and it was not booked when its reminder was
	about to leave - or after."""
	if inizio - adesso < ULTIMA_ORA:
		return False
	momento = momento_di_invio(inizio, ore)
	if adesso < momento:
		return False
	return not (prenotato_il and prenotato_il > momento - APPENA_PRENOTATO)


def da_cercare(adesso: datetime.datetime, ore: int) -> tuple[datetime.datetime, datetime.datetime]:
	"""Where the appointments whose reminder may be due now start: a moment of the
	night may have moved their reminder up to thirteen hours earlier."""
	return adesso + ULTIMA_ORA, adesso + datetime.timedelta(hours=ore + 13)


# ------------------------------------------------------------------ the way


def canali(
	whatsapp: bool, sms: bool, email: bool, numero: bool, indirizzo: bool, fermato: bool = False
) -> list[str]:
	"""The ways a reminder may go, in order: the centre's that the person can
	receive. A STOP written to the centre's SMS leaves the SMS out."""
	vie = []
	if whatsapp and numero:
		vie.append(WHATSAPP)
	if sms and numero and not fermato:
		vie.append(SMS)
	if email and indirizzo:
		vie.append(EMAIL)
	return vie


def variabili(quante: int, nome: str, cosa: str, quando: str, dove: str) -> list[str]:
	"""A template's variables, as many as it has: the name, what, when, where.
	Meta refuses an empty one: a dash stands for what is missing."""
	valori = [nome, cosa, quando, dove]
	return [(valore or "").strip() or "-" for valore in valori[:quante]]


# ------------------------------------------------------------------ the answer


def _parole(testo: str | None) -> str:
	"""A message as words to compare: no accents, no marks, small letters."""
	senza = unicodedata.normalize("NFKD", testo or "")
	senza = "".join(c for c in senza if not unicodedata.combining(c))
	senza = re.sub(r"[^\w\s]", " ", senza.lower().replace("’", "'").replace("'", ""))
	return " ".join(senza.split())


#: A button's words, by what they mean - checked in this order: "non ci sarò"
#: is not a "ci sarò".
PULSANTI = (
	(SPOSTA, ("spost", "cambi", "rimand", "altro orario", "altra data", "altro giorno", "move", "reschedul")),
	(
		NON_VIENE,
		(
			"disd",
			"annull",
			"non posso",
			"non riesco",
			"non vengo",
			"non ci saro",
			"cancel",
			"cant come",
			"cannot come",
		),
	),
	(
		CONFERMA,
		(
			"confer",
			"ci saro",
			"ci sono",
			"vengo",
			"confirm",
			"ill be there",
			"i will be there",
			"ok",
			"si",
			"yes",
		),
	),
)

#: An SMS that says nothing else - but for the courtesy around it.
SOLO = {
	CONFERMA: {
		"si",
		"ok",
		"okay",
		"certo",
		"perfetto",
		"va bene",
		"confermo",
		"conferma",
		"confermato",
		"confermata",
		"yes",
		"confirm",
		"confirmed",
	},
	NON_VIENE: {"no", "disdico", "disdetta", "disdire", "annullo", "annulla", "non posso", "non vengo"},
	SPOSTA: {"sposta", "spostare", "spostalo", "sposto", "cambio", "move", "reschedule"},
}
#: Words that say nothing of the answer: «Sì, grazie» is a yes.
CORTESIA = frozenset(
	{
		"grazie",
		"mille",
		"molte",
		"ciao",
		"buongiorno",
		"buonasera",
		"salve",
		"thanks",
		"thank",
		"you",
		"hi",
		"hello",
	}
)


def _contiene(parole: str, segno: str) -> bool:
	"""Whether ``segno`` is a word or a phrase of ``parole``, or the start of one
	of its words when it is a stem (``confer``)."""
	if " " in segno or len(segno) <= 3:
		return f" {segno} " in f" {parole} "
	return any(parola.startswith(segno) for parola in parole.split())


def risposta(testo: str | None, pulsante: bool = False) -> str | None:
	"""What an answer to a reminder means, or None for a message: a button's words
	(``pulsante``) by what they say, an SMS only when it says nothing else."""
	if (testo or "").strip() == "👍":
		return CONFERMA
	parole = _parole(testo)
	if not parole:
		return None
	if not pulsante:
		parole = " ".join(parola for parola in parole.split() if parola not in CORTESIA)
		intera = next((cosa for cosa, frasi in SOLO.items() if parole in frasi), None)
		if intera or not parole:
			return intera
		# «ok perfetto», «sì sì»: every word says the same thing
		dette = {
			next((cosa for cosa, frasi in SOLO.items() if parola in frasi), None) for parola in parole.split()
		}
		return dette.pop() if len(dette) == 1 else None
	return next(
		(cosa for cosa, segni in PULSANTI if any(_contiene(parole, segno) for segno in segni)),
		None,
	)


def stesso_numero(uno: str | None, altro: str | None) -> bool:
	"""Whether two numbers, written any way, are the same: their last nine digits."""
	a = re.sub(r"\D", "", uno or "")[-9:]
	b = re.sub(r"\D", "", altro or "")[-9:]
	return len(a) >= 6 and a == b


def vale(
	stato: str | None,
	inizio: datetime.datetime,
	ricordato: datetime.datetime | None,
	adesso: datetime.datetime,
	partecipa: bool = True,
) -> bool:
	"""Whether an answer still says something of its appointment: still booked,
	not moved since the reminder, not started, the person still in it."""
	return (
		stato in ("Scheduled", "Confirmed")
		and partecipa
		and ricordato is not None
		and inizio == ricordato
		and inizio > adesso
	)


# ------------------------------------------------------------------ the template

#: DottorCloud's own reminder template, in the centre's language: a utility
#: template whose variables are the name, what, when and where, and three quick
#: replies. Meta wants an example for every variable, none with a comma in it.
MODELLO = {
	"it": {
		"template_name": "promemoria_appuntamento",
		"language": "it",
		"category": "UTILITY",
		"template": (
			"Ciao {{1}}, ti ricordiamo l'appuntamento: {{2}}, {{3}}, presso {{4}}.\n\n"
			"Puoi confermare o avvisarci con i pulsanti qui sotto."
		),
		"sample_values": "Anna,Visita di controllo,mercoledì 7 ottobre alle 9:30,Centro Aurora",
		"buttons": ("Confermo", "Devo disdire", "Vorrei spostarlo"),
	},
	"en": {
		"template_name": "appointment_reminder",
		"language": "en",
		"category": "UTILITY",
		"template": (
			"Hi {{1}}, this is a reminder of your appointment: {{2}}, {{3}}, at {{4}}.\n\n"
			"You can confirm or let us know with the buttons below."
		),
		"sample_values": "Anna,Check-up visit,Wednesday 7 October at 9:30,Aurora Centre",
		"buttons": ("I'll be there", "I need to cancel", "I'd like to move it"),
	},
}


def modello(lingua: str | None) -> dict:
	"""The reminder template in ``lingua``, Italian where it is not English: a copy,
	which the caller may change (its name on a second account)."""
	return dict(MODELLO["en" if (lingua or "").lower().startswith("en") else "it"])


def ha_i_pulsanti(etichette) -> bool:
	"""Whether a template's quick replies say the three answers: one to confirm,
	one for who cannot come; moving is a plus."""
	dette = {risposta(etichetta, pulsante=True) for etichetta in etichette or ()}
	return CONFERMA in dette and NON_VIENE in dette
