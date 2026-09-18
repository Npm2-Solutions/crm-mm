# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The ad as a thing, not as a number.

Two questions the id cannot answer and the person on the phone needs:

- *what did they actually see?* — the headline, the text and the picture of the
  ad that made them leave their number. Whoever calls a lead five minutes after
  it arrives is the one person for whom this matters most, and today they have
  to go hunting in Ads Manager for it.
- *is this ad even running?* — an ad rejected by Meta stops bringing leads
  without telling anybody. The client finds out from the silence.

Both are read with the user token, because both live on the ad account. Both are
remembered, because neither changes often, and neither is ever worth failing a
page or a job over.
"""

import frappe
from frappe.utils import date_diff, now

from crm.integrations.meta.client import graph_get, graph_get_paginated

CREATIVE_FIELDS = "name,preview_shareable_link,creative{title,body,thumbnail_url}"
CREATIVE_CACHE_DAYS = 30

# what Meta means by "this is not delivering", in its own words
NOT_RUNNING = {"DISAPPROVED", "WITH_ISSUES", "PENDING_REVIEW", "ADSET_PAUSED", "CAMPAIGN_PAUSED"}


def read_creative(ad_id: str) -> dict:
	"""What this ad looks like, asked once a month at most.

	Lazy on purpose: it is read when somebody opens a lead that came from the ad,
	so an ad nobody looks at costs nothing. A refusal returns what we already
	have — the lead's own screen must never depend on Meta answering.
	"""
	if not ad_id:
		return {}
	known = _stored(ad_id)
	if (
		known.get("creative_fetched_on")
		and date_diff(now(), known["creative_fetched_on"]) < CREATIVE_CACHE_DAYS
	):
		return known

	from crm.integrations.meta.insights import user_token

	try:
		data = graph_get(ad_id, user_token(), {"fields": CREATIVE_FIELDS})
	except Exception as exc:
		frappe.logger("meta").info(f"Could not read the creative of ad {ad_id}: {exc}")
		return known

	creative = data.get("creative") or {}
	values = {
		"ad_name": data.get("name") or known.get("ad_name") or "",
		"creative_title": creative.get("title") or "",
		"creative_body": creative.get("body") or "",
		"thumbnail_url": creative.get("thumbnail_url") or "",
		"permalink": data.get("preview_shareable_link") or "",
		"creative_fetched_on": now(),
	}
	_remember(ad_id, values)
	return {**known, **values}


def _stored(ad_id: str) -> dict:
	row = frappe.db.get_value(
		"Facebook Ad",
		ad_id,
		[
			"ad_name",
			"adset_name",
			"campaign_name",
			"creative_title",
			"creative_body",
			"thumbnail_url",
			"permalink",
			"creative_fetched_on",
			"effective_status",
		],
		as_dict=True,
	)
	return dict(row) if row else {}


def _remember(ad_id: str, values: dict) -> None:
	try:
		if frappe.db.exists("Facebook Ad", ad_id):
			frappe.db.set_value("Facebook Ad", ad_id, values, update_modified=False)
		else:
			frappe.get_doc({"doctype": "Facebook Ad", "ad_id": ad_id, **values}).insert(
				ignore_permissions=True
			)
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"Meta: could not remember ad {ad_id}")


# --- is it running? ---------------------------------------------------------


def refresh_delivery(account: str) -> int:
	"""One call for a whole account: which of its ads are actually delivering.

	Cheaper and more useful than asking ad by ad, and it runs beside the daily
	spend read — the two answer the same question from opposite sides ("no leads
	today" is either no money spent or an ad Meta stopped).
	"""
	from crm.integrations.meta.insights import user_token

	token = user_token()
	seen = 0
	for ad in graph_get_paginated(
		f"{account}/ads", token, {"fields": "id,name,effective_status", "limit": 200}, max_pages=25
	):
		if not ad.get("id"):
			continue
		_remember(
			ad["id"],
			{
				"ad_name": ad.get("name") or "",
				"effective_status": ad.get("effective_status") or "",
				"status_checked_on": now(),
			},
		)
		seen += 1
	return seen


def stopped_ads(days: int = 30) -> list[dict]:
	"""Ads that brought leads recently and are not running now.

	The join is the point: an old paused ad is housekeeping, an ad that was
	working until yesterday and is now rejected is money and leads stopping.
	"""
	return frappe.db.sql(
		"""
		select a.ad_id, a.ad_name, a.campaign_name, a.effective_status, count(l.name) as leads
		from `tabFacebook Ad` a
		inner join `tabCRM Lead` l on l.facebook_ad_id = a.ad_id
		where a.effective_status in %(statuses)s
			and date(l.creation) >= date_sub(curdate(), interval %(days)s day)
		group by a.ad_id, a.ad_name, a.campaign_name, a.effective_status
		order by leads desc
		""",
		{"statuses": tuple(NOT_RUNNING), "days": frappe.utils.cint(days)},
		as_dict=True,
	)


def ad_of_record(doctype: str, name: str) -> str:
	"""The ad that brought this lead, or the lead behind this deal."""
	if doctype == "CRM Lead":
		return frappe.db.get_value("CRM Lead", name, "facebook_ad_id") or ""
	if doctype == "CRM Deal":
		lead = frappe.db.get_value("CRM Deal", name, "lead")
		return (frappe.db.get_value("CRM Lead", lead, "facebook_ad_id") or "") if lead else ""
	return ""
