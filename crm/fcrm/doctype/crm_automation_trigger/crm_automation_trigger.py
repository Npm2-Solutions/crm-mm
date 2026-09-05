# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRMAutomationTrigger(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		trigger_condition: DF.JSON | None
		trigger_config: DF.JSON | None
		trigger_event: DF.Literal[
			"Lead Created",
			"Deal Created",
			"Lead Status Changed",
			"Deal Status Changed",
			"Booking Created",
			"Booking Cancelled",
			"Booking No Show",
			"Booking Completed",
			"Appointment Created",
			"Appointment Rescheduled",
			"Appointment Cancelled",
			"Appointment No Show",
			"Appointment Completed",
			"Call Transcribed",
			"Callback Requested",
			"Callback Attempt Failed",
			"Callback Completed",
			"Incoming SMS",
			"Customer Replied",
			"Email Opened",
			"Trigger Link Clicked",
			"Tag Added",
			"Tag Removed",
			"Task Completed",
			"Note Added",
			"Date Reminder",
			"Inbound Webhook",
		]
	# end: auto-generated types

	pass
