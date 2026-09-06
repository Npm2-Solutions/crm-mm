# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Lead tracking — where a lead came from, and what it did before it became one.

The shape of it, end to end:

    tracker.js on the customer's site
        │  first-party cookies: crm_vid (the browser), crm_sid (the visit)
        ▼
    collect()                        ← this module, guest endpoint
        │
        ├─ CRM Visitor               one browser, anonymous until it names itself
        ├─ CRM Visitor Session       one visit + the campaign that produced it
        └─ CRM Tracking Event        every page read, form sent, link clicked
                │
                │  a form submission / booking / personalised link click
                ▼
    attribute()                      ← binds the visitor to a Lead or Deal,
                                       back-fills its whole history onto that
                                       record, and writes the two attribution
                                       snapshots: first touch and last touch.

Anything that can create a lead goes through `attribute()`: the public CRM forms,
the booking page, tracked links in outbound email, Meta lead ads, and manual
creation in the CRM itself. That is what makes the source field trustworthy —
there is no path in that leaves it blank.
"""

import json

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import add_days, cint, get_url, now

from crm.fcrm.doctype.crm_tracking_settings.crm_tracking_settings import get_tracking_settings
from crm.fcrm.doctype.crm_visitor.crm_visitor import get_or_create as get_or_create_visitor
from crm.fcrm.doctype.crm_visitor_session.crm_visitor_session import start_or_continue
from crm.utils import attribution, count_field

VISITOR_COOKIE = "crm_vid"
SESSION_COOKIE = "crm_sid"

TRACKED_DOCTYPES = ("CRM Lead", "CRM Deal")

#: Wire name → the `event_type` stored on CRM Tracking Event.
EVENT_TYPES = {
	"page_view": "Page View",
	"form_view": "Form View",
	"form_submit": "Form Submitted",
	"link_click": "Link Clicked",
	"booking": "Booking",
	"call": "Call",
	"identify": "Identified",
	"custom": "Custom",
}

#: Client details CRM Visitor keeps (the session keeps the rest).
VISITOR_CLIENT_FIELDS = ("device_type", "browser", "os", "user_agent", "ip_address", "country")

#: A single beacon may not carry more than this many events. The tracker batches
#: at most a handful; a bigger payload is either a bug or someone probing.
MAX_EVENTS_PER_BEACON = 20


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------


@frappe.whitelist(allow_guest=True, methods=["POST", "OPTIONS"])
@rate_limit(limit=600, seconds=60 * 60)
def collect() -> dict:
	"""The beacon the tracking script posts to.

	Reads its payload from the raw request body rather than from arguments: the
	script sends `text/plain` so the browser treats it as a simple request and
	skips the CORS preflight, which would otherwise cost a round trip on every
	page and fail outright on sites we haven't listed yet.
	"""
	if not _request():
		return {"ok": False}

	origin = frappe.get_request_header("Origin")
	settings = get_tracking_settings()

	if not settings.accepts_origin(origin):
		frappe.local.response["http_status_code"] = 403
		return {"ok": False}

	_allow_origin(origin)
	if _request().method == "OPTIONS":
		return {"ok": True}

	payload = _request_payload()
	if not _may_collect(settings, payload):
		return {"ok": False}

	user_agent = frappe.get_request_header("User-Agent") or ""
	if settings.exclude_bots and attribution.is_bot(user_agent):
		return {"ok": False}

	ip = _client_ip(settings)
	if not settings.accepts_ip(ip):
		return {"ok": False}

	events = payload.get("events") or []
	if not isinstance(events, list) or not events:
		return {"ok": False}
	events = events[:MAX_EVENTS_PER_BEACON]

	client = _client_info(payload, user_agent, ip)
	visitor_client = {k: v for k, v in client.items() if k in VISITOR_CLIENT_FIELDS}
	visitor = get_or_create_visitor(_visitor_id(payload), defaults=visitor_client)
	visitor.db_set(dict(last_seen_on=now(), **visitor_client), update_modified=False)

	landing = _landing_event(events)
	session = start_or_continue(
		visitor,
		_session_id(payload),
		landing.get("url"),
		landing.get("referrer"),
		client=client,
		timeout_minutes=settings.session_timeout_minutes,
		own_domains=own_domains(),
	)

	stored = [t for t in (_store_event(visitor, session, event) for event in events) if t]
	_bump_counters(visitor, session, stored)

	frappe.db.commit()
	_set_cookies(visitor.name, session.session_id, settings.visitor_cookie_days)
	return {"ok": True, "vid": visitor.name, "sid": session.session_id}


def _landing_event(events: list) -> dict:
	"""The event that says where this visit landed.

	The first page view, not simply the first event: a link click flushes on its
	own, and taking its target URL as the landing page would credit the visit to
	the page the visitor left for.
	"""
	for event in events:
		if isinstance(event, dict) and event.get("type") == "page_view":
			return event
	return events[0] if isinstance(events[0], dict) else {}


def _request():
	"""The current HTTP request, or None.

	`frappe.request` is a proxy that raises when nothing is bound, and half of
	this module runs from places with no request at all — a scheduled purge, a
	lead created by a background job, a test. Everything goes through here.
	"""
	return getattr(frappe.local, "request", None)


def _request_cookies() -> dict:
	request = _request()
	return request.cookies if request else {}


def _request_payload() -> dict:
	"""The beacon body. `text/plain` means Frappe hasn't parsed it for us."""
	request = _request()
	try:
		raw = request.get_data(as_text=True) if request else ""
		payload = json.loads(raw) if raw else {}
	except (ValueError, TypeError):
		payload = {}
	return payload if isinstance(payload, dict) else {}


