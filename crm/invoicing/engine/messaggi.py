# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What the engine says, translatable where a screen shows it.

The engine is pure Python and speaks English: its tests read the messages, and an
accountant can read them without a bench. A screen in Italian wants them in
Italian, and a sentence built with an f-string cannot be looked up in a catalogue.
So a message that carries values is a string that reads exactly as before and
keeps the template it was made from, with its values: the boundary translates the
template and fills it again (`crm.invoicing.documento.in_parole`). A message with
no values is its own template.
"""

from __future__ import annotations


class Messaggio(str):
	"""A sentence of the engine: the English text, its template and its values."""

	modello: str
	argomenti: tuple

	def __new__(cls, modello: str, *argomenti) -> Messaggio:
		testo = super().__new__(cls, modello.format(*argomenti))
		testo.modello = modello
		testo.argomenti = argomenti
		return testo
