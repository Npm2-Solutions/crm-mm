# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A quote, without a site (docs/verticali/clinica/design.md, "Tre strati": "Il
preventivo").

- **What it holds**: services from the price list, each with its quantity, price
  and discount, in phases. A module adds what its rows say besides - the clinic a
  tooth and its surfaces (`crm.clinica.cure`).
- **How it goes**: a draft of its author; proposed, it is handed to the person and
  not rewritten; accepted, its services are done one by one - an appointment of a
  service takes the first one still to do - and when every one is done or
  cancelled, the quote is completed. Declined, it stays as it was; a new version
  starts from it. An accepted quote stopped half-way is closed.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

BOZZA, PROPOSTO, ACCETTATO, RIFIUTATO, COMPLETATO, CHIUSO = (
	"Draft",
	"Proposed",
	"Accepted",
	"Declined",
	"Completed",
	"Closed",
)
#: From where each state is reached.
PASSAGGI = {
	PROPOSTO: {BOZZA},
	BOZZA: {PROPOSTO},
	ACCETTATO: {PROPOSTO},
	RIFIUTATO: {PROPOSTO},
	COMPLETATO: {ACCETTATO},
	CHIUSO: {ACCETTATO},
}

DA_FARE, PRENOTATA, FATTA, ANNULLATA = "To do", "Booked", "Done", "Cancelled"
MAX_VOCI = 200
#: How long a quote holds, unless whoever writes it says otherwise.
GIORNI_VALIDITA = 60


@dataclass(frozen=True)
class Problema:
	"""What is wrong, in English words to translate, with their arguments."""

	messaggio: str
	argomenti: tuple = ()

	def testo(self, traduci=lambda s: s) -> str:
		return traduci(self.messaggio).format(*self.argomenti)


def si_passa(da: str, a: str) -> bool:
	return da in PASSAGGI.get(a, set())


def importo(quantita, prezzo, sconto) -> float:
	"""A row's amount: quantity times price, less the discount, to the cent."""
	q = float(quantita or 0)
	p = float(prezzo or 0)
	s = min(max(float(sconto or 0), 0.0), 100.0)
	return round(q * p * (100 - s) / 100 + 1e-9, 2)


def totali(voci: list[dict]) -> dict[str, float]:
	"""The quote's sums: before and after the discount, and how much is done and
	left. A cancelled row does not count."""
	lordo = netto = fatto = 0.0
	for voce in voci:
		if voce.get("status") == ANNULLATA:
			continue
		lordo += float(voce.get("qty") or 0) * float(voce.get("rate") or 0)
		valore = importo(voce.get("qty"), voce.get("rate"), voce.get("discount"))
		netto += valore
		if voce.get("status") == FATTA:
			fatto += valore
	lordo, netto, fatto = round(lordo, 2), round(netto, 2), round(fatto, 2)
	return {
		"gross": lordo,
		"discount": round(lordo - netto, 2),
		"net": netto,
		"done": fatto,
		"left": round(netto - fatto, 2),
	}


def fasi(voci: list[dict]) -> list[tuple[int, list[int]]]:
	"""The phases in order, each with the positions of its rows."""
	gruppi: dict[int, list[int]] = {}
	for n, voce in enumerate(voci):
		gruppi.setdefault(max(int(voce.get("phase") or 1), 1), []).append(n)
	return sorted(gruppi.items())


def voce_per(voci: list[dict], servizio: str) -> int | None:
	"""The row an appointment of ``servizio`` takes: the first still to do, in the
	order of the phases."""
	for _fase, posizioni in fasi(voci):
		for n in posizioni:
			if voci[n].get("service") == servizio and voci[n].get("status", DA_FARE) == DA_FARE:
				return n
	return None


def completato(voci: list[dict]) -> bool:
	"""Every row done or cancelled, and at least one done."""
	stati = [voce.get("status", DA_FARE) for voce in voci]
	return FATTA in stati and all(stato in (FATTA, ANNULLATA) for stato in stati)


#: what the editor writes by itself in a new row
DA_SOLI = ("qty", "phase", "discount", "status")


def vuota(voce: dict) -> bool:
	"""A row nobody wrote in. The editor opens with one and adds them one at a
	time, so one can be left behind empty: it is no row, rather than a «choose the
	service» that stops the draft. A module's field written in it (a tooth) makes
	it a row."""
	for campo, valore in voce.items():
		if campo in DA_SOLI:
			continue
		if campo == "rate":
			if float(valore or 0):
				return False
		elif valore is not None and str(valore).strip():
			return False
	return True


def valida(voci: list[dict]) -> list[Problema]:
	"""What is wrong with a quote's rows before it is proposed; a module checks
	its own fields on top (the clinic: a tooth, its surfaces)."""
	if not voci:
		return [Problema("A quote has at least one service")]
	if len(voci) > MAX_VOCI:
		return [Problema("A quote has at most {0} services", (MAX_VOCI,))]
	problemi = []
	for n, voce in enumerate(voci, 1):
		if not voce.get("service"):
			problemi.append(Problema("Row {0}: choose the service", (n,)))
		if float(voce.get("qty") or 0) <= 0:
			problemi.append(Problema("Row {0}: the quantity is more than zero", (n,)))
		if float(voce.get("rate") or 0) < 0:
			problemi.append(Problema("Row {0}: the price is not negative", (n,)))
		if not 0 <= float(voce.get("discount") or 0) <= 100:
			problemi.append(Problema("Row {0}: the discount is from 0 to 100%", (n,)))
	return problemi


# ------------------------------------------------------------------ the person's answer

#: Where the person said yes or no: at the desk, recorded by the centre, or in
#: their client area, with their own signature.
AL_BANCO, NELL_AREA = "At the desk", "In the client area"
#: The most a reason written in the area keeps.
MAX_MOTIVO = 500


def da_rispondere(stato: str, valido_fino, oggi) -> Problema | None:
	"""Whether the person may still accept or decline the quote from their area:
	proposed, and not past the day it holds until. ``valido_fino`` and ``oggi``
	are dates; what is wrong says the day as the caller words it."""
	if stato != PROPOSTO:
		return Problema("This quote is no longer waiting for an answer")
	if valido_fino and valido_fino < oggi:
		return Problema("This quote was valid until {0}: ask the centre for a new one", (valido_fino,))
	return None


def motivo(testo: str | None) -> str | None:
	"""A reason the person wrote: its words, without the spaces around them, and
	not a book."""
	parole = (testo or "").strip()
	return parole[:MAX_MOTIVO].rstrip() or None


def impronta(contenuto: dict) -> str:
	"""The SHA-256 of what a signature is put on, written the one way: the same
	services and sums give the same fingerprint, whatever order they came in."""
	testo = json.dumps(contenuto, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
	return hashlib.sha256(testo.encode("utf-8")).hexdigest()
