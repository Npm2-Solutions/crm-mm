# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Invoicing: what was billed, what is waiting for a button, what the agenda has not billed.

Offered once the site invoices (``features``): an issuing company set up, or
documents already issued. The documents are ``CRM Invoice`` (``crm.invoicing``):
submitted means issued, and the fiscal date is ``posting_date``.

- **Revenue is the taxable amount** (``net_total``: no VAT, stamp duty or pension
  fund), or the document total when a widget is set to it. Credit notes take their
  amount back; self-invoices and reverse-charge integrations are purchases, not
  sales, and stay out. A document the SdI rejected counts as not issued (Circolare
  13/E del 2018) until it goes out again.
- **Nothing here says "paid".** The module records when a healthcare expense was
  paid, for the Sistema TS, and ``payment_date`` defaults to the issue date: it
  does not record whether a client has settled. An "outstanding" figure would be
  invented, so there is none.
- **Amounts are in euro**, like every FatturaPA document the module writes.
- **What is waiting** is what ``crm.invoicing.api.pending_actions`` lists: issued
  documents still to send to the SdI or the Sistema TS, or sent back by either.

Every widget is for managers, like the Invoices page, and counts the whole
practice: an invoice belongs to the business, not to the salesperson looking.
"""

from __future__ import annotations

import frappe
from frappe import _, _lt
from frappe.query_builder import Case, DocType
from frappe.query_builder.functions import Count, IfNull, Sum
from frappe.utils import add_days

from crm.dashboard import charts
from crm.dashboard.context import Context, where
from crm.dashboard.queries import per_bucket, per_day, total, two_periods_by_day
from crm.dashboard.registry import Option, widget

Invoice = DocType("CRM Invoice")
Item = DocType("CRM Invoice Item")
Supplier = DocType("CRM Supplier Invoice")
Appt = DocType("CRM Appointment")

INVOICING = ("invoicing",)
FROM_THE_AGENDA = ("invoicing", "agenda")
SISTEMA_TS = ("invoicing", "sistema_ts")
SUPPLIERS = ("invoicing", "supplier_invoices")
INVOICES = {"name": "Invoices"}
EURO = "EUR"

# FatturaPA document types (TipoDocumento): the ones that sell, and the ones that
# take a sale back. The rest (TD16-TD23, TD26-TD28) are purchases and self-invoices.
SALES = ("TD01", "TD02", "TD03", "TD05", "TD06", "TD07", "TD09", "TD24", "TD25")
CREDIT_NOTES = ("TD04", "TD08")

SDI_TO_DO = ("da_inviare", "scartata", "errore")
TS_TO_DO = ("da_inviare", "pronto_export", "scartato")

MEASURE = Option(
	"measure",
	_lt("Amount"),
	choices=(("net", _lt("Taxable amount")), ("gross", _lt("Document total"))),
	default="net",
)
ROWS = Option("limit", _lt("Rows"), type="int", default=6, min=3, max=20)
BARS = Option("limit", _lt("Rows"), type="int", default=8, min=3, max=20)
DAYS = Option("days", _lt("Look back (days)"), type="int", default=30, min=7, max=365)


def issued():
	"""Submitted, and not sent back by the SdI."""
	return (Invoice.docstatus == 1) & (IfNull(Invoice.sdi_status, "") != "scartata")


def billed():
	return Invoice.document_type.isin(SALES + CREDIT_NOTES)


def amount(ctx: Context):
	column = Invoice.grand_total if ctx.option("measure") == "gross" else Invoice.net_total
	return IfNull(column, 0)


def signed(ctx: Context):
	"""A credit note takes its amount back."""
	return Case().when(Invoice.document_type.isin(CREDIT_NOTES), -amount(ctx)).else_(amount(ctx))


def signed_line():
	"""A line's taxable amount, taken back when it sits on a credit note."""
	line = IfNull(Item.amount, 0)
	return Case().when(Invoice.document_type.isin(CREDIT_NOTES), -line).else_(line)


def with_money(payload: dict) -> dict:
	payload["currency"] = EURO
	return payload


# -- KPIs -------------------------------------------------------------------


