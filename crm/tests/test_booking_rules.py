# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""Online booking limits — pure, no database: runs with plain ``unittest`` too."""

import datetime
import unittest
from types import SimpleNamespace
from typing import ClassVar
from zoneinfo import ZoneInfo

from crm.scheduling import booking_rules as R

UTC = datetime.timezone.utc
ROME = ZoneInfo("Europe/Rome")
NOW = datetime.datetime(2026, 9, 24, 8, 0, tzinfo=UTC)  # 10:00 in Rome, a Thursday


def at(day, hour, minute=0):
	return datetime.datetime(2026, 9, day, hour, minute, tzinfo=UTC)


def slot(start, minutes=60, join=None):
	return SimpleNamespace(
		start=start, end=start + datetime.timedelta(minutes=minutes), join_appointment=join
	)


class TestFromService(unittest.TestCase):
	def test_missing_fields_fall_back_to_permissive_defaults(self):
		rules = R.OnlineRules.from_service({})
		self.assertTrue(rules.allow_cancel)
		self.assertTrue(rules.allow_reschedule)
		self.assertEqual(rules.max_per_day, 0)
		self.assertEqual(rules.eligibility, "Everyone")

	def test_reads_service_fields(self):
		rules = R.OnlineRules.from_service(
			{
				"min_notice_hours": 2,
				"booking_opens_on": "2026-10-01",
				"same_day_cutoff": datetime.timedelta(hours=12),
				"allow_online_cancel": 0,
				"max_bookings_per_week": "5",
			},
			global_max_active=3,
		)
		self.assertEqual(rules.min_notice_hours, 2)
		self.assertEqual(rules.opens_on, datetime.date(2026, 10, 1))
		self.assertEqual(rules.same_day_cutoff, datetime.time(12))
		self.assertFalse(rules.allow_cancel)
		self.assertEqual(rules.max_per_week, 5)
		self.assertEqual(rules.global_max_active_per_customer, 3)

	def test_negative_or_garbage_numbers_mean_no_limit(self):
		rules = R.OnlineRules.from_service({"max_bookings_per_day": -4, "max_concurrent": "x"})
		self.assertEqual(rules.max_per_day, 0)
		self.assertEqual(rules.max_concurrent, 0)


class TestTimeWindow(unittest.TestCase):
	def test_past_and_notice(self):
		rules = R.OnlineRules(min_notice_hours=24)
		self.assertEqual(rules.check_time(at(24, 7), NOW, ROME), R.LIMIT_IN_PAST)
		self.assertEqual(rules.check_time(at(24, 20), NOW, ROME), R.LIMIT_TOO_SOON)
		self.assertIsNone(rules.check_time(at(25, 9), NOW, ROME))

	def test_horizon(self):
		rules = R.OnlineRules(max_horizon_days=7)
		self.assertIsNone(rules.check_time(at(30, 9), NOW, ROME))
		self.assertEqual(
			rules.check_time(NOW + datetime.timedelta(days=8), NOW, ROME),
			R.LIMIT_TOO_FAR,
		)

	def test_seasonal_window_uses_the_local_date(self):
		rules = R.OnlineRules(opens_on=datetime.date(2026, 9, 26), closes_on=datetime.date(2026, 9, 27))
		self.assertEqual(rules.check_time(at(25, 9), NOW, ROME), R.LIMIT_NOT_OPEN_YET)
		# 23:30 UTC on the 25th is already the 26th in Rome
		self.assertIsNone(rules.check_time(at(25, 23, 30), NOW, ROME))
		self.assertEqual(rules.check_time(at(28, 9), NOW, ROME), R.LIMIT_CLOSED)

	def test_same_day_cutoff(self):
		rules = R.OnlineRules(same_day_cutoff=datetime.time(9, 30))
		# it is 10:00 in Rome: today is closed, tomorrow is not
		self.assertEqual(rules.check_time(at(24, 15), NOW, ROME), R.LIMIT_SAME_DAY_CUTOFF)
		self.assertIsNone(rules.check_time(at(25, 8), NOW, ROME))
		early = R.OnlineRules(same_day_cutoff=datetime.time(18))
		self.assertIsNone(early.check_time(at(24, 15), NOW, ROME))


class TestCapacity(unittest.TestCase):
	booked: ClassVar[list] = [(at(25, 8), at(25, 9)), (at(25, 10), at(25, 11)), (at(29, 8), at(29, 9))]

	def test_daily_cap(self):
		rules = R.OnlineRules(max_per_day=2)
		self.assertEqual(
			rules.check_capacity(at(25, 14), at(25, 15), self.booked, ROME), R.LIMIT_SERVICE_DAY_FULL
		)
		self.assertIsNone(rules.check_capacity(at(26, 14), at(26, 15), self.booked, ROME))

	def test_weekly_cap_is_per_iso_week(self):
		rules = R.OnlineRules(max_per_week=2)
		# the 25th is in the week of the two bookings on the 25th; the 29th is next week
		self.assertEqual(
			rules.check_capacity(at(26, 8), at(26, 9), self.booked, ROME), R.LIMIT_SERVICE_WEEK_FULL
		)
		self.assertIsNone(rules.check_capacity(at(30, 8), at(30, 9), self.booked, ROME))

	def test_concurrency(self):
		rules = R.OnlineRules(max_concurrent=1)
		self.assertEqual(
			rules.check_capacity(at(25, 8, 30), at(25, 9, 30), self.booked, ROME), R.LIMIT_CONCURRENT
		)
		# back to back is not simultaneous
		self.assertIsNone(rules.check_capacity(at(25, 9), at(25, 10), self.booked, ROME))

	def test_peak_overlap(self):
		booked = [(at(25, 8), at(25, 10)), (at(25, 9), at(25, 11)), (at(25, 9, 30), at(25, 9, 45))]
		self.assertEqual(R.peak_overlap(booked, at(25, 8), at(25, 12)), 3)
		self.assertEqual(R.peak_overlap(booked, at(25, 10), at(25, 12)), 1)
		self.assertEqual(R.peak_overlap([], at(25, 8), at(25, 12)), 0)


