# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Ad spend, and what it bought.

Meta knows what was spent. Only the CRM knows what closed. Neither half is worth
much alone — a cost per lead says nothing about whether those leads buy, and a
won deal says nothing about what it cost to get — and nobody but us holds both.
So the spend comes in once a day and gets read on the same line as the outcome.

The lead count is ours, never Meta's: we know exactly which leads arrived from
which ad (`CRM Lead.facebook_ad_id`), and counting them ourselves avoids guessing
which of Meta's action types means "a form was submitted".
"""

import frappe
from frappe import _
from frappe.utils import add_days, flt, now_datetime, nowdate

from crm.integrations.meta.client import graph_get_paginated

INSIGHT_FIELDS = "ad_id,ad_name,adset_name,campaign_id,campaign_name,spend,impressions,clicks"

# Re-read the last week every day. Meta revises recent days (late-charged spend,
# attribution settling), and re-reading a day we already have costs one page of
# results and overwrites the row instead of adding a second one.
SYNC_WINDOW_DAYS = 7


def user_token() -> str:
	"""The token that may read an ad account: the user's, never a page's."""
	token = frappe.get_doc("CRM Meta Settings").get_password("user_access_token", raise_exception=False)
	if not token:
		frappe.throw(_("Facebook is not connected. Connect it from Settings first."))
	return token


# --- the accounts -----------------------------------------------------------


def discover_accounts() -> list[str]:
	"""Remember every ad account this connection can see, enabling none.

	An agency user can see dozens of accounts that have nothing to do with this
	CRM, so the list is an offer, not a decision: `sync_enabled` stays off until
	somebody says which accounts this client's money runs through.
	"""
	token = user_token()
	seen = []
	for account in graph_get_paginated(
		"me/adaccounts",
		token,
		{"fields": "id,name,currency,account_status,business{name}"},
		max_pages=20,
	):
		seen.append(remember_account(account))
	return seen


def remember_account(data: dict) -> str:
	account_id = data.get("id") or ""
	if not account_id:
		return ""
	values = {
		"account_name": data.get("name") or account_id,
		"currency": data.get("currency") or "",
		"account_status": frappe.utils.cint(data.get("account_status")),
		"business_name": (data.get("business") or {}).get("name") or "",
	}
	if frappe.db.exists("Facebook Ad Account", account_id):
		# never touch sync_enabled here: that answer belongs to the person
		frappe.db.set_value("Facebook Ad Account", account_id, values, update_modified=False)
	else:
		frappe.get_doc({"doctype": "Facebook Ad Account", "account_id": account_id, **values}).insert(
			ignore_permissions=True
		)
	return account_id


# --- the spend --------------------------------------------------------------


def sync_account(account: str, days: int = SYNC_WINDOW_DAYS) -> int:
	"""One account's daily spend per ad. Returns how many day-rows were read."""
	token = user_token()
	params = {
		"level": "ad",
		"fields": INSIGHT_FIELDS,
		"time_increment": 1,
		"time_range": frappe.as_json({"since": add_days(nowdate(), -days), "until": nowdate()}),
		"limit": 200,
	}
	rows = 0
	for row in graph_get_paginated(f"{account}/insights", token, params, max_pages=50):
		if _store_insight(account, row):
			rows += 1
	frappe.db.set_value(
		"Facebook Ad Account",
		account,
		{"last_synced_on": now_datetime(), "last_error": ""},
		update_modified=False,
	)
	return rows


def _store_insight(account: str, row: dict) -> bool:
	ad_id = row.get("ad_id")
	date = row.get("date_start")
	if not ad_id or not date:
		return False
	values = {
		"ad_account": account,
		"ad_id": ad_id,
		"date": date,
		"ad_name": row.get("ad_name") or "",
		"adset_name": row.get("adset_name") or "",
		"campaign_id": row.get("campaign_id") or "",
		"campaign_name": row.get("campaign_name") or "",
		"spend": flt(row.get("spend")),
		"impressions": frappe.utils.cint(row.get("impressions")),
		"clicks": frappe.utils.cint(row.get("clicks")),
		"currency": frappe.db.get_value("Facebook Ad Account", account, "currency") or "",
	}
	name = f"{ad_id}-{date}"
	if frappe.db.exists("Facebook Ad Insight", name):
		frappe.db.set_value("Facebook Ad Insight", name, values, update_modified=False)
	else:
		frappe.get_doc({"doctype": "Facebook Ad Insight", **values}).insert(ignore_permissions=True)
	return True


def sync_ad_spend(days: int = SYNC_WINDOW_DAYS) -> dict:
	"""Daily job: every enabled account, each one on its own.

	One account failing — a revoked role, a closed account — must not cost the
	others their numbers, so each is committed and each failure is recorded where
	the person who enabled it will see it.
	"""
	from crm.integrations.meta.ads import refresh_delivery

	read = {}
	for account in frappe.get_all("Facebook Ad Account", filters={"sync_enabled": 1}, pluck="name"):
		try:
			read[account] = sync_account(account, days)
			# same trip, opposite side of the same question: "no leads today" is
			# either no money spent or an ad Meta quietly stopped
			refresh_delivery(account)
			frappe.db.commit()
		except Exception as exc:
			frappe.db.rollback()
			frappe.db.set_value(
				"Facebook Ad Account", account, "last_error", str(exc)[:500], update_modified=False
			)
			frappe.db.commit()
			frappe.log_error(frappe.get_traceback(), f"Meta insights: {account} could not be read")
	return read


# --- what the money bought --------------------------------------------------


