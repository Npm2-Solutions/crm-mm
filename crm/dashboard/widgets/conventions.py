# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Conventions (doc 61): what the funds still owe the centre.

A fund's invoice is the one that holds its pratiche (`CRM Appointment.fund_invoice`):
issued, not a test, not collected yet. By convention, each bar split by how long
its invoice has waited - the same ages as «To collect, by how long it waits».
"""

from __future__ import annotations

import frappe
from frappe import _lt
from frappe.query_builder import DocType

from crm.dashboard import charts
from crm.dashboard.context import Context, where
from crm.dashboard.registry import widget
from crm.dashboard.widgets.invoicing import (
	AGES,
	INVOICING,
	Invoice,
	age_bucket,
	payable,
	still_to_collect,
	with_money,
)

Appt = DocType("CRM Appointment")
Convention = DocType("CRM Convention")


def owed_by_funds() -> list[dict]:
	"""Every fund's invoice still to collect: its convention, its day, its amount."""
	query = (
		frappe.qb.from_(Invoice)
		.join(Appt)
		.on(Appt.fund_invoice == Invoice.name)
		.join(Convention)
		.on(Convention.name == Appt.convention)
		.select(
			Invoice.name,
			Invoice.posting_date,
			Convention.convention_name.as_("convention"),
			payable().as_("amount"),
		)
		.distinct()
	)
	return where(query, still_to_collect()).run(as_dict=True)


@widget(
	"to_collect_from_funds",
	category="invoicing",
	kind="axis",
	title=_lt("To collect from the funds"),
	description=_lt(
		"What the health funds and insurers still owe for their pratiche, by convention and by how long it waits"
	),
	size=(10, 8),
	live=True,
	requires=INVOICING,
	scope="site",
	keywords=("fondi", "convenzioni", "assicurazioni", "pratiche", "funds", "insurers"),
)
def to_collect_from_funds(ctx: Context):
	per_convenzione: dict[str, list[float]] = {}
	for row in owed_by_funds():
		days = (ctx.today - row.posting_date).days if row.posting_date else 0
		per_convenzione.setdefault(row.convention, [0.0] * len(AGES))[age_bucket(days)] += float(
			row.amount or 0
		)
	rows = [
		{"label": nome, **{f"a{i}": valore for i, valore in enumerate(somme)}}
		for nome, somme in sorted(per_convenzione.items(), key=lambda voce: -sum(voce[1]))
	]
	colors = ("green", "amber", "orange", "red")
	return with_money(
		charts.bars(
			rows,
			label_key="label",
			lines=[(f"a{i}", str(label), colors[i]) for i, (_limit, label) in enumerate(AGES)],
			format="currency",
			stacked=True,
		)
	)
