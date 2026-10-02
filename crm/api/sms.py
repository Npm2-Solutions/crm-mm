# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from crm.api.whatsapp import may_converse, validate_access
from crm.integrations.twilio.twilio_handler import Twilio
from crm.integrations.twilio.utils import get_public_url
from crm.telephony import sms

SMS_FIELDS = [
	"name",
	"owner",
	"type",
	"to",
	"from",
	"message",
	"status",
	"creation",
	"reference_doctype",
	"reference_name",
	"error_message",
]


@frappe.whitelist()
def is_sms_enabled() -> bool:
	return may_converse() and bool(frappe.db.get_single_value("CRM Twilio Settings", "enabled"))


@frappe.whitelist()
def get_sms_messages(reference_doctype: str, reference_name: str) -> list[dict]:
	"""SMS thread of a lead/deal (a deal also includes its originating lead's thread)."""
	reference_doc = validate_access(reference_doctype, reference_name)

	messages = []
	if reference_doctype == "CRM Deal":
		lead = reference_doc.get("lead")
		if lead:
			validate_access("CRM Lead", lead)
			messages = frappe.get_all(
				"CRM SMS Message",
				filters={"reference_doctype": "CRM Lead", "reference_name": lead},
				fields=SMS_FIELDS,
			)

	messages += frappe.get_all(
		"CRM SMS Message",
		filters={"reference_doctype": reference_doctype, "reference_name": reference_name},
		fields=SMS_FIELDS,
	)
	messages.sort(key=lambda m: m.creation)
	return messages


@frappe.whitelist()
def get_sms_stop(reference_doctype: str, reference_name: str) -> str | None:
	"""When the person of the record wrote STOP to the centre's SMS, for the
	composer to say so; None while the automatic SMS reach them."""
	validate_access(reference_doctype, reference_name)
	fermo = sms.fermato_il(reference_doctype, reference_name)
	return str(fermo) if fermo else None


@frappe.whitelist(methods=["POST"])
def send_sms(reference_doctype: str, reference_name: str, to: str, message: str) -> dict:
	"""Send an SMS from the centre's sender and log it on the record."""
	validate_access(reference_doctype, reference_name, permtype="write")
	message = (message or "").strip()
	if not message:
		frappe.throw(_("Message cannot be empty"))
	if not (to or "").strip():
		frappe.throw(_("Recipient number is missing"))
	# one sender for every SMS of the centre (doc 52), never somebody's own line:
	# an Italian landline cannot send SMS, and the answers must reach the centre
	da = sms.mittente()
	if not da:
		frappe.throw(
			_(
				"The SMS cannot leave: the centre has no sender yet. The manager sets it in Settings → Phone → Telephony → Twilio."
			)
		)

	doc = create_sms(
		type="Outgoing",
		from_number=da,
		to=to.strip(),
		message=message,
		reference_doctype=reference_doctype,
		reference_name=reference_name,
	)
	deliver_via_twilio(doc)
	return {"name": doc.name, "status": doc.status}


def create_sms(
	type: str,
	from_number: str,
	to: str,
	message: str,
	reference_doctype: str | None = None,
	reference_name: str | None = None,
	status: str | None = None,
):
	doc = frappe.get_doc(
		{
			"doctype": "CRM SMS Message",
			"type": type,
			"from": from_number,
			"to": to,
			"message": message,
			"status": status or ("Received" if type == "Incoming" else "Queued"),
			"telephony_medium": "Twilio",
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc


def deliver_via_twilio(doc):
	"""Push a queued outgoing message to Twilio; failures land on the doc, not the caller."""
	twilio = Twilio.connect()
	if not twilio:
		doc.db_set({"status": "Failed", "error_message": _("Twilio is not enabled")})
		return
	try:
		sent = twilio.twilio_client.messages.create(
			from_=doc.get("from"),
			to=doc.to,
			body=doc.message,
			status_callback=get_public_url("/api/method/crm.integrations.twilio.api.update_sms_status_info"),
		)
		doc.db_set({"message_sid": sent.sid, "status": "Sent"})
	except Exception:
		frappe.log_error(frappe.get_traceback(), "CRM SMS: Twilio send failed")
		doc.db_set({"status": "Failed", "error_message": _("Provider rejected the message")})


def send_automation_sms(to: str, message: str, reference_doctype=None, reference_name=None) -> bool:
	"""Channel adapter used by the automation engine: best-effort, never raises."""
	try:
		da = sms.mittente()
		if not da:
			return False
		doc = create_sms(
			type="Outgoing",
			from_number=da,
			to=to,
			message=message,
			reference_doctype=reference_doctype,
			reference_name=reference_name,
		)
		deliver_via_twilio(doc)
		return doc.status == "Sent"
	except Exception:
		frappe.log_error(frappe.get_traceback(), "CRM SMS: automation send failed")
		return False
