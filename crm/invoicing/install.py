# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Seeding: the roles, and the qualification register.

The register ships as data, not as a fixture that a `bench migrate` overwrites: a
practice that corrects an entry has to keep the correction. So a code that already
exists is left alone, and only a missing one is created.
"""

from __future__ import annotations

from collections.abc import Iterable

import frappe
from frappe import _

from crm import lingue
from crm.invoicing.engine.professioni import Professione, elenco

QUALIFICA = "CRM Professional Qualification"

#: A shipped qualification's words that are DottorCloud's: its name, its notes, the
#: points an accountant still has to check. Written in the centre's language
#: (`crm.lingue`), and following it while nobody changed them. The English is the
#: code's, the Italian is in it.po by hand: the extraction never sees a variable.
PAROLE = ("qualification_name", "notes", "needs_verification")

#: The languages DottorCloud ships these words in: the code's, and the catalog's.
LINGUE = ("en", "it")

RUOLI = (
	("Invoicing Manager", "Issues, cancels and transmits invoices, and configures the register."),
	("Invoicing User", "Issues invoices and records payments; cancels nothing, transmits only when allowed."),
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
		**parole_di(professione, lingue.del_centro()),
		"enabled": 1,
	}


def parole_di(professione: Professione, lingua: str) -> dict:
	"""A shipped qualification's words in ``lingua``: the name, the notes, the points
	to check one per line."""
	return {
		"qualification_name": _(professione.etichetta, lang=lingua),
		"notes": _(professione.note, lang=lingua) if professione.note else "",
		"needs_verification": "\n".join(_(punto, lang=lingua) for punto in professione.da_verificare),
	}


def nella_lingua(professioni: Iterable[Professione], lingua: str | None = None) -> int:
	"""The shipped qualifications still holding DottorCloud's words in another
	language take the centre's. A word the practice changed stays as written, and
	a qualification it deleted is not made again."""
	lingua = lingua or lingue.del_centro()
	cambiate = 0
	for professione in professioni:
		attuali = frappe.db.get_value(QUALIFICA, professione.codice, list(PAROLE), as_dict=True)
		if not attuali:
			continue
		volute = parole_di(professione, lingua)
		spedite = [parole_di(professione, altra) for altra in LINGUE if altra != lingua]
		nuove = {
			campo: volute[campo]
			for campo in PAROLE
			if (attuali.get(campo) or "").strip() != volute[campo].strip()
			and (attuali.get(campo) or "").strip() in {parole[campo].strip() for parole in spedite}
		}
		if nuove:
			frappe.db.set_value(QUALIFICA, professione.codice, nuove, update_modified=False)
			cambiate += 1
	return cambiate


def qualifiche_nella_lingua(_args=None) -> int:
	"""After a migrate and the setup wizard: invoicing's half of the register in the
	centre's language (the Sistema TS follows its own half)."""
	return nella_lingua(elenco())


def semina_qualifiche() -> int:
	"""Create the shipped register as records, once.

	Existing codes are never touched. The file is where the research lives; the
	records are what the practice runs on, and the practice wins.
	"""
	creati = 0
	for professione in elenco():
		if frappe.db.exists(QUALIFICA, professione.codice):
			continue
		frappe.get_doc(campi_qualifica(professione)).insert(ignore_permissions=True)
		creati += 1
	return creati
