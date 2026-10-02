# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A person's page starts with the person (02/10/2026).

The layouts the CRM was born with opened a person's panel and their Data tab on a
company's fields - its description, territory, industry, employees - and showed
the person's own name, mobile and email under them. A centre's clients rarely have
a company: the person comes first now, then where they came from and whose they
are, and the company closed at the end (`crm.install.LEAD_SIDE_PANEL`,
`LEAD_DATA_FIELDS`).

A layout the centre has changed is the centre's: only one still as it was shipped
is replaced. The attribution sections the Data tab carries stay where they are.
"""

import json

import frappe

from crm.install import LEAD_DATA_FIELDS, LEAD_SIDE_PANEL

PANNELLO = "CRM Lead-Side Panel"
DATI = "CRM Lead-Data Fields"

# the two layouts as the CRM shipped them, with the fields the enrichment patch
# may have added to them
PRIMA_PANNELLO = [
	{
		"label": "Details",
		"name": "details_section",
		"opened": True,
		"columns": [
			{
				"name": "column_kl92",
				"fields": [
					"organization",
					"company_description",
					"website",
					"territory",
					"industry",
					"no_of_employees",
					"job_title",
					"source",
					"lead_owner",
					"linkedin",
					"twitter",
					"facebook",
				],
			}
		],
	},
	{
		"label": "Person",
		"name": "person_section",
		"opened": True,
		"columns": [
			{"name": "column_XmW2", "fields": ["salutation", "first_name", "last_name", "email", "mobile_no"]}
		],
	},
]
PRIMA_DATI = [
	{
		"label": "Details",
		"name": "details_section",
		"opened": True,
		"columns": [
			{
				"name": "column_ZgLG",
				"fields": ["organization", "company_description", "industry", "no_of_employees"],
			},
			{"name": "column_TbYq", "fields": ["website", "linkedin", "twitter", "facebook", "job_title"]},
			{"name": "column_OKSX", "fields": ["territory", "source", "lead_owner"]},
		],
	},
	{
		"label": "Person",
		"name": "person_section",
		"opened": True,
		"columns": [
			{"name": "column_6c5g", "fields": ["salutation", "email"]},
			{"name": "column_1n7Q", "fields": ["first_name", "mobile_no"]},
			{"name": "column_cT6C", "fields": ["last_name"]},
		],
	},
]


def _campi(sezioni) -> list:
	"""The fields of some sections, column by column, in order."""
	return [
		campo
		for sezione in sezioni
		for colonna in sezione.get("columns", [])
		for campo in colonna.get("fields", [])
	]


def _come_spedito(sezioni, prima) -> bool:
	"""Whether these sections are the shipped ones: the same sections with the
	same fields, whichever order the enrichment patch appended its fields in."""
	if [s.get("name") for s in sezioni] != [s["name"] for s in prima]:
		return False
	return sorted(_campi(sezioni)) == sorted(_campi(prima))


def _leggi(nome):
	if not frappe.db.exists("CRM Fields Layout", nome):
		return None, None
	doc = frappe.get_doc("CRM Fields Layout", nome)
	try:
		return doc, json.loads(doc.layout or "[]")
	except (TypeError, ValueError):
		return None, None


def execute():
	doc, sezioni = _leggi(PANNELLO)
	if doc and _come_spedito(sezioni, PRIMA_PANNELLO):
		doc.layout = LEAD_SIDE_PANEL
		doc.save(ignore_permissions=True)

	doc, sezioni = _leggi(DATI)
	# the Data tab carries the attribution sections after the two shipped ones
	if doc and _come_spedito(sezioni[:2], PRIMA_DATI):
		doc.layout = json.dumps(json.loads(LEAD_DATA_FIELDS) + sezioni[2:])
		doc.save(ignore_permissions=True)
