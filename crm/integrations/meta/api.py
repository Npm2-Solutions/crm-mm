# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Settings-modal API for the Meta Lead Ads integration (manager only)."""

import json

import frappe
from frappe import _
from frappe.utils import get_url

from crm.integrations.meta.ads import ad_of_record, read_creative, stopped_ads
from crm.integrations.meta.client import (
	MetaAPIError,
	get_app_id,
	get_app_secret,
	get_settings,
	graph_get,
	graph_post,
	is_managed_app,
)
from crm.integrations.meta.conversions import coverage, send_pending
from crm.integrations.meta.insights import (
	discover_accounts,
	performance,
	spend_sync_running,
	start_spend_sync,
	sync_account,
)
from crm.integrations.meta.leads import backfill_form, get_page_token
from crm.integrations.meta.oauth import (
	_check_manager,
	granted_scopes,
	hub_url,
	is_hub,
	known_scopes,
	missing_scopes,
	start_page_sync,
	sync_forms_recording_failure,
	sync_running,
)
from crm.utils import count_field

WEBHOOK_PATH = "/api/method/crm.integrations.meta.webhook.handle"


@frappe.whitelist()
def get_status() -> dict:
	_check_manager()
	settings = get_settings()
	return {
		"app_id": get_app_id(),
		"has_app_secret": bool(get_app_secret()),
		# managed: the app belongs to the provider and is shared by every client
		# site, so this site shows no developer credentials and no webhook setup
		"managed": is_managed_app(),
		"hub": hub_url(),
		# this site owns the app's callbacks (single-site setup, or the hub)
		"is_hub": is_hub(),
		"webhook_url": get_url(WEBHOOK_PATH),
		"webhook_verify_token": settings.webhook_verify_token or "",
		"connected": bool(settings.get_password("user_access_token", raise_exception=False)),
		"connected_user_name": settings.connected_user_name or "",
		"user_token_expires_at": str(settings.user_token_expires_at or ""),
		# what Facebook actually shared: the dialog decides which Pages the app
		# can see, and a login that granted none looks exactly like a successful
		# one unless we say so here
		# a background job is still pulling pages in: the screen says so instead
		# of looking like the login shared nothing
		"syncing": sync_running(),
		# the Pages themselves come from `list_pages`, which pages and filters
		# them; here only how many there are, so the screen can tell "none yet"
		# from "still loading"
		"page_count": frappe.db.count("Facebook Page"),
		# has Meta ever called this webhook, and what did we do with the call?
		# Without this, "Facebook is not sending" and "we refused it" look the
		# same from the screen, and the only way to tell them apart was to guess.
		"last_webhook_seen": str(settings.last_webhook_seen or ""),
		"last_webhook_outcome": settings.last_webhook_outcome or "",
		# what the dialog granted, and what it did not: a token can be valid and
		# still unable to touch a Page, and Meta's error for that names six
		# permissions without saying which one is missing
		"granted_scopes": known_scopes(),
		"missing_scopes": missing_scopes(),
	}


@frappe.whitelist(methods=["POST"])
def save_app_settings(app_id: str, app_secret: str | None = None) -> dict:
	_check_manager()
	if is_managed_app():
		frappe.throw(_("The Meta app is managed by your provider and cannot be changed here"))
	settings = frappe.get_doc("CRM Meta Settings")
	settings.app_id = (app_id or "").strip()
	if app_secret:  # write-only: empty keeps the stored secret
		settings.app_secret = app_secret
	settings.save()
	frappe.clear_document_cache("CRM Meta Settings", "CRM Meta Settings")
	frappe.db.commit()  # nosemgrep: frappe-manual-commit — the handshake below re-enters this site

	# best-effort: register the app-level webhook subscription right away so
	# nothing has to be configured by hand on developers.facebook.com
	status = get_status()
	try:
		status["webhook"] = configure_webhook()
	except Exception as exc:
		status["webhook"] = {"configured": False, "error": str(exc)[:300]}
	return status


def _app_token() -> str:
	if not get_app_id() or not get_app_secret():
		frappe.throw(_("Set the Meta App ID and App Secret first"))
	return f"{get_app_id()}|{get_app_secret()}"


