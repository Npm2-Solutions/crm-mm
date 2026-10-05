# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The fiscal profile of a person or an organization: one each.

Codice fiscale, VAT number, codice destinatario, PEC and address, written once and
read by every invoice (`crm.invoicing.anagrafica`). It sits outside `CRM Lead` on
purpose: marketing sees the people and has no need to see their codice fiscale,
and the permissions of a separate document can say so.
"""

import frappe
from frappe import _
from frappe.model.document import Document

from crm.invoicing.engine import anagrafica as motore

#: Whose profile it can be. A deal or a contact resolves to one of these.
TITOLARI = ("CRM Lead", "CRM Organization")

# nosemgrep: frappe-breaks-multitenancy — functions, called at each check: nothing of a site is kept
_ERRORI = {
	"fiscal_code": lambda v: _(
		"The codice fiscale {0} is not valid: its last character is computed from the others, and it does not match"
	).format(v.get("fiscal_code")),
	"tax_id": lambda v: _("The VAT number {0} is not well formed for country {1}").format(
		v.get("tax_id"), v.get("country") or motore.PAESE_PREDEFINITO
	),
	"recipient_code": lambda v: _(
		"A codice destinatario has seven characters, six for the public administration"
	),
	"country": lambda v: _("The country is written with two letters, for example IT"),
	"postal_code": lambda v: _("An Italian postal code has five digits"),
	"province": lambda v: _("The province is written with two letters, for example MI"),
}


class CRMBillingProfile(Document):
	def validate(self):
		self.normalizza()
		self.controlla_titolare()
		self.controlla_formati()
		self.leggi_il_codice()

	def normalizza(self):
		for campo, valore in motore.normalizza({c: self.get(c) for c in motore.CAMPI}).items():
			self.set(campo, valore)
		self.country = self.country or motore.PAESE_PREDEFINITO

	def controlla_titolare(self):
		if self.party_type not in TITOLARI:
			frappe.throw(_("Billing details belong to a person or an organization"))
		if not frappe.db.exists(self.party_type, self.party):
			frappe.throw(_("{0} {1} does not exist").format(_(self.party_type), self.party))
		altro = frappe.db.get_value(
			"CRM Billing Profile",
			{"party_type": self.party_type, "party": self.party, "name": ("!=", self.name)},
		)
		if altro:
			frappe.throw(
				_("{0} already has billing details").format(self.party),
				frappe.DuplicateEntryError,
			)
		self.party_name = nome_del_titolare(self.party_type, self.party)

	def controlla_formati(self):
		valori = self.as_dict()
		problemi = [_ERRORI[campo](valori) for campo in motore.errori(valori)]
		if problemi:
			frappe.throw("<br>".join(problemi), title=_("These billing details would not reach an invoice"))

	def leggi_il_codice(self):
		"""Date of birth and sex, from the codice fiscale: never typed, never out of step."""
		dati = motore.dati_dal_codice(self.fiscal_code)
		self.birth_date = dati["birth_date"]
		self.sex = dati["sex"]


def nome_del_titolare(party_type: str, party: str) -> str:
	if party_type == "CRM Lead":
		persona = frappe.db.get_value(
			"CRM Lead", party, ["lead_name", "first_name", "last_name"], as_dict=True
		)
		if persona:
			return (
				persona.lead_name
				or " ".join(p for p in (persona.first_name, persona.last_name) if p)
				or party
			)
	if party_type == "CRM Organization":
		return frappe.db.get_value("CRM Organization", party, "organization_name") or party
	return party


def on_doctype_update():
	# one profile per person or organization, held by the database as well: two
	# desks saving the first invoice of the same patient at the same moment
	frappe.db.add_unique("CRM Billing Profile", ["party_type", "party"], constraint_name="unique_party")
