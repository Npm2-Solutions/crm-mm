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
"""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, now_datetime

from crm.api import event as E

NOTE = "Dolore lombare, peggiora la sera"
OGGETTO = "Fisioterapia — Anna Bianchi"


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

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

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
