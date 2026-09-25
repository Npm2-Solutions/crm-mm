# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""The appointments reach each professional's Google Calendar, and only go that way.

Google is the fake from the pure tests, plus the token endpoint; nothing leaves
the machine. Jobs are called directly: `frappe.enqueue` is only recorded.
"""

import datetime
from unittest.mock import patch

import frappe

from crm.integrations.google import api as google_api
from crm.integrations.google import calendar_mirror as M
from crm.integrations.google import oauth
from crm.integrations.google import sync as S
from crm.scheduling.timeutils import to_system_naive
from crm.tests.test_google_calendar_mirror import FakeGoogle
from crm.tests.test_scheduling import SchedulingCase


class Google(FakeGoogle):
	"""The fake Calendar API, answering the token endpoint too."""

	def __init__(self):
		super().__init__()
		self.revoked = False

	def __call__(self, method, url, params=None, json=None, headers=None, data=None):
		if url == oauth.TOKEN_URL:
			if self.revoked:
				return 400, {
					"error": "invalid_grant",
					"error_description": "Token has been expired or revoked.",
				}
			return 200, {"access_token": f"access-{data['refresh_token']}", "expires_in": 3599}
		return super().__call__(method, url, params=params, json=json, headers=headers)

	def only_calendar(self):
		(calendar_id,) = self.calendars
		return calendar_id


class GoogleCalendarCase(SchedulingCase):
	def setUp(self):
		super().setUp()
		settings = frappe.get_doc("Google Settings")
		settings.enable = 1
		settings.client_id = "test-client.apps.googleusercontent.com"
		settings.client_secret = "test-secret"
		settings.save(ignore_permissions=True)

		self.anna = self.make_user("anna_gcal@example.com")
		self.bruno = self.make_user("bruno_gcal@example.com")
		self.make_service("Visita Google", [self.anna, self.bruno])
		self.accounts = []
		self.account = self.connect(self.anna)

		self.google = Google()
		self._http = patch.object(M, "http", self.google)
		self._http.start()
		self._queue = patch("frappe.enqueue")
		self.queued = self._queue.start()

	def tearDown(self):
		self._queue.stop()
		self._http.stop()
		for account in self.accounts:
			S.forget_token(account)
		super().tearDown()

	def connect(self, user):
		doc = frappe.get_doc(
			{
				"doctype": "Google Calendar",
				"calendar_name": f"{user} calendar",
				"user": user,
				"enable": 1,
				"push_to_google_calendar": 1,
				"pull_from_google_calendar": 0,
				"refresh_token": f"refresh-{user}",
			}
		).insert(ignore_permissions=True)
		S.forget_token(doc.name)
		self.accounts.append(doc.name)
		return doc.name

	def book(self, start, staff=None, **kw):
		kw.setdefault("participants", [{"participant_name": "Mario Rossi", "phone": "+39 333 1234567"}])
		return self.make_appointment("Visita Google", start, [self.anna] if staff is None else staff, **kw)

	def events(self, calendar_id=None):
		return self.google.events(calendar_id or self.google.only_calendar())

	def pushes(self):
		return [
			call.kwargs
			for call in self.queued.call_args_list
			if call.args and call.args[0] == "crm.integrations.google.sync.push_appointment"
		]

	def writes(self):
		return [c for c in self.google.calls if c["method"] in ("PUT", "POST", "DELETE")]


class TestFirstSync(GoogleCalendarCase):
	def test_the_appointments_land_in_a_calendar_of_their_own(self):
		tomorrow = self.book(self.tomorrow(10))
		next_week = self.book(self.tomorrow(10) + datetime.timedelta(days=6))
		self.book(self.tomorrow(12), staff=[self.bruno])
		self.book(self.tomorrow(15), status="Cancelled")

		stats = S.sync_user(self.anna)

		self.assertEqual(stats, {"events": 2, "written": 2, "removed": 0})
		calendar_id = self.google.only_calendar()
		self.assertEqual(self.google.calendars[calendar_id]["summary"], S.calendar_title())
		self.assertEqual(frappe.db.get_value("Google Calendar", self.account, "crm_calendar_id"), calendar_id)
		self.assertEqual(set(self.events()), {M.event_id(tomorrow.name), M.event_id(next_week.name)})

		body = self.events()[M.event_id(tomorrow.name)]
		self.assertEqual(body["summary"], tomorrow.title)
		self.assertEqual(body["start"]["dateTime"], M.iso_utc(self.tomorrow(10)))
		self.assertIn("+39 333 1234567", body["description"])
		self.assertIn(f"/crm/calendar?appointment={tomorrow.name}", body["description"])
		self.assertNotIn("attendees", body)

		state = frappe.db.get_value(
			"Google Calendar",
			self.account,
			["crm_synced_events", "crm_last_sync", "crm_sync_error"],
			as_dict=True,
		)
		self.assertEqual(state.crm_synced_events, 2)
		self.assertTrue(state.crm_last_sync)
		self.assertFalse(state.crm_sync_error)

	def test_a_second_sync_writes_nothing(self):
		self.book(self.tomorrow(10))
		S.sync_user(self.anna)
		self.google.calls.clear()
		self.assertEqual(S.sync_user(self.anna)["written"], 0)
		self.assertEqual(self.writes(), [])

	def test_an_appointment_without_professionals_belongs_to_its_author(self):
		frappe.set_user(self.anna)
		mine = self.book(self.tomorrow(9), staff=[], participants=[])
		frappe.set_user("Administrator")
		S.sync_user(self.anna)
		self.assertIn(M.event_id(mine.name), self.events())

	def test_a_calendar_deleted_in_google_is_made_again(self):
		booked = self.book(self.tomorrow(10))
		S.sync_user(self.anna)
		self.google.calendars.clear()
		S.sync_user(self.anna)
		self.assertIn(M.event_id(booked.name), self.events())
		self.assertEqual(
			frappe.db.get_value("Google Calendar", self.account, "crm_calendar_id"),
			self.google.only_calendar(),
		)


class TestPush(GoogleCalendarCase):
	def setUp(self):
		super().setUp()
		self.booked = self.book(self.tomorrow(10))
		S.sync_user(self.anna)
		self.queued.reset_mock()

	def test_a_move_follows_within_the_push(self):
		doc = frappe.get_doc("CRM Appointment", self.booked.name)
		doc.starts_on = to_system_naive(self.tomorrow(14))
		doc.ends_on = to_system_naive(self.tomorrow(15))
		doc.save()
		self.assertEqual(
			self.pushes(),
			[{"queue": "short", "enqueue_after_commit": True, "appointment": doc.name, "users": [self.anna]}],
		)

		S.push_appointment(doc.name, [self.anna])
		self.assertEqual(
			self.events()[M.event_id(doc.name)]["start"]["dateTime"], M.iso_utc(self.tomorrow(14))
		)

	def test_a_cancellation_removes_the_copy(self):
		doc = frappe.get_doc("CRM Appointment", self.booked.name)
		doc.status = "Cancelled"
		doc.save()
		S.push_appointment(doc.name, self.pushes()[0]["users"])
		self.assertEqual(self.events(), {})

	def test_deleting_the_appointment_removes_the_copy(self):
		frappe.delete_doc("CRM Appointment", self.booked.name)
		self.assertEqual(self.pushes()[0]["users"], [self.anna])
		S.push_appointment(self.booked.name, [self.anna])
		self.assertEqual(self.events(), {})

	def test_the_professional_taken_off_loses_the_copy(self):
		self.connect(self.bruno)
		doc = frappe.get_doc("CRM Appointment", self.booked.name)
		doc.set("staff", [{"user": self.bruno}])
		doc.save()
		users = self.pushes()[0]["users"]
		self.assertEqual(users, sorted([self.anna, self.bruno]))

		S.push_appointment(doc.name, users)
		anna_calendar = frappe.db.get_value("Google Calendar", self.account, "crm_calendar_id")
		self.assertEqual(self.events(anna_calendar), {})
		# bruno has no calendar yet: his first sync makes it and brings everything
		self.assertTrue(
			any(
				call.kwargs.get("user") == self.bruno
				for call in self.queued.call_args_list
				if call.args and call.args[0] == "crm.integrations.google.sync.sync_user"
			)
		)

	def test_nothing_is_queued_for_who_has_no_google(self):
		self.book(self.tomorrow(16), staff=[self.bruno])
		self.assertEqual(self.pushes(), [])


class TestConnection(GoogleCalendarCase):
	def test_a_revoked_connection_pauses_the_copy(self):
		self.book(self.tomorrow(10))
		self.google.revoked = True
		self.assertIsNone(S.sync_user(self.anna))
		state = frappe.db.get_value(
			"Google Calendar", self.account, ["push_to_google_calendar", "crm_sync_error"], as_dict=True
		)
		self.assertEqual(state.push_to_google_calendar, 0)
		self.assertIn("Token has been expired or revoked", state.crm_sync_error)

		self.queued.reset_mock()
		self.book(self.tomorrow(12))
		self.assertEqual(self.pushes(), [])

	def test_connecting_switches_the_copy_on_one_way(self):
		carla = self.make_user("carla_gcal@example.com")
		frappe.set_user(carla)
		login = oauth.get_login_url()
		self.assertIn("accounts.google.com", login["login_url"])
		record = frappe.get_doc("Google Calendar", login["calendar"])
		self.accounts.append(record.name)
		# nothing to copy until Google hands over a token
		self.assertEqual(
			(record.enable, record.push_to_google_calendar, record.pull_from_google_calendar), (1, 0, 0)
		)

		oauth.store_tokens(record.name, {"refresh_token": "refresh-carla"})
		record.reload()
		self.assertEqual(
			(record.enable, record.push_to_google_calendar, record.pull_from_google_calendar), (1, 1, 0)
		)
		self.assertEqual(S.account_of(carla), record.name)

	def test_the_settings_screen_sees_how_the_copy_is_doing(self):
		self.book(self.tomorrow(10))
		S.sync_user(self.anna)
		frappe.set_user(self.anna)
		status = google_api.get_status()
		self.assertTrue(status["connected"])
		self.assertEqual(status["sync"]["events"], 1)
		self.assertTrue(status["sync"]["active"])
		self.assertEqual(status["sync"]["error"], "")

	def test_disconnecting_stops_the_copy(self):
		frappe.set_user(self.anna)
		status = google_api.disconnect()
		self.assertFalse(status["connected"])
		self.assertIsNone(S.account_of(self.anna))
		self.assertEqual(frappe.db.get_value("Google Calendar", self.account, "enable"), 0)
