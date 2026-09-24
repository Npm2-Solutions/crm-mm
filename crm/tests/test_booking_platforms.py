# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""Booking platform connectors — pure parsing and signatures, no network, no database."""

import base64
import datetime
import hashlib
import hmac
import json
import time
import unittest
from pathlib import Path

from crm.booking_platforms import PROVIDERS, REGISTRY, provider_class
from crm.booking_platforms import base as B
from crm.booking_platforms import docplanner as D
from crm.booking_platforms import email_parser as E
from crm.booking_platforms import generic_webhook as G
from crm.booking_platforms import ical as I
from crm.booking_platforms import schedulers as S

UTC = datetime.timezone.utc


def utc(*args):
	return datetime.datetime(*args, tzinfo=UTC)


class Conn(dict):
	"""What a connector needs from ``CRM Booking Connection``, as a dict."""

	def get_password(self, field, raise_exception=False):
		return self.get(field) or ""


class TestRegistry(unittest.TestCase):
	def test_every_platform_is_a_select_option(self):
		doctype = (
			Path(__file__).resolve().parent.parent
			/ "fcrm/doctype/crm_booking_connection/crm_booking_connection.json"
		)
		field = next(f for f in json.loads(doctype.read_text())["fields"] if f["fieldname"] == "platform")
		self.assertEqual(field["options"].split("\n"), [cls.label for cls in PROVIDERS])

	def test_lookup_by_label_or_key(self):
		self.assertIs(provider_class("Cal.com"), S.CalCom)
		self.assertIs(provider_class("docplanner"), D.Docplanner)
		self.assertEqual(len(REGISTRY), len(PROVIDERS))

	def test_describe_is_serialisable(self):
		for cls in PROVIDERS:
			json.dumps(cls.describe())
			self.assertTrue(cls.label and cls.key)

	def test_only_proven_connectors_are_stable(self):
		"""What the team (not only administrators) may use: raise this list only with proof."""
		stable = {cls.key for cls in PROVIDERS if cls.stability == "stable"}
		self.assertEqual(stable, {"ical", "webhook"})
		from crm.booking_platforms import catalog, is_stable

		self.assertEqual({p["key"] for p in catalog(include_beta=False)}, stable)
		self.assertTrue(is_stable("iCal feed"))
		self.assertFalse(is_stable("Treatwell / Uala"))
		self.assertFalse(is_stable("nope"))

	def test_missing_fields(self):
		provider = S.CalCom(Conn())
		self.assertEqual(provider.missing_fields(), ["api_key"])
		self.assertEqual(S.CalCom(Conn(api_key="cal_live_x")).missing_fields(), [])


class TestBaseHelpers(unittest.TestCase):
	def test_as_utc_accepts_every_shape(self):
		self.assertEqual(B.as_utc("2026-09-25T10:00:00+02:00"), utc(2026, 9, 25, 8))
		self.assertEqual(B.as_utc("2026-09-25T08:00:00Z"), utc(2026, 9, 25, 8))
		self.assertEqual(B.as_utc("2026-09-25 10:00:00+0200"), utc(2026, 9, 25, 8))
		self.assertEqual(B.as_utc("2026-09-25T08:00:00.0000000Z"), utc(2026, 9, 25, 8))
		self.assertEqual(B.as_utc(1790323200), datetime.datetime.fromtimestamp(1790323200, UTC))

	def test_local_to_utc(self):
		self.assertEqual(B.local_to_utc("2026-09-25 10:00:00", "Europe/Rome"), utc(2026, 9, 25, 8))
		self.assertEqual(B.local_to_utc("2026-01-15T10:00", "Europe/Rome"), utc(2026, 1, 15, 9))
		self.assertEqual(B.local_to_utc("2026-09-25T10:00:00+00:00", "Europe/Rome"), utc(2026, 9, 25, 10))

	def test_booking_normalises(self):
		booking = B.ExternalBooking(
			external_id=" 42 ",
			start="2026-09-25T10:00:00Z",
			end="2026-09-25T09:00:00Z",
			email=" A@B.IT ",
			status="weird",
		)
		self.assertEqual(booking.external_id, "42")
		self.assertEqual(booking.email, "a@b.it")
		self.assertEqual(booking.status, B.STATUS_CONFIRMED)
		self.assertEqual(booking.end - booking.start, datetime.timedelta(minutes=30))

	def test_dig(self):
		data = {"a": {"b": [{"c": 1}, {"c": 2}]}}
		self.assertEqual(B.dig(data, "a.b.1.c"), 2)
		self.assertIsNone(B.dig(data, "a.x.c"))


