# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Stripe's REST API through `requests`: form-encoded in, JSON out.

No SDK: a dozen calls, and one dependency less on the bench. The secret travels in
a variable named ``stripe_secret``, which a traceback hides, and an error is
logged with Stripe's status, type and code only - never the key, never the body.
A fake Stripe in the tests stands in for `_trasporto`.
"""

from __future__ import annotations

import frappe
import requests

from crm.pagamenti import regole as R

API = "https://api.stripe.com/v1/"
#: The API's version DottorCloud was written against: Stripe answers in it whatever
#: the account's default.
VERSIONE = "2024-06-20"
ATTESA = 20


def _api() -> str:
	"""Stripe's address; on a test bench, a fake Stripe's (``stripe_api`` in the site's
	config, never set on a centre's site)."""
	return frappe.conf.get("stripe_api") or API


class ErroreStripe(Exception):
	"""Stripe refused, or did not answer (``stato`` None). A card that was declined
	says why (``rifiuto``, Stripe's ``decline_code``)."""

	def __init__(
		self,
		stato: int | None,
		tipo: str | None = None,
		codice: str | None = None,
		rifiuto: str | None = None,
	):
		self.stato, self.tipo, self.codice, self.rifiuto = stato, tipo, codice, rifiuto
		super().__init__(f"Stripe {stato} {tipo or ''} {codice or ''} {rifiuto or ''}".strip())

	@property
	def della_carta(self) -> bool:
		"""The card was declined: a try that happened, not Stripe away."""
		return self.tipo == "card_error" or self.stato == 402

	def in_parole(self) -> str:
		from frappe import _

		return _(R.errore_in_parole(self.stato, self.tipo, self.codice))


def _trasporto(metodo: str, indirizzo: str, intestazioni: dict, dati: list | None, attesa: int):
	"""One HTTP request: (status, JSON). Replaced by the tests' fake Stripe."""
	risposta = requests.request(metodo, indirizzo, headers=intestazioni, data=dati, timeout=attesa)
	try:
		corpo = risposta.json()
	except ValueError:
		corpo = {}
	return risposta.status_code, corpo


def chiama(
	metodo: str,
	percorso: str,
	stripe_secret: str,
	dati: dict | None = None,
	idempotenza: str | None = None,
) -> dict:
	"""Ask Stripe; the answer's JSON, or `ErroreStripe`."""
	intestazioni = {"Authorization": f"Bearer {stripe_secret}", "Stripe-Version": VERSIONE}
	if idempotenza:
		# the same request asked twice (an answer lost) makes one thing on Stripe
		intestazioni["Idempotency-Key"] = idempotenza
	modulo = R.modulo(dati) if dati else None
	try:
		if metodo == "GET" and modulo:
			from urllib.parse import urlencode

			percorso = f"{percorso}?{urlencode(modulo)}"
			modulo = None
		stato, corpo = _trasporto(metodo, _api() + percorso, intestazioni, modulo, ATTESA)
	except requests.RequestException as errore:
		frappe.log_error(title="Stripe: no answer", message=type(errore).__name__)
		raise ErroreStripe(None) from None
	if stato >= 400:
		problema = (corpo or {}).get("error") or {}
		errore = ErroreStripe(stato, problema.get("type"), problema.get("code"), problema.get("decline_code"))
		frappe.log_error(title="Stripe refused", message=f"{metodo} {percorso.split('?')[0]}: {errore}")
		raise errore
	return corpo or {}