@widget(
	"invoiced_revenue",
	category="invoicing",
	kind="number",
	title=_lt("Invoiced"),
	description=_lt("What the invoices issued in the period are worth, credit notes taken off"),
	requires=INVOICING,
	managers_only=True,
	scope="site",
	options=(MEASURE,),
	keywords=("revenue", "turnover", "billing", "fatturato"),
)
def invoiced_revenue(ctx: Context):
	now, before = two_periods_by_day(
		ctx, Invoice, Invoice.posting_date, issued(), billed(), value=signed(ctx)
	)
	return charts.number(now, before, format="currency", currency=EURO, route=INVOICES)


@widget(
	"invoices_issued",
	category="invoicing",
	kind="number",
	title=_lt("Invoices issued"),
	description=_lt("Invoices issued in the period, credit notes not counted"),
	requires=INVOICING,
	managers_only=True,
	scope="site",
	keywords=("documents", "fatture"),
)
def invoices_issued(ctx: Context):
	now, before = two_periods_by_day(
		ctx, Invoice, Invoice.posting_date, issued(), Invoice.document_type.isin(SALES)
	)
	return charts.number(now, before, route=INVOICES)


@widget(
	"average_invoice",
	category="invoicing",
	kind="number",
	title=_lt("Average invoice"),
	description=_lt("What an invoice issued in the period is worth, on average"),
	requires=INVOICING,
	managers_only=True,
	scope="site",
	options=(MEASURE,),
)
def average_invoice(ctx: Context):
	sales = Invoice.document_type.isin(SALES)
	worth, worth_before = two_periods_by_day(
		ctx, Invoice, Invoice.posting_date, issued(), sales, value=amount(ctx)
	)
	count, count_before = two_periods_by_day(ctx, Invoice, Invoice.posting_date, issued(), sales)
	return charts.number(
		worth / count if count else 0,
		worth_before / count_before if count_before else None,
		format="currency",
		currency=EURO,
	)


@widget(
	"credit_notes",
	category="invoicing",
	kind="number",
	title=_lt("Credit notes"),
	description=_lt("Invoices taken back, in full or in part, in the period"),
	requires=INVOICING,
	managers_only=True,
	scope="site",
)
def credit_notes(ctx: Context):
	now, before = two_periods_by_day(
		ctx, Invoice, Invoice.posting_date, issued(), Invoice.document_type.isin(CREDIT_NOTES)
	)
	return charts.number(now, before, negative_is_better=True, route=INVOICES)


def waiting_for_action():
	return (Invoice.docstatus == 1) & (Invoice.sdi_status.isin(SDI_TO_DO) | Invoice.ts_status.isin(TS_TO_DO))


@widget(
	"invoicing_to_do",
	category="invoicing",
	kind="number",
	title=_lt("Invoicing to do"),
	description=_lt("Invoices waiting to be sent, or sent back by the SdI or the Sistema TS"),
	live=True,
	requires=INVOICING,
	managers_only=True,
	scope="site",
)
def invoicing_to_do(ctx: Context):
	return charts.number(total(Invoice, waiting_for_action()), route=INVOICES)


@widget(
	"sdi_rejected",
	category="invoicing",
	kind="number",
	title=_lt("Rejected by the SdI"),
	description=_lt("To correct and send again within five days, with the same number and date"),
	live=True,
	requires=INVOICING,
	managers_only=True,
	scope="site",
	keywords=("scartate", "notice", "NS"),
)
def sdi_rejected(ctx: Context):
	return charts.number(
		total(Invoice, Invoice.docstatus == 1, Invoice.sdi_status == "scartata"), route=INVOICES
	)


def not_invoiced(ctx: Context):
	"""Appointments that happened lately and have no document (``api.appointments_to_invoice``)."""
	since = add_days(ctx.now, -int(ctx.option("days", 30)))
	invoiced = (
		frappe.qb.from_(Invoice)
		.select(Invoice.appointment)
		.where(Invoice.appointment.isnotnull() & (Invoice.docstatus < 2))
	)
	return (
		(Appt.starts_on >= since)
		& (Appt.starts_on <= ctx.now)
		& Appt.status.notin(("Cancelled", "No Show"))
		& Appt.name.notin(invoiced)
	)


