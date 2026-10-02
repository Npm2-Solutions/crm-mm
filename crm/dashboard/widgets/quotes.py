# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Quotes: how many are proposed, how many are accepted, which wait for an answer.

The deal says where a sale is; the quote is what the person is asked to accept
(`crm.preventivi`). A centre that works with quotes measures two things: the share
of quotes accepted, and the quotes nobody has answered yet, to call back within two
or three days - the ones left waiting are the sales lost without a "no".

A widget counts only the quotes its viewer reads (`crm.preventivi.api.condizione`):
a dentist's care plan is health data, and a number is no way around that. Whose
work is counted is the author's.
"""

from __future__ import annotations

import frappe
from frappe import _, _lt
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count, IfNull, Sum
from frappe.utils import date_diff, getdate

from crm.dashboard import charts
from crm.dashboard.context import Context, where
from crm.dashboard.registry import Option, widget
from crm.preventivi import regole as R

DOCTYPE = "CRM Quote"
Quote = DocType(DOCTYPE)

#: after this many days without an answer, a quote is called back
RICHIAMA_DOPO = 3

ROWS = Option("limit", _lt("Rows"), type="int", default=6, min=3, max=20)


def leggibili(ctx: Context, *criteria):
	"""The quotes the viewer reads, among the people being counted."""
	from crm.preventivi.api import condizione

	return (condizione(Quote, ctx.viewer), ctx.owned(Quote.practitioner), *criteria)


def _conta(ctx: Context, *criteria) -> int:
	query = where(frappe.qb.from_(Quote).select(Count("*")), *leggibili(ctx, *criteria))
	return int(query.run()[0][0] or 0)


def proposed_in(ctx: Context, previous: bool = False) -> int:
	return _conta(ctx, ctx.within(Quote.proposed_on, previous))


def accepted_in(ctx: Context, previous: bool = False) -> int:
	# completed and closed quotes were accepted first: the moment stays
	return _conta(ctx, ctx.within(Quote.accepted_on, previous))


def declined_in(ctx: Context, previous: bool = False) -> int:
	"""Declined in the period, and not followed by a new version: a quote put right
	after a "no" is the same conversation, still going."""
	versioni = frappe.qb.from_(Quote).select(Quote.replaces).where(IfNull(Quote.replaces, "") != "")
	return _conta(ctx, ctx.within(Quote.declined_on, previous), Quote.name.notin(versioni))


def in_attesa():
	return Quote.status == R.PROPOSTO


def valuta(ctx: Context) -> str:
	"""The currency the quotes are written in: a centre's price lists have one."""
	return (
		frappe.db.get_value(DOCTYPE, {"currency": ("is", "set")}, "currency", order_by="creation desc")
		or ctx.currency
	)


@widget(
	"quotes_proposed",
	category="sales",
	kind="number",
	title=_lt("Quotes proposed"),
	description=_lt("Quotes handed to people in the period"),
	requires=("quotes",),
	keywords=("estimates", "care plans", "proposals"),
)
def quotes_proposed(ctx: Context):
	return charts.number(proposed_in(ctx), proposed_in(ctx, True))


@widget(
	"quotes_acceptance_rate",
	category="sales",
	kind="number",
	title=_lt("Quotes accepted"),
	description=_lt("Of the quotes answered in the period, the share accepted"),
	requires=("quotes",),
	keywords=("acceptance", "case acceptance", "conversion", "estimates"),
)
def quotes_acceptance_rate(ctx: Context):
	accettati, rifiutati = accepted_in(ctx), declined_in(ctx)
	prima_si, prima_no = accepted_in(ctx, True), declined_in(ctx, True)
	quota = charts.ratio(accettati, accettati + rifiutati)
	prima = charts.ratio(prima_si, prima_si + prima_no)
	return charts.number(quota or 0, prima, format="percent", compare="points", progress=quota or 0)


@widget(
	"quotes_waiting_value",
	category="sales",
	kind="number",
	title=_lt("Quotes waiting"),
	description=_lt("What the quotes still waiting for an answer are worth"),
	live=True,
	requires=("quotes",),
	keywords=("pending", "unscheduled", "follow up"),
)
def quotes_waiting_value(ctx: Context):
	query = where(
		frappe.qb.from_(Quote).select(Sum(IfNull(Quote.total_net, 0)), Count("*")),
		*leggibili(ctx, in_attesa()),
	)
	valore, quanti = query.run()[0]
	return charts.number(
		float(valore or 0),
		format="currency",
		currency=valuta(ctx),
		hint=_("Quotes waiting: {0}").format(int(quanti)) if quanti else None,
	)


@widget(
	"quotes_waiting",
	category="sales",
	kind="list",
	title=_lt("Quotes to call back"),
	description=_lt("Quotes proposed and not answered yet, the longest waiting first"),
	size=(10, 8),
	live=True,
	requires=("quotes",),
	options=(ROWS,),
	keywords=("pending", "follow up", "unanswered", "estimates"),
)
def quotes_waiting(ctx: Context):
	query = where(
		frappe.qb.from_(Quote).select(
			Quote.name,
			Quote.lead,
			Quote.lead_name,
			Quote.title,
			Quote.total_net,
			Quote.proposed_on,
			Quote.valid_until,
			Quote.practitioner,
		),
		*leggibili(ctx, in_attesa()),
	)
	righe = query.orderby(Quote.proposed_on).limit(ctx.option("limit", 6)).run(as_dict=True)
	oggi = getdate(ctx.today)
	lista = charts.listing(
		[voce(riga, oggi) for riga in righe],
		empty=_("No quote is waiting for an answer"),
		total=_conta(ctx, in_attesa()),
	)
	lista["currency"] = valuta(ctx)
	return lista


def voce(riga, oggi) -> dict:
	"""One quote waiting: the person, what it is, what it is worth, since when."""
	item = {
		"title": riga.lead_name or riga.lead,
		"subtitle": riga.title or None,
		"value": float(riga.total_net or 0),
		"format": "currency",
		"route": {"name": "Lead", "params": {"leadId": riga.lead}, "hash": "#quotes"},
	}
	if riga.proposed_on:
		item["time"] = str(riga.proposed_on)
	if riga.practitioner:
		item["user"] = riga.practitioner
	if riga.valid_until and getdate(riga.valid_until) < oggi:
		item["badge"] = {"label": _("Expired"), "color": "red"}
	elif riga.proposed_on and date_diff(oggi, getdate(riga.proposed_on)) >= RICHIAMA_DOPO:
		item["badge"] = {"label": _("To call back"), "color": "orange"}
	return item
