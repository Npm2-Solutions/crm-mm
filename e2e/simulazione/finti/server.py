#!/usr/bin/env python3
# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The world outside the test bench, as the simulation of a week needs it: Stripe.

Stdlib only, started by the suite (or by hand) before the centre is prepared:

    python3 e2e/simulazione/finti/server.py --porta 8791 --stato e2e/simulazione/rapporto/finti.json

- **Stripe's API** at ``/v1/``: the calls DottorCloud makes, answered by the tests'
  own fake (`crm.pagamenti.tests.stripe_finto`) - Checkout sessions, payment
  intents on a saved card, customers, payment methods, refunds, webhook endpoints.
- **Stripe's hosted page** at ``/checkout/<session>``, where the person's own browser
  pays, as on Stripe: a card number decides how it goes, as Stripe's test cards do -
  4242 4242 4242 4242 pays; 4000 0000 0000 9995 is declined (insufficient funds);
  4000 0025 0000 3155 asks to confirm the payment first; 4000 0000 0000 0341 pays
  now, and the charges on it later are declined; 4000 0027 6000 3184 pays after the
  confirmation, and a charge on it later asks for it again.
- **The webhooks**, signed with the endpoint's secret and sent to the site as Stripe
  sends them: a session paid or expired, a charge on a saved card, a refund. Their
  time is the bench's (``/_orologio``): the site checks it against its own moved clock.
- **Doors for the suite**: ``POST /_orologio`` (the bench's gap in seconds), ``POST
  /_rifiuti`` (the next charges declined, by decline code), ``POST /_scade/<session>``,
  ``GET /_stato``.

Its state is kept in a JSON file, so a restarted fake still knows the endpoint the
centre made on it.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

RADICE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RADICE))

from crm.pagamenti.tests import stripe_finto as finto

#: The test cards, as Stripe's documentation lists them, and what each does here.
PAGA = "4242424242424242"
RIFIUTATA = "4000000000009995"
CONFERMA = "4000002500003155"
POI_RIFIUTATA = "4000000000000341"
SEMPRE_CONFERMA = "4000002760003184"
DA_CONFERMARE = {CONFERMA, SEMPRE_CONFERMA}

