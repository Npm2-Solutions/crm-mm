# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Asking how a visit went: the rules, without a site.

Two ways of asking after a visit, both of them the centre's own voice to a person
it served: a review on Google (`{{ review_link }}` in an automation's message) and
a short questionnaire of its own (the "Survey" use of the forms), whose 0-10
question makes the Net Promoter Score.

**Who may be asked.** Under the Italian Garante's reading of art. 130 of the
privacy code, asking a client how satisfied they are is a promotional purpose,
not a message of the service they had: it is not the reminder of their
appointment. So it needs a yes, and the code treats it the way it treats
marketing (`crm.automation.engine.consenso_marketing`): a person is asked when
they agreed to these requests, or to marketing, which covers them; and never when
they refused or withdrew these requests, whatever they said of marketing - the
narrower answer is the one they gave about this. Somebody never asked about
either is not written to.

**How often.** Once per person every so many months (twelve to start with),
whatever automation asks: the second visit in a week is no second request.

**Everybody the same way.** Google forbids choosing whom to ask by how they are
likely to answer (review gating) and offering anything for a review. The only
choice the centre makes is by service - a service nobody reviews (a certificate,
a blood test) - never by person, nor by what they said in a questionnaire.
"""

from __future__ import annotations

import math
import re
from datetime import datetime

from dateutil.relativedelta import relativedelta

#: The kind of consent (`crm.moduli.registro`) these requests ask about.
CONSENSO = "review_requests"
MARKETING = "marketing"
DATO = "Given"
NEGATI = ("Refused", "Withdrawn")

#: Months before the same person is asked again, to start with.
MESI_PREDEFINITI = 12
MESI_MASSIMI = 60

#: The merge field of a review request, as an automation's text writes it.
SEGNAPOSTO = re.compile(r"\{\{\s*review_link\s*\}\}")

#: Google's page to write a review, from the place's id.
RECENSIONE_DA_PLACE_ID = "https://search.google.com/local/writereview?placeid={0}"

#: The Net Promoter Score's bands, on a 0-10 answer.
PROMOTORI = (9, 10)
DETRATTORI_FINO_A = 6


def puo_chiedere(stato_proprio: str | None, stato_marketing: str | None) -> bool:
	"""Whether a person may be asked how their visit went, from their answers.

	The narrower answer wins: a no to these requests stays a no with a yes to
	marketing. Otherwise a yes to either is enough.
	"""
	if stato_proprio in NEGATI:
		return False
	return stato_proprio == DATO or stato_marketing == DATO


def troppo_presto(ultima: datetime | None, adesso: datetime, mesi: int | None) -> bool:
	"""Whether the last request is less than ``mesi`` months old."""
	if not ultima:
		return False
	return ultima > adesso - relativedelta(months=mesi_tra(mesi))


def mesi_tra(mesi) -> int:
	"""The months between two requests: the default when unset, never less than one."""
	try:
		valore = int(mesi)
	except (TypeError, ValueError):
		return MESI_PREDEFINITI
	if valore <= 0:
		return MESI_PREDEFINITI
	return min(valore, MESI_MASSIMI)


def servizi(valore) -> list[str]:
	"""The services excluded, as the settings keep them: one per line."""
	if isinstance(valore, list | tuple):
		voci = valore
	else:
		voci = str(valore or "").splitlines()
	return list(dict.fromkeys(v.strip() for v in voci if v and str(v).strip()))


def escluso(servizio: str | None, esclusi) -> bool:
	return bool(servizio) and servizio in servizi(esclusi)


def link_di_google(link: str | None, place_id: str | None) -> str | None:
	"""The page where the person writes the review: the link the centre pasted,
	else the one Google makes from the place's id. None when neither is set."""
	link = (link or "").strip()
	if link:
		return link
	place_id = (place_id or "").strip()
	if place_id:
		return RECENSIONE_DA_PLACE_ID.format(place_id)
	return None


def link_valido(link: str | None) -> bool:
	"""A review link is a web address the browser opens: https only, no spaces."""
	link = (link or "").strip()
	return bool(re.fullmatch(r"https://[^\s/]+\.[^\s/]+(/\S*)?", link))


def place_id_valido(place_id: str | None) -> bool:
	"""Google's place ids are letters, digits, dashes and underscores."""
	return bool(re.fullmatch(r"[A-Za-z0-9_-]{10,}", (place_id or "").strip()))


def chiede_una_recensione(*testi) -> bool:
	"""Whether a message asks for a review: one of its texts holds the merge field."""
	for testo in testi:
		if isinstance(testo, list | tuple):
			if chiede_una_recensione(*testo):
				return True
		elif testo and SEGNAPOSTO.search(str(testo)):
			return True
	return False


# ------------------------------------------------------------------ the score


def domanda_nps(schema: dict | None) -> str | None:
	"""The question of a survey that makes the score: its first 0 to 10 scale."""
	for sezione in (schema or {}).get("sections") or []:
		for campo in sezione.get("fields") or []:
			if campo.get("type") != "scale":
				continue
			if _intero(campo.get("min")) == 0 and _intero(campo.get("max")) == 10:
				return campo.get("id")
	return None


def voto(valore) -> int | None:
	"""An answer of 0 to 10, or None for anything else."""
	numero = _intero(valore)
	return numero if numero is not None and 0 <= numero <= 10 else None


def _intero(valore) -> int | None:
	if isinstance(valore, bool) or valore in (None, ""):
		return None
	try:
		numero = float(valore)
	except (TypeError, ValueError):
		return None
	return int(numero) if numero.is_integer() else None


def nps(voti) -> dict:
	"""The Net Promoter Score of these answers: the share of promoters (9 and 10)
	less the share of detractors (0 to 6), from -100 to 100; None without answers.
	Answers that are not 0 to 10 are not counted."""
	validi = [v for v in (voto(x) for x in voti) if v is not None]
	promotori = sum(1 for v in validi if v in PROMOTORI)
	detrattori = sum(1 for v in validi if v <= DETRATTORI_FINO_A)
	risposte = len(validi)
	return {
		"answers": risposte,
		"promoters": promotori,
		"passives": risposte - promotori - detrattori,
		"detractors": detrattori,
		# rounded half up: 62.5 is 63, -62.5 is -62
		"score": math.floor(100 * (promotori - detrattori) / risposte + 0.5) if risposte else None,
	}
