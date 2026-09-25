# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Seeding the thirty-six this module adds.

The register itself is invoicing's and it seeds its own twenty. This adds the
healthcare half to the same table, so a mixed practice sees one list and not two.
"""

from __future__ import annotations

import frappe

from crm.invoicing.install import campi_qualifica
from crm.tessera_sanitaria.engine.professioni import elenco


def semina_qualifiche() -> int:
	"""Create the shipped register as records, once.

	Existing codes are never touched. The file is where the research lives; the
	records are what the practice runs on, and the practice wins.

	The shared columns come from invoicing, which owns the doctype. The four added
	here are the four only this module can fill, and they are the reason the overlay
	is written this way round: invoicing reading them off an ordinary `Professione`
	is an `AttributeError` in `after_install`.
	"""
	creati = 0
	for professione in elenco():
		if frappe.db.exists("CRM Professional Qualification", professione.codice):
			continue
		frappe.get_doc(
			campi_qualifica(professione)
			| {
				"sender_category": professione.soggetto_inviante,
				"is_healthcare": int(professione.sanitaria),
				"ts_required": int(professione.obbligo_ts),
				"ts_required_since": professione.obbligo_ts_dal or 0,
			}
		).insert(ignore_permissions=True)
		creati += 1
	return creati
