# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Tasks and notes: what is due, what is late, what got done.

A task belongs to the person it is assigned to. There is no completion date on
a task, so "done in the period" reads the moment it was last changed while done
— close enough for a dashboard, and stated here so nobody mistakes it for audit.
"""

from __future__ import annotations

import datetime

import frappe
from frappe import _, _lt
from frappe.query_builder import DocType

from crm.dashboard import charts
from crm.dashboard.context import Context, where
from crm.dashboard.queries import grouped, total, two_periods
from crm.dashboard.registry import Option, widget
from crm.dashboard.widgets.conversations import full_names

Task = DocType("CRM Task")
Note = DocType("FCRM Note")

OPEN = ("Backlog", "Todo", "In Progress")
TASKS = {"name": "Tasks"}
ROWS = Option("limit", _lt("Rows"), type="int", default=6, min=3, max=20)
PRIORITY_COLORS = {"High": "red", "Medium": "orange", "Low": "gray"}


def is_open():
	return Task.status.isin(OPEN)


def assigned(ctx: Context):
	return ctx.owned(Task.assigned_to)


def end_of_today(ctx: Context) -> datetime.datetime:
	return datetime.datetime.combine(ctx.today + datetime.timedelta(days=1), datetime.time.min)


@widget(
	"tasks_open",
	category="tasks",
	kind="number",
	title=_lt("Open tasks"),
	description=_lt("Tasks not done or cancelled yet"),
	live=True,
)
def tasks_open(ctx: Context):
	return charts.number(total(Task, is_open(), assigned(ctx)), route=TASKS)


@widget(
	"tasks_overdue",
	category="tasks",
	kind="number",
	title=_lt("Overdue tasks"),
	description=_lt("Open tasks past their due date"),
	live=True,
	keywords=("late",),
)
def tasks_overdue(ctx: Context):
	value = total(Task, is_open(), Task.due_date < ctx.now, assigned(ctx))
	return charts.number(value, negative_is_better=True, route=TASKS)


@widget(
	"tasks_due_today",
	category="tasks",
	kind="number",
	title=_lt("Due today"),
	description=_lt("Open tasks due by the end of today"),
	live=True,
)
def tasks_due_today(ctx: Context):
	start = datetime.datetime.combine(ctx.today, datetime.time.min)
	value = total(
		Task, is_open(), (Task.due_date >= start) & (Task.due_date < end_of_today(ctx)), assigned(ctx)
	)
	return charts.number(value, route=TASKS)


@widget(
	"tasks_completed",
	category="tasks",
	kind="number",
	title=_lt("Tasks done"),
	description=_lt("Tasks marked as done in the period"),
)
def tasks_completed(ctx: Context):
	return charts.number(
		*two_periods(ctx, Task, Task.modified, Task.status == "Done", assigned(ctx)), route=TASKS
	)


@widget(
	"tasks_by_status",
	category="tasks",
	kind="donut",
	title=_lt("Open tasks by status"),
	description=_lt("Backlog, to do and in progress, right now"),
	size=(10, 8),
	live=True,
)
def tasks_by_status(ctx: Context):
	rows = grouped(Task, Task.status, is_open(), assigned(ctx))
	colors = {"Backlog": "amber", "Todo": "blue", "In Progress": "green"}
	return charts.donut([(_(key), value, colors.get(key)) for key, value in rows])


@widget(
	"tasks_by_assignee",
	category="tasks",
	kind="axis",
	title=_lt("Open tasks per person"),
	description=_lt("Who has what on their plate, and how much of it is late"),
	size=(10, 8),
	live=True,
	managers_only=True,
	keywords=("workload",),
)
def tasks_by_assignee(ctx: Context):
	counts: dict[str, dict[str, float]] = {}
	for late, key in ((False, "on_time"), (True, "late")):
		criteria = [is_open(), assigned(ctx)]
		criteria.append(
			Task.due_date < ctx.now if late else (Task.due_date.isnull() | (Task.due_date >= ctx.now))
		)
		for user, value in grouped(Task, Task.assigned_to, *criteria):
			counts.setdefault(user or "", {"on_time": 0, "late": 0})[key] = value
	names = full_names(list(counts))
	rows = sorted(
		({"user": names.get(user) or user or _("Unassigned"), **values} for user, values in counts.items()),
		key=lambda row: row["on_time"] + row["late"],
		reverse=True,
	)[:12]
	return charts.bars(
		rows, label_key="user", lines=[("on_time", _("On time")), ("late", _("Late"))], stacked=True
	)


def task_list(ctx: Context):
	start_of_week_after = end_of_today(ctx) + datetime.timedelta(days=6)
	criteria = (is_open(), Task.due_date.isnotnull(), Task.due_date < start_of_week_after, assigned(ctx))
	query = frappe.qb.from_(Task).select(
		Task.name,
		Task.title,
		Task.priority,
		Task.status,
		Task.due_date,
		Task.assigned_to,
		Task.reference_doctype,
		Task.reference_docname,
	)
	rows = (
		where(query, *criteria)
		.orderby(Task.due_date, order=frappe.qb.asc)
		.limit(ctx.option("limit", 6))
		.run(as_dict=True)
	)
	items = []
	for row in rows:
		late = row.due_date and row.due_date < ctx.now
		item = {
			"title": row.title,
			"subtitle": _(row.status) if row.status else None,
			"time": str(row.due_date) if row.due_date else None,
			"route": record_route(row.reference_doctype, row.reference_docname, "tasks") or TASKS,
		}
		if late:
			item["badge"] = {"label": _("Late"), "color": "red"}
		elif row.priority:
			item["badge"] = {"label": _(row.priority), "color": PRIORITY_COLORS.get(row.priority, "gray")}
		if row.assigned_to:
			item["user"] = row.assigned_to
		items.append(item)
	return charts.listing(
		items,
		empty=_("Nothing due this week"),
		more={"label": _("All tasks"), "route": TASKS},
		total=int(total(Task, *criteria)),
	)


@widget(
	"tasks_due_list",
	category="tasks",
	kind="list",
	title=_lt("Due this week"),
	description=_lt("Open tasks due in the next seven days, late ones first"),
	size=(10, 8),
	live=True,
	options=(ROWS,),
)
def tasks_due_list(ctx: Context):
	return task_list(ctx)


widget(
	"my_tasks",
	category="tasks",
	kind="list",
	title=_lt("My tasks"),
	description=_lt("Your tasks due this week, late ones first"),
	size=(10, 8),
	live=True,
	scope="me",
	options=(ROWS,),
)(task_list)


@widget(
	"notes_created",
	category="tasks",
	kind="number",
	title=_lt("Notes written"),
	description=_lt("Notes added to people and deals in the period"),
)
def notes_created(ctx: Context):
	return charts.number(
		*two_periods(ctx, Note, Note.creation, ctx.owned(Note.owner)), route={"name": "Notes"}
	)


def record_route(doctype: str | None, name: str | None, tab: str | None = None) -> dict | None:
	"""Where a click on something attached to a person or a deal should land."""
	if not name:
		return None
	if doctype == "CRM Deal":
		route = {"name": "Deal", "params": {"dealId": name}}
	elif doctype == "CRM Lead":
		route = {"name": "Lead", "params": {"leadId": name}}
	else:
		return None
	if tab:
		route["hash"] = f"#{tab}"
	return route
