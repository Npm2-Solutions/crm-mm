# Copyright (c) 2026, NPM2 Solutions Srl and contributors
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
	ModuloPiano,
	registra_capacita,
	registra_modulo_piano,
	registra_ruolo,
)

#: Invoicing is an extra of the plan (listino.md, 01/10/2026): many centres
#: invoice through their accountant. The Sistema TS always comes with it - whoever
#: invoices healthcare to private persons owes it, and may not send those
#: invoices to the SdI. On by default: every site invoiced before plans existed.
PIANO = "fatturazione"

MODULO = ModuloPiano(
	PIANO,
	"Invoicing",
	descrizione="Unlimited invoices, the Sistema TS with the practice's credentials, SdI credits included every year",
	ordine=3,
	impostazioni=("Issuing company", "Provider connection", "Invoicing defaults"),
)

RUOLI = (
	(
		"Invoicing Manager",
		"Issues, cancels and transmits invoices, and configures the register.",
		("manager", "amministrazione"),
	),
	(
		"Invoicing User",
		"Issues invoices and records payments; cancels nothing, transmits only when allowed.",
		("segreteria", "manager", "amministrazione"),
	),
)

CAPACITA = (
	(
		Capacita("fatture.vedi", PIANO, scrive=False),
		{"segreteria": CENTRO, "operatore": SUOI, "manager": CENTRO, "amministrazione": CENTRO},
	),
	(
		Capacita("fatture.emetti", PIANO, descrizione="From the appointment or new"),
		{"segreteria": CENTRO, "manager": CENTRO, "amministrazione": CENTRO},
	),
	(
		Capacita("fatture.incassi", PIANO, descrizione="Record payments"),
		{"segreteria": CENTRO, "manager": CENTRO, "amministrazione": CENTRO},
	),
	(
		Capacita("fatture.annulla", PIANO, descrizione="Cancel, credit notes"),
		{"manager": CENTRO, "amministrazione": CENTRO},
	),
	(
		Capacita("fatture.invia", PIANO, descrizione="Send to the SdI and the Sistema TS"),
		{"segreteria": A_SCELTA, "manager": CENTRO, "amministrazione": CENTRO},
	),
	(
		Capacita("fatture.esporta", PIANO, scrive=False, descrizione="For the accountant"),
		{"manager": CENTRO, "amministrazione": CENTRO},
	),
	(
		Capacita("fatture.configura", PIANO, descrizione="Company, register, services, providers, provider"),
		{"manager": CENTRO, "amministrazione": CENTRO},
	),
)

TECNICHE = (Capacita("fatture.segreti", PIANO, agenzia=True, descrizione="The provider's webhook secrets"),)


def registra() -> None:
	from crm.primi_passi import Passo, c_e, registra_passo

	registra_modulo_piano(MODULO)
	# a first step where the centre invoices with the product: who issues them
	registra_passo(
		Passo(
			"fatture",
			"Who issues the invoices",
			"The company's details and numbering, and the Sistema TS: the first invoice goes out right.",
			lambda: c_e("CRM Invoicing Company", {"enabled": 1, "tax_id": ["is", "set"]}),
			("fatture.configura",),
			pagina="Issuing company",
			modulo=PIANO,
			ordine=75,
		)
	)
	for nome, descrizione, livelli in RUOLI:
		# invoicing roles alone do not open the CRM: whoever holds one works in it
		# through a level that also brings a CRM role
		registra_ruolo(nome, descrizione, livelli, accesso=False)
	for capacita, livelli in CAPACITA:
		registra_capacita(capacita, livelli)
	for capacita in TECNICHE:
		registra_capacita(capacita)