def _may_collect(settings, payload: dict) -> bool:
	if not settings.enabled:
		return False
	if settings.require_consent and not payload.get("consent"):
		return False
	if settings.respect_do_not_track and frappe.get_request_header("DNT") == "1":
		return False
	return bool(settings.track_anonymous)


def _allow_origin(origin: str | None) -> None:
	"""Answer the calling site cross-origin. Echoing the origin (rather than `*`)
	keeps the door open for credentialed requests should the tracker ever need them."""
	if not origin:
		return
	frappe.local.response_headers["Access-Control-Allow-Origin"] = origin
	frappe.local.response_headers["Access-Control-Allow-Credentials"] = "true"
	frappe.local.response_headers["Vary"] = "Origin"


def _visitor_id(payload: dict) -> str:
	"""The visitor id the browser sent, or a fresh one.

	Ids are 32 hex characters — 128 bits, so an id cannot be guessed onto someone
	else's history — and are minted here, never accepted in an arbitrary shape.
	"""
	vid = str(payload.get("vid") or _request_cookies().get(VISITOR_COOKIE) or "").strip()
	return vid if _is_id(vid) else frappe.generate_hash(length=32)


def _session_id(payload: dict) -> str:
	sid = str(payload.get("sid") or _request_cookies().get(SESSION_COOKIE) or "").strip()
	return sid if _is_id(sid) else ""


def _is_id(value: str) -> bool:
	return len(value) == 32 and all(c in "0123456789abcdef" for c in value)


def _client_ip(settings) -> str:
	if not settings.store_ip_address:
		return ""
	ip = frappe.local.request_ip or ""
	return attribution.anonymize_ip(ip) if settings.anonymize_ip else ip


def _client_info(payload: dict, user_agent: str, ip: str) -> dict:
	client = payload.get("client") or {}
	return {
		**attribution.parse_user_agent(user_agent),
		"user_agent": user_agent[:500],
		"ip_address": ip,
		# set by Cloudflare and most CDNs; absent on a bare deployment
		"country": (frappe.get_request_header("CF-IPCountry") or "")[:10],
		"language": str(client.get("lang") or "")[:20],
	}


def _store_event(visitor, session, event: dict) -> str | None:
	"""Persist one event and return its stored type, or None if it was dropped.

	The caller totals the return values so the counters reflect what actually
	landed in the table — a payload full of unknown event types must not inflate
	a session's event count.
	"""
	if not isinstance(event, dict):
		return None
	event_type = EVENT_TYPES.get(str(event.get("type") or "").strip())
	if not event_type:
		return None

	url = str(event.get("url") or "")[:500]
	doc = frappe.get_doc(
		{
			"doctype": "CRM Tracking Event",
			"event_type": event_type,
			"visitor": visitor.name,
			"session": session.name,
			"occurred_on": now(),
			"url": url,
			"path": attribution.get_path(url)[:140],
			"label": str(event.get("title") or event.get("label") or event.get("name") or "")[:140],
			"referrer": str(event.get("referrer") or "")[:500],
			"duration": max(0, cint(event.get("duration"))),
			"metadata": _metadata(event),
			"lead": visitor.lead,
			"deal": visitor.deal,
		}
	)
	doc.insert(ignore_permissions=True)
	return event_type


