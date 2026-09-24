# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Marketing: where people come from, and what the ads cost against what they sold.

Three sources of truth, each offered only when the site has it:

- the visitor tracker (``CRM Visitor Session``): traffic, channels, landing
  pages, campaigns — docs/progetto-ghl/15;
- Meta Lead Ads: every form filled on Facebook or Instagram, from the import
  ledger that survives the person being deleted (``Facebook Lead Import``);
- Meta ad spend (``Facebook Ad Insight``, one row per ad per day) crossed with
  the deals of the people each ad brought — the cost per customer and the return
  that neither Meta nor the CRM know alone (docs/progetto-ghl/23). Same rules
  as ``crm.integrations.meta.insights.performance``, over the dashboard's period.

Marketing numbers belong to the business, not to a salesperson: these widgets
count the whole site whatever the person filter says.
"""

from __future__ import annotations

from collections import defaultdict
from urllib.parse import urlparse

import frappe
from frappe import _, _lt
from frappe.query_builder import Case, DocType
from frappe.query_builder.functions import Count, IfNull, Sum

from crm.dashboard import charts
from crm.dashboard.context import Context, where
from crm.dashboard.queries import grouped, per_bucket, per_day, total, two_periods
from crm.dashboard.registry import Option, widget

Session = DocType("CRM Visitor Session")
Link = DocType("CRM Tracked Link")
Lead = DocType("CRM Lead")
Deal = DocType("CRM Deal")
Status = DocType("CRM Deal Status")
Import = DocType("Facebook Lead Import")
Insight = DocType("Facebook Ad Insight")
FailedSync = DocType("Failed Lead Sync Log")
ConversionEvent = DocType("Meta Conversion Event")

TRACKING = ("tracking",)
ROWS = Option("limit", _lt("Rows"), type="int", default=6, min=3, max=20)

# sessions that are the team working in the CRM, not visitors
INTERNAL = "CRM UI"


def real_visits():
	return IfNull(Session.source_category, "") != INTERNAL


# -- the visitor tracker ---------------------------------------------------------


@widget(
	"website_visitors",
	category="marketing",
	kind="number",
	title=_lt("Visitors"),
	description=_lt("Different people who visited your pages"),
	requires=TRACKING,
	scope="site",
	managers_only=True,
)
def website_visitors(ctx: Context):
	return charts.number(
		*two_periods(ctx, Session, Session.started_on, real_visits(), distinct=Session.visitor)
	)


@widget(
	"website_sessions",
	category="marketing",
	kind="number",
	title=_lt("Visits"),
	description=_lt("Visits to your pages; one person can visit many times"),
	requires=TRACKING,
	scope="site",
	managers_only=True,
)
def website_sessions(ctx: Context):
	return charts.number(*two_periods(ctx, Session, Session.started_on, real_visits()))


@widget(
	"visitor_conversion",
	category="marketing",
	kind="number",
	title=_lt("Visits that converted"),
	description=_lt("Share of visits that ended in a form, a booking or a new person"),
	requires=TRACKING,
	scope="site",
	managers_only=True,
)
def visitor_conversion(ctx: Context):
	def rate(previous: bool):
		query = frappe.qb.from_(Session).select(
			Count("*").as_("visits"), Sum(Session.converted).as_("converted")
		)
		row = where(query, ctx.within(Session.started_on, previous), real_visits()).run(as_dict=True)[0]
		return charts.ratio(row.converted, row.visits)

	now = rate(False)
	return charts.number(now or 0, rate(True), format="percent", compare="points", progress=now or 0)


@widget(
	"traffic_sources",
	category="marketing",
	kind="donut",
	title=_lt("Where visits come from"),
	description=_lt("Visits by channel: search, social, ads, email, direct…"),
	size=(10, 8),
	requires=TRACKING,
	scope="site",
	managers_only=True,
)
def traffic_sources(ctx: Context):
	rows = grouped(Session, Session.source_category, ctx.within(Session.started_on), real_visits())
	return charts.donut(
		[(_(key) if key else _("Unknown"), value) for key, value in rows], other_label=_("Other")
	)


@widget(
	"visits_trend",
	category="marketing",
	kind="axis",
	title=_lt("Visits over time"),
	description=_lt("Visits to your pages, and the ones that converted"),
	size=(10, 8),
	requires=TRACKING,
	scope="site",
	managers_only=True,
)
def visits_trend(ctx: Context):
	visits = per_bucket(ctx, per_day(ctx, Session, Session.started_on, real_visits()))
	converted = per_bucket(
		ctx, per_day(ctx, Session, Session.started_on, real_visits(), Session.converted == 1)
	)
	return charts.trend(
		ctx.buckets,
		ctx.grain,
		[
			charts.series("visits", _("Visits"), charts.fill(ctx.buckets, visits)),
			charts.series("converted", _("Converted"), charts.fill(ctx.buckets, converted)),
		],
	)


def page_of(url: str | None) -> str:
	"""The path of a landing page, without the host and the tracking parameters."""
	if not url:
		return _("Unknown")
	parsed = urlparse(url if "//" in url else f"//{url}")
	return parsed.path or "/"


@widget(
	"top_landing_pages",
	category="marketing",
	kind="table",
	title=_lt("Top landing pages"),
	description=_lt("The pages visits start on, and how many of those visits converted"),
	size=(10, 8),
	requires=TRACKING,
	scope="site",
	managers_only=True,
	options=(ROWS,),
)
def top_landing_pages(ctx: Context):
	query = frappe.qb.from_(Session).select(
		Session.landing_page, Count("*").as_("visits"), Sum(Session.converted).as_("converted")
	)
	query = where(query, ctx.within(Session.started_on), real_visits()).groupby(Session.landing_page)
	pages: dict[str, dict] = defaultdict(lambda: {"visits": 0, "converted": 0})
	for row in query.orderby(Count("*"), order=frappe.qb.desc).limit(200).run(as_dict=True):
		page = pages[page_of(row.landing_page)]
		page["visits"] += int(row.visits or 0)
		page["converted"] += int(row.converted or 0)
	rows = [
		{"page": path, **values, "rate": charts.ratio(values["converted"], values["visits"])}
		for path, values in pages.items()
	]
	rows.sort(key=lambda row: row["visits"], reverse=True)
	return charts.table(
		[
			{"key": "page", "label": _("Page"), "format": "text"},
			{"key": "visits", "label": _("Visits"), "format": "number"},
			{"key": "converted", "label": _("Converted"), "format": "number"},
			{"key": "rate", "label": _("Rate"), "format": "percent"},
		],
		rows[: ctx.option("limit", 6)],
		empty=_("No visit tracked in this period"),
	)


@widget(
	"top_campaigns",
	category="marketing",
	kind="table",
	title=_lt("Top campaigns"),
	description=_lt("Campaigns (utm_campaign) by visits and conversions"),
	size=(10, 8),
	requires=TRACKING,
	scope="site",
	managers_only=True,
	options=(ROWS,),
)
def top_campaigns(ctx: Context):
	campaign = IfNull(Session.campaign, Session.utm_campaign)
	query = frappe.qb.from_(Session).select(
		campaign.as_("campaign"),
		Session.source,
		Count("*").as_("visits"),
		Sum(Session.converted).as_("converted"),
	)
	query = where(query, ctx.within(Session.started_on), real_visits(), campaign.isnotnull(), campaign != "")
	rows = (
		query.groupby(campaign, Session.source)
		.orderby(Count("*"), order=frappe.qb.desc)
		.limit(ctx.option("limit", 6))
		.run(as_dict=True)
	)
	return charts.table(
		[
			{"key": "campaign", "label": _("Campaign"), "format": "text"},
			{"key": "source", "label": _("Source"), "format": "text"},
			{"key": "visits", "label": _("Visits"), "format": "number"},
			{"key": "converted", "label": _("Converted"), "format": "number"},
		],
		[
			{
				"campaign": row.campaign,
				"source": row.source,
				"visits": row.visits,
				"converted": row.converted or 0,
			}
			for row in rows
		],
		empty=_("No campaign traffic in this period"),
	)


@widget(
	"tracked_links",
	category="marketing",
	kind="table",
	title=_lt("Tracked links"),
	description=_lt("Your short links by clicks, since they were created"),
	size=(10, 8),
	live=True,
	requires=("tracked_links",),
	scope="site",
	managers_only=True,
	options=(ROWS,),
)
def tracked_links(ctx: Context):
	rows = (
		frappe.qb.from_(Link)
		.select(Link.slug, Link.description, Link.target_url, Link.click_count)
		.orderby(Link.click_count, order=frappe.qb.desc)
		.limit(ctx.option("limit", 6))
		.run(as_dict=True)
	)
	return charts.table(
		[
			{"key": "link", "label": _("Link"), "format": "text"},
			{"key": "clicks", "label": _("Clicks"), "format": "number"},
		],
		[{"link": row.description or row.slug, "clicks": row.click_count or 0} for row in rows],
		empty=_("No tracked link yet"),
	)


@widget(
	"web_form_requests",
	category="marketing",
	kind="number",
	title=_lt("Requests from forms"),
	description=_lt("Deals opened by people who filled in one of your forms"),
	requires=("web_forms",),
	keywords=("website", "contact form"),
)
def web_form_requests(ctx: Context):
	return charts.number(
		*two_periods(ctx, Deal, Deal.creation, Deal.source == "Web Form", ctx.owned(Deal.deal_owner)),
		route={"name": "Deals"},
	)


# -- Meta Lead Ads ----------------------------------------------------------------


@widget(
	"meta_leads",
	category="meta",
	kind="number",
	title=_lt("Leads from Meta"),
	description=_lt("Forms filled in on Facebook and Instagram, returning people included"),
	requires=("meta_leads",),
	scope="site",
)
def meta_leads(ctx: Context):
	return charts.number(*two_periods(ctx, Import, Import.imported_on), route={"name": "Leads"})


@widget(
	"meta_leads_trend",
	category="meta",
	kind="axis",
	title=_lt("Meta leads over time"),
	description=_lt("Forms filled in on Facebook and Instagram, day by day"),
	size=(10, 8),
	requires=("meta_leads",),
	scope="site",
)
def meta_leads_trend(ctx: Context):
	values = per_bucket(ctx, per_day(ctx, Import, Import.imported_on))
	return charts.trend(
		ctx.buckets,
		ctx.grain,
		[charts.series("leads", _("Leads from Meta"), charts.fill(ctx.buckets, values), type="bar")],
	)


@widget(
	"meta_leads_by_form",
	category="meta",
	kind="axis",
	title=_lt("Meta leads by form"),
	description=_lt("Which lead forms people fill in"),
	size=(10, 8),
	requires=("meta_leads",),
	scope="site",
)
def meta_leads_by_form(ctx: Context):
	rows = grouped(Import, IfNull(Import.form_name, Import.form), ctx.within(Import.imported_on), limit=10)
	return charts.bars(
		[{"form": key or _("Unknown"), "n": value} for key, value in rows],
		label_key="form",
		lines=[("n", _("Leads"))],
	)


@widget(
	"meta_sync_errors",
	category="meta",
	kind="number",
	title=_lt("Meta leads not imported"),
	description=_lt("Form fills that failed to import and are waiting for a retry"),
	live=True,
	requires=("meta_leads",),
	scope="site",
	managers_only=True,
)
def meta_sync_errors(ctx: Context):
	value = total(FailedSync, FailedSync.type == "Failure")
	payload = charts.number(value, negative_is_better=True)
	payload["settings"] = "Lead forms"
	return payload


# -- spend and return ---------------------------------------------------------------


def spend(ctx: Context, previous: bool = False) -> tuple[float, str | None]:
	"""Spend in the period, and its currency when every account bills in the same one."""
	low, high = ctx.dates(previous)
	query = (
		frappe.qb.from_(Insight)
		.select(Insight.currency, Sum(Insight.spend).as_("spend"))
		.where((Insight.date >= low) & (Insight.date <= high))
		.groupby(Insight.currency)
	)
	rows = query.run(as_dict=True)
	currencies = {row.currency for row in rows if row.currency}
	return sum(float(row.spend or 0) for row in rows), (
		next(iter(currencies)) if len(currencies) == 1 else None
	)


def ad_leads(ctx: Context, previous: bool = False) -> float:
	return total(Lead, IfNull(Lead.facebook_ad_id, "") != "", ctx.within(Lead.creation, previous))


def ad_sales(ctx: Context, previous: bool = False) -> tuple[float, float]:
	"""Won deals, and their value, of the people the ads brought in the period."""
	query = (
		frappe.qb.from_(Deal)
		.join(Lead)
		.on(Lead.name == Deal.lead)
		.left_join(Status)
		.on(Status.name == Deal.status)
		.select(
			Sum(Case().when(Status.type == "Won", 1).else_(0)).as_("won"),
			Sum(Case().when(Status.type == "Won", IfNull(Deal.deal_value, 0)).else_(0)).as_("revenue"),
		)
	)
	row = where(query, IfNull(Lead.facebook_ad_id, "") != "", ctx.within(Lead.creation, previous)).run(
		as_dict=True
	)[0]
	return float(row.won or 0), float(row.revenue or 0)


def per_unit(amount: float, units: float) -> float | None:
	return amount / units if units else None


@widget(
	"meta_spend",
	category="meta",
	kind="number",
	title=_lt("Ad spend"),
	description=_lt("What the Meta ads cost in the period"),
	requires=("meta_ads",),
	scope="site",
	managers_only=True,
)
def meta_spend(ctx: Context):
	now, currency = spend(ctx)
	before, _currency = spend(ctx, True)
	return charts.number(now, before, format="currency", currency=currency, negative_is_better=True)


@widget(
	"meta_cost_per_lead",
	category="meta",
	kind="number",
	title=_lt("Cost per lead"),
	description=_lt("Ad spend divided by the people the ads brought in"),
	requires=("meta_ads",),
	scope="site",
	managers_only=True,
	keywords=("cpl",),
)
def meta_cost_per_lead(ctx: Context):
	now, currency = spend(ctx)
	before, _currency = spend(ctx, True)
	return charts.number(
		per_unit(now, ad_leads(ctx)) or 0,
		per_unit(before, ad_leads(ctx, True)),
		format="currency",
		currency=currency,
		negative_is_better=True,
	)


@widget(
	"meta_cost_per_customer",
	category="meta",
	kind="number",
	title=_lt("Cost per customer"),
	description=_lt("Ad spend divided by the deals won from the people the ads brought"),
	requires=("meta_ads",),
	scope="site",
	managers_only=True,
	keywords=("cac", "acquisition"),
)
def meta_cost_per_customer(ctx: Context):
	now, currency = spend(ctx)
	before, _currency = spend(ctx, True)
	won, _revenue = ad_sales(ctx)
	won_before, _revenue_before = ad_sales(ctx, True)
	value = per_unit(now, won)
	payload = charts.number(
		value or 0,
		per_unit(before, won_before),
		format="currency",
		currency=currency,
		negative_is_better=True,
	)
	if value is None:
		payload["hint"] = _("No deal won yet")
	return payload


@widget(
	"meta_roas",
	category="meta",
	kind="number",
	title=_lt("Return on ad spend"),
	description=_lt("Value of the deals won from the ads, for each unit spent on them"),
	requires=("meta_ads",),
	scope="site",
	managers_only=True,
	keywords=("roas", "roi"),
)
def meta_roas(ctx: Context):
	now, _currency = spend(ctx)
	before, _currency_before = spend(ctx, True)
	revenue = ad_sales(ctx)[1]
	revenue_before = ad_sales(ctx, True)[1]
	return charts.number(per_unit(revenue, now) or 0, per_unit(revenue_before, before), format="ratio")


@widget(
	"meta_spend_trend",
	category="meta",
	kind="axis",
	title=_lt("Ad spend over time"),
	description=_lt("What the Meta ads cost, day by day"),
	size=(10, 8),
	requires=("meta_ads",),
	scope="site",
	managers_only=True,
)
def meta_spend_trend(ctx: Context):
	query = (
		frappe.qb.from_(Insight)
		.select(Insight.date.as_("day"), Sum(Insight.spend).as_("n"))
		.where(ctx.within_days(Insight.date))
		.groupby(Insight.date)
	)
	values = per_bucket(ctx, {row.day: float(row.n or 0) for row in query.run(as_dict=True)})
	return charts.trend(
		ctx.buckets,
		ctx.grain,
		[charts.series("spend", _("Ad spend"), charts.fill(ctx.buckets, values), type="bar")],
		format="currency",
	)


@widget(
	"meta_ads_table",
	category="meta",
	kind="table",
	title=_lt("Ads that sell"),
	description=_lt("Each ad: what it cost, the people it brought, the deals it won"),
	size=(20, 8),
	requires=("meta_ads",),
	scope="site",
	managers_only=True,
	options=(ROWS,),
)
def meta_ads_table(ctx: Context):
	low, high = ctx.dates()
	ads: dict[str, dict] = {}
	for row in (
		frappe.qb.from_(Insight)
		.select(Insight.ad_id, Insight.ad_name, Insight.campaign_name, Sum(Insight.spend).as_("spend"))
		.where((Insight.date >= low) & (Insight.date <= high))
		.groupby(Insight.ad_id, Insight.ad_name, Insight.campaign_name)
		.run(as_dict=True)
	):
		entry = ads.setdefault(
			row.ad_id, {"ad": row.ad_name or row.ad_id, "spend": 0.0, "leads": 0, "won": 0, "revenue": 0.0}
		)
		entry["spend"] += float(row.spend or 0)
	for ad_id, leads in grouped(
		Lead, Lead.facebook_ad_id, IfNull(Lead.facebook_ad_id, "") != "", ctx.within(Lead.creation)
	):
		ads.setdefault(ad_id, {"ad": ad_id, "spend": 0.0, "leads": 0, "won": 0, "revenue": 0.0})["leads"] = (
			leads
		)
	sales = (
		frappe.qb.from_(Deal)
		.join(Lead)
		.on(Lead.name == Deal.lead)
		.join(Status)
		.on(Status.name == Deal.status)
		.select(
			Lead.facebook_ad_id.as_("ad_id"),
			Count("*").as_("won"),
			Sum(IfNull(Deal.deal_value, 0)).as_("revenue"),
		)
		.where(Status.type == "Won")
		.where(IfNull(Lead.facebook_ad_id, "") != "")
		.where(ctx.within(Lead.creation))
		.groupby(Lead.facebook_ad_id)
	)
	for row in sales.run(as_dict=True):
		entry = ads.setdefault(
			row.ad_id, {"ad": row.ad_id, "spend": 0.0, "leads": 0, "won": 0, "revenue": 0.0}
		)
		entry.update({"won": row.won, "revenue": float(row.revenue or 0)})
	rows = []
	for entry in ads.values():
		rows.append(
			{
				**entry,
				"cost_per_lead": per_unit(entry["spend"], entry["leads"]),
				"roas": per_unit(entry["revenue"], entry["spend"]),
			}
		)
	rows.sort(key=lambda row: (row["spend"], row["leads"]), reverse=True)
	return charts.table(
		[
			{"key": "ad", "label": _("Ad"), "format": "text"},
			{"key": "spend", "label": _("Spend"), "format": "currency"},
			{"key": "leads", "label": _("Leads"), "format": "number"},
			{"key": "cost_per_lead", "label": _("Cost per lead"), "format": "currency"},
			{"key": "won", "label": _("Won"), "format": "number"},
			{"key": "roas", "label": _("Return"), "format": "ratio"},
		],
		rows[: ctx.option("limit", 6)],
		empty=_("No ad ran in this period"),
	)


@widget(
	"meta_conversions_coverage",
	category="meta",
	kind="number",
	title=_lt("Sales reported to Meta"),
	description=_lt(
		"Share of the Meta leads whose outcome was sent back to Meta; below 60% Meta cannot learn from it"
	),
	requires=("meta_conversions",),
	scope="site",
	managers_only=True,
	keywords=("conversions api", "capi", "lead quality"),
)
def meta_conversions_coverage(ctx: Context):
	def rate(previous: bool):
		leads = total(Lead, IfNull(Lead.facebook_lead_id, "") != "", ctx.within(Lead.creation, previous))
		reported = total(
			ConversionEvent,
			ConversionEvent.state == "Sent",
			IfNull(Lead.facebook_lead_id, "") != "",
			ctx.within(Lead.creation, previous),
			distinct=ConversionEvent.lead,
			joins=((Lead, Lead.name == ConversionEvent.lead),),
		)
		return charts.ratio(reported, leads)

	now = rate(False)
	payload = charts.number(now or 0, rate(True), format="percent", compare="points", progress=now or 0)
	payload["settings"] = "Lead quality"
	return payload
