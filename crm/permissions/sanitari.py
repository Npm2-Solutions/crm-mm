# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Health data in what the CRM keeps for a person: which carries the mark, and who
reads it.

A person's plans, programmes and documents are the CRM's, for any centre; some of
them are health data - a diet, a test result, a report (docs/gestionale-medico/
design.md, "Tre strati"). They carry the mark (`clinical`), and the module that
knows health data says who reads them and what else carries it: the clinic
registers its reader here, the dossier and "whatever a health professional
writes is health data".

With nobody registered, what carries the mark is read only by whoever wrote or
added it.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Lettore:
	"""Who reads what carries the mark, where a module says so: the clinic, like a visit."""

	#: Whether ``user`` reads this document with the mark, though it is not theirs.
	legge: Callable[[object, str], bool]
	#: The same, as a condition on the table; None: nobody but whose it is.
	condizione: Callable[[object, str], object | None]
	#: Whether a document is health data whatever its kind: who wrote it, or for whom.
	marca: Callable[[object], bool] | None = None


_lettore: dict[str, Lettore] = {}


def registra_lettore(lettore: Lettore) -> None:
	_lettore["sanitario"] = lettore


def lettore() -> Lettore | None:
	return _lettore.get("sanitario")


def legge(doc, user: str) -> bool:
	"""Whether ``user`` reads a document with the mark that is not theirs."""
	registrato = lettore()
	return bool(registrato and registrato.legge(doc, user))


def condizione(tabella, user: str):
	"""The rows with the mark ``user`` reads though they are not theirs, as a
	condition on ``tabella``; None when there are none."""
	registrato = lettore()
	return registrato.condizione(tabella, user) if registrato else None


def per_chi_scrive(doc) -> bool:
	"""Whether a document is health data by who wrote it or whom it is for."""
	registrato = lettore()
	return bool(registrato and registrato.marca and registrato.marca(doc))
