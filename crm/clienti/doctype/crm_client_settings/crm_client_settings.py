# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Where new clients meet the sales side: which pipeline is the new clients' one, and
where a booking moves its deals (`crm.clienti.pipeline`)."""

from frappe.model.document import Document


class CRMClientSettings(Document):
	def validate(self):
		from crm.clienti import pipeline

		pipeline.controlla(self)