@frappe.whitelist(methods=["POST"])
def configure_webhook() -> dict:
	"""Register the Page→leadgen webhook subscription on the Meta app via API
	(same as the Webhooks product page on developers.facebook.com).

	Meta verifies the callback synchronously (GET handshake against this site),
	so the site must be publicly reachable over HTTPS."""
	_check_manager()
	settings = get_settings()
	if not is_hub():
		# one shared app has a single callback: the hub owns it, and it fans
		# notifications out to the client site that owns each page
		frappe.throw(_("The webhook is configured centrally by your provider"))
	if not settings.webhook_verify_token:
		frappe.throw(_("Save the app settings first to generate a verify token"))
	try:
		graph_post(
			f"{get_app_id()}/subscriptions",
			_app_token(),
			{
				"object": "page",
				"callback_url": get_url(WEBHOOK_PATH),
				"fields": "leadgen",
				"verify_token": settings.webhook_verify_token,
				"include_values": "true",
			},
		)
	except MetaAPIError as exc:
		frappe.throw(_("Could not configure the webhook automatically: {0}").format(exc))
	return get_webhook_subscription()


@frappe.whitelist()
def get_webhook_subscription() -> dict:
	"""Current app-level webhook subscription state, straight from Meta."""
	_check_manager()
	if not is_hub():
		return {"configured": True, "managed_by_hub": True, "callback_url": hub_url() + WEBHOOK_PATH}
	try:
		data = graph_get(f"{get_app_id()}/subscriptions", _app_token())
	except MetaAPIError as exc:
		return {"configured": False, "error": str(exc)[:300]}
	for row in data.get("data") or []:
		if row.get("object") != "page":
			continue
		fields = [f.get("name") if isinstance(f, dict) else f for f in row.get("fields") or []]
		return {
			"configured": bool(row.get("active", True)) and "leadgen" in fields,
			"callback_url": row.get("callback_url") or "",
			"fields": fields,
			"matches_site": (row.get("callback_url") or "") == get_url(WEBHOOK_PATH),
		}
	return {"configured": False}


def stop_page(page_id: str) -> None:
	"""Undo everything that makes a page produce leads.

	Best effort on Meta's side: a page whose token Meta already rejects must
	not keep the rest of the disconnection from happening.
	"""
	token = get_page_token(page_id)
	if token:
		try:
			graph_post(f"{page_id}/subscribed_apps", token, {"method": "delete"})
		except MetaAPIError:
			pass  # already unsubscribed, or the token is dead: nothing to undo

	from crm.integrations.meta.relay import release_page

	release_page(page_id)

	page = frappe.get_doc("Facebook Page", page_id)
	page.sync_enabled = 0
	page.webhook_subscribed = 0
	page.token_valid = 0
	page.access_token = ""  # empty means "forget it" for a Password field
	page.save(ignore_permissions=True)


@frappe.whitelist(methods=["POST"])
def disconnect() -> dict:
	"""Really disconnect, not just forget who logged in.

	Clearing the user token alone left every Page importing: page tokens do not
	expire with it, the app stays subscribed to each Page's leadgen webhook, and
	the hourly reconciliation keeps polling Meta. Leads went on arriving for a
	connection the screen showed as gone.
	"""
	_check_manager()
	for page_id in frappe.get_all("Facebook Page", pluck="name"):
		stop_page(page_id)

	settings = frappe.get_doc("CRM Meta Settings")
	settings.user_access_token = ""
	settings.connected_user_id = ""
	settings.connected_user_name = ""
	settings.user_token_expires_at = None
	settings.save()
	frappe.clear_document_cache("CRM Meta Settings", "CRM Meta Settings")
	return get_status()


@frappe.whitelist(methods=["POST"])
def refresh_pages() -> dict:
	"""Re-pull pages and forms with the stored long-lived user token."""
	_check_manager()
	settings = get_settings()
	if not settings.get_password("user_access_token", raise_exception=False):
		frappe.throw(_("Connect Facebook first"))
	# same reason as the OAuth callback: too slow to hold a web request open
	start_page_sync()
	return {"started": True}


