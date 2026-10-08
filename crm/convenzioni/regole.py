# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Conventions, health funds and insurances, without a site (doc 61).

An Italian private centre works with funds and insurers (UniSalute, Fasi,
Previmedical, Fasdac, Casagit, MetaSalute…) and with companies, in two ways:

- **direct form** (forma diretta): the fund authorises the visit beforehand with a
  number (the «pratica»), the person pays only their share (a franchigia, a
  percentage, or a share by service) and the centre bills the rest to the fund,
  usually in one invoice a month with one line per pratica;
- **indirect form** (forma indiretta): the person pays the whole price, the
  convention's when it has one, and asks the fund for the money back.

A company convention is a discount for a company's employees, indirect by nature.

These rules decide, to the cent and rounding half up, the convention's price of a
service, the person's share and the fund's, what state a pratica is in, which
pratiche of a month the fund is billed for, the line each one becomes on the
fund's invoice, and the month's statement as a CSV. The Sistema TS is never asked
here: it hears of the person's invoice only, the share they paid (the fund's
invoice goes to a VAT subject, which the Sistema TS does not know).
"""

from __future__ import annotations

import csv
import datetime
import io
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from crm.scheduling import cicli_regole as C

#: What a convention is (stored in English, read through `__()`).
FONDO, ASSICURAZIONE, AZIENDA = "Health fund", "Insurance", "Company"
TIPI = (FONDO, ASSICURAZIONE, AZIENDA)
#: How the person pays under it.
DIRETTA, INDIRETTA = "Direct", "Indirect"
FORME = (DIRETTA, INDIRETTA)
#: Where its prices come from: a price list of the agenda, a discount on the
#: centre's own, or the centre's own as they are.
LISTINO, SCONTO, PREZZI_DEL_CENTRO = "Price list", "Discount", "Centre prices"
PREZZI = (LISTINO, SCONTO, PREZZI_DEL_CENTRO)
#: The person's share in direct form: nothing, a fixed amount (a franchigia), a
#: percentage (a scoperto); a service may have its own.
NIENTE, FISSA, PERCENTUALE = "None", "Fixed", "Percentage"
QUOTE = (NIENTE, FISSA, PERCENTUALE)

#: A pratica's states, from the appointment and the fund's invoice.
DA_AUTORIZZARE = "To authorise"
AUTORIZZATA = "Authorised"
ESEGUITA = "Done"
IN_BOZZA = "Drafted"
FATTURATA = "Billed"
PAGATA = "Paid"
ANNULLATA = "Cancelled"
PERSA = "Missed"
STATI = (DA_AUTORIZZARE, AUTORIZZATA, ESEGUITA, IN_BOZZA, FATTURATA, PAGATA, ANNULLATA, PERSA)

#: The ages of what the funds still owe, for the dashboard: up to so many days.
ETA = (30, 60, 90)

CENTESIMO = Decimal("0.01")


@dataclass(frozen=True)
class Problema:
	"""What is wrong, in English words to translate, with their arguments."""

	messaggio: str
	argomenti: tuple = ()

	def testo(self, traduci=lambda s: s) -> str:
		return traduci(self.messaggio).format(*self.argomenti)


def soldi(valore) -> Decimal:
	"""An amount to the cent, half up: 12.345 is 12.35."""
	try:
		numero = Decimal(str(valore if valore not in (None, "") else 0))
	except Exception:
		numero = Decimal(0)
	return numero.quantize(CENTESIMO, rounding=ROUND_HALF_UP)


def _percentuale(valore) -> Decimal:
	return min(max(soldi(valore), Decimal(0)), Decimal(100))


# ------------------------------------------------------------------ the convention


def problemi(convenzione: dict) -> list[Problema]:
	"""What stops a convention from being saved."""
	trovati: list[Problema] = []
	if not (convenzione.get("convention_name") or "").strip():
		trovati.append(Problema("Write the convention's name"))
	if convenzione.get("kind") not in TIPI:
		trovati.append(Problema("Choose what kind of convention it is"))
	diretta, indiretta = bool(convenzione.get("direct")), bool(convenzione.get("indirect"))
	if not (diretta or indiretta):
		trovati.append(Problema("Choose the direct form, the indirect form or both"))
	if diretta and not convenzione.get("organization"):
		trovati.append(Problema("In direct form the fund is billed: choose the company that pays"))
	modo = convenzione.get("price_mode") or PREZZI_DEL_CENTRO
	if modo == LISTINO and not convenzione.get("price_list"):
		trovati.append(Problema("Choose the price list of the convention"))
	if modo == SCONTO and not Decimal(0) < soldi(convenzione.get("discount_percent")) <= Decimal(100):
		trovati.append(Problema("The discount is a percentage between 0 and 100"))
	if diretta:
		quota = convenzione.get("share_mode") or NIENTE
		if quota == PERCENTUALE and not Decimal(0) <= soldi(convenzione.get("share_percent")) <= Decimal(100):
			trovati.append(Problema("The person's share is a percentage between 0 and 100"))
		if quota == FISSA and soldi(convenzione.get("share_amount")) < 0:
			trovati.append(Problema("The person's share cannot be below zero"))
	for riga in convenzione.get("shares") or []:
		if soldi(riga.get("patient_share")) < 0:
			trovati.append(Problema("The person's share cannot be below zero"))
			break
	dal, al = convenzione.get("valid_from"), convenzione.get("valid_upto")
	if dal and al and str(dal) > str(al):
		trovati.append(Problema("It ends before it starts"))
	return trovati


def valida_il(convenzione: dict, giorno) -> bool:
	"""Whether the convention holds on a day: switched on, within its dates."""
	if not convenzione.get("enabled", 1):
		return False
	giorno = str(giorno)[:10]
	dal, al = convenzione.get("valid_from"), convenzione.get("valid_upto")
	return not ((dal and str(dal)[:10] > giorno) or (al and str(al)[:10] < giorno))


def forme(convenzione: dict) -> list[str]:
	"""The forms the person may use it in."""
	return [
		f for f, si in ((DIRETTA, convenzione.get("direct")), (INDIRETTA, convenzione.get("indirect"))) if si
	]


def prezzo(convenzione: dict, prezzo_del_centro, prezzo_del_listino=None) -> Decimal:
	"""What a service costs under the convention: its price list's (the centre's
	where the list has none for it), the centre's less the discount, or the
	centre's."""
	modo = convenzione.get("price_mode") or PREZZI_DEL_CENTRO
	if modo == LISTINO and prezzo_del_listino is not None:
		return soldi(prezzo_del_listino)
	if modo == SCONTO:
		sconto = _percentuale(convenzione.get("discount_percent"))
		return soldi(soldi(prezzo_del_centro) * (Decimal(100) - sconto) / Decimal(100))
	return soldi(prezzo_del_centro)


