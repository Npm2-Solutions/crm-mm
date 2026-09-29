# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""What switching the clinic on makes, for the sites where it was on already.

Switching the clinic on creates the two pipelines of a medical centre and the
centre's dashboard (`crm.clinica.eventi.piano_aggiornato`). A site that had it on
before those existed gets them here, once; a site without the clinic gets nothing.
"""

import frappe


def execute():
	from crm.clinica import paziente, pipeline
	from crm.dashboard import features, store
	from crm.registrazione import carica

	carica()
	if not paziente.clinica_accesa():
		return
	pipeline.crea_pipeline()
	features.forget()
	store.create_template_dashboards(only=("medical_centre",))
	frappe.db.commit()  # nosemgrep: frappe-manual-commit — a patch, run once
