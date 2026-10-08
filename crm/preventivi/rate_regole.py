# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A quote paid in instalments, without a site (docs/crm/63).

The centre's own plan: a deposit, maybe nothing, and from 2 to 36 equal instalments
a month or two apart, without interest nor fees - no finance company in between.

- **The schedule**: the deposit when the quote is accepted, the instalments from the
  first day chosen, on the same day of the month (the last of a shorter month); each
  instalment to the cent, what the cents leave over on the last.
- **How each goes**: to pay; invoiced (its invoice made); paid (its invoice
  collected, or - where the centre invoices by itself - marked); cancelled (the
  quote closed or replaced before it was invoiced).
- **Following it**: how many are paid, the next one and when, the ones late.

The browser does the same sums (`frontend/src/utils/preventivi.js`) on the same
cases (`tests/casi_rate.json`).
"""

from __future__ import annotations

import datetime
import math

from crm.preventivi.regole import Problema
from crm.scheduling.abbonamenti_regole import piu_mesi

#: How the quote is paid.
UNICA, A_RATE = "Single payment", "Instalments"
#: How the deposit is written.
IMPORTO, PERCENTUALE = "Amount", "Percent"
#: A row of the schedule.
ACCONTO, RATA = "Deposit", "Instalment"
#: How a row goes.
DA_PAGARE, FATTURATA, PAGATA, ANNULLATA = "To pay", "Invoiced", "Paid", "Cancelled"
#: How the centre invoices them (`CRM Quote Settings`): DottorCloud an invoice each
#: when due, or the centre by itself, the instalments only followed.
OGNI_RATA, SOLO_SEGUITE = "Each instalment when due", "Track only"

MIN_RATE, MAX_RATE = 2, 36
#: Months between two instalments.
OGNI = (1, 2)


def _cent(valore) -> float:
	return round(float(valore or 0) + 1e-9, 2)


def acconto(totale, tipo: str, valore) -> float:
	"""The deposit in money: an amount, or a share of the total; never below nothing
	nor above the total."""
	totale = _cent(totale)
	numero = float(valore or 0)
	soldi = totale * numero / 100 if tipo == PERCENTUALE else numero
	return min(max(_cent(soldi), 0.0), totale)


def quote(resto, numero: int) -> list[float]:
	"""``resto`` in ``numero`` equal instalments to the cent, what the cents leave on
	the last."""
	centesimi = round(float(resto or 0) * 100)
	base = math.floor(centesimi / numero) if numero else 0
	fatto = [base] * numero
	if fatto:
		fatto[-1] = centesimi - base * (numero - 1)
	return [c / 100 for c in fatto]


def piano(totale, soldi_acconto, numero: int, ogni_mesi: int, primo: datetime.date | None) -> list[dict]:
	"""The schedule: the deposit (when there is one, due when accepted: no day yet)
	and the instalments, the first on ``primo``, then every ``ogni_mesi`` months."""
	totale = _cent(totale)
	soldi_acconto = min(_cent(soldi_acconto), totale)
	fatto = []
	if soldi_acconto > 0:
		fatto.append({"kind": ACCONTO, "number": 0, "due_on": None, "amount": soldi_acconto})
	for n, soldi in enumerate(quote(totale - soldi_acconto, numero)):
		fatto.append(
			{
				"kind": RATA,
				"number": n + 1,
				"due_on": piu_mesi(primo, n * ogni_mesi) if primo else None,
				"amount": soldi,
			}
		)
	return fatto


def problemi(totale, tipo: str, valore, numero, ogni_mesi, primo, oggi=None) -> list[Problema]:
	"""What is wrong with the terms of a plan; ``oggi`` given (when it is proposed),
	the first instalment is not in the past."""
	fatto = []
	try:
		numero = int(numero or 0)
	except (TypeError, ValueError):
		numero = 0
	if not MIN_RATE <= numero <= MAX_RATE:
		fatto.append(Problema("Instalments: from {0} to {1}", (MIN_RATE, MAX_RATE)))
	if int(ogni_mesi or 0) not in OGNI:
		fatto.append(Problema("Instalments go every month or every two months"))
	if float(valore or 0) < 0 or (tipo == PERCENTUALE and float(valore or 0) >= 100):
		fatto.append(Problema("The deposit is less than the total"))
	elif _cent(totale) > 0 and acconto(totale, tipo, valore) >= _cent(totale):
		fatto.append(Problema("The deposit is less than the total"))
	if not primo:
		fatto.append(Problema("Choose the day of the first instalment"))
	elif oggi and primo < oggi:
		fatto.append(Problema("The first instalment is not in the past"))
	if not fatto and _cent(totale) > 0:
		resto = _cent(totale) - acconto(totale, tipo, valore)
		if min(quote(resto, numero)) <= 0:
			fatto.append(Problema("Too many instalments for what is left to pay"))
	return fatto


def stato(annullata: bool, fattura_viva: bool, incassata: bool, segnata: bool = False) -> str:
	"""How a row goes, from its invoice: collected, it is paid; made, invoiced;
	none, to pay. Marked paid by hand where the centre invoices by itself."""
	if annullata:
		return ANNULLATA
	if fattura_viva:
		return PAGATA if incassata else FATTURATA
	return PAGATA if segnata else DA_PAGARE


def dovute(rate: list[dict], oggi: datetime.date) -> list[int]:
	"""The rows to invoice today: to pay, and due."""
	return [
		n
		for n, riga in enumerate(rate)
		if riga.get("status", DA_PAGARE) == DA_PAGARE and riga.get("due_on") and riga["due_on"] <= oggi
	]


def da_annullare(rate: list[dict]) -> list[int]:
	"""What a quote closed or replaced takes away: the rows not invoiced yet."""
	return [n for n, riga in enumerate(rate) if riga.get("status", DA_PAGARE) == DA_PAGARE]


def resto(rate: list[dict]) -> float:
	"""What is left to invoice: the rows still to pay."""
	return _cent(sum(float(rate[n].get("amount") or 0) for n in da_annullare(rate)))


def riassunto(rate: list[dict], oggi: datetime.date) -> dict | None:
	"""How the plan goes: the instalments paid of how many, the next row not paid
	and its day, the rows late and what they are worth, what is left to pay."""
	vive = [riga for riga in rate if riga.get("status", DA_PAGARE) != ANNULLATA]
	if not vive:
		return None
	rate_vive = [riga for riga in vive if riga.get("kind") == RATA]
	aperte = [riga for riga in vive if riga.get("status", DA_PAGARE) != PAGATA]
	tardi = [riga for riga in aperte if riga.get("due_on") and riga["due_on"] < oggi]
	prossima = next(iter(sorted(aperte, key=lambda r: r.get("due_on") or datetime.date.min)), None)
	return {
		"count": len(rate_vive),
		"paid": sum(1 for riga in rate_vive if riga.get("status") == PAGATA),
		"deposit": next((riga for riga in vive if riga.get("kind") == ACCONTO), None),
		"next": prossima,
		"late": len(tardi),
		"late_amount": _cent(sum(float(r.get("amount") or 0) for r in tardi)),
		"left": _cent(sum(float(r.get("amount") or 0) for r in aperte)),
		"cancelled": len(rate) - len(vive),
	}
