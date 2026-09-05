# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import datetime

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, now_datetime

from crm.api import dialer
from crm.scheduling import availability
from crm.scheduling.timeutils import UTC, to_system_naive
from crm.telephony import answering, callbacks

ALL_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


def dt(*args) -> datetime.datetime:
	return datetime.datetime(*args, tzinfo=UTC)


OFFICE_HOURS = [("09:00:00", "17:00:00")]


class TelephonyCase(IntegrationTestCase):
	"""A practice open 09:00-17:00 on weekdays, in UTC so the arithmetic is readable."""

	def setUp(self):
		frappe.set_user("Administrator")
		self.set_company_hours(WEEKDAYS, OFFICE_HOURS)
		self.set_answering(enabled=1)

	def tearDown(self):
		frappe.db.rollback()
		self.clear_caches()

	def clear_caches(self):
		for attr in ("crm_scheduling_settings", "crm_answering_settings", "crm_company_hours"):
			if hasattr(frappe.local, attr):
				delattr(frappe.local, attr)

	def set_company_hours(self, days, windows):
		settings = frappe.get_doc("CRM Scheduling Settings")
		settings.timezone = "UTC"
		settings.set("default_availability", [])
		settings.default_holiday_list = None
		for day in days:
			for start, end in windows:
				settings.append(
					"default_availability", {"workday": day, "start_time": start, "end_time": end}
				)
		settings.save()
		self.clear_caches()

	def set_answering(self, **values):
		settings = frappe.get_doc("CRM Answering Settings")
		settings.update(
			{
				"answer_mode": answering.MODE_ALWAYS,
				"use_working_hours": 1,
				"callback_hours": 3,
				"dedupe_window_hours": 4,
				"max_callback_attempts": 3,
				"retry_after_hours": 3,
				"greeting_source": answering.SOURCE_TEXT,
				"greeting_text": "",
				"after_hours_greeting_text": "",
				**values,
			}
		)
		settings.save()
		self.clear_caches()
		return settings

	def make_incoming_call(self, number: str, **values):
		log = frappe.get_doc(
			{
				"doctype": "CRM Call Log",
				"to": "+390210000000",
				"type": "Incoming",
				"status": "Completed",
				"telephony_medium": "Twilio",
				**values,
			}
		)
		setattr(log, "from", number)
		log.insert(ignore_permissions=True)
		return log


# ---------------------------------------------------------------------------
# working-hours arithmetic
# ---------------------------------------------------------------------------


class TestWorkingHoursHelpers(TelephonyCase):
	def hours(self):
		return availability.company_working_hours()

	def test_open_during_the_working_window(self):
		# Wednesday 2026-09-02 is a weekday
		self.assertTrue(availability.is_open(self.hours(), dt(2026, 9, 2, 10)))

	def test_closed_after_the_window(self):
		self.assertFalse(availability.is_open(self.hours(), dt(2026, 9, 2, 20)))

	def test_closed_at_the_weekend(self):
		# 2026-09-05 is a Saturday
		self.assertFalse(availability.is_open(self.hours(), dt(2026, 9, 5, 10)))

	def test_window_is_half_open_at_its_end(self):
		self.assertTrue(availability.is_open(self.hours(), dt(2026, 9, 2, 9)))
		self.assertFalse(availability.is_open(self.hours(), dt(2026, 9, 2, 17)))

	def test_added_time_stays_inside_the_same_day(self):
		self.assertEqual(
			availability.add_working_time(dt(2026, 9, 2, 10), 3 * 3600, self.hours()),
			dt(2026, 9, 2, 13),
		)

	def test_added_time_spills_into_the_next_working_day(self):
		# 16:00 Wednesday + 3 working hours = 1h left today, 2h tomorrow morning
		self.assertEqual(
			availability.add_working_time(dt(2026, 9, 2, 16), 3 * 3600, self.hours()),
			dt(2026, 9, 3, 11),
		)

	def test_a_call_after_closing_is_due_the_next_morning(self):
		self.assertEqual(
			availability.add_working_time(dt(2026, 9, 2, 21), 3 * 3600, self.hours()),
			dt(2026, 9, 3, 12),
		)

	def test_added_time_jumps_the_weekend(self):
		# Friday 2026-09-04 16:00 + 3 working hours lands on Monday
		self.assertEqual(
			availability.add_working_time(dt(2026, 9, 4, 16), 3 * 3600, self.hours()),
			dt(2026, 9, 7, 11),
		)

	def test_next_opening_from_a_closed_moment(self):
		self.assertEqual(availability.next_opening(self.hours(), dt(2026, 9, 5, 10)), dt(2026, 9, 7, 9))

	def test_next_opening_while_already_open(self):
		self.assertEqual(availability.next_opening(self.hours(), dt(2026, 9, 2, 10)), dt(2026, 9, 2, 10))

	def test_holidays_close_the_practice(self):
		holiday_list = frappe.get_doc(
			{
				"doctype": "CRM Holiday List",
				"holiday_list_name": "Telephony Test Holidays",
				"from_date": "2026-09-01",
				"to_date": "2026-09-30",
				"holidays": [{"date": "2026-09-02", "description": "Closed"}],
			}
		).insert(ignore_permissions=True)
		settings = frappe.get_doc("CRM Scheduling Settings")
		settings.default_holiday_list = holiday_list.name
		settings.save()
		self.clear_caches()

		self.assertFalse(availability.is_open(self.hours(), dt(2026, 9, 2, 10)))
		# the promise skips the closed day entirely
		self.assertEqual(
			availability.add_working_time(dt(2026, 9, 2, 10), 3600, self.hours()), dt(2026, 9, 3, 10)
		)

	def test_no_configured_hours_means_always_open(self):
		self.set_company_hours([], [])
		hours = availability.company_working_hours()
		self.assertTrue(availability.is_open(hours, dt(2026, 9, 5, 3)))
		self.assertEqual(availability.add_working_time(dt(2026, 9, 5, 3), 3600, hours), dt(2026, 9, 5, 4))