@widget(
	"appointments_to_invoice",
	category="invoicing",
	kind="number",
	title=_lt("Appointments to invoice"),
	description=_lt("Appointments that took place and have no invoice yet"),
	live=True,
	requires=FROM_THE_AGENDA,
	managers_only=True,
	scope="site",
	options=(DAYS,),
	keywords=("unbilled", "da fatturare"),
)
def appointments_to_invoice(ctx: Context):
	return charts.number(total(Appt, not_invoiced(ctx)), route=INVOICES)


# -- charts -----------------------------------------------------------------


@widget(
	"invoiced_trend",
	category="invoicing",
	kind="axis",
	title=_lt("Invoiced over time"),
	description=_lt("What the invoices issued are worth, day by day or month by month"),
	size=(10, 8),
	requires=INVOICING,
	managers_only=True,
	scope="site",
	options=(MEASURE,),
)
def invoiced_trend(ctx: Context):
	values = per_bucket(
		ctx, per_day(ctx, Invoice, Invoice.posting_date, issued(), billed(), value=signed(ctx))
	)
	return with_money(
		charts.trend(
			ctx.buckets,
			ctx.grain,
			[charts.series("invoiced", _("Invoiced"), charts.fill(ctx.buckets, values), type="bar")],
			format="currency",
		)
	)


def lines_by(ctx: Context, key, empty: str) -> list[dict]:
	value = signed_line()
	query = (
		frappe.qb.from_(Item)
		.join(Invoice)
		.on((Item.parent == Invoice.name) & (Item.parenttype == "CRM Invoice"))
		.select(key.as_("key"), Sum(value).as_("n"))
	)
	query = where(query, issued(), billed(), ctx.within_days(Invoice.posting_date)).groupby(key)
	query = query.orderby(Sum(value), order=frappe.qb.desc).limit(ctx.option("limit", 8))
	return [{"label": row.key or empty, "n": float(row.n or 0)} for row in query.run(as_dict=True)]


@widget(
	"invoiced_by_service",
	category="invoicing",
	kind="axis",
	title=_lt("Invoiced by service"),
	description=_lt("Which services bring the money in: taxable amount of the invoice lines"),
	size=(10, 8),
	requires=INVOICING,
	managers_only=True,
	scope="site",
	options=(BARS,),
)
def invoiced_by_service(ctx: Context):
	rows = lines_by(ctx, Item.billable_service, _("Not a listed service"))
	return with_money(charts.bars(rows, label_key="label", lines=[("n", _("Invoiced"))], format="currency"))


@widget(
	"invoiced_by_provider",
	category="invoicing",
	kind="axis",
	title=_lt("Invoiced by provider"),
	description=_lt("Who performed what was invoiced: taxable amount of the invoice lines"),
	size=(10, 8),
	requires=("invoicing", "centre"),
	managers_only=True,
	scope="site",
	options=(BARS,),
	keywords=("professional", "practitioner", "professionista"),
)
def invoiced_by_provider(ctx: Context):
	rows = lines_by(ctx, Item.service_provider, _("No provider"))
	return with_money(charts.bars(rows, label_key="label", lines=[("n", _("Invoiced"))], format="currency"))


@widget(
	"invoiced_by_client",
	category="invoicing",
	kind="axis",
	title=_lt("Top clients by invoiced"),
	description=_lt("The clients the invoices of the period were made out to, largest first"),
	size=(10, 8),
	requires=INVOICING,
	managers_only=True,
	scope="site",
	options=(BARS, MEASURE),
	keywords=("customers", "clienti"),
)
def invoiced_by_client(ctx: Context):
	value = signed(ctx)
	query = frappe.qb.from_(Invoice).select(Invoice.billing_name.as_("key"), Sum(value).as_("n"))
	query = where(query, issued(), billed(), ctx.within_days(Invoice.posting_date)).groupby(
		Invoice.billing_name
	)
	query = query.orderby(Sum(value), order=frappe.qb.desc).limit(ctx.option("limit", 8))
	rows = [{"label": row.key or _("No name"), "n": float(row.n or 0)} for row in query.run(as_dict=True)]
	return with_money(charts.bars(rows, label_key="label", lines=[("n", _("Invoiced"))], format="currency"))


