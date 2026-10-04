# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""How an appointment went, and the desk's day (docs/gestionale-medico, fase 1).

The desk checks people in, and the waiting room counts from there; once each
participant came or did not, the appointment closes by itself. An invoice issued
from it says they came. At the end of the day whoever was checked in counts as
came, and the desk is asked about the rest.
"""

import datetime
from unittest.mock import patch

import frappe
from frappe.utils import get_datetime

from crm.api import oggi
from crm.permissions import livelli, utenti
from crm.permissions.test_org_hierarchy import make_user
from crm.scheduling import esiti
from crm.tests.test_scheduling import SchedulingCase

DESK = "oggi.desk@example.com"
DOCTOR = "oggi.doctor@example.com"
OTHER = "oggi.other@example.com"
MARKETING = "oggi.marketing@example.com"


class OggiCase(SchedulingCase):
	def setUp(self):
		super().setUp()
		utenti.sincronizza()
		for user, livello in (
			(DESK, "segreteria"),
			(DOCTOR, "operatore"),
			(OTHER, "operatore"),
			(MARKETING, "marketing"),
		):
			make_user(user)
			utenti.assegna_livelli(user, [livello])
		livelli.dimentica_cache()
		self.service = self.make_service("Visita del giorno", [DOCTOR, OTHER])
		self.mario = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Mario", "last_name": "Oggi"}
		).insert(ignore_permissions=True)
		self.luca = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Luca", "last_name": "Oggi"}).insert(
			ignore_permissions=True
		)

	def tearDown(self):
		super().tearDown()
		livelli.dimentica_cache()

	def come(self, user):
		frappe.set_user(user)
		livelli.dimentica_cache()

	def ieri(self, ora=9):
		return self.tomorrow(ora) - datetime.timedelta(days=2)

	def appuntamento(self, quando, *persone, medico=DOCTOR):
		return self.make_appointment(
			self.service.name,
			quando,
			[medico],
			status="Confirmed",
			participants=[
				{
					"party_type": "CRM Lead",
					"party": p.name,
					"participant_name": p.lead_name,
					"status": "Booked",
				}
				for p in persone
			],
		)

	def riga(self, doc, persona):
		doc.reload()
		return next(row for row in doc.participants if row.party == persona.name)


class GliEsiti(OggiCase):
	def test_l_accettazione_segna_l_ora_e_si_disfa(self):
		incontro = self.appuntamento(self.tomorrow(10), self.mario)
		self.come(DESK)
		esiti.segna(incontro.name, self.riga(incontro, self.mario).name, "Arrived")
		riga = self.riga(incontro, self.mario)
		self.assertEqual(riga.status, "Arrived")
		self.assertIsNotNone(riga.arrived_at)
		esiti.segna(incontro.name, riga.name, "Booked")
		self.assertIsNone(self.riga(incontro, self.mario).arrived_at)

	def test_si_chiude_quando_tutti_hanno_un_esito(self):
		servizio = self.make_service("Gruppo del giorno", [DOCTOR], max_participants=4)
		incontro = self.make_appointment(
			servizio.name,
			self.ieri(),
			[DOCTOR],
			status="Confirmed",
			participants=[
				{
					"party_type": "CRM Lead",
					"party": p.name,
					"participant_name": p.lead_name,
					"status": "Booked",
				}
				for p in (self.mario, self.luca)
			],
		)
		self.come(DESK)
		esiti.segna(incontro.name, self.riga(incontro, self.mario).name, "Attended")
		self.assertEqual(frappe.db.get_value("CRM Appointment", incontro.name, "status"), "Confirmed")
		esiti.segna(incontro.name, self.riga(incontro, self.luca).name, "No Show")
		self.assertEqual(frappe.db.get_value("CRM Appointment", incontro.name, "status"), "Completed")

	def test_un_appuntamento_sovrapposto_si_accoglie(self):
		# a manager forced it over another of the same doctor's: the desk, who may
		# not force anything, says all the same that the person arrived
		self.appuntamento(self.tomorrow(10), self.mario)
		forzato = self.make_appointment(
			self.service.name,
			self.tomorrow(10),
			[DOCTOR],
			status="Confirmed",
			override_conflicts=1,
			participants=[
				{
					"party_type": "CRM Lead",
					"party": self.luca.name,
					"participant_name": self.luca.lead_name,
					"status": "Booked",
				}
			],
		)
		self.assertTrue(forzato.conflict_note)
		self.come(DESK)
		esiti.segna(forzato.name, self.riga(forzato, self.luca).name, "Arrived")
		self.assertEqual(self.riga(forzato, self.luca).status, "Arrived")
		# moving it is a new booking, and the clash is asked about again
		forzato.reload()
		forzato.starts_on = forzato.starts_on + datetime.timedelta(minutes=5)
		forzato.ends_on = forzato.ends_on + datetime.timedelta(minutes=5)
		with self.assertRaises(frappe.ValidationError):
			forzato.save()

	def test_chi_non_c_e_piu_non_ferma_l_accoglienza(self):
		# a professional whose account is gone (an old import): the outcome is said
		incontro = self.appuntamento(self.tomorrow(10), self.mario)
		frappe.db.set_value("CRM Appointment Staff", incontro.staff[0].name, "user", "andato.via@example.com")
		self.come(DESK)
		esiti.segna(incontro.name, self.riga(incontro, self.mario).name, "Arrived")
		self.assertEqual(self.riga(incontro, self.mario).status, "Arrived")

	def test_nessuno_e_venuto(self):
		incontro = self.appuntamento(self.ieri(), self.mario)
		self.come(DESK)
		esiti.segna(incontro.name, self.riga(incontro, self.mario).name, "No Show")
		self.assertEqual(frappe.db.get_value("CRM Appointment", incontro.name, "status"), "No Show")
		# taken back: open again
		esiti.segna(incontro.name, self.riga(incontro, self.mario).name, "Booked")
		self.assertEqual(frappe.db.get_value("CRM Appointment", incontro.name, "status"), "Confirmed")


class ChiSegna(OggiCase):
	def test_la_segreteria_tutti_il_medico_i_suoi(self):
		mio = self.appuntamento(self.tomorrow(10), self.mario)
		altrui = self.appuntamento(self.tomorrow(12), self.luca, medico=OTHER)
		self.come(DESK)
		self.assertTrue(esiti.puo_segnare(mio))
		self.assertTrue(esiti.puo_segnare(altrui))
		self.come(DOCTOR)
		self.assertTrue(esiti.puo_segnare(mio))
		self.assertFalse(esiti.puo_segnare(altrui))
		with self.assertRaises(frappe.PermissionError):
			esiti.segna(altrui.name, self.riga(altrui, self.luca).name, "Arrived")

	def test_il_marketing_no(self):
		self.come(MARKETING)
		with self.assertRaises(frappe.PermissionError):
			oggi.get_day()


class LaFatturaELaGiornata(OggiCase):
	def test_la_fattura_dice_che_e_venuto(self):
		incontro = self.appuntamento(self.ieri(), self.mario)
		esiti.fattura_emessa(
			frappe._dict(
				doctype="CRM Invoice",
				name="FT-1",
				appointment=incontro.name,
				party_type="CRM Lead",
				party=self.mario.name,
			)
		)
		self.assertEqual(self.riga(incontro, self.mario).status, "Attended")
		self.assertEqual(frappe.db.get_value("CRM Appointment", incontro.name, "status"), "Completed")

	def test_una_fattura_fatta_prima_non_dice_niente(self):
		incontro = self.appuntamento(self.tomorrow(10), self.mario)
		self.assertFalse(esiti.presente(incontro.name, self.mario.name))
		self.assertEqual(self.riga(incontro, self.mario).status, "Booked")

	def test_a_fine_giornata(self):
		accolto = self.appuntamento(self.ieri(9), self.mario)
		dimenticato = self.appuntamento(self.ieri(11), self.luca, medico=OTHER)
		self.come(DESK)
		esiti.segna(accolto.name, self.riga(accolto, self.mario).name, "Arrived")
		frappe.set_user("Administrator")
		giorno = get_datetime(frappe.db.get_value("CRM Appointment", dimenticato.name, "ends_on")).date()
		# after the day's last appointment, whoever else booked that day
		fine = max(get_datetime(riga.ends_on) for riga in esiti._di_oggi(giorno))
		frappe.db.set_default(esiti.AVVISATO, "")
		with patch("crm.scheduling.esiti.now_datetime", return_value=fine + datetime.timedelta(hours=1)):
			esiti.fine_giornata()
			# once a day
			esiti.fine_giornata()
		self.assertEqual(self.riga(accolto, self.mario).status, "Attended")
		self.assertEqual(frappe.db.get_value("CRM Appointment", accolto.name, "status"), "Completed")
		avvisi = frappe.get_all(
			"CRM Notification", filters={"type": "Agenda", "to_user": DESK}, fields=["message"]
		)
		self.assertEqual(len(avvisi), 1)
		self.assertIn(dimenticato.name, avvisi[0].message)
		self.assertNotIn(accolto.name, avvisi[0].message)

	def test_una_giornata_che_finisce_tardi_si_chiude_dopo_mezzanotte(self):
		tardi = self.appuntamento(self.ieri(23), self.mario)
		self.come(DESK)
		esiti.segna(tardi.name, self.riga(tardi, self.mario).name, "Arrived")
		frappe.set_user("Administrator")
		fine = get_datetime(frappe.db.get_value("CRM Appointment", tardi.name, "ends_on"))
		giorno = fine.date()
		# the day's last appointment, whatever else the site has that day
		ultimo = max(get_datetime(riga.ends_on) for riga in esiti._di_oggi(giorno))
		dopo = max(ultimo, fine) + datetime.timedelta(hours=1)
		mezzanotte = datetime.datetime.combine(giorno + datetime.timedelta(days=1), datetime.time(0, 30))
		frappe.db.set_default(esiti.AVVISATO, "")
		with patch("crm.scheduling.esiti.now_datetime", return_value=max(dopo, mezzanotte)):
			esiti.fine_giornata()
		self.assertEqual(self.riga(tardi, self.mario).status, "Attended")
		self.assertEqual(frappe.db.get_default(esiti.AVVISATO), str(giorno))
		# asked about once: the next hour, nothing again
		with patch(
			"crm.scheduling.esiti.now_datetime",
			return_value=max(dopo, mezzanotte) + datetime.timedelta(hours=1),
		):
			esiti.fine_giornata()
		self.assertEqual(frappe.db.get_default(esiti.AVVISATO), str(giorno))

	def test_la_giornata_della_segreteria(self):
		oggi_incontro = self.appuntamento(self.tomorrow(10) - datetime.timedelta(days=1), self.mario)
		aperto = self.appuntamento(self.ieri(9) - datetime.timedelta(days=1), self.luca)
		self.come(DESK)
		giorno = str(
			get_datetime(frappe.db.get_value("CRM Appointment", oggi_incontro.name, "starts_on")).date()
		)
		risposta = oggi.get_day(giorno)
		self.assertIn(oggi_incontro.name, [a["name"] for a in risposta["appointments"]])
		self.assertIn(aperto.name, [a["name"] for a in risposta["past_open"]])
		self.assertTrue(all(a["can_mark"] for a in risposta["appointments"]))
		riga = next(a for a in risposta["appointments"] if a["name"] == oggi_incontro.name)["participants"][0]
		esito = oggi.set_outcome(oggi_incontro.name, riga.name, "Arrived")
		self.assertEqual(esito["participants"][0]["status"], "Arrived")


class IlPannelloDellAppuntamento(OggiCase):
	"""The agenda's panel offers what the server says (`get_appointment`): who
	reads the agenda without booking - the medical director, the read-only level -
	found edit, delete, the status and «repeat», which the server then refused."""

	def test_chi_prenota_lo_cambia_chi_legge_soltanto_no(self):
		from crm.api.appointments import get_appointment

		lettore = "oggi.readonly@example.com"
		make_user(lettore)
		utenti.assegna_livelli(lettore, ["segreteria", "sola_lettura"])
		incontro = self.appuntamento(self.tomorrow(10), self.mario)

		self.come(DESK)
		dati = get_appointment(incontro.name)
		self.assertTrue(dati["can_write"])
		self.assertFalse(dati["can_delete"], "deleting is the manager's (agenda.elimina)")

		self.come(lettore)
		dati = get_appointment(incontro.name)
		self.assertEqual(dati["name"], incontro.name)
		self.assertFalse(dati["can_write"])
		self.assertFalse(dati["can_delete"])