def performance(days: int = 30) -> dict:
	"""One line per ad: what it cost, what it brought, what that came to.

	An ad with spend and no leads has to appear — that is the line worth seeing —
	so the rows are the union of both sides, not a join on either.
	"""
	since = add_days(nowdate(), -days)
	rows: dict[str, dict] = {}

	for row in frappe.db.sql(
		"""
		select ad_id,
			max(ad_name) as ad_name, max(adset_name) as adset_name,
			max(campaign_name) as campaign_name, max(currency) as currency,
			sum(spend) as spend, sum(impressions) as impressions, sum(clicks) as clicks
		from `tabFacebook Ad Insight`
		where date >= %(since)s
		group by ad_id
		""",
		{"since": since},
		as_dict=True,
	):
		rows[row.ad_id] = {**row, "leads": 0, "deals": 0, "won": 0, "revenue": 0.0}

	for row in frappe.db.sql(
		"""
		select facebook_ad_id as ad_id, count(*) as leads
		from `tabCRM Lead`
		where ifnull(facebook_ad_id, '') != '' and date(creation) >= %(since)s
		group by facebook_ad_id
		""",
		{"since": since},
		as_dict=True,
	):
		rows.setdefault(row.ad_id, _empty(row.ad_id))["leads"] = row.leads

	for row in frappe.db.sql(
		"""
		select l.facebook_ad_id as ad_id,
			count(d.name) as deals,
			sum(case when s.type = 'Won' then 1 else 0 end) as won,
			sum(case when s.type = 'Won' then ifnull(d.deal_value, 0) else 0 end) as revenue
		from `tabCRM Deal` d
		inner join `tabCRM Lead` l on l.name = d.lead
		left join `tabCRM Deal Status` s on s.name = d.status
		where ifnull(l.facebook_ad_id, '') != '' and date(l.creation) >= %(since)s
		group by l.facebook_ad_id
		""",
		{"since": since},
		as_dict=True,
	):
		entry = rows.setdefault(row.ad_id, _empty(row.ad_id))
		entry.update({"deals": row.deals, "won": row.won, "revenue": flt(row.revenue)})

	# what the CRM knows about these ads beyond the spend: the names of the ones
	# with no spend in the window, and whether each one is still running
	for ad_id, entry in rows.items():
		known = frappe.db.get_value(
			"Facebook Ad",
			ad_id,
			["ad_name", "adset_name", "campaign_name", "effective_status"],
			as_dict=True,
		)
		entry["effective_status"] = (known or {}).get("effective_status") or ""
		if known and not entry.get("ad_name"):
			for key in ("ad_name", "adset_name", "campaign_name"):
				entry[key] = known.get(key) or ""

	for entry in rows.values():
		_derive(entry)

	ordered = sorted(rows.values(), key=lambda row: (flt(row["spend"]), row["leads"]), reverse=True)
	return {"days": days, "since": since, "rows": ordered, "totals": _totals(ordered)}


def _empty(ad_id: str) -> dict:
	return {
		"ad_id": ad_id,
		"ad_name": "",
		"adset_name": "",
		"campaign_name": "",
		"currency": "",
		"spend": 0.0,
		"impressions": 0,
		"clicks": 0,
		"leads": 0,
		"deals": 0,
		"won": 0,
		"revenue": 0.0,
		"effective_status": "",
	}


def _derive(entry: dict) -> None:
	"""The three numbers nobody can read off Meta or off the CRM alone.

	A cost is left as None rather than zero when there is nothing to divide by:
	"cost per customer: 0" would read as free, and the truth is "not yet".
	"""
	spend = flt(entry["spend"])
	entry["cost_per_lead"] = spend / entry["leads"] if entry["leads"] else None
	entry["cost_per_won"] = spend / entry["won"] if entry["won"] else None
	entry["roas"] = flt(entry["revenue"]) / spend if spend else None


def _totals(rows: list[dict]) -> dict:
	"""The bottom line — and an honest flag when it should not be added up.

	Two ad accounts can bill in two currencies. Summing them would produce a
	confident number that means nothing, so the sum still happens (the UI has to
	show something) but it says so, and the currency is left blank.
	"""
	total = _empty("")
	currencies = {row.get("currency") for row in rows if row.get("currency")}
	for row in rows:
		for key in ("spend", "revenue"):
			total[key] = flt(total[key]) + flt(row[key])
		for key in ("impressions", "clicks", "leads", "deals", "won"):
			total[key] += frappe.utils.cint(row[key])
	total["currency"] = next(iter(currencies)) if len(currencies) == 1 else ""
	total["mixed_currencies"] = len(currencies) > 1
	_derive(total)
	total.pop("ad_id", None)
	return total


# --- running it without waiting ---------------------------------------------

SPEND_FLAG = "meta_spend_sync_running"


def spend_sync_running() -> bool:
	return bool(frappe.cache().get_value(SPEND_FLAG))


def start_spend_sync(days: int = SYNC_WINDOW_DAYS) -> None:
	"""Read the spend in the background.

	A request cannot hold the browser for as long as several accounts of daily
	rows take, and the token must not travel through the job arguments — the job
	reads it from the settings itself.
	"""
	frappe.cache().set_value(SPEND_FLAG, 1, expires_in_sec=1800)
	frappe.enqueue(
		"crm.integrations.meta.insights.run_spend_sync",
		queue="long",
		timeout=1800,
		days=frappe.utils.cint(days) or SYNC_WINDOW_DAYS,
	)


def run_spend_sync(days: int = SYNC_WINDOW_DAYS) -> None:
	try:
		sync_ad_spend(days)
	finally:
		frappe.cache().delete_value(SPEND_FLAG)
