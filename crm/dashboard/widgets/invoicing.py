# Copyright (c) 2026, NPM2 Solutions Srl and contributors
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
- **"Paid" is ``collected_on``** (``crm.invoicing.incassi``), never ``payment_date``,
  which defaults to the issue date whatever happened. An invoice to a person issued
  at the desk takes the payment date written in it; the rest wait for somebody to
  mark them. What is still to collect is what has no such day, test invoices and
  credit notes left out.
- **Costs are the suppliers' invoices** (``CRM Supplier Invoice``, read out of
  their own XML), with their VAT by default: a medical centre's services are mostly
  exempt, and VAT it cannot take back is a cost. The margin is what was invoiced
  (taxable) less those costs: a reading of the period, not the accountant's books.
- **Amounts are in euro**, like every FatturaPA document the module writes.
- **What is waiting** is what ``crm.invoicing.api.pending_actions`` lists: issued
  documents still to send to the SdI or the Sistema TS, or sent back by either.

Every widget counts the whole practice - an invoice belongs to the business, not to
the salesperson looking - so it is read by whoever reads the economic numbers of
the whole centre (doc 30: the Manager and Accounting).
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
Cycle = DocType("CRM Session Cycle")
Place = DocType("CRM Appointment Participant")

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
COSTS = Option(
	"costs",
	_lt("Costs"),
	choices=(("gross", _lt("With VAT")), ("net", _lt("Without VAT"))),
	default="gross",
)


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


def collectable():
	"""What a client is to pay: issued sales, not a test, not a credit note."""
	return issued() & Invoice.document_type.isin(SALES) & (IfNull(Invoice.test_document, 0) == 0)


def payable():
	"""What the client pays: the document less the withholding the client pays itself."""
	return IfNull(Invoice.net_payable, IfNull(Invoice.grand_total, 0))


def not_disputed():
	return IfNull(Supplier.status, "") != "rifiutata"


def cost(ctx: Context):
	column = Supplier.taxable_amount if ctx.option("costs") == "net" else Supplier.total_amount
	return IfNull(column, 0)


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
	scope="site",
	keywords=("scartate", "notice", "NS"),
)
def sdi_rejected(ctx: Context):
	return charts.number(
		total(Invoice, Invoice.docstatus == 1, Invoice.sdi_status == "scartata"), route=INVOICES
	)


def not_invoiced(ctx: Context):
	"""Appointments that happened lately and have no document (``api.appointments_to_invoice``);
	a session of a cycle paid as a whole is invoiced with its cycle, an appointment
	where everybody uses an entry of their subscription with the instalments."""
	since = add_days(ctx.now, -int(ctx.option("days", 30)))
	invoiced = (
		frappe.qb.from_(Invoice)
		.select(Invoice.appointment)
		.where(Invoice.appointment.isnotnull() & (Invoice.docstatus < 2))
	)
	whole = frappe.qb.from_(Cycle).select(Cycle.name).where(Cycle.billing == "The whole cycle")
	# somebody in it uses an entry of their subscription; somebody else pays
	of_a_subscription = (
		frappe.qb.from_(Place)
		.select(Place.parent)
		.where((Place.parenttype == "CRM Appointment") & (IfNull(Place.subscription, "") != ""))
	)
	paying = (
		frappe.qb.from_(Place)
		.select(Place.parent)
		.where(
			(Place.parenttype == "CRM Appointment")
			& (Place.status != "Cancelled")
			& (IfNull(Place.subscription, "") == "")
		)
	)
	return (
		(Appt.starts_on >= since)
		& (Appt.starts_on <= ctx.now)
		& Appt.status.notin(("Cancelled", "No Show"))
		& Appt.name.notin(invoiced)
		& (Appt.session_cycle.isnull() | Appt.session_cycle.notin(whole))
		& (Appt.name.notin(of_a_subscription) | Appt.name.isin(paying))
	)


@widget(
	"appointments_to_invoice",
	category="invoicing",
	kind="number",
	title=_lt("Appointments to invoice"),
	description=_lt("Appointments that took place and have no invoice yet"),
	live=True,
	requires=FROM_THE_AGENDA,
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
	scope="site",
	options=(COSTS,),
	keywords=("purchases", "costs", "passive", "fornitori"),
)
def supplier_invoices_received(ctx: Context):
	now, before = two_periods_by_day(ctx, Supplier, Supplier.document_date, not_disputed(), value=cost(ctx))
	return charts.number(now, before, format="currency", currency=EURO, negative_is_better=True)


