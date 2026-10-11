# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What the centre's Telnyx account spends, without a site (doc 65).

- **This month**, by kind - calls, SMS, numbers, recordings - from Telnyx's usage
  reports (one product at a time) and its monthly charges (the numbers' fees);
  the total is their sum, in the account's currency.
- **The balance**: Telnyx's account is prepaid, and its balance says when calls
  and SMS are about to stop. Twilio does not tell a space its account's credit;
  Telnyx tells the account its own, and the page shows it.
- **The alerts**: Telnyx has no trigger that calls back when a month's spend
  reaches an amount, as Twilio's usage triggers do. DottorCloud looks every hour
  and tells whoever pays once a month when the spend reaches the alert, and once
  when the balance goes down to its alert, again only after it was topped up.

The words are English, translated where they are shown.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

#: Telnyx's usage-report products DottorCloud shows, in the order of the page: a
#: kind and the products that make it, with the metrics asked of each.
VOCI = (
	("calls", "Calls", ("call-control", "sip-trunking", "webrtc")),
	("sms", "SMS", ("messaging",)),
	("recordings", "Recordings and transcriptions", ("recording", "speech-to-text")),
)
#: What each product is asked: its cost always, how many where it counts them.
METRICHE = {"messaging": ("cost", "count"), "call-control": ("cost", "billed_sec", "connected")}
#: The products to ask Telnyx for.
PRODOTTI = tuple(prodotto for _chiave, _nome, prodotti in VOCI for prodotto in prodotti)


def _numero(valore) -> Decimal:
	"""A number Telnyx or the page wrote; 0 for anything that is not one."""
	try:
		numero = Decimal(str(valore if valore not in (None, "") else 0).strip())
	except InvalidOperation:
		return Decimal(0)
	return numero if numero.is_finite() else Decimal(0)


def _centesimi(numero: Decimal) -> str:
	return str(numero.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _somma(righe: list[dict], campo: str) -> Decimal:
	return sum((_numero(riga.get(campo)) for riga in righe or []), Decimal(0))


def dei_numeri(sommario: dict | None) -> dict:
	"""The numbers' fees this month, from Telnyx's charges summary: how many numbers,
	and what their monthly and one-off charges come to."""
	righe = ((sommario or {}).get("summary") or {}).get("lines") or []
	quanti, prezzo = 0, Decimal(0)
	for riga in righe:
		if riga.get("type") == "comparative":
			for parte in ("new_this_month", "existing_this_month"):
				dati = riga.get(parte) or {}
				quanti += int(_numero(dati.get("quantity")))
				prezzo += _numero(dati.get("mrc")) + _numero(dati.get("otc"))
		else:
			prezzo += _numero(riga.get("amount"))
	return {"count": quanti, "price": prezzo}


def consumi(per_prodotto: dict[str, list[dict]], numeri: dict | None = None, valuta: str = "") -> dict:
	"""This month's spend by kind, from Telnyx's usage report rows by product
	(``{"messaging": [{"cost": "1.20", "count": 30}]}``) and the numbers' fees
	(`dei_numeri`). A kind carries how many - calls connected, messages - the
	minutes of the calls, and what it cost."""
	voci, totale = [], Decimal(0)
	for chiave, nome, prodotti in VOCI:
		righe = [riga for prodotto in prodotti for riga in per_prodotto.get(prodotto) or []]
		prezzo = _somma(righe, "cost")
		totale += prezzo
		if chiave == "calls":
			quanti = int(_somma(righe, "connected"))
			minuti = int(_somma(righe, "billed_sec") / 60) if any("billed_sec" in r for r in righe) else None
		else:
			quanti = int(_somma(righe, "count"))
			minuti = None
		voci.append(
			{"key": chiave, "label": nome, "count": quanti, "minutes": minuti, "price": _centesimi(prezzo)}
		)
	if numeri is not None:
		totale += numeri["price"]
		voci.insert(
			2,
			{
				"key": "numbers",
				"label": "Numbers",
				"count": numeri["count"],
				"minutes": None,
				"price": _centesimi(numeri["price"]),
			},
		)
	return {"items": voci, "total": _centesimi(totale), "currency": (valuta or "").upper()}


def bilancio_in_parole(bilancio, disponibile=None) -> str:
	"""What the page says of the account's balance; '' while there is credit."""
	if bilancio in (None, ""):
		return ""
	resto = _numero(disponibile if disponibile not in (None, "") else bilancio)
	if resto <= 0:
		return "The Telnyx balance is used up: calls and SMS stop until it is topped up on Telnyx."
	return ""


def da_avvisare_della_spesa(totale, soglia, detto: str | None, mese: str) -> bool:
	"""Whether this month's spend (``totale``) is to be told: it reached the alert
	(``soglia``) and nobody was told this month (``detto``, the month told last)."""
	soglia = _numero(soglia)
	return bool(soglia > 0 and _numero(totale) >= soglia and (detto or "") != mese)


def cosa_fare_del_bilancio(bilancio, soglia, detto: bool) -> str:
	"""What the low balance alert does now: 'tell' (it went down to the alert and
	nobody was told), 'reset' (it was topped up past it since) or ''."""
	soglia = _numero(soglia)
	if soglia <= 0 or bilancio in (None, ""):
		return ""
	basso = _numero(bilancio) <= soglia
	if basso and not detto:
		return "tell"
	if not basso and detto:
		return "reset"
	return ""
