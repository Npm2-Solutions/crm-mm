# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Facebook Login (authorization-code flow) for the Meta integration.

Flow: Settings modal → `get_login_url` → user authorizes on facebook.com →
Meta redirects the browser to `callback` → code→token→long-lived token →
pages + forms are synced. State is HMAC-signed to prevent CSRF.

**One app, many client sites.** Meta requires every redirect URI to be an exact
match against the app's whitelist and supports no wildcards, so an agency app
serving one Frappe site per client cannot whitelist them all. Meta's documented
answer is to send every login through a small number of whitelisted URIs and
carry the destination in `state` (developers.facebook.com/docs/facebook-login/security).
That is the hub: with `meta_hub_url` in the site config, the login uses the
hub's callback as redirect_uri and the hub relays the authorization code back
to the site named in the signed state, which redeems it with the shared app
secret. Without `meta_hub_url` nothing changes: the site is its own callback
and must be whitelisted individually.
"""

import base64
import hashlib
import hmac
import json
import time
from urllib.parse import quote, urlencode

import frappe
from frappe import _
from frappe.utils import add_to_date, get_url, now_datetime

from crm.integrations.meta.client import (
	MetaAPIError,
	exchange_code_for_token,
	exchange_for_long_lived_token,
	get_app_id,
	get_app_secret,
	graph_get,
	graph_get_paginated,
)

CALLBACK_PATH = "/api/method/crm.integrations.meta.oauth.callback"

# Minimal production scope set for reading leads + subscribing pages:
# - pages_show_list: list the user's pages (/me/accounts)
# - pages_read_engagement + pages_manage_metadata: read page data, subscribe the
#   app to the page's leadgen webhook (/{page}/subscribed_apps)
# - leads_retrieval: read /{form}/leads and /{leadgen_id}
# - pages_manage_ads + ads_management: leads_retrieval dependencies (App Review pair)
# - business_management: pages owned via Business Manager
# - pages_manage_posts: publish to the page feed (Social Planner)
# - instagram_basic + instagram_content_publish: publish to the linked IG
#   Business account (Social Planner)
SCOPES = (
	"pages_show_list",
	"pages_read_engagement",
	"pages_manage_metadata",
	"pages_manage_ads",
	"leads_retrieval",
	"ads_management",
	"business_management",
	"pages_manage_posts",
	"instagram_basic",
	"instagram_content_publish",
)


def scopes() -> tuple[str, ...]:
	"""What to ask Facebook for.

	A permission the app does not carry makes the whole login dialog fail with
	"Invalid Scopes" — one missing use case and nobody can connect at all. So
	`meta_scopes` in the site config can narrow the list while the app is still
	being set up (e.g. leads only, before the Page and Instagram use cases are
	added). Remove the key once the app has everything.
	"""
	configured = frappe.conf.get("meta_scopes")
	if configured:
		return (
			tuple(configured) if isinstance(configured, list | tuple) else tuple(str(configured).split(","))
		)
	return SCOPES


MANAGER_ROLES = {"System Manager", "Sales Manager"}


def _check_manager():
	if not MANAGER_ROLES & set(frappe.get_roles()):
		frappe.throw(_("Only sales managers can manage the Meta integration"), frappe.PermissionError)


def hub_url() -> str:
	"""Base URL of the site whose callback is whitelisted on the Meta app."""
	return (frappe.conf.get("meta_hub_url") or "").rstrip("/")


def is_hub() -> bool:
	"""True when THIS site owns the app's callbacks.

	The hub may perfectly well be a client site too (a one-site setup, or the
	agency's own CRM), so `meta_hub_url` pointing at ourselves still means we
	are the hub — and we keep the webhook controls.
	"""
	return not hub_url() or hub_url() == get_url().rstrip("/")


def _redirect_uri() -> str:
	"""What Meta redirects to — the hub when there is one, else this site."""
	return (hub_url() + CALLBACK_PATH) if hub_url() else get_url(CALLBACK_PATH)


def _sign_state(payload: str) -> str:
	"""Sign with the relay secret when sites share one app, so the hub and the
	destination site can both verify the state; otherwise stay site-local."""
	secret = (
		frappe.conf.get("meta_relay_secret") or frappe.local.conf.get("encryption_key") or frappe.local.site
	)
	return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:24]


def _parse_state(state: str | None) -> dict | None:
	"""Verified state payload, or None when missing/forged/expired."""
	if not state or "." not in state:
		return None
	try:
		encoded, signature = state.rsplit(".", 1)
		payload = base64.urlsafe_b64decode(encoded.encode()).decode()
		if not hmac.compare_digest(signature, _sign_state(payload)):
			return None
		parsed = json.loads(payload)
	except Exception:
		return None
	if int(time.time()) - int(parsed.get("t") or 0) > 600:
		return None
	return parsed


@frappe.whitelist()
def get_login_url(rerequest: bool = False) -> dict:
	"""The facebook.com dialog URL the browser should visit to connect.

	`rerequest` forces Facebook to show the dialog again. Without it, a user who
	has already authorised the app is bounced straight back with no consent
	screen — and therefore no page picker, so there is no way to add a Page that
	was left out the first time.
	"""
	_check_manager()
	if not get_app_id() or not get_app_secret():
		frappe.throw(_("Set the Meta App ID and App Secret first"))

	# `site` tells the hub which site to hand the authorization code back to.
	# Nothing else goes in: the state travels through facebook.com in the query
	# string, so it carries no personal data (the CRM user is already known from
	# the session on the site that completes the flow).
	payload = json.dumps({"t": int(time.time()), "site": get_url().rstrip("/")})
	state = f"{base64.urlsafe_b64encode(payload.encode()).decode()}.{_sign_state(payload)}"
	params = {
		"client_id": get_app_id(),
		"redirect_uri": _redirect_uri(),
		"state": state,
		"response_type": "code",
	}
	# Apps created with the use-case wizard get "Facebook Login for Business",
	# which asks for a saved configuration (config_id) instead of a scope list.
	# Classic Facebook Login still takes scopes: support both.
	config_id = frappe.conf.get("meta_login_config_id")
	if config_id:
		params["config_id"] = config_id
	else:
		params["scope"] = ",".join(scopes())
	if rerequest:
		params["auth_type"] = "rerequest"
	return {"login_url": f"https://www.facebook.com/v23.0/dialog/oauth?{urlencode(params)}"}


@frappe.whitelist(allow_guest=True, methods=["GET"])  # nosemgrep: guest-whitelisted-method
def callback(code: str | None = None, state: str | None = None, **kwargs):
	"""OAuth redirect target.

	Guest-accessible because the hub receives this redirect in the browser of a
	user who is logged into THEIR site, not into the hub. Nothing is trusted
	from the query string: the state must carry a valid HMAC (only sites sharing
	the relay secret can mint one) and, once on the destination site, the
	session still has to belong to a sales manager.
	"""
	parsed = _parse_state(state)
	if parsed and (parsed.get("site") or "").rstrip("/") != get_url().rstrip("/"):
		# we are the hub: hand the code to the site that started the login
		_relay_to_site(parsed["site"], code, state, kwargs)
		return

	_check_manager()
	if not code or not state:
		_redirect_back(error=kwargs.get("error_description") or _("Authorization was cancelled"))
		return
	if not parsed:
		_redirect_back(error=_("Invalid or expired login attempt"))
		return

	try:
		short = exchange_code_for_token(code, _redirect_uri())
		long_lived = exchange_for_long_lived_token(short["access_token"])
		user_token = long_lived["access_token"]
		expires_in = int(long_lived.get("expires_in") or 0)

		me = graph_get("me", user_token, {"fields": "id,name"})

		settings = frappe.get_doc("CRM Meta Settings")
		settings.user_access_token = user_token
		settings.connected_user_id = me.get("id")
		settings.connected_user_name = me.get("name")
		settings.user_token_expires_at = (
			add_to_date(now_datetime(), seconds=expires_in) if expires_in else None
		)
		settings.save(ignore_permissions=True)
		# Commit the token BEFORE touching the pages. Discovering them costs one
		# Graph call per page plus one per form, so an account with access to
		# every Page of a portfolio runs into the gateway timeout — and a request
		# that dies takes the whole transaction with it, losing the token that
		# was already obtained. That is why granting access to a single Page
		# worked and granting access to all of them came back disconnected.
		frappe.db.commit()

		start_page_sync()
		_redirect_back()
	except MetaAPIError as exc:
		frappe.log_error(frappe.get_traceback(), "Meta OAuth callback failed")
		_redirect_back(error=str(exc))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Meta OAuth callback failed")
		_redirect_back(error=_("Connection failed, see error log"))


def _relay_to_site(site: str, code: str | None, state: str, kwargs: dict):
	"""Hub → client site: forward the authorization code, nothing else.

	The code is single-use and worthless without the app secret, which only our
	own sites hold. The destination is taken from the signed state, so this is
	not an open redirect.
	"""
	params = {"state": state}
	if code:
		params["code"] = code
	for key in ("error", "error_description", "error_reason"):
		if kwargs.get(key):
			params[key] = kwargs[key]
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = f"{site.rstrip('/')}{CALLBACK_PATH}?{urlencode(params)}"


def _redirect_back(error: str | None = None):
	"""End of the login: a page that reports back to whoever opened it.

	The connect button opens a popup, so the CRM behind it must not be
	navigated anywhere; `oauth_connected` posts the outcome to the opener and
	closes. Opened as a plain tab it redirects to the settings page itself, so
	a blocked popup still lands somewhere sensible.
	"""
	target = "/oauth_connected?provider=meta"
	if error:
		target += f"&error={quote(error[:300])}"
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = target


PAGE_FIELDS = "id,name,category,access_token,tasks,instagram_business_account{id,username}"


def discover_pages(user_token: str) -> list[dict]:
	"""The Pages this person actually granted, and only those.

	`/me/accounts` is exactly the list ticked in the Facebook dialog — a Page
	administered through a Business portfolio appears here too, once granted.
	Walking the portfolio's `owned_pages` and `client_pages` instead surfaces
	Pages that were NOT granted: they arrive without the permissions to use
	them, so every call on them fails with "permission(s) must be granted
	before impersonating a user's page", and they only crowd the list with
	entries nobody can switch on. Whoever wants one adds it in the dialog.
	"""
	return [
		page
		for page in graph_get_paginated("me/accounts", user_token, {"fields": PAGE_FIELDS})
		if page.get("access_token")
	]


SYNC_FLAG = "meta_page_sync_running"


def sync_running() -> bool:
	return bool(frappe.cache().get_value(SYNC_FLAG))


def start_page_sync() -> None:
	"""Run the page/form sync in the background.

	It is too slow for a web request: every Page costs a call for its lead
	forms, and a request that dies takes the whole transaction with it —
	including the token just obtained.

	The token is deliberately NOT passed as an argument: enqueue arguments are
	serialised into the queue and kept in the job record, so a long-lived user
	access token would sit there in the clear, readable from the background
	jobs screen. The job reads it from the settings instead.
	"""
	frappe.cache().set_value(SYNC_FLAG, 1, expires_in_sec=900)
	frappe.enqueue("crm.integrations.meta.oauth.run_page_sync", queue="long", timeout=900)


def run_page_sync() -> None:
	try:
		settings = frappe.get_doc("CRM Meta Settings")
		token = settings.get_password("user_access_token", raise_exception=False)
		if not token:
			return
		sync_pages_and_forms(token)
		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Meta: page sync failed")
	finally:
		frappe.cache().delete_value(SYNC_FLAG)


def sync_pages_and_forms(user_token: str) -> list[dict]:
	"""Upsert the user's pages (with long-lived page tokens) and their forms."""
	pages = discover_pages(user_token)
	for page in pages:
		upsert_page(page)
		sync_forms_recording_failure(page["id"], page["access_token"])

	forget_ungranted_pages({page["id"] for page in pages})

	# make the pages (and linked IG accounts) usable by the Social Planner
	try:
		from crm.social.accounts import sync_from_facebook_pages

		sync_from_facebook_pages()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Meta: social account sync failed")
	return pages


def forget_ungranted_pages(granted: set[str]) -> None:
	"""Remove Pages the connection no longer covers.

	Un-ticking a Page in the Facebook dialog should make it disappear here too,
	otherwise the list keeps growing with Pages that cannot be used. A Page is
	only dropped when nothing hangs off it: with lead forms, or with the lead
	sync still on, it stays, because removing it would break what it feeds.
	"""
	for name in frappe.get_all("Facebook Page", pluck="name"):
		if name in granted:
			continue
		if frappe.db.exists("Facebook Lead Form", {"page": name}):
			continue
		if frappe.db.get_value("Facebook Page", name, "sync_enabled"):
			continue
		frappe.delete_doc("Facebook Page", name, ignore_permissions=True, force=True)


def upsert_page(page: dict) -> None:
	ig = page.get("instagram_business_account") or {}
	values = {
		"page_name": page.get("name"),
		"category": page.get("category"),
		"access_token": page.get("access_token"),
		"token_valid": 1,
		"instagram_account_id": ig.get("id") or "",
		"instagram_username": ig.get("username") or "",
		# what this connection may actually do on the page. A page reachable
		# through a Business portfolio can be listed without the person having
		# granted it in the login dialog, and then every page call fails with
		# "permission(s) must be granted before impersonating a user's page".
		# Keeping the tasks lets the CRM say which pages are really usable.
		"tasks": ",".join(page.get("tasks") or []),
	}
	if frappe.db.exists("Facebook Page", page["id"]):
		doc = frappe.get_doc("Facebook Page", page["id"])
		doc.update(values)
		doc.save(ignore_permissions=True)
	else:
		frappe.get_doc({"doctype": "Facebook Page", "id": page["id"], **values}).insert(
			ignore_permissions=True
		)


def sync_forms_recording_failure(page_id: str, page_token: str) -> str:
	"""Pull a page's forms, keeping any failure where someone can read it.

	Meta refuses `leadgen_forms` for a page whose token comes from a user
	without the ADVERTISE task on it, and rate-limits with error 80005. Both
	used to go only to the error log, so the page appeared connected with no
	forms and no reason given. The message is stored on the page instead.
	"""
	error = ""
	try:
		sync_forms_for_page(page_id, page_token)
	except MetaAPIError as exc:
		error = str(exc)[:500]
		frappe.log_error(frappe.get_traceback(), f"Meta: form sync failed for page {page_id}")
	frappe.db.set_value("Facebook Page", page_id, "last_form_sync_error", error, update_modified=False)
	return error


def sync_forms_for_page(page_id: str, page_token: str) -> None:
	"""Upsert leadgen forms, refreshing questions while keeping existing mappings."""
	for form in graph_get_paginated(
		f"{page_id}/leadgen_forms", page_token, {"fields": "id,name,status,questions"}
	):
		if frappe.db.exists("Facebook Lead Form", form["id"]):
			doc = frappe.get_doc("Facebook Lead Form", form["id"])
			doc.form_name = form.get("name")
			doc.form_status = form.get("status")
			merge_questions(doc, form.get("questions") or [])
			doc.flags.ignore_validate = True
			doc.save(ignore_permissions=True)
		else:
			doc = frappe.get_doc(
				{
					"doctype": "Facebook Lead Form",
					"id": form["id"],
					"form_name": form.get("name"),
					"form_status": form.get("status"),
					"page": page_id,
					"questions": [
						{**question_row(q), "mapped_to_crm_field": default_mapping(q)}
						for q in form.get("questions") or []
					],
				}
			)
			doc.flags.ignore_validate = True
			doc.insert(ignore_permissions=True)


def question_row(q: dict) -> dict:
	return {"key": q.get("key"), "label": q.get("label"), "type": q.get("type"), "id": q.get("id")}


DEFAULT_QUESTION_MAP = {
	"FULL_NAME": "first_name",
	"FIRST_NAME": "first_name",
	"LAST_NAME": "last_name",
	"EMAIL": "email",
	"PHONE": "mobile_no",
	"COMPANY_NAME": "organization",
	"JOB_TITLE": "job_title",
	"WEBSITE": "website",
}


def default_mapping(q: dict) -> str | None:
	return DEFAULT_QUESTION_MAP.get((q.get("type") or "").upper())


def merge_questions(doc, questions: list[dict]) -> None:
	"""Refresh question metadata without losing manual field mappings."""
	existing = {row.key: row for row in doc.questions}
	doc.questions = []
	for q in questions:
		row = question_row(q)
		previous = existing.get(row["key"])
		row["mapped_to_crm_field"] = (
			previous.mapped_to_crm_field if previous and previous.mapped_to_crm_field else default_mapping(q)
		)
		doc.append("questions", row)
