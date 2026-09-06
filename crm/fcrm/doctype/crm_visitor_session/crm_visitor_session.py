# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_datetime, now, time_diff_in_seconds

from crm.utils import attribution

#: Attribution fields copied from a session onto a lead or deal, as
#: `session fieldname -> suffix on the record`. The record spells them
#: `first_touch_<suffix>` and `last_touch_<suffix>`.
SNAPSHOT_FIELDS = {
	"source_category": "category",
	"source": "source",
	"medium": "medium",
	"campaign": "campaign",
	"utm_term": "term",
	"utm_content": "content",
	"landing_page": "landing_page",
	"referrer": "referrer",
}


class CRMVisitorSession(Document):
	"""One visit, and the marketing read of it.

	A session is the unit attribution is credited to: the campaign that brought the
	visitor in is a property of the *visit*, not of the individual page views, and
	that is why "first touch" and "last touch" on a lead are pointers to two
	sessions rather than a pile of loose UTM columns.
	"""

	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		ad_group_id: DF.Data | None
		ad_id: DF.Data | None
		browser: DF.Data | None
		campaign: DF.Data | None
		campaign_id: DF.Data | None
		converted: DF.Check
		country: DF.Data | None
		ctwa_clid: DF.Data | None
		dclid: DF.Data | None
		deal: DF.Link | None
		device_type: DF.Literal["", "Desktop", "Mobile", "Tablet", "Bot"] | None
		duration: DF.Duration | None
		epik: DF.Data | None
		event_count: DF.Int
		fbclid: DF.Data | None
		gbraid: DF.Data | None
		gclid: DF.Data | None
		ip_address: DF.Data | None
		irclickid: DF.Data | None
		landing_page: DF.SmallText | None
		language: DF.Data | None
		last_activity_on: DF.Datetime | None
		lead: DF.Link | None
		li_fat_id: DF.Data | None
		medium: DF.Data | None
		msclkid: DF.Data | None
		os: DF.Data | None
		page_view_count: DF.Int
		rdt_cid: DF.Data | None
		referrer: DF.SmallText | None
		referrer_domain: DF.Data | None
		sccid: DF.Data | None
		session_id: DF.Data
		source: DF.Data | None
		source_category: (
			DF.Literal[
				"",
				"Paid Search",
				"Paid Social",
				"Organic Search",
				"Organic Social",
				"Email",
				"SMS",
				"Affiliate",
				"Referral",
				"Direct Traffic",
				"CRM UI",
				"Third Party",
				"Unknown",
			]
			| None
		)
		started_on: DF.Datetime | None
		ttclid: DF.Data | None
		twclid: DF.Data | None
		user_agent: DF.SmallText | None
		utm_campaign: DF.Data | None
		utm_content: DF.Data | None
		utm_id: DF.Data | None
		utm_keyword: DF.Data | None
		utm_match_type: DF.Data | None
		utm_medium: DF.Data | None
		utm_source: DF.Data | None
		utm_term: DF.Data | None
		visitor: DF.Link
		wbraid: DF.Data | None
		yclid: DF.Data | None
	# end: auto-generated types

	def snapshot(self, prefix: str) -> dict:
		"""This session's attribution as `<prefix>_<suffix>` values, ready to write
		onto a lead or deal. `prefix` is `first_touch` or `last_touch`."""
		values = {f"{prefix}_{suffix}": self.get(field) or "" for field, suffix in SNAPSHOT_FIELDS.items()}
		values[f"{prefix}_on"] = self.started_on
		values[f"{prefix}_session"] = self.name
		return values

	def touch(self) -> None:
		"""Extend the session to now. Written with `db_set` rather than `save()`:
		a beacon fires on every page and must not cost a full document round trip."""
		self.db_set(
			{
				"last_activity_on": now(),
				"duration": max(0, int(time_diff_in_seconds(now(), self.started_on))),
			},
			update_modified=False,
		)


def _carries_new_campaign(session: "CRMVisitorSession", data: dict) -> bool:
	"""Whether an arriving visit is a different campaign from the running session.

	A visitor who is mid-session and clicks an ad has started something new, and
	crediting that click to the session they were already in would lose it. This is
	the same rule Google Analytics applies.
	"""
	for field in ("utm_source", "utm_medium", "utm_campaign", "utm_id"):
		incoming = (data.get(field) or "").strip()
		if incoming and incoming != (session.get(field) or "").strip():
			return True
	for field in attribution.CLICK_ID_PARAMS:
		incoming = (data.get(field) or "").strip()
		if incoming and incoming != (session.get(field) or "").strip():
			return True
	return False


def _is_live(session: "CRMVisitorSession", timeout_minutes: int) -> bool:
	last = session.last_activity_on or session.started_on
	if not last:
		return False
	return time_diff_in_seconds(now(), get_datetime(last)) < timeout_minutes * 60


def start_or_continue(
	visitor,
	session_id: str | None,
	url: str | None,
	referrer: str | None,
	client: dict | None = None,
	timeout_minutes: int = 30,
	own_domains=(),
) -> "CRMVisitorSession":
	"""The session this visit belongs to — the running one, or a fresh one.

	A new session is started when there is no live one (inactivity past
	`timeout_minutes`) or when the visit arrives under a different campaign than
	the one already running.
	"""
	client = client or {}
	data = attribution.attribute(url, referrer, own_domains=own_domains)

	if session_id:
		existing = frappe.db.get_value(
			"CRM Visitor Session", {"session_id": session_id, "visitor": visitor.name}, "name"
		)
		if existing:
			session = frappe.get_doc("CRM Visitor Session", existing)
			if _is_live(session, timeout_minutes) and not _carries_new_campaign(session, data):
				session.touch()
				return session

	values = {
		"doctype": "CRM Visitor Session",
		"session_id": frappe.generate_hash(length=32),
		"visitor": visitor.name,
		"started_on": now(),
		"last_activity_on": now(),
		"campaign": data.get("utm_campaign") or "",
		"lead": visitor.lead,
		"deal": visitor.deal,
	}
	for field in (
		"source_category",
		"source",
		"medium",
		"landing_page",
		"referrer",
		"referrer_domain",
		*attribution.UTM_PARAMS,
		*attribution.CLICK_ID_PARAMS,
		*attribution.AD_PARAM_ALIASES,
	):
		values[field] = data.get(field) or ""
	values.update({k: v for k, v in client.items() if v})

	session = frappe.get_doc(values)
	session.insert(ignore_permissions=True)

	visitor.db_set(
		{
			"session_count": (visitor.session_count or 0) + 1,
			"last_session": session.name,
			"first_session": visitor.first_session or session.name,
			"last_seen_on": now(),
		},
		update_modified=False,
	)
	return session