# Meta requires the ADVERTISE task on the page for anything leadgen: reading
# `leadgen_forms` and subscribing the page to the `leadgen` webhook both fail
# without it, with an error about permissions "before impersonating a user's
# page". A page listed through a Business portfolio can easily lack it.
LEAD_TASK = "ADVERTISE"


def page_tasks(page_id: str) -> list[str]:
	return [t for t in (frappe.db.get_value("Facebook Page", page_id, "tasks") or "").split(",") if t]


def can_sync_leads(tasks: str | None) -> bool:
	"""Unknown tasks mean a page stored before we recorded them: allow it and
	let Meta be the judge, rather than hiding a page that used to work."""
	if not tasks:
		return True
	return LEAD_TASK in tasks.split(",")


def no_token_message(page_id: str | None) -> str:
	"""Why there is no page token, in the words of whoever has to fix it.

	"Reconnect Facebook" was true and useless: the person reconnects, the dialog
	does not offer that Page, and nothing changes. What they need to know is
	that the Page was not part of the last login — and that a Page belonging to
	somebody else's Business portfolio has to be shared with them first, which
	no amount of reconnecting will do on its own.
	"""
	granted = frappe.db.get_value("Facebook Page", page_id, "granted") if page_id else None
	if granted == 0:
		return _(
			"Facebook did not include this Page in the last connection, so the CRM has no token "
			'for it. Press "Reconnect" and tick this Page in the dialog. If it is not offered '
			"there, it belongs to somebody else's Business portfolio: its owner has to give you "
			"a role on the Page first."
		)
	return _(
		'No token is stored for this Page. Press "Reconnect" and make sure this Page is ticked '
		"in the Facebook dialog."
	)


NOT_GRANTED = (
	"Facebook did not grant this CRM the advertising role on this Page, so it cannot read "
	'its lead forms. Press "Choose pages" on the connection screen and tick this Page — '
	"you must be an administrator of it."
)


@frappe.whitelist()
def list_pages(start: int = 0, limit: int = 20, search: str | None = None) -> dict:
	"""The Pages worth showing on the connection screen, a page at a time.

	Only the ones whose switch can actually do something: Meta wants the
	ADVERTISE task for anything leadgen, so a Page without it offers a switch
	that can only fail. They are counted, not listed — vanishing without a
	word would be its own mystery.

	Pages stored before the CRM recorded tasks have none, and are shown: Meta
	is the judge, and hiding something that used to work would be worse.
	"""
	_check_manager()
	filters = {}
	if search:
		filters["page_name"] = ["like", f"%{search}%"]
	usable = [["tasks", "like", f"%{LEAD_TASK}%"], ["tasks", "is", "not set"]]

	total = len(
		frappe.get_all("Facebook Page", filters=filters, or_filters=usable, pluck="name", limit_page_length=0)
	)
	pages = frappe.get_all(
		"Facebook Page",
		filters=filters,
		or_filters=usable,
		fields=["name", "page_name", "instagram_username", "sync_enabled", "tasks", "granted"],
		order_by="page_name asc",
		limit_start=frappe.utils.cint(start),
		limit_page_length=frappe.utils.cint(limit),
	)
	return {
		"pages": pages,
		"total": total,
		# how many the connection screen is deliberately not showing
		"hidden": frappe.db.count("Facebook Page")
		- len(frappe.get_all("Facebook Page", or_filters=usable, pluck="name", limit_page_length=0)),
	}


@frappe.whitelist(methods=["POST"])
def sync_forms(page_id: str) -> dict:
	"""Ask Meta for this page's lead forms, now, and say how it went.

	The page sync pulls forms too, but a page can be connected while its forms
	fail on their own (the connecting user needs the ADVERTISE task on the page
	for `leadgen_forms`). One page is a single Graph call, so unlike the whole
	sync this can answer inside the request.
	"""
	_check_manager()
	token = get_page_token(page_id)
	if not token:
		frappe.throw(no_token_message(page_id))
	if not can_sync_leads(frappe.db.get_value("Facebook Page", page_id, "tasks")):
		frappe.throw(_(NOT_GRANTED))
	error = sync_forms_recording_failure(page_id, token)
	frappe.db.commit()
	return {
		"error": error,
		"forms": frappe.db.count("Facebook Lead Form", {"page": page_id}),
	}