def _bump_counters(visitor, session, stored: list) -> None:
	if not stored:
		return
	page_views = stored.count("Page View")
	session.db_set(
		{
			"event_count": (session.event_count or 0) + len(stored),
			"page_view_count": (session.page_view_count or 0) + page_views,
		},
		update_modified=False,
	)
	if page_views:
		visitor.db_set("page_view_count", (visitor.page_view_count or 0) + page_views, update_modified=False)


def _metadata(event: dict) -> str | None:
	props = event.get("props")
	if not isinstance(props, dict) or not props:
		return None
	try:
		return json.dumps(props, default=str)[:1000]
	except (TypeError, ValueError):
		return None


def _set_cookies(visitor_id: str, session_id: str, days: int) -> None:
	"""Remember the visitor on the CRM's own domain — the public forms, the
	booking page, tracked-link redirects.

	Deliberately `SameSite=Lax` and not a third-party cookie: browsers block those
	now, so continuity on the *customer's* site comes from the tracker's own
	localStorage, which sends the ids back in the beacon body. These cookies are
	what carries the same visitor across pages the CRM itself serves.
	"""
	manager = getattr(frappe.local, "cookie_manager", None)
	request = _request()
	if not manager or not request:
		return
	secure = request.scheme == "https"
	manager.set_cookie(VISITOR_COOKIE, visitor_id, max_age=days * 24 * 60 * 60, samesite="Lax", secure=secure)
	manager.set_cookie(SESSION_COOKIE, session_id, max_age=24 * 60 * 60, samesite="Lax", secure=secure)


def own_domains() -> tuple:
	"""Hosts that are us, so a referrer from one of them isn't a new source."""
	return tuple(d for d in (attribution.get_domain(get_url()),) if d)


# ---------------------------------------------------------------------------
# Attribution
# ---------------------------------------------------------------------------


def attribute(
	doc,
	visitor_id: str | None = None,
	session_id: str | None = None,
	category: str | None = None,
	dimensions: dict | None = None,
) -> None:
	"""Write attribution onto a lead or deal, and adopt the visitor's history.

	`visitor_id`/`session_id` name a tracked browser. When there is none — a lead
	ad, an API import, a record typed into the CRM — `category` and `dimensions`
	describe the origin instead, so every record still gets a source.

	First touch is written once and never overwritten: it is the campaign that
	introduced this person, and a later visit must not be able to claim it. Last
	touch is rewritten on every subsequent touch.

	Called before the insert on every entry point that creates a record, so the
	attribution is part of the row rather than an update after it. At that moment
	the document has no name yet and nothing can point at it — the visitor and the
	session are bound by `bind_visitor()` on `after_insert`.
	"""
	if doc.doctype not in TRACKED_DOCTYPES:
		return

	visitor = _resolve_visitor(visitor_id)
	session = _resolve_session(visitor, session_id)

	values = {}
	if visitor:
		values["visitor"] = visitor.name

	if session:
		first = _first_session(visitor, session)
		if not doc.get("first_touch_category"):
			values.update(first.snapshot("first_touch"))
		values.update(session.snapshot("last_touch"))
	elif category:
		snapshot = _synthetic_snapshot(category, dimensions or {})
		if not doc.get("first_touch_category"):
			values.update({f"first_touch_{k}": v for k, v in snapshot.items()})
		values.update({f"last_touch_{k}": v for k, v in snapshot.items()})

	if not values:
		return

	_apply(doc, values)
	if not doc.is_new():
		bind_visitor(doc)


