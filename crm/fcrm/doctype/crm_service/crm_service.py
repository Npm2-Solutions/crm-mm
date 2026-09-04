# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

from crm.scheduling.timeutils import as_time


class CRMService(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.fcrm.doctype.crm_service_day.crm_service_day import CRMServiceDay
		from crm.fcrm.doctype.crm_service_resource.crm_service_resource import CRMServiceResource
		from crm.fcrm.doctype.crm_service_role.crm_service_role import CRMServiceRole
		from crm.fcrm.doctype.crm_service_staff.crm_service_staff import CRMServiceStaff

		availability: DF.Table[CRMServiceDay]
		bookable_online: DF.Check
		buffer_after: DF.Int
		buffer_before: DF.Int
		category: DF.Data | None
		color: DF.Color | None
		currency: DF.Link | None
		default_price: DF.Currency | None
		description: DF.SmallText | None
		duration: DF.Int
		enabled: DF.Check
		holiday_list: DF.Link | None
		max_horizon_days: DF.Int
		max_participants: DF.Int
		min_notice_hours: DF.Int
		min_participants: DF.Int
		price_per_participant: DF.Check
		resources: DF.Table[CRMServiceResource]
		roles: DF.Table[CRMServiceRole]
		service_name: DF.Data
		slot_interval: DF.Int
		staff: DF.Table[CRMServiceStaff]
		staff_count: DF.Int
		staff_selection: DF.Literal["Any one", "All required", "One per role"]
	# end: auto-generated types

	def validate(self):
		self.validate_numbers()
		self.validate_participants()
		self.validate_staffing()
		self.validate_availability()
		self.validate_resources()

	def validate_numbers(self):
		if cint(self.duration) <= 0:
			frappe.throw(_("Duration must be a positive number of minutes"))
		for field, label in (
			("slot_interval", _("Slot Interval")),
			("buffer_before", _("Buffer Before")),
			("buffer_after", _("Buffer After")),
			("min_notice_hours", _("Minimum Notice")),
			("max_horizon_days", _("Booking Horizon")),
		):
			if cint(self.get(field)) < 0:
				frappe.throw(_("{0} cannot be negative").format(label))

	def validate_participants(self):
		if cint(self.max_participants) < 1:
			self.max_participants = 1
		if cint(self.min_participants) < 1:
			self.min_participants = 1
		if cint(self.min_participants) > cint(self.max_participants):
			frappe.throw(_("Minimum participants cannot exceed maximum participants"))

	def validate_staffing(self):
		seen = set()
		for row in self.staff:
			if row.user in seen:
				frappe.throw(_("{0} is listed more than once among the professionals").format(row.user))
			seen.add(row.user)

		if not self.staff:
			frappe.throw(_("Add at least one professional who can deliver this service"))

		if self.staff_selection == "One per role":
			if not self.roles:
				frappe.throw(_("Add the roles this service needs, or pick another staffing mode"))
			for role in self.roles:
				members = [row for row in self.staff if row.role == role.role]
				if len(members) < cint(role.staff_count):
					frappe.throw(
						_("Role {0} needs {1} professionals but only {2} are listed with that role").format(
							role.role, cint(role.staff_count), len(members)
						)
					)
			for row in self.staff:
				if not row.role:
					frappe.throw(
						_("{0} has no role — every professional needs one in 'One per role' mode").format(
							row.user
						)
					)
		elif self.staff_selection == "Any one":
			if cint(self.staff_count) < 1:
				self.staff_count = 1
			if cint(self.staff_count) > len(self.staff):
				frappe.throw(
					_("{0} professionals are needed per appointment but only {1} are listed").format(
						cint(self.staff_count), len(self.staff)
					)
				)
		else:
			# collective: everybody listed attends
			self.staff_count = len(self.staff)

	def validate_availability(self):
		for row in self.availability:
			if as_time(row.start_time) >= as_time(row.end_time):
				frappe.throw(_("Row {0}: start time must be before end time").format(row.idx))

	def validate_resources(self):
		for row in self.resources:
			if not row.resource and not row.resource_type:
				frappe.throw(_("Row {0}: pick a resource or a resource type").format(row.idx))
			if cint(row.quantity) < 1:
				row.quantity = 1
			if row.resource and row.resource_type:
				actual = frappe.db.get_value("CRM Resource", row.resource, "resource_type")
				if actual != row.resource_type:
					row.resource_type = actual
