import json
import re

import frappe
from frappe import _
from frappe.permissions import add_permission, update_permission_property

from crm.api.doc import get_assigned_users
from crm.api.lead import deal_names_of
from crm.fcrm.doctype.crm_notification.crm_notification import notify_user
from crm.integrations.api import adopt_unknown_number, get_contact_lead_or_deal_from_number
from crm.utils import to_e164

ALLOWED_WHATSAPP_ROLES = ["System Manager", "Sales Manager", "Sales User"]


def validate_access(reference_doctype=None, reference_name=None, permtype="read"):
	if not any(role in ALLOWED_WHATSAPP_ROLES for role in frappe.get_roles()):
		frappe.throw(_("Only sales users can access WhatsApp features."), frappe.PermissionError)

	if reference_doctype and reference_name:
		if not frappe.db.exists(reference_doctype, reference_name):
			frappe.throw(
				_("Reference document {0} {1} does not exist.").format(reference_doctype, reference_name),
				frappe.DoesNotExistError,
			)
		reference_doc = frappe.get_doc(reference_doctype, reference_name)
		if not reference_doc.has_permission(permtype):
			frappe.throw(
				_("Not permitted to access reference document {0} {1}.").format(
					reference_doctype, reference_name
				),
				frappe.PermissionError,
			)
		return reference_doc

	return None


def validate(doc, method):
	if doc.type != "Incoming" and doc.reference_doctype and doc.reference_name:
		# a message we are sending already knows the record it was written from.
		# Looking its number up again could only move it somewhere else — and it
		# did: `get_contact` answers with the person's deal when they have one, so
		# a message sent from a lead was filed on the deal and vanished from the
		# chat it had just been typed into.
		return

	phone_number = doc.get("from") if doc.type == "Incoming" else doc.get("to")
	if phone_number:
		try:
			name, doctype = get_contact_lead_or_deal_from_number(phone_number)
			if not doctype and doc.type == "Incoming":
				# nobody in the CRM owns this number: adopt it, or the message
				# lands in no chat and in no inbox and is lost on arrival
				name, doctype = adopt_unknown_number(phone_number, doc.get("profile_name")) or (
					None,
					None,
				)
			if doctype and name is not None:
				doc.reference_doctype = doctype
				doc.reference_name = name
		except Exception:
			frappe.log_error(frappe.get_traceback(), "CRM WhatsApp: failed to resolve contact from number")


def on_update(doc, method):
	frappe.publish_realtime(
		"whatsapp_message",
		{
			"reference_doctype": doc.reference_doctype,
			"reference_name": doc.reference_name,
		},
	)

	notify_agent(doc)


def notify_agent(doc):
	if doc.type == "Incoming":
		if not doc.reference_doctype or not doc.reference_name:
			return
		doctype = doc.reference_doctype
		if doctype and doctype.startswith("CRM "):
			doctype = doctype[4:].lower()
		safe_reference_name = frappe.utils.escape_html(doc.reference_name)
		notification_text = f"""
            <div class="mb-2 leading-5 text-ink-gray-5">
                <span class="font-medium text-ink-gray-9">{_("You")}</span>
                <span>{_("received a whatsapp message in {0}").format(doctype)}</span>
                <span class="font-medium text-ink-gray-9">{safe_reference_name}</span>
            </div>
        """
		assigned_users = get_assigned_users(doc.reference_doctype, doc.reference_name)
		for user in assigned_users:
			notify_user(
				{
					"owner": doc.owner,
					"assigned_to": user,
					"notification_type": "WhatsApp",
					"message": doc.message,
					"notification_text": notification_text,
					"reference_doctype": "WhatsApp Message",
					"reference_docname": doc.name,
					"redirect_to_doctype": doc.reference_doctype,
					"redirect_to_docname": doc.reference_name,
				}
			)


@frappe.whitelist()
def is_whatsapp_enabled():
	if not frappe.db.exists("DocType", "WhatsApp Settings"):
		return False
	default_outgoing = frappe.get_cached_value(
		"WhatsApp Settings", "WhatsApp Settings", "default_outgoing_account"
	)
	if not default_outgoing:
		return False
	status = frappe.get_cached_value("WhatsApp Account", default_outgoing, "status")
	return status == "Active"


