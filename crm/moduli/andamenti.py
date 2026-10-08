# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A person's questionnaires followed over time: each score's total, form after
form (`andamenti_regole`), for the card on the person's Forms tab - in the
clinic's summary where the clinic is on.

Only what the session reads: the person, through `frappe.get_list`'s rules; a
form with health data only for the care team (`compilazioni.condizioni_per`),
and its reading in the access log, as the record's. A module adds its own signed
answers with `registra_fonte` (the clinic: the visits on its clinical sheets,
read by the dossier's rules).
"""

from __future__ import annotations

import json
from collections.abc import Callable

import frappe
from frappe.utils import cint

from crm.moduli import andamenti_regole, modelli
from crm.permissions import livelli

MODULO = "CRM Form"

#: Who else has signed answers on templates: (lead) -> list of `andamenti_regole.serie`'s rows.
_fonti: list[Callable[[str], list[dict]]] = []


def registra_fonte(fonte: Callable[[str], list[dict]]) -> None:
	if fonte not in _fonti:
		_fonti.append(fonte)


def _schema(versione: str, cache: dict) -> dict:
	if versione not in cache:
		cache[versione] = modelli.carica_schema(frappe.get_cached_value(modelli.VERSIONE, versione, "schema"))
	return cache[versione]


def ha_punteggi(schema: dict) -> bool:
	return any(campo.get("type") == "score" for campo in andamenti_regole.S.campi(schema))


def dai_moduli(lead: str) -> list[dict]:
	"""The person's signed forms whose version has a score, as the session reads them."""
	schemi: dict = {}
	compilati = []
	for riga in frappe.get_list(
		MODULO,
		filters={"lead": lead, "docstatus": 1},
		fields=["name", "template", "template_version", "title", "signed_on", "answers", "clinical"],
		order_by="signed_on asc",
	):
		schema = _schema(riga.template_version, schemi)
		if not ha_punteggi(schema):
			continue
		if cint(riga.clinical):
			# health data read: the access log says who, as for the record
			frappe.get_doc(MODULO, riga.name).add_viewed()
		compilati.append(
			{
				"name": riga.name,
				"template": riga.template,
				"title": riga.title,
				"date": riga.signed_on,
				"schema": schema,
				"answers": json.loads(riga.answers or "{}")
				if isinstance(riga.answers, str)
				else riga.answers,
				"kind": "form",
			}
		)
	return compilati


@frappe.whitelist()
def get_trends(lead: str) -> list[dict]:
	"""Each score of the person's questionnaires over time, oldest first."""
	livelli.verifica_nel_crm("moduli.vedi")
	frappe.has_permission("CRM Lead", "read", doc=lead, throw=True)
	compilati = dai_moduli(lead)
	for fonte in _fonti:
		compilati += fonte(lead)
	return andamenti_regole.serie(compilati)
