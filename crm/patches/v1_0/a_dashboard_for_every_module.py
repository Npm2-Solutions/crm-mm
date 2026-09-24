# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The dashboard grows from one page about deals to one per part of the product.

Until now there was a single shared dashboard, "Manager Dashboard", with the
leads-and-deals widgets the upstream CRM ships. Two things happen here:

- if that dashboard still holds the stock widgets — moved around or not, but
  nothing added and nothing removed — it starts following the "overview"
  template: it now shows what the site actually does today (conversations,
  agenda, calls, ads) and keeps up as features are switched on. A dashboard
  somebody composed by hand keeps its layout, marked as customised, so "reset"
  can take it to the overview whenever they want;
- every other template gets its shared dashboard — sales, conversations,
  agenda, phone, marketing, activity, team, "my day". The ones a site cannot
  answer (an agenda without services) stay out of sight until it can.
"""

import json

import frappe

from crm.dashboard import store
from crm.fcrm.doctype.crm_dashboard.crm_dashboard import default_manager_dashboard_layout


def execute():
	if frappe.db.exists("CRM Dashboard", store.MANAGER_DASHBOARD):
		follow_the_overview_if_untouched()
	store.create_template_dashboards()


def widget_names(value: str | None) -> list[str]:
	try:
		items = json.loads(value or "[]")
	except (TypeError, ValueError):
		return []
	return sorted(item.get("name") or "" for item in items if isinstance(item, dict))


def follow_the_overview_if_untouched() -> None:
	doc = frappe.get_doc("CRM Dashboard", store.MANAGER_DASHBOARD)
	stock = widget_names(default_manager_dashboard_layout())
	untouched = not doc.layout or widget_names(doc.layout) in ([], stock)
	doc.template = "overview"
	doc.sequence = 0
	if untouched:
		doc.layout = "[]"
		doc.customized = 0
		# the name it had described who it was for; the overview names itself
		if doc.title == store.MANAGER_DASHBOARD:
			doc.title = ""
	else:
		doc.customized = 1
	doc.save(ignore_permissions=True)