# ---------------------------------------------------------------------------
# the announcement and the promise
# ---------------------------------------------------------------------------


class TestAnsweringService(TelephonyCase):
	def test_mode_is_explicit_not_derived_from_availability(self):
		self.set_answering(enabled=1, answer_mode=answering.MODE_ALWAYS)
		self.assertTrue(answering.takes_every_call())
		self.assertFalse(answering.rings_agents_first())

		self.set_answering(enabled=1, answer_mode=answering.MODE_RING_FIRST)
		self.assertFalse(answering.takes_every_call())
		self.assertTrue(answering.rings_agents_first())

	def test_a_disabled_service_never_takes_calls(self):
		self.set_answering(enabled=0, answer_mode=answering.MODE_ALWAYS)
		self.assertFalse(answering.takes_every_call())
		self.assertFalse(answering.rings_agents_first())

	def test_due_time_respects_working_hours(self):
		self.set_answering(enabled=1, callback_hours=3, use_working_hours=1)
		due = answering.callback_due(at=to_system_naive(dt(2026, 9, 2, 16)))
		self.assertEqual(due, to_system_naive(dt(2026, 9, 3, 11)))

	def test_due_time_ignores_working_hours_when_switched_off(self):
		self.set_answering(enabled=1, callback_hours=3, use_working_hours=0)
		due = answering.callback_due(at=to_system_naive(dt(2026, 9, 2, 21)))
		self.assertEqual(due, to_system_naive(dt(2026, 9, 3, 0)))

	def test_open_and_closed_greetings_differ(self):
		self.set_answering(
			enabled=1,
			greeting_text="Open, back within {hours}h",
			after_hours_greeting_text="Closed for today",
		)
		self.assertEqual(answering.render_greeting(open_now=True), "Open, back within 3h")
		self.assertEqual(answering.render_greeting(open_now=False), "Closed for today")

	def test_greeting_falls_back_to_a_default_sentence(self):
		self.set_answering(enabled=1, greeting_text="   ")
		self.assertIn("3", answering.render_greeting(open_now=True))

	def test_time_placeholder_is_filled(self):
		self.set_answering(enabled=1, greeting_text="Back by {time}")
		rendered = answering.render_greeting(open_now=True, due=to_system_naive(dt(2026, 9, 2, 11)))
		self.assertNotIn("{time}", rendered)

	def test_an_unknown_placeholder_does_not_break_the_call(self):
		self.set_answering(enabled=1, greeting_text="Ring {nonsense} back")
		# the caller hears the raw text rather than the announcement failing
		self.assertEqual(answering.render_greeting(open_now=True), "Ring {nonsense} back")

	def test_private_audio_is_refused(self):
		self.set_answering(
			enabled=1,
			greeting_source=answering.SOURCE_AUDIO,
			greeting_audio="/private/files/hello.mp3",
			after_hours_greeting_audio="/private/files/hello.mp3",
		)
		self.assertIsNone(answering.greeting_audio_url(open_now=True))

	def test_closed_audio_falls_back_to_the_open_one(self):
		self.set_answering(
			enabled=1,
			greeting_source=answering.SOURCE_AUDIO,
			greeting_audio="/files/open.mp3",
			after_hours_greeting_audio="",
		)
		self.assertTrue(answering.greeting_audio_url(open_now=False).endswith("/files/open.mp3"))


