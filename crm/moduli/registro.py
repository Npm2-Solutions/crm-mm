# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The kinds of consent, and a person's state for each: the rules, without a site.

Every module registers the consents it needs, the way it registers its
capabilities: the CRM brings the privacy notice and marketing, the clinic will
bring the health dossier, online reports and the assistant. A type is a key the
code asks about ("may we write to them?") and a text the person reads; the text
belongs to the centre, which has it checked by its DPO, and each change of it is a
new version.

The register itself only grows. A consent given is never edited: withdrawing it
stamps the same record, giving it again writes a new one. So the state of a person
is simply the last answer they gave.
"""

from __future__ import annotations

from dataclasses import dataclass, field

DATO = "Given"
RIFIUTATO = "Refused"
REVOCATO = "Withdrawn"
STATI = (DATO, RIFIUTATO, REVOCATO)

#: Accepted, and revocable at any time (art. 7(3) GDPR).
CONSENSO = "Consent"
#: Read and acknowledged: a privacy notice is information, not a consent, and
#: there is nothing to take back.
PRESA_VISIONE = "Acknowledgement"

#: How an answer reached the centre.
CANALI = (
	"Online booking",
	"Web form",
	"At the desk",
	"On paper",
	"By phone",
	"By email",
	"Imported",
)
#: The ones a person at the desk can record by hand.
CANALI_A_MANO = ("At the desk", "On paper", "By phone", "By email")


@dataclass(frozen=True)
class TipoConsenso:
	chiave: str
	etichetta: str
	#: What the person reads, per language; the centre can rewrite it.
	testi: dict[str, str] = field(default_factory=dict)
	natura: str = CONSENSO
	descrizione: str = ""
	#: A field of CRM Lead that mirrors the state, for lists and automations.
	campo_persona: str | None = None
	#: The plan module it belongs to: off there, it is not asked and not shown.
	piano: str = "base"
	#: What one must be able to do to see or record it, beyond ``consensi.vedi``:
	#: an answer about a health dossier says the person is a patient.
	capacita: str | None = None


_tipi: dict[str, TipoConsenso] = {}


def registra_tipo(tipo: TipoConsenso) -> None:
	if tipo.natura not in (CONSENSO, PRESA_VISIONE):
		raise ValueError(f"unknown nature of consent: {tipo.natura!r}")
	_tipi[tipo.chiave] = tipo


def tipi() -> list[TipoConsenso]:
	return list(_tipi.values())


def tipo(chiave: str) -> TipoConsenso | None:
	return _tipi.get(chiave)


def testo_per_lingua(tipo: TipoConsenso, lingua: str | None) -> str:
	"""The shipped text in the site's language, Italian first, then any."""
	lingua = (lingua or "it")[:2]
	return tipo.testi.get(lingua) or tipo.testi.get("it") or next(iter(tipo.testi.values()), "")


def stato_attuale(risposte: list[dict]) -> dict | None:
	"""The answer that counts: the latest one, whatever it said.

	``risposte`` are the register's rows for one person and one type, each with
	``answered_on`` and ``creation``; a withdrawal stamps its row, so a withdrawn
	consent stays the latest until the person answers again.
	"""
	if not risposte:
		return None
	return max(risposte, key=lambda r: (str(r.get("answered_on") or ""), str(r.get("creation") or "")))


def puo_revocare(risposta: dict | None, natura: str) -> bool:
	return bool(risposta) and natura == CONSENSO and risposta.get("status") == DATO
