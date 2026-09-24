# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _, generate_hash
from frappe.model.document import Document

from crm.integrations.api import get_contact_by_phone_number
from crm.utils import seconds_to_duration


class CRMCallLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.core.doctype.dynamic_link.dynamic_link import DynamicLink
		from frappe.types import DF

		callback_attempts: DF.Int
		callback_by: DF.Link | None
		callback_completed_on: DF.Datetime | None
		callback_due: DF.Datetime | None
		callback_status: DF.Literal["", "Pending", "Done", "Cancelled"]
		caller: DF.Link | None
		duration: DF.Duration | None
		end_time: DF.Datetime | None
		id: DF.Data | None
		links: DF.Table[DynamicLink]
		medium: DF.Data | None
		note: DF.Link | None
		receiver: DF.Link | None
		recording_url: DF.SmallText | None
		reference_docname: DF.DynamicLink | None
		reference_doctype: DF.Link | None
		start_time: DF.Datetime | None
		status: DF.Literal[
			"Initiated",
			"Ringing",
			"In Progress",
			"Completed",
			"Failed",
			"Busy",
			"No Answer",
			"Queued",
			"Canceled",
		]
		transcribed_on: DF.Datetime | None
		transcript: DF.LongText | None
		transcript_language: DF.Data | None
		transcription_error: DF.SmallText | None
		transcription_status: DF.Literal["", "Pending", "In Progress", "Completed", "Failed", "Skipped"]
		telephony_medium: DF.Literal["", "Manual", "Twilio", "Exotel"]
		to: DF.Data
		type: DF.Literal["Incoming", "Outgoing"]
	# end: auto-generated types

	def before_insert(self):
		if not self.id:
			self.id = generate_hash(length=12)
		if not self.telephony_medium:
			self.telephony_medium = "Manual"
		self.fill_in_who_was_on_the_call()

	def fill_in_who_was_on_the_call(self):
		"""A call logged by hand already knows who it was with.

		It is written from somebody's record, so one end of it is that person's
		number and the other is whoever is typing. Leaving both ends blank asked
		the same question twice on every single call — and got it wrong often
		enough, because `type` decides which end is which and it is easy to fill
		the boxes the way they are laid out rather than the way the call went.

		Only what is missing is filled. Somebody who typed a number meant it.
		"""
		if self.telephony_medium not in ("", "Manual"):
			# a real call from a provider carries its own numbers
			return

		incoming = self.type == "Incoming"
		theirs = self.number_of_the_record()
		mine = self.number_of_the_agent()

		if incoming:
			self.set_if_empty("from", theirs)
			self.set_if_empty("to", mine)
			self.set_if_empty("receiver", frappe.session.user)
		else:
			self.set_if_empty("from", mine)
			self.set_if_empty("to", theirs)
			self.set_if_empty("caller", frappe.session.user)

	def set_if_empty(self, field: str, value: str | None) -> None:
		if value and not self.get(field):
			self.set(field, value)

	def number_of_the_record(self) -> str:
		"""The number of the lead, deal or contact this call was written from."""
		if not self.reference_doctype or not self.reference_docname:
			return ""
		for field in ("mobile_no", "phone", "actual_mobile_no"):
			if not frappe.get_meta(self.reference_doctype).has_field(field):
				continue
			number = frappe.db.get_value(self.reference_doctype, self.reference_docname, field)
			if number:
				return number
		return ""

	def number_of_the_agent(self) -> str:
		"""The number at this end.

		`CRM Telephony Agent` is where a person's working numbers already live —
		their own, and the one each provider calls out from. The User's mobile is
		the fallback for somebody who has never been set up for telephony.
		"""
		agent = frappe.db.get_value(
			"CRM Telephony Agent",
			frappe.session.user,
			["mobile_no", "twilio_number", "exotel_number"],
			as_dict=True,
		)
		if agent:
			for field in ("mobile_no", "twilio_number", "exotel_number"):
				if agent.get(field):
					return agent[field]
		return frappe.db.get_value("User", frappe.session.user, "mobile_no") or ""

	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "Caller",
				"type": "Link",
				"key": "caller",
				"options": "User",
				"width": "9rem",
			},
			{
				"label": "Receiver",
				"type": "Link",
				"key": "receiver",
				"options": "User",
				"width": "9rem",
			},
			{
				"label": "Type",
				"type": "Select",
				"key": "type",
				"width": "9rem",
			},
			{
				"label": "Status",
				"type": "Select",
				"key": "status",
				"width": "9rem",
			},
			{
				"label": "Duration",
				"type": "Duration",
				"key": "duration",
				"width": "6rem",
			},
			{
				"label": "From (number)",
				"type": "Data",
				"key": "from",
				"width": "9rem",
			},
			{
				"label": "To (number)",
				"type": "Data",
				"key": "to",
				"width": "9rem",
			},
			{
				"label": "Created On",
				"type": "Datetime",
				"key": "creation",
				"width": "8rem",
			},
			{
				"label": "Callback Status",
				"type": "Select",
				"key": "callback_status",
				"width": "8rem",
			},
			{
				"label": "Call Back By",
				"type": "Datetime",
				"key": "callback_due",
				"width": "8rem",
			},
		]
		rows = [
			"name",
			"caller",
			"receiver",
			"type",
			"status",
			"duration",
			"from",
			"to",
			"note",
			"recording_url",
			"reference_doctype",
			"reference_docname",
			"creation",
			"callback_status",
			"callback_due",
			"callback_attempts",
			"callback_by",
		]
		return {"columns": columns, "rows": rows}

	def parse_list_data(calls):
		return [parse_call_log(call) for call in calls] if calls else []

	def has_link(self, doctype, name):
		for link in self.links:
			if link.link_doctype == doctype and link.link_name == name:
				return True

	def link_with_reference_doc(self, reference_doctype, reference_name):
		if self.has_link(reference_doctype, reference_name):
			return

		self.append("links", {"link_doctype": reference_doctype, "link_name": reference_name})

	def as_dict(self, *args, **kwargs):
		d = super().as_dict(*args, **kwargs)
		if d.get("recording_url"):
			d["recording_url_path"] = (
				f"/api/method/crm.integrations.api.get_recording_url?call_log_name={d.get('name')}"
			)
		return d