# ---------------------------------------------------------------------------
# the callback queue
# ---------------------------------------------------------------------------


class TestCallbackQueue(TelephonyCase):
	def test_an_incoming_call_queues_a_callback(self):
		log = self.make_incoming_call("+393331234567")
		carrier = callbacks.queue_callback(log)

		self.assertEqual(carrier, log.name)
		self.assertEqual(log.callback_status, callbacks.PENDING)
		self.assertTrue(log.callback_due)
		self.assertEqual(log.callback_attempts, 0)

	def test_a_repeat_caller_joins_the_queued_callback(self):
		first = self.make_incoming_call("+393331234567")
		callbacks.queue_callback(first)

		again = self.make_incoming_call("393331234567")
		carrier = callbacks.queue_callback(again)

		self.assertEqual(carrier, first.name)
		self.assertFalse(again.callback_status)
		self.assertEqual(frappe.db.count("CRM Call Log", {"callback_status": callbacks.PENDING}), 1)

	def test_local_and_international_formats_are_the_same_caller(self):
		first = self.make_incoming_call("+39 333 123 4567")
		callbacks.queue_callback(first)
		again = self.make_incoming_call("333-1234567")
		self.assertEqual(callbacks.queue_callback(again), first.name)

	def test_a_different_caller_gets_their_own_callback(self):
		first = self.make_incoming_call("+393331234567")
		callbacks.queue_callback(first)
		other = self.make_incoming_call("+393339999999")
		self.assertEqual(callbacks.queue_callback(other), other.name)
		self.assertEqual(frappe.db.count("CRM Call Log", {"callback_status": callbacks.PENDING}), 2)

	def test_merging_can_be_switched_off(self):
		self.set_answering(enabled=1, dedupe_window_hours=0)
		first = self.make_incoming_call("+393331234567")
		callbacks.queue_callback(first)
		again = self.make_incoming_call("+393331234567")
		self.assertEqual(callbacks.queue_callback(again), again.name)

	def test_an_unreadable_caller_id_never_merges(self):
		first = self.make_incoming_call("anonymous")
		callbacks.queue_callback(first)
		again = self.make_incoming_call("unknown")
		self.assertEqual(callbacks.queue_callback(again), again.name)

	def test_reaching_the_caller_closes_the_callback(self):
		log = self.make_incoming_call("+393331234567")
		callbacks.queue_callback(log)
		callbacks.resolve_callback(log.name)

		log.reload()
		self.assertEqual(log.callback_status, callbacks.DONE)
		self.assertTrue(log.callback_completed_on)

	def test_an_unanswered_attempt_requeues_the_callback(self):
		log = self.make_incoming_call("+393331234567")
		callbacks.queue_callback(log)
		callbacks.record_attempt(log.name)

		log.reload()
		self.assertEqual(log.callback_status, callbacks.PENDING)
		self.assertEqual(log.callback_attempts, 1)

	def test_the_attempt_cap_closes_an_unreachable_caller(self):
		self.set_answering(enabled=1, max_callback_attempts=2)
		log = self.make_incoming_call("+393331234567")
		callbacks.queue_callback(log)
		callbacks.record_attempt(log.name)
		callbacks.record_attempt(log.name)

		log.reload()
		self.assertEqual(log.callback_status, callbacks.CANCELLED)
		self.assertEqual(log.callback_attempts, 2)

	def test_only_due_callbacks_are_offered_by_default(self):
		due = self.make_incoming_call("+393331111111")
		callbacks.queue_callback(due)
		frappe.db.set_value("CRM Call Log", due.name, "callback_due", add_to_date(now_datetime(), hours=-1))

		later = self.make_incoming_call("+393332222222")
		callbacks.queue_callback(later)
		frappe.db.set_value("CRM Call Log", later.name, "callback_due", add_to_date(now_datetime(), hours=5))

		self.assertEqual([r.name for r in callbacks.pending_callbacks()], [due.name])
		self.assertEqual(len(callbacks.pending_callbacks(only_due=False)), 2)

	def test_summary_counts_what_is_owed_and_what_is_late(self):
		late = self.make_incoming_call("+393331111111")
		callbacks.queue_callback(late)
		frappe.db.set_value("CRM Call Log", late.name, "callback_due", add_to_date(now_datetime(), hours=-1))
		soon = self.make_incoming_call("+393332222222")
		callbacks.queue_callback(soon)
		frappe.db.set_value("CRM Call Log", soon.name, "callback_due", add_to_date(now_datetime(), hours=5))

		summary = callbacks.pending_summary()
		self.assertEqual(summary["pending"], 2)
		self.assertEqual(summary["due"], 1)
		self.assertEqual(summary["upcoming"], 1)


