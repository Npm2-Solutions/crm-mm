# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Guided conditions, written in Python: what the assignment rules and SLA pages build.

The screen lets the Manager pick a field, an operator and a value; the rule runs a
Python expression. The browser wrote that expression and the server kept it as it
came, so whoever could save a rule could put any Python in it. Conditions written in
Python are the agency's (doc 30): for everybody else the server writes the
expression itself, from the guided conditions.

A port of `convertToConditions` in `frontend/src/utils/index.js`, and stricter:
only fields the document has, only the operators the screen offers, every value
quoted, `and` / `or` and nothing else between two conditions. What the screen
builds comes out the same; what it cannot build is refused.

Pure: `test_condizioni.py` proves it without a site.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

#: The screen's operators, and the Python each one becomes.
OPERATORI = {
	"equals": "==",
	"=": "==",
	"==": "==",
	"!=": "!=",
	"not equals": "!=",
	"<": "<",
	"<=": "<=",
	">": ">",
	">=": ">=",
	"in": "in",
	"not in": "not in",
	"like": "like",
	"not like": "not like",
	"is": "is",
	"is not": "is not",
	"between": "between",
}

CONNETTIVI = ("and", "or")

_CAMPO = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class CondizioneNonValida(ValueError):
	"""A guided condition the screen could not have built."""


def in_python(condizioni: list, campi: Iterable[str] | None = None, prefisso: str | None = None) -> str:
	"""The Python expression for ``condizioni``, as the rule evaluates it.

	- ``condizioni``: the guided conditions, ``[campo, operatore, valore]`` rows with
	  ``"and"`` / ``"or"`` between them; a nested list is a group in brackets.
	- ``campi``: the fields the document has. None does not check them (the tests).
	- ``prefisso``: how the rule reaches the document: ``doc`` for an SLA, nothing
	  for an assignment rule, which sees the fields by name.
	"""
	if not condizioni:
		return ""
	if not isinstance(condizioni, list):
		raise CondizioneNonValida("The conditions are not a list")
	campi = None if campi is None else set(campi)
	if prefisso is not None and not _CAMPO.match(prefisso):
		raise CondizioneNonValida(f"Not a name: {prefisso!r}")
	return _gruppo(condizioni, campi, prefisso)


def _gruppo(condizioni: list, campi: set | None, prefisso: str | None) -> str:
	# a condition, a connective, a condition...: nothing else in between
	if len(condizioni) % 2 == 0:
		raise CondizioneNonValida("A condition is missing after the last connective")
	parti = []
	for posizione, voce in enumerate(condizioni):
		if posizione % 2:
			parti.append(_connettivo(voce))
		elif isinstance(voce, list) and voce and isinstance(voce[0], list):
			parti.append(f"({_gruppo(voce, campi, prefisso)})")
		else:
			parti.append(_condizione(voce, campi, prefisso))
	return " ".join(parti)


def _connettivo(voce) -> str:
	if isinstance(voce, str) and voce.strip().lower() in CONNETTIVI:
		return voce.strip().lower()
	raise CondizioneNonValida(f"Only 'and' and 'or' join two conditions, not {voce!r}")


def _stringa(valore) -> str:
	"""A Python string, in double quotes as the screen writes it."""
	testo = str(valore).replace("\\", "\\\\").replace('"', '\\"')
	return '"' + testo.replace("\n", "\\n").replace("\r", "\\r") + '"'


def _scalare(valore) -> str:
	if isinstance(valore, bool):
		return "True" if valore else "False"
	if isinstance(valore, int | float):
		return repr(valore)
	if isinstance(valore, str):
		return _stringa(valore)
	raise CondizioneNonValida(f"Not a value a condition compares with: {valore!r}")


def _condizione(riga, campi: set | None, prefisso: str | None) -> str:
	if not isinstance(riga, list) or len(riga) != 3:
		raise CondizioneNonValida(f"Not a condition: {riga!r}")
	campo, operatore, valore = riga
	if not isinstance(campo, str) or not _CAMPO.match(campo):
		raise CondizioneNonValida(f"Not a field: {campo!r}")
	if campi is not None and campo not in campi:
		raise CondizioneNonValida(f"The document has no field {campo!r}")
	if not isinstance(operatore, str) or operatore.strip().lower() not in OPERATORI:
		raise CondizioneNonValida(f"Not an operator the screen offers: {operatore!r}")

	op = OPERATORI[operatore.strip().lower()]
	accesso = f"{prefisso}.{campo}" if prefisso else campo
	parola = valore.strip().lower() if isinstance(valore, str) else None

	# a check, as the screen shows it: "is Yes", "is not No"
	if op in ("==", "!=") and parola in ("yes", "no"):
		vero = (parola == "yes") == (op == "==")
		return accesso if vero else f"not {accesso}"

	if op in ("is", "is not"):
		# "is empty" is how the screen said "not set" before it had the words
		if valore is None:
			parola = "not set"
		if parola not in ("set", "not set"):
			raise CondizioneNonValida(f"'{operatore}' takes 'set' or 'not set', not {valore!r}")
		impostato = (parola == "set") == (op == "is")
		return accesso if impostato else f"not {accesso}"

	if op == "like":
		return f"({accesso} and {_stringa(valore)} in {accesso})"
	if op == "not like":
		return f"({accesso} and {_stringa(valore)} not in {accesso})"

	if op == "between":
		estremi = valore.split(",") if isinstance(valore, str) else valore
		if not isinstance(estremi, list) or len(estremi) != 2:
			raise CondizioneNonValida(f"'between' takes two values, not {valore!r}")
		inizio, fine = (_stringa(str(v).strip()) for v in estremi)
		return f"({accesso} >= {inizio} and {accesso} <= {fine})"

	if op in ("in", "not in"):
		if isinstance(valore, list):
			voci = valore
		elif isinstance(valore, str):
			voci = valore.split(",")
		else:
			voci = [valore]
		lista = ", ".join(_stringa(str(v).strip()) for v in voci)
		return f"({accesso} and {accesso} {op} [{lista}])"

	if valore is None:
		return f"not {accesso}" if op == "==" else accesso

	return f"{accesso} {op} {_scalare(valore)}"
