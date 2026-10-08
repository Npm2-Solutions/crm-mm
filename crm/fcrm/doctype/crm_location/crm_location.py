# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from crm.scheduling import sedi
from crm.scheduling import sedi_regole as R


class CRMLocation(Document):
	def validate(self):
		self.location_name = " ".join((self.location_name or "").split())
		self.province = (self.province or "").strip().upper()[:2] or None
		self.pincode = (self.pincode or "").strip() or None
		if self.map_link and not R.link_valido(self.map_link):
			frappe.throw(_("The map link must be an address starting with https://"))

	def on_update(self):
		sedi.dimentica()

	def on_trash(self):
		# a location with rooms or appointments keeps their history: switched off instead
		for doctype, campo in (("CRM Resource", "centre_location"), ("CRM Appointment", "centre_location")):
			if frappe.db.exists(doctype, {campo: self.name}):
				frappe.throw(
					_("{0} has rooms or appointments: switch it off instead of deleting it").format(
						self.location_name
					)
				)
		sedi.dimentica()
