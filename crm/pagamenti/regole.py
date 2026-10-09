# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Online payments without a site: what Stripe's words mean to DottorCloud.

- **The key** the centre pastes says its mode by its prefix: ``sk_test_`` and
  ``rk_test_`` are Stripe's test mode, ``sk_live_`` and ``rk_live_`` real money.
  A publishable key (``pk_``) cannot act on the account.
- **The signature** of a webhook (``Stripe-Signature: t=…,v1=…``) is an
  HMAC-SHA256 of ``"{t}.{body}"`` with the endpoint's secret, in hex; one ``v1``
  of the header must match, and ``t`` be within the tolerance of now (Stripe's
  default is five minutes), or an old message could be played again.
- **Amounts** travel in the currency's smallest unit (cents for the euro), to the
  cent and rounded half up, never a float's tail.
- **An event** becomes one thing to do: paid, expired, refunded, failed.
- **The deposit** a service asks online, and whether a cancellation gives it back.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from urllib.parse import quote

#: Stripe's tolerance on a webhook's timestamp, in seconds.
TOLLERANZA = 300
#: The events DottorCloud asks of the endpoint it makes on the centre's account.
EVENTI = (
	"checkout.session.completed",
	"checkout.session.expired",
	"charge.refunded",
	"payment_intent.succeeded",
	"payment_intent.payment_failed",
)
#: The metadata a charge on a saved card carries, which its ``payment_intent``
#: events are read by: a Checkout's are read from its session instead.
ADDEBITO = "off_session"
#: Currencies without decimals in Stripe's API (a few the centre could count in).
SENZA_DECIMALI = frozenset(
	{
		"bif",
		"clp",
		"djf",
		"gnf",
		"jpy",
		"kmf",
		"krw",
		"mga",
		"pyg",
		"rwf",
		"ugx",
		"vnd",
		"vuv",
		"xaf",
		"xof",
		"xpf",
	}
)

#: How long a Checkout link holds: a slot of the booking page for half an hour
#: (Stripe's least), an invoice's link a day (Stripe's most).
MINUTI_ACCONTO = 30
ORE_FATTURA = 24

#: The way the payment of a service is asked online (`CRM Service.online_payment`).
ACCONTO = "Deposit"
TUTTO = "Full price"

TEST = "test"
LIVE = "live"


# ------------------------------------------------------------------ the key


def pulita(chiave: str | None) -> str:
	return "".join((chiave or "").split())


def modalita(chiave: str | None) -> str | None:
	"""``test`` or ``live`` from a secret or restricted key; None for anything else."""
	chiave = pulita(chiave)
	for prefisso in ("sk_", "rk_"):
		if chiave.startswith(prefisso + "test_"):
			return TEST
		if chiave.startswith(prefisso + "live_"):
			return LIVE
	return None


def cosa_manca(chiave: str | None) -> str | None:
	"""What is wrong with what was pasted, before Stripe is asked."""
	chiave = pulita(chiave)
	if not chiave:
		return "Paste the secret key of your Stripe account."
	if chiave.startswith("pk_"):
		return "This is the publishable key: paste the secret key (sk_…) or a restricted key (rk_…)."
	if not modalita(chiave) or len(chiave) < 20:
		return "This is not a Stripe secret key: it starts with sk_ or rk_."
	return None


def mascherata(chiave: str | None) -> str:
	"""A key as the page may show it: its prefix and last four characters."""
	chiave = pulita(chiave)
	if len(chiave) < 12:
		return ""
	prefisso = chiave[: chiave.index("_", 3) + 1] if chiave.count("_") >= 2 else chiave[:3]
	return f"{prefisso}…{chiave[-4:]}"


# ------------------------------------------------------------------ the signature


def firma(corpo: bytes, segreto: str, momento: int) -> str:
	"""The header Stripe writes for ``corpo`` at ``momento`` (for the tests, and a
	fake Stripe)."""
	firmato = hmac.new(segreto.encode(), f"{momento}.".encode() + corpo, hashlib.sha256).hexdigest()
	return f"t={momento},v1={firmato}"


