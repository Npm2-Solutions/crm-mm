# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.model.document import Document

from crm.automation.engine import compile_steps, ensure_step_ids, parse_json, validate_steps


class CRMAutomation(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from crm.fcrm.doctype.crm_automation_trigger.crm_automation_trigger import (
			CRMAutomationTrigger,
		)

		allow_reenrollment: DF.Check
		compiled_steps: DF.JSON | None
		triggers: DF.Table[CRMAutomationTrigger]
		description: DF.SmallText | None
		enabled: DF.Check
		exit_on_reply: DF.Check
		steps: DF.JSON
		time_window_enabled: DF.Check
		title: DF.Data
		trigger_condition: DF.JSON | None
		trigger_config: DF.JSON | None
		trigger_event: DF.Literal[
			"Lead Created",
			"Lead Form Submitted",
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
		webhook_key: DF.Data | None
		window_days: DF.JSON | None
		window_end: DF.Time | None
		window_start: DF.Time | None
	# end: auto-generated types

	def validate(self):
		self.sync_triggers()
		steps = parse_json(self.steps)
		validate_steps(steps)
		ensure_step_ids(steps)
		self.steps = json.dumps(steps)
		self.compiled_steps = json.dumps(compile_steps(steps))
		if "Inbound Webhook" in self.trigger_events() and not self.webhook_key:
			self.webhook_key = frappe.generate_hash(length=32)

	def sync_triggers(self):
		"""Keep the triggers table and the single legacy field in step.

		An automation can listen to several events. Those saved before the table
		existed carry only `trigger_event`/`trigger_config`/`trigger_condition`:
		the first save turns them into row one. From then on the single fields
		mirror that row, so list views and anything reading them keep working.
		"""
		if not self.triggers and self.trigger_event:
			self.append(
				"triggers",
				{
					"trigger_event": self.trigger_event,
					"trigger_config": self.trigger_config,
					"trigger_condition": self.trigger_condition,
				},
			)
		if not self.triggers:
			frappe.throw(_("An automation needs at least one trigger"))

		first = self.triggers[0]
		self.trigger_event = first.trigger_event
		self.trigger_config = first.trigger_config
		self.trigger_condition = first.trigger_condition

	def trigger_events(self) -> list[str]:
		return [row.trigger_event for row in self.triggers if row.trigger_event]

	def on_trash(self):
		frappe.db.delete("CRM Automation Enrollment", {"automation": self.name})
