# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Seeding: the roles, and the qualification register.

The register ships as data, not as a fixture that a `bench migrate` overwrites: a
practice that corrects an entry has to keep the correction. So a code that already
exists is left alone, and only a missing one is created.
"""

from __future__ import annotations

import frappe

from crm.invoicing.engine.professioni import Professione, elenco

RUOLI = (
	("Invoicing Manager", "Issues, cancels and transmits invoices, and configures the register."),
	("Invoicing User", "Reads invoices and the register."),
)


def crea_ruoli() -> None:
	for nome, descrizione in RUOLI:
		if frappe.db.exists("Role", nome):
			continue
		frappe.get_doc(
			{
				"doctype": "Role",
				"role_name": nome,
				"desk_access": 1,
				"is_custom": 1,
				"search_bar": 1,
				"notifications": 1,
				"list_sidebar": 1,
				"form_sidebar": 1,
				"report": 1,
				"dashboard": 1,
				"description": descrizione,
			}
		).insert(ignore_permissions=True)


def imposta_predefiniti() -> None:
	impostazioni = frappe.get_single("CRM Invoicing Settings")
	if impostazioni.ts_silence_days:
		return
	impostazioni.ts_silence_days = 30
	impostazioni.certificate_warning_days = 90
	impostazioni.advances_in_stamp_base = 1
	impostazioni.attach_pdf = 1
	impostazioni.save(ignore_permissions=True)


def dopo_installazione() -> None:
	crea_ruoli()
	semina_qualifiche()
	imposta_predefiniti()
	# No request here, and a later failure must not undo the seeding: a half-created
	# register is worse than none.
	frappe.db.commit()  # nosemgrep: frappe-manual-commit


def campi_qualifica(professione: Professione) -> dict:
	"""The columns a qualification has whatever it does for a living.

	Shared with the healthcare register, which overlays the four columns only its own
	dataclass can fill. It is one function rather than two copies because two copies
	is exactly how a healthcare-only field ended up being read off an ordinary
	`Professione`: an `AttributeError` inside `after_install`, which no suite here
	can reach and which leaves the site half-installed.

	The four it omits - `sender_category`, `is_healthcare`, `ts_required`,
	`ts_required_since` - are left to the doctype's own defaults, and those defaults
	say the true thing about a lawyer: not healthcare, reports to nobody.
	"""
	return {
		"doctype": "CRM Professional Qualification",
		"code": professione.codice,
		"qualification_name": professione.etichetta,
		"category": professione.categoria,
		"vat_exempt": int(professione.esente_iva),
		"exemption_reference": professione.riferimento_esenzione,
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


def semina_qualifiche() -> int:
	"""Create the shipped register as records, once.

	Existing codes are never touched. The file is where the research lives; the
	records are what the practice runs on, and the practice wins.
	"""
	creati = 0
	for professione in elenco():
		if frappe.db.exists("CRM Professional Qualification", professione.codice):
			continue
		frappe.get_doc(campi_qualifica(professione)).insert(ignore_permissions=True)
		creati += 1
	return creati