# where the SdI has each invoice, grouped the way somebody acts on them; a failed
# delivery (MC) is still an issued invoice, sitting in the client's reserved area
SDI_OUTCOMES = (
	(("consegnata", "mancata_consegna", "decorrenza_termini", "esito_pa"), _lt("Accepted"), "darkgreen"),
	(("inviato",), _lt("Waiting for the SdI"), "blue"),
	(("da_inviare", "errore"), _lt("To send"), "amber"),
	(("scartata",), _lt("Rejected"), "pink"),
)


@widget(
	"sdi_outcomes",
	category="invoicing",
	kind="donut",
	title=_lt("Invoices at the SdI"),
	description=_lt("Where the invoices of the period stand with the Sistema di Interscambio"),
	size=(10, 8),
	requires=INVOICING,
	managers_only=True,
	scope="site",
)
def sdi_outcomes(ctx: Context):
	query = frappe.qb.from_(Invoice).select(Invoice.sdi_status.as_("status"), Count("*").as_("n"))
	query = where(
		query,
		Invoice.docstatus == 1,
		Invoice.sdi_status.notin(("non_applicabile", "")),
		ctx.within_days(Invoice.posting_date),
	).groupby(Invoice.sdi_status)
	counts = {row.status: float(row.n or 0) for row in query.run(as_dict=True)}
	return charts.donut(
		[
			(str(label), sum(counts.get(status, 0) for status in statuses), color)
			for statuses, label, color in SDI_OUTCOMES
		]
	)


# -- lists ------------------------------------------------------------------


def what_is_waiting(row) -> tuple[str, str]:
	"""The one thing to do on an invoice, the most urgent first (as ``urgency`` sorts)."""
	if row.sdi_status == "scartata":
		return _("Rejected by the SdI"), "red"
	if row.sdi_status == "errore":
		return _("Sending failed"), "red"
	if row.ts_status == "scartato":
		return _("Rejected by the Sistema TS"), "red"
	if row.sdi_status == "da_inviare":
		return _("To send to the SdI"), "orange"
	return _("To report to the Sistema TS"), "orange"


def urgency():
	"""A rejection by the SdI first: five days to send it again, and they run from the notice."""
	return (
		Case()
		.when(Invoice.sdi_status == "scartata", 0)
		.when(Invoice.sdi_status == "errore", 1)
		.when(Invoice.ts_status == "scartato", 2)
		.when(Invoice.sdi_status == "da_inviare", 3)
		.else_(4)
	)


@widget(
	"invoicing_to_do_list",
	category="invoicing",
	kind="list",
	title=_lt("Invoicing to do"),
	description=_lt("Invoices waiting to be sent, and the ones sent back, rejections first"),
	size=(10, 8),
	live=True,
	requires=INVOICING,
	managers_only=True,
	scope="site",
	options=(ROWS,),
)
def invoicing_to_do_list(ctx: Context):
	query = frappe.qb.from_(Invoice).select(
		Invoice.name,
		Invoice.document_number,
		Invoice.posting_date,
		Invoice.billing_name,
		Invoice.grand_total,
		Invoice.sdi_status,
		Invoice.ts_status,
	)
	query = where(query, waiting_for_action()).orderby(urgency()).orderby(Invoice.posting_date)
	items = []
	for row in query.limit(ctx.option("limit", 6)).run(as_dict=True):
		label, color = what_is_waiting(row)
		items.append(
			{
				"title": row.billing_name or _("No name"),
				"subtitle": _("No. {0}").format(row.document_number) if row.document_number else row.name,
				"value": float(row.grand_total or 0),
				"format": "currency",
				"time": str(row.posting_date),
				"badge": {"label": label, "color": color},
				"icon": "receipt-text",
				"route": INVOICES,
			}
		)
	return with_money(
		charts.listing(
			items,
			empty=_("Nothing waiting: every invoice went where it had to"),
			more={"label": _("Open invoices"), "route": INVOICES},
			total=int(total(Invoice, waiting_for_action())),
		)
	)


