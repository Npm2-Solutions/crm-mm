# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""WhatsApp Embedded Signup — hub side.

Embedded Signup runs in the browser through Facebook's JS SDK, so the page that
hosts it must be listed in the app's *Allowed domains*. With one Frappe site per
client that list could never be complete, so the page lives on the hub
(`/whatsapp-connect`) and the client site only sends the user there with a
signed state saying who it is.

The code the flow returns lives for **30 seconds**, which is too tight to bounce
through the browser: the hub exchanges it for the business token itself and
hands the result to the client site server-to-server, signed with the relay
secret.

Meta reference: Embedded Signup v4 (v2 is retired on 15 October 2026).
"""

import base64
import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import frappe
import requests
from frappe import _
from frappe.utils import get_url

from crm.integrations.meta.client import (
	MetaAPIError,
	get_settings,
	get_whatsapp_app_id,
	get_whatsapp_app_secret,
	whatsapp_app_token,
	whatsapp_graph_get,
	whatsapp_graph_post,
)
from crm.integrations.meta.relay import relay_secret, sign
from crm.integrations.meta.relay import sign as relay_sign
from crm.utils.sites import is_this_site

CONNECT_PATH = "/whatsapp-connect"
# An hour, not fifteen minutes. The state says nothing but "which site started
# this" and is signed, so a long life costs nothing — while a short one costs
# everything: a Coexistence onboarding means opening WhatsApp on the phone,
# confirming, copying a verification code and coming back, and a person who
# fumbles the Facebook login first is easily past a quarter of an hour. When it
# expired mid-flow the session logging went silent and the token exchange
# failed, which is precisely the case nobody could see.
STATE_TTL = 3600
TIMEOUT = 30


def config_id() -> str:
	"""Facebook Login for Business configuration for Embedded Signup v4.

	The bench config wins, so an agency that sets it once for every client site
	keeps doing that. Settings is the fallback, because on a managed host the
	bench is not somebody's to edit and the id is the last thing standing
	between a client and the QR.
	"""
	return frappe.conf.get("whatsapp_signup_config_id") or get_settings().whatsapp_signup_config_id or ""


def config_in_use() -> dict:
	"""Which login configuration the CRM sends, and where that value came from.

	An app can hold several, and which one is used changes what the client gets:
	how long their token lives, and whether they are asked to log in with a
	business portfolio at all. Meta's dashboard shows what is selected *there*,
	in its own builder — which is a different thing from what this CRM sends,
	and telling the two apart by guesswork has already cost an afternoon.
	"""
	return {
		"config_id": config_id(),
		"from_bench": bool(frappe.conf.get("whatsapp_signup_config_id")),
	}


def _state_secret() -> str:
	return relay_secret() or frappe.local.conf.get("encryption_key") or frappe.local.site


def sign_state(payload: str) -> str:
	return hmac.new(_state_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()[:24]


def make_state(site: str) -> str:
	payload = json.dumps({"t": int(time.time()), "site": site.rstrip("/")})
	return f"{base64.urlsafe_b64encode(payload.encode()).decode()}.{sign_state(payload)}"


def parse_state(state: str | None, allow_expired: bool = False) -> dict | None:
	"""The site that started this flow, if the state really came from us.

	`allow_expired` exists for one caller: the session log. An onboarding that
	ran long is exactly the one worth recording, and refusing to write it down
	because the link aged is how a stalled flow becomes invisible. Nothing is
	granted on an expired state — only remembered.
	"""
	if not state or "." not in state:
		return None
	try:
		encoded, signature = state.rsplit(".", 1)
		payload = base64.urlsafe_b64decode(encoded.encode()).decode()
		if not hmac.compare_digest(signature, sign_state(payload)):
			return None
		parsed = json.loads(payload)
	except Exception:
		return None
	if int(time.time()) - int(parsed.get("t") or 0) > STATE_TTL:
		if not allow_expired:
			return None
		parsed["expired"] = True
	return parsed


def allowed_site(site: str) -> bool:
	"""Same closed list the page routing uses: only our own sites may connect."""
	allowed = frappe.conf.get("meta_relay_sites")
	if not allowed:
		return True
	return site.rstrip("/") in [s.rstrip("/") for s in allowed]


OUTCOME_BY_EVENT = {
	"FINISH": "Completed",
	"FINISH_ONLY_WABA": "Completed",
	"FINISH_WHATSAPP_BUSINESS_APP_ONBOARDING": "Completed",
	"CANCEL": "Cancelled",
	"ERROR": "Error",
}


# What Meta calls the parts of an error, across the two places it reports one:
# the `WA_EMBEDDED_SIGNUP` message event while the flow runs, and the OAuth
# query string when it hands the browser back. The names differ; the meaning
# does not, so they land in the same fields.
ERROR_KEYS = {
	"error_message": ("error_message", "error_description", "error_reason", "error"),
	"error_code": ("error_code", "code"),
	"error_id": ("error_id", "fbtrace_id"),
	"session_id": ("session_id",),
	# Meta asks for this one too when you open a ticket: the moment the customer
	# hit the error, which is how support finds it in their own logs.
	"reported_at": ("timestamp",),
}


# Meta does not document every code it sends, so this is where what we worked
# out goes — plainly labelled as a lead, never as a verdict. It exists because
# the alternative is a number on screen and an afternoon of searching that ends
# where ours ended: nobody documents it.
#
# `1690xxx` is documented in exactly one place, *Business Owned Businesses*
# (`POST /{business_id}/owned_businesses`, `client_businesses`) — the calls with
# which an aggregator business links a client business. That is the step
# Embedded Signup runs when the customer picks their portfolio, so the code is
# about the portfolio, not about WhatsApp.
# Each hint is a lambda, not a string: a module is imported once per worker and
# shared by every site and every user on it, so calling _() out here would freeze
# these paragraphs in whichever language happened to be loaded first.
# nosemgrep: frappe-breaks-multitenancy — the lambda is the point: _() runs per call, not once at import
SIGNUP_HINTS = (
	(
		"1690",
		lambda: _(
			"This code belongs to the business-portfolio step, not to WhatsApp. It is the family "
			"Meta documents under client businesses — an aggregator business attaching a client "
			"business — so when it fires on the last screen, the one that offers to share the "
			"account, the id it names is a portfolio that cannot be the client. The usual reason "
			"is that it is your own: the customer's WhatsApp account has to live in a portfolio "
			"other than the one that owns the Meta app. A second documented cause is a WhatsApp "
			"Business Account created through the developer app, which Embedded Signup cannot "
			"select at all. A sandbox test account rules out both at once."
		),
	),
	(
		"3441",
		lambda: _(
			"Meta refused for want of a right over a resource, and it does not say which. The "
			"likeliest one is the WhatsApp Business app account behind the number just typed: "
			"after that number the flow has to read it, to show the business its own name and "
			"picture, and that read is part of Coexistence. If Coexistence is not switched on "
			"for the flow, there is no right to read it. The second candidate is the business "
			"portfolio chosen a screen earlier, where Admin is required and membership is not "
			"enough. What it is almost certainly not is the phone number itself."
		),
	),
	(
		"200",
		lambda: _(
			"Meta refused for want of permission. On a live app only permissions approved for "
			"Advanced Access appear in the flow at all."
		),
	),
)


def hint_for(error_code: str | None) -> str:
	"""What we know about a code Meta did not document. A lead, not a verdict."""
	code = str(error_code or "")
	for prefix, hint in SIGNUP_HINTS:
		if code.startswith(prefix):
			return hint()
	return ""


def error_fields(data: dict) -> dict:
	"""Meta's own words about a failure, pulled out of whatever shape they came in.

	`error_id` and `session_id` are the two values Meta asks for when you open a
	support ticket, which is the whole reason they are worth a field of their
	own rather than a line inside a JSON blob nobody opens.
	"""
	found = {}
	for field, keys in ERROR_KEYS.items():
		for key in keys:
			value = data.get(key)
			if value:
				# error_message is Small Text; the rest are Data, and a Data
				# column is a varchar(140) that raises rather than truncates.
				found[field] = str(value)[: 2000 if field == "error_message" else 140]
				break
	return found


@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
def log_session_event(
	state: str, event: str, data: str | dict | None = None, csrf_token: str | None = None
) -> dict:
	"""Session logging — Meta requires Embedded Signup to be implemented with it.

	The hub page reports every step the business customer goes through, so an
	onboarding that stalls or is abandoned can actually be supported instead of
	guessed at. Nothing here is trusted: the state carries the signature, and
	only the fields we know are stored.

	`csrf_token` is never read here — the page sends it in the body because
	`sendBeacon` cannot set a header, and Frappe takes it off `form_dict` before
	we are called. It is named in the signature so that it does not arrive as an
	unexpected argument.
	"""
	parsed = parse_state(state, allow_expired=True)
	if not parsed:
		return {"ok": False}
	if isinstance(data, str):
		try:
			data = json.loads(data)
		except ValueError:
			data = {"raw": data[:500]}
	data = data or {}

	frappe.get_doc(
		{
			"doctype": "WhatsApp Signup Session",
			"site_url": parsed["site"],
			"event": ("expired: " + (event or ""))[:140] if parsed.get("expired") else (event or "")[:140],
			"current_step": (data.get("current_step") or "")[:140],
			"waba_id": data.get("waba_id") or "",
			"phone_number_id": data.get("phone_number_id") or "",
			"outcome": OUTCOME_BY_EVENT.get(event, "In Progress"),
			# Meta's own words, out of `details` and into fields you can read in
			# a list. The payload was always stored; it took opening a JSON blob
			# to find out that the flow had said something specific.
			**error_fields(data),
			"details": json.dumps(data)[:5000],
		}
	).insert(ignore_permissions=True)
	return {"ok": True}


@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
def complete_signup(
	state: str,
	code: str,
	waba_id: str = "",
	phone_number_id: str = "",
	redirected: int | str = 0,
) -> dict:
	"""Called by the hub page as soon as Embedded Signup finishes.

	Guest-accessible because the browser session belongs to the client site, not
	to the hub; the signed state is what authenticates the request.

	`waba_id` and `phone_number_id` are optional because the browser cannot
	always report them: see `discover_assets`. `redirected` says the code came
	back through the full-page fallback rather than the pop-up, and Meta then
	wants the same `redirect_uri` quoted back at the exchange.
	"""
	parsed = parse_state(state)
	if not parsed:
		frappe.throw(_("This connection attempt is invalid or has expired, please retry"))
	site = parsed["site"]
	if not allowed_site(site):
		frappe.log_error(f"WhatsApp signup from unlisted site {site}", "WhatsApp: signup refused")
		frappe.throw(_("This site is not allowed to connect WhatsApp"))

	token = exchange_code(code, connect_url() if frappe.utils.cint(redirected) else "")
	waba_id, phone_number_id = discover_assets(token, waba_id, phone_number_id)
	number = describe_number(phone_number_id, token)
	coexistence = check_coexistence(phone_number_id, number, token)

	claim_route(waba_id, phone_number_id, number.get("display_phone_number"), site)
	subscribe_waba(waba_id, token)
	deliver_to_site(site, token, waba_id, phone_number_id, number)

	log_session_event(
		state,
		"CONNECTED",
		{
			"waba_id": waba_id,
			"phone_number_id": phone_number_id,
			"current_step": "delivered",
			"coexistence": coexistence,
		},
	)
	return {"ok": True, "site": site, "coexistence": coexistence}


def connect_url() -> str:
	"""The one page Meta may send a login back to, spelled exactly as registered.

	Strict Mode matches the redirect URI character for character, so this is
	also the value that belongs in the app's *Valid OAuth Redirect URIs* — and
	the `fallback_redirect_uri` the page hands to `FB.login`.
	"""
	return get_url().rstrip("/") + CONNECT_PATH


# What Coexistence asks Embedded Signup for. In the JS SDK this rides in
# `extras`; on a hand-built dialog URL there is no documented home for it, so it
# is sent as a query parameter in the same shape Meta's own hosted onboarding
# page uses. If Meta ignores it there, the flow falls back to the plain Cloud
# API onboarding — which is why `check_coexistence` looks at the result instead
# of trusting it.
SIGNUP_EXTRAS = {
	"setup": {},
	"featureType": "whatsapp_business_app_onboarding",
	"sessionInfoVersion": "3",
}


def login_url(state: str) -> str:
	"""The Facebook login dialog, addressed directly.

	`FB.login` needs a click to open its pop-up, and a click can only happen on
	a page we have already put in front of the person — which is the extra
	screen nobody wants. A top-level navigation needs no click and no pop-up
	permission, so the hub page can send the browser straight on to Facebook
	the moment it loads.

	Meta documents the configuration id on a hand-built dialog
	("include your configuration ID as an optional parameter"). It does not
	document `extras` there.
	"""
	params = {
		"client_id": get_whatsapp_app_id(),
		"config_id": config_id(),
		"redirect_uri": connect_url(),
		"response_type": "code",
		"override_default_response_type": "true",
		# see the page: without it Facebook skips every screen it already has an
		# answer for, and the Coexistence branch is one of those screens
		"auth_type": "reauthorize",
		"extras": json.dumps(SIGNUP_EXTRAS),
		# Strict Mode ignores its value when matching the redirect URI, and the
		# manual-flow guide says it comes back unchanged. Belt; sessionStorage
		# in the page is the braces.
		"state": state,
	}
	return f"https://www.facebook.com/v23.0/dialog/oauth?{urlencode(params)}"


def check_coexistence(phone_number_id: str, number: dict, token: str) -> bool:
	"""Did the number keep its WhatsApp Business app, or did we just take it over?

	Coexistence is the whole promise made to the client — "you keep using
	WhatsApp on your phone as always" — and it is decided inside Meta's flow,
	where we cannot see. Meta does expose the answer afterwards: a number that
	can do both reads `is_on_biz_app: true` with `platform_type: CLOUD_API`.

	A plain Cloud API onboarding is not a failure to undo; it is a different
	outcome, and the one thing it must not be is silent.
	"""
	on_app = bool(number.get("is_on_biz_app"))
	if on_app:
		return True
	frappe.log_error(
		f"Number {phone_number_id} finished Embedded Signup without Coexistence: "
		f"is_on_biz_app={number.get('is_on_biz_app')!r} "
		f"platform_type={number.get('platform_type')!r}. The client's WhatsApp Business "
		f"app is NOT connected, and their chat history will not arrive.",
		"WhatsApp: onboarded without Coexistence",
	)
	return False


def exchange_code(code: str, redirect_uri: str = "") -> str:
	"""Trade the 30-second Embedded Signup code for the business token.

	`redirect_uri` is empty for the pop-up flow, where the code was never tied
	to a URL. It is required for the full-page fallback, where it was: Meta
	checks that the exchange quotes back the same address the code was issued
	against, and refuses it otherwise.
	"""
	params = {
		"client_id": get_whatsapp_app_id(),
		"client_secret": get_whatsapp_app_secret(),
		"code": code,
	}
	if redirect_uri:
		params["redirect_uri"] = redirect_uri
	try:
		data = whatsapp_graph_get("oauth/access_token", token="", params=params)
	except MetaAPIError as exc:
		frappe.throw(_("Meta refused the WhatsApp connection: {0}").format(str(exc)))
	if not data.get("access_token"):
		frappe.throw(_("Meta did not return an access token"))
	return data["access_token"]


def discover_assets(token: str, waba_id: str = "", phone_number_id: str = "") -> tuple[str, str]:
	"""Which WhatsApp account was just shared, when the browser could not say.

	Embedded Signup normally posts the WABA and the phone number back to the
	page that opened it. That page is not always still there: when a browser
	suppresses the pop-up the JavaScript SDK falls back to a full-page redirect,
	and what comes back is the code alone — the listener that would have caught
	the ids was destroyed with the page.

	Meta documents the way round, and it is the same one the hosted flow uses:
	the business token itself names, in `granular_scopes`, every WABA that
	granted the app `whatsapp_business_management`, most recently onboarded
	first. From the account, its phone number.

	A connection that is one redirect away from done must not be thrown away for
	want of two ids we can ask for.
	"""
	if waba_id and phone_number_id:
		return waba_id, phone_number_id

	if not waba_id:
		try:
			data = whatsapp_graph_get("debug_token", whatsapp_app_token(), {"input_token": token})
		except MetaAPIError as exc:
			frappe.throw(_("Meta would not say which WhatsApp account was shared: {0}").format(str(exc)))
		for scope in (data.get("data") or {}).get("granular_scopes") or []:
			if scope.get("scope") == "whatsapp_business_management" and scope.get("target_ids"):
				waba_id = str(scope["target_ids"][0])
				break
	if not waba_id:
		frappe.throw(_("Meta did not say which WhatsApp account was shared. Please retry."))

	if not phone_number_id:
		try:
			numbers = whatsapp_graph_get(f"{waba_id}/phone_numbers", token, {"limit": 1})
		except MetaAPIError as exc:
			frappe.throw(_("Could not read this WhatsApp account's phone number: {0}").format(str(exc)))
		rows = numbers.get("data") or []
		if not rows:
			frappe.throw(
				_("This WhatsApp account has no phone number yet. Finish the setup on Meta and retry.")
			)
		phone_number_id = str(rows[0].get("id") or "")
	if not phone_number_id:
		frappe.throw(_("Meta did not say which phone number was shared. Please retry."))

	return waba_id, phone_number_id


def describe_number(phone_number_id: str, token: str) -> dict:
	try:
		return whatsapp_graph_get(
			phone_number_id,
			token,
			{"fields": "display_phone_number,verified_name,quality_rating,platform_type,is_on_biz_app"},
		)
	except MetaAPIError:
		frappe.log_error(frappe.get_traceback(), "WhatsApp: could not read the phone number")
		return {}


def subscribe_waba(waba_id: str, token: str) -> None:
	"""Subscribe the app to this WhatsApp Business account's webhooks.

	Coexistence needs more than `messages`: without `smb_message_echoes` the CRM
	never sees what the business writes from its phone, and without `history` the
	past conversations are never imported.
	"""
	try:
		whatsapp_graph_post(f"{waba_id}/subscribed_apps", token, {})
	except MetaAPIError:
		frappe.log_error(frappe.get_traceback(), f"WhatsApp: could not subscribe WABA {waba_id}")


def claim_route(waba_id: str, phone_number_id: str, display_number: str | None, site: str) -> None:
	"""Record which site owns this account, so the hub can route its messages.

	Like page routes, an account already owned by another site is never silently
	reassigned: the attempt is refused and logged.
	"""
	site = site.rstrip("/")
	current = frappe.db.get_value("Meta WhatsApp Route", waba_id, "site_url")
	if current and current.rstrip("/") != site:
		frappe.log_error(
			f"WABA {waba_id} is routed to {current}; {site} tried to take it over",
			"WhatsApp relay: takeover refused",
		)
		# Name both sides. "Already connected to another site" was true and
		# useless: the commonest cause is not another client at all, it is the
		# same site reached by a second hostname — a custom domain and the one
		# the host gave it — and nobody can see that from a sentence that names
		# neither.
		frappe.throw(
			_(
				"This WhatsApp account is already connected to {0}, and this request came from "
				"{1}. If those are the same CRM under two addresses, remove the Meta WhatsApp "
				"Route for {2} on the hub and connect again."
			).format(current, site, waba_id)
		)
	if current:
		frappe.db.set_value(
			"Meta WhatsApp Route",
			waba_id,
			{"phone_number_id": phone_number_id, "display_phone_number": display_number or ""},
		)
	else:
		frappe.get_doc(
			{
				"doctype": "Meta WhatsApp Route",
				"waba_id": waba_id,
				"phone_number_id": phone_number_id,
				"display_phone_number": display_number or "",
				"site_url": site,
			}
		).insert(ignore_permissions=True)
	frappe.db.commit()  # nosemgrep: frappe-manual-commit — the two calls after this can fail; the claim stands


def deliver_locally(payload: dict) -> None:
	"""The same thing `receive_connection` does, without the round trip.

	When the CRM being connected **is** this site — an agency connecting its own
	number on the hub — the HTTP call goes out to ourselves and comes back in
	while this very request is still open. On one worker that is a deadlock, and
	the person sees the connection fail after Meta has already said yes and they
	have already scanned a QR.

	`claim_route_on_hub` learned this lesson months ago; the delivery never did.
	"""
	from crm.integrations.whatsapp.api import upsert_account, whatsapp_installed

	if not whatsapp_installed():
		frappe.throw(_("The WhatsApp app is not installed on this site"))
	upsert_account(payload)
	frappe.db.commit()  # nosemgrep: frappe-manual-commit — the self-call re-enters this site and must see it


def deliver_to_site(site: str, token: str, waba_id: str, phone_number_id: str, number: dict) -> None:
	"""Hand the credentials to the client CRM, signed with the relay secret."""
	payload = {
		"token": token,
		"waba_id": waba_id,
		"phone_number_id": phone_number_id,
		"display_phone_number": number.get("display_phone_number") or "",
		"verified_name": number.get("verified_name") or "",
	}
	# By hostname, not by string: the site that started the flow can name this
	# hub by its other name (the `.frappe.cloud` one it was created with), and a
	# plain comparison would send the hub off to fetch itself over HTTP.
	if is_this_site(site):
		deliver_locally(payload)
		return

	if not relay_secret():
		frappe.throw(_("meta_relay_secret is not configured on this hub"))
	body = json.dumps(payload).encode()
	try:
		response = requests.post(
			f"{site.rstrip('/')}/api/method/crm.integrations.whatsapp.api.receive_connection",
			data=body,
			headers={"Content-Type": "application/json", "X-CRM-Relay-Signature": relay_sign(body)},
			timeout=TIMEOUT,
		)
		if response.status_code >= 300:
			raise ValueError(f"HTTP {response.status_code}: {response.text[:200]}")
	except Exception as exc:
		frappe.log_error(frappe.get_traceback(), f"WhatsApp: handing the connection to {site} failed")
		frappe.throw(_("Could not hand the connection to your CRM: {0}").format(str(exc)[:200]))


__all__ = [
	"complete_signup",
	"config_id",
	"config_in_use",
	"connect_url",
	"deliver_locally",
	"discover_assets",
	"error_fields",
	"hint_for",
	"login_url",
	"make_state",
	"parse_state",
	"sign",
]