@frappe.whitelist()
def get_pages() -> list[dict]:
	"""The Pages whose leads reach this CRM — the ones switched on, and only those.

	Which Pages the CRM uses is decided on the connection screen; this screen is
	about their forms. Listing every granted Page here meant the forms of Pages
	nobody had switched on sat in the list too, which is precisely what the
	switch is supposed to prevent.
	"""
	_check_manager()
	pages = frappe.get_all(
		"Facebook Page",
		filters={"sync_enabled": 1},
		fields=[
			"name",
			"page_name",
			"category",
			"sync_enabled",
			"webhook_subscribed",
			"granted",
			"token_valid",
			"last_webhook_at",
			"last_form_sync_error",
			"tasks",
		],
		order_by="page_name asc",
	)
	forms_by_page: dict[str, list] = {}
	for form in frappe.get_all(
		"Facebook Lead Form",
		fields=["name", "form_name", "form_status", "page", "last_lead_at"],
		order_by="form_name asc",
	):
		forms_by_page.setdefault(form.page, []).append(form)
	# `count_field()`, not a SQL string: v16 rejects the string form and the
	# whole call raised, which is what made this screen claim there were no
	# pages at all
	lead_counts = dict(
		frappe.get_all(
			"CRM Lead",
			filters={"facebook_form_id": ["is", "set"]},
			fields=["facebook_form_id", count_field()],
			group_by="facebook_form_id",
			as_list=True,
		)
	)
	unmapped = {}
	for row in frappe.get_all(
		"Facebook Lead Form Question",
		fields=["parent", "mapped_to_crm_field"],
	):
		if not row.mapped_to_crm_field:
			unmapped[row.parent] = unmapped.get(row.parent, 0) + 1

	for page in pages:
		page["can_sync_leads"] = can_sync_leads(page.get("tasks"))
		page["forms"] = forms_by_page.get(page.name, [])
		for form in page["forms"]:
			form["lead_count"] = lead_counts.get(form.name, 0)
			form["unmapped_questions"] = unmapped.get(form.name, 0)
	return pages


@frappe.whitelist(methods=["POST"])
def set_page_sync(page_id: str, enabled: bool) -> dict:
	"""Enable/disable a page: subscribes (or unsubscribes) the app to the page's
	leadgen webhook with the PAGE token."""
	_check_manager()
	enabled = bool(frappe.utils.sbool(enabled))
	page = frappe.get_doc("Facebook Page", page_id)
	token = get_page_token(page_id)
	if not token:
		frappe.throw(no_token_message(page_id))
	if enabled and not can_sync_leads(page.tasks):
		frappe.throw(_(NOT_GRANTED))

	subscribed = page.webhook_subscribed
	try:
		if enabled:
			result = graph_post(f"{page_id}/subscribed_apps", token, {"subscribed_fields": "leadgen"})
			subscribed = 1 if result.get("success") else 0
		else:
			graph_post(f"{page_id}/subscribed_apps", token, {"method": "delete"})
			subscribed = 0
	except MetaAPIError as exc:
		if enabled:
			frappe.throw(_("Could not subscribe the page to the leadgen webhook: {0}").format(exc))
		subscribed = 0

	page.sync_enabled = 1 if enabled else 0
	page.webhook_subscribed = subscribed
	page.save(ignore_permissions=True)

	# tell the hub whether leads for this page belong to this site: a page left
	# claimed after sync is switched off can never be connected anywhere else
	from crm.integrations.meta.relay import claim_page, release_page

	if enabled:
		claim_page(page_id)
	else:
		release_page(page_id)
	return {"sync_enabled": page.sync_enabled, "webhook_subscribed": page.webhook_subscribed}


@frappe.whitelist()
def get_form_mapping(form_id: str) -> dict:
	_check_manager()
	form = frappe.get_doc("Facebook Lead Form", form_id)
	return {
		"name": form.name,
		"form_name": form.form_name,
		"page": form.page,
		"questions": [
			{
				"key": q.key,
				"label": q.label,
				"type": q.type,
				"mapped_to_crm_field": q.mapped_to_crm_field or "",
			}
			for q in form.questions
		],
		"lead_fields": get_lead_fields(),
	}


