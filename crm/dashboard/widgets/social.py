# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Social planner: what went out on Facebook and Instagram, and what is coming.

Offered once a social profile is connected. A post can go to several profiles
(its targets); a post counts once, a failed target is what needs fixing.
"""

from __future__ import annotations

import frappe
from frappe import _, _lt
from frappe.query_builder import DocType

from crm.dashboard import charts
from crm.dashboard.context import Context, where
from crm.dashboard.queries import grouped, total, two_periods
from crm.dashboard.registry import Option, widget

Post = DocType("CRM Social Post")
Target = DocType("CRM Social Post Target")

META = {"requires": ("social",), "scope": "site"}
PLANNER = {"name": "Social Planner"}
ROWS = Option("limit", _lt("Rows"), type="int", default=6, min=3, max=20)


@widget(
	"social_published",
	category="social",
	kind="number",
	title=_lt("Posts published"),
	description=_lt("Posts that went out in the period"),
	**META,
)
def social_published(ctx: Context):
	return charts.number(
		*two_periods(ctx, Post, Post.published_at, Post.status == "Published"), route=PLANNER
	)


@widget(
	"social_scheduled",
	category="social",
	kind="number",
	title=_lt("Posts scheduled"),
	description=_lt("Posts waiting for their time to go out"),
	live=True,
	**META,
)
def social_scheduled(ctx: Context):
	return charts.number(total(Post, Post.status == "Scheduled", Post.scheduled_at >= ctx.now), route=PLANNER)


@widget(
	"social_pending_approval",
	category="social",
	kind="number",
	title=_lt("Posts to approve"),
	description=_lt("Posts the team proposed that are waiting for a manager"),
	live=True,
	managers_only=True,
	**META,
)
def social_pending_approval(ctx: Context):
	return charts.number(total(Post, Post.status == "Pending Approval"), route=PLANNER)


@widget(
	"social_failed",
	category="social",
	kind="number",
	title=_lt("Posts that failed"),
	description=_lt("Posts that did not go out on at least one profile"),
	**META,
)
def social_failed(ctx: Context):
	return charts.number(
		*two_periods(ctx, Post, Post.scheduled_at, Post.status == "Failed"),
		negative_is_better=True,
		route=PLANNER,
	)


@widget(
	"social_by_platform",
	category="social",
	kind="donut",
	title=_lt("Posts by platform"),
	description=_lt("Where the period's posts were published"),
	size=(10, 8),
	**META,
)
def social_by_platform(ctx: Context):
	rows = grouped(
		Target,
		Target.platform,
		Target.parenttype == "CRM Social Post",
		Target.status == "Published",
		ctx.within(Post.published_at),
		joins=((Post, Target.parent == Post.name),),
	)
	return charts.donut(rows, other_label=_("Other"))


def posts_list(ctx: Context, *criteria, order, empty: str, badge=None):
	query = frappe.qb.from_(Post).select(
		Post.name, Post.content, Post.status, Post.scheduled_at, Post.published_at
	)
	query = where(query, *criteria)
	rows = query.orderby(order[0], order=order[1]).limit(ctx.option("limit", 6)).run(as_dict=True)
	platforms: dict[str, list[str]] = {}
	names = [row.name for row in rows]
	if names:
		for row in (
			frappe.qb.from_(Target)
			.select(Target.parent, Target.platform)
			.where((Target.parenttype == "CRM Social Post") & Target.parent.isin(names))
			.run(as_dict=True)
		):
			platforms.setdefault(row.parent, [])
			if row.platform and row.platform not in platforms[row.parent]:
				platforms[row.parent].append(row.platform)
	items = []
	for row in rows:
		text = frappe.utils.strip_html(row.content or "").strip()
		item = {
			"title": text[:90] or _("Post without text"),
			"subtitle": ", ".join(platforms.get(row.name, [])),
			"time": str(row.scheduled_at or row.published_at or ""),
			"route": PLANNER,
		}
		if badge:
			item["badge"] = badge
		items.append(item)
	return charts.listing(items, empty=empty, more={"label": _("Open the planner"), "route": PLANNER})


@widget(
	"social_upcoming",
	category="social",
	kind="list",
	title=_lt("Next posts"),
	description=_lt("The next posts going out"),
	size=(10, 8),
	live=True,
	options=(ROWS,),
	**META,
)
def social_upcoming(ctx: Context):
	return posts_list(
		ctx,
		Post.status == "Scheduled",
		Post.scheduled_at >= ctx.now,
		order=(Post.scheduled_at, frappe.qb.asc),
		empty=_("Nothing scheduled"),
	)


@widget(
	"social_failed_list",
	category="social",
	kind="list",
	title=_lt("Posts to fix"),
	description=_lt("Posts that did not go out"),
	size=(10, 8),
	options=(ROWS,),
	**META,
)
def social_failed_list(ctx: Context):
	return posts_list(
		ctx,
		Post.status == "Failed",
		ctx.within(Post.scheduled_at),
		order=(Post.scheduled_at, frappe.qb.desc),
		empty=_("Every post went out"),
		badge={"label": _("Failed"), "color": "red"},
	)