def perche_rifiutata(
	corpo: bytes, intestazione: str | None, segreto: str, adesso: int, tolleranza: int = TOLLERANZA
) -> str | None:
	"""Why a webhook's signature does not hold, or None when it does."""
	if not segreto:
		return "no secret"
	if not intestazione:
		return "no signature"
	momento, firme = None, []
	for parte in intestazione.split(","):
		chiave, _, valore = parte.strip().partition("=")
		if chiave == "t":
			try:
				momento = int(valore)
			except ValueError:
				return "bad timestamp"
		elif chiave == "v1" and valore:
			firme.append(valore)
	if momento is None or not firme:
		return "no signature"
	attesa = hmac.new(segreto.encode(), f"{momento}.".encode() + corpo, hashlib.sha256).hexdigest()
	if not any(hmac.compare_digest(attesa, firma_data) for firma_data in firme):
		return "signature mismatch"
	if abs(adesso - momento) > tolleranza:
		return "too old"
	return None


# ------------------------------------------------------------------ amounts


def _decimale(importo) -> Decimal:
	try:
		return Decimal(str(importo or 0))
	except (InvalidOperation, ValueError):
		return Decimal(0)


def in_centesimi(importo, valuta: str = "eur") -> int:
	"""An amount in the currency's smallest unit, rounded half up."""
	esponente = Decimal(1) if valuta.lower() in SENZA_DECIMALI else Decimal("0.01")
	arrotondato = _decimale(importo).quantize(esponente, rounding=ROUND_HALF_UP)
	return int(arrotondato if esponente == 1 else arrotondato * 100)


def da_centesimi(centesimi, valuta: str = "eur") -> float:
	"""Stripe's integer back to an amount, to the cent."""
	valore = Decimal(int(centesimi or 0))
	if valuta.lower() not in SENZA_DECIMALI:
		valore = valore / 100
	return float(valore.quantize(Decimal("0.01")))