@frappe.whitelist(methods=["POST"])
def save_form_mapping(form_id: str, mapping: dict | str) -> None:
	"""mapping: {question_key: crm_fieldname}"""
	_check_manager()
	if isinstance(mapping, str):
		mapping = json.loads(mapping)
	valid_fields = {f["fieldname"] for f in get_lead_fields()}
	form = frappe.get_doc("Facebook Lead Form", form_id)
	for question in form.questions:
		target = (mapping.get(question.key) or "").strip()
		if target and target not in valid_fields:
			frappe.throw(_("Invalid CRM field: {0}").format(target))
		question.mapped_to_crm_field = target
	form.save(ignore_permissions=True)


def get_lead_fields() -> list[dict]:
	meta = frappe.get_meta("CRM Lead")
	mappable_types = {
		"Data",
		"Small Text",
		"Text",
		"Long Text",
		"Select",
		"Int",
		"Float",
		"Currency",
		"Date",
		"Datetime",
		"Phone",
		"Link",
	}
	skip = {"facebook_lead_id", "facebook_form_id", "naming_series"}
	return [
		{"fieldname": df.fieldname, "label": df.label or df.fieldname}
		for df in meta.fields
		if df.fieldtype in mappable_types and df.fieldname not in skip and not df.read_only
	]


@frappe.whitelist(methods=["POST"])
def backfill(form_id: str, days: int = 90) -> dict:
	"""Pull historical leads (Meta keeps them 90 days) for one form, now."""
	_check_manager()
	days = min(int(days), 90)
	since = frappe.utils.add_to_date(frappe.utils.now_datetime(), days=-days)
	if frappe.flags.in_test:
		return backfill_form(form_id, since=since)
	frappe.enqueue(
		"crm.integrations.meta.leads.backfill_form",
		queue="long",
		form_id=form_id,
		since=since,
	)
	return {"queued": True}


@frappe.whitelist()
def get_failure_logs(limit: int = 50) -> list[dict]:
	_check_manager()
	return frappe.get_all(
		"Failed Lead Sync Log",
		fields=["name", "type", "lead_data", "traceback", "creation"],
		order_by="creation desc",
		page_length=min(int(limit), 200),
	)


@frappe.whitelist()
def test_connection() -> dict:
	"""Sanity check: token valid + can list pages."""
	_check_manager()
	settings = get_settings()
	token = settings.get_password("user_access_token", raise_exception=False)
	if not token:
		frappe.throw(_("Connect Facebook first"))
	try:
		me = graph_get("me", token, {"fields": "id,name"})
	except MetaAPIError as exc:
		return {"ok": False, "error": str(exc)}

	# re-read the permissions while we are here: they change when somebody
	# reconnects, and a stale list is worse than none
	granted = granted_scopes(token)
	if granted:
		frappe.db.set_single_value("CRM Meta Settings", "granted_scopes", ",".join(granted))
		frappe.clear_document_cache("CRM Meta Settings", "CRM Meta Settings")
	return {
		"ok": True,
		"user": me.get("name"),
		"granted_scopes": granted,
		"missing_scopes": missing_scopes(),
	}


@frappe.whitelist(methods=["POST"])
def create_test_lead(form_id: str) -> dict:
	"""Create a Meta test lead for the form (1 per form; the webhook fires for it).

	Requires the app to be Live; the official Lead Ads Testing tool is the
	alternative: https://developers.facebook.com/tools/lead-ads-testing
	"""
	_check_manager()
	page = frappe.db.get_value("Facebook Lead Form", form_id, "page")
	token = get_page_token(page) if page else None
	if not token:
		frappe.throw(no_token_message(page))
	try:
		result = graph_post(f"{form_id}/test_leads", token, {})
		return {"ok": True, "id": result.get("id")}
	except MetaAPIError as exc:
		frappe.throw(_("Could not create test lead: {0}").format(exc))


# --- ad spend --------------------------------------------------------------


