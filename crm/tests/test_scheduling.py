# Copyright (c) 2026, NPM2 Solutions Srl and Contributors
# See license.txt

import datetime

import frappe
from frappe.tests import IntegrationTestCase

from crm.api import appointments as A
from crm.api.activities import appointments_on
from crm.scheduling import intervals as iv
from crm.scheduling import pricing
from crm.scheduling.availability import find_conflicts, get_slots
from crm.scheduling.timeutils import UTC, from_system_naive, to_system_naive

ALL_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def dt(*args) -> datetime.datetime:
	return datetime.datetime(*args, tzinfo=UTC)


# ---------------------------------------------------------------------------
# interval algebra — pure, no database
# ---------------------------------------------------------------------------


class TestIntervals(IntegrationTestCase):
	def test_merge_joins_overlapping_and_touching(self):
		merged = iv.merge([(dt(2026, 9, 3, 9), dt(2026, 9, 3, 10)), (dt(2026, 9, 3, 10), dt(2026, 9, 3, 11))])
		self.assertEqual(merged, [(dt(2026, 9, 3, 9), dt(2026, 9, 3, 11))])

	def test_merge_drops_empty_intervals(self):
		self.assertEqual(iv.merge([(dt(2026, 9, 3, 9), dt(2026, 9, 3, 9))]), [])

	def test_intersect_keeps_the_common_part(self):
		a = [(dt(2026, 9, 3, 9), dt(2026, 9, 3, 12))]
		b = [(dt(2026, 9, 3, 11), dt(2026, 9, 3, 14))]
		self.assertEqual(iv.intersect(a, b), [(dt(2026, 9, 3, 11), dt(2026, 9, 3, 12))])

	def test_intersect_all_of_three_people(self):
		sets = [
			[(dt(2026, 9, 3, 9), dt(2026, 9, 3, 13))],
			[(dt(2026, 9, 3, 10), dt(2026, 9, 3, 14))],
			[(dt(2026, 9, 3, 11), dt(2026, 9, 3, 12))],
		]
		self.assertEqual(iv.intersect_all(sets), [(dt(2026, 9, 3, 11), dt(2026, 9, 3, 12))])

	def test_subtract_punches_a_hole(self):
		base = [(dt(2026, 9, 3, 9), dt(2026, 9, 3, 18))]
		holes = [(dt(2026, 9, 3, 13), dt(2026, 9, 3, 14))]
		self.assertEqual(
			iv.subtract(base, holes),
			[(dt(2026, 9, 3, 9), dt(2026, 9, 3, 13)), (dt(2026, 9, 3, 14), dt(2026, 9, 3, 18))],
		)

	def test_touching_intervals_do_not_overlap(self):
		# back-to-back appointments are legal
		self.assertFalse(
			iv.overlaps([(dt(2026, 9, 3, 9), dt(2026, 9, 3, 10))], dt(2026, 9, 3, 10), dt(2026, 9, 3, 11))
		)

	def test_covers_needs_one_continuous_interval(self):
		split = [(dt(2026, 9, 3, 9), dt(2026, 9, 3, 10)), (dt(2026, 9, 3, 10, 1), dt(2026, 9, 3, 12))]
		self.assertFalse(iv.covers(split, dt(2026, 9, 3, 9, 30), dt(2026, 9, 3, 11)))
		self.assertTrue(iv.covers(iv.merge(split), dt(2026, 9, 3, 9, 30), dt(2026, 9, 3, 10)))

	def test_peak_usage_counts_simultaneous_load(self):
		usage = [
			(dt(2026, 9, 3, 9), dt(2026, 9, 3, 11), 1),
			(dt(2026, 9, 3, 10), dt(2026, 9, 3, 12), 2),
			(dt(2026, 9, 3, 15), dt(2026, 9, 3, 16), 5),
		]
		self.assertEqual(iv.peak_usage(usage, dt(2026, 9, 3, 9), dt(2026, 9, 3, 12)), 3)
		self.assertEqual(iv.peak_usage(usage, dt(2026, 9, 3, 9), dt(2026, 9, 3, 10)), 1)

	def test_peak_usage_ignores_intervals_outside_the_window(self):
		usage = [(dt(2026, 9, 3, 15), dt(2026, 9, 3, 16), 5)]
		self.assertEqual(iv.peak_usage(usage, dt(2026, 9, 3, 9), dt(2026, 9, 3, 10)), 0)

	def test_slots_walk_each_window_from_its_own_start(self):
		windows = [
			(dt(2026, 9, 3, 9), dt(2026, 9, 3, 11)),
			(dt(2026, 9, 3, 14), dt(2026, 9, 3, 15)),
		]
		starts = iv.slots_in(windows, datetime.timedelta(minutes=60), datetime.timedelta(minutes=60))
		self.assertEqual(starts, [dt(2026, 9, 3, 9), dt(2026, 9, 3, 10), dt(2026, 9, 3, 14)])

	def test_slots_never_run_past_the_window(self):
		windows = [(dt(2026, 9, 3, 9), dt(2026, 9, 3, 10, 30))]
		starts = iv.slots_in(windows, datetime.timedelta(minutes=60), datetime.timedelta(minutes=30))
		self.assertEqual(starts, [dt(2026, 9, 3, 9), dt(2026, 9, 3, 9, 30)])


