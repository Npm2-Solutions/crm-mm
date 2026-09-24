# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The ready-made dashboards, one per part of the product.

A template is rows of widgets, not positions. It is laid out for the person
looking, with only the widgets their site and their role can answer: an agency
client without telephony gets no calls row, a salesperson gets no ad spend. A
section whose widgets are all missing disappears with its heading, and a row
with some of its widgets missing shares its width among the rest.

The dashboards made from a template follow it until someone rearranges them
(``crm.dashboard.store``): connecting WhatsApp puts the WhatsApp section on the
conversations dashboard the next time it is opened.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from frappe import _lt

from crm.dashboard import layout, registry

KPI = {"h": 3, "min_w": 4}
CHART = {"h": 8, "min_w": 10}
LIST = {"h": 8, "min_w": 6}
WIDE = {"h": 7, "min_w": 20}
TABLE = {"h": 8, "min_w": 20}


@dataclass(frozen=True)
class Line:
	widgets: tuple[str, ...]
	h: int = 3
	min_w: int = 4

	@classmethod
	def of(cls, shape: dict, *widgets: str) -> Line:
		return cls(widgets=widgets, h=shape["h"], min_w=shape["min_w"])


@dataclass(frozen=True)
class Section:
	lines: tuple[Line, ...]
	heading: Any = None


@dataclass(frozen=True)
class Template:
	id: str
	title: Any
	description: Any
	icon: str
	sections: tuple[Section, ...]
	period: str = "last_30_days"
	# every widget counts only the viewer's own work (the personal dashboard)
	only_mine: bool = False
	managers_only: bool = False
	sequence: int = 100

	def widget_ids(self) -> list[str]:
		return [name for section in self.sections for line in section.lines for name in line.widgets]


def section(*lines: Line, heading: Any = None) -> Section:
	return Section(lines=lines, heading=heading)


