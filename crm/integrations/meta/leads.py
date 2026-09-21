# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Lead ingestion shared by the real-time webhook and the polling backfill.

Deduplication is by Meta's lead id (`facebook_lead_id`) — the id is globally
unique, which makes webhook + backfill safely idempotent. Facebook keeps lead
data for 90 days only, so the backfill can never recover older leads.
"""

import datetime
import re

import frappe
from frappe import _

from crm.integrations.meta.client import MetaAPIError, graph_get, graph_get_paginated

# documented lead-node fields, in decreasing order of appetite.
#
# The ad-level names live on the lead itself: Meta fills `ad_name`, `adset_name`
# and `campaign_name` in the same answer as `ad_id`, for a token belonging to
# somebody who can advertise on the ad account — the same privilege `ad_id`
# already needs. So the name of the ad costs no second call and no ads token,
# and when the privilege is missing Meta simply leaves the fields out (the same
# way it leaves out `ad_id`) instead of failing.
#
# `platform` (fb/ig) is not guaranteed on every Graph version, and neither are
# the ad-level names on an old one, so each attempt drops what a version may not
# know. A refused field must never cost the lead.
LEAD_FIELDS = "id,created_time,ad_id,form_id,is_organic,field_data"
AD_LEVEL_FIELDS = "ad_name,adset_id,adset_name,campaign_id,campaign_name"
LEAD_FIELDS_WITH_ADS = LEAD_FIELDS + "," + AD_LEVEL_FIELDS
LEAD_FIELDS_WITH_PLATFORM = LEAD_FIELDS_WITH_ADS + ",platform"

# 100 is "unknown field on this version", 200 "you may not read this one"
RETRYABLE_FIELD_ERRORS = (100, 200)


def fetch_lead(leadgen_id: str, token: str) -> dict:
	attempts = (LEAD_FIELDS_WITH_PLATFORM, LEAD_FIELDS_WITH_ADS, LEAD_FIELDS)
	for fields in attempts:
		try:
			return graph_get(leadgen_id, token, {"fields": fields})
		except MetaAPIError as exc:
			if fields == attempts[-1] or exc.code not in RETRYABLE_FIELD_ERRORS:
				raise
	return {}


def get_page_token(page_id: str) -> str | None:
	if not frappe.db.exists("Facebook Page", page_id):
		return None
	return frappe.get_doc("Facebook Page", page_id).get_password("access_token", raise_exception=False)


def ingest_leadgen_entry(
	leadgen_id: str, page_id: str | None = None, form_id: str | None = None, created_time=None
) -> None:
	"""Webhook path: fetch one lead by id and store it."""
	if not leadgen_id:
		return
	# a notification can arrive without the page id: resolve it from the form,
	# otherwise a page whose sync was switched off would still be imported
	if not page_id and form_id:
		page_id = frappe.db.get_value("Facebook Lead Form", form_id, "page")
	# Stamp the page BEFORE deciding what to do with the notification. The stamp
	# used to come after the checks below, so a page with sync off — or without a
	# token — looked exactly like a page Meta never calls about, which is the
	# difference between "Facebook is not sending" and "we are not listening".
	if page_id and frappe.db.exists("Facebook Page", page_id):
		frappe.db.set_value(
			"Facebook Page", page_id, "last_webhook_at", frappe.utils.now(), update_modified=False
		)

	if not page_id or not frappe.db.get_value("Facebook Page", page_id, "sync_enabled"):
		return

	token = get_page_token(page_id)
	if not token:
		_log_failure({"leadgen_id": leadgen_id}, form_id, _("No page token available"))
		return

	try:
		lead = fetch_lead(leadgen_id, token)
	except MetaAPIError as exc:
		_log_failure({"leadgen_id": leadgen_id}, form_id, str(exc))
		return
	store_lead(lead, lead.get("form_id") or form_id, token)


def backfill_form(form_id: str, since=None, page_token: str | None = None) -> dict:
	"""Polling path: fetch all (remaining) leads of a form, paginated."""
	token = page_token
	if not token:
		page = frappe.db.get_value("Facebook Lead Form", form_id, "page")
		token = get_page_token(page) if page else None
	if not token:
		frappe.throw(_("No page token available for this form. Reconnect Facebook."))

	params = {}
	if since:
		params["filtering"] = frappe.as_json(
			[
				{
					"field": "time_created",
					"operator": "GREATER_THAN",
					"value": int(frappe.utils.data.get_timestamp(since)),
				}
			]
		)

	def run(fields: str) -> dict:
		counts = {"created": 0, "merged": 0, "duplicates": 0, "failed": 0}
		for lead in graph_get_paginated(
			f"{form_id}/leads", token, {**params, "fields": fields}, max_pages=200
		):
			result = store_lead(lead, form_id, token)
			# "merged" is a submission filed on somebody the CRM already knew
			key = "duplicates" if result == "duplicate" else result
			counts[key] = counts.get(key, 0) + 1
		return counts

	try:
		return run(LEAD_FIELDS_WITH_ADS)
	except MetaAPIError as exc:
		if exc.code not in RETRYABLE_FIELD_ERRORS:
			raise
		# This version will not give the ad names in bulk: the leads matter more.
		# Starting over is safe — the import ledger knows what it already filed,
		# so the leads of the first pass come back as duplicates, not as twins.
		return run(LEAD_FIELDS)


def already_stored(leadgen_id: str) -> bool:
	"""Have we seen this submission before?

	The ledger answers first, and it is the only answer that survives somebody
	deleting the person: a lead removed from the CRM used to come back within
	the hour, because the reconciliation re-reads two days of every form and
	nothing remembered that this submission had already been dealt with.

	The two older places are still consulted for the submissions taken in before
	the ledger existed.
	"""
	return bool(
		frappe.db.exists("Facebook Lead Import", leadgen_id)
		or frappe.db.exists("CRM Lead", {"facebook_lead_id": leadgen_id})
		or frappe.db.exists("CRM Lead Facebook Submission", {"leadgen_id": leadgen_id})
	)


def record_import(lead: dict, form_id: str | None, person: str, outcome: str) -> None:
	"""Write the submission into the ledger. Never fatal: the person is already
	saved, and losing the row must not roll that back."""
	try:
		frappe.get_doc(
			{
				"doctype": "Facebook Lead Import",
				"leadgen_id": lead.get("id"),
				"form": form_id or "",
				"form_name": frappe.db.get_value("Facebook Lead Form", form_id, "form_name") or "",
				"platform": "Instagram" if lead.get("platform") == "ig" else "Facebook",
				"lead": person,
				"outcome": outcome,
				"imported_on": frappe.utils.now(),
			}
		).insert(ignore_permissions=True)
	except frappe.DuplicateEntryError:
		pass
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Meta: could not record the import")


def forget_person(doc, method=None) -> None:
	"""A person was deleted: stamp their submissions instead of dropping them.

	The row stays, so the submission is not imported all over again — deleting a
	lead has to mean deleting it, not asking for it back.
	"""
	for name in frappe.get_all("Facebook Lead Import", filters={"lead": doc.name}, pluck="name"):
		frappe.db.set_value(
			"Facebook Lead Import", name, "deleted_on", frappe.utils.now(), update_modified=False
		)


def submitted_at(created_time) -> str:
	"""Meta's own timestamp, in a shape the database accepts.

	The Graph API answers ISO 8601 with an offset — "2026-09-21T11:02:23+0000" —
	and MariaDB refuses it outright: *Incorrect datetime value*. Storing it raw
	did not merely lose the timestamp, it threw in the middle of saving the lead,
	which is how a whole day of submissions ended up in the failure log.

	The instant is kept, not the wall clock: converted to the site's timezone, so
	"submitted at 13:02" means what the person reading the record thinks it
	means. An unparseable value falls back to now — a slightly wrong timestamp is
	worth incomparably less than the lead it would otherwise cost.
	"""
	if not created_time:
		return frappe.utils.now()
	try:
		moment = frappe.utils.get_datetime(created_time)
	except Exception:
		return frappe.utils.now()
	if moment is None:
		return frappe.utils.now()
	if moment.tzinfo:
		utc_naive = moment.astimezone(datetime.timezone.utc).replace(tzinfo=None)
		try:
			moment = frappe.utils.convert_utc_to_system_timezone(utc_naive).replace(tzinfo=None)
		except Exception:
			moment = utc_naive
	return frappe.utils.get_datetime_str(moment)


def submission_row(lead: dict, form_id: str | None) -> dict:
	return {
		"leadgen_id": lead.get("id"),
		"form": form_id or "",
		"form_name": frappe.db.get_value("Facebook Lead Form", form_id, "form_name") or "",
		"submitted_on": submitted_at(lead.get("created_time")),
		"platform": "Instagram" if lead.get("platform") == "ig" else "Facebook",
	}


def store_lead(lead: dict, form_id: str | None, token: str | None = None) -> str:
	"""Map field_data → CRM Lead via the form's question mapping. Idempotent.

	The token travels with the lead because attribution asks Meta what the ad is
	called, and the only token allowed to ask is the one the lead came with.
	"""
	lead_id = lead.get("id")
	if not lead_id:
		return "failed"
	if already_stored(lead_id):
		return "duplicate"

	mapping = get_question_mapping(form_id)
	labels = get_question_labels(form_id)
	values: dict = {}
	unmapped: list[tuple[str, str]] = []
	for item in lead.get("field_data") or []:
		key = item.get("name")
		raw_values = item.get("values") or []
		if not raw_values:
			continue
		crm_field = mapping.get(key)
		if crm_field and not normalize_value(crm_field, raw_values[0]):
			# mapped, but unusable for that field (a phone that is not a phone):
			# the answer still belongs to the person who gave it
			unmapped.append((labels.get(key) or key, ", ".join(clean_answer(v) for v in raw_values)))
			continue
		if not crm_field:
			# an answer nobody mapped is still the customer talking: keep it
			unmapped.append((labels.get(key) or key, ", ".join(clean_answer(v) for v in raw_values)))
			continue
		values[crm_field] = normalize_value(crm_field, raw_values[0])

	if "first_name" not in values:
		# FULL_NAME questions arrive under one key: split into first/last
		full = values.pop("full_name", None) or next(
			(
				(item.get("values") or [""])[0]
				for item in lead.get("field_data") or []
				if item.get("name") in ("full_name", "FULL_NAME")
			),
			None,
		)
		if full:
			parts = str(full).split(maxsplit=1)
			values["first_name"] = parts[0]
			values.setdefault("last_name", parts[1] if len(parts) > 1 else "")

	if not values.get("first_name"):
		_log_failure(lead, form_id, _("No first name could be mapped"))
		return "failed"

	# the same human being can answer two ads, or the same ad twice: that is a
	# second submission, not a second person
	from crm.api.lead import find_person

	# only the mobile number, never the landline: a switchboard is shared by a
	# whole company, and merging two colleagues into one person loses one of them
	person = find_person(email=values.get("email"), phone=values.get("mobile_no"))
	if person:
		return _merge_submission(person, lead, form_id, values, unmapped, token)

	values.update(
		{
			"doctype": "CRM Lead",
			"source": _ensure_source("Instagram" if lead.get("platform") == "ig" else "Facebook"),
			"facebook_lead_id": lead_id,
			"facebook_form_id": form_id,
			"facebook_ad_id": lead.get("ad_id") or "",
			"facebook_submissions": [submission_row(lead, form_id)],
		}
	)
	# All of it, or none of it. Without the savepoint a failure halfway through
	# left the person in the CRM while the submission row and the ledger entry
	# were lost — a lead that looks imported, is not recorded as imported, and
	# comes back at the next reconciliation.
	frappe.db.savepoint("meta_lead")
	try:
		doc = frappe.get_doc(values)
		_attribute(doc, lead, form_id, token)
		doc.insert(ignore_permissions=True)
		record_import(lead, form_id, doc.name, "Created")
		if unmapped:
			_note_unmapped_answers(doc, unmapped)
		_note_form_submitted(doc, form_id)
		return "created"
	except frappe.UniqueValidationError:
		frappe.db.rollback(save_point="meta_lead")
		return "duplicate"
	except Exception:
		frappe.db.rollback(save_point="meta_lead")
		_log_failure(lead, form_id, frappe.get_traceback())
		return "failed"


def _merge_submission(
	person: str,
	lead: dict,
	form_id: str | None,
	values: dict,
	unmapped: list,
	token: str | None = None,
) -> str:
	"""File a submission on the person who made it, instead of cloning them.

	What they typed this time fills only what is still empty: a number somebody
	corrected by hand in the CRM outranks the one re-typed into an ad form. The
	first touch is theirs already; this becomes the last one.
	"""
	frappe.db.savepoint("meta_merge")
	try:
		doc = frappe.get_doc("CRM Lead", person)
		for field, value in values.items():
			if value and not doc.get(field):
				doc.set(field, value)
		if not doc.facebook_lead_id:
			doc.facebook_lead_id = lead.get("id")
			doc.facebook_form_id = form_id
		# the ad that first brought them keeps the credit, like the first touch:
		# otherwise a second submission would move the cost of an old lead onto a
		# new ad, and every report built on it would be wrong in both directions
		if not doc.facebook_ad_id:
			doc.facebook_ad_id = lead.get("ad_id") or ""
		doc.append("facebook_submissions", submission_row(lead, form_id))
		_attribute(doc, lead, form_id, token)
		doc.save(ignore_permissions=True)
		record_import(lead, form_id, doc.name, "Merged")
		if unmapped:
			_note_unmapped_answers(doc, unmapped)
		_note_form_submitted(doc, form_id)
		return "merged"
	except Exception:
		# the person existed before this submission and must survive it failing
		frappe.db.rollback(save_point="meta_merge")
		_log_failure(lead, form_id, frappe.get_traceback())
		return "failed"


def _note_form_submitted(doc, form_id: str | None) -> None:
	"""Say that a form was filled in, whoever filled it.

	`Lead Created` cannot carry this any more: a customer who comes back has
	existed for months. GHL splits the two the same way — a contact is created
	once, a form is submitted every time.
	"""
	if form_id:
		frappe.db.set_value(
			"Facebook Lead Form", form_id, "last_lead_at", frappe.utils.now(), update_modified=False
		)
	try:
		from crm.automation.engine import process_event

		process_event(
			"form_submitted",
			doc,
			{"facebook_form_id": form_id, "source": doc.get("source")},
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Meta: form_submitted automations failed")


# An ad's name can be edited, so a cached one is not true forever; a week is
# long enough to save the calls and short enough that a renamed campaign catches
# up on the next lead.
AD_CACHE_DAYS = 7


def ads_token(page_token: str | None = None) -> str | None:
	"""The token allowed to read an ad object.

	The lead arrives on a page token, but an ad belongs to the ad account, not to
	the page: Meta answers a read of the ad node only for a token that carries
	`ads_management` (or `ads_read`), and that is the user token the login dialog
	asks for — a page token is scoped to page data and gets refused. Asking with
	the wrong one spends a call to be told no, and refusals count towards the
	app's error rate.

	The page token stays as the fallback, for a site connected before the user
	token was stored or one whose token has expired: it may still be refused,
	which `describe_ad` survives by design.
	"""
	token = frappe.get_doc("CRM Meta Settings").get_password("user_access_token", raise_exception=False)
	return token or page_token or None


def describe_ad(ad_id: str, page_token: str | None = None) -> dict:
	"""What Meta calls this ad, its ad set and its campaign.

	A lead arrives with an `ad_id` and nothing else, so the CRM could only say
	"ad 120210…" — true and useless. This asks once per ad and remembers the
	answer: many leads come from the same ad, and the answer does not change
	between them.

	Never fatal. Even the right token can be refused — the ad belongs to the
	client's ad account, and whoever connected Facebook may not be able to
	advertise on it — and a lead is worth more than the name of the ad that
	produced it. A refusal is remembered so the CRM stops asking, but only for
	the cache window: access granted later must be able to take effect, and a
	name we already knew is not forgotten because of one refusal.
	"""
	if not ad_id:
		return {}

	cached = frappe.db.get_value(
		"Facebook Ad",
		ad_id,
		["ad_name", "adset_name", "campaign_id", "campaign_name", "fetched_on", "unreadable"],
		as_dict=True,
	)
	known = _names(cached)
	if (
		cached
		and cached.fetched_on
		and frappe.utils.date_diff(frappe.utils.now(), cached.fetched_on) < AD_CACHE_DAYS
	):
		return known

	token = ads_token(page_token)
	if not token:
		return known

	try:
		data = graph_get(ad_id, token, {"fields": "name,adset{name},campaign{id,name}"})
	except MetaAPIError as exc:
		_remember_ad(ad_id, {"unreadable": 1})
		frappe.logger("meta").info(f"Could not describe ad {ad_id}: {exc}")
		return known

	values = {
		"ad_name": data.get("name") or "",
		"adset_name": (data.get("adset") or {}).get("name") or "",
		"campaign_id": (data.get("campaign") or {}).get("id") or "",
		"campaign_name": (data.get("campaign") or {}).get("name") or "",
		"unreadable": 0,
	}
	_remember_ad(ad_id, values)
	return values


def _names(cached: dict | None) -> dict:
	"""The part of a remembered ad that attribution reads."""
	if not cached or (cached.get("unreadable") and not cached.get("ad_name")):
		return {}
	return {key: cached.get(key) or "" for key in ("ad_name", "adset_name", "campaign_id", "campaign_name")}


def _remember_ad(ad_id: str, values: dict) -> None:
	values = {**values, "fetched_on": frappe.utils.now()}
	try:
		if frappe.db.exists("Facebook Ad", ad_id):
			frappe.db.set_value("Facebook Ad", ad_id, values, update_modified=False)
		else:
			frappe.get_doc({"doctype": "Facebook Ad", "ad_id": ad_id, **values}).insert(
				ignore_permissions=True
			)
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"Meta: could not remember ad {ad_id}")


def _ad_names(lead: dict) -> dict:
	"""The ad-level names Meta already put on the lead, when it did.

	This is the cheap road and the one that works everywhere: no second call, no
	user token, nothing to keep in step. `describe_ad` stays for the leads that
	arrive without them — an older Graph version, or a backfill that had to ask
	for less.
	"""
	names = {key: (lead.get(key) or "") for key in ("ad_name", "adset_name", "campaign_id", "campaign_name")}
	return names if (names["ad_name"] or names["campaign_name"]) else {}


def _attribute(doc, lead: dict, form_id: str | None, token: str | None = None) -> None:
	"""Credit a lead-ad submission to the ad that produced it.

	These leads never touch a browser we track — Meta hands them over server to
	server — so there is no session to read. `is_organic` is what separates a paid
	placement from a lead form on an organic post.

	The ad is named, not numbered: "arrived from the ad Promo Autunno, campaign
	Lead Settembre" is worth incomparably more to whoever reads the record than
	the id of the same ad. The names usually travel with the lead; `describe_ad`
	is the fallback for when they do not. The form name stays the fallback
	for the campaign slot, which is what an organic lead has instead.
	"""
	from crm.api.tracking import attribute

	organic = bool(lead.get("is_organic"))
	instagram = lead.get("platform") == "ig"
	ad = _ad_names(lead)
	if not ad and lead.get("ad_id") and not organic:
		ad = describe_ad(lead.get("ad_id"), token)
	form_name = frappe.db.get_value("Facebook Lead Form", form_id, "form_name") or ""

	attribute(
		doc,
		category="Organic Social" if organic else "Paid Social",
		dimensions={
			"source": "instagram" if instagram else "facebook",
			"medium": "social" if organic else "paid_social",
			"campaign": ad.get("campaign_name") or form_name,
			"term": ad.get("adset_name") or "",
			"content": ad.get("ad_name") or lead.get("ad_id") or "",
			"landing_page": "lead_ad_form",
		},
	)


def _note_unmapped_answers(lead_doc, answers: list[tuple[str, str]]) -> None:
	"""Park the answers with no CRM field on the lead, instead of dropping them."""
	lines = "".join(
		f"<li><b>{frappe.utils.escape_html(q)}</b>: {frappe.utils.escape_html(a)}</li>" for q, a in answers
	)
	try:
		lead_doc.add_comment(
			"Comment",
			_("Form answers with no mapped field:") + f"<ul>{lines}</ul>",
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Meta: could not record unmapped answers")


def get_question_labels(form_id: str | None) -> dict:
	if not form_id:
		return {}
	rows = frappe.get_all("Facebook Lead Form Question", filters={"parent": form_id}, fields=["key", "label"])
	return {row.key: row.label for row in rows if row.label}


def get_question_mapping(form_id: str | None) -> dict:
	if not form_id:
		return {}
	rows = frappe.get_all(
		"Facebook Lead Form Question",
		filters={"parent": form_id},
		fields=["key", "mapped_to_crm_field"],
	)
	return {row.key: row.mapped_to_crm_field for row in rows if row.mapped_to_crm_field}


# Meta's Lead Ads Testing Tool answers every question with
# "<test lead: dummy data for nome>". Frappe sees a tag, its HTML sanitiser
# removes it, and the value arrives EMPTY — so the lead died on a mandatory
# first name. The one flow every App Review reviewer uses was the one flow that
# could not work, and the error blamed a missing name that Meta had sent.
TEST_PLACEHOLDER = re.compile(r"<\s*test lead:[^>]*>", re.IGNORECASE)


def clean_answer(value) -> str:
	"""An answer as typed, minus what the sanitiser would silently swallow."""
	value = str(value).strip()
	value = TEST_PLACEHOLDER.sub("Test", value)
	if "<" in value and ">" in value:
		# whatever else arrives wrapped in angle brackets would be eaten just as
		# silently: keep the text, lose the brackets
		value = value.replace("<", "").replace(">", "").strip()
	return value


def normalize_value(crm_field: str, value):
	"""One answer, ready for its field — or nothing, rather than a lost lead.

	Frappe validates phone numbers and email addresses, and a value it refuses
	raises on save: "Test is not a valid Phone Number" cost us every test lead
	the moment they stopped being eaten by the sanitiser. An answer that cannot
	be a phone is not a phone, and dropping it keeps the person, their name and
	every other answer. The original text is not lost either: an unmappable
	answer is already written on the lead as a note.
	"""
	value = clean_answer(value)
	if crm_field in ("mobile_no", "phone"):
		# Meta sends phones like "+3933312345 67" / "p:+39..." — keep digits and +
		value = value.removeprefix("p:")
		value = "+" + "".join(ch for ch in value if ch.isdigit()) if value.startswith("+") else value
		if not any(ch.isdigit() for ch in value):
			return ""
	if crm_field == "email" and "@" not in value:
		return ""
	return value


def _ensure_source(source_name: str) -> str:
	if not frappe.db.exists("CRM Lead Source", source_name):
		frappe.get_doc({"doctype": "CRM Lead Source", "source_name": source_name}).insert(
			ignore_permissions=True
		)
	return source_name


def _log_failure(lead_data: dict, form_id: str | None, traceback: str):
	try:
		frappe.get_doc(
			{
				"doctype": "Failed Lead Sync Log",
				"type": "Failure",
				"lead_data": frappe.as_json(lead_data),
				"form": form_id,
				"traceback": traceback,
			}
		).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Meta: failed to write failure log")


# --- hourly reconciliation --------------------------------------------------


def reconcile_synced_pages() -> None:
	"""Hourly safety net: Meta retries failed webhooks for only 36 hours, so we
	re-poll the last 2 days of every synced page's forms (dedup makes it cheap)."""
	since = frappe.utils.add_to_date(frappe.utils.now_datetime(), days=-2)
	pages = frappe.get_all("Facebook Page", filters={"sync_enabled": 1}, pluck="name")
	if not pages:
		return
	forms = frappe.get_all("Facebook Lead Form", filters={"page": ["in", pages]}, pluck="name")
	for form_id in forms:
		try:
			backfill_form(form_id, since=since)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), f"Meta: reconciliation failed for form {form_id}")


# --- daily token health -----------------------------------------------------


def check_token_health() -> None:
	"""Daily: verify page tokens still work; flag pages and notify managers."""
	from crm.integrations.meta.client import debug_token, get_app_id

	if not get_app_id():
		return
	broken = []
	for page in frappe.get_all("Facebook Page", filters={"sync_enabled": 1}, pluck="name"):
		token = get_page_token(page)
		valid = False
		if token:
			try:
				valid = bool(debug_token(token).get("is_valid"))
			except Exception:
				valid = False
		frappe.db.set_value("Facebook Page", page, "token_valid", 1 if valid else 0, update_modified=False)
		if not valid:
			broken.append(page)
	if broken:
		frappe.log_error(
			f"Meta pages with invalid tokens: {', '.join(broken)}. Reconnect Facebook from Settings.",
			"Meta Lead Ads: token expired",
		)
