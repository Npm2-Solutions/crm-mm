# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The verticals: a module of the plan that turns the CRM into the software of a trade.

The CRM underneath is the same for everybody, and says what it does in neutral
words: clients, appointments, the client area. A vertical switched on by the plan
makes it the software of its trade, all the way (docs/gestionale-medico/design.md,
"Tre strati"): with the clinic on, the CRM is a medical centre's management
software and says so everywhere.

- **Its words**: pairs of English strings, the base's and the vertical's that
  replaces it - "Client area", "Patient area". Each language translates the
  vertical's own string: the SPA gets them in its boot already translated
  (`per_il_boot`), the area with its own dictionary (`parole`), the server asks
  `parola()`.
- **Its places**: what of the base would limit the trade is hidden (`nascosto`),
  and the vertical's own shows instead.
- **Its brand** (`marchio`): the product's name, icon, logo, favicon and colours,
  everywhere, from `crm.marchio`.
- **Its invoicing** (`fatturazione`): the profile of its trade, the only one offered
  while it is on (`crm.invoicing.scelte`).

A vertical registers from its own `registra()`, like its capabilities: the CRM
never names one. At most one is on on a site; if two were, the first registered
would speak.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Verticale:
	chiave: str
	#: The plan's module that switches it on.
	piano: str
	#: The base's string -> the vertical's, both in English.
	parole: Mapping[str, str] = field(default_factory=dict)
	#: The base's places it hides, because it shows its own instead.
	nasconde: frozenset[str] = frozenset()
	#: The key of its brand (`crm.marchio`): the product's name, icon, logo, favicon
	#: and colours wherever it is on.
	marchio: str | None = None
	#: The invoicing profile of its trade (`crm.invoicing.engine.voci`): with the
	#: clinic on, "sanitario" - only the choices a healthcare practice meets, and the
	#: healthcare settings ready.
	fatturazione: str | None = None


_verticali: dict[str, Verticale] = {}


def registra_verticale(verticale: Verticale) -> None:
	_verticali[verticale.chiave] = verticale


def attiva() -> Verticale | None:
	"""The vertical this site's plan has on, in trial or read only: a module that
	ended still holds its trade's data, and speaks its words."""
	from crm.permissions import livelli

	livelli.carica()
	moduli = livelli.moduli_attivi()
	for verticale in _verticali.values():
		if livelli.stato_modulo(verticale.piano, moduli) != livelli.SPENTO:
			return verticale
	return None


def parole() -> dict[str, str]:
	"""The vertical's words, in English: the base's string -> its own."""
	verticale = attiva()
	return dict(verticale.parole) if verticale else {}


def parola(testo: str) -> str:
	"""A string of the base, in the site's words and the session's language."""
	from frappe import _

	return _(parole().get(testo, testo))


def traduttore():
	"""Strings of the base - lazy (`_lt`) or plain English - in the site's words and
	the session's language, the vertical's words read once: for a list of many, as
	the dashboard's widgets."""
	from frappe import _

	sue = parole()

	def traduci(testo) -> str:
		inglese = str(getattr(testo, "msg", testo))
		return _(sue.get(inglese, inglese))

	return traduci


def nascosto(luogo: str) -> bool:
	"""Whether the vertical hides this place of the base."""
	verticale = attiva()
	return bool(verticale and luogo in verticale.nasconde)


def per_il_boot() -> dict:
	"""What the SPA needs: the words already in the session's language, keyed by
	the base's string, to lay over its translations; the places hidden."""
	from frappe import _

	verticale = attiva()
	if not verticale:
		return {"key": None, "words": {}, "hidden": []}
	return {
		"key": verticale.chiave,
		"words": {base: _(sua) for base, sua in verticale.parole.items()},
		"hidden": sorted(verticale.nasconde),
	}
