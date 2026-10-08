# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Online payments on the centre's own Stripe account (doc 60).

A beauty centre, a gym and a medical centre are paid the same way, so it is the
CRM's. DottorCloud resells nothing and holds no money: as with Twilio (doc 52),
the centre connects its own account and Stripe pays it; DottorCloud makes the
links and hears what happened.

- **The rules** (`regole`): the key's mode, Stripe's signature, amounts in cents,
  what an event means, the deposit a service asks, a refund at cancelling.
- **Stripe** (`cliente`): its REST API through `requests`.
- **The connection** (`collegamento`): Settings > Invoicing > Online payments.
- **The payments** (`pagamenti`): an invoice paid from the area or a link the desk
  sends, a deposit at online booking; `webhook` applies what Stripe says, once.
"""

from __future__ import annotations

from crm.permissions.livelli import CENTRO, Capacita, registra_capacita

CAPACITA = (
	(
		Capacita("pagamenti.gestisci", descrizione="Connect Stripe, the deposits' rule"),
		{"manager": CENTRO, "amministrazione": CENTRO},
	),
)


def registra() -> None:
	for capacita, livelli in CAPACITA:
		registra_capacita(capacita, livelli)