def quote(convenzione: dict, forma: str, totale, servizio: str | None = None) -> tuple[Decimal, Decimal]:
	"""``(the person's share, the fund's)`` of a total.

	In indirect form the person pays everything. In direct form a service's own
	share wins over the convention's; a fixed share is never more than the total,
	a percentage is rounded half up and the fund takes the rest, so the two always
	add up to the total."""
	totale = soldi(totale)
	if forma != DIRETTA:
		return totale, Decimal("0.00")
	per_servizio = {
		r.get("service"): r.get("patient_share") for r in convenzione.get("shares") or [] if r.get("service")
	}
	if servizio and servizio in per_servizio:
		persona = soldi(per_servizio[servizio])
	else:
		modo = convenzione.get("share_mode") or NIENTE
		if modo == FISSA:
			persona = soldi(convenzione.get("share_amount"))
		elif modo == PERCENTUALE:
			persona = soldi(totale * _percentuale(convenzione.get("share_percent")) / Decimal(100))
		else:
			persona = Decimal("0.00")
	persona = min(max(persona, Decimal("0.00")), totale)
	return persona, totale - persona


# ------------------------------------------------------------------ the person's cover


def copertura_valida(copertura: dict, giorno) -> bool:
	"""Whether a person's cover holds on a day."""
	giorno = str(giorno)[:10]
	dal, al = copertura.get("valid_from"), copertura.get("valid_upto")
	return not ((dal and str(dal)[:10] > giorno) or (al and str(al)[:10] < giorno))


def problemi_della_copertura(copertura: dict) -> list[Problema]:
	trovati: list[Problema] = []
	if not copertura.get("convention"):
		trovati.append(Problema("Choose the convention"))
	dal, al = copertura.get("valid_from"), copertura.get("valid_upto")
	if dal and al and str(dal) > str(al):
		trovati.append(Problema("It ends before it starts"))
	return trovati


# ------------------------------------------------------------------ the pratica


def manca_l_autorizzazione(forma: str | None, richiesta: bool, autorizzazione: str | None) -> bool:
	"""Direct form, the fund wants its yes first, and nobody wrote its number."""
	return forma == DIRETTA and bool(richiesta) and not (autorizzazione or "").strip()


def stato(
	stato_appuntamento: str | None,
	stato_partecipante: str | None,
	richiesta: bool,
	autorizzazione: str | None,
	fattura_docstatus: int | None = None,
	incassata: bool = False,
) -> str:
	"""Where a pratica in direct form stands: from the appointment, its person's
	attendance and the fund's invoice that holds it (a cancelled one holds none)."""
	if fattura_docstatus == 1:
		return PAGATA if incassata else FATTURATA
	if fattura_docstatus == 0:
		return IN_BOZZA
	seduta = C.seduta(stato_appuntamento, stato_partecipante)
	if seduta == C.ANNULLATA:
		return ANNULLATA
	if seduta == C.PERSA:
		return PERSA
	if manca_l_autorizzazione(DIRETTA, richiesta, autorizzazione):
		return DA_AUTORIZZARE
	return ESEGUITA if seduta == C.FATTA else AUTORIZZATA


