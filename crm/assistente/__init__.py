# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The assistant: documentation support, never alone (design.md, "L'assistente").

In order, from what gives most with least risk: office work first - a paper form
that becomes a template - then drafts the professional checks and signs. It is a
module of the plan of its own, off until the agency switches it on, and it runs
only where the model's contract says it keeps nothing and trains on nothing.

What a module brings: its functions (`registra_funzione`), each with the
capability that uses it and the one that reads its events in the register. The
CRM brings "a form from paper"; the clinic registers its own, which read health
data, and whose register only the medical director reads.
"""

from __future__ import annotations

from dataclasses import dataclass

from crm.permissions.livelli import (
	CENTRO,
	Capacita,
	ModuloPiano,
	registra_capacita,
	registra_modulo_piano,
)

#: The plan's module: off until the agency switches it on.
PIANO = "assistente"

MODULO = ModuloPiano(
	PIANO,
	"Assistant",
	predefinito=False,
	descrizione="Forms from paper, drafts from a signed note: documentation support the professional reviews",
	ordine=6,
)

CAPACITA = (
	(
		Capacita(
			"assistente.moduli",
			PIANO,
			descrizione="Turn the centre's paper form into a draft template, checked before it is used",
		),
		{"manager": CENTRO},
	),
	(
		Capacita(
			"assistente.registro",
			PIANO,
			scrive=False,
			descrizione="Read the assistant's register: what was asked, of which model, and what became of it",
		),
		{"manager": CENTRO},
	),
)


@dataclass(frozen=True)
class Funzione:
	chiave: str
	etichetta: str
	#: the capability that uses it
	usa: str
	#: the capability that reads its events in the register
	legge: str
	#: the switch in the settings that turns it on, when it has one
	interruttore: str | None = None


_funzioni: dict[str, Funzione] = {}


def registra_funzione(funzione: Funzione) -> None:
	_funzioni[funzione.chiave] = funzione


def funzione(chiave: str) -> Funzione | None:
	return _funzioni.get(chiave)


def funzioni() -> list[Funzione]:
	return list(_funzioni.values())


DAL_MODULO_DI_CARTA = Funzione(
	"form_from_paper",
	"A form from paper",
	usa="assistente.moduli",
	legge="assistente.registro",
	interruttore="paper_forms",
)


def registra() -> None:
	registra_modulo_piano(MODULO)
	for capacita, livelli in CAPACITA:
		registra_capacita(capacita, livelli)
	registra_funzione(DAL_MODULO_DI_CARTA)
