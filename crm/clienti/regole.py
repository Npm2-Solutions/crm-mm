# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Who becomes a client: the rules, without a site.

Every centre works its own way - the one with a front desk, the one where the
practitioner opens the door, the one that only issues invoices - so no step is
compulsory: each fact below says the person is a client, and the first to arrive
counts (`cliente.diventa_cliente`). A client stays a client.

A module whose trade has rules of its own builds its list on these (the clinic's
patients): the same `Regola`, the same `presente`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Regola:
	numero: int
	#: What the automations hear as the event's rule, in English like every stored choice.
	valore: str
	descrizione: str


ACCETTAZIONE = Regola(1, "Check-in", "Their arrival registered at the desk")
APPUNTAMENTO_SVOLTO = Regola(2, "Appointment attended", "An appointment marked as completed or attended")
FATTURA = Regola(3, "Invoice", "The first confirmed invoice made out to them")

REGOLE = (ACCETTAZIONE, APPUNTAMENTO_SVOLTO, FATTURA)

#: How the appointment ended, for the rules that read the agenda.
APPUNTAMENTO_COMPLETATO = "Completed"
PARTECIPANTE_PRESENTE = "Attended"
#: A participant who did not come does not become a client because the others did.
PARTECIPANTE_ASSENTE = ("No Show", "Cancelled")
#: A credit note gives money back: it sells nothing (the SDI's document types).
NOTE_DI_CREDITO = ("TD04", "TD08")


def presente(stato_appuntamento: str | None, stato_partecipante: str | None) -> bool:
	"""Whether this participant came: marked attended, or on a completed appointment.

	Somebody who booked and never showed stays a contact: better one client less
	than a no-show counted as a client.
	"""
	if stato_partecipante == PARTECIPANTE_PRESENTE:
		return True
	return stato_appuntamento == APPUNTAMENTO_COMPLETATO and stato_partecipante not in PARTECIPANTE_ASSENTE


def accolto(arrivato: datetime | str | None, stato_partecipante: str | None) -> bool:
	"""Whether the desk checked this participant in, and nobody then marked them gone."""
	return bool(arrivato) and stato_partecipante not in PARTECIPANTE_ASSENTE


def vendita(tipo_documento: str | None) -> bool:
	"""Whether an invoice of this document type sold something: not a credit note."""
	return tipo_documento not in NOTE_DI_CREDITO


def primo(fatti: list[tuple[datetime | None, Regola]]) -> tuple[datetime, Regola] | None:
	"""The fact that came first, in time: the moment a person became a client, found
	in the data already there. On the same moment, the table's order."""
	trovati = [(quando, regola.numero, regola) for quando, regola in fatti if quando]
	if not trovati:
		return None
	quando, _numero, regola = min(trovati, key=lambda t: (t[0], t[1]))
	return quando, regola
