# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Reading the stored register, for the rows that carry a healthcare duty.

The table is invoicing's and so is the plain reading of it. What is here is the
half that only means something with this module installed: a row that reports to
the Sistema TS needs a class that can say so, and that class does not exist
without this file.

So the traffic runs the right way. Invoicing never reaches for a healthcare class
it may not have; this module reaches for invoicing's table, which is always there.
A row that carries no healthcare duty is refused with `KeyError`, and the chain in
`crm.invoicing.estensioni` hands it to invoicing's own reader.
"""

from __future__ import annotations

import frappe

from crm.invoicing.registro import CAMPI, da_record
from crm.tessera_sanitaria.engine.professioni import ProfessioneSanitaria


def _sanitaria(record: dict) -> bool:
	return bool(record.get("ts_required")) or record.get("sender_category") not in (
		None,
		"",
		"non_sanitario",
	)


def professione(codice: str | None) -> ProfessioneSanitaria:
	"""A stored row that carries a healthcare duty, or KeyError."""
	if not codice:
		raise KeyError("No qualification on the line")
	record = frappe.db.get_value("CRM Professional Qualification", codice, CAMPI, as_dict=True)
	if not record or not record.get("enabled") or not _sanitaria(record):
		raise KeyError(codice)

	base = da_record(record)
	return ProfessioneSanitaria(
		**{campo: getattr(base, campo) for campo in base.__dataclass_fields__},
		soggetto_inviante=record.get("sender_category") or "non_sanitario",
		obbligo_ts=bool(record.get("ts_required")),
		obbligo_ts_dal=record.get("ts_required_since") or None,
	)


def risolutore():
	return professione