@frappe.whitelist()
def get_ad_accounts() -> dict:
	"""The ad accounts we know of, and whether a read is running right now."""
	_check_manager()
	accounts = frappe.get_all(
		"Facebook Ad Account",
		fields=[
			"name as account_id",
			"account_name",
			"business_name",
			"currency",
			"account_status",
			"sync_enabled",
			"last_synced_on",
			"last_error",
		],
		order_by="sync_enabled desc, account_name asc",
	)
	return {"accounts": accounts, "syncing": spend_sync_running()}


@frappe.whitelist(methods=["POST"])
def refresh_ad_accounts() -> dict:
	"""Ask Facebook which ad accounts this connection can see."""
	_check_manager()
	try:
		found = discover_accounts()
	except MetaAPIError as exc:
		frappe.throw(str(exc))
	return {"found": len(found)}


@frappe.whitelist(methods=["POST"])
def set_account_sync(account_id: str, enabled: bool = True) -> dict:
	"""Turn one account's spend on or off.

	Turning it on reads it straight away: an empty report right after saying yes
	looks broken, and the first read is the one that proves the access works.
	"""
	_check_manager()
	enabled = frappe.parse_json(enabled) if isinstance(enabled, str) else bool(enabled)
	frappe.db.set_value("Facebook Ad Account", account_id, "sync_enabled", 1 if enabled else 0)
	if not enabled:
		return {"enabled": False}
	try:
		rows = sync_account(account_id)
	except MetaAPIError as exc:
		frappe.db.set_value(
			"Facebook Ad Account", account_id, "last_error", str(exc)[:500], update_modified=False
		)
		frappe.throw(_("Facebook refused to give the spend of this account: {0}").format(str(exc)))
	return {"enabled": True, "rows": rows}


@frappe.whitelist(methods=["POST"])
def sync_ad_spend_now(days: int = 7) -> dict:
	"""Read every enabled account again, without waiting for tomorrow.

	`days` is how far back to go. The daily job only re-reads the last week —
	enough to catch Meta's revisions — so a longer window is what fills the
	report's history the first time an account is switched on.
	"""
	_check_manager()
	days = min(max(frappe.utils.cint(days) or 7, 1), 365)
	start_spend_sync(days)
	return {"queued": True, "days": days}


@frappe.whitelist()
def get_ad_performance(days: int = 30) -> dict:
	"""Spend against outcome, one line per ad — plus the ads that stopped.

	An ad that was bringing leads and is now rejected belongs at the top of this
	screen, not in a log: it is the difference between "we spent badly" and "we
	stopped spending at all".
	"""
	_check_manager()
	days = min(max(frappe.utils.cint(days) or 30, 1), 365)
	report = performance(days)
	report["stopped"] = stopped_ads(days)
	return report


