import json

import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.desk.form.load import get_docinfo
from frappe.query_builder import JoinType
from frappe.translate import get_translated_doctypes
from frappe.utils import get_datetime, getdate

from crm.api.lead import deal_names_of
from crm.fcrm.doctype.crm_call_log.crm_call_log import parse_call_log


@frappe.whitelist()
def get_activities(name: str):
	if frappe.db.exists("CRM Deal", name):
		return get_deal_activities(name)
	elif frappe.db.exists("CRM Lead", name):
		return get_lead_activities(name)
	else:
		frappe.throw(_("Document not found"), frappe.DoesNotExistError)


def communication_activity(communication, is_lead: bool) -> dict:
	return {
		"activity_type": "communication",
		"communication_type": communication.communication_type,
		"communication_date": communication.communication_date or communication.creation,
		"creation": communication.creation,
		"data": {
			"subject": communication.subject,
			"content": communication.content,
			"sender_full_name": communication.sender_full_name,
			"sender": communication.sender,
			"recipients": communication.recipients,
			"cc": communication.cc,
			"bcc": communication.bcc,
			"attachments": get_attachments("Communication", communication.name),
			"read_by_recipient": communication.read_by_recipient,
			"delivery_status": communication.delivery_status,
		},
		"is_lead": is_lead,
	}


