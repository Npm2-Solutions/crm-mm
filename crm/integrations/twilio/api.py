import json

import frappe
from frappe import _
from twilio.twiml.voice_response import VoiceResponse
from werkzeug.wrappers import Response

from crm.integrations.api import get_contact_by_phone_number
from crm.telephony import inbound, transcription
from crm.telephony.providers import get as get_provider

from .twilio_handler import Twilio, TwilioCallDetails
from .utils import get_public_url


def _signature_check_enabled(settings) -> bool:
	"""On unless it has been switched off on purpose.

	An installation that predates the setting has nothing stored, and the safe
	reading of "nothing stored" for a security check is "on".
	"""
	stored = settings.get("verify_webhook_signature")
	return True if stored is None else bool(frappe.utils.cint(stored))


def _signed_url_candidates(request) -> list[str]:
	"""The spellings of this request that Twilio might have signed.

	Twilio signs the exact URL it called. A reverse proxy can hand the app a
	different scheme or host for the same request, so the few readings that
	legitimately mean the same call are all offered before giving up.
	"""
	seen: set[str] = set()
	urls: list[str] = []

	def add(url: str | None):
		if url and url not in seen:
			seen.add(url)
			urls.append(url)

	add(request.url)
	if request.url.startswith("http://"):
		# a proxy terminating TLS leaves the app believing the call arrived in the clear
		add("https://" + request.url[len("http://") :])
	# werkzeug leaves a bare "?" on full_path when there is no query string
	add(get_public_url((request.full_path or "").rstrip("?")))
	return urls


def _signature_is_valid(auth_token: str | None) -> bool:
	from twilio.request_validator import RequestValidator

	# read the request off frappe.local: outside a web request there is nothing to
	# validate, and asking for a header would raise rather than answer
	request = getattr(frappe.local, "request", None)
	if not (auth_token and request):
		return False

	signature = request.headers.get("X-Twilio-Signature")
	if not signature:
		return False

	validator = RequestValidator(auth_token)
	params = request.form.to_dict(flat=True) if request.form else {}
	return any(validator.validate(url, params, signature) for url in _signed_url_candidates(request))


def validate_twilio_request(args, require_application_sid: bool = False):
	"""Refuse anything Twilio did not send.

	The signature is the only real gate. The Account SID below proves nothing on
	its own — it travels in every request and is visible all over the console —
	so it is checked afterwards, purely to give a clearer error when a webhook has
	been pointed at the wrong account.
	"""
	twilio = Twilio.connect()
	if not twilio:
		frappe.throw(_("Twilio configuration is missing"), frappe.PermissionError)

	if _signature_check_enabled(twilio.settings) and not _signature_is_valid(twilio.auth_token):
		frappe.throw(_("Invalid Twilio signature"), frappe.PermissionError)

	account_sid = frappe.utils.cstr(args.get("AccountSid"))
	if not account_sid or account_sid != frappe.utils.cstr(twilio.account_sid):
		frappe.throw(_("Invalid Twilio account"), frappe.PermissionError)

	if require_application_sid:
		application_sid = frappe.utils.cstr(args.get("ApplicationSid"))
		if not application_sid or application_sid != frappe.utils.cstr(twilio.application_sid):
			frappe.throw(_("Invalid Twilio application"), frappe.PermissionError)

	return twilio


@frappe.whitelist()
def is_enabled():
	return frappe.db.get_single_value("CRM Twilio Settings", "enabled")


@frappe.whitelist()
def usable_caller_ids() -> list[str]:
	"""Numbers this account can present, for the agent's own settings.

	Not sensitive — they are the practice's own numbers, and the alternative is an
	agent typing one Twilio has never heard of and wondering why calls fail.
	"""
	settings = frappe.get_cached_doc("CRM Twilio Settings")
	return settings.usable_caller_ids() if settings.enabled else []


@frappe.whitelist()
def generate_access_token():
	"""Returns access token that is required to authenticate Twilio Client SDK."""
	twilio = Twilio.connect()
	if not twilio:
		return {}

	from_number = frappe.db.get_value("CRM Telephony Agent", frappe.session.user, "twilio_number")
	if not from_number:
		return {
			"ok": False,
			"error": "caller_phone_identity_missing",
			"detail": "Phone number is not mapped to the caller",
		}

	token = twilio.generate_voice_access_token(identity=frappe.session.user)
	return {"token": frappe.safe_decode(token)}


