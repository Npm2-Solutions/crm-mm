# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A form template: the draft the centre works on (`crm.moduli.modelli`).

People never fill the draft: they fill a published version, which does not
change. So the draft can be half-written; publishing is what asks it to be right.
"""

import frappe
from frappe import _
from frappe.model.document import Document

from crm.moduli import modelli


class CRMFormTemplate(Document):
	def validate(self):
		self.title = (self.title or "").strip()
		if not self.title:
			frappe.throw(_("A form needs a title"))
		self.use = self.use or modelli.FORMA
		uso = next((uso for uso in modelli.usi() if uso.chiave == self.use), None)
		if not uso:
			frappe.throw(_("{0} is not a use of forms on this site").format(frappe.bold(self.use)))
		if uso.clinico:
			# a use that records health data, always
			self.clinical = 1
		if not uso.della_persona:
			# a sheet is written by the operator at the desk: nobody owes it, nothing sends it
			self.ask_on = "By hand"
			self.send_before = 0
		if self.clinical and not modelli.dato_clinico_disponibile():
			# the mark means something only where the clinic is on: elsewhere it
			# would promise a protection nobody gives
			frappe.throw(_("Health data is for the medical centre, which is off on this site"))
		schema = modelli.carica_schema(self.schema)
		if not isinstance(schema.get("sections"), list):
			frappe.throw(_("This is not a form"))
		if self.ask_on != "Services":
			self.set("services", [])

	def on_trash(self):
		if frappe.db.exists(modelli.VERSIONE, {"template": self.name}):
			frappe.throw(
				_(
					"{0} has published versions, and what was filled on them points at them: "
					"switch it off instead"
				).format(frappe.bold(self.title)),
				frappe.LinkExistsError,
			)