_senza_proxy = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class Stripe(finto.StripeFinto):
	"""The tests' fake, reachable over HTTP, with a hosted page and webhooks sent."""

	def __init__(self, base: str, stato: Path | None):
		super().__init__()
		self.base = base.rstrip("/")
		self.file = stato
		#: payment method -> the card number it was saved from
		self.carte: dict[str, str] = {}
		#: the bench's clock: real time plus this many seconds
		self.scarto = 0.0
		#: what was sent to the site: (event type, object id, HTTP answer)
		self.inviati: list[list] = []
		self.blocco = threading.RLock()
		self._carica()

	# -- state kept on disk

	CAMPI = (
		"endpoint",
		"sessioni",
		"clienti",
		"intenti",
		"staccate",
		"rimborsi",
		"carte",
		"scarto",
		"inviati",
	)

	def _carica(self) -> None:
		if self.file and self.file.exists():
			dati = json.loads(self.file.read_text())
			for campo in self.CAMPI:
				if campo in dati:
					setattr(self, campo, dati[campo])
			self.numeri = iter(range(dati.get("numero", 1), 10**9))
			self.chiavi = {k: tuple(v) for k, v in (dati.get("chiavi") or {}).items()}

	def salva(self) -> None:
		if not self.file:
			return
		dati = {campo: getattr(self, campo) for campo in self.CAMPI}
		dati["chiavi"] = self.chiavi
		dati["numero"] = next(self.numeri)
		self.file.parent.mkdir(parents=True, exist_ok=True)
		temporaneo = self.file.with_suffix(".tmp")
		temporaneo.write_text(json.dumps(dati, indent=1))
		os.replace(temporaneo, self.file)

	def adesso(self) -> int:
		return int(time.time() + self.scarto)

	# -- the API

	def _rispondi(self, metodo, percorso, modulo):
		parti = percorso.split("/")
		if parti[0] == "payment_intents" and metodo == "POST" and len(parti) == 1:
			carta = self.carte.get(modulo.get("payment_method") or "", PAGA)
			if carta == POI_RIFIUTATA:
				self.rifiuti.insert(0, "insufficient_funds")
			elif carta == SEMPRE_CONFERMA:
				self.rifiuti.insert(0, "authentication_required")
			stato, corpo = super()._rispondi(metodo, percorso, modulo)
			intento = corpo if stato == 200 else (corpo.get("error") or {}).get("payment_intent")
			if intento:
				riuscito = intento.get("status") == "succeeded"
				self._dopo(self.intento(intento["id"], riuscito))
			return stato, corpo
		stato, corpo = super()._rispondi(metodo, percorso, modulo)
		if parti[:2] == ["checkout", "sessions"] and metodo == "POST" and len(parti) == 2 and stato == 200:
			corpo["url"] = f"{self.base}/checkout/{corpo['id']}"
			corpo["cancel_url"] = modulo.get("cancel_url")
			corpo["descrizione"] = modulo.get("line_items[0][price_data][product_data][name]") or ""
		if percorso == "refunds" and stato == 200:
			sessione = self._sessione_dell_intento(modulo.get("payment_intent"))
			if sessione:
				centesimi = int(modulo.get("amount") or self.sessioni[sessione]["amount_total"])
				self._dopo(self.rimborsato(sessione, centesimi))
		return stato, corpo

	def _sessione_dell_intento(self, intento: str | None) -> str | None:
		for nome, sessione in self.sessioni.items():
			if sessione.get("payment_intent") == intento:
				return nome
		return None

	def _metodo(self, nome):
		# the card as the person typed it on the page: its last four digits
		metodo = super()._metodo(nome)
		if metodo:
			metodo["card"]["last4"] = (self.carte.get(nome) or PAGA)[-4:]
		return metodo

	# -- the hosted page

	def paga_con(self, sessione: str, carta: str) -> dict:
		evento = self.paga(sessione)
		self.carte[f"pm_{sessione}"] = carta
		return evento

	# -- the webhooks

	def invia(self, evento: dict) -> int:
		"""The event to every endpoint, signed at the bench's hour."""
		corpo, firma = finto.firmato(evento, momento=self.adesso())
		esito = 0
		for endpoint in list(self.endpoint.values()):
			richiesta = urllib.request.Request(
				endpoint["url"],
				data=corpo,
				method="POST",
				headers={"Content-Type": "application/json", "Stripe-Signature": firma},
			)
			try:
				with _senza_proxy.open(richiesta, timeout=60) as risposta:
					esito = risposta.status
			except urllib.error.HTTPError as errore:
				esito = errore.code
			except OSError:
				esito = -1
			oggetto = evento["data"]["object"].get("id")
			with self.blocco:
				self.inviati.append([evento["type"], oggetto, esito, self.adesso()])
		with self.blocco:
			self.salva()
		return esito

	def _dopo(self, evento: dict) -> None:
		"""Sent a moment after the answer, as Stripe does."""
		threading.Timer(0.8, self.invia, args=(evento,)).start()


def _pagina(titolo: str, corpo: str) -> bytes:
	return f"""<!doctype html><html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titolo)}</title>
<style>
:root {{ color-scheme: light dark; }}
body {{ font-family: system-ui, sans-serif; margin: 0; background: #f6f9fc; color: #1a1f36; }}
@media (prefers-color-scheme: dark) {{ body {{ background: #0f1320; color: #e6e9f2; }} .scheda {{ background: #1a2033; }} }}
.scheda {{ max-width: 420px; margin: 24px auto; background: #fff; border-radius: 12px; padding: 20px 16px;
  box-shadow: 0 2px 10px rgba(0,0,0,.08); }}
h1 {{ font-size: 18px; margin: 0 0 4px; }} .importo {{ font-size: 28px; font-weight: 600; margin: 8px 0 16px; }}
label {{ display: block; font-size: 14px; margin: 12px 0 4px; }}
input {{ width: 100%; box-sizing: border-box; font-size: 16px; height: 44px; padding: 0 12px;
  border: 1px solid #c7cdd8; border-radius: 8px; }}
.riga {{ display: flex; gap: 8px; }} .riga > div {{ flex: 1; min-width: 0; }}
button {{ width: 100%; height: 48px; margin-top: 20px; font-size: 16px; font-weight: 600; color: #fff;
  background: #635bff; border: 0; border-radius: 8px; }}
.secondario {{ background: transparent; color: inherit; border: 1px solid #c7cdd8; }}
.errore {{ color: #b3261e; margin-top: 12px; }} .nota {{ font-size: 13px; opacity: .8; margin-top: 12px; }}
</style></head><body><main class="scheda">{corpo}</main></body></html>""".encode()


def _euro(centesimi: int) -> str:
	euro, cent = divmod(int(centesimi), 100)
	return f"{euro:,}".replace(",", ".") + f",{cent:02d} €"