TEMPLATES: tuple[Template, ...] = (
	Template(
		"overview",
		_lt("Overview"),
		_lt("The day at a glance: sales, people waiting, agenda, calls and marketing"),
		"layout-dashboard",
		sequence=0,
		sections=(
			section(
				Line.of(KPI, "won_value", "won_deals", "deals_new", "win_rate", "pipeline_value"),
				Line.of(
					KPI,
					"conversations_waiting",
					"reply_time",
					"appointments_today",
					"calls_missed",
					"meta_cost_per_customer",
				),
				Line.of(CHART, "sales_trend", "funnel_conversion"),
				Line.of(LIST, "conversations_waiting_list", "appointments_upcoming", "deals_closing_soon"),
				Line.of(LIST, "tasks_due_list", "callbacks_list", "deals_stale"),
			),
		),
	),
	Template(
		"my_day",
		_lt("My day"),
		_lt("Your tasks, your people waiting, your appointments and call backs"),
		"sun",
		period="today",
		only_mine=True,
		sequence=10,
		sections=(
			section(
				Line.of(
					KPI,
					"tasks_due_today",
					"tasks_overdue",
					"conversations_waiting",
					"appointments_today",
					"callbacks_pending",
				),
				Line.of(LIST, "tasks_due_list", "conversations_waiting_list", "my_appointments_today"),
				Line.of(LIST, "callbacks_list", "deals_closing_soon", "deals_stale"),
			),
		),
	),
	Template(
		"sales",
		_lt("Sales"),
		_lt("Deals won and lost, pipeline, forecast and who sells what"),
		"handshake",
		sequence=20,
		sections=(
			section(
				Line.of(KPI, "deals_new", "won_deals", "won_value", "win_rate", "average_won_deal_value"),
				Line.of(
					KPI,
					"deals_open",
					"pipeline_value",
					"weighted_pipeline",
					"average_time_to_close_a_deal",
					"deals_lost",
				),
				Line.of(CHART, "sales_trend", "won_value_trend"),
				Line.of(CHART, "forecasted_revenue", "funnel_conversion"),
				Line.of(CHART, "deals_by_stage", "lost_deal_reasons"),
				Line.of(CHART, "deals_by_source", "deals_by_salesperson"),
				Line.of(LIST, "deals_closing_soon", "deals_stale", "deals_recently_won"),
				Line.of(TABLE, "team_leaderboard"),
			),
		),
	),
	Template(
		"conversations",
		_lt("Conversations"),
		_lt("Who is waiting, how fast the team answers, and every channel"),
		"messages-square",
		sequence=30,
		sections=(
			section(
				Line.of(
					KPI,
					"conversations_waiting",
					"conversations_unassigned",
					"reply_time",
					"messages_received",
					"messages_sent",
				),
				Line.of(CHART, "messages_trend", "reply_time_distribution"),
				Line.of(WIDE, "messages_heatmap"),
				Line.of(CHART, "conversations_waiting_list", "messages_by_channel"),
				Line.of(CHART, "conversations_by_assignee"),
			),
			section(
				Line.of(
					KPI,
					"whatsapp_received",
					"whatsapp_sent",
					"whatsapp_new_conversations",
					"whatsapp_read_rate",
					"whatsapp_failed",
				),
				Line.of(CHART, "whatsapp_trend", "whatsapp_status"),
				Line.of(CHART, "whatsapp_templates", "whatsapp_failed_list"),
				Line.of(KPI, "whatsapp_from_phone"),
				heading=_lt("WhatsApp"),
			),
			section(
				Line.of(KPI, "sms_received", "sms_sent", "sms_failed"),
				Line.of(CHART, "sms_trend"),
				heading=_lt("SMS"),
			),
			section(
				Line.of(KPI, "emails_received", "emails_sent"),
				Line.of(CHART, "emails_trend"),
				heading=_lt("Email"),
			),
		),
	),
	Template(
		"agenda",
		_lt("Agenda"),
		_lt("How full the agenda is, who shows up, what it is worth"),
		"calendar",
		sequence=40,
		sections=(
			section(
				Line.of(
					KPI,
					"appointments_today",
					"appointments_count",
					"appointments_to_confirm",
					"agenda_occupancy",
					"appointments_revenue",
				),
				Line.of(
					KPI,
					"appointments_no_show_rate",
					"appointments_cancellation_rate",
					"new_clients",
					"appointments_no_show_value",
				),
				Line.of(CHART, "appointments_trend", "appointments_by_service"),
				Line.of(CHART, "appointments_upcoming", "appointments_to_confirm_list"),
				Line.of(WIDE, "appointments_heatmap"),
				Line.of(CHART, "appointments_by_source", "appointments_by_staff"),
				Line.of(TABLE, "staff_occupancy"),
			),
			section(
				Line.of(KPI, "online_bookings", "online_booking_share"),
				Line.of(CHART, "online_bookings_trend", "platform_bookings"),
				Line.of(CHART, "platform_connections"),
				heading=_lt("Online booking and platforms"),
			),
		),
	),
	Template(
		"phone",
		_lt("Phone"),
		_lt("Calls in and out, missed calls, call backs and the dialer"),
		"phone",
		sequence=50,
		sections=(
			section(
				Line.of(
					KPI,
					"calls_total",
					"calls_incoming",
					"calls_outgoing",
					"calls_missed",
					"calls_answer_rate",
				),
				Line.of(
					KPI,
					"calls_average_duration",
					"calls_talk_time",
					"callbacks_pending",
					"dialer_calls",
					"dialer_reached_rate",
				),
				Line.of(CHART, "calls_trend", "calls_by_agent"),
				Line.of(WIDE, "calls_heatmap"),
				Line.of(CHART, "callbacks_list", "dialer_outcomes"),
			),
		),
	),
	Template(
		"marketing",
		_lt("Marketing"),
		_lt("Where people come from, the website, and what the ads cost against what they sold"),
		"megaphone",
		sequence=60,
		sections=(
			section(
				Line.of(KPI, "total_leads", "people_with_deal", "web_form_requests"),
				Line.of(CHART, "people_by_channel", "leads_by_source"),
			),
			section(
				Line.of(KPI, "website_visitors", "website_sessions", "visitor_conversion"),
				Line.of(CHART, "visits_trend", "traffic_sources"),
				Line.of(CHART, "top_landing_pages", "top_campaigns"),
				Line.of(CHART, "tracked_links"),
				heading=_lt("Website"),
			),
			section(
				Line.of(
					KPI,
					"meta_leads",
					"meta_spend",
					"meta_cost_per_lead",
					"meta_cost_per_customer",
					"meta_roas",
				),
				Line.of(CHART, "meta_spend_trend", "meta_leads_trend"),
				Line.of(TABLE, "meta_ads_table"),
				Line.of(CHART, "meta_leads_by_form"),
				Line.of(KPI, "meta_conversions_coverage", "meta_sync_errors"),
				heading=_lt("Meta ads"),
			),
		),
	),
	Template(
		"activity",
		_lt("Activity"),
		_lt("Tasks, automations and social posts"),
		"list-checks",
		sequence=70,
		sections=(
			section(
				Line.of(
					KPI, "tasks_open", "tasks_overdue", "tasks_due_today", "tasks_completed", "notes_created"
				),
				Line.of(CHART, "tasks_due_list", "tasks_by_status"),
				Line.of(CHART, "tasks_by_assignee"),
			),
			section(
				Line.of(
					KPI,
					"automations_active",
					"automation_enrollments",
					"automation_running",
					"automation_actions",
					"automation_failures",
				),
				Line.of(CHART, "automation_trend", "automation_actions_by_type"),
				Line.of(TABLE, "automation_top"),
				heading=_lt("Automations"),
			),
			section(
				Line.of(
					KPI, "social_published", "social_scheduled", "social_pending_approval", "social_failed"
				),
				Line.of(LIST, "social_upcoming", "social_failed_list", "social_by_platform"),
				heading=_lt("Social"),
			),
		),
	),
	Template(
		"team",
		_lt("Team"),
		_lt("Results and workload of each person on the team"),
		"users",
		managers_only=True,
		sequence=80,
		sections=(
			section(
				Line.of(TABLE, "team_leaderboard"),
				Line.of(TABLE, "team_workload"),
				Line.of(CHART, "deals_by_salesperson", "conversations_by_assignee"),
				Line.of(CHART, "calls_by_agent", "appointments_by_staff"),
				Line.of(CHART, "tasks_by_assignee"),
			),
		),
	),
)

