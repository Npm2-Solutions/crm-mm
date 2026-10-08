# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Where Stripe tells DottorCloud what happened to a payment.

The endpoint made on the centre's account (`collegamento`) signs every message
with its secret: the signature is checked on the raw body before anything is read
(`regole.perche_rifiutata`), a wrong or old one is a 400. Each event is kept in
`CRM Stripe Event` before it is applied, by Stripe's own id: Stripe sends an event
again until it hears 2xx, and the same event is applied once. One that fails is
kept with its error and answered 500, so Stripe tries again.

An account may serve more than one site, each with its own endpoint: an event
another site's payment wrote (its ``metadata.site``) is acknowledged, never applied.
"""

from __future__ import annotations

import json
import time

import frappe
from frappe.utils import now_datetime

from crm.pagamenti import collegamento, pagamenti
from crm.pagamenti import regole as R

EVENTO = "CRM Stripe Event"


def _conferma() -> None:
	"""The event kept, or its outcome, whatever the request does next."""
	if not frappe.flags.in_test:
		frappe.db.commit()  # nosemgrep: frappe-manual-commit — kept before it is applied, as Stripe retries


def _risposta(stato: int, **dati) -> dict:
	frappe.local.response.http_status_code = stato
	return dati


# nosemgrep: guest-whitelisted-method — Stripe's signature on the raw body is the credential
@frappe.whitelist(allow_guest=True, methods=["POST"])
def stripe() -> dict:
	corpo = frappe.request.get_data(cache=True) or b""
	webhook_secret = collegamento.segreto_del_webhook()
	motivo = R.perche_rifiutata(
		corpo, frappe.get_request_header("Stripe-Signature"), webhook_secret, int(time.time())
	)
	if motivo:
		return _risposta(400, ok=False, reason=motivo)
	try:
		evento = json.loads(corpo)
	except ValueError:
		return _risposta(400, ok=False, reason="not json")
	return ricevi(evento)


def ricevi(evento: dict) -> dict:
	"""Keep the event, then apply it once. (Its signature was checked.)"""
	nome = str(evento.get("id") or "")
	if not nome:
		return _risposta(400, ok=False, reason="no id")
	# what follows writes as DottorCloud: the invoice's log, the booking, the notices
	frappe.set_user("Administrator")
	if frappe.db.get_value(EVENTO, nome, "done"):
		return {"ok": True, "again": True}
	if not frappe.db.exists(EVENTO, nome):
		frappe.get_doc(
			{
				"doctype": EVENTO,
				"event_id": nome,
				"event_type": evento.get("type"),
				"received_on": now_datetime(),
				"payload": json.dumps(evento)[:100000],
			}
		).insert(ignore_permissions=True)
		_conferma()
	# one at a time: Stripe may deliver the same event twice at once
	frappe.db.get_value(EVENTO, nome, "name", for_update=True)
	if frappe.db.get_value(EVENTO, nome, "done"):
		return {"ok": True, "again": True}
	significato = R.significato(evento)
	frappe.db.savepoint("evento_stripe")
	try:
		pagamento = None
		if significato and (not significato.sito or significato.sito == frappe.local.site):
			pagamento = pagamenti.applica(significato)
		frappe.db.set_value(
			EVENTO, nome, {"done": 1, "payment": pagamento, "last_error": ""}, update_modified=False
		)
		_conferma()
	except Exception:
		frappe.db.rollback(save_point="evento_stripe")
		tentativi = (frappe.db.get_value(EVENTO, nome, "attempts") or 0) + 1
		frappe.db.set_value(
			EVENTO,
			nome,
			{"attempts": tentativi, "last_error": frappe.get_traceback()[-2000:]},
			update_modified=False,
		)
		_conferma()
		frappe.log_error(title=f"Stripe event {nome}")
		return _risposta(500, ok=False)
	return {"ok": True}
