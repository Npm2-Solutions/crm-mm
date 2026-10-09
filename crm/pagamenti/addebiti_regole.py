# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Subscriptions bought from the client area and charged on a saved card, without a
site (doc 60).

- **What is sold online**: a subscription type the centre marked «Sold online from
  the area», enabled, with a price and a fiscal card (its invoice is born at the
  payment); paid at once while the centre sells from the area, by the month only
  while it charges a saved card too.
- **The monthly charge**: on an instalment's day the saved card is charged first,
  and the instalment is invoiced only when the money arrived. A charge that does not
  go through is tried again 3 and 7 days after the due day, at most three times in
  all, never twice the same day; then the instalment is invoiced as any other and
  the desk follows it.
- **The card** as Stripe describes it: brand, last four digits, expiry - never
  more - and in words.
- **Why a charge failed**, from Stripe's code, in the catalogue's words.
"""

from __future__ import annotations

import datetime

#: The days after the due day the card is tried: the first, and the two again.
TENTATIVI = (0, 3, 7)

SUBITO, MENSILE = "Upfront", "Monthly"

#: The card brands Stripe names, as people read them.
MARCHI = {
	"visa": "Visa",
	"mastercard": "Mastercard",
	"amex": "American Express",
	"maestro": "Maestro",
	"discover": "Discover",
	"diners": "Diners Club",
	"jcb": "JCB",
	"unionpay": "UnionPay",
	"cartes_bancaires": "Cartes Bancaires",
}


def perche_non_in_vendita(tipo: dict, vendita: bool, addebiti: bool, collegato: bool = True) -> str | None:
	"""Why a type is not sold from the area, in the catalogue's words; None when it
	is. ``vendita`` and ``addebiti`` are the centre's two switches."""
	if not collegato:
		return "Online payments are not connected: Settings > Invoicing > Online payments."
	if not vendita:
		return "The centre does not sell from the area."
	if not tipo.get("enabled") or not tipo.get("sold_online"):
		return "This subscription is not sold online."
	if not tipo.get("billable_service"):
		return "A subscription sold online needs a fiscal card: its invoice is made at the payment."
	if not float(tipo.get("price") or 0) > 0:
		return "A subscription sold online needs a price."
	if mensile(tipo) and not addebiti:
		return (
			"A subscription paid by the month is sold online only with the monthly charge on the saved card."
		)
	return None


def mensile(tipo: dict) -> bool:
	"""Whether a type is paid month by month: by the month, over more than one."""
	return tipo.get("payment") == MENSILE and int(tipo.get("months") or 1) > 1


def da_tentare(
	oggi: datetime.date,
	dovuta: datetime.date,
	tentativi: int,
	ultimo: datetime.date | None = None,
) -> bool:
	"""Whether the card is charged today for an instalment due on ``dovuta``, after
	``tentativi`` that did not go through, the last on ``ultimo``."""
	tentativi = max(int(tentativi or 0), 0)
	if tentativi >= len(TENTATIVI) or (ultimo and ultimo >= oggi):
		return False
	return oggi >= dovuta + datetime.timedelta(days=TENTATIVI[tentativi])


def esauriti(tentativi: int) -> bool:
	"""Whether the card was tried as many times as it is."""
	return max(int(tentativi or 0), 0) >= len(TENTATIVI)


def prossimo(dovuta: datetime.date, tentativi: int) -> datetime.date | None:
	"""When the card is tried next for an instalment due on ``dovuta``; None when it
	was tried as many times as it is."""
	tentativi = max(int(tentativi or 0), 0)
	if tentativi >= len(TENTATIVI):
		return None
	return dovuta + datetime.timedelta(days=TENTATIVI[tentativi])


def chiave(sito: str, abbonamento: str, rata: str, tentativo: int) -> str:
	"""Stripe's idempotency key of one try: the same try asked twice charges once."""
	return f"{sito}:{abbonamento}:{rata}:{int(tentativo)}"


def marchio(nome: str | None) -> str:
	return MARCHI.get((nome or "").lower(), (nome or "").replace("_", " ").title())


def carta(dettagli: dict | None) -> dict | None:
	"""A card as Stripe describes it (`payment_method.card`), kept to what the page
	shows: brand, last four digits, expiry."""
	if not dettagli or not dettagli.get("last4"):
		return None
	mese, anno = int(dettagli.get("exp_month") or 0), int(dettagli.get("exp_year") or 0)
	return {
		"brand": marchio(dettagli.get("brand")),
		"last4": str(dettagli.get("last4"))[-4:],
		"expiry": f"{mese:02d}/{anno}" if mese and anno else "",
	}


def scaduta(scadenza: str | None, oggi: datetime.date) -> bool:
	"""Whether a card expiring ``MM/YYYY`` is past its month on ``oggi``."""
	try:
		mese, anno = (int(parte) for parte in (scadenza or "").split("/"))
	except ValueError:
		return False
	return (oggi.year, oggi.month) > (anno, mese)


#: Stripe's codes of a charge that did not go through, as the centre and the person
#: read them (`decline_code` first, then `code`).
MOTIVI = {
	"insufficient_funds": "There is not enough money on the card.",
	"expired_card": "The card has expired.",
	"authentication_required": "The bank asks the person to confirm the payment.",
	"lost_card": "The card was reported lost.",
	"stolen_card": "The card was reported stolen.",
	"card_velocity_exceeded": "The card's spending limit was reached.",
	"incorrect_cvc": "The card was declined.",
	"processing_error": "The bank could not process the payment: it is tried again.",
	"card_declined": "The card was declined.",
	"do_not_honor": "The card was declined.",
	"generic_decline": "The card was declined.",
}


def motivo(codice: str | None) -> str:
	"""Why a charge did not go through, in the catalogue's words."""
	return MOTIVI.get(codice or "", "The card could not be charged.")
