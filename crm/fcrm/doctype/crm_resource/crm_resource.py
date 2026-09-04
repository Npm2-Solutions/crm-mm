# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
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
