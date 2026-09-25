# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""The widget catalogue against a real database.

The first test is the net under all the others: every widget in the catalogue is
asked for its answer, for the whole team and for one salesperson, and must give
back a payload of the kind it promises. A query that only breaks on MariaDB, a
column renamed under a widget, a join that no longer exists — they all fail
here, by name, instead of as a blank tile on somebody's dashboard.
"""

import datetime

import frappe
from frappe.tests import IntegrationTestCase
from frappe.tests.utils import make_test_records
from frappe.utils import add_days, get_first_day, get_last_day, nowdate

from crm.dashboard import registry
from crm.dashboard.context import Context

SALES_USER = "crm.user1@example.com"

#: Features whose data lives in another app entirely. Without that app there is no
#: table to query, and no answer a widget could give.
DOCTYPE_DI_UN_ALTRA_APP = {"whatsapp": "WhatsApp Message"}


class TestDashboardWidgets(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.from_date = get_first_day(nowdate())
		cls.to_date = get_last_day(nowdate())
		for doctype in (
			"CRM Lead Status",
			"CRM Deal Status",
			"CRM Lead Source",
			"CRM Lost Reason",
			"CRM Organization",
			"CRM Lead",
			"CRM Deal",
		):
			make_test_records(doctype)

	@classmethod
	def tearDownClass(cls):
		frappe.db.rollback()
		super().tearDownClass()

	def skip_if_unavailable(self, widget):
		"""Skip only what this site physically cannot answer: a missing app's table.

		A feature merely switched off is **not** a reason to skip. Those widgets query
		doctypes the CRM owns, answer zero, and are exactly the kind of thing this net
		is here to catch. Skipping on `features.missing` alone traded thirty errors for
		two hundred and forty-nine skips, which is not a green suite, it is a quieter
		one.

		What genuinely cannot be asked is a widget whose table belongs to an app that is
		not installed: the WhatsApp widgets read `tabWhatsApp Message`, which ships with
		`frappe_whatsapp`. The skip is loud, and names what is missing.
		"""
		for chiave in widget.requires:
			doctype = DOCTYPE_DI_UN_ALTRA_APP.get(chiave)
			if doctype and not frappe.db.exists("DocType", doctype):
				self.skipTest(f"{widget.id}: {doctype} is not installed on this site")

	def answer(self, widget_id, user=None, config=None, **dates):
		widget = registry.get(widget_id)
		self.assertIsNotNone(widget, widget_id)
		self.skip_if_unavailable(widget)
		ctx = Context.build(
			dates.get("from_date", self.from_date),
			dates.get("to_date", self.to_date),
			requested_user=user,
			scope=widget.scope,
			config=widget.clean_config(config),
		)
		return widget.fn(ctx)

	def test_every_widget_answers_with_its_kind(self):
		for widget in registry.all_widgets():
			for user in (None, SALES_USER):
				with self.subTest(widget=widget.id, user=user):
					data = self.answer(widget.id, user)
					self.assertIsInstance(data, dict)
					self.assertIn(data["kind"], registry.KINDS)
					if not widget.retired:
						self.assertEqual(data["kind"], widget.kind)

	def test_every_widget_survives_an_empty_period(self):
		far = add_days(nowdate(), 3650)
		for widget in registry.all_widgets():
			with self.subTest(widget=widget.id):
				data = self.answer(widget.id, from_date=far, to_date=add_days(far, 30))
				self.assertIn(data["kind"], registry.KINDS)

	def test_catalogue_is_consistent(self):
		for widget in registry.all_widgets():
			with self.subTest(widget=widget.id):
				self.assertIn(widget.category, registry.CATEGORIES)
				self.assertTrue(str(widget.title))
				width, height = widget.size
				self.assertTrue(1 <= width <= 20 and 1 <= height <= 40)


PIPELINE = "Dashboard numbers"
MARCH = ("2025-03-01", "2025-03-31")


class TestSalesNumbers(IntegrationTestCase):
	"""Known deals in a pipeline of their own, and the numbers they must add up to.

	The period is March 2025; the one before it is the 31 days up to 28 February.
	Every widget is asked about this pipeline only, so deals made by other tests
	cannot move the numbers.
	"""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if not frappe.db.exists("CRM Pipeline", PIPELINE):
			frappe.get_doc({"doctype": "CRM Pipeline", "pipeline_name": PIPELINE}).insert(
				ignore_permissions=True
			)
		for stage, kind, probability in (
			("Numbers open", "Open", 20),
			("Numbers won", "Won", 100),
			("Numbers lost", "Lost", 0),
		):
			if not frappe.db.exists("CRM Deal Status", stage):
				frappe.get_doc(
					{
						"doctype": "CRM Deal Status",
						"deal_status": stage,
						"type": kind,
						"pipeline": PIPELINE,
						"probability": probability,
					}
				).insert(ignore_permissions=True)
		if not frappe.db.exists("CRM Lost Reason", "Numbers price"):
			frappe.get_doc({"doctype": "CRM Lost Reason", "lost_reason": "Numbers price"}).insert(
				ignore_permissions=True
			)
		frappe.db.delete("CRM Deal", {"pipeline": PIPELINE})

		cls.deal("Numbers won", 1000, created="2025-02-10", closed="2025-03-05")
		cls.deal("Numbers won", 2000, created="2025-03-02", closed="2025-03-20", owner=SALES_USER)
		cls.deal("Numbers won", 3000, created="2025-03-10", closed="2025-03-31", owner=SALES_USER)
		cls.deal("Numbers won", 500, created="2025-02-01", closed="2025-02-15")
		cls.deal("Numbers lost", 800, created="2025-03-03", lost="2025-03-12")
		cls.deal("Numbers open", 4000, created="2025-03-15", expected=5000)
		cls.deal("Numbers open", 1500, created="2025-01-05")

	@classmethod
	def tearDownClass(cls):
		frappe.db.rollback()
		super().tearDownClass()

	@staticmethod
	def deal(stage, value, *, created, closed=None, lost=None, expected=None, owner="Administrator"):
		doc = frappe.get_doc(
			{
				"doctype": "CRM Deal",
				"status": stage,
				"deal_value": value,
				"expected_deal_value": expected or value,
				"expected_closure_date": closed or created,
				"deal_owner": owner,
				"lost_reason": "Numbers price" if lost else None,
			}
		).insert(ignore_permissions=True)
		# saving stamps today on everything; put the deal back where it belongs in time
		Deal = frappe.qb.DocType("CRM Deal")
		frappe.qb.update(Deal).set(Deal.creation, f"{created} 10:00:00").set(
			Deal.modified, f"{lost or closed or created} 10:00:00"
		).set(Deal.closed_date, closed).where(Deal.name == doc.name).run()
		if lost:
			Log = frappe.qb.DocType("CRM Status Change Log")
			frappe.qb.update(Log).set(Log.from_date, f"{lost} 10:00:00").where(Log.parent == doc.name).where(
				Log.from_type == "Lost"
			).run()

	def answer(self, widget_id, user=None):
		widget = registry.get(widget_id)
		ctx = Context.build(
			*MARCH,
			requested_user=user,
			scope=widget.scope,
			config=widget.clean_config({"pipeline": PIPELINE}),
		)
		return widget.fn(ctx)

	def test_won_lost_and_the_rate_between_them(self):
		won = self.answer("won_deals")
		self.assertEqual((won["value"], won["previous"]), (3, 1))
		lost = self.answer("deals_lost")
		self.assertEqual((lost["value"], lost["previous"]), (1, 0))
		# 3 won of 4 closed, against 1 of 1 before: a fall of 25 points, not of 25%
		rate = self.answer("win_rate")
		self.assertEqual((rate["value"], rate["previous"]), (75, 100))
		self.assertEqual((rate["delta"], rate["deltaUnit"]), (-25, "points"))

	def test_revenue_is_what_was_won_in_the_period(self):
		won = self.answer("won_value")
		self.assertEqual((won["value"], won["previous"]), (6000, 500))
		self.assertEqual(won["delta"], 1100)
		self.assertEqual(self.answer("average_won_deal_value")["value"], 2000)

	def test_new_deals_are_counted_when_they_were_opened(self):
		new = self.answer("deals_new")
		self.assertEqual((new["value"], new["previous"]), (4, 2))

	def test_the_open_pipeline_is_worth_what_is_expected_of_it(self):
		self.assertEqual(self.answer("deals_open")["value"], 2)
		# the expected value when there is one (5000), else the deal value (1500)
		self.assertEqual(self.answer("pipeline_value")["value"], 6500)
		self.assertEqual(self.answer("weighted_pipeline")["value"], 1300)

	def test_one_salesperson_sees_their_own_deals(self):
		self.assertEqual(self.answer("won_deals", user=SALES_USER)["value"], 2)
		self.assertEqual(self.answer("won_value", user=SALES_USER)["value"], 5000)
		self.assertEqual(self.answer("deals_open", user=SALES_USER)["value"], 0)


class TestInvoicingNumbers(IntegrationTestCase):
	"""Documents written straight to the table, and what the invoicing widgets make of them.

	The fiscal engine is ``crm.invoicing``'s to test; here the question is only which
	documents count. March 2025 again, with one sale in February for the comparison.
	Every invoice and appointment on the site is set aside first (rolled back at the
	end), because the widgets about the present count all of them.
	"""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		for doctype in ("CRM Invoice", "CRM Invoice Item", "CRM Appointment"):
			frappe.db.delete(doctype)

		visit, check, physio = "Visita", "Controllo", "Fisioterapia"
		bianchi, neri = "Dott. Bianchi", "Dott. Neri"
		invoice = cls.invoice
		invoice("A", "TD01", "2025-03-05", 1000, 1220, "consegnata", "Rossi", [(visit, bianchi, 1000)])
		invoice("B", "TD01", "2025-03-10", 500, 610, "inviato", "Verdi", [(check, neri, 500)])
		# a credit note takes 200 of the visit back
		invoice("C", "TD04", "2025-03-15", 200, 244, "consegnata", "Rossi", [(visit, bianchi, 200)])
		# rejected: counts as not issued, and is the first thing to do
		invoice("D", "TD01", "2025-03-20", 300, 300, "scartata", "Gialli", [(visit, bianchi, 300)])
		invoice("E", "TD01", "2025-02-10", 800, 976, "consegnata", "Rossi", [(visit, bianchi, 800)])
		invoice(
			"F", "TD01", "2025-03-25", 999, 999, "da_inviare", "Bozza", [(visit, bianchi, 999)], docstatus=0
		)
		invoice(
			"G",
			"TD01",
			"2025-03-28",
			777,
			777,
			"consegnata",
			"Annullata",
			[(visit, bianchi, 777)],
			docstatus=2,
		)
		# a reverse-charge integration is a purchase: at the SdI, but not a sale
		invoice("H", "TD17", "2025-03-12", 400, 488, "consegnata", "Fornitore", [(None, None, 400)])
		# healthcare, outside the SdI, still to be reported to the Sistema TS
		invoice(
			"I",
			"TD01",
			"2025-03-18",
			250,
			250,
			"non_applicabile",
			"Blu",
			[(physio, neri, 250)],
			ts="da_inviare",
		)
		invoice("J", "TD01", "2025-03-22", 150, 183, "da_inviare", "Verdi", [(check, neri, 150)])

		now = frappe.utils.now_datetime()
		cls.appointment("done", now - datetime.timedelta(days=2), "Completed")
		cls.appointment("invoiced", now - datetime.timedelta(days=3), "Completed")
		cls.appointment("cancelled", now - datetime.timedelta(days=2), "Cancelled")
		cls.appointment("long ago", now - datetime.timedelta(days=60), "Completed")
		cls.appointment("tomorrow", now + datetime.timedelta(days=1), "Scheduled")
		invoice("K", "TD01", "2024-12-01", 90, 90, "consegnata", "Viola", [(visit, bianchi, 90)])
		frappe.db.set_value("CRM Invoice", "TEST-DASH-K", "appointment", "TEST-DASH-APPT-invoiced")

	@classmethod
	def tearDownClass(cls):
		frappe.db.rollback()
		super().tearDownClass()

	@staticmethod
	def invoice(key, kind, day, net, gross, sdi, billing, lines, docstatus=1, ts="non_applicabile"):
		name = f"TEST-DASH-{key}"
		frappe.get_doc(
			{
				"doctype": "CRM Invoice",
				"name": name,
				"document_type": kind,
				"posting_date": day,
				"payment_date": day,
				"net_total": net,
				"grand_total": gross,
				"net_payable": gross,
				"sdi_status": sdi,
				"ts_status": ts,
				"channel": "pdf_ts" if ts != "non_applicabile" else "sdi",
				"billing_name": billing,
				"docstatus": docstatus,
			}
		).db_insert()
		for index, (service, provider, amount) in enumerate(lines, start=1):
			frappe.get_doc(
				{
					"doctype": "CRM Invoice Item",
					"name": f"{name}-{index}",
					"parent": name,
					"parenttype": "CRM Invoice",
					"parentfield": "items",
					"idx": index,
					"billable_service": service,
					"service_provider": provider,
					"qty": 1,
					"rate": amount,
					"amount": amount,
				}
			).db_insert()

	@staticmethod
	def appointment(key, starts_on, status):
		frappe.get_doc(
			{
				"doctype": "CRM Appointment",
				"name": f"TEST-DASH-APPT-{key}",
				"title": key,
				"starts_on": starts_on,
				"ends_on": starts_on + datetime.timedelta(hours=1),
				"status": status,
			}
		).db_insert()

	def answer(self, widget_id, **config):
		widget = registry.get(widget_id)
		ctx = Context.build(*MARCH, scope=widget.scope, config=widget.clean_config(config))
		return widget.fn(ctx)

	def test_invoiced_is_sales_less_credit_notes(self):
		# 1000 + 500 + 250 + 150 sold, 200 taken back; the rejected, the draft, the
		# cancelled and the purchase are not revenue
		invoiced = self.answer("invoiced_revenue")
		self.assertEqual((invoiced["value"], invoiced["previous"]), (1700, 800))
		self.assertEqual(invoiced["currency"], "EUR")
		self.assertEqual(
			self.answer("invoiced_revenue", measure="gross")["value"], 1220 + 610 + 250 + 183 - 244
		)

	def test_documents_and_their_average(self):
		issued = self.answer("invoices_issued")
		self.assertEqual((issued["value"], issued["previous"]), (4, 1))
		self.assertEqual(self.answer("average_invoice")["value"], 475)
		notes = self.answer("credit_notes")
		self.assertEqual((notes["value"], notes["previous"]), (1, 0))

	def test_what_is_waiting_puts_the_rejected_first(self):
		self.assertEqual(self.answer("invoicing_to_do")["value"], 3)
		self.assertEqual(self.answer("sdi_rejected")["value"], 1)
		self.assertEqual(self.answer("ts_to_send")["value"], 1)
		waiting = self.answer("invoicing_to_do_list")
		self.assertEqual(waiting["total"], 3)
		# the SdI rejection first (five days to fix it), then what is still to send
		self.assertEqual([item["title"] for item in waiting["items"]], ["Gialli", "Verdi", "Blu"])
		self.assertEqual(waiting["items"][0]["badge"]["color"], "red")

	def test_where_the_invoices_stand_at_the_sdi(self):
		slices = {slice_["label"]: slice_["value"] for slice_ in self.answer("sdi_outcomes")["slices"]}
		# A, C and the integration H accepted; B waiting; J to send; D rejected
		self.assertEqual(slices, {"Accepted": 3, "Waiting for the SdI": 1, "To send": 1, "Rejected": 1})

	def test_lines_by_service_provider_and_client(self):
		def bars(widget_id):
			answer = self.answer(widget_id)
			return dict(zip(answer["x"]["values"], answer["series"][0]["values"], strict=True))

		self.assertEqual(bars("invoiced_by_service"), {"Visita": 800, "Controllo": 650, "Fisioterapia": 250})
		self.assertEqual(bars("invoiced_by_provider"), {"Dott. Neri": 900, "Dott. Bianchi": 800})
		self.assertEqual(bars("invoiced_by_client"), {"Rossi": 800, "Verdi": 650, "Blu": 250})

	def test_appointments_that_happened_and_were_not_invoiced(self):
		self.assertEqual(self.answer("appointments_to_invoice")["value"], 1)
		listed = self.answer("appointments_to_invoice_list")
		self.assertEqual([item["title"] for item in listed["items"]], ["done"])
