# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""The one-way copy of appointments into Google Calendar — pure, no Frappe, no network.

A small fake of the Google Calendar API stands in for Google: it keeps calendars and
events, soft-deletes like Google does, and can be told to fail.
"""

import datetime
import re
import unittest
from urllib.parse import unquote

from crm.integrations.google import calendar_mirror as M

UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 9, 25, 12, tzinfo=UTC)


def at(days: float, hours: float = 0) -> datetime.datetime:
	return NOW + datetime.timedelta(days=days, hours=hours)


def appointment(name="APPT-00001", start=None, minutes=60, **kw):
	start = start or at(1)
	row = {
		"name": name,
		"title": "Pulizia viso — Mario Rossi",
		"service": "Pulizia viso",
		"status": "Scheduled",
		"starts_on": start,
		"ends_on": start + datetime.timedelta(minutes=minutes),
		"location": "Studio 1",
		"notes": "",
		"customer_notes": "",
		"owner": "segreteria@example.com",
		"staff": [{"user": "anna@example.com", "status": "Assigned"}],
		"participants": [
			{"participant_name": "Mario Rossi", "phone": "+39 333 1234567", "email": "", "status": "Booked"}
		],
	}
	row.update(kw)
	return row


def body_of(row, user="anna@example.com", **kw):
	kw.setdefault("timezone", "Europe/Rome")
	kw.setdefault("link", f"https://crm.example.com/crm/calendar?appointment={row['name']}")
	return M.event_body(row, user=user, **kw)


class FakeGoogle:
	"""Enough of Google Calendar API v3 for the mirror: calendars, events, the bin.

	A deleted event stays in the bin, and its id stays taken. With ``bin_keeps_ids``
	the bin also refuses to give an event back, the strictest Google could be.
	"""

	def __init__(self, page_size=2500, bin_keeps_ids=False):
		self.calendars = {}
		self.calls = []
		self.failures = []
		self.page_size = page_size
		self.bin_keeps_ids = bin_keeps_ids
		self.created = 0

	def fail_next(self, *responses):
		self.failures.extend(responses)

	def add_calendar(self, summary="CRM"):
		self.created += 1
		cid = f"cal{self.created}@group.calendar.google.com"
		self.calendars[cid] = {"summary": summary, "events": {}}
		return cid

	def events(self, cid, live=True):
		return {
			eid: e["body"]
			for eid, e in self.calendars[cid]["events"].items()
			if not live or e["status"] != "cancelled"
		}

	def __call__(self, method, url, params=None, json=None, headers=None, data=None):
		self.calls.append({"method": method, "url": url, "params": dict(params or {}), "json": json})
		if self.failures:
			return self.failures.pop(0)
		parts = [unquote(p) for p in url[len(M.API) :].strip("/").split("/")]
		if parts == ["calendars"] and method == "POST":
			return 200, {"id": self.add_calendar(json["summary"]), "summary": json["summary"]}
		calendar = self.calendars.get(parts[1]) if len(parts) > 1 else None
		if calendar is None:
			return 404, {"error": {"code": 404, "message": "Not Found"}}
		if len(parts) == 2 and method == "GET":
			return 200, {"id": parts[1], "summary": calendar["summary"]}
		store = calendar["events"]
		if len(parts) == 3 and method == "GET":
			return 200, self._list(store, params)
		if len(parts) == 3 and method == "POST":
			self.created += 1
			eid = json.get("id") or f"google{self.created}"
			if eid in store:
				return 409, {"error": {"code": 409, "message": "The requested identifier already exists."}}
			store[eid] = {"body": json, "status": json.get("status", "confirmed")}
			return 200, {**json, "id": eid}
		eid = parts[3]
		if method == "PUT":
			if eid not in store:
				return 404, {"error": {"code": 404, "message": "Not Found"}}
			if self.bin_keeps_ids and store[eid]["status"] == "cancelled":
				return 410, {"error": {"code": 410, "message": "Resource has been deleted"}}
			store[eid] = {"body": json, "status": json.get("status", "confirmed")}
			return 200, json
		if method == "DELETE":
			if eid not in store:
				return 404, {"error": {"code": 404, "message": "Not Found"}}
			if store[eid]["status"] == "cancelled":
				return 410, {"error": {"code": 410, "message": "Resource has been deleted"}}
			store[eid]["status"] = "cancelled"
			return 204, {}
		raise AssertionError(f"unexpected call {method} {url}")

	def _list(self, store, params):
		low = params.get("timeMin")
		high = params.get("timeMax")
		constraints = params["privateExtendedProperty"]
		if isinstance(constraints, str):
			constraints = [constraints]
		wanted = dict(c.partition("=")[::2] for c in constraints)
		items = []
		for eid, event in sorted(store.items()):
			body = event["body"]
			private = body.get("extendedProperties", {}).get("private", {})
			start = body["start"]["dateTime"].replace("Z", "+00:00")
			end = body["end"]["dateTime"].replace("Z", "+00:00")
			if event["status"] == "cancelled" or any(private.get(k) != v for k, v in wanted.items()):
				continue
			if low and datetime.datetime.fromisoformat(end) <= _parse(low):
				continue
			if high and datetime.datetime.fromisoformat(start) >= _parse(high):
				continue
			items.append({"id": eid, "extendedProperties": {"private": private}})
		offset = int(params.get("pageToken") or 0)
		page = {"items": items[offset : offset + self.page_size]}
		if offset + self.page_size < len(items):
			page["nextPageToken"] = str(offset + self.page_size)
		return page


def _parse(value):
	return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))


class Tokens:
	"""The token provider: counts how often a fresh token was asked for."""

	def __init__(self):
		self.refreshed = 0

	def __call__(self, refresh=False):
		if refresh:
			self.refreshed += 1
		return f"token-{self.refreshed}"


def client_for(google, **kw):
	kw.setdefault("sleep", lambda seconds: None)
	return M.CalendarClient(Tokens(), transport=google, **kw)


# --------------------------------------------------------------------------
# what goes to Google
# --------------------------------------------------------------------------


class TestEventId(unittest.TestCase):
	def test_is_stable_and_valid_for_google(self):
		eid = M.event_id("APPT-00001")
		self.assertEqual(eid, M.event_id("APPT-00001"))
		self.assertNotEqual(eid, M.event_id("APPT-00002"))
		# base32hex: digits and a to v only, 5 to 1024 characters
		self.assertRegex(eid, r"^[0-9a-v]{5,1024}$")


class TestWhoGetsACopy(unittest.TestCase):
	def test_every_professional_except_who_declined(self):
		staff = [
			{"user": "anna@example.com", "status": "Assigned"},
			{"user": "bruno@example.com", "status": "Declined"},
			{"user": "carla@example.com", "status": "Confirmed"},
			{"user": "anna@example.com", "status": "Assigned"},
		]
		self.assertEqual(
			M.mirror_users(staff, "segreteria@example.com"), ["anna@example.com", "carla@example.com"]
		)

	def test_nobody_on_it_means_whoever_booked_it(self):
		self.assertEqual(M.mirror_users([], "segreteria@example.com"), ["segreteria@example.com"])
		self.assertEqual(
			M.mirror_users([{"user": None}], "segreteria@example.com"), ["segreteria@example.com"]
		)

	def test_a_booking_made_online_has_no_owner_to_fall_back_on(self):
		self.assertEqual(M.mirror_users([], "Guest"), [])

	def test_all_declined_is_nobody(self):
		self.assertEqual(
			M.mirror_users([{"user": "anna@example.com", "status": "Declined"}], "x@example.com"), []
		)


class TestEventBody(unittest.TestCase):
	def test_times_are_utc_with_the_practice_timezone(self):
		body = body_of(appointment(start=datetime.datetime(2026, 10, 1, 8, 30, tzinfo=UTC)))
		self.assertEqual(body["start"], {"dateTime": "2026-10-01T08:30:00Z", "timeZone": "Europe/Rome"})
		self.assertEqual(body["end"], {"dateTime": "2026-10-01T09:30:00Z", "timeZone": "Europe/Rome"})

	def test_summary_falls_back_from_title_to_service_to_name(self):
		self.assertEqual(body_of(appointment())["summary"], "Pulizia viso — Mario Rossi")
		self.assertEqual(body_of(appointment(title=""))["summary"], "Pulizia viso")
		self.assertEqual(body_of(appointment(title="", service=""))["summary"], "APPT-00001")

	def test_nobody_is_invited(self):
		body = body_of(
			appointment(participants=[{"participant_name": "Mario", "email": "mario@example.com"}])
		)
		self.assertNotIn("attendees", body)
		self.assertIn("mario@example.com", body["description"])

	def test_it_is_stamped_as_the_crm_s_own(self):
		private = body_of(appointment())["extendedProperties"]["private"]
		self.assertEqual(private[M.MARKER], "1")
		self.assertEqual(private[M.APPOINTMENT_KEY], "APPT-00001")
		self.assertRegex(private[M.HASH_KEY], r"^[0-9a-f]{20}$")

	def test_the_fingerprint_follows_the_content(self):
		first = M.stamp(body_of(appointment()))
		self.assertEqual(first, M.stamp(body_of(appointment())))
		self.assertNotEqual(first, M.stamp(body_of(appointment(start=at(2)))))
		self.assertNotEqual(first, M.stamp(body_of(appointment(location="Studio 2"))))
		self.assertEqual(first, M.body_hash(body_of(appointment())))

	def test_links_back_to_the_crm(self):
		body = body_of(appointment(), source="Studio Bianchi")
		self.assertEqual(
			body["source"],
			{"title": "Studio Bianchi", "url": "https://crm.example.com/crm/calendar?appointment=APPT-00001"},
		)
		self.assertNotIn("source", body_of(appointment(), link=""))


class TestDescription(unittest.TestCase):
	def test_clients_colleagues_notes_and_link(self):
		row = appointment(
			staff=[
				{"user": "anna@example.com", "status": "Assigned"},
				{"user": "bruno@example.com", "status": "Assigned"},
				{"user": "carla@example.com", "status": "Declined"},
			],
			participants=[
				{"participant_name": "Mario Rossi", "phone": "+39 333 1234567", "email": "m@example.com"},
				{"participant_name": "Luca Verdi", "phone": "", "email": ""},
				{"participant_name": "Chi ha disdetto", "phone": "1", "status": "Cancelled"},
			],
			notes="Portare le analisi",
			customer_notes="Allergia al lattice",
		)
		text = M.describe(
			row,
			"anna@example.com",
			names={"bruno@example.com": "Bruno Neri"},
			labels={"with": "Con", "client_notes": "Note del cliente"},
			link="https://crm.example.com/x",
		)
		self.assertEqual(
			text,
			"Mario Rossi · +39 333 1234567 · m@example.com\n"
			"Luca Verdi\n"
			"Con: Bruno Neri\n\n"
			"Portare le analisi\n\n"
			"Note del cliente: Allergia al lattice\n\n"
			"https://crm.example.com/x",
		)

	def test_nothing_to_say_is_an_empty_description(self):
		row = appointment(participants=[], notes=" ", customer_notes=None)
		self.assertEqual(M.describe(row, "anna@example.com"), "")


# --------------------------------------------------------------------------
# what a reconcile does
# --------------------------------------------------------------------------


class TestPlan(unittest.TestCase):
	def found(self, **events):
		"""event id → (appointment, fingerprint)"""
		return {eid: {"appointment": a, "hash": h} for eid, (a, h) in events.items()}

	def test_writes_what_changed_and_removes_what_is_gone(self):
		same, moved, new = (body_of(appointment(n, start=at(i + 1))) for i, n in enumerate("ABC"))
		desired = {"A": same, "B": moved, "C": new}
		found = {
			M.event_id("A"): {"appointment": "A", "hash": M.stamp(same)},
			M.event_id("B"): {"appointment": "B", "hash": "an older fingerprint"},
			M.event_id("GONE"): {"appointment": "GONE", "hash": "whatever"},
		}
		to_write, to_remove = M.plan(desired, found, NOW)
		self.assertEqual(to_write, [("B", M.event_id("B")), ("C", None)])
		self.assertEqual(to_remove, [M.event_id("GONE")])

	def test_an_event_is_matched_by_its_appointment_not_its_id(self):
		body = body_of(appointment("A"))
		found = {"googlesown1": {"appointment": "A", "hash": M.stamp(body)}}
		self.assertEqual(M.plan({"A": body}, found, NOW), ([], []))

	def test_one_event_per_appointment_the_chosen_id_first(self):
		body = body_of(appointment("A"))
		found = {
			"googlesown1": {"appointment": "A", "hash": M.stamp(body)},
			M.event_id("A"): {"appointment": "A", "hash": "an older fingerprint"},
		}
		to_write, to_remove = M.plan({"A": body}, found, NOW)
		self.assertEqual(to_write, [("A", M.event_id("A"))])
		self.assertEqual(to_remove, ["googlesown1"])

	def test_upcoming_first_nearest_first_then_the_past_latest_first(self):
		desired = {
			"last_week": body_of(appointment("A", start=at(-7))),
			"next_month": body_of(appointment("B", start=at(30))),
			"yesterday": body_of(appointment("C", start=at(-1))),
			"tomorrow": body_of(appointment("D", start=at(1))),
		}
		to_write, _ = M.plan(desired, {}, NOW)
		self.assertEqual([name for name, _ in to_write], ["tomorrow", "next_month", "yesterday", "last_week"])


class TestReconcile(unittest.TestCase):
	def setUp(self):
		self.google = FakeGoogle()
		self.cal = self.google.add_calendar()
		self.client = client_for(self.google)
		self.window = (at(-14), at(180))

	def run_reconcile(self, rows):
		desired = {r["name"]: body_of(r) for r in rows}
		return M.reconcile(self.client, self.cal, desired, *self.window, now=NOW)

	def writes(self):
		return [c for c in self.google.calls if c["method"] in ("PUT", "POST", "DELETE")]

	def test_first_sync_writes_everything_then_nothing(self):
		rows = [appointment("APPT-1", start=at(1)), appointment("APPT-2", start=at(3))]
		self.assertEqual(self.run_reconcile(rows), {"events": 2, "written": 2, "removed": 0})
		self.assertEqual(set(self.google.events(self.cal)), {M.event_id("APPT-1"), M.event_id("APPT-2")})
		self.google.calls.clear()
		self.assertEqual(self.run_reconcile(rows), {"events": 2, "written": 0, "removed": 0})
		self.assertEqual(self.writes(), [])

	def test_a_moved_appointment_is_rewritten_and_a_cancelled_one_removed(self):
		self.run_reconcile([appointment("APPT-1", start=at(1)), appointment("APPT-2", start=at(3))])
		stats = self.run_reconcile([appointment("APPT-1", start=at(2))])
		self.assertEqual(stats, {"events": 1, "written": 1, "removed": 1})
		live = self.google.events(self.cal)
		self.assertEqual(list(live), [M.event_id("APPT-1")])
		self.assertEqual(live[M.event_id("APPT-1")]["start"]["dateTime"], M.iso_utc(at(2)))

	def test_an_event_deleted_in_google_comes_back(self):
		self.run_reconcile([appointment("APPT-1")])
		self.client.delete(self.cal, M.event_id("APPT-1"))
		self.assertEqual(self.google.events(self.cal), {})
		self.assertEqual(self.run_reconcile([appointment("APPT-1")])["written"], 1)
		self.assertIn(M.event_id("APPT-1"), self.google.events(self.cal))

	def test_it_comes_back_even_when_google_keeps_its_id_in_the_bin(self):
		self.google.bin_keeps_ids = True
		self.run_reconcile([appointment("APPT-1")])
		self.client.delete(self.cal, M.event_id("APPT-1"))
		self.run_reconcile([appointment("APPT-1")])
		(eid,) = self.google.events(self.cal)
		self.assertNotEqual(eid, M.event_id("APPT-1"))
		# and from then on it is that event that is kept up to date, not a new one each time
		self.google.calls.clear()
		self.assertEqual(self.run_reconcile([appointment("APPT-1")])["written"], 0)
		self.run_reconcile([appointment("APPT-1", start=at(2))])
		self.assertEqual(list(self.google.events(self.cal)), [eid])
		self.assertEqual(self.google.events(self.cal)[eid]["start"]["dateTime"], M.iso_utc(at(2)))

	def test_what_the_professional_added_by_hand_is_left_alone(self):
		self.google.calendars[self.cal]["events"]["mine1"] = {
			"body": {
				"summary": "Palestra",
				"start": {"dateTime": M.iso_utc(at(1))},
				"end": {"dateTime": M.iso_utc(at(1, 1))},
			},
			"status": "confirmed",
		}
		self.run_reconcile([])
		self.assertIn("mine1", self.google.events(self.cal))

	def test_outside_the_window_is_not_touched(self):
		far = appointment("APPT-FAR", start=at(400))
		self.client.save(self.cal, "APPT-FAR", body_of(far))
		self.run_reconcile([])
		self.assertIn(M.event_id("APPT-FAR"), self.google.events(self.cal))

	def test_follows_the_pages(self):
		self.google.page_size = 2
		rows = [appointment(f"APPT-{i}", start=at(i + 1)) for i in range(5)]
		self.run_reconcile(rows)
		self.google.calls.clear()
		self.assertEqual(self.run_reconcile(rows)["written"], 0)
		self.assertEqual(len([c for c in self.google.calls if c["method"] == "GET"]), 3)

	def test_a_calendar_deleted_in_google_is_reported(self):
		del self.google.calendars[self.cal]
		with self.assertRaises(M.CalendarMissing):
			self.run_reconcile([appointment()])


# --------------------------------------------------------------------------
# the client
# --------------------------------------------------------------------------


class TestClient(unittest.TestCase):
	def setUp(self):
		self.google = FakeGoogle()
		self.cal = self.google.add_calendar()

	def test_create_and_find_a_calendar(self):
		client = client_for(self.google)
		cid = client.create_calendar("Studio Bianchi (CRM)", "Europe/Rome", "Appuntamenti")
		self.assertEqual(client.get_calendar(cid)["summary"], "Studio Bianchi (CRM)")
		self.assertIsNone(client.get_calendar("nope@group.calendar.google.com"))
		self.assertTrue(self.google.calls[-1]["url"].endswith("/calendars/nope%40group.calendar.google.com"))

	def test_writes_notify_nobody(self):
		client = client_for(self.google)
		client.save(self.cal, "APPT-1", body_of(appointment("APPT-1")))
		client.remove(self.cal, "APPT-1")
		for call in self.google.calls:
			if call["method"] != "GET":
				self.assertEqual(call["params"].get("sendUpdates"), "none")

	def test_an_insert_carries_the_chosen_id(self):
		client = client_for(self.google)
		self.assertEqual(
			client.save(self.cal, "APPT-1", body_of(appointment("APPT-1"))), M.event_id("APPT-1")
		)
		put, post = self.google.calls
		self.assertEqual((put["method"], post["method"]), ("PUT", "POST"))
		self.assertEqual(post["json"]["id"], M.event_id("APPT-1"))

	def test_a_race_on_insert_ends_in_an_update(self):
		client = client_for(self.google)
		# another job inserts the event between this job's update and its insert
		client.save(self.cal, "APPT-1", body_of(appointment("APPT-1")))
		self.google.calls.clear()
		self.google.fail_next((404, {"error": {"code": 404}}))
		moved = body_of(appointment("APPT-1", start=at(2)))
		client.save(self.cal, "APPT-1", moved)
		self.assertEqual([c["method"] for c in self.google.calls], ["PUT", "POST", "PUT"])
		self.assertEqual(self.google.events(self.cal)[M.event_id("APPT-1")], moved)

	def test_an_appointment_cancelled_and_booked_again_comes_back(self):
		client = client_for(self.google)
		client.save(self.cal, "APPT-1", body_of(appointment("APPT-1")))
		self.assertEqual(client.remove(self.cal, "APPT-1"), 1)
		self.assertEqual(self.google.events(self.cal), {})
		client.save(self.cal, "APPT-1", body_of(appointment("APPT-1")))
		self.assertEqual(list(self.google.events(self.cal)), [M.event_id("APPT-1")])

	def test_when_google_keeps_the_id_in_its_bin_a_new_event_takes_over(self):
		self.google.bin_keeps_ids = True
		client = client_for(self.google)
		client.save(self.cal, "APPT-1", body_of(appointment("APPT-1")))
		client.remove(self.cal, "APPT-1")
		eid = client.save(self.cal, "APPT-1", body_of(appointment("APPT-1")))
		self.assertNotEqual(eid, M.event_id("APPT-1"))
		self.assertEqual(list(self.google.events(self.cal)), [eid])
		# saved again it is updated where it lives, and removing it finds it there
		self.assertEqual(client.save(self.cal, "APPT-1", body_of(appointment("APPT-1", start=at(3)))), eid)
		self.assertEqual(len(self.google.events(self.cal)), 1)
		self.assertEqual(client.remove(self.cal, "APPT-1"), 1)
		self.assertEqual(self.google.events(self.cal), {})

	def test_saving_into_a_vanished_calendar(self):
		del self.google.calendars[self.cal]
		with self.assertRaises(M.CalendarMissing):
			client_for(self.google).save(self.cal, "APPT-1", body_of(appointment()))

	def test_deleting_twice_is_harmless(self):
		client = client_for(self.google)
		client.save(self.cal, "APPT-1", body_of(appointment("APPT-1")))
		self.assertTrue(client.delete(self.cal, M.event_id("APPT-1")))
		self.assertFalse(client.delete(self.cal, M.event_id("APPT-1")))
		self.assertFalse(client.delete(self.cal, M.event_id("APPT-NEVER")))
		self.assertEqual(client.remove(self.cal, "APPT-NEVER"), 0)

	def test_an_expired_token_is_renewed_once(self):
		tokens = Tokens()
		client = M.CalendarClient(tokens, transport=self.google, sleep=lambda s: None)
		self.google.fail_next((401, {"error": {"code": 401, "message": "Invalid Credentials"}}))
		self.assertIsNotNone(client.get_calendar(self.cal))
		self.assertEqual(tokens.refreshed, 1)
		self.google.fail_next(*[(401, {"error": {"code": 401, "message": "Invalid Credentials"}})] * 2)
		with self.assertRaises(M.GoogleError) as caught:
			client.get_calendar(self.cal)
		self.assertEqual(caught.exception.status, 401)

	def test_busy_google_is_retried_with_backoff(self):
		waits = []
		client = client_for(self.google, sleep=waits.append)
		rate_limited = (403, {"error": {"code": 403, "errors": [{"reason": "rateLimitExceeded"}]}})
		self.google.fail_next((503, {}), rate_limited, (0, {"error": {"message": "ConnectionError"}}))
		self.assertIsNotNone(client.get_calendar(self.cal))
		self.assertEqual(waits, [1, 2, 4])

	def test_gives_up_after_the_retries(self):
		client = client_for(self.google, retries=1)
		self.google.fail_next(*[(0, {"error": {"message": "ConnectionError"}})] * 2)
		with self.assertRaises(M.GoogleError) as caught:
			client.get_calendar(self.cal)
		self.assertEqual(str(caught.exception), "Google could not be reached (ConnectionError)")
		self.assertEqual(caught.exception.status, 0)

	def test_a_refusal_is_not_retried(self):
		client = client_for(self.google)
		forbidden = {
			"error": {
				"code": 403,
				"message": "Calendar API has not been used",
				"errors": [{"reason": "accessNotConfigured"}],
			}
		}
		self.google.fail_next((403, forbidden))
		with self.assertRaises(M.GoogleError) as caught:
			client.get_calendar(self.cal)
		self.assertEqual(caught.exception.reason, "accessNotConfigured")
		self.assertEqual(str(caught.exception), "Google 403: Calendar API has not been used")
		self.assertEqual(len(self.google.calls), 1)


class TestErrorText(unittest.TestCase):
	def test_token_endpoint_errors_read_well_too(self):
		self.assertEqual(
			M.error_message(
				{"error": "invalid_grant", "error_description": "Token has been expired or revoked."}, 400
			),
			"Google 400: Token has been expired or revoked.",
		)
		self.assertEqual(M.error_message({}, 500), "Google 500")
		self.assertTrue(re.match(r"^Google could not be reached", M.error_message({}, 0)))