@frappe.whitelist()
def is_whatsapp_installed():
	if not frappe.db.exists("DocType", "WhatsApp Settings"):
		return False
	return True


def whatsapp_thread_of(reference_doctype: str, reference_name: str, reference_doc):
	"""Every record a message with this person could have been filed against.

	The conversation belongs to the person, not to the negotiation it happened
	during: a message sent from a deal is still a message to them. So a lead
	answers with its own messages and its deals', and a deal still answers with
	the lead's, for whatever opens it that way.
	"""
	yield reference_doctype, reference_name

	if reference_doctype == "CRM Deal":
		lead = reference_doc.get("lead")
		if lead and frappe.has_permission("CRM Lead", "read", lead):
			yield "CRM Lead", lead
	elif reference_doctype == "CRM Lead":
		for deal in deal_names_of(reference_name):
			# a user can have the person and not one of their deals
			if frappe.has_permission("CRM Deal", "read", deal):
				yield "CRM Deal", deal


@frappe.whitelist()
def get_whatsapp_messages(reference_doctype: str, reference_name: str):
	reference_doc = validate_access(reference_doctype, reference_name)
	# twilio integration app is not compatible with crm app
	# crm has its own twilio integration in built
	if "twilio_integration" in frappe.get_installed_apps():
		return []
	if not frappe.db.exists("DocType", "WhatsApp Message"):
		return []
	messages = []
	# one thread per person, wherever a message happened to be filed: the deal
	# used to show the lead's chat, and now the lead shows its deals'
	for doctype, docname in whatsapp_thread_of(reference_doctype, reference_name, reference_doc):
		messages += frappe.get_all(
			"WhatsApp Message",
			filters={"reference_doctype": doctype, "reference_name": docname},
			fields=[
				"name",
				"type",
				"to",
				"from",
				"content_type",
				"message_type",
				"attach",
				"template",
				"use_template",
				"message_id",
				"is_reply",
				"reply_to_message_id",
				"creation",
				"message",
				"status",
				"reference_doctype",
				"reference_name",
				"template_parameters",
				"template_header_parameters",
			],
		)

	# Filter messages to get only Template messages
	template_messages = [message for message in messages if message["message_type"] == "Template"]

	# Iterate through template messages
	for template_message in template_messages:
		# Find the template that this message is using
		if not frappe.db.exists("WhatsApp Templates", template_message["template"]):
			continue
		template = frappe.get_doc("WhatsApp Templates", template_message["template"])

		if template:
			template_message["template_name"] = template.template_name
			if template_message["template_parameters"]:
				parameters = json.loads(template_message["template_parameters"])
				template.template = parse_template_parameters(template.template, parameters)

			template_message["template"] = template.template
			if template_message["template_header_parameters"]:
				header_parameters = json.loads(template_message["template_header_parameters"])
				template.header = parse_template_parameters(template.header, header_parameters)
			template_message["header"] = template.header
			template_message["footer"] = template.footer

	# Filter messages to get only reaction messages
	reaction_messages = [message for message in messages if message["content_type"] == "reaction"]
	reaction_messages.reverse()

	# Iterate through reaction messages
	for reaction_message in reaction_messages:
		# Find the message that this reaction is reacting to
		reacted_message = next(
			(m for m in messages if m["message_id"] == reaction_message["reply_to_message_id"]),
			None,
		)

		# If the reacted message is found, add the reaction to it
		if reacted_message:
			reacted_message["reaction"] = reaction_message["message"]

	for message in messages:
		from_name = get_from_name(message) if message["from"] else _("You")
		message["from_name"] = from_name
	# Filter messages to get only replies
	reply_messages = [message for message in messages if message["is_reply"]]

	# Iterate through reply messages
	for reply_message in reply_messages:
		# Find the message that this message is replying to
		replied_message = next(
			(m for m in messages if m["message_id"] == reply_message["reply_to_message_id"]),
			None,
		)

		# If the replied message is found, add the reply details to the reply message
		if replied_message:
			from_name = get_from_name(reply_message) if replied_message["from"] else _("You")
			message = replied_message["message"]
			if replied_message["message_type"] == "Template":
				message = replied_message["template"]
			reply_message["reply_message"] = message
			reply_message["header"] = replied_message.get("header") or ""
			reply_message["footer"] = replied_message.get("footer") or ""
			reply_message["reply_to"] = replied_message["name"]
			reply_message["reply_to_type"] = replied_message["type"]
			reply_message["reply_to_from"] = from_name

	return [message for message in messages if message["content_type"] != "reaction"]


