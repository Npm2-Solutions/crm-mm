# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The qualification register, as the practice can edit it.

The engine ships a register in `engine/professioni.py`. That file is the
documented starting point, and it is where the research lives - but the choices
that decide fiscal correctness belong to the practice owner, and while they sat in
a Python file, correcting one meant a developer.

So the shipped register is seeded into `CRM Professional Qualification` records at
install, and from then on the records win. A code that has a record uses the
record; a code that does not falls back to the file; a code in neither raises,
because the catalogue never infers.
"""

from __future__ import annotations

from decimal import Decimal

import frappe
from frappe import _

from crm.invoicing.engine.professioni import Professione
from crm.invoicing.engine.professioni import professione as professione_di_serie

CAMPI = (
	"code",
	"qualification_name",
	"category",
	"sender_category",
	"is_healthcare",
	"vat_exempt",
	"exemption_reference",
	"ts_required",
	"ts_required_since",
	"sdi_rule",
	"fund_type",
	"fund_rate",
	"fund_mandatory",
	"fund_subject_to_withholding",
	"withholding_applies",
	"withholding_rate",
	"withholding_type",
	"payment_reason",
	"default_vat_rate",
	"needs_verification",
	"notes",
	"enabled",
)


def _decimale(valore) -> Decimal | None:
	if valore in (None, "", 0):
		return None
	return Decimal(str(valore))


def da_record(record: dict) -> Professione:
	"""Turn a stored qualification into the dataclass the engine speaks."""
	return Professione(
		codice=record["code"],
		etichetta=record.get("qualification_name") or record["code"],
		categoria=record.get("category") or "non_ordinistica",
		soggetto_inviante=record.get("sender_category") or "non_sanitario",
		esente_iva=bool(record.get("vat_exempt")),
		riferimento_esenzione=record.get("exemption_reference"),
		obbligo_ts=bool(record.get("ts_required")),
		obbligo_ts_dal=record.get("ts_required_since") or None,
		regola_sdi=record.get("sdi_rule") or "obbligatorio",
		cassa=record.get("fund_type") or None,
		cassa_percentuale=_decimale(record.get("fund_rate")),
		cassa_obbligatoria=bool(record.get("fund_mandatory")),
		cassa_soggetta_a_ritenuta=bool(record.get("fund_subject_to_withholding")),
		ritenuta_applicabile=bool(record.get("withholding_applies")),
		ritenuta_aliquota=_decimale(record.get("withholding_rate")) or Decimal("20.00"),
		tipo_ritenuta=record.get("withholding_type") or "RT01",
		causale_pagamento=record.get("payment_reason") or "A",
		aliquota_iva_default=_decimale(record.get("default_vat_rate")) or Decimal("22.00"),
		da_verificare=tuple(filter(None, (record.get("needs_verification") or "").splitlines())),
		note=record.get("notes") or "",
	)


def professione(codice: str | None) -> Professione:
	"""Resolve a qualification code. Records first, shipped register second."""
	if not codice:
		raise KeyError(_("No qualification on the line: the expense type cannot be determined"))
	record = frappe.db.get_value("CRM Professional Qualification", codice, CAMPI, as_dict=True)
	if record:
		if not record.get("enabled"):
			raise KeyError(
				_("The qualification {0} is disabled: re-enable it or pick another one").format(codice)
			)
		return da_record(record)
	return professione_di_serie(codice)


def risolutore():
	"""The resolver to hand the classification engine."""
	return professione


def da_verificare(azienda: str | None = None) -> list[dict]:
	"""Qualifications the accountant still has to sign off.

	Shown as a live checklist rather than a document nobody opens: the list gets
	shorter, and each row says what it costs to leave it open.
	"""
	filtri = {"enabled": 1, "verified": 0, "needs_verification": ["is", "set"]}
	righe = frappe.get_all(
		"CRM Professional Qualification",
		filters=filtri,
		fields=["name", "qualification_name", "needs_verification", "category"],
		order_by="category asc, qualification_name asc",
	)
	if azienda:
		in_uso = set(
			frappe.get_all(
				"CRM Service Provider",
				filters={"enabled": 1},
				pluck="qualification",
			)
		)
		righe = [r for r in righe if r["name"] in in_uso]
	return righe
