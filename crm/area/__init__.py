# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The client area, `/area`: the person's own window on the centre.

Any business that works by appointments gives it to the people it looks after - a
beauty centre, a gym, a medical centre - so it is the CRM's, not the clinic's
(docs/gestionale-medico/design.md, "Tre strati"). Who enters is a user of the site
with the area's role, never staff, invited by the centre for one or more people:
themselves, a child, an elderly parent who said yes (`CRM Area Access`). Every call
derives "my people" on the server from that list and never takes a person the
session was not given.

- **The door** is a code by email or a passkey (`accesso`, `passkey`).
- **Inside**: the appointments, the forms to fill before one, the invoices
  (`api`); the centre's board (`messaggi`); a chat about hours and bookings
  (`chat`); news also by WhatsApp or SMS (`avvisi`).
- **Other modules add to it** without the CRM knowing them: their places
  (`sezioni`) - the clinic its documents, plans and care plans - and their kinds of
  message, with their own readers (`messaggi.registra_tipo`).

It is a module of the plan of its own, "Client area", which the base comprises:
every centre has it, since every centre gives its people documents and invoices
(05/10/2026). The clinic comprises it too, and names it "the patient area".
"""

from __future__ import annotations

from crm.assistente import Funzione, registra_funzione
from crm.permissions.livelli import (
	CENTRO,
	SUOI,
	Capacita,
	ModuloPiano,
	registra_capacita,
	registra_modulo_piano,
)

#: The plan's module: the base comprises it, and so does the clinic.
PIANO = "area"

MODULO = ModuloPiano(
	PIANO,
	"Client area",
	predefinito=False,
	descrizione="The app of the people the centre looks after: appointments, forms, invoices, "
	"messages, the chat",
	ordine=5,
	impostazioni=("News in the client area",),
)

CAPACITA = (
	# the centre opens a person's area to them, or to whoever answers for them
	(
		Capacita(
			"area.invita",
			PIANO,
			descrizione="Open a person's area to them, or to who answers for them, and close it",
		),
		{"segreteria": CENTRO, "operatore": SUOI, "manager": CENTRO},
	),
	(
		Capacita(
			"area.messaggi",
			PIANO,
			descrizione="Write on the person's board in their area, and read what they passed on "
			"from the chat",
		),
		{"segreteria": CENTRO, "operatore": SUOI},
	),
)

#: The chat in the area: the people use it; in DottorCloud it goes with the area's
#: messages, where what it passes on arrives, and the manager reads its register.
#: The key is the one it was born with: the switch and the events keep it.
CHAT = Funzione(
	"patient_chat",
	"The chat in the area",
	usa="area.messaggi",
	legge="assistente.registro",
	interruttore="patient_chat",
)


def registra() -> None:
	from crm.area import messaggi

	registra_modulo_piano(MODULO)
	for capacita, concessioni in CAPACITA:
		registra_capacita(capacita, concessioni)
	registra_funzione(CHAT)
	messaggi.registra()
	# its share of the demo: the area opened to the regulars, who came in
	from crm.area import demo
	from crm.demo.registro import Parte, registra_parte

	registra_parte(
		Parte(
			"area",
			"Client area",
			demo.crea,
			modulo=PIANO,
			dopo=("clienti", "abbonamenti"),
			descrizione="The area opened to the regulars and to a few who come in the next days, a "
			"mother with her child's beside her own; most came in, the desk wrote on some boards "
			"and some read it.",
		)
	)