def insert_and_send(doc) -> str:
	"""Insert the message, and say what actually went wrong when the send fails.

	`frappe_whatsapp` reports a failed send by reading
	`frappe.flags.integration_request.json()`. That flag is only set once a
	request reaches Meta, so when the call never leaves the server — a malformed
	URL, DNS, a timeout — its own error handler dies with "'NoneType' object has
	no attribute 'json'" and buries the cause. Python keeps the cause in
	`__context__`: report that one instead.
	"""
	try:
		doc.insert(ignore_permissions=True)
	except AttributeError as exc:
		cause = exc
		while cause.__context__ is not None:
			cause = cause.__context__
		frappe.log_error(frappe.get_traceback(), "WhatsApp: send failed")
		frappe.throw(_("WhatsApp could not send the message: {0}").format(cause))
	return doc.name


def whatsapp_recipient(reference_doctype: str, reference_name: str, to: str | None = None) -> str:
	"""The number a message is going to, decided here and not in the browser.

	The page sent whatever `mobile_no` it happened to be holding. When that was
	empty the message left with no recipient and Meta answered "The parameter to
	is required" — an error about a field the person pressing send has never
	heard of. The record knows who it is for, so it says so.

	Whatever comes out is in E.164, prefix and all: the same person written
	`370 340 0189` here and `+39 370 340 0189` there is one number, and only the
	second form is one Meta accepts.
	"""
	number = to or frappe.db.get_value(reference_doctype, reference_name, "mobile_no")

	if not number:
		# the lead's own field is a copy; the address book is where the numbers live
		contact = None
		if reference_doctype == "CRM Lead":
			contact = frappe.db.get_value("CRM Lead", reference_name, "contact")
		elif reference_doctype == "CRM Deal":
			contact = frappe.db.get_value(
				"CRM Contacts", {"parent": reference_name, "is_primary": 1}, "contact"
			)
		if contact:
			number = frappe.db.get_value("Contact", contact, "mobile_no")

	if not number:
		frappe.throw(_("There is no phone number to send this to. Add one first."))

	return to_e164(number)


@frappe.whitelist()
def create_whatsapp_message(
	reference_doctype: str,
	reference_name: str,
	message: str,
	to: str,
	attach: str,
	reply_to: str,
	content_type: str = "text",
):
	validate_access(reference_doctype, reference_name)
	doc = frappe.new_doc("WhatsApp Message")

	if reply_to:
		if not frappe.db.exists("WhatsApp Message", reply_to):
			frappe.throw(_("Referenced WhatsApp message does not exist."), frappe.DoesNotExistError)
		reply_doc = frappe.get_doc("WhatsApp Message", reply_to)
		if not reply_doc.has_permission("read"):
			frappe.throw(
				_("Not permitted to access the referenced WhatsApp message."), frappe.PermissionError
			)
		validate_access(reply_doc.reference_doctype, reply_doc.reference_name)
		doc.update(
			{
				"is_reply": True,
				"reply_to_message_id": reply_doc.message_id,
			}
		)

	doc.update(
		{
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"message": message or attach,
			"to": whatsapp_recipient(reference_doctype, reference_name, to),
			"attach": attach,
			"content_type": content_type,
		}
	)
	return insert_and_send(doc)


