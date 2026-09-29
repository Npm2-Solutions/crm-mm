# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""How a person becomes a patient: the rules, without a site.

Every centre works its own way - the one with a front desk, the doctor who opens
the page and starts writing, the one that only issues invoices - so there is no
compulsory step, but a list of rules: **the first that fires converts, and that is
it** (`docs/gestionale-medico/README.md`, "Come si diventa paziente"). None
excludes the others, none is required, and a patient stays a patient: the clinical
record has to be kept.

The same list works backwards: switched on over months of appointments and
invoices, the clinic finds its patients by itself. There the rule that counts is
the one that would have fired first, in time; the table's order only breaks a tie.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Regola:
	numero: int
	#: What the patient card stores, in English like every stored choice.
	valore: str
	descrizione: str


INFORMAZIONE_MEDICA = Regola(1, "Medical information", "The first clinical record saved about the person")
ACCETTAZIONE = Regola(2, "Check-in", "Their arrival registered at the desk")
APPUNTAMENTO_SVOLTO = Regola(3, "Appointment attended", "An appointment marked as completed or attended")
FATTURA_SANITARIA = Regola(4, "Healthcare invoice", "The first confirmed invoice with a healthcare line")
IMPORTAZIONE = Regola(5, "Import", "Brought over from the previous software")
A_MANO = Regola(6, "By hand", "Somebody marked them as a patient")

REGOLE = (INFORMAZIONE_MEDICA, ACCETTAZIONE, APPUNTAMENTO_SVOLTO, FATTURA_SANITARIA, IMPORTAZIONE, A_MANO)
PER_VALORE = {regola.valore: regola for regola in REGOLE}

#: How the appointment ended, for the rule that reads the agenda.
APPUNTAMENTO_COMPLETATO = "Completed"
PARTECIPANTE_PRESENTE = "Attended"
#: A participant who did not come does not become a patient because the others did.
PARTECIPANTE_ASSENTE = ("No Show", "Cancelled")


def presente(stato_appuntamento: str | None, stato_partecipante: str | None) -> bool:
	"""Whether this participant came: marked attended, or on a completed appointment.

	Somebody who booked and never showed stays a contact: better one patient less
	than a no-show counted as a patient.
	"""
	if stato_partecipante == PARTECIPANTE_PRESENTE:
		return True
	return stato_appuntamento == APPUNTAMENTO_COMPLETATO and stato_partecipante not in PARTECIPANTE_ASSENTE


def prima_regola(fatti: dict[str, datetime | None]) -> tuple[Regola, datetime] | None:
	"""Which rule would have fired first, from the facts found about one person.

	``fatti`` maps a rule's value to the moment its first fact happened (or None).
	The earliest fact wins; on the same moment, the table's order.
	"""
	trovati = [(quando, regola.numero, regola) for regola in REGOLE if (quando := fatti.get(regola.valore))]
	if not trovati:
		return None
	quando, _numero, regola = min(trovati, key=lambda t: (t[0], t[1]))
	return regola, quando