def get_deal_activities(name: str):
	if not frappe.has_permission("CRM Deal", "read", name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	get_docinfo("", "CRM Deal", name)
	docinfo = frappe.response["docinfo"]
	deal_meta = frappe.get_meta("CRM Deal")
	deal_fields = {
		field.fieldname: {"label": field.label, "options": field.options} for field in deal_meta.fields
	}
	avoid_fields = [
		"lead",
		"response_by",
		"sla_creation",
		"sla",
		"first_response_time",
		"first_responded_on",
	]

	doc = frappe.db.get_values("CRM Deal", name, ["creation", "owner", "lead"])[0]
	lead = doc[2]

	activities = []
	calls = []
	notes = []
	tasks = []
	attachments = []
	creation_text = _("created this deal")

	if lead:
		# the person's story stays on the person: replaying it here made the deal
		# read like a second copy of the lead, chat and all
		creation_text = _("converted the lead to this deal")

	activities.append(
		{
			"activity_type": "creation",
			"creation": doc[0],
			"owner": doc[1],
			"data": creation_text,
			"is_lead": False,
		}
	)

	docinfo.versions.reverse()

	for version in docinfo.versions:
		data = json.loads(version.data)
		if not data.get("changed"):
			continue

		if change := data.get("changed")[0]:
			field = deal_fields.get(change[0], None)

			if not field or change[0] in avoid_fields or (not change[1] and not change[2]):
				continue

			field_label = field.get("label") or change[0]
			field_option = field.get("options") or None

			activity_type = "changed"
			data = {
				"field": change[0],
				"field_label": field_label,
				"old_value": change[1],
				"value": change[2],
			}

			if not change[1] and change[2]:
				activity_type = "added"
				data = {
					"field": change[0],
					"field_label": field_label,
					"value": change[2],
				}
			elif change[1] and not change[2]:
				activity_type = "removed"
				data = {
					"field": change[0],
					"field_label": field_label,
					"value": change[1],
				}

			if data.get("value") and field_option and is_translatable(field_option):
				data["value"] = _(data["value"])

				if data.get("old_value"):
					data["old_value"] = _(data["old_value"])

		activity = {
			"activity_type": activity_type,
			"creation": version.creation,
			"owner": version.owner,
			"data": data,
			"is_lead": False,
			"options": field_option,
		}
		activities.append(activity)

	for comment in docinfo.comments:
		activity = {
			"name": comment.name,
			"activity_type": "comment",
			"creation": comment.creation,
			"owner": comment.owner,
			"content": comment.content,
			"attachments": get_attachments("Comment", comment.name),
			"is_lead": False,
		}
		activities.append(activity)

	for communication in docinfo.communications + docinfo.automated_messages:
		activities.append(communication_activity(communication, is_lead=False))

	for attachment_log in docinfo.attachment_logs:
		activity = {
			"name": attachment_log.name,
			"activity_type": "attachment_log",
			"creation": attachment_log.creation,
			"owner": attachment_log.owner,
			"data": parse_attachment_log(attachment_log.content, attachment_log.comment_type),
			"is_lead": False,
		}
		activities.append(activity)

	calls = calls + get_linked_calls(name).get("calls", [])
	notes = notes + get_linked_notes(name) + get_linked_calls(name).get("notes", [])
	tasks = tasks + get_linked_tasks(name) + get_linked_calls(name).get("tasks", [])
	attachments = attachments + get_attachments("CRM Deal", name)
	activities += everything_else_on("CRM Deal", name)

	activities.sort(key=lambda x: x["creation"], reverse=True)
	activities = handle_multiple_versions(activities)

	return activities, calls, notes, tasks, attachments


def get_lead_activities(name: str):
	if not frappe.has_permission("CRM Lead", "read", name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	get_docinfo("", "CRM Lead", name)
	docinfo = frappe.response["docinfo"]
	lead_meta = frappe.get_meta("CRM Lead")
	lead_fields = {
		field.fieldname: {"label": field.label, "options": field.options} for field in lead_meta.fields
	}
	avoid_fields = [
		"converted",
		"response_by",
		"sla_creation",
		"sla",
		"first_response_time",
		"first_responded_on",
	]

	doc = frappe.db.get_values("CRM Lead", name, ["creation", "owner"])[0]
	activities = [
		{
			"activity_type": "creation",
			"creation": doc[0],
			"owner": doc[1],
			"data": _("created this lead"),
			"is_lead": True,
		}
	]

	docinfo.versions.reverse()

	for version in docinfo.versions:
		data = json.loads(version.data)
		if not data.get("changed"):
			continue

		if change := data.get("changed")[0]:
			field = lead_fields.get(change[0], None)

			if not field or change[0] in avoid_fields or (not change[1] and not change[2]):
				continue

			field_label = field.get("label") or change[0]
			field_option = field.get("options") or None

			activity_type = "changed"
			data = {
				"field": change[0],
				"field_label": field_label,
				"old_value": change[1],
				"value": change[2],
			}

			if not change[1] and change[2]:
				activity_type = "added"
				data = {
					"field": change[0],
					"field_label": field_label,
					"value": change[2],
				}
			elif change[1] and not change[2]:
				activity_type = "removed"
				data = {
					"field": change[0],
					"field_label": field_label,
					"value": change[1],
				}

			if data.get("value") and field_option and is_translatable(field_option):
				data["value"] = _(data["value"])

				if data.get("old_value"):
					data["old_value"] = _(data["old_value"])

		activity = {
			"activity_type": activity_type,
			"creation": version.creation,
			"owner": version.owner,
			"data": data,
			"is_lead": True,
			"options": field_option,
		}
		activities.append(activity)

	for comment in docinfo.comments:
		activity = {
			"name": comment.name,
			"activity_type": "comment",
			"creation": comment.creation,
			"owner": comment.owner,
			"content": comment.content,
			"attachments": get_attachments("Comment", comment.name),
			"is_lead": True,
		}
		activities.append(activity)

	for communication in docinfo.communications + docinfo.automated_messages:
		activities.append(communication_activity(communication, is_lead=True))

	for attachment_log in docinfo.attachment_logs:
		activity = {
			"name": attachment_log.name,
			"activity_type": "attachment_log",
			"creation": attachment_log.creation,
			"owner": attachment_log.owner,
			"data": parse_attachment_log(attachment_log.content, attachment_log.comment_type),
			"is_lead": True,
		}
		activities.append(activity)

	calls = get_linked_calls(name).get("calls", [])
	notes = get_linked_notes(name) + get_linked_calls(name).get("notes", [])
	tasks = get_linked_tasks(name) + get_linked_calls(name).get("tasks", [])
	attachments = get_attachments("CRM Lead", name)

	activities += everything_else_on("CRM Lead", name)

	deal_activities, deal_calls = get_conversation_on_deals(name)
	activities += deal_activities
	calls += deal_calls

	activities.sort(key=lambda x: x["creation"], reverse=True)
	activities = handle_multiple_versions(activities)

	return activities, calls, notes, tasks, attachments


def get_conversation_on_deals(lead: str):
	"""What was said on this person's deals, brought back to the person.

	An email or a call belongs to whoever we were talking to, not to the
	negotiation it happened during. The deal no longer shows a copy of this
	conversation, so without gathering it here anything said from a deal would
	have nowhere left to be read.
	"""
	activities = []
	calls = []

	for deal in deal_names_of(lead):
		# a user can have the person and not one of their deals
		if not frappe.has_permission("CRM Deal", "read", deal):
			continue

		get_docinfo("", "CRM Deal", deal)
		docinfo = frappe.response["docinfo"]
		for communication in docinfo.communications + docinfo.automated_messages:
			activities.append(communication_activity(communication, is_lead=False))

		calls += get_linked_calls(deal).get("calls", [])

	return activities, calls


def get_attachments(doctype: str, name: str):
	return (
		frappe.db.get_all(
			"File",
			filters={"attached_to_doctype": doctype, "attached_to_name": name},
			fields=[
				"name",
				"file_name",
				"file_type",
				"file_url",
				"file_size",
				"is_private",
				"modified",
				"creation",
				"owner",
			],
		)
		or []
	)


def handle_multiple_versions(versions: list):
	activities = []
	grouped_versions = []
	old_version = None
	for version in versions:
		is_version = version["activity_type"] in ["changed", "added", "removed"]
		if not is_version:
			activities.append(version)
		if not old_version:
			old_version = version
			if is_version:
				grouped_versions.append(version)
			continue
		if is_version and old_version.get("owner") and version["owner"] == old_version["owner"]:
			grouped_versions.append(version)
		else:
			if grouped_versions:
				activities.append(parse_grouped_versions(grouped_versions))
			grouped_versions = []
			if is_version:
				grouped_versions.append(version)
		old_version = version
		if version == versions[-1] and grouped_versions:
			activities.append(parse_grouped_versions(grouped_versions))

	return activities


def parse_grouped_versions(versions: list):
	version = versions[0]
	if len(versions) == 1:
		return version
	other_versions = versions[1:]
	version["other_versions"] = other_versions
	return version


def get_linked_calls(name: str):
	calls = frappe.db.get_all(
		"CRM Call Log",
		filters={"reference_docname": name},
		fields=[
			"name",
			"caller",
			"receiver",
			"from",
			"to",
			"duration",
			"start_time",
			"end_time",
			"status",
			"type",
			"recording_url",
			"creation",
			"note",
		],
	)

	linked_calls = frappe.db.get_all(
		"Dynamic Link", filters={"link_name": name, "parenttype": "CRM Call Log"}, pluck="parent"
	)

	notes = []
	tasks = []

	if linked_calls:
		CallLog = frappe.qb.DocType("CRM Call Log")
		Link = frappe.qb.DocType("Dynamic Link")
		query = (
			frappe.qb.from_(CallLog)
			.select(
				CallLog.name,
				CallLog.caller,
				CallLog.receiver,
				CallLog["from"],
				CallLog.to,
				CallLog.duration,
				CallLog.start_time,
				CallLog.end_time,
				CallLog.status,
				CallLog.type,
				CallLog.recording_url,
				CallLog.creation,
				CallLog.note,
				Link.link_doctype,
				Link.link_name,
			)
			.join(Link, JoinType.inner)
			.on(Link.parent == CallLog.name)
			.where(CallLog.name.isin(linked_calls))
		)
		_calls = query.run(as_dict=True)

		for call in _calls:
			if call.get("link_doctype") == "FCRM Note":
				notes.append(call.link_name)
			elif call.get("link_doctype") == "CRM Task":
				tasks.append(call.link_name)

		_calls = [call for call in _calls if call.get("link_doctype") not in ["FCRM Note", "CRM Task"]]
		if _calls:
			calls = calls + _calls

	if notes:
		notes = frappe.db.get_all(
			"FCRM Note",
			filters={"name": ("in", notes)},
			fields=["name", "title", "content", "owner", "modified"],
		)

	if tasks:
		tasks = frappe.db.get_all(
			"CRM Task",
			filters={"name": ("in", tasks)},
			fields=[
				"name",
				"title",
				"description",
				"assigned_to",
				"due_date",
				"priority",
				"status",
				"modified",
			],
		)

	calls = [parse_call_log(call) for call in calls] if calls else []

	return {"calls": calls, "notes": notes, "tasks": tasks}


def get_linked_notes(name: str):
	notes = frappe.db.get_all(
		"FCRM Note",
		filters={"reference_docname": name},
		fields=["name", "title", "content", "owner", "modified", "creation"],
	)
	return notes or []


def get_linked_tasks(name: str):
	tasks = frappe.db.get_all(
		"CRM Task",
		filters={"reference_docname": name},
		fields=[
			"name",
			"title",
			"description",
			"assigned_to",
			"due_date",
			"priority",
			"status",
			"modified",
			"creation",
		],
	)
	return tasks or []


def parse_attachment_log(html: str, type: str):
	soup = BeautifulSoup(html, "html.parser")
	a_tag = soup.find("a")
	type = "added" if type == "Attachment" else "removed"
	if not a_tag:
		return {
			"type": type,
			"file_name": html.replace("Removed ", ""),
			"file_url": "",
			"is_private": False,
		}

	is_private = False
	if "private/files" in a_tag["href"]:
		is_private = True

	return {
		"type": type,
		"file_name": a_tag.text,
		"file_url": a_tag["href"],
		"is_private": is_private,
	}


def is_translatable(doctype: str) -> bool:
	return doctype in get_translated_doctypes()


# --- everything else that happens to a person ---------------------------------
#
# A history that holds only what was *said* is half a history. An appointment
# booked, a task somebody set themselves, a meeting put in the calendar, a note
# written on the record: those are the things that happened between one message
# and the next, and reading the messages without them is reading a conversation
# with the actions cut out.


def appointments_on(doctype: str, name: str) -> list[dict]:
	"""Appointments this person is a participant of.

	The link lives on the participants table rather than on the appointment, so
	a meeting with three people is one appointment on three records rather than
	three appointments.
	"""
	if not frappe.db.exists("DocType", "CRM Appointment"):
		return []
	booked = frappe.get_all(
		"CRM Appointment Participant",
		filters={"party_type": doctype, "party": name},
		pluck="parent",
		limit_page_length=0,
	)
	if not booked:
		return []
	rows = frappe.get_all(
		"CRM Appointment",
		filters={"name": ["in", booked]},
		fields=["name", "title", "service", "status", "starts_on", "ends_on", "creation", "owner"],
		limit_page_length=0,
	)
	return [
		{
			"name": row.name,
			"activity_type": "appointment",
			# when it *is*, not when it was written down: an appointment belongs
			# in the history at the moment it happens, the way a call does
			"creation": row.starts_on or row.creation,
			"owner": row.owner,
			"data": dict(row),
			"is_lead": doctype == "CRM Lead",
		}
		for row in rows
	]


def events_on(doctype: str, name: str) -> list[dict]:
	"""Calendar events put against this record."""
	rows = frappe.get_all(
		"Event",
		filters={"reference_docname": name, "reference_doctype": doctype},
		fields=["name", "subject", "starts_on", "ends_on", "event_category", "creation", "owner"],
		limit_page_length=0,
	)
	return [
		{
			"name": row.name,
			"activity_type": "event",
			"creation": row.starts_on or row.creation,
			"owner": row.owner,
			"data": dict(row),
			"is_lead": doctype == "CRM Lead",
		}
		for row in rows
	]


def tasks_on(doctype: str, name: str) -> list[dict]:
	"""Tasks set on this record, as they were set.

	A task that is done still belongs where it was created: it is what somebody
	decided to do about this person that day, and moving it to the day it was
	ticked off would lose the decision.
	"""
	rows = frappe.get_all(
		"CRM Task",
		filters={"reference_docname": name, "reference_doctype": doctype},
		fields=["name", "title", "status", "priority", "due_date", "creation", "owner", "assigned_to"],
		limit_page_length=0,
	)
	return [
		{
			"name": row.name,
			"activity_type": "task",
			"creation": row.creation,
			"owner": row.owner,
			"data": dict(row),
			"is_lead": doctype == "CRM Lead",
		}
		for row in rows
	]


def notes_on(doctype: str, name: str) -> list[dict]:
	"""Notes written on this record.

	They had a tab of their own and nowhere else, so something written down
	about a person could not be read beside the conversation it was about.
	"""
	rows = frappe.get_all(
		"FCRM Note",
		filters={"reference_docname": name, "reference_doctype": doctype},
		fields=["name", "title", "content", "creation", "owner"],
		limit_page_length=0,
	)
	return [
		{
			"name": row.name,
			"activity_type": "note",
			"creation": row.creation,
			"owner": row.owner,
			"data": dict(row),
			"is_lead": doctype == "CRM Lead",
		}
		for row in rows
	]


def invoice_moment(row) -> str:
	"""Where an invoice sits: on the date printed on it, at the hour it was written.

	The posting date is the invoice's real date — the one on the document, the one
	somebody looks for it under — so an invoice entered today for the 20th belongs
	on the 20th. When the two agree, the creation time is kept, because midnight
	would float today's invoice above the whole day's messages.
	"""
	created = get_datetime(row.creation)
	if not row.posting_date:
		return row.creation
	if getdate(row.posting_date) == created.date():
		return row.creation
	return get_datetime(row.posting_date)


def invoices_on(doctype: str, name: str) -> list[dict]:
	"""Invoices issued to this person.

	Money is the loudest thing that happens on a record and it had no place in
	the history at all: an invoice lived on its own page, so the one fact that
	says the relationship became a paying one could not be read beside the
	conversation that produced it.

	The link is written twice — `party_type`/`party` like an appointment, and a
	plain `deal` link — so both are read: an invoice raised from a deal never
	shows up on the deal it came from otherwise.
	"""
	if not frappe.db.exists("DocType", "CRM Invoice"):
		return []
	fields = [
		"name",
		"document_type",
		"document_number",
		"posting_date",
		"grand_total",
		"net_payable",
		"sdi_status",
		"ts_status",
		"docstatus",
		"creation",
		"owner",
	]
	# Gathered as two lookups rather than one `or_filters`: a multi-key dict in
	# `or_filters` is flattened into independent OR conditions, so asking for
	# «party_type = CRM Deal and party = this one, or deal = this one» would in
	# fact ask for every invoice raised against any deal at all.
	billed = set(
		frappe.get_all(
			"CRM Invoice",
			filters={"party_type": doctype, "party": name},
			pluck="name",
			limit_page_length=0,
		)
	)
	if doctype == "CRM Deal":
		billed |= set(
			frappe.get_all("CRM Invoice", filters={"deal": name}, pluck="name", limit_page_length=0)
		)
	if not billed:
		return []
	rows = frappe.get_all(
		"CRM Invoice",
		filters={"name": ["in", sorted(billed)]},
		fields=fields,
		limit_page_length=0,
	)
	return [
		{
			"name": row.name,
			"activity_type": "invoice",
			"creation": invoice_moment(row),
			"owner": row.owner,
			"data": dict(row),
			"is_lead": doctype == "CRM Lead",
		}
		for row in rows
	]


def everything_else_on(doctype: str, name: str) -> list[dict]:
	"""The gatherers above, gathered. Each one is allowed to fail on its own.

	A site without the booking app, without invoicing, or with an older Event
	doctype, should lose that one row type and keep the history — not lose the
	history.
	"""
	gathered = []
	for gather in (appointments_on, events_on, tasks_on, notes_on, invoices_on):
		try:
			gathered += gather(doctype, name)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Activities: {gather.__name__} did not run")
	return gathered
