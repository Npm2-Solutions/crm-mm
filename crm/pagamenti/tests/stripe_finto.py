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
		modulo = dict(dati or [])
		parti = percorso.split("/")
		if percorso == "account":
			return 200, {
				"id": "acct_finto",
				"country": "IT",
				"default_currency": "eur",
				"business_profile": {"name": "Centro Prova"},
			}
		if parti[0] == "webhook_endpoints":
			if metodo == "POST":
				nome = f"we_{next(self.numeri)}"
				self.endpoint[nome] = {
					"id": nome,
					"url": modulo["url"],
					"secret": SEGRETO,
					"status": "enabled",
					"events": [v for k, v in modulo.items() if k.startswith("enabled_events")],
				}
				return 200, self.endpoint[nome]
			if parti[1] not in self.endpoint:
				return 404, {"error": {"type": "invalid_request_error", "code": "resource_missing"}}
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
		return 404, {"error": {"type": "invalid_request_error"}}

	# -- what Stripe would send

	def paga(self, sessione: str) -> dict:
		"""The person paid: the session complete, and its event."""
		s = self.sessioni[sessione]
		s.update({"status": "complete", "payment_status": "paid", "payment_intent": f"pi_{sessione}"})
		return evento("checkout.session.completed", s)

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
