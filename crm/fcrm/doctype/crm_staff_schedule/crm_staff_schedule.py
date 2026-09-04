# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

from crm.scheduling.timeutils import as_time


class CRMStaffSchedule(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.fcrm.doctype.crm_availability_exception.crm_availability_exception import (
			CRMAvailabilityException,
		)
		from crm.fcrm.doctype.crm_service_day.crm_service_day import CRMServiceDay

		availability: DF.Table[CRMServiceDay]
		enabled: DF.Check
		exceptions: DF.Table[CRMAvailabilityException]
		holiday_list: DF.Link | None
		max_daily_appointments: DF.Int
		user: DF.Link
	# end: auto-generated types

	def validate(self):
		for row in self.availability:
			if as_time(row.start_time) >= as_time(row.end_time):
				frappe.throw(_("Weekly hours row {0}: start time must be before end time").format(row.idx))
		for row in self.exceptions:
			if cint(row.unavailable):
				row.start_time = None
				row.end_time = None
				continue
			if not row.start_time or not row.end_time:
				frappe.throw(
					_("Exception row {0}: set the extra hours, or tick 'Unavailable all day'").format(row.idx)
				)
			if as_time(row.start_time) >= as_time(row.end_time):
				frappe.throw(_("Exception row {0}: start time must be before end time").format(row.idx))
		if cint(self.max_daily_appointments) < 0:
			self.max_daily_appointments = 0
