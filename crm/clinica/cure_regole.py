# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Dental care plans, without a site (docs/gestionale-medico, phase 3: "piani di cura
(odontoiatria)"; the open question 2: "odontogramma, preventivi, piani di cura").

- **The teeth** in the FDI notation (ISO 3950), the one Italian dentists write:
  two digits, the quadrant then the tooth counted from the midline. Permanent 11-18,
  21-28, 31-38, 41-48; deciduous 51-55, 61-65, 71-75, 81-85.
- **The surfaces**: mesial, occlusal (incisal on incisors and canines), distal,
  vestibular, lingual (palatal on the upper arch): M, O, D, V, L, written in that
  order ("MOD"). I, B and P are read as O, V and L.
- **The chart** says what each tooth is now, one row per condition: caries and a
  filling on their surfaces, a root canal, a crown, an implant, missing, to extract.
  A missing tooth has nothing else; the rest may go together.
- **A care plan is a quote first**: treatments, each maybe on a tooth and its
  surfaces, in phases, with its price and discount. Proposed, it is handed to the
  person; accepted, its treatments are done one by one - an appointment of a
  treatment's service takes the first one still to do - and when every one is done
  or cancelled, the plan is completed. Declined, it stays as it was.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Who writes the chart and the plans, by the code of their qualification: the
#: dentist, and the doctor who practises dentistry (a hygienist reads them).
DENTISTI = frozenset({"odontoiatra", "medico_chirurgo"})


def scrive(qualifica: str | None) -> bool:
	return qualifica in DENTISTI


# ------------------------------------------------------------------ the teeth

PERMANENTI = (1, 2, 3, 4)
DECIDUI = (5, 6, 7, 8)

PERMANENTE, MISTA, DECIDUA = "Permanent", "Mixed", "Deciduous"
DENTIZIONI = (PERMANENTE, MISTA, DECIDUA)


def e_dente(codice) -> bool:
	"""Whether ``codice`` is a tooth in the FDI notation."""
	try:
		numero = int(str(codice).strip())
	except (TypeError, ValueError):
		return False
	quadrante, dente = divmod(numero, 10)
	if quadrante in PERMANENTI:
		return 1 <= dente <= 8
	if quadrante in DECIDUI:
		return 1 <= dente <= 5
	return False


def deciduo(dente) -> bool:
	return int(dente) // 10 in DECIDUI


def superiore(dente) -> bool:
	return int(dente) // 10 in (1, 2, 5, 6)


def anteriore(dente) -> bool:
	"""Incisors and canines: their occlusal surface is the incisal edge."""
	return int(dente) % 10 <= 3


def arcate(dentizione: str = PERMANENTE) -> list[list[int]]:
	"""The rows a chart draws, the patient's right on the viewer's left: the upper
	arch, then the lower. A mixed dentition draws the milk teeth between them."""

	def arcata(destra: int, sinistra: int, quanti: int) -> list[int]:
		return [destra * 10 + n for n in range(quanti, 0, -1)] + [
			sinistra * 10 + n for n in range(1, quanti + 1)
		]

	permanenti = [arcata(1, 2, 8), arcata(4, 3, 8)]
	decidui = [arcata(5, 6, 5), arcata(8, 7, 5)]
	if dentizione == DECIDUA:
		return decidui
	if dentizione == MISTA:
		return [permanenti[0], decidui[0], decidui[1], permanenti[1]]
	return permanenti


# ------------------------------------------------------------------ the surfaces

SUPERFICI = ("M", "O", "D", "V", "L")
_SINONIMI = {"I": "O", "B": "V", "P": "L"}


def superfici(testo: str | None) -> str | None:
	"""The surfaces in their order ("dom" is "MOD"); None when one is not a surface."""
	lettere = set()
	for lettera in (testo or "").upper().replace(",", "").replace(" ", ""):
		lettera = _SINONIMI.get(lettera, lettera)
		if lettera not in SUPERFICI:
			return None
		lettere.add(lettera)
	return "".join(s for s in SUPERFICI if s in lettere)


# ------------------------------------------------------------------ the chart

CARIE = "Caries"
OTTURAZIONE = "Filling"
DEVITALIZZATO = "Root canal"
CORONA = "Crown"
IMPIANTO = "Implant"
MANCANTE = "Missing"
DA_ESTRARRE = "To extract"
PONTE = "Bridge"
FRATTURA = "Fracture"
SIGILLATURA = "Sealant"
FACCETTA = "Veneer"
MOBILE = "Mobile"
INCLUSO = "Impacted"
ALTRO = "Other"
CONDIZIONI = (
	CARIE,
	OTTURAZIONE,
	DEVITALIZZATO,
	CORONA,
	IMPIANTO,
	MANCANTE,
	DA_ESTRARRE,
	PONTE,
	FRATTURA,
	SIGILLATURA,
	FACCETTA,
	MOBILE,
	INCLUSO,
	ALTRO,
)
#: The conditions that sit on surfaces; the others are the whole tooth.
SU_SUPERFICI = frozenset({CARIE, OTTURAZIONE, FRATTURA, SIGILLATURA})


@dataclass(frozen=True)
class Problema:
	"""What is wrong, in English words to translate, with their arguments."""

	messaggio: str
	argomenti: tuple = ()

	def testo(self, traduci=lambda s: s) -> str:
		return traduci(self.messaggio).format(*self.argomenti)


