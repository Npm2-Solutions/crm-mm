# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""What invoicing brings to the permission registry.

Its two roles, the levels they go to, and the invoicing column of doc 30's matrix.
The registry is the CRM's (`crm.permissions.livelli`): invoicing registers into it
the way the Sistema TS registers into invoicing, and the CRM never names an
invoicing capability itself.

The level keys are plain strings on purpose: importing them from the CRM's
catalogue would tie this module to it for nothing.
"""

from __future__ import annotations

from crm.permissions.livelli import (
	A_SCELTA,
	CENTRO,
	SUOI,
	Capacita,
	registra_capacita,
	registra_ruolo,
)

#: Invoicing belongs to the Base plan: every centre issues invoices, and the
#: Sistema TS comes with them (listino.md, "Il Sistema TS sta nella Base").
PIANO = "base"

RUOLI = (
	(
		"Invoicing Manager",
		"Issues, cancels and transmits invoices, and configures the register.",
		("manager",),
	),
	("Invoicing User", "Reads invoices and the register.", ("segreteria", "manager")),
)

CAPACITA = (
	(
		Capacita("fatture.vedi", PIANO, scrive=False),
		{"segreteria": CENTRO, "operatore": SUOI, "manager": CENTRO},
	),
	(
		Capacita("fatture.emetti", PIANO, descrizione="From the appointment or new"),
		{"segreteria": CENTRO, "manager": CENTRO},
	),
	(
		Capacita("fatture.incassi", PIANO, descrizione="Record payments"),
		{"segreteria": CENTRO, "manager": CENTRO},
	),
	(Capacita("fatture.annulla", PIANO, descrizione="Cancel, credit notes"), {"manager": CENTRO}),
	(
		Capacita("fatture.invia", PIANO, descrizione="Send to the SdI and the Sistema TS"),
		{"segreteria": A_SCELTA, "manager": CENTRO},
	),
	(Capacita("fatture.esporta", PIANO, scrive=False, descrizione="For the accountant"), {"manager": CENTRO}),
	(
		Capacita("fatture.configura", PIANO, descrizione="Company, register, services, providers, provider"),
		{"manager": CENTRO},
	),
)

TECNICHE = (Capacita("fatture.segreti", PIANO, agenzia=True, descrizione="The provider's webhook secrets"),)


def registra() -> None:
	for nome, descrizione, livelli in RUOLI:
		# invoicing roles alone do not open the CRM: whoever holds one works in it
		# through a level that also brings a CRM role
		registra_ruolo(nome, descrizione, livelli, accesso=False)
	for capacita, livelli in CAPACITA:
		registra_capacita(capacita, livelli)
	for capacita in TECNICHE:
		registra_capacita(capacita)
