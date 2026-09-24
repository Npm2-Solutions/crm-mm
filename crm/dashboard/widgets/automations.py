# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Automations: what is running, what it did, and what failed.

Managers only, like the automations page. An enrollment is one person or deal
going through one automation; a step log is one thing an automation did — an
email, a WhatsApp template, a task. Soft skips are logged as successes with a
"Skipped:" note by the engine, so "done" here means "ran".
"""

from __future__ import annotations

from collections import defaultdict

import frappe
from frappe import _, _lt
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count

from crm.dashboard import charts
from crm.dashboard.context import Context, where
from crm.dashboard.queries import per_bucket, per_day, total, two_periods
from crm.dashboard.registry import Option, widget

Automation = DocType("CRM Automation")
Enrollment = DocType("CRM Automation Enrollment")
StepLog = DocType("CRM Automation Step Log")

META = {"requires": ("automations",), "managers_only": True, "scope": "site"}
AUTOMATIONS = {"name": "Automations"}
ROWS = Option("limit", _lt("Rows"), type="int", default=6, min=3, max=20)

RUNNING = ("Active", "Waiting")


def action_labels() -> dict[str, str]:
	return {
		"send_email": _("Emails"),
		"send_sms": _("SMS"),
		"send_whatsapp_template": _("WhatsApp templates"),
		"notify": _("Notifications"),
		"create_task": _("Tasks"),
		"assign": _("Assignments"),
		"add_note": _("Notes"),
		"add_tag": _("Tags added"),
		"add_tag_comment": _("Tags added"),
		"remove_tag": _("Tags removed"),
		"set_field": _("Fields updated"),
		"convert_to_deal": _("Deals opened"),
		"webhook": _("Webhooks"),
		"add_to_workflow": _("Moved to another automation"),
		"remove_from_workflow": _("Removed from an automation"),
	}


def steps(ctx: Context, *criteria, previous: bool = False):
	query = frappe.qb.from_(StepLog).where(StepLog.parenttype == "CRM Automation Enrollment")
	return where(query, ctx.within(StepLog.creation, previous), *criteria)


@widget(
	"automations_active",
	category="automations",
	kind="number",
	title=_lt("Active automations"),
	description=_lt("Automations switched on right now"),
	live=True,
	**META,
)
def automations_active(ctx: Context):
	return charts.number(total(Automation, Automation.enabled == 1), route=AUTOMATIONS)


@widget(
	"automation_enrollments",
	category="automations",
	kind="number",
	title=_lt("People enrolled"),
	description=_lt("People and deals that entered an automation in the period"),
	**META,
)
def automation_enrollments(ctx: Context):
	return charts.number(*two_periods(ctx, Enrollment, Enrollment.creation), route=AUTOMATIONS)


@widget(
	"automation_running",
	category="automations",
	kind="number",
	title=_lt("In progress"),
	description=_lt("Enrollments still running or waiting for their next step"),
	live=True,
	**META,
)
def automation_running(ctx: Context):
	return charts.number(total(Enrollment, Enrollment.status.isin(RUNNING)), route=AUTOMATIONS)


@widget(
	"automation_actions",
	category="automations",
	kind="number",
	title=_lt("Actions done"),
	description=_lt("Emails, messages, tasks and every other step the automations carried out"),
	**META,
)
def automation_actions(ctx: Context):
	def done(previous: bool):
		return float(
			steps(ctx, StepLog.status == "Success", previous=previous).select(Count("*")).run()[0][0] or 0
		)

	return charts.number(done(False), done(True), route=AUTOMATIONS)


@widget(
	"automation_failures",
	category="automations",
	kind="number",
	title=_lt("Failed steps"),
	description=_lt("Steps that raised an error; the error log says why"),
	**META,
)
def automation_failures(ctx: Context):
	def failed(previous: bool):
		return float(
			steps(ctx, StepLog.status == "Failed", previous=previous).select(Count("*")).run()[0][0] or 0
		)

	return charts.number(failed(False), failed(True), negative_is_better=True, route=AUTOMATIONS)


@widget(
	"automation_actions_by_type",
	category="automations",
	kind="axis",
	title=_lt("What the automations did"),
	description=_lt("Steps carried out in the period, by kind"),
	size=(10, 8),
	**META,
)
def automation_actions_by_type(ctx: Context):
	labels = action_labels()
	query = steps(ctx, StepLog.status == "Success", StepLog.action.isin(list(labels))).select(
		StepLog.action, Count("*").as_("n")
	)
	counts: dict[str, float] = defaultdict(float)
	for row in query.groupby(StepLog.action).run(as_dict=True):
		counts[labels.get(row.action, row.action)] += float(row.n or 0)
	rows = sorted(({"action": key, "n": value} for key, value in counts.items()), key=lambda row: -row["n"])
	return charts.bars(rows, label_key="action", lines=[("n", _("Steps"))])


@widget(
	"automation_trend",
	category="automations",
	kind="axis",
	title=_lt("Automation activity"),
	description=_lt("People enrolled and steps carried out, over time"),
	size=(10, 8),
	**META,
)
def automation_trend(ctx: Context):
	enrolled = per_bucket(ctx, per_day(ctx, Enrollment, Enrollment.creation))
	done = per_bucket(
		ctx,
		per_day(
			ctx,
			StepLog,
			StepLog.creation,
			StepLog.parenttype == "CRM Automation Enrollment",
			StepLog.status == "Success",
		),
	)
	return charts.trend(
		ctx.buckets,
		ctx.grain,
		[
			charts.series("enrolled", _("Enrolled"), charts.fill(ctx.buckets, enrolled)),
			charts.series("steps", _("Steps done"), charts.fill(ctx.buckets, done)),
		],
	)


@widget(
	"automation_top",
	category="automations",
	kind="table",
	title=_lt("Busiest automations"),
	description=_lt("Each automation: who entered it in the period and how they left"),
	size=(10, 8),
	options=(ROWS,),
	**META,
)
def automation_top(ctx: Context):
	query = frappe.qb.from_(Enrollment).select(Enrollment.automation, Enrollment.status, Count("*").as_("n"))
	query = where(query, ctx.within(Enrollment.creation)).groupby(Enrollment.automation, Enrollment.status)
	by_automation: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
	for row in query.run(as_dict=True):
		by_automation[row.automation][row.status] += float(row.n or 0)
	rows = []
	for name, counts in by_automation.items():
		entered = sum(counts.values())
		rows.append(
			{
				"automation": name,
				"entered": entered,
				"running": counts["Active"] + counts["Waiting"],
				"completed": counts["Completed"],
				"exited": counts["Exited"] + counts["Failed"],
			}
		)
	rows.sort(key=lambda row: row["entered"], reverse=True)
	return charts.table(
		[
			{"key": "automation", "label": _("Automation"), "format": "text"},
			{"key": "entered", "label": _("Entered"), "format": "number"},
			{"key": "running", "label": _("Running"), "format": "number"},
			{"key": "completed", "label": _("Completed"), "format": "number"},
			{"key": "exited", "label": _("Left early"), "format": "number"},
		],
		rows[: ctx.option("limit", 6)],
		empty=_("Nobody entered an automation in this period"),
	)
