# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What DottorCloud invoices when money arrives online, without a site (doc 60).

Stripe only collects: the invoice is always DottorCloud's (the SdI, the Sistema
TS), and it is born the day the money arrives. A payment made before the service
makes the service done for that amount (art. 6, c. 4, DPR 633/72): a deposit paid
at /prenota is invoiced on the day it is paid, an «advance invoice».

- **The amount**: an invoice adds the fund and the stamp duty on top of its lines,
  so the line of what was paid is found again until the invoice adds up to the
  money received, to the cent (`imponibile_per`, `torna`).
- **The balance**: the desk invoices the appointment later for its price less the
  advances already invoiced for it (their taxable, less what credit notes took
  back); nothing when they cover it.
- **A refund**: a credit note on the advance for the share given back; an advance
  still a draft has no number, and is thrown away.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

CENTESIMO = Decimal("0.01")

#: What a refund does to the advance invoice, by where the advance is.
NOTA, TOGLI, NIENTE = "credit note", "delete draft", "nothing"


def soldi(valore) -> Decimal:
	"""An amount to the cent, rounded half up."""
	try:
		return Decimal(str(valore or 0)).quantize(CENTESIMO, rounding=ROUND_HALF_UP)
	except (InvalidOperation, ValueError):
		return Decimal("0.00")


def imponibile_per(obiettivo, imponibile, totale) -> Decimal:
	"""The next try at a line's amount, for an invoice that adds up to ``obiettivo``
	when ``imponibile`` made it add up to ``totale``: the fund and the VAT grow with
	the line, so the line moves by the same proportion."""
	obiettivo, imponibile, totale = soldi(obiettivo), soldi(imponibile), soldi(totale)
	if totale <= 0 or imponibile <= 0:
		return obiettivo
	return soldi(imponibile * obiettivo / totale)


def torna(obiettivo, totale) -> bool:
	"""Whether an invoice adds up to the money received, to the cent."""
	return soldi(obiettivo) == soldi(totale)


def anticipato(acconti: list[dict]) -> Decimal:
	"""The taxable already invoiced in advance for an appointment: each advance
	invoice's ``net_total``, less its credit notes' (``nota`` true)."""
	somma = Decimal("0.00")
	for riga in acconti:
		valore = soldi(riga.get("net_total"))
		somma += -valore if riga.get("nota") else valore
	return max(somma, Decimal("0.00"))


def saldo(prezzo, anticipato_) -> Decimal:
	"""What is left to invoice of an appointment: its price less the advances, never
	below nothing."""
	return max(soldi(prezzo) - soldi(anticipato_), Decimal("0.00"))


def coperto(prezzo, anticipato_) -> bool:
	"""Whether the advances invoiced cover the whole price: nothing is left to
	invoice. An appointment without a price is never covered by an advance."""
	return soldi(anticipato_) > 0 and saldo(prezzo, anticipato_) == 0


def al_rimborso(docstatus: int | None) -> str:
	"""What a refund does to its advance invoice: a credit note on an issued one, a
	draft thrown away (it has no number), nothing where there is none."""
	if docstatus == 1:
		return NOTA
	if docstatus == 0:
		return TOGLI
	return NIENTE


def da_stornare(rimborsato, pagato, imponibile_acconto, gia_stornato) -> Decimal:
	"""The taxable a credit note takes back for a refund: the advance's taxable in
	the share given back, less what earlier credit notes took; never more than is
	left of it, never below nothing."""
	rimborsato, pagato = soldi(rimborsato), soldi(pagato)
	imponibile_acconto, gia_stornato = soldi(imponibile_acconto), soldi(gia_stornato)
	if pagato <= 0 or rimborsato <= 0:
		return Decimal("0.00")
	quota = imponibile_acconto if rimborsato >= pagato else soldi(imponibile_acconto * rimborsato / pagato)
	return min(
		max(quota - gia_stornato, Decimal("0.00")), max(imponibile_acconto - gia_stornato, Decimal("0.00"))
	)
