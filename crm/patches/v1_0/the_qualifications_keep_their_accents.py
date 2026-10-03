# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Two qualifications shipped with their accents written as apostrophes
("Societa' o impresa di servizi"), and the professionals' list showed them so. The
register keeps what a practice corrected: only a name still as it was shipped is
written again, the way the registers now ship it."""

import frappe

#: code -> the name as it was shipped
COME_ERANO = {
	"societa_servizi": "Societa' o impresa di servizi",
	"terapista_neuro_psicomotricita": "Terapista della neuro e psicomotricita' dell'eta' evolutiva",
}


def execute():
	from crm.invoicing.engine import professioni
	from crm.tessera_sanitaria.engine import professioni as sanitarie

	nuovi = {p.codice: p.etichetta for p in (*professioni.elenco(), *sanitarie.elenco())}
	for codice, prima in COME_ERANO.items():
		frappe.db.set_value(
			"CRM Professional Qualification",
			{"name": codice, "qualification_name": prima},
			"qualification_name",
			nuovi[codice],
			update_modified=False,
		)