# ---------------------------------------------------------------------------
# scheduling fixtures
# ---------------------------------------------------------------------------


class SchedulingCase(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		settings = frappe.get_doc("CRM Scheduling Settings")
		settings.timezone = "UTC"
		settings.sync_to_event = 0
		settings.check_google_busy = 0
		settings.enforce_staff_conflicts = 1
		settings.enforce_resource_conflicts = 1
		settings.enforce_participant_conflicts = 1
		settings.enforce_working_hours = 0
		settings.allow_override = 1
		settings.set("default_availability", [])
		for day in ALL_DAYS:
			settings.append(
				"default_availability",
				{"workday": day, "start_time": "00:00:00", "end_time": "23:59:59"},
			)
		settings.save()
		if hasattr(frappe.local, "crm_scheduling_settings"):
			del frappe.local.crm_scheduling_settings

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		for cache in ("crm_scheduling_settings", "crm_service_buffers"):
			if hasattr(frappe.local, cache):
				delattr(frappe.local, cache)

	# -- fixtures ----------------------------------------------------------

	def make_user(self, email: str):
		if frappe.db.exists("User", email):
			return email
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0].title(),
				"send_welcome_email": 0,
				"roles": [{"role": "Sales User"}],
			}
		).insert(ignore_permissions=True)
		return email

	def make_resource(self, name, **kw):
		payload = {
			"doctype": "CRM Resource",
			"resource_name": name,
			"resource_type": kw.pop("resource_type", "Room"),
			"enabled": 1,
			"capacity": kw.pop("capacity", 1),
			"seats": kw.pop("seats", 0),
		}
		payload.update(kw)
		return frappe.get_doc(payload).insert()

	def make_service(self, name, staff, **kw):
		"""``staff`` takes plain emails, or ``(email, role)`` pairs for role staffing."""
		rows = []
		for entry in staff:
			user, role = entry if isinstance(entry, tuple) else (entry, None)
			rows.append({"user": user, "role": role} if role else {"user": user})
		payload = {
			"doctype": "CRM Service",
			"service_name": name,
			"enabled": 1,
			"duration": kw.pop("duration", 60),
			"staff_selection": kw.pop("staff_selection", "Any one"),
			"staff_count": kw.pop("staff_count", 1),
			"max_participants": kw.pop("max_participants", 1),
			"min_notice_hours": kw.pop("min_notice_hours", 0),
			"max_horizon_days": kw.pop("max_horizon_days", 30),
			"staff": rows,
			"roles": kw.pop("roles", []),
			# open around the clock so the tests do not depend on when they run
			"availability": [
				{"workday": day, "start_time": "00:00:00", "end_time": "23:59:59"} for day in ALL_DAYS
			],
		}
		payload.update(kw)
		return frappe.get_doc(payload).insert()

	def make_appointment(self, service, start, staff, **kw):
		payload = {
			"doctype": "CRM Appointment",
			"service": service,
			"status": kw.pop("status", "Scheduled"),
			"starts_on": to_system_naive(start),
			"staff": [{"user": u} for u in staff],
			"participants": kw.pop("participants", []),
			"resources": kw.pop("resources", []),
		}
		payload.update(kw)
		return frappe.get_doc(payload).insert()

	def tomorrow(self, hour=10):
		day = datetime.datetime.now(UTC).date() + datetime.timedelta(days=1)
		return datetime.datetime.combine(day, datetime.time(hour), tzinfo=UTC)


# ---------------------------------------------------------------------------
# staffing models
# ---------------------------------------------------------------------------


