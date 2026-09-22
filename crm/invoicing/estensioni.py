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

from crm.invoicing.engine.qualifica import Risolutore, risolutore_neutro

#: The registered resolver, or nothing. Module-level rather than a Frappe hook so
#: the engine stays importable without a site - the suite that proves the fiscal
#: rules runs on a checkout and a Python interpreter, and that is worth keeping.
_risolutore: Risolutore | None = None


def registra_risolutore(funzione: Risolutore) -> None:
	"""Supply the register of qualifications. Called once, when a module loads."""
	global _risolutore
	_risolutore = funzione


def dimentica_risolutore() -> None:
	"""Back to the neutral answer. For tests that need the bare module."""
	global _risolutore
	_risolutore = None


def risolutore() -> Risolutore:
	"""Whoever answers about qualifications today, or the dull default."""
	return _risolutore or risolutore_neutro


#: How a line's secondary-reporting code is worked out. Invoicing knows a line may
#: have a duty towards some system that is not the SdI; which code that system wants,
#: and whether this line can even produce one, is the registering module's business.
_arricchitore = None


def registra_arricchitore(funzione) -> None:
	global _arricchitore
	_arricchitore = funzione


def dimentica_arricchitore() -> None:
	global _arricchitore
	_arricchitore = None


def arricchitore():
	"""The registered enricher, or nothing - which means nothing to report."""
	return _arricchitore


#: Extra rows for the onboarding checklist. A module that adds a duty adds the gap
#: that comes with it, rather than invoicing carrying a list of other people's
#: obligations it cannot explain.
_controlli: list = []


def registra_controlli(funzione) -> None:
	"""Contribute onboarding gaps. Called once, when a module loads."""
	if funzione not in _controlli:
		_controlli.append(funzione)


def dimentica_controlli() -> None:
	_controlli.clear()


def controlli_aggiuntivi(emittente: dict) -> list[dict]:
	"""Every registered module's gaps for this company, in registration order."""
	voci: list[dict] = []
	for funzione in _controlli:
		voci.extend(funzione(emittente) or [])
	return voci