# webhook authenticity is enforced by validate_twilio_request(); guest access itself is unchanged
@frappe.whitelist(allow_guest=True)  # nosemgrep: guest-whitelisted-method
def voice(**kwargs):
	"""This is a webhook called by twilio to get instructions when the voice call request comes to twilio server."""

	def _get_caller_number(caller):
		identity = (caller or "").replace("client:", "").strip()
		if not identity:
			return None
		user = Twilio.emailid_from_identity(identity)
		return frappe.db.get_value("CRM Telephony Agent", user, "twilio_number")

	args = frappe._dict(kwargs)
	twilio = validate_twilio_request(args, require_application_sid=True)

	# Generate TwiML instructions to make a call
	from_number = _get_caller_number(args.Caller)
	if not from_number:
		resp = VoiceResponse()
		resp.say(_("Your account is not configured with a phone number. Please contact your administrator."))
		return Response(resp.to_xml(), mimetype="text/xml")

	call_details = TwilioCallDetails(args, call_from=from_number)
	try:
		create_call_log(call_details)
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="Error while creating Twilio call log")
		frappe.db.commit()
		return Response(_call_failed_response().to_xml(), mimetype="text/xml")

	# outgoing: the person being rung is the one who has not been told yet
	resp = twilio.generate_twilio_dial_response(from_number, args.To, notify_callee=True)
	return Response(resp.to_xml(), mimetype="text/xml")


# webhook authenticity is enforced by validate_twilio_request(); guest access itself is unchanged
@frappe.whitelist(allow_guest=True)  # nosemgrep: guest-whitelisted-method
def twilio_incoming_call_handler(**kwargs):
	args = frappe._dict(kwargs)
	validate_twilio_request(args)

	call_details = TwilioCallDetails(args)
	try:
		call_log = create_call_log(call_details)
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="Error while creating Twilio call log")
		frappe.db.commit()
		return Response(_call_failed_response().to_xml(), mimetype="text/xml")

	# the log goes in so the answering service can hang the callback off it and
	# tell the caller the time it was actually promised for
	instruction = inbound.handle_incoming_call(get_provider("twilio"), args.From, args.To, call_log=call_log)
	frappe.db.commit()
	return Response(instruction.body, mimetype=instruction.mimetype)


def _call_failed_response():
	resp = VoiceResponse()
	resp.say(_("We're unable to connect your call right now. Please try again later."))
	return resp


def create_call_log(call_details: TwilioCallDetails):
	details = call_details.to_dict()

	call_log = frappe.get_doc({**details, "doctype": "CRM Call Log", "telephony_medium": "Twilio"})

	# link call log with lead/deal
	contact_number = details.get("from") if details.get("type") == "Incoming" else details.get("to")
	link(contact_number, call_log)

	call_log.save(ignore_permissions=True)
	frappe.db.commit()
	return call_log


def link(contact_number, call_log):
	contact = get_contact_by_phone_number(contact_number)
	if contact.get("name"):
		doctype = "Contact"
		docname = contact.get("name")
		if contact.get("lead"):
			doctype = "CRM Lead"
			docname = contact.get("lead")
		elif contact.get("deal"):
			doctype = "CRM Deal"
			docname = contact.get("deal")
		call_log.link_with_reference_doc(doctype, docname)


def update_call_log(call_sid, status=None):
	"""Update call log status."""
	twilio = Twilio.connect()
	if not (twilio and frappe.db.exists("CRM Call Log", call_sid)):
		return

	try:
		call_details = twilio.get_call_info(call_sid)
		call_log = frappe.get_doc("CRM Call Log", call_sid)
		call_log.status = TwilioCallDetails.get_call_status(status or call_details.status)
		call_log.duration = call_details.duration
		call_log.start_time = get_datetime_from_timestamp(call_details.start_time)
		call_log.end_time = get_datetime_from_timestamp(call_details.end_time)
		call_log.save(ignore_permissions=True)
		frappe.db.commit()
		return call_log
	except Exception:
		frappe.log_error(title="Error while updating call record")
		frappe.db.commit()


def get_twilio_settings():
	return frappe.get_single("CRM Twilio Settings")


# webhook authenticity is enforced by validate_twilio_request(); guest access itself is unchanged
@frappe.whitelist(allow_guest=True)  # nosemgrep: guest-whitelisted-method
def update_recording_info(**kwargs):
	args = frappe._dict(kwargs)
	validate_twilio_request(args)

	call_sid = args.CallSid
	if not (call_sid and frappe.db.exists("CRM Call Log", call_sid)):
		# retrying will not conjure the call log, so acknowledge instead of handing
		# Twilio a 5xx it would replay for hours
		frappe.log_error(f"Twilio recording for an unknown call: {call_sid}", "CRM Telephony")
		return _acknowledged()

	update_call_log(call_sid)
	try:
		frappe.db.set_value("CRM Call Log", call_sid, "recording_url", args.RecordingUrl)
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "CRM Telephony: failed to capture recording")
		return _acknowledged()

	# set_value bypasses document hooks, so the transcription is asked for here
	# rather than from the CRM Call Log on_update handler
	if transcription.transcribes_automatically():
		transcription.request_transcription(call_sid)
		frappe.db.commit()

	return _acknowledged()