def pulisci_stato(righe: list[dict]) -> list[dict]:
	"""The chart's rows as they are kept: one per tooth and condition - the surfaces
	of two rows of caries on a tooth go together - in the chart's order."""
	per_chiave: dict[tuple[int, str], dict] = {}
	for riga in righe:
		dente, condizione = riga.get("tooth"), riga.get("condition")
		if not e_dente(dente) or condizione not in CONDIZIONI:
			continue
		chiave = (int(dente), condizione)
		lati = superfici(riga.get("surfaces")) if condizione in SU_SUPERFICI else ""
		nota = (riga.get("note") or "").strip()
		if chiave in per_chiave:
			prima = per_chiave[chiave]
			prima["surfaces"] = superfici((prima["surfaces"] or "") + (lati or "")) or ""
			prima["note"] = "; ".join(n for n in (prima["note"], nota) if n)
			continue
		per_chiave[chiave] = {
			"tooth": str(int(dente)),
			"condition": condizione,
			"surfaces": lati or "",
			"note": nota,
		}
	ordine = {condizione: n for n, condizione in enumerate(CONDIZIONI)}
	return sorted(per_chiave.values(), key=lambda r: (int(r["tooth"]), ordine[r["condition"]]))


def valida_stato(righe: list[dict]) -> list[Problema]:
	"""What is wrong with a chart: a tooth that is not one, a condition unknown,
	surfaces that are not surfaces, a missing tooth with something on it."""
	problemi = []
	per_dente: dict[int, set[str]] = {}
	for riga in righe:
		dente, condizione = riga.get("tooth"), riga.get("condition")
		if not e_dente(dente):
			problemi.append(Problema("{0} is not a tooth", (dente,)))
			continue
		if condizione not in CONDIZIONI:
			problemi.append(Problema("Unknown condition: {0}", (condizione,)))
			continue
		if condizione in SU_SUPERFICI and superfici(riga.get("surfaces")) is None:
			problemi.append(Problema("Tooth {0}: {1} are not surfaces", (dente, riga.get("surfaces"))))
		per_dente.setdefault(int(dente), set()).add(condizione)
	for dente, condizioni in sorted(per_dente.items()):
		if MANCANTE in condizioni and len(condizioni) > 1:
			problemi.append(Problema("Tooth {0} is missing: nothing else goes on it", (dente,)))
	return problemi


# ------------------------------------------------------------------ the plan

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


def si_passa(da: str, a: str) -> bool:
	return da in PASSAGGI.get(a, set())


def importo(quantita, prezzo, sconto) -> float:
	"""A treatment's amount: quantity times price, less the discount, to the cent."""
	q = float(quantita or 0)
	p = float(prezzo or 0)
	s = min(max(float(sconto or 0), 0.0), 100.0)
	return round(q * p * (100 - s) / 100 + 1e-9, 2)


def totali(voci: list[dict]) -> dict[str, float]:
	"""The plan's sums: before and after the discount, and how much is done and left.
	A cancelled treatment does not count."""
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
	"""The phases in order, each with the positions of its treatments."""
	gruppi: dict[int, list[int]] = {}
	for n, voce in enumerate(voci):
		gruppi.setdefault(max(int(voce.get("phase") or 1), 1), []).append(n)
	return sorted(gruppi.items())


def voce_per(voci: list[dict], servizio: str) -> int | None:
	"""The treatment an appointment of ``servizio`` takes: the first still to do, in
	the order of the phases."""
	for _fase, posizioni in fasi(voci):
		for n in posizioni:
			if voci[n].get("service") == servizio and voci[n].get("status", DA_FARE) == DA_FARE:
				return n
	return None


def completato(voci: list[dict]) -> bool:
	"""Every treatment done or cancelled, and at least one done."""
	stati = [voce.get("status", DA_FARE) for voce in voci]
	return FATTA in stati and all(stato in (FATTA, ANNULLATA) for stato in stati)


def valida_piano(voci: list[dict]) -> list[Problema]:
	"""What is wrong with a plan's treatments before it is proposed."""
	problemi = []
	if not voci:
		return [Problema("A plan has at least one treatment")]
	if len(voci) > MAX_VOCI:
		return [Problema("A plan has at most {0} treatments", (MAX_VOCI,))]
	for n, voce in enumerate(voci, 1):
		if not voce.get("service"):
			problemi.append(Problema("Treatment {0}: choose the service", (n,)))
		dente = voce.get("tooth")
		if dente and not e_dente(dente):
			problemi.append(Problema("Treatment {0}: {1} is not a tooth", (n, dente)))
		if voce.get("surfaces") and (not dente or superfici(voce.get("surfaces")) is None):
			problemi.append(Problema("Treatment {0}: surfaces go with a tooth, as M, O, D, V, L", (n,)))
		if float(voce.get("qty") or 0) <= 0:
			problemi.append(Problema("Treatment {0}: the quantity is more than zero", (n,)))
		if float(voce.get("rate") or 0) < 0:
			problemi.append(Problema("Treatment {0}: the price is not negative", (n,)))
		if not 0 <= float(voce.get("discount") or 0) <= 100:
			problemi.append(Problema("Treatment {0}: the discount is from 0 to 100%", (n,)))
	return problemi