def acconto(modo: str | None, importo_acconto, prezzo) -> float:
	"""What a service asks online at booking: its deposit (never over the price), the
	whole price, or nothing."""
	prezzo = _decimale(prezzo)
	if modo == TUTTO:
		somma = prezzo
	elif modo == ACCONTO:
		somma = _decimale(importo_acconto)
		if prezzo > 0:
			somma = min(somma, prezzo)
	else:
		return 0.0
	return float(max(somma, Decimal(0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


# ------------------------------------------------------------------ the form Stripe reads


def modulo(dati: dict, prefisso: str = "") -> list[tuple[str, str]]:
	"""A nested dict as Stripe's form encoding: ``line_items[0][price_data][currency]``."""
	righe: list[tuple[str, str]] = []
	for chiave, valore in dati.items():
		nome = f"{prefisso}[{chiave}]" if prefisso else str(chiave)
		if valore is None:
			continue
		if isinstance(valore, dict):
			righe.extend(modulo(valore, nome))
		elif isinstance(valore, list | tuple):
			for i, voce in enumerate(valore):
				if isinstance(voce, dict):
					righe.extend(modulo(voce, f"{nome}[{i}]"))
				else:
					righe.append((f"{nome}[{i}]", _testo(voce)))
		else:
			righe.append((nome, _testo(valore)))
	return righe


def _testo(valore) -> str:
	if isinstance(valore, bool):
		return "true" if valore else "false"
	return str(valore)


def percorso(*parti: str) -> str:
	"""A path of Stripe's API with each id quoted."""
	return "/".join(quote(str(parte), safe="") for parte in parti)


# ------------------------------------------------------------------ what an event means


@dataclass(frozen=True)
class Significato:
	#: ``pagato``, ``scaduto``, ``rimborsato``, ``non_riuscito``
	cosa: str
	sessione: str | None = None
	intento: str | None = None
	importo: float = 0.0
	valuta: str = "eur"
	#: the payment of DottorCloud's it names (`client_reference_id`, metadata)
	pagamento: str | None = None
	sito: str | None = None
	errore: str | None = None
	#: Stripe's reason of a charge that did not go through (`decline_code`, else `code`)
	codice: str | None = None


PAGATO, SCADUTO, RIMBORSATO, NON_RIUSCITO = "pagato", "scaduto", "rimborsato", "non_riuscito"


def significato(evento: dict) -> Significato | None:
	"""The one thing an event of Stripe's asks DottorCloud to do, or None."""
	tipo = evento.get("type")
	oggetto = (evento.get("data") or {}).get("object") or {}
	metadati = oggetto.get("metadata") or {}
	valuta = (oggetto.get("currency") or "eur").lower()
	if tipo in ("checkout.session.completed", "checkout.session.async_payment_succeeded"):
		# a session completed with a delayed method (a SEPA debit) is not paid yet
		if oggetto.get("payment_status") not in ("paid", "no_payment_required"):
			return None
		return Significato(
			PAGATO,
			sessione=oggetto.get("id"),
			intento=oggetto.get("payment_intent"),
			importo=da_centesimi(oggetto.get("amount_total"), valuta),
			valuta=valuta,
			pagamento=oggetto.get("client_reference_id") or metadati.get("payment"),
			sito=metadati.get("site"),
		)
	if tipo == "checkout.session.expired":
		return Significato(
			SCADUTO,
			sessione=oggetto.get("id"),
			pagamento=oggetto.get("client_reference_id") or metadati.get("payment"),
			sito=metadati.get("site"),
		)
	if tipo == "charge.refunded":
		return Significato(
			RIMBORSATO,
			intento=oggetto.get("payment_intent"),
			importo=da_centesimi(oggetto.get("amount_refunded"), valuta),
			valuta=valuta,
			pagamento=metadati.get("payment"),
			sito=metadati.get("site"),
		)
	if tipo == "payment_intent.succeeded":
		# a Checkout's payment is told by its session: only a charge on a saved card here
		if metadati.get("charge") != ADDEBITO:
			return None
		return Significato(
			PAGATO,
			intento=oggetto.get("id"),
			importo=da_centesimi(oggetto.get("amount_received") or oggetto.get("amount"), valuta),
			valuta=valuta,
			pagamento=metadati.get("payment"),
			sito=metadati.get("site"),
		)
	if tipo == "payment_intent.payment_failed":
		problema = oggetto.get("last_payment_error") or {}
		return Significato(
			NON_RIUSCITO,
			intento=oggetto.get("id"),
			pagamento=metadati.get("payment"),
			sito=metadati.get("site"),
			errore=problema.get("message"),
			codice=problema.get("decline_code") or problema.get("code"),
		)
	return None


# ------------------------------------------------------------------ cancelling a deposit


def rimborsabile(inizio: datetime, disdetto: datetime, rimborsa: bool, ore: int | None) -> bool:
	"""Whether a cancellation gives the deposit back: the centre wants it, and it came
	at least ``ore`` hours before the appointment (no hours: any time before it)."""
	if not rimborsa:
		return False
	return disdetto <= inizio - timedelta(hours=max(int(ore or 0), 0))


def scaduto(scade: datetime | None, adesso: datetime, margine_minuti: int = 5) -> bool:
	"""Whether a Checkout link waiting for payment is past its time, with a margin for
	Stripe's own event to arrive first."""
	return bool(scade) and adesso >= scade + timedelta(minutes=margine_minuti)


# ------------------------------------------------------------------ Stripe's refusals in words


def errore_in_parole(stato: int | None, tipo: str | None = None, codice: str | None = None) -> str:
	"""What Stripe's answer means to the centre, in a sentence of the catalogue."""
	if stato is None:
		return "Stripe did not answer: try again in a few minutes."
	if stato == 401:
		return (
			"Stripe did not accept the key: copy it again from the Stripe dashboard, Developers > API keys."
		)
	if stato == 403:
		return (
			"The restricted key may not do this: give it Checkout Sessions, Webhook Endpoints and Refunds "
			"(write) and Charges (read), or use the secret key."
		)
	if stato == 404:
		return "Stripe does not have it any more."
	if stato == 429:
		return "Stripe asks to slow down: try again in a minute."
	if codice == "url_invalid" or (tipo == "invalid_request_error" and codice == "parameter_invalid_string"):
		return "Stripe refused this site's address: it must be public and on https."
	if stato >= 500:
		return "Stripe did not answer: try again in a few minutes."
	return "Stripe refused the request."
