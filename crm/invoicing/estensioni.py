# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Where another module plugs into invoicing.

Invoicing knows how to issue, calculate, format and transmit a document. What it
deliberately does not know is which qualifications exist and what duties they carry
- that arrives from outside, through here.

One direction only: invoicing never imports the module that registers. A module
that wants in calls `registra_risolutore` when it loads, and invoicing goes on
working unchanged when nobody does.
"""

from __future__ import annotations

from contextlib import contextmanager

from crm.invoicing.engine import professioni
from crm.invoicing.engine.qualifica import Risolutore

#: Resolvers, in registration order. A chain rather than one slot, because more
#: than one register legitimately answers: what the practice edited, what the
#: healthcare module adds, and what this module ships. Module-level rather than a
#: Frappe hook so the engine stays importable without a site.
_risolutori: list[Risolutore] = []


def registra_risolutore(funzione: Risolutore) -> None:
	"""Add a register. The last one registered is asked first."""
	if funzione not in _risolutori:
		_risolutori.append(funzione)


def risolutore() -> Risolutore:
	"""Ask each register in turn, most recently added first.

	A register says "not mine" by raising `KeyError`, and the chain moves on. The
	floor is this module's own twenty qualifications - not a neutral answer, because
	a lawyer's invoice without Cassa Forense and withholding is a **wrong invoice**,
	not an incomplete one.

	The last link raises too. A qualification nobody configured has no VAT regime, no
	fund and no withholding, and inventing any of the three produces a document that
	is wrong in a way nobody notices until it is too late.
	"""

	def _risolvi(codice: str):
		for funzione in reversed(_risolutori):
			try:
				return funzione(codice)
			except KeyError:
				continue
		return professioni.professione(codice)

	return _risolvi


#: How a line's secondary-reporting code is worked out. Invoicing knows a line may
#: have a duty towards some system that is not the SdI; which code that system wants,
#: and whether this line can even produce one, is the registering module's business.
_arricchitore = None


def registra_arricchitore(funzione) -> None:
	global _arricchitore
	_arricchitore = funzione


def arricchitore():
	"""The registered enricher, or nothing - which means nothing to report."""
	return _arricchitore


#: Extra checks to run while a document is being edited. A module that adds a
#: duty adds the checking of it: invoicing has no way to explain a rule it does
#: not own, and a controller that imports one is a controller that stops loading
#: the day that module is not installed.
_verifiche: list = []


def registra_verifica(funzione) -> None:
	"""Contribute a check that runs on validate. Called once, when a module loads."""
	if funzione not in _verifiche:
		_verifiche.append(funzione)


def verifiche(doc, preparato) -> None:
	"""Run every registered check. One failing never hides the rest."""
	for funzione in _verifiche:
		funzione(doc, preparato)


#: Extra rows for the onboarding checklist. A module that adds a duty adds the gap
#: that comes with it, rather than invoicing carrying a list of other people's
#: obligations it cannot explain.
_controlli: list = []


def registra_controlli(funzione) -> None:
	"""Contribute onboarding gaps. Called once, when a module loads."""
	if funzione not in _controlli:
		_controlli.append(funzione)


def controlli_aggiuntivi(emittente: dict) -> list[dict]:
	"""Every registered module's gaps for this company, in registration order."""
	voci: list[dict] = []
	for funzione in _controlli:
		voci.extend(funzione(emittente) or [])
	return voci


@contextmanager
def senza_estensioni():
	"""Invoicing on its own for the length of a block, and put back exactly as found.

	A test that needs the bare module must not leave the module bare. These registries
	are process-wide - one list, filled once when the app loads - so emptying one
	without putting it back does not isolate a test, it breaks every test that runs
	after it, and in a worker it breaks the site.

	That is not hypothetical either: clearing the resolvers and not restoring them
	cost sixty-one errors in the one suite that runs everything in a single process,
	all of them reading "qualification 'osteopata' is not in the register" - which was
	true, because a test three modules earlier had thrown the register away.
	"""
	global _arricchitore
	risolutori, arricchitore = list(_risolutori), _arricchitore
	verifiche_precedenti, controlli_precedenti = list(_verifiche), list(_controlli)
	_risolutori.clear()
	_verifiche.clear()
	_controlli.clear()
	_arricchitore = None
	try:
		yield
	finally:
		_risolutori[:] = risolutori
		_verifiche[:] = verifiche_precedenti
		_controlli[:] = controlli_precedenti
		_arricchitore = arricchitore