class TestStaffing(SchedulingCase):
	def test_round_robin_offers_a_slot_while_one_professional_is_free(self):
		anna = self.make_user("anna_sched@example.com")
		bruno = self.make_user("bruno_sched@example.com")
		self.make_service("Consulenza RR", [anna, bruno])
		start = self.tomorrow(10)
		self.make_appointment("Consulenza RR", start, [anna])

		slots = get_slots("Consulenza RR", start.date(), start.date())
		at_ten = [s for s in slots if s.start == start]
		self.assertEqual(len(at_ten), 1)
		self.assertEqual(at_ten[0].staff, [bruno])

	def test_round_robin_prefers_the_least_booked_professional(self):
		anna = self.make_user("anna_sched@example.com")
		bruno = self.make_user("bruno_sched@example.com")
		self.make_service("Consulenza carico", [anna, bruno])
		# anna already has a future appointment, so bruno should be picked first
		self.make_appointment("Consulenza carico", self.tomorrow(15), [anna])

		slots = get_slots("Consulenza carico", self.tomorrow(9).date(), self.tomorrow(9).date())
		free_at_nine = [s for s in slots if s.start == self.tomorrow(9)]
		self.assertEqual(free_at_nine[0].staff, [bruno])

	def test_priority_beats_load(self):
		anna = self.make_user("anna_sched@example.com")
		bruno = self.make_user("bruno_sched@example.com")
		service = self.make_service("Consulenza priorita", [anna, bruno])
		service.staff[0].priority = 0
		service.staff[1].priority = 5
		service.save()
		self.make_appointment("Consulenza priorita", self.tomorrow(15), [anna])

		slots = get_slots("Consulenza priorita", self.tomorrow(9).date(), self.tomorrow(9).date())
		free_at_nine = [s for s in slots if s.start == self.tomorrow(9)]
		self.assertEqual(free_at_nine[0].staff, [anna])

	def test_collective_books_every_professional_together(self):
		anna = self.make_user("anna_sched@example.com")
		bruno = self.make_user("bruno_sched@example.com")
		self.make_service("Visita in due", [anna, bruno], staff_selection="All required")

		slots = get_slots("Visita in due", self.tomorrow(9).date(), self.tomorrow(9).date())
		self.assertTrue(slots)
		self.assertEqual(sorted(slots[0].staff), sorted([anna, bruno]))

	def test_collective_slot_disappears_when_one_professional_is_busy(self):
		anna = self.make_user("anna_sched@example.com")
		bruno = self.make_user("bruno_sched@example.com")
		self.make_service("Visita in due", [anna, bruno], staff_selection="All required")
		self.make_service("Altro", [bruno])
		start = self.tomorrow(11)
		self.make_appointment("Altro", start, [bruno])

		starts = [s.start for s in get_slots("Visita in due", start.date(), start.date())]
		self.assertNotIn(start, starts)

	def test_one_per_role_fills_each_role(self):
		fisio = self.make_user("fisio_sched@example.com")
		aiuto = self.make_user("aiuto_sched@example.com")
		self.make_service(
			"Riabilitazione",
			[(fisio, "Therapist"), (aiuto, "Assistant")],
			staff_selection="One per role",
			roles=[
				{"role": "Therapist", "staff_count": 1},
				{"role": "Assistant", "staff_count": 1},
			],
		)

		slots = get_slots("Riabilitazione", self.tomorrow(9).date(), self.tomorrow(9).date())
		self.assertTrue(slots)
		self.assertEqual(sorted(slots[0].staff), sorted([fisio, aiuto]))

	def test_two_professionals_needed_but_only_one_free(self):
		anna = self.make_user("anna_sched@example.com")
		bruno = self.make_user("bruno_sched@example.com")
		self.make_service("Doppio", [anna, bruno], staff_count=2)
		start = self.tomorrow(10)
		self.make_service("Singolo", [bruno])
		self.make_appointment("Singolo", start, [bruno])

		starts = [s.start for s in get_slots("Doppio", start.date(), start.date())]
		self.assertNotIn(start, starts)


# ---------------------------------------------------------------------------
# rooms and equipment
# ---------------------------------------------------------------------------


class TestServiceHours(SchedulingCase):
	def test_a_service_of_one_day_is_closed_on_the_others(self):
		# the service's hours used to narrow only the days they named: on the
		# others it was open whenever its staff worked
		anna = self.make_user("anna_hours@example.com")
		start = self.tomorrow(10)
		self.make_service(
			"Solo un giorno",
			[anna],
			availability=[
				{"workday": ALL_DAYS[start.weekday()], "start_time": "10:00:00", "end_time": "12:00:00"}
			],
		)
		slots = get_slots("Solo un giorno", start.date(), (start + datetime.timedelta(days=1)).date())
		self.assertEqual([s.start for s in slots], [start, start + datetime.timedelta(hours=1)])

	def test_a_service_without_hours_follows_its_staff(self):
		anna = self.make_user("anna_hours@example.com")
		start = self.tomorrow(10)
		self.make_service("Sempre", [anna], availability=[])
		# every hour of the staff's day, which ends a second before midnight
		slots = get_slots("Sempre", start.date(), start.date())
		self.assertEqual([s.start.hour for s in slots], list(range(23)))


