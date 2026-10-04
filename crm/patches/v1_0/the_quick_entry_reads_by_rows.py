# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A new person, and a deal's person, read by rows on a phone (04/10/2026).

The person's fields were one section of three columns of two - title and email,
name and mobile, surname and gender - which a computer draws as two rows and a
phone reads column by column: «Title, Email, Name, Mobile, Surname, Gender». Each
row is a section of its own now, as a new site has them (`crm.install`): title,
name, surname; mobile, email, gender.

Only a section still as it was shipped is split: one the centre changed is the
centre's, and the rest of the layout stays as the centre left it.
"""

import json

import frappe

from crm.install import DEAL_QUICK_ENTRY, LEAD_QUICK_ENTRY

# the section as it was shipped, column by column
PRIMA = [["salutation", "email"], ["first_name", "mobile_no"], ["last_name", "gender"]]

# each layout: the section to split and the two rows that take its place
RIGHE = {
	"CRM Lead-Quick Entry": (LEAD_QUICK_ENTRY, "person_section", "person_contacts_section"),
	"CRM Deal-Quick Entry": (DEAL_QUICK_ENTRY, "contact_details_section", "contact_details_more_section"),
}


def _come_spedita(sezione) -> bool:
	return [colonna.get("fields") for colonna in sezione.get("columns", [])] == PRIMA


def _a_righe(sezioni, nome, righe) -> bool:
	"""Puts the two rows in place of the shipped section, in a list of sections.
	Tells whether it found one."""
	for i, sezione in enumerate(sezioni):
		if sezione.get("name") == nome and _come_spedita(sezione):
			# a hidden or fixed section keeps being so, row by row
			tenute = {chiave: sezione[chiave] for chiave in ("hidden", "editable") if chiave in sezione}
			sezioni[i : i + 1] = [{**riga, **tenute} for riga in righe]
			return True
	return False


def execute():
	for nome, (spedito, sezione, seconda) in RIGHE.items():
		if not frappe.db.exists("CRM Fields Layout", nome):
			continue
		doc = frappe.get_doc("CRM Fields Layout", nome)
		try:
			disposizione = json.loads(doc.layout or "[]")
		except (TypeError, ValueError):
			continue
		righe = [s for s in json.loads(spedito) if s["name"] in (sezione, seconda)]
		# the old format is a list of sections, the new one a list of tabs holding them
		elenchi = (
			[scheda["sections"] for scheda in disposizione if "sections" in scheda]
			if any("sections" in voce for voce in disposizione)
			else [disposizione]
		)
		if any(_a_righe(elenco, sezione, righe) for elenco in elenchi):
			doc.layout = json.dumps(disposizione)
			doc.save(ignore_permissions=True)
