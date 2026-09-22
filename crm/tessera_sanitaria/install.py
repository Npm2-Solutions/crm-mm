# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Seeding what this module brings with it.

The register of qualifications is this module's, so creating it is this module's
job. Invoicing installs and runs without any of it.
"""

from __future__ import annotations

import frappe

from crm.tessera_sanitaria.engine.professioni import elenco


def semina_qualifiche() -> int:
	"""Create the shipped register as records, once.

	Existing codes are never touched. The file is where the research lives; the
	records are what the practice runs on, and the practice wins.
	"""
	creati = 0
	for professione in elenco():
		if frappe.db.exists("CRM Professional Qualification", professione.codice):
			continue
		frappe.get_doc(
			{
				"doctype": "CRM Professional Qualification",
				"code": professione.codice,
				"qualification_name": professione.etichetta,
				"category": professione.categoria,
				"sender_category": professione.soggetto_inviante,
				"is_healthcare": int(professione.sanitaria),
				"vat_exempt": int(professione.esente_iva),
				"exemption_reference": professione.riferimento_esenzione,
				"ts_required": int(professione.obbligo_ts),
				"ts_required_since": professione.obbligo_ts_dal or 0,
				"sdi_rule": professione.regola_sdi,
				"fund_type": professione.cassa,
				"fund_rate": float(professione.cassa_percentuale or 0),
				"fund_mandatory": int(professione.cassa_obbligatoria),
				"fund_subject_to_withholding": int(professione.cassa_soggetta_a_ritenuta),
				"withholding_applies": int(professione.ritenuta_applicabile),
				"withholding_rate": float(professione.ritenuta_aliquota),
				"withholding_type": professione.tipo_ritenuta,
				"payment_reason": professione.causale_pagamento,
				"default_vat_rate": float(professione.aliquota_iva_default),
				"needs_verification": "\n".join(professione.da_verificare),
				"notes": professione.note,
				"enabled": 1,
			}
		).insert(ignore_permissions=True)
		creati += 1
	return creati
