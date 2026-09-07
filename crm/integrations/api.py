import ipaddress
import socket
from urllib.parse import urlparse, urlunparse

import frappe
import requests
from frappe import _
from frappe.query_builder import Order
from pypika.functions import Replace
from werkzeug.wrappers import Response

from crm.utils import are_same_phone_number, digits_of, parse_phone_number


def _get_recording_credentials(telephony_medium: str) -> tuple | None:
	"""Credentials for fetching a recording, or None when it needs no auth.

	Asked of the provider rather than decided here, so a new carrier does not mean
	another branch in this file. A manual or unrecognised medium (a recording added
	by hand) is fetched as-is, and a provider whose credentials aren't configured
	yet falls back to no auth rather than raising — the proxy attempts the fetch and
	lets the provider decide, instead of 500-ing before the request is even made.
	"""
	from crm.telephony import providers

	provider = providers.for_medium(telephony_medium)
	return provider.recording_credentials() if provider else None


@frappe.whitelist()
def is_call_integration_enabled():
	from crm.telephony import providers

	descriptors = [provider.as_dict() for provider in providers.all_providers()]
	return {
		# name -> bool, the shape the call button has always read
		"integrations": {row["name"]: row["enabled"] for row in descriptors},
		# the full list, so the medium picker learns about a new carrier from the
		# registry instead of from a hardcoded array in the frontend
		"providers": descriptors,
		"default_calling_medium": get_user_default_calling_medium(),
		# deliberately outside "integrations": the answering service answers calls, it
		# does not place them, so it must not make the call buttons appear on its own
		"answering_service": bool(frappe.db.get_single_value("CRM Answering Settings", "enabled")),
		"transcription": bool(frappe.db.get_single_value("CRM Transcription Settings", "enabled")),
	}


def get_user_default_calling_medium():
	if not frappe.db.exists("CRM Telephony Agent", frappe.session.user):
		return None

	default_medium = frappe.db.get_value("CRM Telephony Agent", frappe.session.user, "default_medium")

	if not default_medium:
		return None

	return default_medium


@frappe.whitelist()
def set_default_calling_medium(medium: str):
	if not frappe.db.exists("CRM Telephony Agent", frappe.session.user):
		frappe.get_doc(
			{
				"doctype": "CRM Telephony Agent",
				"user": frappe.session.user,
				"default_medium": medium,
			}
		).insert(ignore_permissions=True)
	else:
		frappe.db.set_value("CRM Telephony Agent", frappe.session.user, "default_medium", medium)

	return get_user_default_calling_medium()


@frappe.whitelist()
def add_note_to_call_log(call_sid: str, note: dict):
	"""Add/Update note to call log based on call sid."""
	if not frappe.has_permission("CRM Call Log", "write", call_sid):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	_note = None
	if not note.get("name"):
		_note = frappe.get_doc(
			{
				"doctype": "FCRM Note",
				"title": note.get("title", "Call Note"),
				"content": note.get("content"),
			}
		).insert(ignore_permissions=True)
	else:
		_note = frappe.set_value("FCRM Note", note.get("name"), "content", note.get("content"))

	call_log = frappe.get_cached_doc("CRM Call Log", call_sid)
	call_log.link_with_reference_doc("FCRM Note", _note.name)
	call_log.save(ignore_permissions=True)

	return _note


@frappe.whitelist()
def add_task_to_call_log(call_sid: str, task: dict):
	"""Add/Update task to call log based on call sid."""
	if not frappe.has_permission("CRM Call Log", "write", call_sid):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	_task = None
	if not task.get("name"):
		_task = frappe.get_doc(
			{
				"doctype": "CRM Task",
				"title": task.get("title"),
				"description": task.get("description"),
				"assigned_to": task.get("assigned_to"),
				"due_date": task.get("due_date"),
				"status": task.get("status"),
				"priority": task.get("priority"),
			}
		).insert(ignore_permissions=True)
	else:
		_task = frappe.get_doc("CRM Task", task.get("name"))
		_task.update(
			{
				"title": task.get("title"),
				"description": task.get("description"),
				"assigned_to": task.get("assigned_to"),
				"due_date": task.get("due_date"),
				"status": task.get("status"),
				"priority": task.get("priority"),
			}
		)
		_task.save(ignore_permissions=True)

	call_log = frappe.get_doc("CRM Call Log", call_sid)
	call_log.link_with_reference_doc("CRM Task", _task.name)
	call_log.save(ignore_permissions=True)

	return _task