# webhook authenticity is enforced by validate_twilio_request(); guest access itself is unchanged
@frappe.whitelist(allow_guest=True)  # nosemgrep: guest-whitelisted-method
def update_call_status_info(**kwargs):
	args = frappe._dict(kwargs)
	validate_twilio_request(args)

	parent_call_sid = args.ParentCallSid
	if not (parent_call_sid and frappe.db.exists("CRM Call Log", parent_call_sid)):
		frappe.log_error(f"Twilio status for an unknown call: {parent_call_sid}", "CRM Telephony")
		return _acknowledged()

	update_call_log(parent_call_sid, status=args.CallStatus)

	call_info = {
		"ParentCallSid": args.ParentCallSid,
		"CallSid": args.CallSid,
		"CallStatus": args.CallStatus,
		"CallDuration": args.CallDuration,
		"From": args.From,
		"To": args.To,
	}

	try:
		# relayed back onto the call so the agent's browser can follow it live
		client = Twilio.get_twilio_client()
		client.calls(args.ParentCallSid).user_defined_messages.create(content=json.dumps(call_info))
	except Exception:
		# the log is already updated; failing to mirror it into the browser is not
		# worth a retry storm
		frappe.log_error(frappe.get_traceback(), "CRM Telephony: failed to relay call status")

	return _acknowledged()


# webhook authenticity is enforced by validate_twilio_request(); guest access itself is unchanged
@frappe.whitelist(allow_guest=True)  # nosemgrep: guest-whitelisted-method
def recording_notice(**kwargs):
	"""Spoken to the person being called, before they are connected.

	Recording someone without telling them is not a choice a practice gets to
	make, so the notice rides on the same leg as the recording.
	"""
	args = frappe._dict(kwargs)
	twilio = validate_twilio_request(args)

	resp = VoiceResponse()
	twilio.say_notice(resp)
	return Response(resp.to_xml(), mimetype="text/xml")


def _acknowledged() -> Response:
	"""An empty TwiML 200 — received, nothing to say, do not retry."""
	return Response("<?xml version='1.0' encoding='UTF-8'?><Response></Response>", mimetype="text/xml")


def get_datetime_from_timestamp(timestamp):
	from datetime import datetime
	from zoneinfo import ZoneInfo

	if not timestamp:
		return None

	datetime_utc_tz_str = timestamp.strftime("%Y-%m-%d %H:%M:%S%z")
	datetime_utc_tz = datetime.strptime(datetime_utc_tz_str, "%Y-%m-%d %H:%M:%S%z")
	system_timezone = frappe.utils.get_system_timezone()
	converted_datetime = datetime_utc_tz.astimezone(ZoneInfo(system_timezone))
	return frappe.utils.format_datetime(converted_datetime, "yyyy-MM-dd HH:mm:ss")


# webhook authenticity is enforced by validate_twilio_request(); guest access itself is unchanged
@frappe.whitelist(allow_guest=True)  # nosemgrep: guest-whitelisted-method
def incoming_sms_handler(**kwargs):
	"""Webhook called by Twilio when an SMS arrives on one of our numbers."""
	args = frappe._dict(kwargs)
	validate_twilio_request(args)

	from crm.api.sms import create_sms

	try:
		create_sms(
			type="Incoming",
			from_number=args.From,
			to=args.To,
			message=args.Body or "",
		)
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="Error while creating Twilio SMS log")
		frappe.db.commit()

	# empty TwiML: no auto-reply
	return Response("<?xml version='1.0' encoding='UTF-8'?><Response></Response>", mimetype="text/xml")


# webhook authenticity is enforced by validate_twilio_request(); guest access itself is unchanged
@frappe.whitelist(allow_guest=True)  # nosemgrep: guest-whitelisted-method
def update_sms_status_info(**kwargs):
	"""Delivery status callback for outgoing SMS."""
	args = frappe._dict(kwargs)
	validate_twilio_request(args)

	status_map = {
		"queued": "Queued",
		"sent": "Sent",
		"delivered": "Delivered",
		"undelivered": "Undelivered",
		"failed": "Failed",
	}
	status = status_map.get((args.MessageStatus or "").lower())
	name = args.MessageSid and frappe.db.get_value("CRM SMS Message", {"message_sid": args.MessageSid})
	if name and status:
		frappe.db.set_value("CRM SMS Message", name, "status", status)
		frappe.db.commit()
