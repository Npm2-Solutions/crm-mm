# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""An event's reminder on the screen reaches only whom the event is for (doc 43).

Dott.ssa Neri's appointment with Anna Bianchi has its calendar copy: a private
Event, its subject the service and the person, its description the appointment's
notes. When its reminder is due it appears on Dott.ssa Neri's screen and on Dott.
Verdi's, who is on it too, each in their own room, without the notes. It went to
the site's room, which every desk user's browser joins - the reception,
marketing, the other professionals, the agency - with the notes, and each browser
kept them. A colleague who left, the patient's area and an address of nobody's
get nothing.

By email it goes to the centre's users only, never to the patient's address on
the copy. Like the screen's, it never says the description; of an appointment's
copy, whose title is the service and the person, it says only that it is an
appointment, and when.

An all-day event's reminder leaves at its hour: the database gives the hour as a
span since midnight, and the round failed on it.
"""

import datetime
import html
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, now_datetime

from crm.api import event as E

NOTE = "Dolore lombare, peggiora la sera"
OGGETTO = "Fisioterapia — Anna Bianchi"
PAZIENTE = "anna.bianchi@example.com"


def _utente(email: str, tipo: str = "System User", **campi) -> str:
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
	# the kind of user said here, whatever the roles would make of it
	frappe.db.set_value("User", email, {"user_type": tipo, "enabled": 1, **campi}, update_modified=False)
	return email


class GliAvvisiDegliEventi(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.neri = _utente("avviso.neri@example.com")
		self.verdi = _utente("avviso.verdi@example.com")
		self.andata_via = _utente("avviso.andata.via@example.com", enabled=0)
		self.area = _utente("avviso.area@example.com", "Website User")
		self.mandati = []
		emetti = patch(
			"frappe.realtime.emit_via_redis",
			side_effect=lambda evento, messaggio, stanza: self.mandati.append((evento, messaggio, stanza)),
		)
		emetti.start()
		self.addCleanup(emetti.stop)
		# the reminders of the centre and of other tests' events are not these tests'
		frappe.db.delete("Event Notifications", {"parenttype": ["in", ["Event", "FCRM Settings"]]})

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def evento(self, inizio, promemoria, proprietario=None, partecipanti=(), **campi) -> str:
		"""An event at ``inizio`` with its own ``promemoria``, whose ``proprietario`` it is
		(the session's where none), with these users on it and Anna Bianchi by her address."""
		evento = frappe.get_doc(
			{
				"doctype": "Event",
				"subject": OGGETTO,
				"description": NOTE,
				"event_type": "Private",
				"starts_on": inizio,
				"ends_on": add_to_date(inizio, minutes=45),
				"notifications": promemoria,
				"event_participants": [
					*(
						{"reference_doctype": "User", "reference_docname": u, "email": u}
						for u in partecipanti
					),
					{
						"reference_doctype": "CRM Lead",
						"reference_docname": "CRM-LEAD-FINTO",
						"email": PAZIENTE,
					},
				],
				**campi,
			}
		).insert(ignore_permissions=True, ignore_links=True)
		if proprietario:
			frappe.db.set_value("Event", evento.name, "owner", proprietario, update_modified=False)
		return evento.name

	def giri(self, interval, *quando):
		"""The round of ``interval`` at each of these moments: (to, subject, message) of
		every email it handed over. What it could not do fails the test."""
		email = []

		def manda(**kwargs):
			email.append((tuple(kwargs["recipients"]), kwargs["subject"], kwargs["message"]))

		with (
			patch.object(E.frappe, "sendmail", side_effect=manda),
			patch.object(E.frappe, "log_error", side_effect=AssertionError("the round logged an error")),
		):
			for momento in quando:
				with patch.object(E, "now_datetime", return_value=momento):
					E._process_event_notifications_by_interval(interval)
		return email

	def avvisi(self, evento=None):
		"""(room, message) of every reminder sent, of one event where it is given."""
		return [
			(stanza, messaggio)
			for nome, messaggio, stanza in self.mandati
			if nome == "event_notification" and (evento is None or messaggio.get("event_name") == evento)
		]

	def stanze(self, evento=None):
		return sorted(stanza for stanza, _messaggio in self.avvisi(evento))

	def senza_note(self, avvisi):
		self.assertTrue(avvisi)
		for _stanza, messaggio in avvisi:
			self.assertNotIn("description", messaggio)
			self.assertNotIn(NOTE, frappe.as_json(messaggio))
			self.assertEqual(messaggio["subject"], OGGETTO)

	def test_a_chi_e_l_evento_ognuno_nella_sua_stanza(self):
		inizio = add_to_date(now_datetime(), minutes=10)
		E._send_system_notification(
			frappe._dict(
				{
					"event_name": "EV-AVVISO-1",
					"subject": OGGETTO,
					"description": NOTE,
					"starts_on": inizio,
					"ends_on": add_to_date(inizio, minutes=45),
					"all_day_event": 0,
					"owner": self.neri,
					"event_participants": [
						self.verdi,
						self.andata_via,
						self.area,
						"anna.bianchi@example.com",
						self.neri,
					],
					"notification_type": "Notification",
					"before_value": 10,
				}
			)
		)
		self.assertEqual(self.stanze(), [f"user:{self.neri}", f"user:{self.verdi}"])
		self.senza_note(self.avvisi())
		# what the popup draws: who it is for, when
		_stanza, messaggio = self.avvisi()[0]
		self.assertEqual(messaggio["event_name"], "EV-AVVISO-1")
		self.assertEqual(messaggio["owner"], self.neri)
		self.assertIn(self.verdi, messaggio["event_participants"])

	def test_administrator_anche_dalla_sua_email(self):
		# the event keeps its participants by email, and Administrator's name is not one
		email = frappe.db.get_value("User", "Administrator", "email")
		if not email:
			self.skipTest("Administrator has no email on this site")
		E._send_system_notification(
			{
				"event_name": "EV-AVVISO-2",
				"subject": OGGETTO,
				"owner": self.neri,
				"event_participants": [email],
			}
		)
		self.assertEqual(self.stanze(), ["user:Administrator", f"user:{self.neri}"])

	def test_un_evento_di_nessuno_del_centro_non_va_a_nessuno(self):
		E._send_system_notification(
			{
				"event_name": "EV-AVVISO-3",
				"subject": OGGETTO,
				"description": NOTE,
				"owner": "Guest",
				"event_participants": ["anna.bianchi@example.com", self.area],
			}
		)
		# to nobody, not to everybody
		self.assertEqual(self.avvisi(), [])

	def test_dal_giro_dei_promemoria(self):
		# the round finds the events of the user it runs as (the scheduler's
		# Administrator): one of theirs, with Dott. Verdi on it, due now
		inizio = add_to_date(now_datetime(), minutes=10)
		evento = frappe.get_doc(
			{
				"doctype": "Event",
				"subject": OGGETTO,
				"description": NOTE,
				"event_type": "Private",
				"starts_on": inizio,
				"ends_on": add_to_date(inizio, minutes=45),
				"notifications": [{"type": "Notification", "before": 10, "interval": "minutes"}],
				"event_participants": [
					{"reference_doctype": "User", "reference_docname": self.verdi, "email": self.verdi},
					{"reference_doctype": "User", "reference_docname": self.area, "email": self.area},
				],
			}
		).insert(ignore_permissions=True)
		E._process_event_notifications_by_interval("minutes")
		self.assertEqual(self.stanze(evento.name), ["user:Administrator", f"user:{self.verdi}"])
		self.senza_note(self.avvisi(evento.name))
		# nothing of any event to the site's room, the reception's browser among them
		self.assertNotIn("all", [stanza for _nome, _messaggio, stanza in self.mandati])

	def test_un_evento_di_tutto_il_giorno_alla_sua_ora(self):
		# the centre's reminder of all-day events, the day before at an hour: the time
		# came from the database as a span since midnight, and the round failed on it
		adesso = now_datetime().replace(microsecond=0)
		domani = datetime.datetime.combine(adesso.date() + datetime.timedelta(days=1), datetime.time())
		frappe.db.delete("Event Notifications", {"parenttype": "FCRM Settings"})
		frappe.get_doc(
			{
				"doctype": "Event Notifications",
				"parenttype": "FCRM Settings",
				"parentfield": "all_day_event_notifications",
				"parent": "FCRM Settings",
				"type": "Notification",
				"before": 1,
				"interval": "days",
				"time": adesso.strftime("%H:%M:%S"),
			}
		).db_insert()
		evento = frappe.get_doc(
			{
				"doctype": "Event",
				"subject": OGGETTO,
				"event_type": "Private",
				"all_day": 1,
				"starts_on": domani,
				"ends_on": domani.replace(hour=23, minute=59),
			}
		).insert(ignore_permissions=True)
		with (
			patch.object(E, "now_datetime", return_value=adesso),
			patch.object(E.frappe, "log_error", side_effect=AssertionError("the round failed")),
		):
			E._process_event_notifications_by_interval("days")
		self.assertEqual(self.stanze(evento.name), ["user:Administrator"])

	# ------------------------------------------------------------------ by email

	def test_la_copia_di_un_appuntamento_non_dice_cosa_ne_chi(self):
		adesso = now_datetime().replace(microsecond=0)
		inizio = add_to_date(adesso, hours=1)
		self.evento(
			inizio,
			[{"type": "Email", "before": 1, "interval": "hours"}],
			partecipanti=[self.verdi],
			reference_doctype="CRM Appointment",
			reference_docname="APPT-FINTO",
		)
		email = self.giri("hours", adesso)
		# to Dott. Verdi: never Administrator, never the patient's address on the copy
		self.assertEqual([a for a, _oggetto, _testo in email], [(self.verdi,)])
		_a, oggetto, testo = email[0]
		# the service and the person are its title, the notes its description
		for parola in ("Fisioterapia", "Anna Bianchi", NOTE):
			self.assertNotIn(parola, oggetto)
			self.assertNotIn(parola, testo)
		self.assertIn(inizio.strftime("%H:%M"), oggetto)

	def test_un_evento_dice_il_suo_titolo_mai_la_descrizione(self):
		adesso = now_datetime().replace(microsecond=0)
		inizio = add_to_date(adesso, minutes=10)
		self.evento(
			inizio,
			[{"type": "Email", "before": 10, "interval": "minutes"}],
			partecipanti=[self.verdi, self.andata_via, self.area],
			subject="Riunione d'équipe",
		)
		email = self.giri("minutes", adesso)
		# the centre's users only: not who left, not the area, not the patient
		self.assertEqual([a for a, _oggetto, _testo in email], [(self.verdi,)])
		_a, oggetto, testo = email[0]
		# its title, when and where to open it, as on the screen; never its description
		self.assertIn("Riunione d'équipe", oggetto)
		self.assertIn("Riunione d'équipe", html.unescape(testo))
		self.assertNotIn(NOTE, testo)
		self.assertIn(inizio.strftime("%H:%M"), testo)
		self.assertIn(f"/crm/calendar?date={inizio.date().isoformat()}", testo)

	def test_i_promemoria_del_centro_anche_per_email(self):
		# the centre's reminders were handed over as plain dicts, which the email read
		# by attribute: it failed every time
		adesso = now_datetime().replace(microsecond=0)
		frappe.get_doc(
			{
				"doctype": "Event Notifications",
				"parenttype": "FCRM Settings",
				"parentfield": "event_notifications",
				"parent": "FCRM Settings",
				"type": "Email",
				"before": 10,
				"interval": "minutes",
			}
		).db_insert()
		self.evento(add_to_date(adesso, minutes=10), [], partecipanti=[self.verdi])
		email = self.giri("minutes", adesso)
		self.assertEqual([a for a, _oggetto, _testo in email], [(self.verdi,)])
