# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A fake Stripe for the tests: the dozen calls DottorCloud makes, in memory, and
the events it would send, signed as Stripe signs them."""

from __future__ import annotations

import itertools
import json
import time
from unittest.mock import patch

from crm.pagamenti import regole as R

SEGRETO = "whsec_finto_segreto"


class StripeFinto:
	def __init__(self):
		self.numeri = itertools.count(1)
		self.endpoint: dict[str, dict] = {}
		self.sessioni: dict[str, dict] = {}
		self.rimborsi: list[dict] = []
		self.clienti: dict[str, dict] = {}
		self.intenti: dict[str, dict] = {}
		self.staccate: list[str] = []
		#: the idempotency keys seen, and what each answered: the same key, once
		self.chiavi: dict[str, tuple[int, dict]] = {}
		#: why the next charges on a saved card are declined (``card_declined``…), in order
		self.rifiuti: list[str] = []
		self.chiamate: list[tuple[str, str]] = []
		#: (status, error) the next call answers with, once
		self.rifiuta: tuple[int, dict] | None = None

	def __enter__(self):
		self._patch = patch("crm.pagamenti.cliente._trasporto", self)
		self._patch.start()
		return self

	def __exit__(self, *args):
		self._patch.stop()

	def __call__(self, metodo, indirizzo, intestazioni, dati, attesa):
		percorso = indirizzo.split("/v1/", 1)[1].split("?")[0]
		self.chiamate.append((metodo, percorso))
		assert intestazioni["Authorization"].startswith("Bearer sk_test_")
		if self.rifiuta:
			risposta, self.rifiuta = self.rifiuta, None
			return risposta
		chiave = intestazioni.get("Idempotency-Key")
		if chiave and chiave in self.chiavi and parti_post(metodo, percorso):
			return self.chiavi[chiave]
		risposta = self._rispondi(metodo, percorso, dict(dati or []))
		if chiave and parti_post(metodo, percorso):
			self.chiavi[chiave] = risposta
		return risposta

	def _rispondi(self, metodo, percorso, modulo):
		parti = percorso.split("/")
		if percorso == "account":
			return 200, {
				"id": "acct_finto",
				"country": "IT",
				"default_currency": "eur",
				"business_profile": {"name": "Centro Prova"},
			}
		if parti[0] == "webhook_endpoints":
			if metodo == "POST" and len(parti) == 1:
				nome = f"we_{next(self.numeri)}"
				self.endpoint[nome] = {
					"id": nome,
					"url": modulo["url"],
					"secret": SEGRETO,
					"status": "enabled",
					"enabled_events": [v for k, v in modulo.items() if k.startswith("enabled_events")],
				}
				return 200, self.endpoint[nome]
			if parti[1] not in self.endpoint:
				return 404, {"error": {"type": "invalid_request_error", "code": "resource_missing"}}
			if metodo == "POST":
				self.endpoint[parti[1]]["enabled_events"] = [
					v for k, v in modulo.items() if k.startswith("enabled_events")
				]
			if metodo == "DELETE":
				return 200, {"id": parti[1], "deleted": True, **self.endpoint.pop(parti[1])}
			return 200, {k: v for k, v in self.endpoint[parti[1]].items() if k != "secret"}
		if parti[:2] == ["checkout", "sessions"]:
			if metodo == "POST" and len(parti) == 2:
				nome = f"cs_test_{next(self.numeri)}"
				self.sessioni[nome] = {
					"id": nome,
					"url": f"https://checkout.stripe.com/c/pay/{nome}",
					"status": "open",
					"payment_status": "unpaid",
					"amount_total": int(modulo["line_items[0][price_data][unit_amount]"]),
					"currency": modulo["line_items[0][price_data][currency]"],
					"client_reference_id": modulo["client_reference_id"],
					"metadata": {k[9:-1]: v for k, v in modulo.items() if k.startswith("metadata[")},
					"success_url": modulo["success_url"],
					"expires_at": int(modulo["expires_at"]),
					"customer": modulo.get("customer"),
					"setup_future_usage": modulo.get("payment_intent_data[setup_future_usage]"),
					"custom_text": modulo.get("custom_text[submit][message]"),
				}
				return 200, self.sessioni[nome]
			sessione = self.sessioni.get(parti[2])
			if not sessione:
				return 404, {"error": {"type": "invalid_request_error", "code": "resource_missing"}}
			if len(parti) == 4 and parti[3] == "expire":
				sessione["status"] = "expired"
			return 200, sessione
		if percorso == "refunds":
			self.rimborsi.append(modulo)
			return 200, {"id": f"re_{next(self.numeri)}", "status": "succeeded"}
		if percorso == "customers" and metodo == "POST":
			nome = f"cus_{next(self.numeri)}"
			self.clienti[nome] = {"id": nome, "email": modulo.get("email"), "name": modulo.get("name")}
			return 200, self.clienti[nome]
		if parti[0] == "payment_methods" and len(parti) == 3 and parti[2] == "detach":
			self.staccate.append(parti[1])
			return 200, {"id": parti[1], "customer": None}
		if parti[0] == "payment_intents":
			if metodo == "POST" and len(parti) == 1:
				nome = f"pi_{next(self.numeri)}"
				intento = {
					"id": nome,
					"amount": int(modulo["amount"]),
					"currency": modulo["currency"],
					"customer": modulo.get("customer"),
					"payment_method": modulo.get("payment_method"),
					"metadata": {k[9:-1]: v for k, v in modulo.items() if k.startswith("metadata[")},
					"off_session": modulo.get("off_session"),
				}
				if self.rifiuti:
					codice = self.rifiuti.pop(0)
					intento.update(
						{
							"status": "requires_payment_method",
							"last_payment_error": {"code": "card_declined", "decline_code": codice},
						}
					)
					self.intenti[nome] = intento
					return 402, {
						"error": {
							"type": "card_error",
							"code": "authentication_required"
							if codice == "authentication_required"
							else "card_declined",
							"decline_code": codice,
							"payment_intent": intento,
						}
					}
				intento.update({"status": "succeeded", "amount_received": intento["amount"]})
				self.intenti[nome] = intento
				return 200, intento
			intento = self.intenti.get(parti[1])
			if not intento:
				return 404, {"error": {"type": "invalid_request_error", "code": "resource_missing"}}
			# asked with ``expand[]=payment_method``: the card as Stripe describes it
			return 200, {**intento, "payment_method": self._metodo(intento.get("payment_method"))}
		return 404, {"error": {"type": "invalid_request_error"}}

	def _metodo(self, nome):
		if not nome:
			return None
		return {
			"id": nome,
			"type": "card",
			"card": {"brand": "visa", "last4": "4242", "exp_month": 12, "exp_year": 2034},
		}

	# -- what Stripe would send

	def paga(self, sessione: str) -> dict:
		"""The person paid: the session complete, and its event. Its payment intent
		holds the card, kept on the customer when the session asked it."""
		s = self.sessioni[sessione]
		s.update({"status": "complete", "payment_status": "paid", "payment_intent": f"pi_{sessione}"})
		self.intenti[f"pi_{sessione}"] = {
			"id": f"pi_{sessione}",
			"status": "succeeded",
			"amount": s["amount_total"],
			"amount_received": s["amount_total"],
			"currency": s["currency"],
			"customer": s.get("customer"),
			"payment_method": f"pm_{sessione}",
			"metadata": s["metadata"],
		}
		return evento("checkout.session.completed", s)

	def intento(self, nome: str, riuscito: bool = True) -> dict:
		"""The event of a charge on a saved card, as Stripe sends it after the answer."""
		i = self.intenti[nome]
		return evento("payment_intent.succeeded" if riuscito else "payment_intent.payment_failed", i)

	def scade(self, sessione: str) -> dict:
		s = self.sessioni[sessione]
		s["status"] = "expired"
		return evento("checkout.session.expired", s)

	def rimborsato(self, sessione: str, centesimi: int) -> dict:
		s = self.sessioni[sessione]
		return evento(
			"charge.refunded",
			{
				"id": f"ch_{sessione}",
				"payment_intent": s.get("payment_intent"),
				"amount_refunded": centesimi,
				"currency": s["currency"],
				"metadata": s["metadata"],
			},
		)


def parti_post(metodo: str, percorso: str) -> bool:
	"""A POST that makes something: the ones an idempotency key protects."""
	return metodo == "POST"


_eventi = itertools.count(1)


def evento(tipo: str, oggetto: dict) -> dict:
	return {
		"id": f"evt_finto_{next(_eventi)}_{int(time.time() * 1000)}",
		"type": tipo,
		"data": {"object": dict(oggetto)},
	}


def firmato(evento_: dict, segreto: str = SEGRETO, momento: int | None = None) -> tuple[bytes, str]:
	corpo = json.dumps(evento_).encode()
	return corpo, R.firma(corpo, segreto, momento or int(time.time()))