ICS = """BEGIN:VCALENDAR\r
VERSION:2.0\r
X-WR-TIMEZONE:Europe/Rome\r
BEGIN:VEVENT\r
UID:tw-1001@treatwell\r
DTSTART;TZID=Europe/Rome:20260925T100000\r
DTEND;TZID=Europe/Rome:20260925T104500\r
SUMMARY:Maria Bianchi - Piega\r
DESCRIPTION:Tel: +39 333 123 4567\\nEmail: maria@example.com\\, grazie\r
BEGIN:VALARM\r
TRIGGER:-PT15M\r
DESCRIPTION:Reminder\r
END:VALARM\r
END:VEVENT\r
BEGIN:VEVENT\r
UID:tw-1002@treatwell\r
DTSTART:20260926T080000Z\r
DURATION:PT1H30M\r
STATUS:CANCELLED\r
SUMMARY:Colore (Giulia\r
  Verdi)\r
END:VEVENT\r
BEGIN:VEVENT\r
UID:holiday\r
DTSTART;VALUE=DATE:20261225\r
SUMMARY:Chiuso\r
END:VEVENT\r
END:VCALENDAR\r
"""


class TestICal(unittest.TestCase):
	def test_parse_feed(self):
		bookings = I.parse_feed(ICS)
		self.assertEqual([b.external_id for b in bookings], ["tw-1001@treatwell", "tw-1002@treatwell"])
		first, second = bookings
		self.assertEqual(first.start, utc(2026, 9, 25, 8))
		self.assertEqual(first.end, utc(2026, 9, 25, 8, 45))
		self.assertEqual(first.customer_name, "Maria Bianchi")
		self.assertEqual(first.service_name, "Piega")
		self.assertEqual(first.email, "maria@example.com")
		self.assertEqual(first.phone, "+393331234567")
		# the alarm's DESCRIPTION did not overwrite the event's
		self.assertIn("grazie", first.notes)
		self.assertEqual(second.status, B.STATUS_CANCELLED)
		self.assertEqual(second.end - second.start, datetime.timedelta(minutes=90))
		self.assertEqual(second.customer_name, "Colore")

	def test_window_filter(self):
		self.assertEqual(len(I.parse_feed(ICS, since=utc(2026, 9, 26))), 1)

	def test_not_a_feed(self):
		with self.assertRaises(B.PlatformError):
			I.parse_feed("<html>login</html>")

	def test_quoted_colon_in_params(self):
		name, params, value = I.split_line('ATTENDEE;CN="Dr. Rossi: studio":mailto:r@example.com')
		self.assertEqual(
			(name, params["CN"], value), ("ATTENDEE", "Dr. Rossi: studio", "mailto:r@example.com")
		)

	def test_attendee_gives_client(self):
		text = ICS.replace(
			"SUMMARY:Maria Bianchi - Piega",
			"SUMMARY:Visita\r\nORGANIZER:mailto:studio@example.com\r\nATTENDEE;CN=Luca Neri:mailto:luca@example.com",
		)
		first = I.parse_feed(text)[0]
		self.assertEqual((first.customer_name, first.email), ("Luca Neri", "maria@example.com"))


