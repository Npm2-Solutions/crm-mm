# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A person is added without a company (10/10/2026).

«Aggiungi una persona» asked, after the name, the mobile and the email, for seven
fields of a company - its website, revenue already at «0,00 €», employees already
at «1-10», sector, LinkedIn, Twitter, Facebook - in three columns read in zig-zag:
a medical centre adds patients. Two to a row now (name and surname, mobile and
email, gender and title), and the company only by its name, for whoever works for
one the centre has an agreement with.

As a new site has them (`crm.install.LEAD_QUICK_ENTRY`). Only a section whose
fields are still as they were shipped changes: one the centre changed is the
centre's, and what the centre set around the fields (a title, folding, hidden)
stays.
"""

import json

import frappe

from crm.install import LEAD_QUICK_ENTRY

NOME = "CRM Lead-Quick Entry"

# the sections as they were shipped, column by column
PERSONA_PRIMA = [["salutation"], ["first_name"], ["last_name"]]
RECAPITI_PRIMA = [["mobile_no"], ["email"], ["gender"]]
AZIENDA_PRIMA = [
	["organization", "territory"],
	["website", "annual_revenue", "company_description"],
	["no_of_employees", "industry", "linkedin", "twitter", "facebook"],
]


def _colonne(sezione) -> list:
	return [colonna.get("fields") for colonna in sezione.get("columns", [])]


def _nuova(nome) -> dict:
	return next(s for s in json.loads(LEAD_QUICK_ENTRY) if s["name"] == nome)


def _come_il_centro(nuova, vecchia, senza=()) -> dict:
	"""The shipped section in its new shape, with what the centre set on the old
	one around its fields: its title, whether it folds, hides or is fixed."""
	tenute = {k: v for k, v in vecchia.items() if k not in ("name", "columns", *senza)}
	return {**nuova, **tenute}


def _rifai(sezioni) -> bool:
	"""The shipped sections in their new shape, in a list of sections. Tells
	whether anything changed."""
	cambiato = False
	nomi = [s.get("name") for s in sezioni]
	if "person_section" in nomi and "person_contacts_section" in nomi:
		i = nomi.index("person_section")
		j = nomi.index("person_contacts_section")
		if j == i + 1 and _colonne(sezioni[i]) == PERSONA_PRIMA and _colonne(sezioni[j]) == RECAPITI_PRIMA:
			persona, recapiti = sezioni[i], sezioni[j]
			sezioni[i : j + 1] = [
				_come_il_centro(_nuova("person_section"), persona),
				_come_il_centro(_nuova("person_contacts_section"), recapiti),
				# the new row of the two: hidden or fixed as the row it comes out
				# of, never a second time under its title
				_come_il_centro(_nuova("person_more_section"), recapiti, senza=("label",)),
			]
			cambiato = True
	for k, sezione in enumerate(sezioni):
		if sezione.get("name") == "organization_section" and _colonne(sezione) == AZIENDA_PRIMA:
			sezioni[k] = _come_il_centro(_nuova("organization_section"), sezione)
			cambiato = True
	return cambiato


def _elenchi(disposizione) -> list:
	"""The lists of sections of a layout: the old format is one, the new one a
	list of tabs holding them."""
	if any("sections" in voce for voce in disposizione):
		return [scheda["sections"] for scheda in disposizione if "sections" in scheda]
	return [disposizione]


def execute():
	if not frappe.db.exists("CRM Fields Layout", NOME):
		return
	doc = frappe.get_doc("CRM Fields Layout", NOME)
	try:
		disposizione = json.loads(doc.layout or "[]")
	except (TypeError, ValueError):
		return
	if any([_rifai(elenco) for elenco in _elenchi(disposizione)]):
		doc.layout = json.dumps(disposizione)
		doc.save(ignore_permissions=True)