@frappe.whitelist()
def get_contact_lead_or_deal_from_number(number: str):
	"""Get contact, lead or deal from the given number."""
	contact = get_contact_by_phone_number(number)
	if not contact.get("name"):
		return None, None

	if contact.get("lead"):
		return contact["lead"], "CRM Lead"
	if contact.get("deal"):
		return contact["deal"], "CRM Deal"

	# A bare contact is nowhere: no chat opens on it — the Contact page has no
	# activity at all — and the Inbox lists conversations by lead or deal. Every
	# contact now belongs to a lead, so ask which one; and if the answer is
	# nobody, say nobody rather than hand the message to a dead end.
	lead = frappe.db.get_value("CRM Lead", {"contact": contact["name"], "converted": 0}, "name")
	return (lead, "CRM Lead") if lead else (None, None)


def adopt_unknown_number(number: str, display_name: str | None = None) -> tuple[str, str] | None:
	"""Give an incoming message from a stranger somewhere to land.

	A message that matches no contact and no lead is stored with no reference,
	and then it exists nowhere anybody looks: not in a chat, which is opened from
	a record, and not in the Inbox, which lists conversations by lead or deal. It
	is received and lost in the same instant.

	So the number becomes a lead, as it does in GoHighLevel. Only for a live
	incoming message: imported chat history arrives in blocks of months and would
	invent hundreds of leads in one go.
	"""
	digits = digits_of(number)
	if len(digits) < 6:
		# not a number anyone could call back
		return None

	# WhatsApp hands the number over without the plus, and parsing it as-is would
	# have phonenumbers guess a country and guess wrong
	parsed = parse_phone_number(f"+{digits}")
	mobile_no = parsed.get("formats", {}).get("E164") if parsed.get("is_valid") else f"+{digits}"

	# two messages arriving together would otherwise each create their own lead
	existing = frappe.db.get_value("CRM Lead", {"mobile_no": mobile_no, "converted": 0}, "name")
	if existing:
		return existing, "CRM Lead"

	lead = frappe.get_doc(
		{
			"doctype": "CRM Lead",
			# the WhatsApp profile name when there is one, the number otherwise:
			# a lead called "Unknown" is one nobody ever opens
			"first_name": (display_name or "").strip() or mobile_no,
			"mobile_no": mobile_no,
			"source": _known_source(),
		}
	)
	lead.insert(ignore_permissions=True)
	return lead.name, "CRM Lead"


def _known_source() -> str | None:
	"""The WhatsApp lead source, when the site has one.

	No source at all beats a wrong one: a lead stamped "Existing Customer"
	because that happened to exist would quietly poison the source report.
	"""
	return "WhatsApp" if frappe.db.exists("CRM Lead Source", "WhatsApp") else None


@frappe.whitelist()
def get_contact_by_phone_number(phone_number: str):
	"""Get contact by phone number."""
	number = parse_phone_number(phone_number)

	if number.get("is_valid"):
		return get_contact(number.get("national_number"), number.get("country"))

	international = _as_international(phone_number)
	if international.get("is_valid"):
		return get_contact(international.get("national_number"), international.get("country"))

	return get_contact(phone_number, number.get("country"), exact_match=True)


def _as_international(phone_number: str) -> dict:
	"""Read a plus-less number as the international one it is.

	WhatsApp hands over "393703400189" and webhooks generally drop the plus. With
	no plus `phonenumbers` falls back to the default region — India — and reads
	that same number as Indian: +91393703400189. The `LIKE` finds the right
	contact and `are_same_phone_number` then rejects it, comparing an Italian
	number against an Indian one. Found and thrown away in the same breath.
	"""
	digits = digits_of(phone_number)
	# a national number would become a different country's if we prefixed it blindly
	if (phone_number or "").strip().startswith("+") or not 8 <= len(digits) <= 15:
		return {}
	return parse_phone_number(f"+{digits}")


def _resolve_validated_ip(hostname: str, port: int) -> str:
	# Refuse any host that resolves to a non-public address (cloud metadata, localhost,
	# private/link-local ranges) and return a single validated IP to connect to. Returning
	# the exact resolved IP — rather than re-resolving at connect time — is what closes the
	# DNS-rebinding TOCTOU window.
	try:
		addrinfos = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
	except socket.gaierror:
		frappe.throw(_("Invalid recording URL"), frappe.ValidationError)

	ips = [info[4][0] for info in addrinfos]
	if not ips:
		frappe.throw(_("Invalid recording URL"), frappe.ValidationError)

	for ip in ips:
		if not ipaddress.ip_address(ip).is_global:
			frappe.throw(_("Recording URL is not allowed"), frappe.ValidationError)

	return ips[0]


