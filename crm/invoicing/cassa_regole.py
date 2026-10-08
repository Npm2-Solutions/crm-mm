# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The desk's cash closing without a site: what a day collected, by how it was paid
and by who issued it, the credit notes that gave money back, and the cash the
drawer should hold.

- **Collected** is an invoice's `collected_on` that day (`incassi`), at what the
  client pays (the document less the withholding they pay themselves).
- **Given back** is a credit note issued that day: it is never collected, and its
  money leaves by the way it names.
- **The drawer** holds the cash collected less the cash given back; what was
  counted against it is the difference, to the cent.
"""

from __future__ import annotations

from collections.abc import Iterable

#: The payment method of cash (FatturaPA's MP01): what the drawer holds.
CONTANTI = "MP01"


def centesimi(valore) -> float:
	"""An amount to the cent, never a float's tail (0.1 + 0.2)."""
	try:
		# a zero below zero (-0.0) reads as zero
		return round(float(valore or 0), 2) + 0.0
	except (TypeError, ValueError):
		return 0.0


def riepilogo(incassate: Iterable[dict], restituite: Iterable[dict] = ()) -> dict:
	"""The day: rows of ``payment_method``, ``amount`` and ``issued_by``, for the
	invoices collected and the credit notes issued."""
	metodi: dict[str, dict] = {}
	persone: dict[str, dict] = {}

	def metodo(codice: str) -> dict:
		return metodi.setdefault(
			codice, {"method": codice, "collected": 0.0, "refunded": 0.0, "count": 0, "notes": 0}
		)

	for riga in incassate:
		voce = metodo(riga.get("payment_method") or "")
		voce["collected"] += centesimi(riga.get("amount"))
		voce["count"] += 1
		chi = persone.setdefault(
			riga.get("issued_by") or "", {"user": riga.get("issued_by") or "", "total": 0.0, "count": 0}
		)
		chi["total"] += centesimi(riga.get("amount"))
		chi["count"] += 1
	for riga in restituite:
		voce = metodo(riga.get("payment_method") or "")
		voce["refunded"] += centesimi(riga.get("amount"))
		voce["notes"] += 1
	for voce in metodi.values():
		voce["collected"] = centesimi(voce["collected"])
		voce["refunded"] = centesimi(voce["refunded"])
		voce["net"] = centesimi(voce["collected"] - voce["refunded"])
	for chi in persone.values():
		chi["total"] = centesimi(chi["total"])
	incassato = centesimi(sum(voce["collected"] for voce in metodi.values()))
	restituito = centesimi(sum(voce["refunded"] for voce in metodi.values()))
	contanti = metodi.get(CONTANTI)
	return {
		# the way most money came by first; cash where it falls
		"methods": sorted(metodi.values(), key=lambda voce: (-voce["net"], voce["method"])),
		"by_user": sorted(persone.values(), key=lambda chi: (-chi["total"], chi["user"])),
		"collected": incassato,
		"refunded": restituito,
		"total": centesimi(incassato - restituito),
		"count": sum(voce["count"] for voce in metodi.values()),
		"expected_cash": contanti["net"] if contanti else 0.0,
	}


def differenza(contati, attesi) -> float:
	"""What the drawer holds against what it should: above zero more, below less."""
	return centesimi(centesimi(contati) - centesimi(attesi))
