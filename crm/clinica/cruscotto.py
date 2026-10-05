# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The clinic's numbers on the dashboard: new patients, and what one costs.

The CRM counts new clients - whoever came or bought, a Pilates class as much as a
visit (`crm.dashboard.widgets.people`). A medical centre counts its patients too:
whoever had a health service, or whose health data it keeps
(`paziente.assicura_paziente`). From `CRM Lead.patient_since`, which the door
writes with the card: how many, never who. Registered when the clinic registers.
"""

from __future__ import annotations

from frappe import _lt
from frappe.query_builder import DocType
from frappe.query_builder.functions import IfNull

from crm.dashboard import charts
from crm.dashboard.context import Context
from crm.dashboard.queries import total, two_periods
from crm.dashboard.registry import widget
from crm.dashboard.widgets.marketing import per_unit, spend

Lead = DocType("CRM Lead")


@widget(
	"new_patients",
	category="people",
	kind="number",
	title=_lt("New patients"),
	description=_lt(
		"People who became patients in the period: a health service, or health data the centre keeps"
	),
	requires=("clinic",),
	scope="site",
	keywords=("first visit", "patients", "conversion"),
)
def new_patients(ctx: Context):
	now, before = two_periods(ctx, Lead, Lead.patient_since)
	return charts.number(now, before)


def ad_patients(ctx: Context, previous: bool = False) -> float:
	"""The people the ads brought who became patients in the period."""
	return total(Lead, IfNull(Lead.facebook_ad_id, "") != "", ctx.within(Lead.patient_since, previous))


@widget(
	"meta_cost_per_patient",
	category="meta",
	kind="number",
	title=_lt("Cost per new patient"),
	description=_lt("Ad spend divided by the people the ads brought who became patients"),
	requires=("meta_ads", "clinic"),
	scope="site",
	keywords=("cac", "acquisition", "patients"),
)
def meta_cost_per_patient(ctx: Context):
	now, currency = spend(ctx)
	before, _currency = spend(ctx, True)
	return charts.number(
		per_unit(now, ad_patients(ctx)) or 0,
		per_unit(before, ad_patients(ctx, True)),
		format="currency",
		currency=currency,
		negative_is_better=True,
	)
