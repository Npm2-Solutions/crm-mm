# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""An event's reminder reaches whom the event is for, and each leaves once (doc 43).

Dott.ssa Neri's appointment with Anna Bianchi has its calendar copy: a private
Event, its subject the service and the person, its description the appointment's
notes. When its reminder is due it appears on Dott.ssa Neri's screen and on Dott.
Verdi's, who is on it too, each in their own room, without the notes. It went to
the site's room, which every desk user's browser joins - the reception,
marketing, the other professionals, the agency - with the notes, and each browser
kept them. A colleague who left, the patient's area and an address of nobody's
get nothing.

The round runs as the scheduler's Administrator, and it looked only at the events
of the user it ran as: Dott.ssa Neri never had the reminders of her own events.
Now it looks at everybody's, and an email leaves once, however many rounds fall in
its window: each is written in the register before it leaves. Like the screen's, it
never says the description; of an appointment's copy, whose title is the service
and the person, it says only that it is an appointment. A client-area account with
the address of a person on the event gets nothing, on the screen or by email.

An all-day event's reminder leaves at its hour: the database gives the hour as a
span since midnight, and the round failed on it.
"""

import datetime
import html
import unittest
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, now_datetime

from crm.api import event as E
from crm.demo import guardie

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


class LeRegoleDeiPromemoria(unittest.TestCase):
	"""What the round decides without a site: the register's key, how far it looks,
	when a reminder is due."""

	def test_la_stessa_chiave_lo_stesso_nome(self):
		inizio = datetime.datetime(2026, 10, 12, 10, 30)
		nome = E.nome_del_promemoria("EV00001", "a1b2c3", "neri@example.com", "Email", inizio)
		self.assertEqual(len(nome), 32)
		# the time as the database gives it back, or written
		self.assertEqual(
			nome,
			E.nome_del_promemoria(
				"EV00001", "a1b2c3", "neri@example.com", "Email", "2026-10-12 10:30:00.000000"
			),
		)
		# each part counts: another recipient, another reminder, another time
		for altra in (
			("EV00001", "a1b2c3", "verdi@example.com", "Email", inizio),
			("EV00001", "d4e5f6", "neri@example.com", "Email", inizio),
			("EV00001", "a1b2c3", "neri@example.com", "Email", inizio + datetime.timedelta(hours=2)),
			("EV00002", "a1b2c3", "neri@example.com", "Email", inizio),
		):
			self.assertNotEqual(nome, E.nome_del_promemoria(*altra))

	def test_fin_dove_guarda(self):
		adesso = datetime.datetime(2026, 10, 12, 9, 0)
		# ten minutes ahead: a reminder is never due before its time
		self.assertEqual(E.fin_dove_cercare(adesso, "minutes", 10), datetime.datetime(2026, 10, 12, 9, 10))
		self.assertEqual(E.fin_dove_cercare(adesso, "hours", 2), datetime.datetime(2026, 10, 12, 11, 0))
		# an all-day event is reminded at an hour of its day before: a day more
		self.assertEqual(E.fin_dove_cercare(adesso, "days", 1), datetime.datetime(2026, 10, 14, 9, 0))
		self.assertEqual(E.fin_dove_cercare(adesso, "weeks", 1), datetime.datetime(2026, 10, 20, 9, 0))

	def test_quando_parte(self):
		inizio = datetime.datetime(2026, 10, 12, 10, 0)
		fine = datetime.datetime(2026, 10, 12, 10, 45)
		ora = datetime.datetime(2026, 10, 12, 9, 50)
		# from its time to five minutes after it, never before it
		self.assertTrue(E.e_il_momento(ora, ora, inizio, fine, "minutes"))
		self.assertTrue(E.e_il_momento(ora + datetime.timedelta(minutes=4), ora, inizio, fine, "minutes"))
		self.assertFalse(E.e_il_momento(ora + datetime.timedelta(minutes=6), ora, inizio, fine, "minutes"))
		self.assertFalse(E.e_il_momento(ora - datetime.timedelta(minutes=4), ora, inizio, fine, "minutes"))
		# under way, its time long gone: a round that did not run then
		self.assertTrue(E.e_il_momento(inizio + datetime.timedelta(minutes=20), ora, inizio, fine, "minutes"))
		self.assertFalse(E.e_il_momento(fine, ora, inizio, fine, "minutes"))
		# an event with no end is never under way
		self.assertFalse(
			E.e_il_momento(inizio + datetime.timedelta(minutes=20), ora, inizio, None, "minutes")
		)
		# on the screen only: an email under way would say it starts in ten minutes
		self.assertFalse(
			E.e_il_momento(
				inizio + datetime.timedelta(minutes=20), ora, inizio, fine, "minutes", in_corso=False
			)
		)
		self.assertTrue(E.e_il_momento(ora, ora, inizio, fine, "minutes", in_corso=False))

	def test_mai_prima_della_sua_ora(self):
		# «1 hour before» a visit at 11 is due at 10: the window went as far before its
		# time as after it, and the one email the register lets leave left at 9
		inizio = datetime.datetime(2026, 10, 13, 11, 0)
		fine = datetime.datetime(2026, 10, 13, 11, 45)
		ora = datetime.datetime(2026, 10, 13, 10, 0)
		for prima in (55, 30, 1):
			momento = ora - datetime.timedelta(minutes=prima)
			self.assertFalse(E.e_il_momento(momento, ora, inizio, fine, "hours"), momento)
		self.assertTrue(E.e_il_momento(ora, ora, inizio, fine, "hours"))
		self.assertTrue(E.e_il_momento(ora + datetime.timedelta(minutes=56), ora, inizio, fine, "hours"))
		# «1 day before» a visit at ten, at ten the day before: not seven hours early
		domani = datetime.datetime(2026, 10, 14, 10, 0)
		fine = domani + datetime.timedelta(minutes=45)
		self.assertFalse(E.e_il_momento(datetime.datetime(2026, 10, 13, 3, 0), ora, domani, fine, "days"))
		self.assertTrue(E.e_il_momento(ora, ora, domani, fine, "days"))

	def test_il_registro_non_va_nell_archivio_del_centro(self):
		# keys only: nothing a centre needs elsewhere (crm/esportazione)
		from crm.esportazione import regole

		self.assertEqual(regole.da_esportare([{"name": E.REGISTRO, "module_app": "crm"}]), [])


class GliAvvisiDegliEventi(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		# each reads their reminders in their own language, whatever the site's
		self.neri = _utente("avviso.neri@example.com", language="it")
		self.verdi = _utente("avviso.verdi@example.com", language="en")
		self.andata_via = _utente("avviso.andata.via@example.com", enabled=0)
		self.area = _utente("avviso.area@example.com", "Website User")
		self.mandati = []
		emetti = patch(
			"frappe.realtime.emit_via_redis",
			side_effect=lambda evento, messaggio, stanza: self.mandati.append((evento, messaggio, stanza)),
		)
		emetti.start()
		self.addCleanup(emetti.stop)
		# what the round could not do is a failure here, not a row in the Error Log
		errore = patch.object(E.frappe, "log_error", side_effect=AssertionError("the round logged an error"))
		errore.start()
		self.addCleanup(errore.stop)
		# the events of a minute ago, of the centre and of the other tests, are not these tests'
		frappe.db.delete("Event Notifications", {"parenttype": ["in", ["Event", "FCRM Settings"]]})

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
		every email it handed over."""
		return [
			(a, oggetto, testo)
			for _momento, a, oggetto, testo in self.nei_giri(
				*(
					(lambda: E._process_event_notifications_by_interval(interval), momento)
					for momento in quando
				)
			)
		]

	def nei_giri(self, *giri):
		"""Each (job, moment) run at its moment: (moment, to, subject, message) of every
		email they handed over."""
		email = []
		adesso = None

		def manda(**kwargs):
			email.append((adesso, tuple(kwargs["recipients"]), kwargs["subject"], kwargs["message"]))

		with patch.object(E.frappe, "sendmail", side_effect=manda):
			for lavoro, adesso in giri:
				with patch.object(E, "now_datetime", return_value=adesso):
					lavoro()
		return email

	def lo_scheduler(self, *momenti):
		"""The reminders' jobs as the hooks schedule them, at these moments: the round of
		every few minutes at each, the hourly one on the hour, the daily one at
		midnight, the weekly one at Sunday's midnight. (moment, to, subject, message) of
		every email they handed over."""
		lavori = frappe.get_hooks("scheduler_events", app_name="crm")

		def di(frequenza):
			return [
				frappe.get_attr(metodo)
				for metodo in lavori.get(frequenza, [])
				if metodo.startswith("crm.api.event.")
			]

		giri = []
		for momento in momenti:
			fanno = di("all")
			if momento.minute == 0:
				fanno += di("hourly")
				if momento.hour == 0:
					fanno += di("daily")
					if momento.weekday() == 6:
						fanno += di("weekly")
			giri += [(lavoro, momento) for lavoro in fanno]
		return self.nei_giri(*giri)

	def registrati(self, evento):
		return sorted(
			(r.recipient, r.channel)
			for r in frappe.get_all(
				"CRM Event Reminder", filters={"event": evento}, fields=["recipient", "channel"]
			)
		)

	# ------------------------------------------------------------------ on the screen

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
						PAZIENTE,
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
				"event_participants": [PAZIENTE, self.area],
			}
		)
		# to nobody, not to everybody
		self.assertEqual(self.avvisi(), [])

	def test_dal_giro_dei_promemoria(self):
		# one of Administrator's, the user the round runs as, with Dott. Verdi on it, due now
		inizio = add_to_date(now_datetime(), minutes=10)
		evento = self.evento(
			inizio,
			[{"type": "Notification", "before": 10, "interval": "minutes"}],
			partecipanti=[self.verdi, self.area],
		)
		E._process_event_notifications_by_interval("minutes")
		self.assertEqual(self.stanze(evento), ["user:Administrator", f"user:{self.verdi}"])
		self.senza_note(self.avvisi(evento))
		# nothing of any event to the site's room, the reception's browser among them
		self.assertNotIn("all", [stanza for _nome, _messaggio, stanza in self.mandati])

	def test_anche_gli_eventi_di_chi_non_e_administrator(self):
		# Dott.ssa Neri's own event: the round, as Administrator, used to skip it
		inizio = add_to_date(now_datetime(), minutes=10)
		evento = self.evento(
			inizio,
			[{"type": "Notification", "before": 10, "interval": "minutes"}],
			proprietario=self.neri,
			partecipanti=[self.verdi],
		)
		E._process_event_notifications_by_interval("minutes")
		self.assertEqual(self.stanze(evento), [f"user:{self.neri}", f"user:{self.verdi}"])

	# ------------------------------------------------------------------ by email, once

	def test_l_email_parte_una_volta_sola(self):
		adesso = now_datetime().replace(microsecond=0)
		inizio = add_to_date(adesso, minutes=10)
		evento = self.evento(
			inizio,
			[{"type": "Email", "before": 10, "interval": "minutes"}],
			proprietario=self.neri,
			partecipanti=[self.verdi, self.andata_via, self.area],
			subject="Riunione d'équipe",
		)
		# three rounds inside its window of five minutes either side, one after it
		email = self.giri(
			"minutes",
			add_to_date(adesso, minutes=-3),
			adesso,
			add_to_date(adesso, minutes=4),
			add_to_date(adesso, minutes=8),
		)
		# once each, to whom the event is for: never the patient, the area, who left
		self.assertEqual(sorted(a for a, _oggetto, _testo in email), [(self.neri,), (self.verdi,)])
		self.assertEqual(self.registrati(evento), [(self.neri, "Email"), (self.verdi, "Email")])
		per_chi = {a: (oggetto, html.unescape(testo)) for (a,), oggetto, testo in email}
		# its title, when, how long to it and where to open it, in each one's language;
		# never its description, as on the screen
		self.assertEqual(per_chi[self.neri][0], "Promemoria: Riunione d'équipe")
		self.assertEqual(per_chi[self.verdi][0], "Reminder: Riunione d'équipe")
		self.assertIn("Inizia tra 10 minuti.", per_chi[self.neri][1])
		self.assertIn("It starts in 10 minutes.", per_chi[self.verdi][1])
		for _oggetto, testo in per_chi.values():
			self.assertIn("Riunione d'équipe", testo)
			self.assertNotIn(NOTE, testo)
			self.assertIn(inizio.strftime("%H:%M"), testo)
			self.assertIn(f"/crm/calendar?date={inizio.date().isoformat()}", testo)
		# a round of the same window once more: it is written down already
		self.assertEqual(self.giri("minutes", adesso), [])

	def test_la_copia_di_un_appuntamento_non_dice_cosa_ne_chi(self):
		adesso = now_datetime().replace(microsecond=0)
		inizio = add_to_date(adesso, hours=1)
		evento = self.evento(
			inizio,
			[{"type": "Email", "before": 1, "interval": "hours"}],
			proprietario=self.neri,
			reference_doctype="CRM Appointment",
			reference_docname="APPT-FINTO",
		)
		email = self.giri("hours", adesso)
		self.assertEqual([a for a, _oggetto, _testo in email], [(self.neri,)])
		_a, oggetto, testo = email[0]
		# the service and the person are its title, the notes its description: only
		# that it is an appointment, and when
		for parola in ("Fisioterapia", "Anna Bianchi", NOTE):
			self.assertNotIn(parola, oggetto)
			self.assertNotIn(parola, testo)
		# its sentence in her language, as the bench's compiled catalogue has it: a new
		# sentence reads «Promemoria: appuntamento di …» once the catalogue is built
		from crm.notifiche.posta import nella_lingua_di

		with nella_lingua_di(self.neri):
			frase = frappe._("Reminder: appointment on {0}")
		self.assertTrue(oggetto.startswith(frase.split("{0}")[0]), oggetto)
		self.assertIn(inizio.strftime("%H:%M"), oggetto)
		self.assertIn("<b>Appuntamento</b>", testo)
		self.assertIn("Inizia tra un'ora.", html.unescape(testo))
		self.assertEqual(self.registrati(evento), [(self.neri, "Email")])

	def test_l_account_dell_area_con_l_email_di_un_partecipante_non_riceve_niente(self):
		# Anna Bianchi put on an event by her address book entry: the framework writes
		# the entry's email on her row (`set_participants_email`), and her client-area
		# account has that address. A reminder is for the centre's people, never hers:
		# on the screen and by email, only to enabled System Users
		cliente = _utente("avviso.anna.area@example.com", "Website User")
		contatto = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "Anna",
				"last_name": "Bianchi",
				"email_ids": [{"email_id": cliente, "is_primary": 1}],
			}
		).insert(ignore_permissions=True)
		adesso = now_datetime().replace(microsecond=0)
		evento = frappe.get_doc(
			{
				"doctype": "Event",
				"subject": OGGETTO,
				"description": NOTE,
				"event_type": "Private",
				"starts_on": add_to_date(adesso, minutes=10),
				"ends_on": add_to_date(adesso, minutes=55),
				"notifications": [
					{"type": "Email", "before": 10, "interval": "minutes"},
					{"type": "Notification", "before": 10, "interval": "minutes"},
				],
				"event_participants": [{"reference_doctype": "Contact", "reference_docname": contatto.name}],
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value("Event", evento.name, "owner", self.neri, update_modified=False)
		# the framework wrote her address on her row
		self.assertEqual([riga.email for riga in evento.event_participants], [cliente])
		email = self.giri("minutes", adesso)
		self.assertEqual([a for a, _oggetto, _testo in email], [(self.neri,)])
		self.assertEqual(self.stanze(evento.name), [f"user:{self.neri}"])
		self.assertEqual(self.registrati(evento.name), [(self.neri, "Email")])

	def test_gli_eventi_di_administrator_come_prima(self):
		# its owner reads it on the screen, never by email; Dott. Verdi gets both
		adesso = now_datetime().replace(microsecond=0)
		evento = self.evento(
			add_to_date(adesso, minutes=10),
			[
				{"type": "Email", "before": 10, "interval": "minutes"},
				{"type": "Notification", "before": 10, "interval": "minutes"},
			],
			partecipanti=[self.verdi],
		)
		email = self.giri("minutes", adesso, add_to_date(adesso, minutes=4))
		self.assertEqual([a for a, _oggetto, _testo in email], [(self.verdi,)])
		self.assertIn("user:Administrator", self.stanze(evento))
		self.assertIn(f"user:{self.verdi}", self.stanze(evento))

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

	def test_un_evento_spostato_si_ricorda_di_nuovo(self):
		adesso = now_datetime().replace(microsecond=0)
		evento = self.evento(
			add_to_date(adesso, minutes=10),
			[{"type": "Email", "before": 10, "interval": "minutes"}],
			proprietario=self.neri,
		)
		self.assertEqual(len(self.giri("minutes", adesso)), 1)
		# moved two hours on: its reminder is of the new time, and leaves again then
		nuovo = add_to_date(adesso, hours=2, minutes=10)
		frappe.db.set_value(
			"Event",
			evento,
			{"starts_on": nuovo, "ends_on": add_to_date(nuovo, minutes=45)},
			update_modified=False,
		)
		self.assertEqual(self.giri("minutes", adesso), [])
		self.assertEqual(len(self.giri("minutes", add_to_date(adesso, hours=2))), 1)
		self.assertEqual(len(self.registrati(evento)), 2)

	def test_due_giri_insieme_lo_scrivono_una_volta(self):
		# this round and the hourly one both take the hours: the database takes the
		# second one's row as already there, even when it did not see it before
		adesso = now_datetime().replace(microsecond=0)
		evento = self.evento(
			add_to_date(adesso, minutes=10),
			[{"type": "Email", "before": 10, "interval": "minutes"}],
			proprietario=self.neri,
		)
		riga = frappe.get_all(
			"Event Notifications", filters={"parent": evento}, fields=["name"], pluck="name"
		)[0]
		promemoria = frappe._dict(
			event_name=evento, reminder=riga, starts_on=frappe.db.get_value("Event", evento, "starts_on")
		)
		self.assertTrue(E._segna(promemoria, self.neri))
		esiste = frappe.db.exists

		def non_l_ha_visto(doctype, *args, **kwargs):
			return False if doctype == E.REGISTRO else esiste(doctype, *args, **kwargs)

		with patch.object(E.frappe.db, "exists", side_effect=non_l_ha_visto):
			self.assertFalse(E._segna(promemoria, self.neri))
		self.assertEqual(self.registrati(evento), [(self.neri, "Email")])

	def test_l_evento_si_toglie_anche_dopo_il_suo_promemoria(self):
		# an appointment cancelled takes its calendar copy away (`remove_event`): the
		# reminder written down does not hold it (`ignore_links_on_delete`)
		adesso = now_datetime().replace(microsecond=0)
		evento = self.evento(
			add_to_date(adesso, minutes=10),
			[{"type": "Email", "before": 10, "interval": "minutes"}],
			proprietario=self.neri,
		)
		self.giri("minutes", adesso)
		self.assertEqual(len(self.registrati(evento)), 1)
		# the hooks as this code says them, not as the site's cache keeps them
		with patch.dict(frappe.local.conf, {"developer_mode": 1}):
			frappe.delete_doc("Event", evento, ignore_permissions=True, delete_permanently=True)
		self.assertFalse(frappe.db.exists("Event", evento))

	def test_il_registro_si_svuota_dopo_l_evento(self):
		# Log Settings' retention: an event that started three months ago is looked at
		# by no round, unless it is still under way
		from crm.fcrm.doctype.crm_event_reminder.crm_event_reminder import CRMEventReminder

		adesso = now_datetime().replace(microsecond=0)
		for giorni in (100, 1):
			frappe.get_doc(
				{
					"doctype": E.REGISTRO,
					"event": "EV-REGISTRO",
					"reminder": f"riga-{giorni}",
					"recipient": self.neri,
					"channel": E.EMAIL,
					"starts_on": add_to_date(adesso, days=-giorni),
				}
			).insert(ignore_permissions=True, ignore_links=True)
		CRMEventReminder.clear_old_logs(days=90)
		self.assertEqual(
			frappe.get_all(E.REGISTRO, filters={"event": "EV-REGISTRO"}, pluck="reminder"), ["riga-1"]
		)

	def test_un_evento_di_tutto_il_giorno_alla_sua_ora(self):
		# the centre's reminder of all-day events, the day before at an hour: the time
		# came from the database as a span since midnight, and the round failed on it
		adesso = now_datetime().replace(microsecond=0)
		domani = datetime.datetime.combine(adesso.date() + datetime.timedelta(days=1), datetime.time())
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
		with patch.object(E, "now_datetime", return_value=adesso):
			E._process_event_notifications_by_interval("days")
		self.assertEqual(self.stanze(evento.name), ["user:Administrator"])

	def test_i_promemoria_del_centro_per_tutto_il_giorno(self):
		# the centre's: the day before at an hour, for an all-day event that has none
		# of its own (the time came from the database as a span, and the round failed)
		adesso = now_datetime().replace(microsecond=0)
		domani = datetime.datetime.combine(adesso.date() + datetime.timedelta(days=1), datetime.time())
		frappe.get_doc(
			{
				"doctype": "Event Notifications",
				"parenttype": "FCRM Settings",
				"parentfield": "all_day_event_notifications",
				"parent": "FCRM Settings",
				"type": "Email",
				"before": 1,
				"interval": "days",
				"time": adesso.strftime("%H:%M:%S"),
			}
		).db_insert()
		evento = self.evento(domani, [], proprietario=self.neri, all_day=1)
		frappe.db.set_value(
			"Event", evento, "ends_on", domani.replace(hour=23, minute=59), update_modified=False
		)
		email = self.giri("days", adesso, add_to_date(adesso, hours=1))
		self.assertEqual([a for a, _oggetto, _testo in email], [(self.neri,)])
		self.assertEqual(self.registrati(evento), [(self.neri, "Email")])

	# ------------------------------------------------------------------ at its time

	def test_un_ora_prima_parte_alla_sua_ora(self):
		# «1 hour before» a visit, as the scheduler runs the rounds: at its hour. The
		# window went an hour before it as well, and the one email the register lets
		# leave left at its start: two hours before, «It starts in an hour.»
		ora = now_datetime().replace(minute=0, second=0, microsecond=0)
		self.evento(
			add_to_date(ora, hours=2),
			[{"type": "Email", "before": 1, "interval": "hours"}],
			proprietario=self.neri,
		)
		email = self.lo_scheduler(*(add_to_date(ora, minutes=4 * giro) for giro in range(31)))
		self.assertEqual(
			[(quando, a) for quando, a, _o, _t in email], [(add_to_date(ora, hours=1), (self.neri,))]
		)
		self.assertIn("Inizia tra un'ora.", html.unescape(email[0][3]))

	def test_un_giorno_prima_parte_il_giorno_prima_alla_sua_ora(self):
		# «1 day before» a visit at ten: the day before at ten. The days were looked at
		# only at midnight, eight hours either side of their time: a visit between
		# eight and four was never reminded
		oggi = now_datetime().replace(hour=0, minute=0, second=0, microsecond=0)
		alle_dieci = oggi.replace(hour=10)
		self.evento(
			add_to_date(alle_dieci, days=1),
			[{"type": "Email", "before": 1, "interval": "days"}],
			proprietario=self.neri,
		)
		email = self.lo_scheduler(*(add_to_date(oggi, hours=ora) for ora in range(25)))
		self.assertEqual([(quando, a) for quando, a, _o, _t in email], [(alle_dieci, (self.neri,))])
		self.assertIn("Inizia domani.", html.unescape(email[0][3]))

	def test_tutto_il_giorno_all_ora_che_il_centro_ha_scelto(self):
		# the centre's «1 day before at 09:00» of an all-day event: the day before at
		# nine. It left at the midnight the event began, «It starts tomorrow.»
		oggi = now_datetime().replace(hour=0, minute=0, second=0, microsecond=0)
		domani = add_to_date(oggi, days=1)
		frappe.get_doc(
			{
				"doctype": "Event Notifications",
				"parenttype": "FCRM Settings",
				"parentfield": "all_day_event_notifications",
				"parent": "FCRM Settings",
				"type": "Email",
				"before": 1,
				"interval": "days",
				"time": "09:00:00",
			}
		).db_insert()
		evento = self.evento(domani, [], proprietario=self.neri, all_day=1)
		frappe.db.set_value(
			"Event", evento, "ends_on", domani.replace(hour=23, minute=59), update_modified=False
		)
		email = self.lo_scheduler(*(add_to_date(oggi, hours=ora) for ora in range(25)))
		self.assertEqual([(quando, a) for quando, a, _o, _t in email], [(oggi.replace(hour=9), (self.neri,))])
		self.assertEqual(self.registrati(evento), [(self.neri, "Email")])

	def test_un_email_tardiva_non_parte_a_evento_cominciato(self):
		# a visit booked a few minutes ago for within the hour, with the centre's «2
		# hours before» by email: its time had passed before it was booked, and the
		# email left as it began, «It starts in 2 hours.» - «It starts tomorrow.» for a
		# «1 day before» of a visit booked that morning. On the screen it still shows
		ora = now_datetime().replace(minute=0, second=0, microsecond=0)
		for tipo in ("Email", "Notification"):
			frappe.get_doc(
				{
					"doctype": "Event Notifications",
					"parenttype": "FCRM Settings",
					"parentfield": "event_notifications",
					"parent": "FCRM Settings",
					"type": tipo,
					"before": 2,
					"interval": "hours",
				}
			).db_insert()
		evento = self.evento(add_to_date(ora, hours=1), [], proprietario=self.neri)
		email = self.lo_scheduler(*(add_to_date(ora, minutes=4 * giro) for giro in range(1, 27)))
		self.assertEqual(email, [])
		self.assertEqual(self.registrati(evento), [])
		self.assertEqual(sorted(set(self.stanze(evento))), [f"user:{self.neri}"])

	# ------------------------------------------------------------------ what the round reads

	def test_legge_solo_gli_eventi_che_possono_essere_dovuti(self):
		adesso = now_datetime().replace(microsecond=0)
		vicino = self.evento(
			add_to_date(adesso, minutes=10), [{"type": "Email", "before": 10, "interval": "minutes"}]
		)
		lontano = self.evento(
			add_to_date(adesso, days=3), [{"type": "Email", "before": 10, "interval": "minutes"}]
		)
		letti = {p.event_name for p in E._promemoria_degli_eventi("minutes", adesso, 10, [])}
		self.assertIn(vicino, letti)
		self.assertNotIn(lontano, letti)

	def test_senza_promemoria_di_quell_unita_non_legge_nessun_evento(self):
		self.evento(add_to_date(now_datetime(), days=3), [])
		with patch.object(E, "_promemoria_degli_eventi", wraps=E._promemoria_degli_eventi) as letti:
			E._process_event_notifications_by_interval("weeks")
			letti.assert_not_called()
			# one of the centre's, and it looks
			frappe.get_doc(
				{
					"doctype": "Event Notifications",
					"parenttype": "FCRM Settings",
					"parentfield": "event_notifications",
					"parent": "FCRM Settings",
					"type": "Notification",
					"before": 1,
					"interval": "weeks",
				}
			).db_insert()
			E._process_event_notifications_by_interval("weeks")
			letti.assert_called_once()

	# ------------------------------------------------------------------ the demo

	def test_un_appuntamento_della_demo_non_si_ricorda_per_email(self):
		adesso = now_datetime().replace(microsecond=0)
		frappe.get_doc(
			{
				"doctype": "CRM Demo Record",
				"ref_doctype": "CRM Appointment",
				"ref_name": "APPT-DEMO-FINTO",
				"parte": "test",
			}
		).insert(ignore_permissions=True)
		evento = self.evento(
			add_to_date(adesso, minutes=10),
			[
				{"type": "Email", "before": 10, "interval": "minutes"},
				{"type": "Notification", "before": 10, "interval": "minutes"},
			],
			proprietario=self.neri,
			reference_doctype="CRM Appointment",
			reference_docname="APPT-DEMO-FINTO",
		)
		with patch("crm.demo.registro.caricati", return_value=True):
			email = self.giri("minutes", adesso)
		# on the screen, as a notification about it is in the panel; never by email
		self.assertEqual(email, [])
		self.assertEqual(self.registrati(evento), [])
		self.assertEqual(self.stanze(evento), [f"user:{self.neri}"])

	def test_l_email_passa_dalla_guardia_della_demo(self):
		# a colleague of the demo's is at example.com: while the demo is in, the queue
		# keeps what is written to them, an event's reminder too
		adesso = now_datetime().replace(microsecond=0)
		evento = self.evento(
			add_to_date(adesso, minutes=10),
			[{"type": "Email", "before": 10, "interval": "minutes"}],
			proprietario=self.neri,
		)
		# a mailbox the email leaves from, as a centre has
		frappe.local.outgoing_email_account = {}
		self.addCleanup(setattr, frappe.local, "outgoing_email_account", {})
		posta = frappe.get_doc(
			{
				"doctype": "Email Account",
				"email_account_name": "Promemoria degli eventi",
				"email_id": "promemoria.eventi@example.com",
				"enable_outgoing": 1,
				"default_outgoing": 1,
			}
		)
		posta.flags.ignore_mandatory = True
		posta.flags.ignore_validate = True
		posta.insert(ignore_permissions=True)
		with (
			patch("crm.demo.registro.caricati", return_value=True),
			patch("frappe.utils.get_assets_json", return_value={}),
			patch.object(E, "now_datetime", return_value=adesso),
		):
			E._process_event_notifications_by_interval("minutes")
		coda = frappe.get_all(
			"Email Queue",
			filters={"reference_doctype": "Event", "reference_name": evento},
			fields=["name", "status", "error"],
		)
		self.assertEqual([(r.status, r.error) for r in coda], [("Error", guardie.NON_INVIATA)])
		self.assertFalse(frappe.db.exists("Email Queue Recipient", {"parent": coda[0].name}))
		self.assertEqual(self.registrati(evento), [(self.neri, "Email")])
