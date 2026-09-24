# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""One booking system: per-professional rules, inheritance, migration, overview APIs."""

import datetime
import json
from unittest.mock import patch

import frappe
from frappe.utils import get_datetime

from crm.api import booking_admin as ADMIN
from crm.api import service_booking as SB
from crm.scheduling import pricing, unify
from crm.scheduling.availability import get_slots
from crm.tests.test_scheduling import ALL_DAYS, SchedulingCase


class TestUnifiedBooking(SchedulingCase):
	def setUp(self):
		super().setUp()
		settings = frappe.get_doc("CRM Scheduling Settings")
		settings.online_booking_enabled = 1
		settings.require_privacy_consent = 0
		settings.default_min_notice_hours = 0
		settings.default_max_horizon_days = 30
		settings.default_require_phone = 0
		settings.save()
		self._reset_settings_cache()
		self.anna = self.make_user("anna.unified@example.com")
		self.bruno = self.make_user("bruno.unified@example.com")
		self._mail = patch("frappe.sendmail")
		self._mail.start()

	def tearDown(self):
		self._mail.stop()
		super().tearDown()

	def set_default(self, field, value):
		settings = frappe.get_doc("CRM Scheduling Settings")
		settings.set(field, value)
		settings.save()
		self._reset_settings_cache()

	def _reset_settings_cache(self):
		if hasattr(frappe.local, "crm_scheduling_settings"):
			del frappe.local.crm_scheduling_settings

	def service(self, name="Unified Visit", **kw):
		kw.setdefault("bookable_online", 1)
		kw.setdefault("website_slug", name.lower().replace(" ", "-"))
		return self.make_service(name, kw.pop("staff", [self.anna, self.bruno]), **kw)

	def set_staff(self, service, user, **values):
		for row in service.staff:
			if row.user == user:
				row.update(values)
		service.save()
		frappe.clear_document_cache("CRM Service", service.name)
		return service

	# -- professional x service --------------------------------------------------

	def test_own_duration_shapes_the_slot(self):
		service = self.set_staff(self.service(duration=60), self.bruno, duration=30)
		day = self.tomorrow().date()
		slots = get_slots(service.name, day, day, staff=[self.bruno])
		self.assertTrue(slots)
		self.assertEqual(slots[0].end - slots[0].start, datetime.timedelta(minutes=30))
		anna = get_slots(service.name, day, day, staff=[self.anna])
		self.assertEqual(anna[0].end - anna[0].start, datetime.timedelta(minutes=60))

	def test_offline_professional_is_not_offered_online(self):
		service = self.set_staff(self.service(), self.bruno, bookable_online=0)
		day = self.tomorrow().date()
		online = get_slots(service.name, day, day, online=True)
		self.assertTrue(online)
		self.assertTrue(all(slot.staff == [self.anna] for slot in online))
		# the practice itself can still book them
		internal = get_slots(service.name, day, day, staff=[self.bruno])
		self.assertTrue(internal)

	def test_professional_offline_everywhere(self):
		frappe.get_doc(
			{
				"doctype": "CRM Staff Schedule",
				"user": self.anna,
				"enabled": 1,
				"bookable_online": 0,
				"availability": [
					{"workday": d, "start_time": "00:00:00", "end_time": "23:59:59"} for d in ALL_DAYS
				],
			}
		).insert()
		service = self.service(staff=[self.anna])
		day = self.tomorrow().date()
		self.assertEqual(get_slots(service.name, day, day, online=True), [])
		self.assertFalse(SB._service_card(frappe.get_doc("CRM Service", service.name))["bookable"])

	def test_collective_service_closes_online_when_a_member_is_offline(self):
		service = self.set_staff(self.service(staff_selection="All required"), self.bruno, bookable_online=0)
		day = self.tomorrow().date()
		self.assertEqual(get_slots(service.name, day, day, online=True), [])

	def test_weekly_cap(self):
		frappe.get_doc(
			{
				"doctype": "CRM Staff Schedule",
				"user": self.anna,
				"enabled": 1,
				"max_weekly_appointments": 1,
				"availability": [
					{"workday": d, "start_time": "00:00:00", "end_time": "23:59:59"} for d in ALL_DAYS
				],
			}
		).insert()
		service = self.service(staff=[self.anna])
		self.make_appointment(service.name, self.tomorrow(9), [self.anna])
		day = self.tomorrow().date()
		self.assertEqual(get_slots(service.name, day, day), [])

	def test_own_price_beats_service_price(self):
		service = self.set_staff(self.service(default_price=50), self.bruno, custom_price=1, price=70)
		price = pricing.resolve_price(service.name, self.tomorrow(), staff=[self.bruno])
		self.assertEqual(price.rate, 70)
		self.assertEqual(pricing.resolve_price(service.name, self.tomorrow(), staff=[self.anna]).rate, 50)
		card = SB._service_card(frappe.get_doc("CRM Service", service.name))
		self.assertTrue(card["price_from"])
		self.assertEqual(card["price"], 50)

	def test_own_duration_sets_the_appointment_end(self):
		service = self.set_staff(self.service(duration=60), self.bruno, duration=20)
		appointment = self.make_appointment(service.name, self.tomorrow(10), [self.bruno])
		length = get_datetime(appointment.ends_on) - get_datetime(appointment.starts_on)
		self.assertEqual(length, datetime.timedelta(minutes=20))

	# -- inheritance ----------------------------------------------------------------

	def test_service_inherits_then_customises(self):
		self.set_default("default_min_notice_hours", 72)
		service = self.service(min_notice_hours=0)
		doc = frappe.get_doc("CRM Service", service.name)
		self.assertEqual(SB._rules(doc).min_notice_hours, 72)
		doc.online_overrides = json.dumps(["min_notice_hours"])
		doc.save()
		self.assertEqual(SB._rules(frappe.get_doc("CRM Service", service.name)).min_notice_hours, 0)

	def test_inherited_notice_hides_near_slots(self):
		self.set_default("default_min_notice_hours", 72)
		service = self.service()
		day = self.tomorrow().date()
		result = SB.get_slots_public(
			service=service.website_slug, start_date=day.isoformat(), end_date=day.isoformat(), timezone="UTC"
		)
		self.assertFalse(result["days"])

	# -- migration --------------------------------------------------------------------

	def test_calendar_becomes_a_service_and_redirects(self):
		cal = frappe.get_doc(
			{
				"doctype": "CRM Booking Calendar",
				"calendar_name": "Consulenza Gratuita",
				"route": "consulenza-gratuita",
				"enabled": 1,
				"timezone": "UTC",
				"duration": 30,
				"min_notice_hours": 4,
				"max_horizon_days": 14,
				"price": 0,
				"location": "Online",
				"show_in_menu": 0,
				"members": [{"user": self.anna}],
				"availability": [
					{"workday": d, "start_time": "09:00:00", "end_time": "18:00:00"} for d in ALL_DAYS
				],
			}
		).insert()
		created = unify.migrate_all()
		self.assertEqual(len(created), 1)
		service = frappe.get_doc("CRM Service", created[0])
		self.assertEqual(service.service_name, "Consulenza Gratuita")
		self.assertEqual([r.user for r in service.staff], [self.anna])
		self.assertEqual(service.location, "Online")
		self.assertTrue(service.hide_from_menu)
		self.assertEqual(service.website_slug, "consulenza-gratuita")
		self.assertIn("min_notice_hours", json.loads(service.online_overrides))
		self.assertEqual(
			frappe.db.get_value("CRM Booking Calendar", cal.name, "migrated_service"), service.name
		)
		self.assertEqual(unify.service_for_route("consulenza-gratuita"), service.name)
		self.assertEqual(unify.booking_url(service.name), "/prenota?servizio=consulenza-gratuita")
		# running it again moves nothing twice
		self.assertEqual(unify.migrate_all(), [])

	def test_link_only_service_is_not_in_the_menu(self):
		service = self.service("Hidden Visit", hide_from_menu=1)
		ids = [s["id"] for s in SB.get_catalog()["services"]]
		self.assertNotIn(service.website_slug, ids)
		ids = [s["id"] for s in SB.get_catalog(service=service.website_slug)["services"]]
		self.assertIn(service.website_slug, ids)

	# -- overview APIs ----------------------------------------------------------------

	def test_matrix_cell_row_and_column(self):
		service = self.service(staff=[self.anna])
		matrix = ADMIN.get_matrix()
		row = next(s for s in matrix["services"] if s["name"] == service.name)
		self.assertIn(self.anna, row["cells"])
		self.assertIn("Only one person delivers it", row["warnings"])

		ADMIN.set_cell(service=service.name, user=self.bruno, enabled=1, values={"duration": 15})
		doc = frappe.get_doc("CRM Service", service.name)
		self.assertEqual({r.user: r.duration for r in doc.staff}[self.bruno], 15)

		result = ADMIN.set_column(user=self.anna, services=[service.name], enabled=0)
		self.assertEqual([r.user for r in frappe.get_doc("CRM Service", service.name).staff], [self.bruno])
		self.assertEqual(result["errors"], [])

		# the last professional cannot be removed: reported, not raised
		result = ADMIN.set_column(user=self.bruno, services=[service.name], enabled=0)
		self.assertTrue(result["errors"])

	def test_copy_column(self):
		service = self.service(staff=[self.anna])
		ADMIN.copy_column(source=self.anna, target=self.bruno)
		self.assertIn(self.bruno, [r.user for r in frappe.get_doc("CRM Service", service.name).staff])

	def test_explain_slot_names_the_reason(self):
		service = self.service(staff=[self.anna])
		self.make_appointment(service.name, self.tomorrow(10), [self.anna])
		report = ADMIN.explain_slot(service=service.name, start=self.tomorrow(10).isoformat(), online=0)
		self.assertFalse(report["offered"])
		anna = report["staff"][0]
		self.assertEqual(anna["reasons"][0]["code"], "BUSY")
		free = ADMIN.explain_slot(service=service.name, start=self.tomorrow(15).isoformat(), online=0)
		self.assertTrue(free["offered"])
		self.assertTrue(free["staff"][0]["free"])

	def test_team_rota(self):
		self.service(staff=[self.anna])
		rota = ADMIN.get_team_rota(start=self.tomorrow().date().isoformat())
		self.assertEqual(len(rota["days"]), 7)
		person = next(p for p in rota["team"] if p["user"] == self.anna)
		self.assertEqual(len(person["days"]), 7)

	def test_inheritance_summary(self):
		service = self.service()
		frappe.db.set_value("CRM Service", service.name, "online_overrides", json.dumps(["max_reschedules"]))
		frappe.clear_document_cache("CRM Service", service.name)
		summary = ADMIN.get_inheritance_summary()
		self.assertIn(service.service_name, summary["max_reschedules"]["own"])
		self.assertGreaterEqual(summary["min_notice_hours"]["inherit"], 1)

	# -- online booking, one screen ------------------------------------------------

	def test_online_setup_switches(self):
		service = self.service(staff=[self.anna])
		setup = ADMIN.get_online_setup()
		self.assertTrue(setup["open"])
		anna = next(p for p in setup["team"] if p["user"] == self.anna)
		self.assertEqual(anna["bookable"], [service.name])

		# bruno does nothing yet: switching the service on for him adds him to it
		setup = ADMIN.set_person_service_online(user=self.bruno, service=service.name, online=1)
		bruno = next(p for p in setup["team"] if p["user"] == self.bruno)
		self.assertEqual(bruno["bookable"], [service.name])
		self.assertIn(self.bruno, [r.user for r in frappe.get_doc("CRM Service", service.name).staff])

		# off for a person, without a schedule: no longer bookable, hours untouched
		setup = ADMIN.set_person_online(user=self.bruno, online=0)
		bruno = next(p for p in setup["team"] if p["user"] == self.bruno)
		self.assertFalse(bruno["online"])
		self.assertEqual(bruno["bookable"], [])
		day = self.tomorrow().date()
		self.assertTrue(all(s.staff == [self.anna] for s in get_slots(service.name, day, day, online=True)))

		# the service off: nobody is bookable for it
		setup = ADMIN.set_service_online(service=service.name, online=0)
		anna = next(p for p in setup["team"] if p["user"] == self.anna)
		self.assertEqual(anna["bookable"], [])
		self.assertTrue(anna["reason"])

		setup = ADMIN.set_booking_open(enabled=0)
		self.assertFalse(setup["open"])


class TestParticipantsArePeople(SchedulingCase):
	def test_contact_and_deal_become_their_person(self):
		user = self.make_user("people.unified@example.com")
		service = self.make_service("People Visit", [user])
		lead = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Persona", "email": "persona@example.com"}
		).insert()
		lead.reload()
		rows = []
		if lead.get("contact"):
			rows.append({"party_type": "Contact", "party": lead.contact, "participant_name": "Persona"})
		appointment = self.make_appointment(service.name, self.tomorrow(10), [user], participants=rows)
		for row in appointment.participants:
			self.assertEqual((row.party_type, row.party), ("CRM Lead", lead.name))

	def test_person_of(self):
		from crm.fcrm.doctype.crm_appointment.crm_appointment import person_of

		self.assertEqual(person_of("CRM Lead", "X"), "X")
		self.assertIsNone(person_of("Contact", None))
		self.assertIsNone(person_of("Contact", "does-not-exist"))