class TestClient(unittest.TestCase):
	def test_eligibility(self):
		new = R.ClientHistory()
		old = R.ClientHistory(all_starts=[at(1, 8)], is_returning=True)
		only_new = R.OnlineRules(eligibility="New customers only")
		only_old = R.OnlineRules(eligibility="Returning customers only")
		self.assertIsNone(only_new.check_client(at(25, 8), NOW, ROME, new))
		self.assertEqual(only_new.check_client(at(25, 8), NOW, ROME, old), R.LIMIT_NEW_ONLY)
		self.assertEqual(only_old.check_client(at(25, 8), NOW, ROME, new), R.LIMIT_RETURNING_ONLY)
		self.assertIsNone(only_old.check_client(at(25, 8), NOW, ROME, old))

	def test_active_limits_count_only_future(self):
		history = R.ClientHistory(
			service_starts=[at(1, 8), at(26, 8)], all_starts=[at(1, 8), at(26, 8), at(27, 8)]
		)
		self.assertEqual(
			R.OnlineRules(max_active_per_customer=1).check_client(at(28, 8), NOW, ROME, history),
			R.LIMIT_CLIENT_ACTIVE,
		)
		self.assertIsNone(
			R.OnlineRules(max_active_per_customer=2).check_client(at(28, 8), NOW, ROME, history)
		)
		self.assertEqual(
			R.OnlineRules(global_max_active_per_customer=2).check_client(at(28, 8), NOW, ROME, history),
			R.LIMIT_CLIENT_ACTIVE,
		)

	def test_per_day_and_spacing(self):
		history = R.ClientHistory(service_starts=[at(26, 8)], all_starts=[at(26, 8)])
		self.assertEqual(
			R.OnlineRules(max_per_customer_per_day=1).check_client(at(26, 14), NOW, ROME, history),
			R.LIMIT_CLIENT_DAY,
		)
		spacing = R.OnlineRules(min_days_between=7)
		self.assertEqual(spacing.check_client(at(30, 8), NOW, ROME, history), R.LIMIT_CLIENT_SPACING)
		self.assertIsNone(
			spacing.check_client(datetime.datetime(2026, 10, 3, 8, tzinfo=UTC), NOW, ROME, history)
		)


class TestAfterBooking(unittest.TestCase):
	def test_cancel(self):
		self.assertEqual(
			R.OnlineRules(allow_cancel=False).check_cancel(at(26, 8), NOW), R.LIMIT_CANCEL_DISABLED
		)
		self.assertEqual(
			R.OnlineRules(cancel_notice_hours=48).check_cancel(at(25, 8), NOW), R.LIMIT_CANCEL_NOTICE
		)
		self.assertIsNone(R.OnlineRules(cancel_notice_hours=24).check_cancel(at(25, 8), NOW))

	def test_reschedule(self):
		self.assertEqual(
			R.OnlineRules(allow_reschedule=False).check_reschedule(at(26, 8), NOW),
			R.LIMIT_RESCHEDULE_DISABLED,
		)
		self.assertEqual(
			R.OnlineRules(max_reschedules=2).check_reschedule(at(26, 8), NOW, done=2),
			R.LIMIT_RESCHEDULE_COUNT,
		)
		self.assertIsNone(R.OnlineRules(max_reschedules=2).check_reschedule(at(26, 8), NOW, done=1))
		self.assertEqual(
			R.OnlineRules(reschedule_notice_hours=72).check_reschedule(at(26, 8), NOW),
			R.LIMIT_RESCHEDULE_NOTICE,
		)


class TestSlotFilters(unittest.TestCase):
	def test_filter_drops_rule_breakers_but_keeps_group_joins(self):
		rules = R.OnlineRules(min_notice_hours=12, max_per_day=1)
		booked = [(at(26, 8), at(26, 9))]
		slots = [slot(at(24, 12)), slot(at(25, 8)), slot(at(26, 12)), slot(at(26, 8), join="APP-1")]
		kept = R.filter_slots(rules, slots, NOW, ROME, booked)
		self.assertEqual([s.start for s in kept], [at(25, 8), at(26, 8)])

	def test_thin_grid_aligns_to_local_midnight(self):
		slots = [slot(at(25, 7, m)) for m in (0, 15, 30, 45)]
		kept = R.thin_grid(slots, 30, ROME)
		self.assertEqual([s.start.minute for s in kept], [0, 30])
		self.assertEqual(len(R.thin_grid(slots, 0, ROME)), 4)


if __name__ == "__main__":
	unittest.main()
