# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, getdate

from crm.scheduling.timeutils import as_time


class CRMServicePrice(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		currency: DF.Link | None
		enabled: DF.Check
		end_time: DF.Time | None
		label: DF.Data | None
		max_participants: DF.Int
		min_participants: DF.Int
		per_participant: DF.Check
		price: DF.Currency
		price_list: DF.Link
		priority: DF.Int
		resource: DF.Link | None
		service: DF.Link
		staff: DF.Link | None
		start_time: DF.Time | None
		valid_from: DF.Date | None
		valid_upto: DF.Date | None
		weekday: DF.Literal["", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
	# end: auto-generated types

	def validate(self):
		if self.start_time and self.end_time and as_time(self.start_time) >= as_time(self.end_time):
			frappe.throw(_("The time band must start before it ends"))
		if self.valid_from and self.valid_upto and getdate(self.valid_from) > getdate(self.valid_upto):
			frappe.throw(_("Valid From must be on or before Valid Upto"))
		if (
			cint(self.min_participants)
			and cint(self.max_participants)
			and cint(self.min_participants) > cint(self.max_participants)
		):
			frappe.throw(_("'From participants' cannot exceed 'Up to participants'"))
		if self.staff and self.service:
			eligible = frappe.get_all("CRM Service Staff", filters={"parent": self.service}, pluck="user")
			if self.staff not in eligible:
				frappe.throw(_("{0} does not deliver {1}").format(self.staff, self.service))
		if not self.currency:
			self.currency = frappe.db.get_value("CRM Price List", self.price_list, "currency")
