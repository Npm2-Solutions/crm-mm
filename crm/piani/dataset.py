# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""exercises-dataset as the CRM's library keeps it, without a site (design.md, "I
piani", "Le librerie"; ricerca-design.md §2.3).

hasaneyldrm's dataset, the data MIT; the media © Gym visual, with its written
authorisation to NPM2 Solutions: the name in English, how it is done in Italian in
steps, the body part, the equipment and the muscles in the centre's language; the
animation and the picture only from where the agency hosts them. The assistant
never touches them.
"""

from __future__ import annotations

import re

DATASET = "exercises-dataset"
#: The dataset, at the version the import was written on (18/03/2026).
DATASET_URL = (
	"https://raw.githubusercontent.com/hasaneyldrm/exercises-dataset/"
	"7455efae41b330c265e7cd4b78dfa848e7ce5ebd/data/exercises.json"
)
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


def esercizio(record, lingua: str = "it") -> dict | None:
	"""An exercise of the dataset as the library keeps it; None for a record that
	is not one. Its pictures are paths in the dataset: where they are served from
	is the agency's, and may change."""
	if not isinstance(record, dict):
		return None
	codice = str(record.get("id") or "").strip()
	nome = re.sub(r"\s+", " ", str(record.get("name") or "")).strip()
	if not codice or not nome:
		return None
	nome = (nome[0].upper() + nome[1:])[:140]
	principale = parola(str(record.get("target") or ""), lingua)
	secondari = []
	for muscolo in record.get("secondary_muscles") or []:
		tradotto = parola(str(muscolo), lingua)
		if tradotto and tradotto not in secondari and tradotto != principale:
			secondari.append(tradotto)
	return {
		"code": codice[:40],
		"name": nome,
		"name_in_source": nome,
		"body_part": PARTI_DATASET.get(str(record.get("body_part") or "").strip().lower(), "Other"),
		"equipment": parola(str(record.get("equipment") or ""), lingua)[:140] or None,
		"primary_muscles": principale or None,
		"secondary_muscles": ", ".join(secondari) or None,
		"instructions": _passi(record, lingua) or None,
		"media_path": _percorso(record.get("image"), _PERCORSO_IMMAGINE),
		"animation_path": _percorso(record.get("gif_url"), _PERCORSO_ANIMAZIONE),
		# the media's owner, cited wherever they are shown
		"attribution": str(record.get("attribution") or "").strip()[:140] or None,
	}
