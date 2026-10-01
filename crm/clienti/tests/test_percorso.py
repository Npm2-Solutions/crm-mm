# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The person's journey, in five steps: the rules on their own, then Giulia's
page as she arrives, books, comes, gets her invoice and follows a plan."""

from __future__ import annotations

import datetime

import frappe
from frappe.tests import UnitTestCase
from frappe.utils import nowdate

from crm.clienti import percorso as p
from crm.clienti.tests.test_clienti import ClientiCase

LUNEDI = datetime.datetime(2026, 5, 4, 9, 0)


def stati(tappe):
	return [tappa["state"] for tappa in tappe]


class LeTappe(UnitTestCase):
	def test_appena_arrivato_la_prenotazione_e_quella_in_corso(self):
		tappe = p.percorso({"arrivato": LUNEDI, "fonte": "Instagram"})
		self.assertEqual([t["key"] for t in tappe], list(p.TAPPE))
		self.assertEqual(stati(tappe), ["done", "current", "next", "next", "next"])
		self.assertEqual(tappe[0]["detail"], "Instagram")
		self.assertEqual(tappe[0]["on"], "2026-05-04 09:00")

	def test_prenotato_si_aspetta_la_visita(self):
		tappe = p.percorso(
			{
				"arrivato": LUNEDI,
				"prenotato": LUNEDI,
				"canale": "Online",
				"prossimo": LUNEDI + datetime.timedelta(days=2, hours=1),
			}
		)
		self.assertEqual(stati(tappe), ["done", "done", "current", "next", "next"])
		self.assertEqual(tappe[1]["detail"], "Online")
		self.assertEqual(tappe[2]["expected"], "2026-05-06 10:00")

	def test_una_tappa_fatta_dopo_una_mancata_resta_fatta(self):
		"""An invoice with no visit marked: what the data says is done stays done,
		the first missing one is under way."""
		tappe = p.percorso({"arrivato": LUNEDI, "dopo": LUNEDI.date(), "dopo_cosa": "Invoice"})
		self.assertEqual(stati(tappe), ["done", "current", "next", "done", "next"])
		self.assertEqual(tappe[3]["on"], "2026-05-04")

	def test_tutto_fatto_nessuna_in_corso(self):
		giorno = LUNEDI
		tappe = p.percorso(
			{"arrivato": giorno, "prenotato": giorno, "venuto": giorno, "dopo": giorno, "a_casa": giorno}
		)
		self.assertEqual(stati(tappe), ["done"] * 5)

	def test_chi_e_venuto_e_quando(self):
		appuntamenti = [
			{"starts_on": "2026-05-06 10:00:00", "status": "Confirmed", "participant_status": "Booked"},
			{"starts_on": "2026-05-05 10:00:00", "status": "Completed", "participant_status": "Booked"},
			{
				"starts_on": "2026-05-04 10:00:00",
				"status": "Confirmed",
				"participant_status": "No Show",
				"arrived_at": "2026-05-04 09:50:00",
			},
		]
		self.assertEqual(p.primo_arrivo(appuntamenti), datetime.datetime(2026, 5, 5, 10, 0))
		self.assertIsNone(p.primo_arrivo(appuntamenti[:1]))

	def test_la_prima_prenotazione_e_il_suo_canale(self):
		appuntamenti = [
			{"creation": "2026-05-01 08:00:00", "status": "Cancelled", "source": "Online"},
			{"creation": "2026-05-02 08:00:00", "status": "Confirmed", "source": "Internal"},
			{
				"creation": "2026-05-03 08:00:00",
				"status": "Confirmed",
				"source": "External",
				"external_platform": "MioDottore",
			},
		]
		self.assertEqual(
			p.prima_prenotazione(appuntamenti),
			{"il": datetime.datetime(2026, 5, 2, 8, 0), "canale": "At the desk"},
		)
		self.assertEqual(p.prima_prenotazione(appuntamenti[2:])["canale"], "MioDottore")
		self.assertIsNone(p.prima_prenotazione(appuntamenti[:1]))

	def test_il_prossimo_appuntamento(self):
		appuntamenti = [
			{"starts_on": "2026-05-03 10:00:00", "status": "Confirmed"},
			{"starts_on": "2026-05-08 10:00:00", "status": "Cancelled"},
			{"starts_on": "2026-05-09 10:00:00", "status": "Confirmed", "participant_status": "No Show"},
			{"starts_on": "2026-05-07 10:00:00", "status": "Confirmed"},
		]
		self.assertEqual(p.prossimo(appuntamenti, LUNEDI), datetime.datetime(2026, 5, 7, 10, 0))
		self.assertIsNone(p.prossimo(appuntamenti[:3], LUNEDI))


class IlPercorsoDiGiulia(ClientiCase):
	def passi(self):
		return {tappa["key"]: tappa for tappa in p.get_journey(self.giulia.name)["steps"]}

	def test_arriva_prenota_viene_poi_a_casa(self):
		frappe.db.set_value("CRM Lead", self.giulia.name, "first_touch_source", "instagram")
		passi = self.passi()
		self.assertEqual(passi[p.ARRIVA]["state"], "done")
		self.assertEqual(passi[p.ARRIVA]["detail"], "instagram")
		self.assertEqual(passi[p.PRENOTA]["state"], "current")

		domani = self.appuntamento(self.giulia, self.tomorrow(10))
		passi = self.passi()
		self.assertEqual(passi[p.PRENOTA]["state"], "done")
		self.assertEqual(passi[p.PRENOTA]["detail"], "At the desk")
		self.assertEqual(passi[p.VIENE]["state"], "current")
		self.assertTrue(passi[p.VIENE]["expected"].startswith(str(self.tomorrow(10).date())))

		# she came yesterday to another appointment: the visit is done, nothing expected
		self.appuntamento(self.giulia, self.ieri(10), stato="Completed")
		passi = self.passi()
		self.assertEqual(passi[p.VIENE]["state"], "done")
		self.assertNotIn("expected", passi[p.VIENE])
		self.assertEqual(passi[p.DOPO]["state"], "current")

		# a document added today follows the visit
		frappe.get_doc(
			{
				"doctype": "CRM Document",
				"lead": self.giulia.name,
				"title": "Consenso firmato",
				"document_type": "Other",
				"file": "/private/files/consenso-giulia.pdf",
			}
		).insert(ignore_permissions=True)
		passi = self.passi()
		self.assertEqual(passi[p.DOPO]["state"], "done")
		self.assertEqual(passi[p.DOPO]["detail"], "Document")
		self.assertEqual(passi[p.DOPO]["on"], nowdate())
		self.assertEqual(passi[p.A_CASA]["state"], "current")
		self.assertTrue(domani.name)

	def test_chi_non_legge_la_persona_non_ne_vede_il_percorso(self):
		estraneo = "clienti.estraneo@example.com"
		if not frappe.db.exists("User", estraneo):
			frappe.get_doc(
				{"doctype": "User", "email": estraneo, "first_name": "Estraneo", "send_welcome_email": 0}
			).insert(ignore_permissions=True)
		frappe.set_user(estraneo)
		with self.assertRaises(frappe.PermissionError):
			p.get_journey(self.giulia.name)
