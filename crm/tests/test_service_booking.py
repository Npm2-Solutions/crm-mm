# Copyright (c) 2026, NPM2 Solutions Srl and Contributors
# See license.txt

"""Public service booking: the menu, the slots, the limits, manage by token."""

import datetime
import json
from unittest.mock import patch

import frappe

from crm.api import service_booking as SB
from crm.scheduling.availability import forget_settings
from crm.scheduling.timeutils import UTC, from_system_naive
from crm.tests.test_scheduling import SchedulingCase


class TestServiceBooking(SchedulingCase):
	def setUp(self):
		super().setUp()
		settings = frappe.get_doc("CRM Scheduling Settings")
		settings.online_booking_enabled = 1
		settings.require_privacy_consent = 0
		settings.max_active_per_customer = 0
		settings.no_show_limit = 0
		settings.no_show_action = "Manual approval"
		# permissive booking-page defaults: each test customises what it checks
		settings.default_min_notice_hours = 0
		settings.default_max_horizon_days = 30
		settings.default_require_phone = 0
		settings.default_cancel_notice_hours = 0
		settings.default_reschedule_notice_hours = 0
		settings.default_max_reschedules = 0
		settings.default_online_confirmation = "Automatic"
		settings.save()
		forget_settings()
		self.anna = self.make_user("anna.online@example.com")
		self.bruno = self.make_user("bruno.online@example.com")
		# emails are queued, never sent; keep them out of the way
		self._mail = patch("frappe.sendmail")
		self._mail.start()

	def tearDown(self):
		self._mail.stop()
		super().tearDown()

	def online_service(self, name="Online Physio", **kw):
		from crm.scheduling.booking_rules import INHERITED

		kw.setdefault("bookable_online", 1)
		kw.setdefault("website_slug", name.lower().replace(" ", "-"))
		kw.setdefault("require_phone", 0)
		# an inheritable rule a test sets is a rule the service customises
		custom = [key for key in kw if key in INHERITED and key != "require_phone"]
		if custom:
			kw["online_overrides"] = json.dumps(custom)
		return self.make_service(name, kw.pop("staff", [self.anna, self.bruno]), **kw)

	def book(self, service, start, email="cliente@example.com", **kw):
		frappe.set_user("Guest")
		try:
			return SB.book(
				service=service.website_slug,
				start=start.isoformat(),
				full_name=kw.pop("full_name", "Cliente Online"),
				email=email,
				**kw,
			)
		finally:
			frappe.set_user("Administrator")

	# -- branding ----------------------------------------------------------------

	def test_the_public_page_carries_the_centres_logo(self):
		# A reader of two fields that asked `get_single_value` for a list with
		# `as_dict` raised every time; /prenota caught it and went out without
		# the centre's logo, on every site, without a word. The favicon and the
		# colours are the product's (crm.marchio, tests/test_marchio.py).
		frappe.db.set_single_value("FCRM Settings", "brand_logo", "/files/studio-logo.png")
		branding = SB.page_branding({})
		self.assertEqual(branding["logo"], "/files/studio-logo.png")

	def test_a_logo_of_the_page_itself_wins_over_the_brand(self):
		frappe.db.set_single_value("FCRM Settings", "brand_logo", "/files/studio-logo.png")
		branding = SB.page_branding({"booking_page_logo": "/files/booking.png"})
		self.assertEqual(branding["logo"], "/files/booking.png")

	def test_the_scheduling_settings_page_loads(self):
		# the same reader broke the settings page that shows the fallback brand
		from crm.api.appointments import get_scheduling_settings

		frappe.db.set_single_value("FCRM Settings", "brand_name", "Studio Luce")
		data = get_scheduling_settings()
		self.assertEqual(data["brand"]["name"], "Studio Luce")

	# -- catalogue -------------------------------------------------------------

	def test_catalog_lists_only_bookable_services_and_hides_staff_emails(self):
		self.online_service()
		self.make_service("Internal Only", [self.anna])
		catalog = SB.get_catalog()
		names = [s["name"] for s in catalog["services"]]
		self.assertIn("Online Physio", names)
		self.assertNotIn("Internal Only", names)
		physio = next(s for s in catalog["services"] if s["name"] == "Online Physio")
		self.assertTrue(physio["can_pick_staff"])
		self.assertNotIn("@", frappe.as_json(physio["staff"]))

	def test_closed_page_refuses(self):
		frappe.db.set_single_value("CRM Scheduling Settings", "online_booking_enabled", 0)
		forget_settings()
		with self.assertRaises(frappe.PermissionError):
			SB.get_catalog()

	# -- booking ----------------------------------------------------------------

	def test_book_creates_an_online_appointment_with_a_lead(self):
		service = self.online_service()
		result = self.book(service, self.tomorrow(10))
		self.assertEqual(result["status"], "Confirmed")
		row = frappe.db.get_value(
			"CRM Appointment Participant",
			{"access_token": result["token"]},
			["parent", "party"],
			as_dict=True,
		)
		appointment = frappe.get_doc("CRM Appointment", row.parent)
		self.assertEqual(appointment.source, "Online")
		self.assertEqual(from_system_naive(appointment.starts_on), self.tomorrow(10))
		self.assertTrue(row.party)
		self.assertEqual(len(appointment.staff), 1)

	def test_the_email_names_a_zone_only_from_another_and_in_words(self):
		"""The hour is the centre's: «(Europe/Rome)» told nothing to a patient in Rome
		(the simulation of a week found it in every confirmation)."""

		def al_cliente(email):
			return next(
				c.kwargs["message"]
				for c in reversed(frappe.sendmail.call_args_list)
				if c.kwargs.get("recipients") == [email]
			)

		service = self.online_service()
		self.book(service, self.tomorrow(10), timezone="UTC")
		messaggio = al_cliente("cliente@example.com")
		self.assertNotIn("(UTC)", messaggio)
		self.assertNotIn("Europe/", messaggio)
		self.book(service, self.tomorrow(11), email="londra@example.com", timezone="Europe/London")
		messaggio = al_cliente("londra@example.com")
		self.assertNotIn("Europe/London", messaggio)
		self.assertRegex(messaggio, r"\((Londra|London) · ")

	def test_manual_approval_books_as_scheduled(self):
		service = self.online_service(online_confirmation="Manual approval")
		result = self.book(service, self.tomorrow(10))
		self.assertEqual(result["status"], "Scheduled")
		self.assertTrue(result["pending_approval"])

	def test_slot_taken_twice_is_refused(self):
		service = self.online_service(staff=[self.anna])
		self.book(service, self.tomorrow(10))
		with self.assertRaises(frappe.ValidationError):
			self.book(service, self.tomorrow(10), email="altro@example.com")

	def test_chosen_professional_is_honoured(self):
		service = self.online_service()
		bruno_id = SB.public_staff_id(self.bruno)
		result = self.book(service, self.tomorrow(11), staff=bruno_id)
		appointment = frappe.get_doc(
			"CRM Appointment",
			frappe.db.get_value("CRM Appointment Participant", {"access_token": result["token"]}, "parent"),
		)
		self.assertEqual([r.user for r in appointment.staff], [self.bruno])

	def test_notice_is_enforced(self):
		service = self.online_service(min_notice_hours=48)
		with self.assertRaises(frappe.ValidationError):
			self.book(service, self.tomorrow(10))

	def test_client_cap_is_enforced(self):
		service = self.online_service(max_active_per_customer=1)
		self.book(service, self.tomorrow(9))
		with self.assertRaises(frappe.ValidationError):
			self.book(service, self.tomorrow(15))

	def mancati(self, service, quanti, giorni_fa=10):
		"""``quanti`` appointments of the client's, ``giorni_fa`` ago, never shown up to."""
		for ora in range(9, 9 + quanti):
			result = self.book(service, self.tomorrow(ora))
			parent = frappe.db.get_value(
				"CRM Appointment Participant", {"access_token": result["token"]}, "parent"
			)
			passato = frappe.db.get_value("CRM Appointment", parent, "starts_on") - datetime.timedelta(
				days=giorni_fa
			)
			frappe.db.set_value("CRM Appointment", parent, "starts_on", passato, update_modified=False)
			frappe.db.set_value("CRM Appointment Participant", {"parent": parent}, "status", "No Show")

	def no_show(self, limite, azione="Manual approval", mesi=12):
		settings = frappe.get_doc("CRM Scheduling Settings")
		settings.update({"no_show_limit": limite, "no_show_action": azione, "no_show_months": mesi})
		settings.save()
		forget_settings()

	def test_who_does_not_show_up_waits_for_approval(self):
		service = self.online_service()
		self.mancati(service, 2)
		self.no_show(2)
		result = self.book(service, self.tomorrow(14))
		self.assertEqual(result["status"], "Scheduled")
		self.assertTrue(result["pending_approval"])
		# somebody else books as before
		self.assertEqual(
			self.book(service, self.tomorrow(15), email="altra@example.com")["status"], "Confirmed"
		)

	def test_who_does_not_show_up_is_refused_where_the_centre_chose_so(self):
		service = self.online_service()
		self.mancati(service, 2)
		self.no_show(2, "Refuse")
		with self.assertRaises(frappe.ValidationError):
			self.book(service, self.tomorrow(14))

	def test_no_shows_off_or_old_change_nothing(self):
		service = self.online_service()
		self.mancati(service, 2, giorni_fa=100)
		self.assertEqual(self.book(service, self.tomorrow(14))["status"], "Confirmed")
		# only the last three months count: the misses are older
		self.no_show(2, mesi=3)
		self.assertEqual(self.book(service, self.tomorrow(15))["status"], "Confirmed")

	def test_daily_cap_hides_slots(self):
		service = self.online_service(max_bookings_per_day=1)
		day = self.tomorrow().date()
		before = SB.get_slots_public(
			service=service.website_slug, start_date=day.isoformat(), end_date=day.isoformat(), timezone="UTC"
		)
		self.assertTrue(before["days"])
		self.book(service, self.tomorrow(9))
		after = SB.get_slots_public(
			service=service.website_slug, start_date=day.isoformat(), end_date=day.isoformat(), timezone="UTC"
		)
		self.assertFalse(after["days"].get(day.isoformat()))

	# -- manage ------------------------------------------------------------------

	def test_cancel_by_token(self):
		service = self.online_service()
		token = self.book(service, self.tomorrow(10))["token"]
		frappe.set_user("Guest")
		view = SB.cancel(token=token)
		frappe.set_user("Administrator")
		self.assertEqual(view["status"], "Cancelled")

	def test_cancel_respects_notice(self):
		service = self.online_service(cancel_notice_hours=72)
		token = self.book(service, self.tomorrow(10))["token"]
		self.assertFalse(SB.get_booking(token)["can_cancel"])
		with self.assertRaises(frappe.ValidationError):
			SB.cancel(token=token)

	def test_reschedule_moves_and_counts(self):
		service = self.online_service(max_reschedules=1)
		token = self.book(service, self.tomorrow(10))["token"]
		view = SB.reschedule(token=token, start=self.tomorrow(14).isoformat())
		self.assertEqual(datetime.datetime.fromisoformat(view["start"]).astimezone(UTC), self.tomorrow(14))
		self.assertFalse(view["can_reschedule"])
		with self.assertRaises(frappe.ValidationError):
			SB.reschedule(token=token, start=self.tomorrow(16).isoformat())

	def test_group_seat_cancel_keeps_the_session(self):
		service = self.online_service(
			"Online Pilates", staff=[self.anna], max_participants=4, online_max_participants=2
		)
		first = self.book(service, self.tomorrow(10), email="uno@example.com")
		second = self.book(service, self.tomorrow(10), email="due@example.com")
		parent = frappe.db.get_value(
			"CRM Appointment Participant", {"access_token": first["token"]}, "parent"
		)
		self.assertEqual(
			parent,
			frappe.db.get_value("CRM Appointment Participant", {"access_token": second["token"]}, "parent"),
		)
		SB.cancel(token=first["token"])
		self.assertEqual(frappe.db.get_value("CRM Appointment", parent, "status"), "Confirmed")
