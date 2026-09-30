# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The places other modules add to the client area.

The area's own places - home, agenda, messages, invoices - are always there. A
module adds its own the way it adds capabilities (docs/gestionale-medico/design.md,
"Tre strati"): the documents given online and the plans, the clinic its care plans.
For each person the session sees, ``per_persona`` says what the place has for
them, and the app shows it when that is something: "Plans" only to who follows
one now.

A place that fails is hidden and logged: the rest of the area still opens.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import frappe


@dataclass(frozen=True)
class Sezione:
	chiave: str
	#: What the place has for this person (a CRM Lead): shown when truthy.
	per_persona: Callable[[str], Any]


_sezioni: dict[str, Sezione] = {}


def registra_sezione(sezione: Sezione) -> None:
	_sezioni[sezione.chiave] = sezione


def sezioni() -> list[Sezione]:
	return list(_sezioni.values())


def per_persona(lead: str) -> dict[str, Any]:
	"""Every registered place, for one person."""
	from crm.permissions import livelli

	livelli.carica()
	fatto: dict[str, Any] = {}
	for sezione in _sezioni.values():
		try:
			fatto[sezione.chiave] = sezione.per_persona(lead)
		except Exception:
			frappe.log_error(
				title=f"Area place {sezione.chiave} not read",
				reference_doctype="CRM Lead",
				reference_name=lead,
			)
			fatto[sezione.chiave] = False
	return fatto