class TestEmailParser(unittest.TestCase):
	today = datetime.date(2026, 9, 20)

	def parse(self, subject, body, sender="notifiche@treatwell.it"):
		return E.parse_notification(subject, body, sender, "Europe/Rome", self.today)

	def test_treatwell_style_confirmation(self):
		booking = self.parse(
			"Nuova prenotazione: Piega e taglio",
			"""Hai ricevuto una nuova prenotazione!
			Cliente: Maria Bianchi
			Servizio: Piega e taglio
			Data: giovedì 25 settembre 2026
			Orario: 10:30 - 11:15
			Operatore: Sara
			Telefono: +39 333 123 4567
			Prezzo: € 45,00
			Codice prenotazione: TW-99812""",
		)
		self.assertEqual(booking.external_id, "TW-99812")
		self.assertEqual(booking.start, utc(2026, 9, 25, 8, 30))
		self.assertEqual(booking.end, utc(2026, 9, 25, 9, 15))
		self.assertEqual(booking.customer_name, "Maria Bianchi")
		self.assertEqual(booking.service_name, "Piega e taglio")
		self.assertEqual(booking.staff_name, "Sara")
		self.assertEqual(booking.phone, "+393331234567")
		self.assertEqual(booking.price, 45.0)
		self.assertEqual(booking.status, B.STATUS_CONFIRMED)
		self.assertNotIn("match_by_customer", booking.raw)

	def test_cancellation_without_reference(self):
		booking = self.parse(
			"Prenotazione annullata",
			"<p>La prenotazione di <b>Luca Neri</b> del 26/09/2026 alle ore 15.00 è stata annullata.</p><p>Email: luca@example.com</p>",
			"no-reply@fresha.com",
		)
		self.assertEqual(booking.status, B.STATUS_CANCELLED)
		self.assertEqual(booking.start, utc(2026, 9, 26, 13))
		self.assertEqual(booking.email, "luca@example.com")
		self.assertTrue(booking.raw["match_by_customer"])

	def test_moved_is_not_a_cancellation(self):
		booking = self.parse(
			"Appuntamento spostato",
			"Paziente: Anna Neri\nNuova data: 2026-10-01 alle 09:00\nIl vecchio appuntamento è stato cancellato.",
		)
		self.assertEqual(booking.status, B.STATUS_CONFIRMED)
		self.assertTrue(booking.raw["moved"])
		self.assertEqual(booking.start, utc(2026, 10, 1, 7))

	def test_english_and_duration(self):
		booking = self.parse(
			"Booking confirmed",
			"Customer: John Smith\nWhen: September 28, 2026 at 3:30 PM\nDuration: 1h 15min",
			"x@calendly.com",
		)
		self.assertEqual(booking.start, utc(2026, 9, 28, 13, 30))
		self.assertEqual(booking.end - booking.start, datetime.timedelta(minutes=75))

	def test_date_without_year_rolls_forward(self):
		booking = self.parse("Prenotazione", "Cliente: X\n3 gennaio alle 11:00", "a@elty.it")
		self.assertEqual(booking.start.date(), datetime.date(2027, 1, 3))

	def test_no_time_means_no_booking(self):
		self.assertIsNone(self.parse("Newsletter", "Promo di settembre 25/09/2026, sconti!"))

	def test_same_content_same_id(self):
		one = self.parse("Nuova prenotazione", "Cliente: A\n25/09/2026 ore 10:00")
		two = self.parse("Nuova prenotazione", "Cliente: A\n25/09/2026 ore 10:00")
		self.assertEqual(one.external_id, two.external_id)

	def test_sender_filter(self):
		provider = provider_class("Treatwell / Uala")(Conn())
		self.assertTrue(provider.sender_matches("Treatwell <noreply@mail.treatwell.it>"))
		self.assertFalse(provider.sender_matches("spam@example.com"))
		custom = provider_class("Treatwell / Uala")(Conn(sender_filter="salone.it"))
		self.assertTrue(custom.sender_matches("x@salone.it"))

	def test_email_webhook_json_and_form(self):
		provider = E.NotificationEmail(Conn())
		body = json.dumps(
			{"from": "a@b.it", "subject": "Nuova prenotazione", "text": "Cliente: A\n25/09/2026 ore 10:00"}
		).encode()
		self.assertEqual(len(provider.parse_webhook({"Content-Type": "application/json"}, body)), 1)
		form = b"sender=a%40b.it&subject=Prenotazione&body-plain=Cliente%3A+A%0A25%2F09%2F2026+ore+10%3A00"
		self.assertEqual(
			len(provider.parse_webhook({"Content-Type": "application/x-www-form-urlencoded"}, form)), 1
		)


class TestGenericWebhook(unittest.TestCase):
	def test_defaults(self):
		bookings = G.payload_to_bookings(
			{
				"id": 7,
				"start": "2026-09-25T10:00:00+02:00",
				"duration": 45,
				"status": "cancelled",
				"customer": {"first_name": "A", "last_name": "B"},
			}
		)
		self.assertEqual(bookings[0].customer_name, "A B")
		self.assertEqual(bookings[0].status, B.STATUS_CANCELLED)
		self.assertEqual(bookings[0].end - bookings[0].start, datetime.timedelta(minutes=45))

	def test_custom_map_and_list(self):
		payload = {
			"items": [
				{
					"ref": "x1",
					"when": {"from": "2026-09-25T08:00:00Z", "to": "2026-09-25T09:00:00Z"},
					"state": "RIFIUTATA",
				}
			]
		}
		bookings = G.payload_to_bookings(
			payload, {"list": "items", "id": "ref", "start": "when.from", "end": "when.to", "status": "state"}
		)
		self.assertEqual(bookings[0].external_id, "x1")
		self.assertEqual(bookings[0].status, B.STATUS_CANCELLED)

	def test_signature(self):
		body = b'{"id":1}'
		good = hmac.new(b"s3cret", body, hashlib.sha256).hexdigest()
		G.verify_generic_signature("s3cret", {"X-Hub-Signature-256": f"sha256={good}"}, body)
		with self.assertRaises(B.InvalidSignature):
			G.verify_generic_signature("s3cret", {"X-Signature": "nope"}, body)
		G.verify_generic_signature("", {}, body)  # no secret: the URL token is the credential


