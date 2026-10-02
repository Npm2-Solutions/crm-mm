# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What the centre's Twilio space spends, without a site (doc 52, fifth part).

- **This month**, by kind: calls, SMS, numbers, recordings and transcriptions,
  and whatever else Twilio billed, from Twilio's usage records; the total is
  Twilio's own, in the account's currency.
- **The spend alert**: when this month's total reaches the amount the centre set,
  Twilio calls DottorCloud back (a usage trigger, every month again). What is to
  be done with the trigger when the amount changes.

The words are English, translated where they are shown.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

#: Twilio's usage categories DottorCloud shows, in the order of the page: a kind
#: and the categories that make it. Each is a parent of Twilio's finer ones (calls
#: holds the inbound, the outbound and the browser's), so nothing counts twice.
VOCI = (
	("calls", "Calls", ("calls",)),
	("sms", "SMS", ("sms",)),
	("numbers", "Numbers", ("phonenumbers",)),
	("recordings", "Recordings and transcriptions", ("recordings", "recordingstorage", "transcriptions")),
)
#: Everything Twilio billed in the period.
TOTALE = "totalprice"
#: The categories to ask Twilio for.
CATEGORIE = (*(categoria for _chiave, _nome, categorie in VOCI for categoria in categorie), TOTALE)

#: The largest monthly alert the page takes, in the account's currency.
SOGLIA_MASSIMA = Decimal("100000")


def _numero(valore) -> Decimal:
	"""A number Twilio or the page wrote; 0 for anything that is not one."""
	try:
		numero = Decimal(str(valore or 0).strip())
	except InvalidOperation:
		return Decimal(0)
	return numero if numero.is_finite() else Decimal(0)


def _centesimi(numero: Decimal) -> str:
	return str(numero.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def consumi(righe: dict[str, dict]) -> dict:
	"""This month's spend by kind, from Twilio's records by category
	(``{"calls": {"count", "usage", "usage_unit", "price", "price_unit"}}``).

	A kind carries how many (calls, messages, numbers), the minutes where Twilio
	counts them, and what it cost; "other" is what the total holds besides them.
	Prices stay as Twilio states them, rounded to the cent only here."""
	voci = []
	somma = Decimal(0)
	for chiave, nome, categorie in VOCI:
		trovate = [righe[categoria] for categoria in categorie if categoria in righe]
		prezzo = sum((_numero(riga.get("price")) for riga in trovate), Decimal(0))
		principale = righe.get(categorie[0]) or {}
		minuti = _numero(principale.get("usage")) if principale.get("usage_unit") == "minutes" else None
		somma += prezzo
		voci.append(
			{
				"key": chiave,
				"label": nome,
				"count": int(_numero(principale.get("count"))),
				"minutes": int(minuti) if minuti is not None else None,
				"price": _centesimi(prezzo),
			}
		)
	totale = _numero((righe.get(TOTALE) or {}).get("price"))
	altro = max(totale - somma, Decimal(0))
	if altro >= Decimal("0.01"):
		voci.append(
			{"key": "other", "label": "Other", "count": None, "minutes": None, "price": _centesimi(altro)}
		)
	valuta = next((riga.get("price_unit") for riga in righe.values() if riga.get("price_unit")), "") or ""
	return {
		"items": voci,
		"total": _centesimi(max(totale, somma)),
		"currency": valuta.upper(),
	}


def soglia(valore) -> Decimal | None:
	"""The monthly alert's amount as the page wrote it; None for no alert. Raises
	ValueError for an amount that cannot be one."""
	if valore in (None, "", 0, "0"):
		return None
	numero = _numero(valore)
	if numero <= 0 or numero > SOGLIA_MASSIMA:
		raise ValueError("The alert is an amount between 0 and 100,000.")
	return numero.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def cosa_fare_del_trigger(attuale: dict | None, voluta: Decimal | None, indirizzo: str) -> str:
	"""What to do with Twilio's trigger for the wanted amount: 'create', 'replace'
	(Twilio does not change a trigger's amount: a new one takes the old one's
	place), 'update' (only where it calls back), 'delete' (no alert any more) or ''
	(as it should be). ``attuale`` is Twilio's trigger - its ``trigger_value`` and
	``callback_url`` - or None; ``indirizzo`` is where DottorCloud hears it."""
	if voluta is None:
		return "delete" if attuale else ""
	if not attuale:
		return "create"
	if _numero(attuale.get("trigger_value")) != voluta:
		return "replace"
	return "" if attuale.get("callback_url") == indirizzo else "update"