BY_ID = {template.id: template for template in TEMPLATES}


def get(template_id: str | None) -> Template | None:
	return BY_ID.get(template_id or "")


def build(template: Template, can_show: Callable[[registry.Widget], bool]) -> list[dict[str, Any]]:
	"""The template laid out with the widgets ``can_show`` accepts."""
	lines: list[dict[str, Any]] = []
	for part in template.sections:
		part_lines = []
		for line in part.lines:
			items = []
			for name in line.widgets:
				widget_ = registry.get(name)
				if widget_ and can_show(widget_):
					items.append({"name": name, "type": widget_.kind})
			if items:
				part_lines.append({"items": items, "h": line.h, "min_w": line.min_w})
		if not part_lines:
			continue
		if part.heading:
			lines.append(
				{
					"items": [
						{
							"name": layout.HEADING,
							"type": layout.HEADING,
							"config": {"title": str(part.heading)},
						}
					],
					"h": 1,
					"min_w": layout.GRID_COLUMNS,
				}
			)
		lines += part_lines
	return layout.pack(lines)


def describe(template: Template) -> dict[str, Any]:
	return {
		"id": template.id,
		"title": str(template.title),
		"description": str(template.description),
		"icon": template.icon,
		"period": template.period,
		"only_mine": template.only_mine,
		"managers_only": template.managers_only,
	}
