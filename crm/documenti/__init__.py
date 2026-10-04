# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A person's documents, and giving them: the CRM's, for any centre
(docs/gestionale-medico/design.md, "Tre strati": "I documenti della persona").

A beauty centre keeps a signed consent and a photo, a gym a contract and a
certificate, a medical centre a report and a test result: each one a document
with its type, its date, where it comes from and whom it is for, the file private
and its SHA-256 kept.

- **The documents** (`api`): read, added, put right, taken away by mistake; filed
  from a conversation. The kinds are registered (`regole`): the CRM's own, and the
  clinic's with the mark of health data.
- **Giving one** (`consegna`): by hand, or online with a link and a code given
  another way; a module says when one of its documents may not go online, and for
  how long at most.
- **In the area** (`area`): what was given online, while it is.

What carries the mark of health data is read by the rule the clinic registers
(`crm.permissions.sanitari`); a module adds its fields (`api.registra_estensione`)
and its rules on going online (`consegna.registra_regola`).
"""

from __future__ import annotations

from crm.permissions.livelli import CENTRO, SUOI, Capacita, registra_capacita

#: The plan's module documents go with: the base, every centre has them.
PIANO = "base"

CAPACITA = (
	(
		Capacita(
			"documenti.vedi",
			PIANO,
			scrive=False,
			descrizione="Read the documents of the people one sees: contracts, signed forms, what they "
			"brought. Health data is read like the clinical record",
		),
		{"segreteria": CENTRO, "operatore": SUOI, "manager": CENTRO},
	),
	(
		Capacita(
			"documenti.aggiungi",
			PIANO,
			descrizione="Add a person's documents: what they bring, what arrives in a conversation",
		),
		{"segreteria": CENTRO, "operatore": SUOI, "manager": CENTRO},
	),
	(
		Capacita(
			"documenti.consegna",
			PIANO,
			descrizione="Give a document to the person: by hand, or online with a link and a code",
		),
		{"segreteria": CENTRO, "operatore": SUOI, "manager": CENTRO},
	),
	# the same day whoever added it takes a document away; later, the manager
	(
		Capacita(
			"documenti.togli",
			PIANO,
			descrizione="Take away a document added by mistake, after the day it was added",
		),
		{"manager": CENTRO},
	),
)


def registra() -> None:
	from crm.area.sezioni import Sezione, registra_sezione
	from crm.documenti import area

	for capacita, concessioni in CAPACITA:
		registra_capacita(capacita, concessioni)
	# "Documents" in the area, to whom the centre gave something online
	registra_sezione(Sezione("documents", area.documenti_online))
	# its share of the demo: contracts, certificates, a few given online
	from crm.demo.registro import Parte, registra_parte
	from crm.documenti import demo

	registra_parte(
		Parte(
			"documenti",
			"Documents",
			demo.crea,
			dopo=("clienti", "abbonamenti"),
			descrizione="The contract of every subscription, handed over; the certificate the regulars "
			"of the classes brought; a few given online, one already downloaded.",
		)
	)
