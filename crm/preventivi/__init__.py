# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Quotes: what the centre proposes to a person, service by service, and follows
until it is done (docs/verticali/clinica/design.md, "Tre strati": "Il preventivo").

A beauty centre's laser package, a gym's personal training, a dentist's care plan:
each is a quote, so it is the CRM's, not the clinic's.

- **The rules** (`regole`): the rows from the price list with a discount, in
  phases, the sums, the states.
- **The quotes** (`api`): a draft of its author; proposed, a PDF to hand over and
  the person's deal in the quotes pipeline; accepted or declined, by the author or
  by who handles quotes; a new version; what a module adds to the rows
  (`registra_estensione`: the clinic's tooth and surfaces).
- **The appointments** (`appuntamenti`): an appointment of a service still to do
  takes its row at the price agreed, and done, it is done.
- **The pipeline** (`pipeline`): "Quotes", from the quote delivered to accepted or
  declined.
- **In the area** (`area`): the quotes proposed to the person and going on.
"""

from __future__ import annotations

from crm.permissions.livelli import CENTRO, SUOI, TEAM, Capacita, registra_capacita

#: The plan's module quotes go with: the base, every centre makes them.
PIANO = "base"

CAPACITA = (
	(
		Capacita(
			"preventivi.vedi",
			PIANO,
			scrive=False,
			descrizione="Read the quotes proposed to the people one sees, and how they are going",
		),
		{"segreteria": CENTRO, "operatore": SUOI, "commerciale": TEAM, "manager": CENTRO},
	),
	(
		Capacita(
			"preventivi.scrivi",
			PIANO,
			descrizione="Write quotes from the price list, propose them, and make a new version",
		),
		{"segreteria": CENTRO, "operatore": SUOI, "commerciale": TEAM, "manager": CENTRO},
	),
	# the desk records the answer, whoever wrote the quote
	(
		Capacita(
			"preventivi.gestisci",
			PIANO,
			descrizione="Record a quote accepted or declined, whoever wrote it",
		),
		{"segreteria": CENTRO, "manager": CENTRO},
	),
)


def registra() -> None:
	from crm.area.sezioni import Sezione, registra_sezione
	from crm.persone import riepilogo
	from crm.preventivi import api, area

	for capacita, concessioni in CAPACITA:
		registra_capacita(capacita, concessioni)
	# the quotes proposed and going on, in the person's area
	registra_sezione(Sezione("quotes", area.nell_area))
	# the ones waiting for an answer and the ones going on, in the person's summary
	riepilogo.registra_voce(riepilogo.Voce("quotes", api.nel_riepilogo))