@frappe.whitelist()
def send_whatsapp_template(
	reference_doctype: str,
	reference_name: str,
	template: str,
	to: str,
	template_parameters: list | str | None = None,
	template_header_parameters: list | str | None = None,
):
	"""Send an approved template.

	`template_parameters` are the values for the {{1}}, {{2}}… placeholders, in
	order. When they are given they are stored on the message, so the text that
	actually left is what the timeline shows later.
	"""
	validate_access(reference_doctype, reference_name)
	doc = frappe.new_doc("WhatsApp Message")
	doc.update(
		{
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"message_type": "Template",
			"message": "Template message",
			"content_type": "text",
			"use_template": True,
			"template": template,
			"to": whatsapp_recipient(reference_doctype, reference_name, to),
		}
	)
	for fieldname, value in (
		("template_parameters", template_parameters),
		("template_header_parameters", template_header_parameters),
	):
		values = json.loads(value) if isinstance(value, str) else value
		if values:
			doc.set(fieldname, json.dumps(values))
	return insert_and_send(doc)


@frappe.whitelist()
def get_template_placeholders(template: str) -> dict:
	"""How many variables a template needs, so the sender can fill them in."""
	validate_access()
	if not frappe.db.exists("WhatsApp Templates", template):
		frappe.throw(_("Template not found"), frappe.DoesNotExistError)
	doc = frappe.get_doc("WhatsApp Templates", template)

	def count(text):
		return len(set(re.findall(r"{{\s*(\d+)\s*}}", text or "")))

	return {
		"name": doc.name,
		"template": doc.get("template") or "",
		"header": doc.get("header") or "",
		"footer": doc.get("footer") or "",
		"body_count": count(doc.get("template")),
		"header_count": count(doc.get("header")),
	}


@frappe.whitelist()
def react_on_whatsapp_message(emoji: str, reply_to_name: str):
	validate_access()
	if not frappe.db.exists("WhatsApp Message", reply_to_name):
		frappe.throw(_("Referenced WhatsApp message does not exist."), frappe.DoesNotExistError)
	reply_to_doc = frappe.get_doc("WhatsApp Message", reply_to_name)

	if not reply_to_doc.has_permission("read"):
		frappe.throw(_("Not permitted to access the referenced WhatsApp message."), frappe.PermissionError)

	validate_access(reply_to_doc.reference_doctype, reply_to_doc.reference_name)

	to = (reply_to_doc.type == "Incoming" and reply_to_doc.get("from")) or reply_to_doc.to
	doc = frappe.new_doc("WhatsApp Message")
	doc.update(
		{
			"reference_doctype": reply_to_doc.reference_doctype,
			"reference_name": reply_to_doc.reference_name,
			"message": emoji,
			"to": to,
			"reply_to_message_id": reply_to_doc.message_id,
			"content_type": "reaction",
		}
	)
	return insert_and_send(doc)


def parse_template_parameters(string, parameters):
	for i, parameter in enumerate(parameters, start=1):
		placeholder = "{{" + str(i) + "}}"
		string = string.replace(placeholder, str(parameter))

	return string


def get_from_name(message):
	doc = frappe.get_doc(message["reference_doctype"], message["reference_name"])
	from_name = ""
	if message["reference_doctype"] == "CRM Deal":
		if doc.get("contacts"):
			for c in doc.get("contacts"):
				if c.is_primary:
					from_name = c.full_name or c.mobile_no
					break
		else:
			from_name = doc.get("lead_name")
	else:
		from_name = " ".join(name for name in [doc.get("first_name"), doc.get("last_name")] if name)
	return from_name


def add_roles():
	if "frappe_whatsapp" not in frappe.get_installed_apps():
		return

	role_list = ["Sales Manager", "Sales User"]
	doctypes = ["WhatsApp Message", "WhatsApp Templates", "WhatsApp Settings"]
	for doctype in doctypes:
		for role in role_list:
			if frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role}):
				continue
			add_permission(doctype, role, 0, "write")
			update_permission_property(doctype, role, 0, "create", 1)
			update_permission_property(doctype, role, 0, "delete", 1)
			update_permission_property(doctype, role, 0, "share", 1)
			update_permission_property(doctype, role, 0, "email", 1)
			update_permission_property(doctype, role, 0, "print", 1)
			update_permission_property(doctype, role, 0, "report", 1)
			update_permission_property(doctype, role, 0, "export", 1)