class _PinnedIPAdapter(requests.adapters.HTTPAdapter):
	# Connect to a pre-validated IP while keeping the original hostname for the Host header,
	# TLS SNI and certificate verification. The socket therefore reaches the exact IP that was
	# checked, so DNS can't be rebound to an internal address between check and connect.
	def __init__(self, pinned_ip: str, hostname: str, **kwargs):
		self._pinned_ip = pinned_ip
		self._hostname = hostname
		super().__init__(**kwargs)

	def send(self, request, **kwargs):
		parsed = urlparse(request.url)
		literal_ip = (
			f"[{self._pinned_ip}]" if ipaddress.ip_address(self._pinned_ip).version == 6 else self._pinned_ip
		)
		netloc = f"{literal_ip}:{parsed.port}" if parsed.port else literal_ip
		request.url = urlunparse(parsed._replace(netloc=netloc))
		host = f"[{parsed.hostname}]" if ":" in parsed.hostname else parsed.hostname
		request.headers["Host"] = f"{host}:{parsed.port}" if parsed.port else host
		if parsed.scheme == "https":
			self.poolmanager.connection_pool_kw["server_hostname"] = self._hostname
			self.poolmanager.connection_pool_kw["assert_hostname"] = self._hostname
		return super().send(request, **kwargs)


def _safe_get(url: str, auth, headers: dict):
	# TODO: this SSRF-safe fetch (host validation + IP pinning) will likely need to be shared
	# with domain enrichment; until that feature ships, this local helper is the interim workaround.
	parsed = urlparse(url)
	if parsed.scheme not in ("http", "https") or not parsed.hostname:
		frappe.throw(_("Invalid recording URL"), frappe.ValidationError)

	port = parsed.port or (443 if parsed.scheme == "https" else 80)
	pinned_ip = _resolve_validated_ip(parsed.hostname, port)

	session = requests.Session()
	session.mount(f"{parsed.scheme}://", _PinnedIPAdapter(pinned_ip, parsed.hostname))
	resp = session.get(url, auth=auth, headers=headers, stream=True, timeout=30, allow_redirects=False)
	return resp, session


def _fetch_recording(url: str, auth, headers: dict):
	# Follow redirects manually so every hop is validated and IP-pinned: a provider URL can
	# 302 to a signed CDN URL (legitimate), but without per-hop checks a redirect to an
	# internal address would bypass validation. Provider credentials are dropped after the
	# first hop so they aren't leaked to the redirect target.
	current_url = url
	current_auth = auth
	for _hop in range(5):
		resp, session = _safe_get(current_url, current_auth, headers)
		if resp.is_redirect and resp.headers.get("Location"):
			current_url = requests.compat.urljoin(current_url, resp.headers["Location"])
			current_auth = None
			resp.close()
			session.close()
			continue
		resp._pinned_session = session
		return resp

	frappe.throw(_("Too many redirects while fetching recording"), frappe.ValidationError)


def download_recording(call_log, max_bytes: int | None = None) -> tuple[bytes, str]:
	"""Fetch a recording through the same hardened path the in-browser player uses.

	Returns the audio and its content type. ``max_bytes`` caps what is pulled into
	memory: the size of a recording is decided by how long someone talked, so it is
	not ours to trust, and every transcription provider has a ceiling of its own.
	"""
	if not call_log.recording_url:
		frappe.throw(_("Recording URL not found"), frappe.DoesNotExistError)

	auth = _get_recording_credentials(call_log.telephony_medium)
	upstream = _fetch_recording(call_log.recording_url, auth, {})
	try:
		upstream.raise_for_status()
		chunks, total = [], 0
		for chunk in upstream.iter_content(chunk_size=64 * 1024):
			total += len(chunk)
			if max_bytes and total > max_bytes:
				frappe.throw(_("Recording is larger than the configured limit"), frappe.ValidationError)
			chunks.append(chunk)
		return b"".join(chunks), upstream.headers.get("Content-Type") or "audio/mpeg"
	finally:
		upstream.close()
		session = getattr(upstream, "_pinned_session", None)
		if session is not None:
			session.close()


