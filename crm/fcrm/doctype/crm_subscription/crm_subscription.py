# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A person's subscription: a type sold from a day, its terms as they were then,
its suspensions and instalments (`crm.scheduling.abbonamenti`)."""

import frappe
from frappe.model.document import Document

from crm.scheduling import abbonamenti


class CRMSubscription(Document):
	def validate(self):
		abbonamenti.prepara(self)

	def on_trash(self):
		# its person's places are priced by the price list again
		for riga in abbonamenti.ingressi(self.name):
			abbonamenti._metti(riga["name"], self.lead, None)
		if self.renewal_of and frappe.db.exists("CRM Subscription", self.renewal_of):
			frappe.db.set_value(
				"CRM Subscription", self.renewal_of, "renewed_by", None, update_modified=False
			)