@widget(
	"appointments_to_invoice_list",
	category="invoicing",
	kind="list",
	title=_lt("Appointments to invoice"),
	description=_lt("Appointments that took place and have no invoice yet, most recent first"),
	size=(10, 8),
	live=True,
	requires=FROM_THE_AGENDA,
	managers_only=True,
	scope="site",
	options=(DAYS, ROWS),
)
def appointments_to_invoice_list(ctx: Context):
	query = frappe.qb.from_(Appt).select(
		Appt.name, Appt.title, Appt.service, Appt.starts_on, Appt.total_amount, Appt.currency
	)
	query = where(query, not_invoiced(ctx)).orderby(Appt.starts_on, order=frappe.qb.desc)
	rows = query.limit(ctx.option("limit", 6)).run(as_dict=True)
	items = []
	for row in rows:
		title = row.title or row.name
		item = {
			"title": title,
			# a booking's title often names the service already
			"subtitle": row.service if row.service and row.service not in title else None,
			"time": str(row.starts_on),
			"icon": "calendar-check",
			"route": INVOICES,
		}
		if row.total_amount:
			item["value"] = float(row.total_amount)
			item["format"] = "currency"
		items.append(item)
	payload = charts.listing(
		items,
		empty=_("Every appointment has its invoice"),
		more={"label": _("Invoice them"), "route": INVOICES},
		total=int(total(Appt, not_invoiced(ctx))),
	)
	currency = next((row.currency for row in rows if row.currency), None)
	if currency:
		payload["currency"] = currency
	return payload


# -- Sistema TS ---------------------------------------------------------------


@widget(
	"ts_to_send",
	category="invoicing",
	kind="number",
	title=_lt("Expenses to report"),
	description=_lt("Healthcare expenses not yet sent to the Sistema TS"),
	live=True,
	requires=SISTEMA_TS,
	managers_only=True,
	scope="site",
	keywords=("tessera sanitaria", "730", "spese sanitarie"),
)
def ts_to_send(ctx: Context):
	return charts.number(
		total(Invoice, Invoice.docstatus == 1, Invoice.ts_status.isin(("da_inviare", "pronto_export"))),
		route=INVOICES,
	)


@widget(
	"ts_rejected",
	category="invoicing",
	kind="number",
	title=_lt("Rejected by the Sistema TS"),
	description=_lt("Healthcare expenses the Sistema TS sent back, to correct and send again"),
	live=True,
	requires=SISTEMA_TS,
	managers_only=True,
	scope="site",
	keywords=("tessera sanitaria", "scartate"),
)
def ts_rejected(ctx: Context):
	return charts.number(
		total(Invoice, Invoice.docstatus == 1, Invoice.ts_status == "scartato"), route=INVOICES
	)


@widget(
	"ts_reported",
	category="invoicing",
	kind="number",
	title=_lt("Reported to the Sistema TS"),
	description=_lt("Healthcare expenses of the period the Sistema TS has accepted"),
	requires=SISTEMA_TS,
	managers_only=True,
	scope="site",
	keywords=("tessera sanitaria", "730", "spese sanitarie"),
)
def ts_reported(ctx: Context):
	now, before = two_periods_by_day(
		ctx, Invoice, Invoice.posting_date, Invoice.docstatus == 1, Invoice.ts_status == "accolto"
	)
	return charts.number(now, before, route=INVOICES)


# -- supplier invoices ----------------------------------------------------------


@widget(
	"supplier_invoices_received",
	category="invoicing",
	kind="number",
	title=_lt("Supplier invoices"),
	description=_lt("What the invoices received from suppliers in the period are worth"),
	requires=SUPPLIERS,
	managers_only=True,
	scope="site",
	keywords=("purchases", "costs", "passive", "fornitori"),
)
def supplier_invoices_received(ctx: Context):
	now, before = two_periods_by_day(
		ctx,
		Supplier,
		Supplier.document_date,
		Supplier.status != "rifiutata",
		value=IfNull(Supplier.total_amount, 0),
	)
	return charts.number(now, before, format="currency", currency=EURO, negative_is_better=True)


@widget(
	"supplier_invoices_to_register",
	category="invoicing",
	kind="number",
	title=_lt("Supplier invoices to register"),
	description=_lt("Invoices received from suppliers that nobody has registered yet"),
	live=True,
	requires=SUPPLIERS,
	managers_only=True,
	scope="site",
)
def supplier_invoices_to_register(ctx: Context):
	return charts.number(total(Supplier, Supplier.status.isin(("ricevuta", "letta"))))
