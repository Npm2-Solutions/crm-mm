# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A campaign without a site: which ways an automation writes by, who of a list
it leaves out and why, the counts the dialog and the report show.

A campaign is an automation started by hand ("Started by Hand"): the manager
sends it from the People list to a saved view, the filters on screen or the rows
chosen. Before anybody is enrolled, each person of the list is looked at once:
already in it, no marketing consent where it asks for one, STOP where it writes
only by SMS, nowhere to write to. The engine checks again at every step (a consent
withdrawn later, a STOP, the promotional hours): this is what is known today.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

#: The most people one campaign enrols: a larger list is narrowed first.
MASSIMO = 5000

EMAIL = "email"
SMS = "sms"
WHATSAPP = "whatsapp"

#: Why a person of the list is left out, in the order they are looked at.
GIA_DENTRO = "already"
SENZA_CONSENSO = "consent"
CONDIZIONI = "conditions"
STOP = "stop"
SENZA_RECAPITO = "no_contact"
MOTIVI = (GIA_DENTRO, SENZA_CONSENSO, CONDIZIONI, STOP, SENZA_RECAPITO)

_CANALE_DEL_PASSO = {
	"send_email": EMAIL,
	"send_sms": SMS,
	"send_whatsapp_template": WHATSAPP,
}


def canali(passi: Iterable[dict] | None) -> set[str]:
	"""The ways an automation writes to the person, read through its branches and
	paths: email, SMS, WhatsApp; a form goes the way its step says."""
	trovati: set[str] = set()
	for passo in passi or []:
		if not isinstance(passo, dict):
			continue
		tipo = passo.get("type")
		if tipo in _CANALE_DEL_PASSO:
			trovati.add(_CANALE_DEL_PASSO[tipo])
		elif tipo == "send_form":
			trovati.add(passo.get("via") if passo.get("via") in (EMAIL, SMS, WHATSAPP) else EMAIL)
		for ramo in passo.get("branches") or []:
			trovati |= canali(ramo.get("steps"))
		trovati |= canali(passo.get("else_steps"))
		for percorso in passo.get("paths") or []:
			trovati |= canali(percorso.get("steps"))
	return trovati


def raggiungibile(persona: dict, canale: str) -> bool:
	"""Whether a way reaches the person: an email for the email, a mobile for the
	rest, never an SMS to whoever wrote STOP."""
	if canale == EMAIL:
		return bool((persona.get("email") or "").strip())
	if canale == SMS and persona.get("stop"):
		return False
	return bool((persona.get("mobile_no") or "").strip())


def motivo(persona: dict, *, marketing: bool, vie: set[str]) -> str | None:
	"""Why ``persona`` is left out of the campaign, or None when it enrols them.

	``persona`` says ``already`` (in it: running, or once and the automation lets
	nobody in twice), ``consent`` (to marketing), ``conditions`` (meets the start's
	conditions; None when there are none), ``stop``, ``email``, ``mobile_no``.
	An automation that writes nothing (a task, a tag) leaves nobody out for want
	of an address."""
	if persona.get("already"):
		return GIA_DENTRO
	if marketing and not persona.get("consent"):
		return SENZA_CONSENSO
	if persona.get("conditions") is False:
		return CONDIZIONI
	if vie and not any(raggiungibile(persona, via) for via in vie):
		# STOP said when it is what keeps them out: the SMS would have reached them
		if SMS in vie and persona.get("stop") and raggiungibile({**persona, "stop": False}, SMS):
			return STOP
		return SENZA_RECAPITO
	return None


def conta(motivi: Iterable[str | None]) -> dict:
	"""How many of a list enrol, and how many are left out by reason (only the
	reasons that happened, in their order)."""
	contati = Counter(motivi)
	entrano = contati.pop(None, 0)
	return {
		"total": entrano + sum(contati.values()),
		"enrolled": entrano,
		"skipped": {chiave: contati[chiave] for chiave in MOTIVI if contati.get(chiave)},
	}
