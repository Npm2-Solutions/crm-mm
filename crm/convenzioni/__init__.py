# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Conventions, health funds and insurances (doc 61).

A medical centre works with funds and insurers, a gym or a beauty centre with the
companies whose employees get a discount: so it is the CRM's.

- **The rules** (`regole`): the convention's price, the person's share and the
  fund's to the cent, a pratica's state, the month's statement.
- **The records**: `CRM Convention` (Settings > Invoicing > Conventions and funds,
  `convenzioni.gestisci`), a person's `CRM Convention Cover` (their Data tab, their
  summary), the appointment's `convention`, `convention_form`, `authorisation`
  and its two shares (`convenzioni`).
- **The fund's invoice** (`convenzioni.fattura_al_fondo`): one a month, one line a
  pratica, from the Invoices page's Conventions tab (`api`).
"""

from __future__ import annotations

from crm.permissions.livelli import CENTRO, Capacita, registra_capacita

CAPACITA = (
	(
		Capacita("convenzioni.gestisci", descrizione="Conventions with funds, insurers and companies"),
		{"manager": CENTRO, "amministrazione": CENTRO},
	),
)


def registra() -> None:
	for capacita, livelli in CAPACITA:
		registra_capacita(capacita, livelli)
	# the person's covers, in their summary
	from crm.convenzioni import api
	from crm.persone import riepilogo

	riepilogo.registra_voce(riepilogo.Voce("covers", api.nel_riepilogo))
	# its share of the demo: a fund in direct form, a company's discount
	from crm.convenzioni import demo
	from crm.demo.registro import Parte, registra_parte

	registra_parte(
		Parte(
			"convenzioni",
			"Conventions and funds",
			demo.crea,
			dopo=("clienti", "aziende"),
			prima=("fatturazione",),
			descrizione="An insurance in direct form with the people it covers, their visits "
			"authorised and done and one still to authorise; a company's discount for its "
			"employees.",
		)
	)