class Gestore(BaseHTTPRequestHandler):
	stripe: Stripe

	def _rispondi(self, stato: int, corpo: bytes, tipo: str = "application/json", **intestazioni):
		self.send_response(stato)
		self.send_header("Content-Type", tipo)
		self.send_header("Content-Length", str(len(corpo)))
		for chiave, valore in intestazioni.items():
			self.send_header(chiave.replace("_", "-"), valore)
		self.end_headers()
		self.wfile.write(corpo)

	def _json(self, dati, stato: int = 200):
		self._rispondi(stato, json.dumps(dati).encode())

	def _corpo(self) -> str:
		lunghezza = int(self.headers.get("Content-Length") or 0)
		return self.rfile.read(lunghezza).decode() if lunghezza else ""

	def _vai(self, dove: str):
		self._rispondi(303, b"", "text/plain", Location=dove)

	def _api(self, metodo: str):
		grezzo = self._corpo()
		dati = parse_qsl(grezzo, keep_blank_values=True)
		indirizzo = "http://stripe/v1/" + self.path.split("/v1/", 1)[1]
		with self.stripe.blocco:
			try:
				stato, corpo = self.stripe(
					metodo,
					indirizzo,
					{
						"Authorization": self.headers.get("Authorization", ""),
						"Idempotency-Key": self.headers.get("Idempotency-Key"),
					},
					dati,
					10,
				)
			except AssertionError:
				stato, corpo = 401, {"error": {"type": "invalid_request_error", "message": "Invalid API Key"}}
			self.stripe.salva()
		self._json(corpo, stato)

	# -- the hosted page

	def _checkout(self, sessione: str, errore: str = "", conferma: bool = False, carta: str = ""):
		s = self.stripe.sessioni.get(sessione)
		if not s:
			return self._rispondi(404, _pagina("Pagamento", "<h1>Pagamento non trovato</h1>"), "text/html")
		if s["status"] == "complete":
			return self._vai(s["success_url"])
		if s["status"] == "expired" or s["expires_at"] < self.stripe.adesso():
			return self._rispondi(
				410, _pagina("Pagamento", "<h1>Questo link di pagamento è scaduto</h1>"), "text/html"
			)
		descrizione = html.escape(s.get("descrizione") or "")
		testo = html.escape(s.get("custom_text") or "")
		if conferma:
			corpo = f"""<h1>Conferma il pagamento</h1>
<p>La tua banca chiede di confermare il pagamento di <strong>{_euro(s["amount_total"])}</strong>.</p>
<form method="post" action="/checkout/{sessione}/autentica">
<input type="hidden" name="carta" value="{html.escape(carta)}">
<button type="submit" name="esito" value="ok" data-azione="conferma">Conferma</button>
<button type="submit" name="esito" value="no" class="secondario" data-azione="annulla">Non confermare</button>
</form>"""
			return self._rispondi(200, _pagina("Conferma il pagamento", corpo), "text/html")
		corpo = f"""<h1>Pagamento sicuro</h1>{f"<p>{descrizione}</p>" if descrizione else ""}
<div class="importo" data-importo="{s["amount_total"]}">{_euro(s["amount_total"])}</div>
<form method="post" action="/checkout/{sessione}/paga">
<label for="email">Email</label><input id="email" name="email" type="email" autocomplete="email" value="">
<label for="carta">Numero della carta</label>
<input id="carta" name="carta" inputmode="numeric" autocomplete="cc-number" placeholder="1234 1234 1234 1234">
<div class="riga"><div><label for="scadenza">Scadenza</label>
<input id="scadenza" name="scadenza" inputmode="numeric" placeholder="MM / AA" value="12 / 34"></div>
<div><label for="cvc">CVC</label><input id="cvc" name="cvc" inputmode="numeric" placeholder="CVC" value="123"></div></div>
<label for="titolare">Titolare della carta</label><input id="titolare" name="titolare" autocomplete="cc-name">
{f'<p class="nota" data-mandato>{testo}</p>' if testo else ""}
{f'<p class="errore" role="alert">{html.escape(errore)}</p>' if errore else ""}
<button type="submit" data-azione="paga">Paga {_euro(s["amount_total"])}</button>
</form>
<p class="nota">Pagamento di prova: nessun addebito reale.</p>"""
		self._rispondi(200, _pagina("Pagamento sicuro", corpo), "text/html")

	def _paga(self, sessione: str):
		modulo = dict(parse_qsl(self._corpo()))
		carta = "".join(c for c in modulo.get("carta", "") if c.isdigit())
		s = self.stripe.sessioni.get(sessione)
		if not s or s["status"] != "open":
			return self._checkout(sessione)
		if len(carta) < 15:
			return self._checkout(sessione, "Il numero della carta non è completo.")
		if carta == RIFIUTATA:
			return self._checkout(
				sessione, "La carta è stata rifiutata: fondi insufficienti. Prova con un'altra carta."
			)
		if carta in DA_CONFERMARE:
			return self._checkout(sessione, conferma=True, carta=carta)
		self._completa(sessione, carta)

	def _autentica(self, sessione: str):
		modulo = dict(parse_qsl(self._corpo()))
		if modulo.get("esito") != "ok":
			return self._checkout(sessione, "Il pagamento non è stato confermato.")
		self._completa(sessione, modulo.get("carta") or CONFERMA)

	def _completa(self, sessione: str, carta: str):
		with self.stripe.blocco:
			evento = self.stripe.paga_con(sessione, carta)
			self.stripe.salva()
		# delivered before the person comes back, as Stripe mostly manages
		self.stripe.invia(evento)
		self._vai(self.stripe.sessioni[sessione]["success_url"])

	# -- the suite's doors

	def _porta(self, metodo: str):
		parti = urlparse(self.path).path.strip("/").split("/")
		corpo = self._corpo() if metodo == "POST" else ""
		if parti[0] == "_orologio" and metodo == "POST":
			self.stripe.scarto = float(corpo or 0)
			self.stripe.salva()
			return self._json({"scarto": self.stripe.scarto, "adesso": self.stripe.adesso()})
		if parti[0] == "_rifiuti" and metodo == "POST":
			self.stripe.rifiuti = [x for x in corpo.split(",") if x]
			return self._json({"rifiuti": self.stripe.rifiuti})
		if parti[0] == "_scade" and len(parti) == 2:
			s = self.stripe.sessioni.get(parti[1])
			if not s:
				return self._json({"error": "unknown session"}, 404)
			return self._json({"answer": self.stripe.invia(self.stripe.scade(parti[1]))})
		if parti[0] == "_stato":
			s = self.stripe
			return self._json(
				{
					"endpoint": list(s.endpoint.values()),
					"sessioni": s.sessioni,
					"intenti": s.intenti,
					"rimborsi": s.rimborsi,
					"carte": s.carte,
					"staccate": s.staccate,
					"inviati": s.inviati,
					"chiamate": s.chiamate[-50:],
					"scarto": s.scarto,
				}
			)
		return self._json({"error": "unknown door"}, 404)

	def do_GET(self):
		percorso = urlparse(self.path).path
		if percorso.startswith("/v1/"):
			return self._api("GET")
		if percorso.startswith("/checkout/"):
			parti = percorso.strip("/").split("/")
			if len(parti) == 3 and parti[2] == "annulla":
				s = self.stripe.sessioni.get(parti[1]) or {}
				return self._vai(s.get("cancel_url") or "/")
			return self._checkout(parti[1])
		if percorso.startswith("/_"):
			return self._porta("GET")
		if percorso == "/":
			return self._json({"ok": True})
		self._json({"error": "not found"}, 404)

	def do_POST(self):
		percorso = urlparse(self.path).path
		if percorso.startswith("/v1/"):
			return self._api("POST")
		if percorso.startswith("/checkout/"):
			parti = percorso.strip("/").split("/")
			if len(parti) == 3 and parti[2] == "paga":
				return self._paga(parti[1])
			if len(parti) == 3 and parti[2] == "autentica":
				return self._autentica(parti[1])
		if percorso.startswith("/_"):
			return self._porta("POST")
		self._json({"error": "not found"}, 404)

	def do_DELETE(self):
		if self.path.startswith("/v1/"):
			return self._api("DELETE")
		self._json({"error": "not found"}, 404)

	def log_message(self, formato, *argomenti):
		if os.environ.get("FINTI_LOG"):
			super().log_message(formato, *argomenti)


def main() -> None:
	parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
	parser.add_argument("--porta", type=int, default=8791)
	parser.add_argument("--host", default="127.0.0.1")
	parser.add_argument("--stato", default=str(RADICE / "e2e/simulazione/rapporto/finti.json"))
	parser.add_argument("--base", help="the address the persons' browsers reach the hosted page at")
	argomenti = parser.parse_args()
	base = argomenti.base or f"http://{argomenti.host}:{argomenti.porta}"
	Gestore.stripe = Stripe(base, Path(argomenti.stato) if argomenti.stato else None)
	server = ThreadingHTTPServer((argomenti.host, argomenti.porta), Gestore)
	print(f"finti: Stripe on {base}/v1/, the hosted page on {base}/checkout/", flush=True)
	server.serve_forever()


if __name__ == "__main__":
	main()