# ---------------------------------------------------------------------------
# working the queue from the dialer
# ---------------------------------------------------------------------------


class TestCallbackRound(TelephonyCase):
	def queue(self, number: str):
		log = self.make_incoming_call(number)
		callbacks.queue_callback(log)
		frappe.db.set_value("CRM Call Log", log.name, "callback_due", add_to_date(now_datetime(), hours=-1))
		return log

	def test_a_round_is_built_from_the_queue(self):
		self.queue("+393331111111")
		self.queue("+393332222222")

		session = dialer.create_session(source="Callbacks")
		self.assertEqual(session["source"], "Callbacks")
		self.assertEqual(session["total"], 2)
		self.assertTrue(all(e["call_log"] for e in session["entries"]))

	def test_an_empty_queue_says_so(self):
		with self.assertRaises(frappe.ValidationError):
			dialer.create_session(source="Callbacks")

	def test_reaching_the_caller_closes_their_callback(self):
		log = self.queue("+393331111111")
		session = dialer.create_session(source="Callbacks")
		dialer.complete_entry(session["name"], session["current"]["idx"], disposition="Interested")

		self.assertEqual(frappe.db.get_value("CRM Call Log", log.name, "callback_status"), "Done")

	def test_no_answer_keeps_the_callback_owed(self):
		log = self.queue("+393331111111")
		session = dialer.create_session(source="Callbacks")
		dialer.complete_entry(session["name"], session["current"]["idx"], disposition="No Answer")

		row = frappe.db.get_value(
			"CRM Call Log", log.name, ["callback_status", "callback_attempts"], as_dict=True
		)
		self.assertEqual(row.callback_status, "Pending")
		self.assertEqual(row.callback_attempts, 1)

	def test_reaching_an_answering_machine_is_not_reaching_the_caller(self):
		log = self.queue("+393331111111")
		session = dialer.create_session(source="Callbacks")
		dialer.complete_entry(session["name"], session["current"]["idx"], disposition="Voicemail")

		self.assertEqual(frappe.db.get_value("CRM Call Log", log.name, "callback_status"), "Pending")

	def test_a_wrong_number_closes_the_callback(self):
		log = self.queue("+393331111111")
		session = dialer.create_session(source="Callbacks")
		dialer.complete_entry(session["name"], session["current"]["idx"], disposition="Wrong Number")

		self.assertEqual(frappe.db.get_value("CRM Call Log", log.name, "callback_status"), "Cancelled")

	def test_skipping_leaves_the_promise_standing(self):
		log = self.queue("+393331111111")
		session = dialer.create_session(source="Callbacks")
		dialer.complete_entry(session["name"], session["current"]["idx"], skipped=True)

		row = frappe.db.get_value(
			"CRM Call Log", log.name, ["callback_status", "callback_attempts"], as_dict=True
		)
		self.assertEqual(row.callback_status, "Pending")
		self.assertEqual(row.callback_attempts, 0)

	def test_a_callback_with_no_matching_record_still_works(self):
		self.queue("+393331111111")
		session = dialer.create_session(source="Callbacks")
		entry = session["current"]

		self.assertFalse(entry["reference_name"])
		self.assertEqual(entry["display_name"], "+393331111111")
		# an outcome on an unmatched caller must not fail for want of a record to comment on
		dialer.complete_entry(session["name"], entry["idx"], disposition="Interested", note="ok")