def parse_call_log(call):
	call["show_recording"] = False
	call["_duration"] = seconds_to_duration(call.get("duration"))
	if call.get("type") == "Incoming":
		call["activity_type"] = "incoming_call"
		contact = get_contact_by_phone_number(call.get("from"))
		receiver = (
			frappe.db.get_values("User", call.get("receiver"), ["full_name", "user_image"])[0]
			if call.get("receiver")
			else [None, None]
		)
		call["_caller"] = {
			"label": contact.get("full_name", "Unknown"),
			"image": contact.get("image"),
		}
		call["_receiver"] = {
			"label": receiver[0],
			"image": receiver[1],
		}
	elif call.get("type") == "Outgoing":
		call["activity_type"] = "outgoing_call"
		contact = get_contact_by_phone_number(call.get("to"))
		caller = (
			frappe.db.get_values("User", call.get("caller"), ["full_name", "user_image"])[0]
			if call.get("caller")
			else [None, None]
		)
		call["_caller"] = {
			"label": caller[0],
			"image": caller[1],
		}
		call["_receiver"] = {
			"label": contact.get("full_name", "Unknown"),
			"image": contact.get("image"),
		}

	return call


@frappe.whitelist()
def get_call_log(name: str):
	call = frappe.get_cached_doc(
		"CRM Call Log",
		name,
		fields=[
			"name",
			"caller",
			"receiver",
			"duration",
			"type",
			"status",
			"from",
			"to",
			"note",
			"recording_url",
			"recording_url_path",
			"reference_doctype",
			"reference_docname",
			"creation",
		],
	).as_dict()

	call = parse_call_log(call)

	notes = []
	tasks = []

	if call.get("note"):
		note = frappe.get_cached_doc("FCRM Note", call.get("note")).as_dict()
		notes.append(note)

	if call.get("reference_doctype") and call.get("reference_docname"):
		if call.get("reference_doctype") == "CRM Lead":
			call["_lead"] = call.get("reference_docname")
		elif call.get("reference_doctype") == "CRM Deal":
			call["_deal"] = call.get("reference_docname")

	if call.get("links"):
		for link in call.get("links"):
			if link.get("link_doctype") == "CRM Task":
				task = frappe.get_cached_doc("CRM Task", link.get("link_name")).as_dict()
				tasks.append(task)
			elif link.get("link_doctype") == "FCRM Note":
				note = frappe.get_cached_doc("FCRM Note", link.get("link_name")).as_dict()
				notes.append(note)
			elif link.get("link_doctype") == "CRM Lead":
				call["_lead"] = link.get("link_name")
			elif link.get("link_doctype") == "CRM Deal":
				call["_deal"] = link.get("link_name")

	call["_tasks"] = tasks
	call["_notes"] = notes
	return call


@frappe.whitelist()
def create_lead_from_call_log(call_log: str | dict, lead_details: str | dict | None = None):
	call_log_data = frappe.parse_json(call_log or {})

	if isinstance(call_log_data, str):
		call_log_name = call_log_data
	elif isinstance(call_log_data, dict):
		call_log_name = call_log_data.get("name")
	else:
		call_log_name = None

	if not call_log_name:
		frappe.throw(_("A valid call log is required."), frappe.ValidationError)

	call_doc = frappe.get_doc("CRM Call Log", call_log_name)

	if not call_doc.has_permission("write"):
		frappe.throw(_("You are not permitted to update this call log."), frappe.PermissionError)

	if not frappe.has_permission("CRM Lead", "create"):
		frappe.throw(_("You are not permitted to create leads."), frappe.PermissionError)

	lead_details_data = frappe.parse_json(lead_details or {})
	if lead_details_data and not isinstance(lead_details_data, dict):
		frappe.throw(_("Invalid lead details supplied."), frappe.ValidationError)

	lead = frappe.new_doc("CRM Lead")
	meta = frappe.get_meta("CRM Lead")
	valid_fieldnames = [df.fieldname for df in meta.fields]

	sanitized_details = {
		key: value for key, value in (lead_details_data or {}).items() if key in valid_fieldnames
	}

	if "lead_owner" in valid_fieldnames and not sanitized_details.get("lead_owner"):
		sanitized_details["lead_owner"] = frappe.session.user

	if "mobile_no" in valid_fieldnames and not sanitized_details.get("mobile_no"):
		sanitized_details["mobile_no"] = call_doc.get("from") or ""

	if "first_name" in valid_fieldnames and not sanitized_details.get("first_name"):
		reference_label = sanitized_details.get("mobile_no") or call_doc.name
		sanitized_details["first_name"] = _("Lead from call {0}").format(reference_label)

	lead.update(sanitized_details)
	lead.insert()

	call_doc.link_with_reference_doc("CRM Lead", lead.name)
	call_doc.save()

	return lead.name