@frappe.whitelist()
def get_record_ad(doctype: str, name: str) -> dict:
	"""The actual ad behind a lead or a deal: headline, text, picture, link.

	Read when somebody opens the record, so an ad nobody looks at costs nothing,
	and never fatal: the record's own screen cannot depend on Meta answering.
	"""
	if doctype not in ("CRM Lead", "CRM Deal"):
		return {}
	if not frappe.has_permission(doctype, "read", doc=name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	ad_id = ad_of_record(doctype, name)
	if not ad_id:
		return {}
	return {"ad_id": ad_id, **read_creative(ad_id)}


# --- lead quality feedback (Conversions API) --------------------------------


@frappe.whitelist()
def get_conversions_status() -> dict:
	"""How the feedback loop is doing, in the terms Meta grades it on."""
	_check_manager()
	settings = get_settings()
	return {
		"enabled": bool(settings.conversions_enabled),
		"dataset_id": settings.conversions_dataset_id or "",
		"test_code": settings.conversions_test_code or "",
		"last_error": settings.conversions_last_error or "",
		"connected": bool(settings.connected_user_id),
		**coverage(30),
	}


@frappe.whitelist(methods=["POST"])
def save_conversions_settings(
	dataset_id: str | None = None, enabled: bool = False, test_code: str | None = None
) -> dict:
	"""Turn the feedback loop on, and say where to send it.

	Refusing to enable it without a dataset is the whole validation: events sent
	nowhere would look like a working integration and quietly teach Meta nothing.
	"""
	_check_manager()
	enabled = frappe.parse_json(enabled) if isinstance(enabled, str) else bool(enabled)
	settings = frappe.get_doc("CRM Meta Settings")
	if dataset_id is not None:
		settings.conversions_dataset_id = (dataset_id or "").strip()
	if test_code is not None:
		settings.conversions_test_code = (test_code or "").strip()
	if enabled and not settings.conversions_dataset_id:
		frappe.throw(_("Put the dataset id from Events Manager in first."))
	settings.conversions_enabled = 1 if enabled else 0
	settings.save(ignore_permissions=True)
	return {"enabled": bool(settings.conversions_enabled)}


@frappe.whitelist(methods=["POST"])
def send_conversions_now() -> dict:
	"""Empty the queue without waiting for the hour."""
	_check_manager()
	return send_pending()


@frappe.whitelist(methods=["POST"])
def retry_failed_leads(limit: int = 500) -> dict:
	"""Re-import every submission still sitting in the failure log.

	A failure log is not an archive: each row is a person who asked to be
	contacted and never reached anybody. Retrying them one by one through the
	desk is fine for three and absurd for three hundred, which is exactly the
	number a single bad deploy produces.

	Safe to press twice: a submission already imported comes back as a duplicate
	and its log is marked Synced either way.
	"""
	_check_manager()
	from crm.integrations.meta.leads import get_page_token, store_lead

	rows = frappe.get_all(
		"Failed Lead Sync Log",
		filters={"type": "Failure"},
		fields=["name", "form", "lead_data"],
		order_by="creation asc",
		limit=min(max(frappe.utils.cint(limit) or 500, 1), 2000),
	)
	counts = {"created": 0, "merged": 0, "duplicate": 0, "failed": 0}
	for row in rows:
		try:
			lead = frappe.parse_json(row.lead_data)
		except Exception:
			counts["failed"] += 1
			continue
		form_id = row.form or lead.get("form_id")
		if not form_id:
			counts["failed"] += 1
			continue
		page = frappe.db.get_value("Facebook Lead Form", form_id, "page")
		result = store_lead(lead, form_id, get_page_token(page) if page else None)
		counts[result] = counts.get(result, 0) + 1
		if result != "failed":
			frappe.db.set_value("Failed Lead Sync Log", row.name, "type", "Synced")
		frappe.db.commit()
	return counts


@frappe.whitelist(methods=["POST"])
def verify_webhook_subscriptions() -> dict:
	"""Ask META whether each Page really has this app installed.

	`webhook_subscribed` in the CRM only means "our POST to `subscribed_apps`
	answered success", once, at some point. Meta can drop that on its own — a
	Page can disable the App platform in its own settings, and the docs are
	explicit that notifications stop then — and nothing tells us. So the flag is
	checked against the source instead of trusted: `GET /{page}/subscribed_apps`
	says who is installed right now.
	"""
	_check_manager()
	app_id = get_app_id()
	report = []
	for page in frappe.get_all("Facebook Page", filters={"sync_enabled": 1}, fields=["name", "page_name"]):
		token = get_page_token(page.name)
		if not token:
			report.append({"page": page.page_name, "installed": None, "error": _("No page token")})
			continue
		try:
			apps = graph_get(f"{page.name}/subscribed_apps", token).get("data") or []
		except MetaAPIError as exc:
			report.append({"page": page.page_name, "installed": None, "error": str(exc)})
			continue
		installed = any(str(app.get("id")) == str(app_id) for app in apps)
		# what Meta says now wins over what we remembered
		frappe.db.set_value(
			"Facebook Page", page.name, "webhook_subscribed", 1 if installed else 0, update_modified=False
		)
		report.append(
			{
				"page": page.page_name,
				"installed": installed,
				"fields": next(
					(app.get("subscribed_fields") for app in apps if str(app.get("id")) == str(app_id)),
					[],
				),
			}
		)
	frappe.db.commit()
	return {"pages": report, "app_id": app_id}