def da_fatturare(pratica: dict) -> bool:
	"""A pratica the fund may be billed for: done, with its yes when it needs one,
	something to bill, in no invoice yet."""
	return pratica.get("state") == ESEGUITA and soldi(pratica.get("fund_share")) > 0


def mese(valore) -> tuple[datetime.date, datetime.date]:
	"""The first and last day of the month of ``valore`` ("2026-10" or a date)."""
	testo = str(valore)[:7]
	anno, numero = int(testo[:4]), int(testo[5:7])
	primo = datetime.date(anno, numero, 1)
	dopo = datetime.date(anno + (numero == 12), numero % 12 + 1, 1)
	return primo, dopo - datetime.timedelta(days=1)


def totali(pratiche: list[dict]) -> dict:
	"""A month's statement in numbers: how many by state, what the people paid and
	what the fund owes, what is still to bill."""
	per_stato = {s: 0 for s in STATI}
	persone = fondo = da_fatturare_ = Decimal("0.00")
	for p in pratiche:
		per_stato[p.get("state")] = per_stato.get(p.get("state"), 0) + 1
		if p.get("state") in (ANNULLATA, PERSA):
			continue
		persone += soldi(p.get("patient_share"))
		fondo += soldi(p.get("fund_share"))
		if da_fatturare(p):
			da_fatturare_ += soldi(p.get("fund_share"))
	return {
		"count": len(pratiche),
		"by_state": per_stato,
		"patient_share": float(persone),
		"fund_share": float(fondo),
		"to_bill": float(da_fatturare_),
		"to_bill_count": sum(1 for p in pratiche if da_fatturare(p)),
	}


def descrizione(servizio: str, persona: str, giorno, autorizzazione: str | None, tessera: str | None) -> str:
	"""A pratica's line on the fund's invoice: what, for whom, when, and the
	numbers the fund matches it by. Nothing more of the person's health: the
	electronic invoice to a VAT subject carries no health data it does not need."""
	data = datetime.date.fromisoformat(str(giorno)[:10]).strftime("%d/%m/%Y")
	parti = [servizio, persona, data]
	if autorizzazione:
		parti.append(f"Aut. {autorizzazione}")
	if tessera:
		parti.append(f"Tessera {tessera}")
	return " · ".join(p for p in parti if p)


#: The statement's columns, in Italian as the funds' portals read them.
COLONNE = (
	("date", "Data"),
	("patient", "Assistito"),
	("card_number", "Tessera"),
	("authorisation", "Autorizzazione"),
	("service", "Prestazione"),
	("total", "Importo"),
	("patient_share", "Quota assistito"),
	("fund_share", "Quota fondo"),
	("state", "Stato"),
	("invoice", "Fattura"),
)

#: A state as the statement writes it.
STATI_IN_ITALIANO = {
	DA_AUTORIZZARE: "Da autorizzare",
	AUTORIZZATA: "Autorizzata",
	ESEGUITA: "Eseguita",
	IN_BOZZA: "In bozza",
	FATTURATA: "Fatturata",
	PAGATA: "Pagata",
	ANNULLATA: "Annullata",
	PERSA: "Non presentato",
}


def csv_del_mese(pratiche: list[dict]) -> str:
	"""The month's pratiche as a CSV an Italian spreadsheet opens: semicolons, the
	comma for decimals, the day as dd/mm/yyyy."""
	uscita = io.StringIO()
	scrittore = csv.writer(uscita, delimiter=";", lineterminator="\r\n")
	scrittore.writerow([titolo for _chiave, titolo in COLONNE])
	for p in pratiche:
		riga = []
		for chiave, _titolo in COLONNE:
			valore = p.get(chiave)
			if chiave in ("total", "patient_share", "fund_share"):
				valore = f"{soldi(valore):.2f}".replace(".", ",")
			elif chiave == "date" and valore:
				valore = datetime.date.fromisoformat(str(valore)[:10]).strftime("%d/%m/%Y")
			elif chiave == "state":
				valore = STATI_IN_ITALIANO.get(valore, valore)
			riga.append("" if valore is None else valore)
		scrittore.writerow(riga)
	return uscita.getvalue()


def fascia(giorni: int) -> str:
	"""How old something still owed is: "30", "60", "90" or "older"."""
	for limite in ETA:
		if giorni <= limite:
			return str(limite)
	return "older"