@widget(
	"supplier_invoices_to_register",
	category="invoicing",
	kind="number",
	title=_lt("Supplier invoices to register"),
	description=_lt("Invoices received from suppliers that nobody has registered yet"),
	live=True,
	requires=SUPPLIERS,
	scope="site",
)
def supplier_invoices_to_register(ctx: Context):
	return charts.number(total(Supplier, Supplier.status.isin(("ricevuta", "letta"))))


# -- the centre's economics: collected, to collect, costs, margin, VAT --------------

#: How long an invoice has waited for its money, in the words of a bucket.
AGES = (
	(30, _lt("Up to 30 days")),
	(60, _lt("31 to 60 days")),
	(90, _lt("61 to 90 days")),
	(None, _lt("Over 90 days")),
)


def age_bucket(days: int) -> int:
	"""The index in ``AGES`` of an invoice issued ``days`` ago."""
	for index, (limit, _label) in enumerate(AGES):
		if limit is None or days <= limit:
			return index
	return len(AGES) - 1


def still_to_collect():
	return collectable() & Invoice.collected_on.isnull()


@widget(
	"collected",
	category="invoicing",
	kind="number",
	title=_lt("Collected"),
	description=_lt("The money that reached the centre in the period, by the day it was collected"),
	requires=INVOICING,
	scope="site",
	keywords=("incassato", "cash", "payments", "incassi"),
)
def collected(ctx: Context):
	now, before = two_periods_by_day(ctx, Invoice, Invoice.collected_on, collectable(), value=payable())
	return charts.number(now, before, format="currency", currency=EURO, route=INVOICES)


@widget(
	"to_collect",
	category="invoicing",
	kind="number",
	title=_lt("To collect"),
	description=_lt("What the invoices issued and not collected yet are worth, today"),
	live=True,
	requires=INVOICING,
	scope="site",
	keywords=("da incassare", "outstanding", "receivables", "crediti"),
)
def to_collect(ctx: Context):
	return charts.number(
		total(Invoice, still_to_collect(), value=payable()),
		format="currency",
		currency=EURO,
		route=INVOICES,
	)


def waiting_rows(limit: int | None = None) -> list:
	query = frappe.qb.from_(Invoice).select(
		Invoice.name,
		Invoice.document_number,
		Invoice.posting_date,
		Invoice.billing_name,
		payable().as_("amount"),
	)
	query = where(query, still_to_collect()).orderby(Invoice.posting_date)
	if limit:
		query = query.limit(limit)
	return query.run(as_dict=True)


@widget(
	"to_collect_by_age",
	category="invoicing",
	kind="donut",
	title=_lt("To collect, by how long it waits"),
	description=_lt("The money still to collect, by how many days ago its invoice was issued"),
	size=(6, 8),
	live=True,
	requires=INVOICING,
	scope="site",
	keywords=("aging", "anzianità", "crediti"),
)
def to_collect_by_age(ctx: Context):
	sums = [0.0] * len(AGES)
	today = ctx.today
	for row in waiting_rows():
		days = (today - row.posting_date).days if row.posting_date else 0
		sums[age_bucket(days)] += float(row.amount or 0)
	colors = ("green", "amber", "orange", "red")
	return with_money(
		charts.donut(
			[(str(label), sums[index], colors[index]) for index, (_limit, label) in enumerate(AGES)],
			format="currency",
		)
	)


@widget(
	"to_collect_list",
	category="invoicing",
	kind="list",
	title=_lt("Invoices to collect"),
	description=_lt("The invoices still waiting for their money, the oldest first"),
	size=(10, 8),
	live=True,
	requires=INVOICING,
	scope="site",
	options=(ROWS,),
)
def to_collect_list(ctx: Context):
	today = ctx.today
	items = []
	for row in waiting_rows(ctx.option("limit", 6)):
		days = (today - row.posting_date).days if row.posting_date else 0
		_limit, label = AGES[age_bucket(days)]
		items.append(
			{
				"title": row.billing_name or _("No name"),
				"subtitle": _("No. {0}").format(row.document_number) if row.document_number else row.name,
				"value": float(row.amount or 0),
				"format": "currency",
				"time": str(row.posting_date),
				# a lazy word (`_lt`) says itself in the reader's language only as a
				# string: `_()` gave it back as it was, and JSON could not carry it
				"badge": {
					"label": str(label),
					"color": ("green", "orange", "orange", "red")[age_bucket(days)],
				},
				"icon": "wallet",
				"route": INVOICES,
			}
		)
	return with_money(
		charts.listing(
			items,
			empty=_("Nothing to collect: every invoice has been paid"),
			more={"label": _("Open invoices"), "route": INVOICES},
			total=int(total(Invoice, still_to_collect())),
		)
	)


