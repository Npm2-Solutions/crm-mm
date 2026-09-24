# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMDashboard(Document):
	pass


def default_manager_dashboard_layout():
	"""
	Returns the default layout for the CRM Manager Dashboard.

	This is the layout the first dashboard shipped with. It is no longer what a
	new site gets — see ``create_default_manager_dashboard`` — but it is how the
	migration recognises a dashboard nobody ever rearranged.
	"""
	return '[{"name":"total_leads","type":"number_chart","tooltip":"Total number of leads","layout":{"x":0,"y":0,"w":4,"h":3,"i":"total_leads"}},{"name":"ongoing_deals","type":"number_chart","tooltip":"Total number of ongoing deals","layout":{"x":8,"y":0,"w":4,"h":3,"i":"ongoing_deals"}},{"name":"won_deals","type":"number_chart","tooltip":"Total number of won deals","layout":{"x":12,"y":0,"w":4,"h":3,"i":"won_deals"}},{"name":"average_won_deal_value","type":"number_chart","tooltip":"Average value of won deals","layout":{"x":16,"y":0,"w":4,"h":3,"i":"average_won_deal_value"}},{"name":"average_deal_value","type":"number_chart","tooltip":"Average deal value of ongoing and won deals","layout":{"x":0,"y":2,"w":4,"h":3,"i":"average_deal_value"}},{"name":"average_time_to_close_a_lead","type":"number_chart","tooltip":"Average time taken to close a lead","layout":{"x":4,"y":0,"w":4,"h":3,"i":"average_time_to_close_a_lead"}},{"name":"average_time_to_close_a_deal","type":"number_chart","layout":{"x":4,"y":2,"w":4,"h":3,"i":"average_time_to_close_a_deal"}},{"name":"spacer","type":"spacer","layout":{"x":8,"y":2,"w":12,"h":3,"i":"spacer"}},{"name":"sales_trend","type":"axis_chart","layout":{"x":0,"y":4,"w":10,"h":9,"i":"sales_trend"}},{"name":"forecasted_revenue","type":"axis_chart","layout":{"x":10,"y":4,"w":10,"h":9,"i":"forecasted_revenue"}},{"name":"funnel_conversion","type":"axis_chart","layout":{"x":0,"y":11,"w":10,"h":9,"i":"funnel_conversion"}},{"name":"deals_by_stage_donut","type":"donut_chart","layout":{"x":10,"y":11,"w":10,"h":9,"i":"deals_by_stage_donut"}},{"name":"lost_deal_reasons","type":"axis_chart","layout":{"x":0,"y":32,"w":20,"h":9,"i":"lost_deal_reasons"}},{"name":"leads_by_source","type":"donut_chart","layout":{"x":0,"y":18,"w":10,"h":9,"i":"leads_by_source"}},{"name":"deals_by_source","type":"donut_chart","layout":{"x":10,"y":18,"w":10,"h":9,"i":"deals_by_source"}},{"name":"deals_by_territory","type":"axis_chart","layout":{"x":0,"y":25,"w":10,"h":9,"i":"deals_by_territory"}},{"name":"deals_by_salesperson","type":"axis_chart","layout":{"x":10,"y":25,"w":10,"h":9,"i":"deals_by_salesperson"}}]'


def create_default_manager_dashboard(force=False):
	"""
	Creates the default CRM Manager Dashboard if it does not exist.

	The dashboard follows the "overview" template: its layout stays empty and is
	built for whoever opens it, from the widgets their site can answer. ``force``
	puts an existing one back on the template.
	"""
	from crm.dashboard import store

	return store.ensure_manager_dashboard(force=force)


def get_permission_query_conditions(user=None):
	"""Private dashboards are their owner's alone; shared ones are everybody's."""
	user = user or frappe.session.user
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return ""
	return f"(`tabCRM Dashboard`.`private` = 0 or `tabCRM Dashboard`.`user` = {frappe.db.escape(user)})"


def has_permission(doc, ptype=None, user=None):
	user = user or frappe.session.user
	if not doc.private or user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return True
	return doc.user == user
