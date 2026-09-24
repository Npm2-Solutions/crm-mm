# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""External bookings land on the calendar: created, moved, cancelled, never refused."""

import json
from unittest.mock import patch

import frappe

from crm.api import booking_platforms as API
from crm.booking_platforms import sync
from crm.booking_platforms.base import STATUS_CANCELLED, ExternalBooking
from crm.scheduling.timeutils import from_system_naive
from crm.tests.test_scheduling import SchedulingCase


class TestPlatformSync(SchedulingCase):
	def setUp(self):
		super().setUp()
		self.doc = self.make_user("doc.platform@example.com")
		self.service = self.make_service("Platform Visit", [self.doc])
		self.conn = frappe.get_doc(
			{
				"doctype": "CRM Booking Connection",
				"connection_name": "Test Webhook",
				"platform": "Generic webhook (Zapier, Make, n8n)",
				"enabled": 1,
				"import_bookings": 1,
				"default_service": self.service.name,
				"create_leads": 1,
				"mappings": [{"map_type": "Staff", "external_id": "st-1", "staff": self.doc}],
			}
		).insert()
		self._queue = patch("frappe.enqueue")
		self._queue.start()

	def tearDown(self):
		self._queue.stop()
		super().tearDown()

	def post(self, payload):
		return sync.handle_webhook(self.conn.webhook_token, {}, json.dumps(payload).encode())

	def payload(self, **kw):
		start = kw.pop("start", self.tomorrow(10))
		return {
			"id": "ext-1",
			"start": start.isoformat(),
			"end": (start.replace(hour=start.hour + 1)).isoformat(),
			"staff_id": "st-1",
			"customer": {"name": "Paziente Esterno", "email": "esterno@example.com"},
			**kw,
		}

	def appointment(self):
		name = frappe.db.get_value(
			"CRM Appointment", {"booking_connection": self.conn.name, "external_id": "ext-1"}
		)
		return frappe.get_doc("CRM Appointment", name) if name else None

	def test_create_update_cancel(self):
		self.assertEqual(self.post(self.payload())["created"], 1)
		doc = self.appointment()
		self.assertEqual((doc.source, doc.status, doc.staff[0].user), ("External", "Confirmed", self.doc))
		self.assertTrue(doc.participants[0].party)

		self.assertEqual(self.post(self.payload(start=self.tomorrow(14)))["updated"], 1)
		self.assertEqual(from_system_naive(self.appointment().starts_on), self.tomorrow(14))

		self.assertEqual(self.post(self.payload(status="cancelled"))["cancelled"], 1)
		self.assertEqual(self.appointment().status, "Cancelled")

	def test_repeat_is_unchanged(self):
		self.post(self.payload())
		self.assertEqual(self.post(self.payload())["unchanged"], 1)

	def test_clash_is_kept_and_noted(self):
		self.make_appointment(self.service.name, self.tomorrow(10), [self.doc])
		self.assertEqual(self.post(self.payload())["created"], 1)
		self.assertTrue(self.appointment().conflict_note)

	def test_unknown_token_is_refused(self):
		with self.assertRaises(frappe.PermissionError):
			sync.handle_webhook("nope", {}, b"{}")

	def test_cancel_of_unknown_booking_is_skipped(self):
		self.assertEqual(self.post(self.payload(status="cancelled"))["skipped"], 1)

	def test_authoritative_feed_cancels_missing(self):
		self.post(self.payload())
		self.assertEqual(sync._cancel_missing(self.conn, [], self.tomorrow(0), self.tomorrow(23)), 1)
		self.assertEqual(self.appointment().status, "Cancelled")

	def test_busy_feed_hides_everything_but_time(self):
		self.make_appointment(
			self.service.name,
			self.tomorrow(9),
			[self.doc],
			participants=[{"participant_name": "Segreto", "party_type": "CRM Lead"}],
		)
		self.post(self.payload())  # the platform's own booking must not echo back
		frappe.set_user("Guest")
		response = API.busy_feed(
			token=self.conn.webhook_token, key=API.feed_key(self.conn, self.doc), staff=self.doc
		)
		frappe.set_user("Administrator")
		text = response.get_data(as_text=True)
		self.assertEqual(text.count("BEGIN:VEVENT"), 1)
		self.assertNotIn("Segreto", text)
		with self.assertRaises(frappe.PermissionError):
			API.busy_feed(token=self.conn.webhook_token, key="wrong", staff=self.doc)

	def test_email_cancellation_matches_by_client(self):
		conn = frappe.get_doc(
			{
				"doctype": "CRM Booking Connection",
				"connection_name": "Test Mail",
				"platform": "Treatwell / Uala",
				"enabled": 1,
				"import_bookings": 1,
				"default_service": self.service.name,
			}
		).insert()
		booked = ExternalBooking(
			external_id="hash-1",
			start=self.tomorrow(10),
			end=self.tomorrow(11),
			email="cli@example.com",
			customer_name="Cli",
		)
		sync.apply(conn, [booked])
		cancel = ExternalBooking(
			external_id="hash-2",
			start=self.tomorrow(10),
			end=self.tomorrow(11),
			email="cli@example.com",
			status=STATUS_CANCELLED,
			raw={"match_by_customer": True},
		)
		self.assertEqual(sync.apply(conn, [cancel])["cancelled"], 1)
