# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Lead ingestion shared by the real-time webhook and the polling backfill.

Deduplication is by Meta's lead id (`facebook_lead_id`) — the id is globally
unique, which makes webhook + backfill safely idempotent. Facebook keeps lead
data for 90 days only, so the backfill can never recover older leads.
"""

import frappe
from frappe import _

from crm.integrations.meta.client import MetaAPIError, graph_get, graph_get_paginated

# documented lead-node fields; PLATFORM_FIELDS adds `platform` (fb/ig) which is
# not guaranteed on every Graph version — we retry without it on error 100
LEAD_FIELDS = "id,created_time,ad_id,form_id,is_organic,field_data"
LEAD_FIELDS_WITH_PLATFORM = LEAD_FIELDS + ",platform"


def fetch_lead(leadgen_id: str, token: str) -> dict:
	try:
		return graph_get(leadgen_id, token, {"fields": LEAD_FIELDS_WITH_PLATFORM})
	except MetaAPIError as exc:
		if exc.code == 100:  # invalid field on this version
			return graph_get(leadgen_id, token, {"fields": LEAD_FIELDS})
		raise


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
	if not page_id or not frappe.db.get_value("Facebook Page", page_id, "sync_enabled"):
		return

	token = get_page_token(page_id)
	if not token:
		_log_failure({"leadgen_id": leadgen_id}, form_id, _("No page token available"))
		return

	frappe.db.set_value(
		"Facebook Page", page_id, "last_webhook_at", frappe.utils.now(), update_modified=False
	)

	try:
		lead = fetch_lead(leadgen_id, token)
	except MetaAPIError as exc:
		_log_failure({"leadgen_id": leadgen_id}, form_id, str(exc))
		return
	store_lead(lead, lead.get("form_id") or form_id)


def backfill_form(form_id: str, since=None, page_token: str | None = None) -> dict:
	"""Polling path: fetch all (remaining) leads of a form, paginated."""
	token = page_token
	if not token:
		page = frappe.db.get_value("Facebook Lead Form", form_id, "page")
		token = get_page_token(page) if page else None
	if not token:
		frappe.throw(_("No page token available for this form. Reconnect Facebook."))

	params = {"fields": LEAD_FIELDS}  # keep the safe set for bulk reads
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

	counts = {"created": 0, "merged": 0, "duplicates": 0, "failed": 0}
	for lead in graph_get_paginated(f"{form_id}/leads", token, params, max_pages=200):
		result = store_lead(lead, form_id)
		# "merged" is a submission filed on somebody the CRM already knew
		key = "duplicates" if result == "duplicate" else result
		counts[key] = counts.get(key, 0) + 1
	return counts


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


def submission_row(lead: dict, form_id: str | None) -> dict:
	return {
		"leadgen_id": lead.get("id"),
		"form": form_id or "",
		"form_name": frappe.db.get_value("Facebook Lead Form", form_id, "form_name") or "",
		"submitted_on": lead.get("created_time") or frappe.utils.now(),
		"platform": "Instagram" if lead.get("platform") == "ig" else "Facebook",
	}


def store_lead(lead: dict, form_id: str | None) -> str:
	"""Map field_data → CRM Lead via the form's question mapping. Idempotent."""
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
		if not crm_field:
			# an answer nobody mapped is still the customer talking: keep it
			unmapped.append((labels.get(key) or key, ", ".join(str(v) for v in raw_values)))
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
		return _merge_submission(person, lead, form_id, values, unmapped)

	values.update(
		{
			"doctype": "CRM Lead",
			"source": _ensure_source("Instagram" if lead.get("platform") == "ig" else "Facebook"),
			"facebook_lead_id": lead_id,
			"facebook_form_id": form_id,
			"facebook_submissions": [submission_row(lead, form_id)],
		}
	)
	try:
		doc = frappe.get_doc(values)
		_attribute(doc, lead, form_id)
		doc.insert(ignore_permissions=True)
		record_import(lead, form_id, doc.name, "Created")
		if unmapped:
			_note_unmapped_answers(doc, unmapped)
		_note_form_submitted(doc, form_id)
		return "created"
	except frappe.UniqueValidationError:
		return "duplicate"
	except Exception:
		_log_failure(lead, form_id, frappe.get_traceback())
		return "failed"


def _merge_submission(person: str, lead: dict, form_id: str | None, values: dict, unmapped: list) -> str:
	"""File a submission on the person who made it, instead of cloning them.

	What they typed this time fills only what is still empty: a number somebody
	corrected by hand in the CRM outranks the one re-typed into an ad form. The
	first touch is theirs already; this becomes the last one.
	"""
	try:
		doc = frappe.get_doc("CRM Lead", person)
		for field, value in values.items():
			if value and not doc.get(field):
				doc.set(field, value)
		if not doc.facebook_lead_id:
			doc.facebook_lead_id = lead.get("id")
			doc.facebook_form_id = form_id
		doc.append("facebook_submissions", submission_row(lead, form_id))
		_attribute(doc, lead, form_id)
		doc.save(ignore_permissions=True)
		record_import(lead, form_id, doc.name, "Merged")
		if unmapped:
			_note_unmapped_answers(doc, unmapped)
		_note_form_submitted(doc, form_id)
		return "merged"
	except Exception:
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


def _attribute(doc, lead: dict, form_id: str | None) -> None:
	"""Credit a lead-ad submission to the ad that produced it.

	These leads never touch a browser we track — Meta hands them over server to
	server — so there is no session to read. `is_organic` is what separates a paid
	placement from a lead form on an organic post, and `ad_id` is the closest thing
	the lead node gives us to a creative, so it goes in the content slot.
	"""
	from crm.api.tracking import attribute

	organic = bool(lead.get("is_organic"))
	instagram = lead.get("platform") == "ig"
	attribute(
		doc,
		category="Organic Social" if organic else "Paid Social",
		dimensions={
			"source": "instagram" if instagram else "facebook",
			"medium": "social" if organic else "paid_social",
			"campaign": frappe.db.get_value("Facebook Lead Form", form_id, "form_name") or "",
			"content": lead.get("ad_id") or "",
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


def normalize_value(crm_field: str, value):
	value = str(value).strip()
	if crm_field in ("mobile_no", "phone"):
		# Meta sends phones like "+3933312345 67" / "p:+39..." — keep digits and +
		value = value.removeprefix("p:")
		value = "+" + "".join(ch for ch in value if ch.isdigit()) if value.startswith("+") else value
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