class TestResources(SchedulingCase):
	def test_exclusive_room_blocks_a_second_appointment(self):
		anna = self.make_user("anna_sched@example.com")
		bruno = self.make_user("bruno_sched@example.com")
		room = self.make_resource("Sala A", capacity=1)
		service = self.make_service("Trattamento", [anna, bruno])
		service.append("resources", {"resource": room.name, "quantity": 1, "required": 1})
		service.save()

		start = self.tomorrow(10)
		self.make_appointment(
			"Trattamento", start, [anna], resources=[{"resource": room.name, "quantity": 1}]
		)
		starts = [s.start for s in get_slots("Trattamento", start.date(), start.date())]
		self.assertNotIn(start, starts, "the only room is taken, so nobody else can be booked")

	def test_a_room_with_capacity_two_takes_two_appointments(self):
		anna = self.make_user("anna_sched@example.com")
		bruno = self.make_user("bruno_sched@example.com")
		room = self.make_resource("Palestra", capacity=2)
		service = self.make_service("Ginnastica", [anna, bruno])
		service.append("resources", {"resource": room.name, "quantity": 1, "required": 1})
		service.save()

		start = self.tomorrow(10)
		self.make_appointment("Ginnastica", start, [anna], resources=[{"resource": room.name, "quantity": 1}])
		starts = [s.start for s in get_slots("Ginnastica", start.date(), start.date())]
		self.assertIn(start, starts)

	def test_any_free_resource_of_a_type_is_picked(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_resource("Sala 1")
		self.make_resource("Sala 2")
		service = self.make_service("Colloquio", [anna])
		service.append("resources", {"resource_type": "Room", "quantity": 1, "required": 1})
		service.save()

		slots = get_slots("Colloquio", self.tomorrow(9).date(), self.tomorrow(9).date())
		self.assertTrue(slots)
		self.assertEqual(len(slots[0].resources), 1)
		self.assertIn(slots[0].resources[0]["resource"], ("Sala 1", "Sala 2"))

	def test_equipment_quantity_is_respected(self):
		anna = self.make_user("anna_sched@example.com")
		bruno = self.make_user("bruno_sched@example.com")
		machine = self.make_resource("Tapis roulant", resource_type="Equipment", capacity=3)
		service = self.make_service("Test da sforzo", [anna, bruno])
		service.append("resources", {"resource": machine.name, "quantity": 2, "required": 1})
		service.save()

		start = self.tomorrow(10)
		self.make_appointment(
			"Test da sforzo", start, [anna], resources=[{"resource": machine.name, "quantity": 2}]
		)
		# only one unit left, but the service needs two
		starts = [s.start for s in get_slots("Test da sforzo", start.date(), start.date())]
		self.assertNotIn(start, starts)

	def test_optional_resource_does_not_block_the_slot(self):
		anna = self.make_user("anna_sched@example.com")
		room = self.make_resource("Sala unica", capacity=1)
		service = self.make_service("Visita", [anna])
		service.append("resources", {"resource": room.name, "quantity": 1, "required": 0})
		service.save()

		start = self.tomorrow(10)
		other = self.make_user("bruno_sched@example.com")
		service2 = self.make_service("Occupa sala", [other])
		service2.append("resources", {"resource": room.name, "quantity": 1, "required": 1})
		service2.save()
		self.make_appointment(
			"Occupa sala", start, [other], resources=[{"resource": room.name, "quantity": 1}]
		)

		slot = next(s for s in get_slots("Visita", start.date(), start.date()) if s.start == start)
		self.assertEqual(slot.resources, [], "the room is taken but it was only optional")


# ---------------------------------------------------------------------------
# group sessions
# ---------------------------------------------------------------------------


class TestGroupSessions(SchedulingCase):
	def test_an_existing_class_with_seats_left_is_joinable(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Corso yoga", [anna], max_participants=8)
		start = self.tomorrow(18)
		appointment = self.make_appointment(
			"Corso yoga",
			start,
			[anna],
			participants=[{"participant_name": "Marco"}, {"participant_name": "Lucia"}],
		)

		joinable = [s for s in get_slots("Corso yoga", start.date(), start.date()) if s.join_appointment]
		self.assertEqual(len(joinable), 1)
		self.assertEqual(joinable[0].join_appointment, appointment.name)
		self.assertEqual(joinable[0].seats_left, 6)

	def test_a_full_class_is_not_offered(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Corso pieno", [anna], max_participants=2)
		start = self.tomorrow(18)
		self.make_appointment(
			"Corso pieno",
			start,
			[anna],
			participants=[{"participant_name": "Marco"}, {"participant_name": "Lucia"}],
		)

		joinable = [s for s in get_slots("Corso pieno", start.date(), start.date()) if s.join_appointment]
		self.assertEqual(joinable, [])

	def test_room_seats_cap_the_class(self):
		anna = self.make_user("anna_sched@example.com")
		room = self.make_resource("Saletta", seats=3)
		service = self.make_service("Corso piccolo", [anna], max_participants=10)
		service.append("resources", {"resource": room.name, "quantity": 1, "required": 1})
		service.save()

		slots = get_slots("Corso piccolo", self.tomorrow(9).date(), self.tomorrow(9).date())
		self.assertEqual(slots[0].seats_left, 3)

	def test_more_participants_than_the_service_allows_is_rejected(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Uno a uno", [anna], max_participants=1)
		with self.assertRaises(frappe.ValidationError):
			self.make_appointment(
				"Uno a uno",
				self.tomorrow(10),
				[anna],
				participants=[{"participant_name": "A"}, {"participant_name": "B"}],
			)


# ---------------------------------------------------------------------------
# conflicts
# ---------------------------------------------------------------------------


class TestConflicts(SchedulingCase):
	def test_double_booking_a_professional_is_blocked(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Visita A", [anna])
		start = self.tomorrow(10)
		self.make_appointment("Visita A", start, [anna])
		with self.assertRaises(frappe.ValidationError):
			self.make_appointment("Visita A", start, [anna])

	def test_back_to_back_appointments_are_allowed(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Visita B", [anna], duration=60)
		start = self.tomorrow(10)
		self.make_appointment("Visita B", start, [anna])
		later = self.make_appointment("Visita B", start + datetime.timedelta(hours=1), [anna])
		self.assertEqual(later.status, "Scheduled")

	def test_a_buffer_pushes_the_next_appointment_away(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Con buffer", [anna], duration=60, buffer_after=15)
		start = self.tomorrow(10)
		self.make_appointment("Con buffer", start, [anna])
		with self.assertRaises(frappe.ValidationError):
			self.make_appointment("Con buffer", start + datetime.timedelta(hours=1), [anna])

	def test_a_cancelled_appointment_frees_the_slot(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Visita C", [anna])
		start = self.tomorrow(10)
		booked = self.make_appointment("Visita C", start, [anna])
		booked.status = "Cancelled"
		booked.save()
		again = self.make_appointment("Visita C", start, [anna])
		self.assertEqual(again.status, "Scheduled")

	def test_a_no_show_still_occupies_the_slot(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Visita D", [anna])
		start = self.tomorrow(10)
		booked = self.make_appointment("Visita D", start, [anna])
		booked.status = "No Show"
		booked.save()
		with self.assertRaises(frappe.ValidationError):
			self.make_appointment("Visita D", start, [anna])

	def test_the_same_client_cannot_be_in_two_places(self):
		anna = self.make_user("anna_sched@example.com")
		bruno = self.make_user("bruno_sched@example.com")
		self.make_service("Visita E", [anna, bruno])
		lead = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Cliente"}).insert()
		start = self.tomorrow(10)
		participant = [{"party_type": "CRM Lead", "party": lead.name, "participant_name": "Cliente"}]
		self.make_appointment("Visita E", start, [anna], participants=participant)
		with self.assertRaises(frappe.ValidationError):
			self.make_appointment("Visita E", start, [bruno], participants=participant)

	def test_a_manager_can_force_a_conflict_and_it_is_recorded(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Visita F", [anna])
		start = self.tomorrow(10)
		self.make_appointment("Visita F", start, [anna])
		forced = self.make_appointment("Visita F", start, [anna], override_conflicts=1)
		self.assertTrue(forced.conflict_note)
		self.assertIn("already booked", forced.conflict_note)

	def test_moving_an_appointment_does_not_conflict_with_itself(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Visita G", [anna])
		booked = self.make_appointment("Visita G", self.tomorrow(10), [anna])
		self.assertEqual(find_conflicts(booked), [])

	def test_end_before_start_is_rejected(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Visita H", [anna])
		start = self.tomorrow(10)
		with self.assertRaises(frappe.ValidationError):
			self.make_appointment(
				"Visita H", start, [anna], ends_on=to_system_naive(start - datetime.timedelta(hours=1))
			)


# ---------------------------------------------------------------------------
# variable price lists
# ---------------------------------------------------------------------------


class TestPricing(SchedulingCase):
	def make_price_list(self, name, **kw):
		payload = {
			"doctype": "CRM Price List",
			"price_list_name": name,
			"enabled": 1,
			"currency": "EUR",
		}
		payload.update(kw)
		return frappe.get_doc(payload).insert()

	def make_price(self, price_list, service, price, **kw):
		payload = {
			"doctype": "CRM Service Price",
			"price_list": price_list,
			"service": service,
			"price": price,
			"enabled": 1,
		}
		payload.update(kw)
		return frappe.get_doc(payload).insert()

	def test_without_a_rule_the_service_base_price_wins(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Visita listino", [anna], default_price=80, currency="EUR")
		self.make_price_list("Listino base")
		resolved = pricing.resolve_price("Visita listino", self.tomorrow(10), price_list="Listino base")
		self.assertEqual(resolved.rate, 80)
		self.assertIn("default", resolved.source.lower())

	def test_a_matching_rule_overrides_the_base_price(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Visita listino", [anna], default_price=80)
		self.make_price_list("Listino base")
		self.make_price("Listino base", "Visita listino", 60, label="Convenzionato")
		resolved = pricing.resolve_price("Visita listino", self.tomorrow(10), price_list="Listino base")
		self.assertEqual(resolved.rate, 60)
		self.assertIn("Convenzionato", resolved.source)

	def test_the_more_specific_rule_wins_at_equal_priority(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Visita listino", [anna], default_price=80)
		self.make_price_list("Listino base")
		self.make_price("Listino base", "Visita listino", 60)
		self.make_price("Listino base", "Visita listino", 90, staff=anna, label="Tariffa Anna")
		resolved = pricing.resolve_price(
			"Visita listino", self.tomorrow(10), price_list="Listino base", staff=[anna]
		)
		self.assertEqual(resolved.rate, 90)

	def test_priority_beats_specificity(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Visita listino", [anna], default_price=80)
		self.make_price_list("Listino base")
		self.make_price("Listino base", "Visita listino", 50, priority=10, label="Promo")
		self.make_price("Listino base", "Visita listino", 90, staff=anna)
		resolved = pricing.resolve_price(
			"Visita listino", self.tomorrow(10), price_list="Listino base", staff=[anna]
		)
		self.assertEqual(resolved.rate, 50)

	def test_a_time_band_rule_only_applies_inside_it(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Visita serale", [anna], default_price=80)
		self.make_price_list("Listino base")
		self.make_price(
			"Listino base",
			"Visita serale",
			100,
			start_time="18:00:00",
			end_time="22:00:00",
			label="Serale",
		)
		evening = pricing.resolve_price("Visita serale", self.tomorrow(19), price_list="Listino base")
		morning = pricing.resolve_price("Visita serale", self.tomorrow(10), price_list="Listino base")
		self.assertEqual(evening.rate, 100)
		self.assertEqual(morning.rate, 80)

	def test_a_group_rule_kicks_in_above_a_headcount(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Corso", [anna], default_price=30, max_participants=10)
		self.make_price_list("Listino base")
		self.make_price("Listino base", "Corso", 20, min_participants=5, per_participant=1, label="Gruppo")
		small = pricing.resolve_price("Corso", self.tomorrow(10), price_list="Listino base", participants=2)
		big = pricing.resolve_price("Corso", self.tomorrow(10), price_list="Listino base", participants=6)
		self.assertEqual(small.rate, 30)
		self.assertEqual(big.rate, 20)
		self.assertTrue(big.per_participant)
		self.assertEqual(big.total(6), 120)

	def test_an_expired_rule_is_ignored(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Visita listino", [anna], default_price=80)
		self.make_price_list("Listino base")
		yesterday = (datetime.datetime.now(UTC).date() - datetime.timedelta(days=1)).isoformat()
		self.make_price("Listino base", "Visita listino", 40, valid_upto=yesterday)
		resolved = pricing.resolve_price("Visita listino", self.tomorrow(10), price_list="Listino base")
		self.assertEqual(resolved.rate, 80)

	def test_the_appointment_stores_the_resolved_total(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Corso prezzi", [anna], default_price=30, max_participants=5)
		price_list = self.make_price_list("Listino corsi")
		self.make_price(price_list.name, "Corso prezzi", 25, per_participant=1, label="A testa")
		appointment = self.make_appointment(
			"Corso prezzi",
			self.tomorrow(10),
			[anna],
			price_list=price_list.name,
			participants=[
				{"participant_name": "A"},
				{"participant_name": "B"},
				{"participant_name": "C"},
			],
		)
		self.assertEqual(appointment.unit_price, 25)
		self.assertEqual(appointment.total_amount, 75)
		self.assertIn("A testa", appointment.price_source)


# ---------------------------------------------------------------------------
# API surface
# ---------------------------------------------------------------------------


class TestAppointmentApi(SchedulingCase):
	def test_a_cancelled_appointment_brought_back_books_the_person_again(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Visita ripresa", [anna])
		booked = self.make_appointment(
			"Visita ripresa", self.tomorrow(10), [anna], participants=[{"participant_name": "Cliente"}]
		)
		cancelled = A.set_status(booked.name, "Cancelled", reason="Ha chiamato per disdire")
		self.assertEqual(cancelled["cancellation_reason"], "Ha chiamato per disdire")
		self.assertEqual([p["status"] for p in cancelled["participants"]], ["Cancelled"])

		# with nobody in it, nobody was reminded and the agenda showed only the service
		back = A.set_status(booked.name, "Confirmed")
		self.assertEqual([p["status"] for p in back["participants"]], ["Booked"])
		self.assertFalse(back["cancellation_reason"])
		self.assertIn("Cliente", back["title"])

	def test_a_class_brought_back_fills_only_its_seats(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Corso ripreso", [anna], max_participants=2)
		corso = self.make_appointment(
			"Corso ripreso",
			self.tomorrow(18),
			[anna],
			participants=[
				{"participant_name": "Marco"},
				{"participant_name": "Lucia", "status": "Cancelled"},
				{"participant_name": "Paolo"},
			],
		)
		A.set_status(corso.name, "Cancelled")
		back = A.set_status(corso.name, "Scheduled")
		self.assertEqual(
			[(p["participant_name"], p["status"]) for p in back["participants"]],
			[("Marco", "Booked"), ("Lucia", "Booked"), ("Paolo", "Cancelled")],
		)

	def test_somebody_typed_with_a_contact_gets_a_record(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Visita scritta", [anna])
		start = self.tomorrow(10)

		def prenota(ore):
			inizio = start + datetime.timedelta(hours=ore)
			return A.save_appointment(
				{
					"service": "Visita scritta",
					"starts_on": inizio.isoformat(),
					"ends_on": (inizio + datetime.timedelta(minutes=30)).isoformat(),
					"staff": [{"user": anna}],
					"participants": [
						{"participant_name": "Giulia Scritta", "email": "giulia.scritta@example.com"}
					],
				}
			)

		persona = prenota(0)["participants"][0]["party"]
		self.assertTrue(persona)
		self.assertEqual(frappe.db.get_value("CRM Lead", persona, "email"), "giulia.scritta@example.com")
		# typed again, the same person: never a second record
		self.assertEqual(prenota(2)["participants"][0]["party"], persona)

	def test_a_name_typed_alone_stays_a_name(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Visita anonima", [anna])
		start = self.tomorrow(10)
		saved = A.save_appointment(
			{
				"service": "Visita anonima",
				"starts_on": start.isoformat(),
				"ends_on": (start + datetime.timedelta(minutes=30)).isoformat(),
				"staff": [{"user": anna}],
				"participants": [{"participant_name": "Maria Rossi"}],
			}
		)
		self.assertFalse(saved["participants"][0]["party"])

	def test_save_and_move_an_appointment(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Visita API", [anna])
		start = self.tomorrow(10)
		saved = A.save_appointment(
			{
				"service": "Visita API",
				"starts_on": start.isoformat(),
				"ends_on": (start + datetime.timedelta(hours=1)).isoformat(),
				"staff": [{"user": anna}],
				"participants": [{"participant_name": "Cliente"}],
			}
		)
		self.assertEqual(saved["status"], "Scheduled")

		moved = A.move_appointment(saved["name"], (start + datetime.timedelta(hours=2)).isoformat())
		self.assertEqual(from_system_naive(moved["starts_on"]), start + datetime.timedelta(hours=2))
		self.assertEqual(from_system_naive(moved["ends_on"]), start + datetime.timedelta(hours=3))

	def test_calendar_feed_carries_staff_and_participants(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Visita feed", [anna])
		start = self.tomorrow(10)
		self.make_appointment("Visita feed", start, [anna], participants=[{"participant_name": "Cliente"}])
		feed = A.get_calendar(start.date().isoformat(), start.date().isoformat(), include_events=False)
		row = next(a for a in feed["appointments"] if a["service"] == "Visita feed")
		self.assertEqual([s["user"] for s in row["staff"]], [anna])
		self.assertEqual([p["participant_name"] for p in row["participants"]], ["Cliente"])

	def test_the_feed_marks_a_persons_first_visit(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Visita prima", [anna])
		lead = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Prima", "last_name": "Visita"}).insert(
			ignore_permissions=True
		)
		who = [{"party_type": "CRM Lead", "party": lead.name, "participant_name": "Prima Visita"}]
		start = self.tomorrow(10)
		# a cancelled one before it does not count
		cancelled = self.make_appointment(
			"Visita prima",
			start - datetime.timedelta(hours=2),
			[anna],
			participants=[dict(row) for row in who],
			status="Cancelled",
		)
		first = self.make_appointment("Visita prima", start, [anna], participants=[dict(row) for row in who])
		later = self.make_appointment(
			"Visita prima",
			start + datetime.timedelta(days=2),
			[anna],
			participants=[dict(row) for row in who],
		)
		other = self.make_appointment(
			"Visita prima",
			start + datetime.timedelta(hours=3),
			[anna],
			participants=[{"participant_name": "Senza scheda"}],
		)

		def marks():
			feed = A.get_calendar(
				(start - datetime.timedelta(days=1)).date().isoformat(),
				(start + datetime.timedelta(days=2)).date().isoformat(),
				include_events=False,
			)
			return {row["name"]: row["first_visit"] for row in feed["appointments"]}

		self.assertEqual(
			{name: marks()[name] for name in (cancelled.name, first.name, later.name, other.name)},
			{cancelled.name: False, first.name: True, later.name: False, other.name: False},
		)
		# a client from before the agenda: no first visit
		frappe.db.set_value("CRM Lead", lead.name, "client_since", "2020-01-01")
		self.assertFalse(marks()[first.name])

	def test_calendar_feed_filters_by_professional(self):
		anna = self.make_user("anna_sched@example.com")
		bruno = self.make_user("bruno_sched@example.com")
		self.make_service("Visita filtro", [anna, bruno])
		start = self.tomorrow(10)
		self.make_appointment("Visita filtro", start, [anna])
		self.make_appointment("Visita filtro", start, [bruno])
		feed = A.get_calendar(
			start.date().isoformat(), start.date().isoformat(), staff=[bruno], include_events=False
		)
		users = {s["user"] for row in feed["appointments"] for s in row["staff"]}
		self.assertEqual(users, {bruno})

	def test_cancelling_marks_the_participants_too(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Visita annulla", [anna])
		booked = self.make_appointment(
			"Visita annulla",
			self.tomorrow(10),
			[anna],
			participants=[{"participant_name": "Cliente"}],
		)
		cancelled = A.set_status(booked.name, "Cancelled", "Cliente indisponibile")
		self.assertEqual(cancelled["status"], "Cancelled")
		self.assertEqual(cancelled["participants"][0]["status"], "Cancelled")

	def test_joining_a_group_session_respects_the_seat_limit(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Corso API", [anna], max_participants=2)
		booked = self.make_appointment(
			"Corso API", self.tomorrow(18), [anna], participants=[{"participant_name": "A"}]
		)
		joined = A.join_appointment(booked.name, {"participant_name": "B"})
		self.assertEqual(len(joined["participants"]), 2)
		with self.assertRaises(frappe.ValidationError):
			A.join_appointment(booked.name, {"participant_name": "C"})

	def test_a_weekly_series_creates_independent_appointments(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Ciclo", [anna])
		booked = self.make_appointment("Ciclo", self.tomorrow(10), [anna])
		result = A.create_series(booked.name, "Weekly", 3)
		self.assertEqual(len(result["created"]), 3)
		self.assertEqual(result["skipped"], [])
		siblings = frappe.get_all("CRM Appointment", filters={"series": result["series"]})
		self.assertEqual(len(siblings), 4, "the source plus its three repeats")

	def test_a_series_reports_the_dates_it_could_not_book(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Ciclo bloccato", [anna])
		start = self.tomorrow(10)
		booked = self.make_appointment("Ciclo bloccato", start, [anna])
		# something else already sits on the second occurrence
		self.make_appointment("Ciclo bloccato", start + datetime.timedelta(days=14), [anna])
		result = A.create_series(booked.name, "Weekly", 2)
		self.assertEqual(len(result["created"]), 1)
		self.assertEqual(len(result["skipped"]), 1)

	def _person(self, first_name):
		return frappe.get_doc({"doctype": "CRM Lead", "first_name": first_name}).insert(
			ignore_permissions=True
		)

	def test_a_person_has_their_appointments_newest_first(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Visita persona", [anna])
		giulia = self._person("Giulia")
		marta = self._person("Marta")
		earlier = self.make_appointment(
			"Visita persona",
			self.tomorrow(9),
			[anna],
			participants=[{"party_type": "CRM Lead", "party": giulia.name, "participant_name": "Giulia"}],
		)
		later = self.make_appointment(
			"Visita persona",
			self.tomorrow(11),
			[anna],
			participants=[{"party_type": "CRM Lead", "party": giulia.name, "participant_name": "Giulia"}],
		)
		self.make_appointment(
			"Visita persona",
			self.tomorrow(14),
			[anna],
			participants=[{"party_type": "CRM Lead", "party": marta.name, "participant_name": "Marta"}],
		)
		rows = A.get_person_appointments("CRM Lead", giulia.name)
		self.assertEqual([row["name"] for row in rows], [later.name, earlier.name])
		self.assertEqual(rows[0]["service"], "Visita persona")

	def test_in_a_class_a_place_given_up_is_cancelled_for_that_person(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Lezione di gruppo", [anna], max_participants=8)
		giulia = self._person("Giulia")
		marta = self._person("Marta")
		self.make_appointment(
			"Lezione di gruppo",
			self.tomorrow(18),
			[anna],
			participants=[
				{
					"party_type": "CRM Lead",
					"party": giulia.name,
					"participant_name": "Giulia",
					"status": "Cancelled",
				},
				{"party_type": "CRM Lead", "party": marta.name, "participant_name": "Marta"},
			],
		)
		# the class goes on, Giulia's page says she is not coming
		self.assertEqual(A.get_person_appointments("CRM Lead", giulia.name)[0]["status"], "Cancelled")
		self.assertEqual(A.get_person_appointments("CRM Lead", marta.name)[0]["status"], "Scheduled")
		self.assertEqual(appointments_on("CRM Lead", giulia.name)[0]["data"]["status"], "Cancelled")

	def test_a_place_says_how_it_went_for_that_person(self):
		self.assertEqual(A.per_la_persona("Completed", "No Show"), "No Show")
		# came, while the class is still open at the desk
		self.assertEqual(A.per_la_persona("Confirmed", "Attended"), "Completed")
		self.assertEqual(A.per_la_persona("Confirmed", "Booked"), "Confirmed")
		self.assertEqual(A.per_la_persona("Cancelled", None), "Cancelled")

	def test_a_deal_answers_for_the_person_behind_it(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Visita trattativa", [anna])
		giulia = self._person("Giulia")
		organization = frappe.get_doc(
			{"doctype": "CRM Organization", "organization_name": "Studio Appuntamenti"}
		).insert(ignore_permissions=True)
		deal = frappe.get_doc(
			{"doctype": "CRM Deal", "lead": giulia.name, "organization": organization.name}
		).insert(ignore_permissions=True)
		booked = self.make_appointment(
			"Visita trattativa",
			self.tomorrow(10),
			[anna],
			participants=[{"party_type": "CRM Lead", "party": giulia.name, "participant_name": "Giulia"}],
		)
		rows = A.get_person_appointments("CRM Deal", deal.name)
		self.assertEqual([row["name"] for row in rows], [booked.name])

	def test_nobody_booked_nothing_listed(self):
		self.assertEqual(A.get_person_appointments("CRM Lead", self._person("Nessuno").name), [])
		self.assertEqual(A.get_person_appointments("Contact", "anything"), [])

	def test_quote_price_answers_without_saving_anything(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Visita preventivo", [anna], default_price=70)
		quote = A.quote_price("Visita preventivo", self.tomorrow(10).isoformat())
		self.assertEqual(quote["rate"], 70)
		self.assertEqual(quote["total"], 70)

	def test_check_conflicts_warns_before_saving(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Visita check", [anna])
		start = self.tomorrow(10)
		self.make_appointment("Visita check", start, [anna])
		conflicts = A.check_conflicts(
			{
				"service": "Visita check",
				"starts_on": start.isoformat(),
				"ends_on": (start + datetime.timedelta(hours=1)).isoformat(),
				"staff": [{"user": anna}],
			}
		)
		self.assertTrue(conflicts)

	def test_scheduler_meta_lists_services_with_their_team(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Visita meta", [anna])
		meta = A.get_scheduler_meta()
		service = next(s for s in meta["services"] if s["name"] == "Visita meta")
		self.assertEqual([row["user"] for row in service["staff"]], [anna])
		self.assertIn(anna, [person["name"] for person in meta["staff"]])

	def test_workload_counts_booked_minutes_per_professional(self):
		anna = self.make_user("anna_sched@example.com")
		self.make_service("Visita carico", [anna], duration=60)
		start = self.tomorrow(10)
		self.make_appointment("Visita carico", start, [anna])
		workload = A.get_workload(start.date().isoformat(), start.date().isoformat())
		self.assertEqual(workload["staff"][anna], 60)
