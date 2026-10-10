# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A person reads in order on a phone too (04/10/2026).

A phone reads a section column by column. The person's fields were laid out for a
computer's rows, and read out of order:

- «Aggiungi una persona», and the person of «Crea una trattativa»: one section of
  three columns of two - title and email, name and mobile, surname and gender -
  read «Title, Email, Name, Mobile, Surname, Gender». Each row is a section of its
  own now: title, name, surname; mobile, email, gender.
- The person's Data tab: name, mobile and title; surname, phone and gender;
  email - read «Name, Mobile, Title, Surname...». A column per kind now: the name,
  how to reach them, the rest, as the panel on the side reads.

As a new site has them (`crm.install`). Only a section still as it was shipped
changes: one the centre changed is the centre's, and the rest of a layout stays as
the centre left it.
"""

import json

import frappe

from crm.install import DEAL_QUICK_ENTRY, LEAD_DATA_FIELDS

# the quick entries' section as it was shipped, column by column
PRIMA = [["salutation", "email"], ["first_name", "mobile_no"], ["last_name", "gender"]]

# «Aggiungi una persona»'s two rows as this patch shipped them: the install's
# moved on (`a_person_is_added_without_a_company`, which takes these further),
# and reading them from there split a site's person into rows without gender
# and title
PERSONA_DEL_04_10 = json.dumps(
	[
		{
			"name": "person_section",
			"columns": [
				{"name": "column_5jrk", "fields": ["salutation"]},
				{"name": "column_5CPV", "fields": ["first_name"]},
				{"name": "column_gXOy", "fields": ["last_name"]},
			],
		},
		{
			"name": "person_contacts_section",
			"hideBorder": True,
			"columns": [
				{"name": "column_Mb7q", "fields": ["mobile_no"]},
				{"name": "column_Em2w", "fields": ["email"]},
				{"name": "column_Gn4z", "fields": ["gender"]},
			],
		},
	]
)

# each quick entry: the section to split and the two rows that take its place
RIGHE = {
	"CRM Lead-Quick Entry": (PERSONA_DEL_04_10, "person_section", "person_contacts_section"),
	"CRM Deal-Quick Entry": (DEAL_QUICK_ENTRY, "contact_details_section", "contact_details_more_section"),
}

# the Data tab's person, as `the_person_first_on_their_page` left it
DATI = "CRM Lead-Data Fields"
PRIMA_DATI = [["first_name", "mobile_no", "salutation"], ["last_name", "phone", "gender"], ["email"]]


def _colonne(sezione) -> list:
	return [colonna.get("fields") for colonna in sezione.get("columns", [])]


def _a_righe(sezioni, nome, righe) -> bool:
	"""Puts the two rows in place of the shipped section, in a list of sections.
	Tells whether it found one."""
	for i, sezione in enumerate(sezioni):
		if sezione.get("name") == nome and _colonne(sezione) == PRIMA:
			# a hidden or fixed section keeps being so, row by row
			tenute = {chiave: sezione[chiave] for chiave in ("hidden", "editable") if chiave in sezione}
			sezioni[i : i + 1] = [{**riga, **tenute} for riga in righe]
			return True
	return False


def _per_tipo(sezioni) -> bool:
	"""The Data tab's person in a column per kind, its label and state kept."""
	spedita = next(s for s in json.loads(LEAD_DATA_FIELDS) if s["name"] == "person_section")
	for sezione in sezioni:
		if sezione.get("name") == "person_section" and _colonne(sezione) == PRIMA_DATI:
			sezione["columns"] = spedita["columns"]
			return True
	return False


def _elenchi(disposizione) -> list:
	"""The lists of sections of a layout: the old format is one, the new one a
	list of tabs holding them."""
	if any("sections" in voce for voce in disposizione):
		return [scheda["sections"] for scheda in disposizione if "sections" in scheda]
	return [disposizione]


def _cambia(nome, come) -> None:
	if not frappe.db.exists("CRM Fields Layout", nome):
		return
	doc = frappe.get_doc("CRM Fields Layout", nome)
	try:
		disposizione = json.loads(doc.layout or "[]")
	except (TypeError, ValueError):
		return
	if any(come(elenco) for elenco in _elenchi(disposizione)):
		doc.layout = json.dumps(disposizione)
		doc.save(ignore_permissions=True)


def execute():
	for nome, (spedito, sezione, seconda) in RIGHE.items():
		righe = [s for s in json.loads(spedito) if s["name"] in (sezione, seconda)]
		_cambia(nome, lambda elenco, sezione=sezione, righe=righe: _a_righe(elenco, sezione, righe))
	_cambia(DATI, _per_tipo)
