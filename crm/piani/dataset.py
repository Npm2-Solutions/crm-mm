# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The exercise library DottorCloud ships, as the CRM keeps it, without a site
(design.md, "I piani", "Le librerie"; ricerca-design.md §2.3).

`dati/esercizi.json` was made once from hasaneyldrm's exercises-dataset at
7455efa (18/03/2026), keeping only what the library reads: the name in English,
how it is done in Italian and English in steps, the body part, the equipment and
the muscles, the pictures' paths and whose they are. The dataset names its
exercises in English only: the Italian names (`names.it`) are NPM2's, written in
the words of an Italian gym ("Panca piana con bilanciere", "Rematore a un braccio
con manubrio") and kept by code from one version to the next. The data are MIT
(the notice travels with them, `dati/esercizi.LICENSE.txt`); the media © Gym
visual, with its written authorisation to NPM2 Solutions, only from the server's
own copy (`immagini`) or the agency's CDN, and always with "© Gym visual —
https://gymvisual.com/". The assistant never touches them. A new exercise of the
library is a new record of that file, with an id of NPM2's ("dc-0001"): the
centre never imports one.
"""

from __future__ import annotations

import re

#: The library's exercises carry it as their source: what the centre adds has none.
DATASET = "exercises-dataset"
PARTI_DATASET = {
	"back": "Back",
	"cardio": "Full body",
	"chest": "Chest",
	"lower arms": "Arms",
	"lower legs": "Legs",
	"neck": "Neck",
	"shoulders": "Shoulders",
	"upper arms": "Arms",
	"upper legs": "Legs",
	"waist": "Core",
}

#: The dataset's words for equipment and muscles, in Italian: a few dozen, read
#: once. A word not here stays in English.
ITALIANO = {
	# equipment
	"body weight": "corpo libero",
	"dumbbell": "manubri",
	"cable": "cavi",
	"barbell": "bilanciere",
	"leverage machine": "macchina a leva",
	"band": "elastico",
	"smith machine": "multipower",
	"kettlebell": "kettlebell",
	"weighted": "sovraccarico",
	"stability ball": "fitball",
	"ez barbell": "bilanciere EZ",
	"assisted": "assistito",
	"sled machine": "macchina a slitta",
	"medicine ball": "palla medica",
	"rope": "corda",
	"roller": "rullo",
	"resistance band": "banda elastica",
	"bosu ball": "bosu",
	"olympic barbell": "bilanciere olimpico",
	"wheel roller": "ruota per addominali",
	"upper body ergometer": "ergometro a braccia",
	"skierg machine": "SkiErg",
	"hammer": "martello",
	"stationary bike": "cyclette",
	"tire": "pneumatico",
	"trap bar": "trap bar",
	"elliptical machine": "ellittica",
	"stepmill machine": "stepmill",
	# muscles
	"abs": "addominali",
	"abdominals": "addominali",
	"lower abs": "addominali bassi",
	"pectorals": "pettorali",
	"chest": "petto",
	"upper chest": "parte alta del petto",
	"biceps": "bicipiti",
	"triceps": "tricipiti",
	"glutes": "glutei",
	"delts": "deltoidi",
	"deltoids": "deltoidi",
	"rear deltoids": "deltoidi posteriori",
	"shoulders": "spalle",
	"upper back": "parte alta della schiena",
	"back": "schiena",
	"lower back": "zona lombare",
	"lats": "dorsali",
	"latissimus dorsi": "gran dorsale",
	"calves": "polpacci",
	"soleus": "soleo",
	"quads": "quadricipiti",
	"quadriceps": "quadricipiti",
	"hamstrings": "femorali",
	"forearms": "avambracci",
	"cardiovascular system": "sistema cardiovascolare",
	"spine": "erettori spinali",
	"traps": "trapezi",
	"trapezius": "trapezio",
	"adductors": "adduttori",
	"abductors": "abduttori",
	"inner thighs": "interno coscia",
	"serratus anterior": "dentato anteriore",
	"levator scapulae": "elevatore della scapola",
	"core": "core",
	"hip flexors": "flessori dell'anca",
	"obliques": "obliqui",
	"rhomboids": "romboidi",
	"brachialis": "brachiale",
	"ankles": "caviglie",
	"ankle stabilizers": "stabilizzatori della caviglia",
	"feet": "piedi",
	"hands": "mani",
	"wrists": "polsi",
	"wrist flexors": "flessori del polso",
	"wrist extensors": "estensori del polso",
	"grip muscles": "muscoli della presa",
	"rotator cuff": "cuffia dei rotatori",
	"sternocleidomastoid": "sternocleidomastoideo",
	"groin": "inguine",
	"shins": "tibiali",
}


def parola(testo: str, lingua: str) -> str:
	testo = (testo or "").strip()
	if lingua == "it":
		return ITALIANO.get(testo.lower(), testo)
	return testo


def _passi(record: dict, lingua: str) -> str:
	for codice in dict.fromkeys((lingua, "en")):
		passi = ((record.get("instruction_steps") or {}).get(codice)) or []
		passi = [str(p).strip() for p in passi if str(p).strip()]
		if passi:
			return "\n".join(f"{numero_passo}. {passo}" for numero_passo, passo in enumerate(passi, 1))
		testo = str(((record.get("instructions") or {}).get(codice)) or "").strip()
		if testo:
			return testo
	return ""


_PERCORSO_IMMAGINE = re.compile(r"^images/[A-Za-z0-9._-]+\.(jpg|jpeg|png)$")
_PERCORSO_ANIMAZIONE = re.compile(r"^videos/[A-Za-z0-9._-]+\.gif$")


def indirizzo_media(base: str | None, percorso) -> str | None:
	"""Where the agency hosts a picture of the dataset: its address plus the
	dataset's own path. Nothing when the agency hosts none."""
	base = (base or "").strip()
	percorso = str(percorso or "").strip()
	if not base or not percorso:
		return None
	if not (_PERCORSO_IMMAGINE.match(percorso) or _PERCORSO_ANIMAZIONE.match(percorso)):
		return None
	if not (base.startswith("https://") or (base.startswith("/") and not base.startswith("//"))):
		return None
	return base.rstrip("/") + "/" + percorso


def _percorso(valore, forma: re.Pattern) -> str | None:
	percorso = str(valore or "").strip()
	return percorso if forma.match(percorso) else None


#: The languages the library's words come in.
LINGUE = ("it", "en")


def _nome(record: dict, lingua: str) -> str:
	"""The exercise's name in ``lingua``: NPM2's (`names`), else the dataset's
	English one, with its first letter capital."""
	inglese = re.sub(r"\s+", " ", str(record.get("name") or "")).strip()
	nome = inglese
	if lingua != "en":
		nome = re.sub(r"\s+", " ", str(((record.get("names") or {}).get(lingua)) or "")).strip() or inglese
	return (nome[0].upper() + nome[1:])[:140] if nome else ""


def _parole(record: dict, lingua: str) -> dict:
	"""What the library writes of an exercise in ``lingua`` and a centre may have
	rewritten before: its name, its equipment and how it is done."""
	return {
		"exercise_name": _nome(record, lingua) or None,
		"equipment": parola(str(record.get("equipment") or ""), lingua)[:140] or None,
		"instructions": _passi(record, lingua) or None,
	}


def nella_lingua(record: dict, lingua: str, attuali: dict) -> dict:
	"""The library's words a site keeps of an exercise in another language than
	``lingua``, in ``lingua``: a site loaded in English before it said it is in
	Italy. Words the centre wrote are the library's in no language, and stay."""
	cambi = {}
	for campo, nuovo in _parole(record, lingua).items():
		attuale = (attuali.get(campo) or "").strip() or None
		if not nuovo or attuale == nuovo:
			continue
		if attuale in {_parole(record, altra)[campo] for altra in LINGUE if altra != lingua}:
			cambi[campo] = nuovo
	return cambi


def esercizio(record, lingua: str = "it") -> dict | None:
	"""An exercise of the dataset as the library keeps it; None for a record that
	is not one. Its pictures are paths in the dataset: where they are served from
	is the server's, or the agency's, and may change."""
	if not isinstance(record, dict):
		return None
	codice = str(record.get("id") or "").strip()
	inglese = _nome(record, "en")
	if not codice or not inglese:
		return None
	principale = parola(str(record.get("target") or ""), lingua)
	secondari = []
	for muscolo in record.get("secondary_muscles") or []:
		tradotto = parola(str(muscolo), lingua)
		if tradotto and tradotto not in secondari and tradotto != principale:
			secondari.append(tradotto)
	return {
		"code": codice[:40],
		"name": _nome(record, lingua),
		# the dataset's own, which a search in English still finds
		"name_in_source": inglese,
		"body_part": PARTI_DATASET.get(str(record.get("body_part") or "").strip().lower(), "Other"),
		"primary_muscles": principale or None,
		"secondary_muscles": ", ".join(secondari) or None,
		**_parole(record, lingua),
		"media_path": _percorso(record.get("image"), _PERCORSO_IMMAGINE),
		"animation_path": _percorso(record.get("gif_url"), _PERCORSO_ANIMAZIONE),
		# the media's owner, cited wherever they are shown
		"attribution": str(record.get("attribution") or "").strip()[:140] or None,
	}