@widget(
	"costs_by_supplier",
	category="invoicing",
	kind="axis",
	title=_lt("Costs by supplier"),
	description=_lt("Who the centre's money goes to: the suppliers' invoices of the period"),
	size=(10, 8),
	requires=SUPPLIERS,
	scope="site",
	options=(BARS, COSTS),
	keywords=("fornitori", "spese", "purchases"),
)
def costs_by_supplier(ctx: Context):
	key = IfNull(Supplier.supplier_name, Supplier.supplier_tax_id)
	query = frappe.qb.from_(Supplier).select(key.as_("key"), Sum(cost(ctx)).as_("n"))
	query = where(query, not_disputed(), ctx.within_days(Supplier.document_date)).groupby(key)
	query = query.orderby(Sum(cost(ctx)), order=frappe.qb.desc).limit(ctx.option("limit", 8))
	rows = [{"label": row.key or _("A supplier"), "n": float(row.n or 0)} for row in query.run(as_dict=True)]
	return with_money(charts.bars(rows, label_key="label", lines=[("n", _("Costs"))], format="currency"))


def revenue_per_bucket(ctx: Context) -> dict:
	return per_bucket(
		ctx, per_day(ctx, Invoice, Invoice.posting_date, issued(), billed(), value=signed_line_total())
	)


def signed_line_total():
	"""The taxable amount of an invoice, taken back on a credit note."""
	value = IfNull(Invoice.net_total, 0)
	return Case().when(Invoice.document_type.isin(CREDIT_NOTES), -value).else_(value)


@widget(
	"margin",
	category="invoicing",
	kind="number",
	title=_lt("Margin"),
	description=_lt("What was invoiced in the period (taxable) less the suppliers' invoices"),
	requires=SUPPLIERS,
	scope="site",
	options=(COSTS,),
	keywords=("margine", "profit", "utile", "risultato"),
)
def margin(ctx: Context):
	sold, sold_before = two_periods_by_day(
		ctx, Invoice, Invoice.posting_date, issued(), billed(), value=signed_line_total()
	)
	spent, spent_before = two_periods_by_day(
		ctx, Supplier, Supplier.document_date, not_disputed(), value=cost(ctx)
	)
	return charts.number(
		sold - spent,
		sold_before - spent_before,
		format="currency",
		currency=EURO,
		hint=_("A reading of the period, not the accountant's books"),
	)


@widget(
	"margin_trend",
	category="invoicing",
	kind="axis",
	title=_lt("Invoiced, costs and margin"),
	description=_lt("What was invoiced and what the suppliers billed, period by period, and what is left"),
	size=(12, 8),
	requires=SUPPLIERS,
	scope="site",
	options=(COSTS,),
	keywords=("margine", "costi", "andamento"),
)
def margin_trend(ctx: Context):
	sold = charts.fill(ctx.buckets, revenue_per_bucket(ctx))
	spent = charts.fill(
		ctx.buckets,
		per_bucket(ctx, per_day(ctx, Supplier, Supplier.document_date, not_disputed(), value=cost(ctx))),
	)
	return with_money(
		charts.trend(
			ctx.buckets,
			ctx.grain,
			[
				charts.series("invoiced", _("Invoiced"), sold, type="bar"),
				charts.series("costs", _("Costs"), spent, type="bar"),
				charts.series("margin", _("Margin"), [a - b for a, b in zip(sold, spent, strict=True)]),
			],
			format="currency",
		)
	)


@widget(
	"vat_balance",
	category="invoicing",
	kind="number",
	title=_lt("VAT of the period"),
	description=_lt(
		"VAT on the invoices issued less VAT on the suppliers' ones: an indication, the settlement is the accountant's"
	),
	requires=INVOICING,
	scope="site",
	keywords=("iva", "liquidazione", "vat"),
)
def vat_balance(ctx: Context):
	sales_vat = IfNull(Invoice.vat_total, 0)
	signed_vat = Case().when(Invoice.document_type.isin(CREDIT_NOTES), -sales_vat).else_(sales_vat)
	owed, owed_before = two_periods_by_day(
		ctx, Invoice, Invoice.posting_date, issued(), billed(), value=signed_vat
	)
	back, back_before = two_periods_by_day(
		ctx, Supplier, Supplier.document_date, not_disputed(), value=IfNull(Supplier.vat_amount, 0)
	)
	return charts.number(
		owed - back,
		owed_before - back_before,
		format="currency",
		currency=EURO,
		negative_is_better=True,
		hint=_("An indication: the settlement is the accountant's"),
	)