@frappe.whitelist()
def get_recording_url(call_log_name: str):
	"""Proxy a call recording (authenticating with the provider) so it plays in the browser.

	Forwards the browser's Range request to the provider and passes the response back with
	Accept-Ranges/Content-Length set. Without range support the HTML <audio> element can't
	read the recording's duration (shows 0:00) or seek within it.
	"""
	if not call_log_name or not frappe.db.exists("CRM Call Log", call_log_name):
		frappe.throw(_("Call log not found"), frappe.DoesNotExistError)

	log = frappe.get_doc("CRM Call Log", call_log_name)
	log.check_permission("read")

	if not log.recording_url:
		frappe.throw(_("Recording URL not found"), frappe.DoesNotExistError)

	auth = _get_recording_credentials(log.telephony_medium)
	# forward the browser's Range header so the provider (Twilio/Exotel CDN) can return
	# just the requested bytes; falls back to the full file if it doesn't support ranges
	req_headers = {}
	range_header = frappe.get_request_header("Range")
	if range_header:
		req_headers["Range"] = range_header

	# stream instead of buffering the whole file: the provider's Content-Length reaches
	# the browser immediately so the <audio> element can show the duration right away,
	# rather than waiting for the entire recording to download server-side first
	upstream = _fetch_recording(log.recording_url, auth, req_headers)
	upstream.raise_for_status()

	def _stream():
		try:
			yield from upstream.iter_content(chunk_size=64 * 1024)
		finally:
			upstream.close()
			session = getattr(upstream, "_pinned_session", None)
			if session is not None:
				session.close()

	response = Response(
		_stream(),
		status=upstream.status_code,
		mimetype=upstream.headers.get("Content-Type") or "audio/mpeg",
	)
	response.headers["Accept-Ranges"] = "bytes"
	for header in ("Content-Length", "Content-Range"):
		if upstream.headers.get(header):
			response.headers[header] = upstream.headers[header]
	return response


def get_contact(phone_number: str, country: str = "IN", exact_match: bool = False):
	if not phone_number:
		return {"mobile_no": phone_number}

	cleaned_number = (
		phone_number.strip()
		.replace(" ", "")
		.replace("-", "")
		.replace("(", "")
		.replace(")", "")
		.replace("+", "")
	)

	# Check if the number is associated with a contact.
	# Search all of a contact's numbers (phone_nos child table) and not just the
	# primary mobile_no, so calls from a secondary number still resolve.
	Contact = frappe.qb.DocType("Contact")
	ContactPhone = frappe.qb.DocType("Contact Phone")
	normalized_phone = Replace(
		Replace(Replace(Replace(Replace(ContactPhone.phone, " ", ""), "-", ""), "(", ""), ")", ""), "+", ""
	)

	query = (
		frappe.qb.from_(ContactPhone)
		.join(Contact)
		.on(ContactPhone.parent == Contact.name)
		.select(
			Contact.name,
			Contact.full_name,
			Contact.image,
			Contact.mobile_no,
			ContactPhone.phone.as_("matched_phone"),
		)
		.where(ContactPhone.parenttype == "Contact")
		.where(normalized_phone.like(f"%{cleaned_number}%"))
		.orderby(Contact.modified, order=Order.desc)
	)
	contacts = query.run(as_dict=True)

	if len(contacts):
		# Check if the contact is associated with a deal
		for contact in contacts:
			if frappe.db.exists("CRM Contacts", {"contact": contact.name, "is_primary": 1}):
				deal = frappe.db.get_value(
					"CRM Contacts", {"contact": contact.name, "is_primary": 1}, "parent"
				)
				if are_same_phone_number(
					contact.matched_phone, phone_number, country, validate=not exact_match
				):
					contact["deal"] = deal
					return contact

	# Else, Check if the number is associated with a lead
	Lead = frappe.qb.DocType("CRM Lead")
	normalized_phone = Replace(
		Replace(Replace(Replace(Replace(Lead.mobile_no, " ", ""), "-", ""), "(", ""), ")", ""), "+", ""
	)

	query = (
		frappe.qb.from_(Lead)
		.select(Lead.name, Lead.lead_name, Lead.image, Lead.mobile_no)
		.where(Lead.converted == 0)
		.where(normalized_phone.like(f"%{cleaned_number}%"))
		.orderby("modified", order=Order.desc)
	)
	leads = query.run(as_dict=True)

	if len(leads):
		for lead in leads:
			if are_same_phone_number(lead.mobile_no, phone_number, country, validate=not exact_match):
				lead["lead"] = lead.name
				lead["full_name"] = lead.lead_name
				return lead

	if len(contacts) and are_same_phone_number(
		contacts[0].matched_phone, phone_number, country, validate=not exact_match
	):
		return contacts[0]

	return {"mobile_no": phone_number}