def bind_visitor(doc, method=None) -> None:
	"""`after_insert` hook: point the visitor and its last session at the record.

	Separate from `attribute()` because that runs before the insert, when the
	document has no name for anything to reference. Reading it back off the
	document — rather than carrying state between the two — means it works the
	same whether the record was just created or attributed later.
	"""
	if doc.doctype not in TRACKED_DOCTYPES or not doc.get("visitor"):
		return

	claim_visitor(doc.visitor, doc)

	session_name = doc.get("last_touch_session")
	if not session_name or not frappe.db.exists("CRM Visitor Session", session_name):
		return
	field = "lead" if doc.doctype == "CRM Lead" else "deal"
	frappe.db.set_value(
		"CRM Visitor Session",
		session_name,
		{"converted": 1, field: doc.name},
		update_modified=False,
	)


def attribute_from_request(doc, category: str | None = None, dimensions: dict | None = None) -> None:
	"""`attribute()` for a record being created by something a visitor just did.

	The ids ride along with the submission — as form fields on a public post, and
	as cookies for anything served from the CRM's own domain.
	"""
	form = frappe.local.form_dict or {}
	cookies = _request_cookies()
	attribute(
		doc,
		visitor_id=form.get("crm_vid") or cookies.get(VISITOR_COOKIE),
		session_id=form.get("crm_sid") or cookies.get(SESSION_COOKIE),
		category=category,
		dimensions=dimensions,
	)


def stamp_manual_source(doc, method=None) -> None:
	"""`before_insert` hook: a record created by a signed-in person, with nothing
	else claiming it, is attributed to the CRM itself rather than left blank."""
	if doc.get("first_touch_category"):
		return
	if frappe.session.user in ("Guest", None) or frappe.flags.get("in_web_form"):
		return
	if frappe.flags.in_import or frappe.flags.in_install:
		return
	snapshot = _synthetic_snapshot("CRM UI", {})
	_apply(
		doc,
		{f"{prefix}_{k}": v for prefix in ("first_touch", "last_touch") for k, v in snapshot.items()},
	)


def _apply(doc, values: dict) -> None:
	"""Write `values`, whichever side of the insert we are on: into the document
	when it is still being built, straight to the row once it exists."""
	if doc.is_new():
		doc.update(values)
	else:
		doc.db_set(values, update_modified=False)


def _resolve_visitor(visitor_id: str | None):
	visitor_id = (visitor_id or "").strip()
	if not visitor_id or not frappe.db.exists("CRM Visitor", visitor_id):
		return None
	return frappe.get_doc("CRM Visitor", visitor_id)


def _resolve_session(visitor, session_id: str | None):
	session_id = (session_id or "").strip()
	if session_id:
		name = frappe.db.get_value("CRM Visitor Session", {"session_id": session_id}, "name")
		if name:
			return frappe.get_doc("CRM Visitor Session", name)
	if visitor and visitor.last_session:
		return frappe.get_doc("CRM Visitor Session", visitor.last_session)
	return None


def _first_session(visitor, fallback):
	if visitor and visitor.first_session:
		return frappe.get_doc("CRM Visitor Session", visitor.first_session)
	return fallback


def _synthetic_snapshot(category: str, dimensions: dict) -> dict:
	"""An attribution snapshot for an origin with no browsing session behind it —
	a lead ad, an inbound API call, a record typed into the CRM."""
	source = dimensions.get("source") or ""
	medium = dimensions.get("medium") or attribution.IMPLIED_MEDIUM.get(category, "(none)")
	return {
		"category": category,
		"source": source or category.lower().replace(" ", "_"),
		"medium": medium,
		"campaign": dimensions.get("campaign") or "",
		"term": dimensions.get("term") or "",
		"content": dimensions.get("content") or "",
		"landing_page": dimensions.get("landing_page") or "",
		"referrer": dimensions.get("referrer") or "",
		"on": now(),
		"session": None,
	}


def copy_attribution(source_doc, target_doc) -> None:
	"""Carry attribution across a lead → deal conversion.

	Without this a converted deal reports as created in the CRM UI, and every
	campaign silently loses credit at exactly the point it starts to be worth
	money.
	"""
	fields = ["visitor"]
	for prefix in ("first_touch", "last_touch"):
		fields += [
			f"{prefix}_{suffix}"
			for suffix in (
				"category",
				"source",
				"medium",
				"campaign",
				"term",
				"content",
				"landing_page",
				"referrer",
				"on",
				"session",
			)
		]
	for field in fields:
		if source_doc.get(field) and not target_doc.get(field):
			target_doc.set(field, source_doc.get(field))


