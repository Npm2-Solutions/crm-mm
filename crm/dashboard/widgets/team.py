# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The team, person by person: results in the period, and what is on each plate now.

Managers only. The columns follow the site: the calls column appears where there
is telephony, the appointments column where there is an agenda — a leaderboard
with a column of zeros ranks nobody.
"""

from __future__ import annotations

from collections import defaultdict

import frappe
from frappe import _, _lt
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count, Sum

from crm.dashboard import charts, features
from crm.dashboard.context import Context, where
from crm.dashboard.queries import channels
from crm.dashboard.registry import widget
from crm.dashboard.widgets.sales import amount

Deal = DocType("CRM Deal")
Status = DocType("CRM Deal Status")
Lead = DocType("CRM Lead")
Call = DocType("CRM Call Log")
Task = DocType("CRM Task")
Appt = DocType("CRM Appointment")
Staff = DocType("CRM Appointment Staff")


def add(table: dict, column: str, rows) -> None:
	for user, value in rows:
		if user:
			table[user][column] += float(value or 0)


def by_user(query) -> list[tuple[str, float]]:
	return [(row[0], row[1]) for row in query.run()]


@widget(
	"team_leaderboard",
	category="team",
	kind="table",
	title=_lt("Team results"),
	description=_lt("Each person's deals, wins and activity in the period"),
	size=(20, 8),
	managers_only=True,
	keywords=("leaderboard", "ranking", "performance"),
)
def team_leaderboard(ctx: Context):
	active = features.active()
	table: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

	deals = frappe.qb.from_(Deal).select(Deal.deal_owner, Count("*")).groupby(Deal.deal_owner)
	add(table, "deals", by_user(where(deals, ctx.within(Deal.creation), ctx.owned(Deal.deal_owner))))

	won = (
		frappe.qb.from_(Deal)
		.join(Status)
		.on(Deal.status == Status.name)
		.select(Deal.deal_owner, Count("*"), Sum(amount()))
		.where(Status.type == "Won")
		.groupby(Deal.deal_owner)
	)
	for owner, count, value in where(
		won, ctx.within_days(Deal.closed_date), ctx.owned(Deal.deal_owner)
	).run():
		if owner:
			table[owner]["won"] += float(count or 0)
			table[owner]["won_value"] += float(value or 0)

	columns = [
		{"key": "user", "label": _("Person"), "format": "user"},
		{"key": "deals", "label": _("New deals"), "format": "number"},
		{"key": "won", "label": _("Won"), "format": "number"},
		{"key": "won_value", "label": _("Won revenue"), "format": "currency"},
	]

	if "calls" in active:
		for column, direction in ((Call.caller, "Outgoing"), (Call.receiver, "Incoming")):
			query = (
				frappe.qb.from_(Call).select(column, Count("*")).where(Call.type == direction).groupby(column)
			)
			add(table, "calls", by_user(where(query, ctx.within(Call.creation), ctx.owned(column))))
		columns.append({"key": "calls", "label": _("Calls"), "format": "number"})

	for chan in channels():
		messages = chan.table
		query = frappe.qb.from_(messages).select(messages.owner, Count("*")).groupby(messages.owner)
		query = where(
			query, *chan.base(), chan.is_outgoing(), ctx.within(messages.creation), ctx.owned(messages.owner)
		)
		add(table, "messages", by_user(query))
	columns.append({"key": "messages", "label": _("Messages sent"), "format": "number"})

	if "agenda" in active:
		query = (
			frappe.qb.from_(Staff)
			.join(Appt)
			.on(Staff.parent == Appt.name)
			.select(Staff.user, Count(Appt.name).distinct())
			.where(Staff.parenttype == "CRM Appointment")
			.where(Appt.status == "Completed")
			.groupby(Staff.user)
		)
		add(table, "appointments", by_user(where(query, ctx.within(Appt.starts_on), ctx.owned(Staff.user))))
		columns.append({"key": "appointments", "label": _("Appointments done"), "format": "number"})

	done = (
		frappe.qb.from_(Task)
		.select(Task.assigned_to, Count("*"))
		.where(Task.status == "Done")
		.groupby(Task.assigned_to)
	)
	add(table, "tasks", by_user(where(done, ctx.within(Task.modified), ctx.owned(Task.assigned_to))))
	columns.append({"key": "tasks", "label": _("Tasks done"), "format": "number"})

	rows = [
		{"user": user, **values} for user, values in table.items() if user not in ("Guest", "Administrator")
	]
	rows.sort(key=lambda row: (row.get("won_value", 0), row.get("won", 0), row.get("deals", 0)), reverse=True)
	return charts.table(columns, rows[:20], empty=_("No activity in this period"))


@widget(
	"team_workload",
	category="team",
	kind="table",
	title=_lt("Team workload"),
	description=_lt("What each person has open right now: deals, people waiting, tasks"),
	size=(20, 8),
	live=True,
	managers_only=True,
)
def team_workload(ctx: Context):
	table: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

	open_deals = (
		frappe.qb.from_(Deal)
		.join(Status)
		.on(Deal.status == Status.name)
		.select(Deal.deal_owner, Count("*"))
		.where(Status.type.notin(("Won", "Lost")))
		.groupby(Deal.deal_owner)
	)
	add(table, "deals", by_user(where(open_deals, ctx.owned(Deal.deal_owner))))

	waiting = (
		frappe.qb.from_(Lead)
		.select(Lead.conversation_assigned_to, Lead.lead_owner, Count("*"))
		.where(Lead.conversation_status == "Open")
		.where(Lead.conversation_snoozed_until.isnull())
		.where(Lead.conversation_unread == 1)
		.groupby(Lead.conversation_assigned_to, Lead.lead_owner)
	)
	for assignee, owner, count in waiting.run():
		user = assignee or owner
		if user and (ctx.everyone or user in (ctx.owners or [])):
			table[user]["waiting"] += float(count or 0)

	open_tasks = (
		frappe.qb.from_(Task)
		.select(Task.assigned_to, Count("*"))
		.where(Task.status.isin(("Backlog", "Todo", "In Progress")))
		.groupby(Task.assigned_to)
	)
	add(table, "tasks", by_user(where(open_tasks, ctx.owned(Task.assigned_to))))
	late_tasks = (
		frappe.qb.from_(Task)
		.select(Task.assigned_to, Count("*"))
		.where(Task.status.isin(("Backlog", "Todo", "In Progress")))
		.where(Task.due_date < ctx.now)
		.groupby(Task.assigned_to)
	)
	add(table, "late", by_user(where(late_tasks, ctx.owned(Task.assigned_to))))

	rows = [
		{"user": user, **values} for user, values in table.items() if user not in ("Guest", "Administrator")
	]
	rows.sort(key=lambda row: (row.get("waiting", 0), row.get("late", 0), row.get("deals", 0)), reverse=True)
	return charts.table(
		[
			{"key": "user", "label": _("Person"), "format": "user"},
			{"key": "deals", "label": _("Open deals"), "format": "number"},
			{"key": "waiting", "label": _("People waiting"), "format": "number"},
			{"key": "tasks", "label": _("Open tasks"), "format": "number"},
			{"key": "late", "label": _("Late tasks"), "format": "number"},
		],
		rows[:20],
		empty=_("Nothing open"),
	)
