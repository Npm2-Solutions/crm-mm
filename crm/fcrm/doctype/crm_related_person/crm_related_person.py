# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Two people who belong together: parent and child, partners, guardian and ward.

One row per pair, from the side of the one who is looked after (`crm.persone.legami`):
`related_person` is `relation` to `person`, and pays, books or acts for them. The
person's page reads it from either side; the booking pages use it to tell a mother
from the child she books for, on the email they share.
"""

import frappe
from frappe import _
from frappe.model.document import Document

from crm.persone import legami


class CRMRelatedPerson(Document):
	def validate(self):
		if self.person == self.related_person:
			frappe.throw(_("A person is not linked to themselves"))
		if self.relation not in legami.RELAZIONI:
			frappe.throw(_("Unknown relation: {0}").format(self.relation))
		self.controlla_coppia()

	def controlla_coppia(self):
		"""One row per pair, whichever way it was written: two would disagree."""
		altra = frappe.db.get_value(
			self.doctype,
			{
				"name": ("!=", self.name or ""),
				"person": ("in", (self.person, self.related_person)),
				"related_person": ("in", (self.person, self.related_person)),
			},
			"name",
		)
		if altra:
			frappe.throw(
				_("{0} and {1} are already linked").format(
					self.person_name or self.person, self.related_person_name or self.related_person
				),
				frappe.DuplicateEntryError,
			)


def on_doctype_update():
	frappe.db.add_unique("CRM Related Person", ["person", "related_person"], constraint_name="unique_pair")
