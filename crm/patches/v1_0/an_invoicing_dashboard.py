# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""The invoicing dashboard, on sites that already have the others.

The shared dashboards are made once, the first time a site has none, so a template
added later has to be brought in. Only this one: a template dashboard somebody
deleted on purpose stays deleted. Like the others it stays out of sight until the
site invoices (``crm.dashboard.features``).
"""

from crm.dashboard import store


def execute():
	store.create_template_dashboards(only=("invoicing",))
