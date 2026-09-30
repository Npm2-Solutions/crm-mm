# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The clinic's numbers on the dashboard: how many new patients, and what one costs.

Registered by `crm.clinica.registra`, offered where the clinic is on (the "clinic"
feature). A count says nothing about anybody: marketing may see how many became
patients, never who.
"""

from __future__ import annotations

import frappe
from frappe import _lt
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count, IfNull

from crm.dashboard import charts
from crm.dashboard.context import Context, where
from crm.dashboard.queries import two_periods
from crm.dashboard.registry import widget
from crm.dashboard.widgets.marketing import per_unit, spend

Patient = DocType("Clinic Patient")
Lead = DocType("CRM Lead")


@widget(
	"new_patients",
	category="people",
	kind="number",
	title=_lt("New patients"),
	description=_lt("People who became patients in the period, whatever the rule that made them"),
	requires=("clinic",),
	scope="site",
	keywords=("patients", "clinic", "conversion"),
)
def new_patients(ctx: Context):
	now, before = two_periods(ctx, Patient, Patient.patient_since)
	return charts.number(now, before)


def patients_from_ads(ctx: Context, previous: bool = False) -> float:
	"""The people the ads brought who became patients in the period."""
	query = frappe.qb.from_(Patient).join(Lead).on(Lead.name == Patient.lead).select(Count(Patient.name))
	query = where(query, IfNull(Lead.facebook_ad_id, "") != "", ctx.within(Patient.patient_since, previous))
	return float(query.run()[0][0] or 0)


@widget(
	"meta_cost_per_patient",
	category="meta",
	kind="number",
	title=_lt("Cost per new patient"),
	description=_lt("Ad spend divided by the people the ads brought who became patients"),
	requires=("meta_ads", "clinic"),
	scope="site",
	managers_only=True,
	keywords=("cac", "acquisition", "patients"),
)
def meta_cost_per_patient(ctx: Context):
	now, currency = spend(ctx)
	before, _currency = spend(ctx, True)
	return charts.number(
		per_unit(now, patients_from_ads(ctx)) or 0,
		per_unit(before, patients_from_ads(ctx, True)),
		format="currency",
		currency=currency,
		negative_is_better=True,
	)