class TestSignatures(unittest.TestCase):
	def test_calendly(self):
		body = b'{"event":"invitee.created"}'
		t = str(int(time.time()))
		v1 = hmac.new(b"key", f"{t}.".encode() + body, hashlib.sha256).hexdigest()
		S.verify_calendly("key", {"Calendly-Webhook-Signature": f"t={t},v1={v1}"}, body)
		with self.assertRaises(B.InvalidSignature):
			S.verify_calendly("key", {"Calendly-Webhook-Signature": f"t={t},v1=00"}, body)
		old = str(int(time.time()) - 3600)
		v1_old = hmac.new(b"key", f"{old}.".encode() + body, hashlib.sha256).hexdigest()
		with self.assertRaises(B.InvalidSignature):
			S.verify_calendly("key", {"Calendly-Webhook-Signature": f"t={old},v1={v1_old}"}, body)

	def test_calcom(self):
		body = json.dumps(
			{
				"triggerEvent": "BOOKING_CANCELLED",
				"payload": {
					"uid": "u1",
					"startTime": "2026-09-25T08:00:00Z",
					"endTime": "2026-09-25T08:30:00Z",
					"attendees": [{"name": "A", "email": "a@x.it"}],
				},
			}
		).encode()
		provider = S.CalCom(Conn(webhook_secret="k"))
		signature = hmac.new(b"k", body, hashlib.sha256).hexdigest()
		bookings = provider.parse_webhook({"x-cal-signature-256": signature}, body)
		self.assertEqual((bookings[0].external_id, bookings[0].status), ("u1", B.STATUS_CANCELLED))
		with self.assertRaises(B.InvalidSignature):
			provider.parse_webhook({"x-cal-signature-256": "bad"}, body)

	def test_acuity_signature_is_base64(self):
		body = b"action=appointment.scheduled&id=1"
		expected = base64.b64encode(hmac.new(b"api", body, hashlib.sha256).digest()).decode()
		self.assertEqual(B.hmac_b64("api", body), expected)


