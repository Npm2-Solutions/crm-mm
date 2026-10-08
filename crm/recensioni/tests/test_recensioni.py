# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A review asked after a visit, on a real site: only to who agreed, once in so
many months, never after a service excluded; the request written before the
message leaves, its link counting the click and going on to Google."""

import email
import json
import re
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, now_datetime

from crm.automation import engine
from crm.moduli import consensi
from crm.recensioni import chiedi

LINK = "https://g.page/r/centro-di-prova/review"


def automazione(titolo="Chiedi una recensione", messaggio="Ciao {{ first_name }}: {{ review_link }}"):
	return frappe.get_doc(
		{
			"doctype": "CRM Automation",
			"title": titolo,
			"enabled": 1,
			"trigger_event": "Appointment Completed",
			"steps": json.dumps(
				[
					{"type": "send_email", "subject": "Com'è andata?", "message": messaggio},
					# a second message of the same run is no second request
					{"type": "send_email", "subject": "Ancora", "message": "Di nuovo: {{ review_link }}"},
				]
			),
		}
	).insert()


class Recensioni(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.inizio = now_datetime()
		self.impostazioni(google_review_link=LINK, months_between=12, excluded_services="")
		self.servizio = frappe.get_doc(
			{
				"doctype": "CRM Service",
				"service_name": "Certificato di prova",
				"enabled": 1,
				"staff": [{"user": "Administrator"}],
			}
		).insert(ignore_permissions=True)
		self.persona = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Rita",
				"last_name": "Recensione",
				"email": "rita@example.com",
			}
		).insert(ignore_permissions=True)
		self.auto = automazione()

	def tearDown(self):
		frappe.flags.crm_review_link = None
		frappe.db.rollback()

	def impostazioni(self, **valori):
		doc = frappe.get_single(chiedi.IMPOSTAZIONI)
		doc.update(valori)
		doc.save(ignore_permissions=True)

	def acconsente(self, chiave="review_requests", stato="Given"):
		consensi.registra_risposta(self.persona.name, chiave, stato, "At the desk")

	def dopo_la_visita(self, persona=None, automazione=None, servizio=None):
		nome = engine.enroll(
			(automazione or self.auto).name,
			"CRM Lead",
			(persona or self.persona).name,
			{"status": "Completed", "service": servizio},
		)
		return frappe.get_doc("CRM Automation Enrollment", nome)

	def richieste(self, persona=None):
		return frappe.get_all(
			chiedi.RICHIESTA,
			filters={"lead": (persona or self.persona).name},
			fields=["name", "enrollment", "channel", "clicked_on"],
		)

	def email_con_il_link(self):
		"""The emails the person was sent, as they read them: the queue keeps MIME."""
		testi = []
		for grezzo in frappe.get_all(
			"Email Queue",
			filters={
				"reference_doctype": "CRM Lead",
				"reference_name": self.persona.name,
				"creation": (">=", self.inizio),
			},
			pluck="message",
		):
			testi.append(
				"".join(
					parte.get_payload(decode=True).decode()
					for parte in email.message_from_string(grezzo).walk()
					if parte.get_content_type() == "text/html"
				)
			)
		return testi

	def test_senza_consenso_non_parte_niente(self):
		iscrizione = self.dopo_la_visita()
		self.assertEqual([log.status for log in iscrizione.logs], ["Skipped", "Skipped"])
		self.assertIn("Did not agree", iscrizione.logs[0].detail)
		self.assertEqual(self.richieste(), [])

	def test_il_no_alle_richieste_vince_sul_si_al_marketing(self):
		self.acconsente("marketing")
		self.acconsente(stato="Refused")
		iscrizione = self.dopo_la_visita()
		self.assertEqual(iscrizione.logs[0].status, "Skipped")

	def test_con_il_si_al_marketing_parte_una_richiesta_sola(self):
		self.acconsente("marketing")
		iscrizione = self.dopo_la_visita()
		self.assertEqual([log.status for log in iscrizione.logs], ["Success", "Success"])
		richieste = self.richieste()
		self.assertEqual(len(richieste), 1)
		self.assertEqual(richieste[0].enrollment, iscrizione.name)
		self.assertEqual(richieste[0].channel, "Email")
		# the link is the request's own, never Google's page with somebody on it
		messaggi = "".join(self.email_con_il_link())
		self.assertIn("crm.recensioni.chiedi.vai", messaggi)
		self.assertNotIn("{{ review_link }}", messaggi)

	def test_una_volta_ogni_tanti_mesi_qualunque_automazione(self):
		self.acconsente()
		self.dopo_la_visita()
		altra = automazione("Un'altra che chiede")
		iscrizione = self.dopo_la_visita(automazione=altra)
		self.assertEqual(iscrizione.logs[0].status, "Skipped")
		self.assertIn("12 months", iscrizione.logs[0].detail)
		self.assertEqual(len(self.richieste()), 1)
		# a year and a day later, asked again
		frappe.db.set_value(
			chiedi.RICHIESTA,
			self.richieste()[0].name,
			"sent_on",
			add_to_date(now_datetime(), months=-12, days=-1),
		)
		frappe.db.delete("CRM Automation Enrollment", {"automation": altra.name})
		self.assertEqual(self.dopo_la_visita(automazione=altra).logs[0].status, "Success")

	def test_mai_dopo_un_servizio_escluso(self):
		self.acconsente()
		self.impostazioni(excluded_services=self.servizio.name)
		iscrizione = self.dopo_la_visita(servizio=self.servizio.name)
		self.assertEqual(iscrizione.logs[0].status, "Skipped")
		self.assertIn("this service", iscrizione.logs[0].detail)

	def test_senza_link_non_si_chiede(self):
		self.acconsente()
		self.impostazioni(google_review_link=None, google_place_id=None)
		self.assertEqual(self.dopo_la_visita().logs[0].status, "Skipped")

	def test_un_messaggio_senza_il_link_non_e_una_richiesta(self):
		auto = automazione("Grazie", messaggio="Grazie {{ first_name }}")
		iscrizione = self.dopo_la_visita(automazione=auto)
		self.assertEqual(iscrizione.logs[0].status, "Success")
		self.assertEqual(self.richieste(), [])

	def test_il_link_conta_il_clic_e_porta_a_google(self):
		self.acconsente()
		self.dopo_la_visita()
		# the SMS and the email of the same request carry the same link
		chiavi = {
			c for testo in self.email_con_il_link() for c in re.findall(r"chiedi\.vai\?r=([\w.-]+)", testo)
		}
		self.assertEqual(len(chiavi), 1)
		chiave = chiavi.pop()
		# a GET's own commit: the test's rollback undoes the rest
		with patch.object(frappe.db, "commit"):
			chiedi.vai(chiave)
		self.assertEqual(frappe.local.response["location"], LINK)
		self.assertTrue(self.richieste()[0].clicked_on)
		# a guess opens Google all the same, and counts nothing
		with patch.object(frappe.db, "commit"):
			chiedi.vai("non-una-chiave-vera")
			chiedi.vai(f"{self.richieste()[0].name}.0123456789abcdef0123")
		self.assertEqual(frappe.local.response["location"], LINK)

	def test_le_richieste_se_ne_vanno_con_la_persona(self):
		self.acconsente()
		self.dopo_la_visita()
		frappe.delete_doc("CRM Lead", self.persona.name, ignore_permissions=True)
		self.assertFalse(frappe.db.exists(chiedi.RICHIESTA, {"lead": self.persona.name}))

	def test_le_impostazioni_si_controllano(self):
		with self.assertRaises(frappe.ValidationError):
			self.impostazioni(google_review_link="http://non-sicuro.example.com")
		self.impostazioni(months_between=0, excluded_services=" A \n\nA\nB ")
		doc = frappe.get_single(chiedi.IMPOSTAZIONI)
		self.assertEqual(doc.months_between, 12)
		self.assertEqual(doc.excluded_services, "A\nB")
