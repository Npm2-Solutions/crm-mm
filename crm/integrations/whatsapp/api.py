# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""WhatsApp connection — client-site side.

The client never sees a token: they press Connect, the hub runs Embedded Signup
(where they scan the QR code from their WhatsApp Business app), and hands the
credentials back here, signed with the relay secret. This module turns them into
a ready `WhatsApp Account` for frappe_whatsapp, which owns the messaging itself.
"""

import json

import frappe
import requests
from frappe import _
from frappe.utils import get_url
from werkzeug.wrappers import Response

from crm.integrations.meta.client import (
	GRAPH_BASE,
	GRAPH_VERSION,
	MetaAPIError,
	get_settings,
	get_whatsapp_app_id,
	get_whatsapp_app_secret,
	whatsapp_graph_get,
	whatsapp_graph_post,
)
from crm.integrations.meta.oauth import is_hub
from crm.integrations.meta.relay import sign as relay_sign
from crm.integrations.meta.relay import valid_relay_signature
from crm.integrations.whatsapp.signup import CONNECT_PATH, config_id, make_state

RELAY_TIMEOUT = 15

MANAGER_ROLES = {"System Manager", "Sales Manager"}


def _check_manager():
	if not MANAGER_ROLES & set(frappe.get_roles()):
		frappe.throw(_("Only sales managers can manage WhatsApp"), frappe.PermissionError)


def whatsapp_installed() -> bool:
	return (
		frappe.db.exists("DocType", "WhatsApp Account") and "frappe_whatsapp" in frappe.get_installed_apps()
	)


def hub_url() -> str:
	from crm.integrations.meta.oauth import hub_url as meta_hub

	return meta_hub() or get_url().rstrip("/")


@frappe.whitelist()
def get_status() -> dict:
	_check_manager()
	if not whatsapp_installed():
		return {"installed": False}

	accounts = frappe.get_all(
		"WhatsApp Account",
		fields=["name", "phone_id", "business_id", "status"],
		order_by="creation desc",
	)
	# read the flag frappe_whatsapp actually sends from, not the Settings link
	default = frappe.db.get_value("WhatsApp Account", {"is_default_outgoing": 1}, "name") or (
		frappe.db.get_single_value("WhatsApp Settings", "default_outgoing_account")
	)
	return {
		"installed": True,
		"can_connect": bool(get_whatsapp_app_id() and config_id()),
		# say WHICH piece is missing: "ask your provider" left nobody, the
		# provider included, able to tell what to do next
		"missing": missing_requirements(),
		"accounts": accounts,
		"default_account": default,
		"connected": bool(accounts),
	}


def missing_requirements() -> list[dict]:
	"""What still has to exist before the QR connection can run at all.

	None of it can be created from the CRM: the Meta app is the agency's, and
	Embedded Signup is unlocked by Meta, not by configuration.
	"""
	missing = []
	if not get_whatsapp_app_id():
		missing.append(
			{
				"key": "whatsapp_app_id",
				"what": _("The WhatsApp app is not configured"),
				"how": _(
					"Set whatsapp_app_id and whatsapp_app_secret in the bench config. Leave them out "
					"only if WhatsApp lives in the same Meta app as Facebook, in which case "
					"meta_app_id and meta_app_secret are used."
				),
			}
		)
	if not config_id():
		missing.append(
			{
				"key": "whatsapp_signup_config_id",
				"what": _("Embedded Signup is not configured"),
				"how": _(
					"On the Meta app, create a Facebook Login for Business configuration of type "
					"WhatsApp Embedded Signup, and put its id in whatsapp_signup_config_id. Meta "
					"only offers it to apps registered as a WhatsApp Business Tech Provider — that "
					"registration comes first."
				),
			}
		)
	return missing


WEBHOOK_PATH = "/api/method/crm.integrations.whatsapp.webhook.handle"

# What the CRM needs to see. `messages` alone is the plain Cloud API flow;
# Coexistence adds the rest — without `smb_message_echoes` the CRM never sees
# what the business writes from its own phone, and without `history` the past
# conversations are never imported.
WEBHOOK_FIELDS = "messages,smb_message_echoes,history,smb_app_state_sync,message_template_status_update"


@frappe.whitelist()
def get_webhook() -> dict:
	"""The webhook this hub expects on the WhatsApp app, and whether it is set."""
	_check_manager()
	settings = get_settings()
	configured = False
	error = ""
	if is_hub() and get_whatsapp_app_id() and get_whatsapp_app_secret():
		try:
			data = whatsapp_graph_get(f"{get_whatsapp_app_id()}/subscriptions", _app_token())
			for row in data.get("data") or []:
				if row.get("object") == "whatsapp_business_account":
					configured = get_url(WEBHOOK_PATH) in str(row)
		except MetaAPIError as exc:
			error = str(exc)
	return {
		"is_hub": is_hub(),
		"url": get_url(WEBHOOK_PATH),
		"verify_token": settings.webhook_verify_token or "",
		"fields": WEBHOOK_FIELDS,
		"configured": configured,
		"error": error,
	}


def _app_token() -> str:
	return f"{get_whatsapp_app_id()}|{get_whatsapp_app_secret()}"


@frappe.whitelist(methods=["POST"])
def configure_webhook() -> dict:
	"""Register this hub as the WhatsApp app's webhook, without leaving the CRM.

	The WhatsApp app is a different app from the Facebook one, so its webhook
	does not come along with the Meta one: it has to be registered separately,
	and doing it by hand means copying a URL and a verify token into
	developers.facebook.com. Meta verifies the callback synchronously, so the
	hub must already be reachable over HTTPS.
	"""
	_check_manager()
	if not is_hub():
		frappe.throw(_("The webhook is configured centrally by your provider"))
	settings = get_settings()
	if not settings.webhook_verify_token:
		frappe.throw(_("Open Settings → Meta connection once to generate a verify token"))
	if not get_whatsapp_app_id() or not get_whatsapp_app_secret():
		frappe.throw(_("Set whatsapp_app_id and whatsapp_app_secret in the bench config first"))
	try:
		whatsapp_graph_post(
			f"{get_whatsapp_app_id()}/subscriptions",
			_app_token(),
			{
				"object": "whatsapp_business_account",
				"callback_url": get_url(WEBHOOK_PATH),
				"fields": WEBHOOK_FIELDS,
				"verify_token": settings.webhook_verify_token,
				"include_values": "true",
			},
		)
	except MetaAPIError as exc:
		frappe.throw(_("Could not configure the webhook automatically: {0}").format(exc))
	return get_webhook()


CLAIM_PATH = "/api/method/crm.integrations.whatsapp.api.claim_route"


def app_is_subscribed(waba_id: str, token: str) -> bool:
	"""Is our app among the ones Meta notifies for this WhatsApp Business account?"""
	data = whatsapp_graph_get(f"{waba_id}/subscribed_apps", token)
	app_id = str(get_whatsapp_app_id())
	for row in data.get("data") or []:
		api_data = row.get("whatsapp_business_api_data") or {}
		if str(api_data.get("id")) == app_id:
			return True
	return False


def claim_route_on_hub(waba_id: str, phone_number_id: str, display_number: str = "") -> None:
	"""Tell the hub that this CRM owns the account, so it forwards its messages here.

	The webhook is registered per app and therefore lands on the hub for every
	client at once; the route is what turns one incoming entry into a delivery to
	one site. Embedded Signup records it as it goes — a number added by hand has
	nobody to do it, and without it the hub silently drops everything.
	"""
	site = get_url().rstrip("/")
	if is_hub():
		from crm.integrations.whatsapp.signup import claim_route as record_route

		record_route(waba_id, phone_number_id, display_number, site)
		return

	body = json.dumps(
		{
			"waba_id": waba_id,
			"phone_number_id": phone_number_id,
			"display_phone_number": display_number or "",
			"site": site,
		}
	).encode()
	response = requests.post(
		f"{hub_url()}{CLAIM_PATH}",
		data=body,
		headers={"Content-Type": "application/json", "X-CRM-Relay-Signature": relay_sign(body)},
		timeout=RELAY_TIMEOUT,
	)
	if response.status_code >= 300:
		raise ValueError(f"HTTP {response.status_code}: {response.text[:200]}")


def wire_up_delivery(account) -> list[dict]:
	"""Everything that has to be true before a reply can come back in.

	Sending needs only a token; receiving needs Meta to be subscribed to the
	account *and* the hub to know where to forward what it receives. Both are
	idempotent, so this doubles as the check: what it cannot fix, it names.
	"""
	problems = []
	token = account.get_password("token", raise_exception=False)
	waba_id = account.get("business_id")
	if not token:
		problems.append(
			{
				"key": "token",
				"what": _("This number has no access token"),
				"detail": _("Add it again with its credentials."),
			}
		)
		return problems
	if not waba_id:
		# both remaining steps are keyed by the business account: without it
		# there is nothing to subscribe and nothing to route
		problems.append(
			{
				"key": "waba_id",
				"what": _("This number has no WhatsApp Business Account id"),
				"detail": _("Without it Meta cannot be asked to send its messages anywhere."),
			}
		)
		return problems

	try:
		if not app_is_subscribed(waba_id, token):
			whatsapp_graph_post(f"{waba_id}/subscribed_apps", token, {})
	except MetaAPIError as exc:
		problems.append(
			{
				"key": "subscribed_apps",
				"what": _("Meta is not sending this number's messages to the app"),
				"detail": str(exc)[:300],
			}
		)

	try:
		claim_route_on_hub(waba_id, account.get("phone_id") or "", account.get("account_name") or "")
	except Exception as exc:
		frappe.log_error(frappe.get_traceback(), "WhatsApp: could not claim the route on the hub")
		problems.append(
			{
				"key": "route",
				"what": _("The hub does not know this number belongs to this CRM"),
				"detail": str(exc)[:300],
			}
		)
	return problems


@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
def claim_route():
	"""Client site → hub: this CRM owns this WhatsApp account.

	Guest-accessible because the caller is another of our sites rather than a
	logged-in user; the relay signature over the exact body authenticates it, and
	an account already routed elsewhere is refused rather than reassigned.
	"""
	raw_body = frappe.request.get_data() or b""
	if not valid_relay_signature(frappe.request.headers.get("X-CRM-Relay-Signature"), raw_body):
		return Response("invalid signature", status=403, mimetype="text/plain")

	try:
		data = json.loads(raw_body)
	except ValueError:
		return Response("bad payload", status=400, mimetype="text/plain")

	from crm.integrations.whatsapp.signup import allowed_site
	from crm.integrations.whatsapp.signup import claim_route as record_route

	site = (data.get("site") or "").rstrip("/")
	waba_id = data.get("waba_id") or ""
	if not site or not waba_id or not allowed_site(site):
		return Response("refused", status=403, mimetype="text/plain")

	try:
		record_route(waba_id, data.get("phone_number_id") or "", data.get("display_phone_number") or "", site)
	except frappe.ValidationError as exc:
		return Response(str(exc)[:200], status=409, mimetype="text/plain")
	return Response(json.dumps({"ok": True}), mimetype="application/json")


@frappe.whitelist(methods=["POST"])
def recheck_delivery(name: str) -> dict:
	"""Make incoming messages possible for this number, and say what is missing.

	Everything it does is idempotent, so the button that repairs a number and the
	button that checks one are the same button.
	"""
	_check_manager()
	if not frappe.db.exists("WhatsApp Account", name):
		frappe.throw(_("That number is not connected"))
	problems = wire_up_delivery(frappe.get_doc("WhatsApp Account", name))
	return {"ok": not problems, "problems": problems}


@frappe.whitelist(methods=["POST"])
def add_account(phone_number_id: str, waba_id: str, token: str, account_name: str | None = None) -> dict:
	"""Add a number with credentials typed in, instead of Embedded Signup.

	Clients connect by scanning a QR — that stays the one path offered to them.
	This is the way in for a number Embedded Signup cannot reach: the test
	number Meta lends every app, which is what an agency needs to record the
	App Review videos before it is a Tech Provider at all, and which otherwise
	leaves the CRM with no way to send a single message.
	"""
	_check_manager()
	if not whatsapp_installed():
		frappe.throw(_("The WhatsApp app is not installed on this site"))
	phone_number_id = (phone_number_id or "").strip()
	waba_id = (waba_id or "").strip()
	if not phone_number_id or not waba_id or not (token or "").strip():
		frappe.throw(_("Phone number ID, WhatsApp Business Account ID and token are all required"))

	name = upsert_account(
		{
			"phone_number_id": phone_number_id,
			"waba_id": waba_id,
			"token": token.strip(),
			"verified_name": (account_name or "").strip() or None,
		}
	)
	frappe.db.commit()

	# sending would work from here; receiving would not, and silently
	problems = wire_up_delivery(frappe.get_doc("WhatsApp Account", name))
	return {"account": name, "problems": problems}


@frappe.whitelist()
def get_connect_url() -> dict:
	"""Where to send the browser to run Embedded Signup on the hub."""
	_check_manager()
	if not whatsapp_installed():
		frappe.throw(_("The WhatsApp app is not installed on this site"))
	if not config_id():
		frappe.throw(_("WhatsApp signup is not configured yet — ask your provider"))
	state = make_state(get_url().rstrip("/"))
	return {"url": f"{hub_url()}{CONNECT_PATH}?state={state}"}


@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
def receive_connection():
	"""Hub → this site: the credentials of a freshly connected WhatsApp number.

	Guest-accessible: the caller is the hub, not a logged-in user. It is
	authenticated by the relay signature over the exact body, so nobody else can
	inject an account.
	"""
	raw_body = frappe.request.get_data() or b""
	if not valid_relay_signature(frappe.request.headers.get("X-CRM-Relay-Signature"), raw_body):
		return Response("invalid signature", status=403, mimetype="text/plain")

	try:
		data = json.loads(raw_body)
	except ValueError:
		return Response("bad payload", status=400, mimetype="text/plain")

	if not whatsapp_installed():
		return Response("whatsapp app not installed", status=400, mimetype="text/plain")

	try:
		name = upsert_account(data)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "WhatsApp: could not store the connection")
		return Response("could not store account", status=500, mimetype="text/plain")

	frappe.db.commit()
	return Response(json.dumps({"ok": True, "account": name}), mimetype="application/json")


def upsert_account(data: dict) -> str:
	"""Create or refresh the frappe_whatsapp account for this number.

	Only fields the installed version actually has are written, so a different
	frappe_whatsapp release cannot break the connection.
	"""
	phone_id = data.get("phone_number_id")
	if not phone_id:
		frappe.throw(_("No phone number id in the connection payload"))

	values = {
		"token": data.get("token"),
		"phone_id": phone_id,
		# `frappe_whatsapp` builds every call as f"{url}/{version}/{phone_id}/messages".
		# Without these two the request is never issued and the send dies far from
		# here, on `frappe.flags.integration_request.json()` of a request that was
		# never made: "'NoneType' object has no attribute 'json'".
		"url": GRAPH_BASE,
		"version": GRAPH_VERSION,
		"business_id": data.get("waba_id"),
		"app_id": get_whatsapp_app_id(),
		"webhook_verify_token": frappe.get_cached_value(
			"CRM Meta Settings", "CRM Meta Settings", "webhook_verify_token"
		),
		"status": "Active",
		"enabled": 1,
		"account_name": data.get("verified_name") or data.get("display_phone_number") or phone_id,
	}
	known = {df.fieldname for df in frappe.get_meta("WhatsApp Account").fields}
	# keep only what this frappe_whatsapp version understands
	values = {key: value for key, value in values.items() if key in known and value is not None}

	existing = frappe.db.get_value("WhatsApp Account", {"phone_id": phone_id}, "name")
	if existing:
		doc = frappe.get_doc("WhatsApp Account", existing)
		for field in ("url", "version"):
			# an endpoint someone pinned by hand stays pinned
			if doc.get(field):
				values.pop(field, None)
		doc.update(values)
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc({"doctype": "WhatsApp Account", **values})
		doc.insert(ignore_permissions=True)

	make_default_if_first(doc)
	return doc.name


def make_default_if_first(doc) -> None:
	"""The first number connected becomes the one messages go through.

	`frappe_whatsapp` resolves the account from the **checkboxes on the account
	itself** (`is_default_outgoing` / `is_default_incoming`), not from the links
	in `WhatsApp Settings`: see `utils.get_whatsapp_account`. Setting only the
	links left every send failing with "Please set a default outgoing WhatsApp
	Account", with a number that looked perfectly connected.

	Both are written anyway — the links are what the Settings screen shows, and
	a future release may go back to reading them.
	"""
	known = {df.fieldname for df in frappe.get_meta("WhatsApp Account").fields}
	for field, kind in (("is_default_outgoing", "outgoing"), ("is_default_incoming", "incoming")):
		if field not in known:
			continue
		if frappe.db.exists("WhatsApp Account", {field: 1, "name": ["!=", doc.name]}):
			continue  # somebody else already holds this role
		if not doc.get(field):
			doc.db_set(field, 1, update_modified=False)
		link = f"default_{kind}_account"
		if frappe.get_meta("WhatsApp Settings").has_field(link) and not frappe.db.get_single_value(
			"WhatsApp Settings", link
		):
			frappe.db.set_single_value("WhatsApp Settings", link, doc.name)


@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
def receive_events():
	"""Hub → this site: the Coexistence webhooks frappe_whatsapp cannot read.

	Messages the business sends from its phone, imported chat history and the
	contact list. Authenticated by the relay signature over the exact body.
	"""
	raw_body = frappe.request.get_data() or b""
	if not valid_relay_signature(frappe.request.headers.get("X-CRM-Relay-Signature"), raw_body):
		return Response("invalid signature", status=403, mimetype="text/plain")

	try:
		payload = json.loads(raw_body)
	except ValueError:
		return Response("bad payload", status=400, mimetype="text/plain")

	if not whatsapp_installed():
		return Response("whatsapp app not installed", status=400, mimetype="text/plain")

	from crm.integrations.whatsapp.coexistence import ingest_entry

	tally = {"echoes": 0, "history": 0, "contacts": 0}
	for entry in payload.get("entry") or []:
		try:
			counts = ingest_entry(entry)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "WhatsApp: coexistence ingest failed")
			continue
		for key, value in counts.items():
			tally[key] += value
	frappe.db.commit()
	return Response(json.dumps({"ok": True, **tally}), mimetype="application/json")


@frappe.whitelist(methods=["POST"])
def set_default_account(name: str) -> dict:
	"""Send from this number from now on.

	The flag lives on the account and only one may hold it, so the previous
	holder has to give it up first — `frappe_whatsapp` picks the account by
	`is_default_outgoing`, and two of them would make the choice arbitrary.
	"""
	_check_manager()
	if not frappe.db.exists("WhatsApp Account", name):
		frappe.throw(_("That number is not connected"))
	if frappe.get_meta("WhatsApp Account").has_field("is_default_outgoing"):
		for other in frappe.get_all(
			"WhatsApp Account", filters={"is_default_outgoing": 1, "name": ["!=", name]}, pluck="name"
		):
			frappe.db.set_value("WhatsApp Account", other, "is_default_outgoing", 0, update_modified=False)
		frappe.db.set_value("WhatsApp Account", name, "is_default_outgoing", 1, update_modified=False)
	if frappe.get_meta("WhatsApp Settings").has_field("default_outgoing_account"):
		frappe.db.set_single_value("WhatsApp Settings", "default_outgoing_account", name)
	return {"default_account": name}


@frappe.whitelist(methods=["POST"])
def disconnect(name: str) -> dict:
	"""Remove a number from this CRM. The WhatsApp Business app keeps working."""
	_check_manager()
	settings = frappe.get_doc("WhatsApp Settings")
	if settings.get("default_outgoing_account") == name:
		settings.default_outgoing_account = None
		settings.save(ignore_permissions=True)
	frappe.delete_doc("WhatsApp Account", name, ignore_permissions=True)
	return get_status()
