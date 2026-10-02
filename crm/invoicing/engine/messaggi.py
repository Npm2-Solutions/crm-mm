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


def in_chiaro(valore):
	"""A value as the English text shows it: a list of names joined by commas."""
	if isinstance(valore, list | tuple):
		return ", ".join(str(voce) for voce in valore)
	return valore


class Messaggio(str):
	"""A sentence of the engine: the English text, its template and its values.

	A value that is a name (an expense type, a category: `Nome`) is translated with
	the sentence; a list of them is joined by commas. Any other value - an amount, a
	code the person typed - goes in as it is."""

	modello: str
	argomenti: tuple

	def __new__(cls, modello: str, *argomenti) -> Messaggio:
		testo = super().__new__(cls, modello.format(*(in_chiaro(valore) for valore in argomenti)))
		testo.modello = modello
		testo.argomenti = argomenti
		return testo


class Rilievo(Messaggio):
	"""A finding of the SdI's own checks: a sentence, and the code the SdI would
	answer with (its "Elenco dei controlli"). The code stays out of the words, at the
	end and the same in every language: support looks it up, and
	`fatturapa.bloccanti` tells a rejection from a remark even in a stored message."""

	codice: str

	def __new__(cls, codice: str, modello: str, *argomenti) -> Rilievo:
		testo = Messaggio.__new__(cls, modello, *argomenti)
		testo = str.__new__(cls, f"{testo}{coda_sdi(codice)}")
		testo.modello = modello
		testo.argomenti = argomenti
		testo.codice = codice
		return testo

	@property
	def coda(self) -> str:
		return coda_sdi(self.codice)


def coda_sdi(codice: str) -> str:
	"""How a finding says the code the SdI would answer with: « (SdI 00422)»."""
	return f" (SdI {codice})"


class Nome(str):
	"""A name from a vocabulary (`Voce.etichetta`) put in a sentence: it is
	translated where the sentence is, never shown as its code."""