def visitor_for(doc) -> str:
	"""The visitor id representing this lead or deal, minted if it has none.

	Used when the CRM reaches a person outside the browser — an email, an SMS —
	and needs an id to hand to the tracker on the far side, so the click and
	everything after it lands on the record instead of starting a new anonymous
	trail.
	"""
	if doc.get("visitor"):
		return doc.visitor

	field = "lead" if doc.doctype == "CRM Lead" else "deal"
	existing = frappe.db.get_value("CRM Visitor", {field: doc.name}, "name")
	if not existing:
		visitor = get_or_create_visitor(frappe.generate_hash(length=32))
		visitor.identify(doc.doctype, doc.name)
		existing = visitor.name

	doc.db_set("visitor", existing, update_modified=False)
	return existing


def claim_visitor(visitor_id: str, doc) -> None:
	"""Attach an existing visitor to a further record — the deal a lead became.

	The lead keeps its binding; the visitor gains the deal, and its sessions and
	events are stamped with it, so the journey reads the same from either side.
	"""
	if not visitor_id or not frappe.db.exists("CRM Visitor", visitor_id):
		return
	frappe.get_doc("CRM Visitor", visitor_id).identify(doc.doctype, doc.name)


def record_conversion(doc, event_type: str, label: str = "", reference=None) -> None:
	"""Log a conversion onto the visitor's timeline, so the journey shows what the
	person actually did and not only the pages they read."""
	if not doc.get("visitor"):
		return
	session = frappe.db.get_value("CRM Visitor", doc.visitor, "last_session")
	frappe.get_doc(
		{
			"doctype": "CRM Tracking Event",
			"event_type": EVENT_TYPES.get(event_type, "Custom"),
			"visitor": doc.visitor,
			"session": session,
			"occurred_on": now(),
			"label": label[:140],
			"lead": doc.name if doc.doctype == "CRM Lead" else None,
			"deal": doc.name if doc.doctype == "CRM Deal" else None,
			"reference_doctype": reference.doctype if reference else None,
			"reference_name": reference.name if reference else None,
		}
	).insert(ignore_permissions=True)


# ---------------------------------------------------------------------------
# Reading it back
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_journey(doctype: str, name: str, limit: int = 200) -> dict:
	"""Everything known about how this record came to exist: the two attribution
	snapshots, the sessions behind them, and the page-by-page timeline."""
	if doctype not in TRACKED_DOCTYPES:
		frappe.throw(_("Tracking is only available for leads and deals"))
	if not frappe.has_permission(doctype, "read", doc=name):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	field = "lead" if doctype == "CRM Lead" else "deal"
	doc = frappe.db.get_value(
		doctype,
		name,
		["visitor", *_snapshot_fieldnames()],
		as_dict=True,
	)
	if not doc:
		return {"visitor": None, "sessions": [], "events": [], "first_touch": {}, "last_touch": {}}

	sessions = frappe.get_all(
		"CRM Visitor Session",
		filters={field: name},
		fields=[
			"name",
			"session_id",
			"started_on",
			"last_activity_on",
			"duration",
			"source_category",
			"source",
			"medium",
			"campaign",
			"landing_page",
			"referrer",
			"referrer_domain",
			"device_type",
			"browser",
			"os",
			"country",
			"page_view_count",
			"event_count",
			"converted",
		],
		order_by="started_on desc",
		limit=50,
	)
	events = frappe.get_all(
		"CRM Tracking Event",
		filters={field: name},
		fields=[
			"name",
			"event_type",
			"occurred_on",
			"label",
			"url",
			"path",
			"referrer",
			"duration",
			"session",
			"metadata",
		],
		order_by="occurred_on desc",
		limit=cint(limit) or 200,
	)
	return {
		"visitor": doc.get("visitor"),
		"first_touch": {k[len("first_touch_") :]: v for k, v in doc.items() if k.startswith("first_touch_")},
		"last_touch": {k[len("last_touch_") :]: v for k, v in doc.items() if k.startswith("last_touch_")},
		"sessions": sessions,
		"events": events,
	}


