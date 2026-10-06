# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMArchivedFile(Document):
	"""A private file whose content is on the agency's archive (crm/archivio):
	written and read only there, named by its address's fingerprint."""

	def autoname(self):
		from crm.archivio.archivio import nome_di

		self.name = nome_di(self.file_url)