class TestPlatformMappers(unittest.TestCase):
	def test_docplanner_booking_and_notification(self):
		item = {
			"id": "b1",
			"status": "booked",
			"start_at": "2026-09-25T10:00:00+02:00",
			"end_at": "2026-09-25T10:30:00+02:00",
			"patient": {"name": "Anna", "surname": "Neri", "email": "anna@x.it", "phone": "+39333"},
			"address_service": {"id": "s9", "name": "Prima visita", "price": 80},
			"comment": "mal di schiena",
		}
		booking = D.booking_from_docplanner(item, "d1", "a1")
		self.assertEqual(booking.external_id, "d1/a1/b1")
		self.assertEqual(booking.start, utc(2026, 9, 25, 8))
		self.assertEqual(
			(booking.customer_name, booking.service_ref, booking.price), ("Anna Neri", "s9", 80.0)
		)
		cancelled = D.bookings_from_notification(
			{
				"name": "booking-canceled",
				"data": {"doctor": {"id": "d1"}, "address": {"id": "a1"}, "visit_booking": item},
			}
		)
		self.assertEqual(cancelled[0].status, B.STATUS_CANCELLED)
		self.assertEqual(D.bookings_from_notification({"name": "break-created", "data": {}}), [])

	def test_docplanner_api_key_header(self):
		provider = D.Docplanner(Conn(webhook_secret="k"))
		with self.assertRaises(B.InvalidSignature):
			provider.parse_webhook({}, b"{}")
		self.assertEqual(provider.parse_webhook({"X-Api-Key": "k"}, b'{"name":"break-created"}'), [])

	def test_calcom_booking(self):
		booking = S.cal_to_booking(
			{
				"uid": "abc",
				"status": "pending",
				"start": "2026-09-25T08:00:00.000Z",
				"end": "2026-09-25T09:00:00.000Z",
				"eventTypeId": 12,
				"eventType": {"id": 12, "slug": "consulenza"},
				"hosts": [{"email": "doc@studio.it", "name": "Doc"}],
				"attendees": [{"name": "A", "email": "a@x.it", "phoneNumber": "+39 1"}],
			}
		)
		self.assertEqual(
			(booking.status, booking.service_ref, booking.staff_ref),
			(B.STATUS_PENDING, "12", "doc@studio.it"),
		)

	def test_calendly_booking(self):
		event = {
			"uri": "https://api.calendly.com/scheduled_events/EV1",
			"name": "Consulenza",
			"status": "active",
			"start_time": "2026-09-25T08:00:00.000000Z",
			"end_time": "2026-09-25T08:30:00.000000Z",
			"event_type": "https://api.calendly.com/event_types/ET1",
			"event_memberships": [
				{
					"user": "https://api.calendly.com/users/U1",
					"user_email": "doc@studio.it",
					"user_name": "Doc",
				}
			],
		}
		invitee = {
			"uri": "https://api.calendly.com/scheduled_events/EV1/invitees/IN1",
			"name": "A",
			"email": "a@x.it",
			"status": "active",
			"questions_and_answers": [{"question": "Telefono", "answer": "333"}],
		}
		booking = S.calendly_to_booking(invitee, event)
		self.assertEqual(booking.external_id, "EV1/IN1")
		self.assertEqual(
			(booking.service_ref, booking.staff_ref, booking.phone), ("ET1", "doc@studio.it", "333")
		)
		self.assertEqual(S.calendly_to_booking(invitee, event, canceled=True).status, B.STATUS_CANCELLED)

	def test_simplybook_local_times(self):
		booking = S.simplybook_to_booking(
			{
				"id": 5,
				"status": "canceled",
				"start_datetime": "2026-09-25 10:00:00",
				"end_datetime": "2026-09-25 11:00:00",
				"service_id": 3,
				"provider_id": 4,
				"client": {"name": "A", "email": "a@x.it", "phone": "1"},
				"service": {"name": "Massaggio", "price": "50"},
			},
			"Europe/Rome",
		)
		self.assertEqual(booking.start, utc(2026, 9, 25, 8))
		self.assertEqual(
			(booking.status, booking.service_ref, booking.staff_ref, booking.price),
			(B.STATUS_CANCELLED, "3", "4", 50.0),
		)

	def test_acuity_booking(self):
		booking = S.acuity_to_booking(
			{
				"id": 9,
				"datetime": "2026-09-25T10:00:00+0200",
				"duration": "45",
				"firstName": "A",
				"lastName": "B",
				"calendarID": 2,
				"appointmentTypeID": 3,
				"price": "30.00",
				"canceled": True,
			}
		)
		self.assertEqual(
			(booking.start, booking.end - booking.start),
			(utc(2026, 9, 25, 8), datetime.timedelta(minutes=45)),
		)
		self.assertEqual(booking.status, B.STATUS_CANCELLED)

	def test_msbookings_graph_times(self):
		booking = S.msbookings_to_booking(
			{
				"id": "AAMk",
				"startDateTime": {"dateTime": "2026-09-25T08:00:00.0000000", "timeZone": "UTC"},
				"endDateTime": {"dateTime": "2026-09-25T10:30:00.0000000", "timeZone": "Europe/Rome"},
				"staffMemberIds": ["st1"],
				"customers": [{"name": "A", "emailAddress": "a@x.it"}],
			}
		)
		self.assertEqual((booking.start, booking.end), (utc(2026, 9, 25, 8), utc(2026, 9, 25, 8, 30)))

	def test_booksy_naive_local_times_and_reservations(self):
		item = {
			"id": 1,
			"booked_from": "2026-09-25T10:00",
			"booked_till": "2026-09-25T10:45",
			"status": "N",
			"type": "C",
			"business_timezone": "Europe/Rome",
			"customer_name": "A",
			"subbookings": [{"staffer_id": 456, "service_variant_id": 789, "service_name": "Taglio"}],
		}
		booking = S.booksy_to_booking(item)
		self.assertEqual(
			(booking.start, booking.status, booking.staff_ref), (utc(2026, 9, 25, 8), B.STATUS_NO_SHOW, "456")
		)
		self.assertIsNone(S.booksy_to_booking({**item, "type": "R"}))

	def test_timify_and_setmore(self):
		timify = S.timify_to_booking(
			{
				"id": "t1",
				"from": "2026-09-25T08:00:00Z",
				"duration": 20,
				"resources": [{"id": "r1"}],
				"customers": [{"firstName": "A", "lastName": "B"}],
			}
		)
		self.assertEqual(
			(timify.end - timify.start, timify.staff_ref, timify.customer_name),
			(datetime.timedelta(minutes=20), "r1", "A B"),
		)
		setmore = S.setmore_to_booking(
			{
				"key": "k1",
				"start_time": "2026-09-25T08:00Z",
				"end_time": "2026-09-25T08:30Z",
				"label": "Cancelled",
				"customer": {"first_name": "A"},
			}
		)
		self.assertEqual(setmore.status, B.STATUS_CANCELLED)


if __name__ == "__main__":
	unittest.main()
