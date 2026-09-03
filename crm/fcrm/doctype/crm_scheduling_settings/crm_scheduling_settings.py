# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMSchedulingSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.fcrm.doctype.crm_service_day.crm_service_day import CRMServiceDay

		allow_override: DF.Check
		cancellation_notice_hours: DF.Int
		default_availability: DF.Table[CRMServiceDay]
		default_duration: DF.Int
		default_holiday_list: DF.Link | None
		default_price_list: DF.Link | None
		enforce_participant_conflicts: DF.Check
		enforce_resource_conflicts: DF.Check
		enforce_staff_conflicts: DF.Check
		enforce_working_hours: DF.Check
		sync_to_event: DF.Check
		timezone: DF.Data | None
	# end: auto-generated types

	pass
