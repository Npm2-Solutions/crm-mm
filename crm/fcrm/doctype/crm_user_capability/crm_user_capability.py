# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""An optional capability turned on for one person.

Some rows of doc 30's matrix read "a scelta": off by default, and the Manager turns
them on for that person - booking over a conflict, sending to the SdI, writing
social drafts. They cannot be roles: Frappe rebuilds a profiled user's roles from
their levels at every save, and a role added by hand would vanish. So they live
here, and `crm.permissions.livelli.capacita_di` adds them.
"""

import frappe
from frappe import _
from frappe.model.document import Document

from crm.permissions import livelli


class CRMUserCapability(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		capability: DF.Data
		enabled: DF.Check
		granted_by: DF.Link | None
		user: DF.Link
	# end: auto-generated types

	def autoname(self):
		# one row per person and capability, enforced by the name
		self.name = f"{self.user}|{self.capability}"

	def validate(self):
		livelli.carica()
		if self.capability not in livelli.capacita_registrate():
			frappe.throw(_("{0} is not a capability").format(frappe.bold(self.capability)))

	def on_update(self):
		livelli.dimentica_cache()

	def on_trash(self):
		livelli.dimentica_cache()