def _snapshot_fieldnames() -> list[str]:
	suffixes = (
		"category",
		"source",
		"medium",
		"campaign",
		"term",
		"content",
		"landing_page",
		"referrer",
		"on",
		"session",
	)
	return [f"{prefix}_{s}" for prefix in ("first_touch", "last_touch") for s in suffixes]


@frappe.whitelist()
def source_report(
	doctype: str = "CRM Lead",
	touch: str = "first_touch",
	group_by: str = "category",
	from_date: str | None = None,
	to_date: str | None = None,
) -> list[dict]:
	"""Records grouped by where they came from — the report that makes the whole
	mechanism worth having."""
	if doctype not in TRACKED_DOCTYPES:
		frappe.throw(_("Tracking is only available for leads and deals"))
	if touch not in ("first_touch", "last_touch"):
		frappe.throw(_("Attribution must be first_touch or last_touch"))
	if group_by not in ("category", "source", "medium", "campaign"):
		frappe.throw(_("Cannot group by {0}").format(group_by))

	field = f"{touch}_{group_by}"
	filters = {}
	if from_date and to_date:
		filters["creation"] = ["between", [from_date, to_date]]
	elif from_date:
		filters["creation"] = [">=", from_date]
	elif to_date:
		filters["creation"] = ["<=", to_date]

	rows = frappe.get_list(
		doctype,
		filters=filters,
		# count_field(): v16 rejects a SQL function written as a string, and a call
		# that gets it wrong raises rather than degrading
		fields=[f"{field} as label", count_field("total")],
		group_by=field,
		order_by="total desc",
		limit=100,
	)
	return [{"label": r["label"] or _("Unknown"), "total": cint(r["total"])} for r in rows]


# ---------------------------------------------------------------------------
# Settings surface
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_snippet() -> dict:
	"""The script tag to paste into a website, plus the current settings."""
	_check_manager()
	settings = get_tracking_settings()
	base = get_url()
	snippet = f'<script async src="{base}/assets/crm/js/tracker.js" data-crm="{base}"></script>'
	return {
		"snippet": snippet,
		"script_url": f"{base}/assets/crm/js/tracker.js",
		"endpoint": f"{base}/api/method/crm.api.tracking.collect",
		"enabled": bool(settings.enabled),
		"stats": _stats(),
	}


def _stats() -> dict:
	return {
		"visitors": frappe.db.count("CRM Visitor"),
		"identified": frappe.db.count("CRM Visitor", {"status": "Identified"}),
		"sessions": frappe.db.count("CRM Visitor Session"),
		"events": frappe.db.count("CRM Tracking Event"),
	}


def _check_manager() -> None:
	if not set(frappe.get_roles()) & {"System Manager", "Sales Manager"}:
		frappe.throw(_("Not permitted"), frappe.PermissionError)


# ---------------------------------------------------------------------------
# Housekeeping
# ---------------------------------------------------------------------------


def purge_old_data() -> None:
	"""Nightly: drop anonymous browsing history past the retention window.

	Anything attached to a lead or a deal stays — that history is CRM data now,
	and the retention setting is about not hoarding traffic from people who never
	became anything.
	"""
	settings = get_tracking_settings()
	days = cint(settings.retention_days)
	if days <= 0:
		return

	cutoff = add_days(now(), -days)
	unclaimed = {"lead": ["is", "not set"], "deal": ["is", "not set"]}
	# events first, then the sessions they hang off, then the visitor: deleting a
	# parent while children still point at it would leave dangling links.
	for doctype, filters in (
		("CRM Tracking Event", {"occurred_on": ["<", cutoff], **unclaimed}),
		("CRM Visitor Session", {"started_on": ["<", cutoff], **unclaimed}),
		("CRM Visitor", {"last_seen_on": ["<", cutoff], "status": "Anonymous"}),
	):
		for name in frappe.get_all(doctype, filters=filters, pluck="name", limit=5000):
			frappe.delete_doc(doctype, name, ignore_permissions=True, force=True, delete_permanently=True)
		frappe.db.commit()
