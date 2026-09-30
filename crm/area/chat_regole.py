# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What the patient's chat may answer, without a site (design.md, "L'assistente",
point 6): "una chat per il paziente solo per l'amministrazione (orari,
prenotazioni, domande frequenti scritte dal centro); se parla di sintomi passa a
una persona o indica il 112".

- **An emergency is read before any model**: words of an emergency get 112 at
  once, in fixed words, and nothing is sent anywhere.
- **Health is a person's**: symptoms, medicines, doses, results, a diagnosis.
  The chat does not answer them: it offers to pass the question to the centre,
  and the patient decides.
- **The rest is administration**: hours, bookings, the centre's frequent
  questions - answered by the model only from what the centre wrote, and when it
  does not know, it says so and offers a person too.
- The words are compared without accents and case: "è" and "E'" alike.
"""

from __future__ import annotations

import re
import unicodedata

EMERGENZA, SALUTE = "emergency", "health"

#: The words of an emergency: 112 at once. Italian and English, the area's two.
PAROLE_EMERGENZA = (
	# "il 112", not a bare number: "via Roma 112" is an address
	"il 112",
	"il 118",
	"emergenza",
	"dolore al petto",
	"dolore toracico",
	"male al petto",
	"non riesco a respirare",
	"non respiro",
	"respiro a fatica",
	"soffoco",
	"svenut",
	"perdo sangue",
	"emorragia",
	"infarto",
	"ictus",
	"paralisi",
	"convulsion",
	"suicid",
	"farla finita",
	"togliermi la vita",
	"overdose",
	"avvelenat",
	"emergency",
	"chest pain",
	"can't breathe",
	"cannot breathe",
	"unconscious",
	"bleeding heavily",
	"heart attack",
	"stroke",
	"suicide",
	"kill myself",
)

#: The words of health: a person answers, not the chat.
PAROLE_SALUTE = (
	"sintom",
	"dolor",
	"mi fa male",
	"ho male",
	"febbre",
	"tosse",
	"nausea",
	"vomit",
	"diarrea",
	"gonfi",
	"prurito",
	"eruzion",
	"ferita",
	"farmac",
	"medicin",
	"dose",
	"dosi",
	"dosaggio",
	"compress",
	"pastigli",
	"antibiotic",
	"effetti collaterali",
	"allergi",
	"diagnos",
	"terapi",
	"esito",
	"risultat",
	"referto",
	"analisi",
	"esami del sangue",
	"pressione alta",
	"glicemia",
	"incinta",
	"gravidanz",
	"symptom",
	"pain",
	"fever",
	"medicine",
	"medication",
	"diagnosis",
	"test result",
	"pregnan",
)


def normalizza(testo: str) -> str:
	"""Lower case, without accents, apostrophes and spaces made one."""
	senza = unicodedata.normalize("NFKD", testo or "")
	senza = "".join(c for c in senza if not unicodedata.combining(c)).lower()
	senza = senza.replace("’", "'")
	return re.sub(r"\s+", " ", senza).strip()


def _dice(testo: str, parole: tuple[str, ...]) -> bool:
	# from the start of a word: "dolor" finds "dolore" and "dolori", not "addolorato"
	return any(re.search(rf"(?<![a-z0-9]){re.escape(normalizza(parola))}", testo) for parola in parole)


def classifica(domanda: str) -> str | None:
	"""An emergency, a question of health, or neither: then the chat may answer."""
	testo = normalizza(domanda)
	if _dice(testo, PAROLE_EMERGENZA):
		return EMERGENZA
	if _dice(testo, PAROLE_SALUTE):
		return SALUTE
	return None


#: How long a question is, and how much of the conversation goes with it.
MAX_DOMANDA = 500
MAX_TURNI = 6
MAX_RISPOSTA = 1200


def storia(turni) -> list[dict]:
	"""The last turns of the conversation, as the model reads them: who spoke and
	what, trimmed. Anything else is dropped."""
	righe = []
	for turno in turni or []:
		if not isinstance(turno, dict):
			continue
		chi = turno.get("role")
		testo = str(turno.get("text") or "").strip()[:MAX_RISPOSTA]
		if chi in ("patient", "assistant") and testo:
			righe.append({"role": chi, "text": testo})
	return righe[-MAX_TURNI:]


def risposta(dati) -> dict | None:
	"""The model's answer as the chat keeps it: the words, and whether a person
	should take it. Anything else is not an answer."""
	if not isinstance(dati, dict):
		return None
	testo = str(dati.get("answer") or "").strip()[:MAX_RISPOSTA]
	if not testo:
		return None
	return {"answer": testo, "handoff": bool(dati.get("handoff"))}
