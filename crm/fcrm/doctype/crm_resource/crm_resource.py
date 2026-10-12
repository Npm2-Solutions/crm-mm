# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

from crm.scheduling.timeutils import as_time


class CRMResource(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.fcrm.doctype.crm_service_day.crm_service_day import CRMServiceDay

		availability: DF.Table[CRMServiceDay]
		capacity: DF.Int
		color: DF.Color | None
		currency: DF.Link
		description: DF.SmallText | None
		enabled: DF.Check
		holiday_list: DF.Link | None
		hourly_rate: DF.Currency | None
		location: DF.Data | None
		resource_name: DF.Data
		resource_type: DF.Literal["Room", "Equipment", "Vehicle", "Other"]
		seats: DF.Int
	# end: auto-generated types

	def validate(self):
		if cint(self.capacity) < 1:
			self.capacity = 1
		if cint(self.seats) < 0:
			self.seats = 0
		for row in self.availability:
			if as_time(row.start_time) >= as_time(row.end_time):
				frappe.throw(_("Row {0}: start time must be before end time").format(row.idx))

	def on_trash(self):
		"""What still names it refuses in DottorCloud's words: the framework's own
		refusal, which comes after this, names a record's code and links into the
		Desk. Switched off, it is no longer booked and keeps what it was in."""
		nome = frappe.bold(self.resource_name)
		if frappe.db.exists("CRM Appointment Resource", {"resource": self.name}):
			frappe.throw(
				_("{0} has appointments, and they keep it: switch it off to stop booking it").format(nome),
				frappe.LinkExistsError,
			)
		servizio = frappe.db.get_value(
			"CRM Service Resource", {"resource": self.name, "parenttype": "CRM Service"}, "parent"
		)
		if servizio:
			frappe.throw(
				_(
					"{0} is needed by the service {1}: take it off the service first, "
					"or switch it off to stop booking it"
				).format(nome, frappe.bold(servizio)),
				frappe.LinkExistsError,
			)
		listino = frappe.db.get_value("CRM Service Price", {"resource": self.name}, "price_list")
		if listino:
			frappe.throw(
				_(
					"{0} has a price of its own in the price list {1}: take that price away first, "
					"or switch it off to stop booking it"
				).format(nome, frappe.bold(listino)),
				frappe.LinkExistsError,
			)
		piattaforma = frappe.db.get_value(
			"CRM Booking Connection Map",
			{"resource": self.name, "parenttype": "CRM Booking Connection"},
			"parent",
		)
		if piattaforma:
			frappe.throw(
				_(
					"{0} is matched to the booking platform {1}: take the match away there first, "
					"or switch it off to stop booking it"
				).format(nome, frappe.bold(piattaforma)),
				frappe.LinkExistsError,
			)
