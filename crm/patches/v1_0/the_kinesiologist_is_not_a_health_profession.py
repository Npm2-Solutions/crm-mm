# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The kinesiologist shipped in the healthcare register: a health profession, and
the Sistema TS's «health professional». The Ministry of Health says it is not one
(Ris. AdE 9/2026: art. 41 D.Lgs. 36/2021, physical activity for wellbeing, never
care), and with the clinic on whatever a health professional writes is health
data: a kinesiologist's trainings were read like a clinical record, and they
made their people patients. It is now invoicing's ordinary non-regulated
profession; the stored record takes it, where it still is what shipped - taxed,
reporting to nobody - and what a kinesiologist wrote takes the mark again by the
rules of its kind. The patients already made stay: a patient stays a patient."""

import frappe

QUALIFICA = "CRM Professional Qualification"
CODICE = "chinesiologo"


def execute():
	attuale = frappe.db.get_value(QUALIFICA, CODICE, ["category", "vat_exempt", "ts_required"], as_dict=True)
	if not attuale or attuale.category != "sanitaria" or attuale.vat_exempt or attuale.ts_required:
		return
	frappe.db.set_value(
		QUALIFICA,
		CODICE,
		{"category": "non_ordinistica", "sender_category": "non_sanitario", "is_healthcare": 0},
		update_modified=False,
	)

	from crm import registrazione
	from crm.documenti import api as documenti
	from crm.piani import api as piani
	from crm.piani import programmi
	from crm.preventivi import api as preventivi

	# the kinds' own marks are the modules' registries
	registrazione.carica()
	# the plans before the programmes, which carry the mark of a stage's plan
	for doctype, marca in (
		("CRM Personal Plan", piani.marca),
		("CRM Document", documenti.marca),
		("CRM Quote", preventivi.marca),
		("CRM Programme", programmi.marca),
	):
		for nome in frappe.get_all(doctype, filters={"discipline": CODICE, "clinical": 1}, pluck="name"):
			doc = frappe.get_doc(doctype, nome)
			marca(doc)
			if not doc.clinical:
				frappe.db.set_value(doctype, nome, "clinical", 0, update_modified=False)
