# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A call nobody answered, on a real site (doc 52).

From somebody the centre knows, the automations hear «Missed Call»: the recipe
waits a minute and texts the booking page from the centre's sender, never to who
wrote STOP. From a number nobody knows, where the centre wants it, one SMS of
service a day, only to a mobile of the countries the centre calls, never for the
demo.
"""

import datetime
import json
from unittest.mock import patch

import frappe
from frappe.utils import now_datetime

from crm.automation import engine
from crm.telephony import answering, inbound, persa
from crm.telephony.tests.test_collegamento import TwilioCase
from crm.telephony.tests.test_sms import CELLULARE, mittente_di_prova
from crm.tests.test_telephony_providers import STUDIO_NUMBER, FakeProvider

CHI_CHIAMA = "+393401112233"
SCONOSCIUTO = "+393409998877"


class ChiamataPersaCase(TwilioCase):
	def setUp(self):
		super().setUp()
		mittente_di_prova(numero=CELLULARE)
		frappe.db.set_single_value("CRM Scheduling Settings", "online_booking_enabled", 1)
		self.risposte(sms_to_missed_callers=0)
		frappe.cache.delete_keys("crm_sms_chiamata_persa")
		self.provider = FakeProvider()

	def tearDown(self):
		super().tearDown()
		for cache in ("crm_answering_settings", "crm_scheduling_settings"):
			if hasattr(frappe.local, cache):
				delattr(frappe.local, cache)

	def risposte(self, **valori):
		doc = frappe.get_single("CRM Answering Settings")
		doc.update({"enabled": 1, "answer_mode": answering.MODE_RING_FIRST, "use_working_hours": 0, **valori})
		doc.save()
		if hasattr(frappe.local, "crm_answering_settings"):
			del frappe.local.crm_answering_settings

	def chiamata(self, numero, persona=None):
		log = frappe.get_doc(
			{
				"doctype": "CRM Call Log",
				"id": "CA" + frappe.generate_hash(length=32),
				"to": STUDIO_NUMBER,
				"type": "Incoming",
				"status": "In Progress",
				"telephony_medium": "Twilio",
				"reference_doctype": "CRM Lead" if persona else None,
				"reference_docname": persona,
			}
		)
		setattr(log, "from", numero)
		return log.insert(ignore_permissions=True)


class DaChiConosciamo(ChiamataPersaCase):
	def setUp(self):
		super().setUp()
		self.persona = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Piera", "last_name": "Persa", "mobile_no": CHI_CHIAMA}
		).insert(ignore_permissions=True)
		# the recipe, as the builder saves it once the centre switches it on
		self.automazione = frappe.get_doc(
			{
				"doctype": "CRM Automation",
				"title": "Ti abbiamo cercato",
				"enabled": 1,
				"trigger_event": persa.TRIGGER,
				"steps": json.dumps(
					[
						{"type": "wait", "mode": "duration", "days": 0, "hours": 0, "minutes": 1},
						{"type": "send_sms", "message": "Ciao {{ first_name }}, prenota: {{ booking_link }}"},
					]
				),
			}
		).insert(ignore_permissions=True)

	def iscrizione(self):
		return frappe.db.get_value(
			"CRM Automation Enrollment",
			{"automation": self.automazione.name, "reference_name": self.persona.name},
			["name", "status"],
			as_dict=True,
		)

	def test_un_minuto_dopo_l_sms_con_la_pagina_di_prenotazione(self):
		with patch("crm.api.sms.deliver_via_twilio") as consegna:
			inbound.nobody_answered(self.provider, call_log=self.chiamata(CHI_CHIAMA, self.persona.name))
			iscritta = self.iscrizione()
			self.assertEqual(iscritta.status, "Waiting")
			consegna.assert_not_called()
			dopo = now_datetime() + datetime.timedelta(minutes=2)
			with patch("crm.automation.engine.now_datetime", return_value=dopo):
				engine.advance_enrollment(iscritta.name)
		[doc] = consegna.call_args.args
		self.assertEqual((doc.get("from"), doc.to), (CELLULARE, CHI_CHIAMA))
		self.assertIn("Ciao Piera, prenota: ", doc.message)
		self.assertTrue(doc.message.endswith("/prenota"))

	def test_chi_ha_scritto_stop_no(self):
		frappe.db.set_value("CRM Lead", self.persona.name, "sms_opt_out", 1)
		with patch("crm.api.sms.deliver_via_twilio") as consegna:
			inbound.nobody_answered(self.provider, call_log=self.chiamata(CHI_CHIAMA, self.persona.name))
			with patch(
				"crm.automation.engine.now_datetime",
				return_value=now_datetime() + datetime.timedelta(minutes=2),
			):
				engine.advance_enrollment(self.iscrizione().name)
		consegna.assert_not_called()

	def test_l_automazione_spenta_non_sente_niente(self):
		frappe.db.set_value("CRM Automation", self.automazione.name, "enabled", 0)
		inbound.nobody_answered(self.provider, call_log=self.chiamata(CHI_CHIAMA, self.persona.name))
		self.assertIsNone(self.iscrizione())


class DaUnNumeroSconosciuto(ChiamataPersaCase):
	def test_spento_niente(self):
		with patch("frappe.enqueue") as coda:
			inbound.nobody_answered(self.provider, call_log=self.chiamata(SCONOSCIUTO))
		coda.assert_not_called()

	def test_acceso_un_sms_dopo_la_chiamata(self):
		self.risposte(sms_to_missed_callers=1)
		with patch("frappe.enqueue") as coda:
			inbound.nobody_answered(self.provider, call_log=self.chiamata(SCONOSCIUTO))
		self.assertEqual(coda.call_args.kwargs["numero"], SCONOSCIUTO)

	def test_una_volta_al_giorno_dal_mittente_del_centro(self):
		with (
			patch("crm.moduli.richieste.nome_del_centro", return_value="Aurora"),
			patch("crm.api.sms.deliver_via_twilio") as consegna,
		):
			persa.scrivi_a_chi_ha_chiamato("340 999 8877")
			persa.scrivi_a_chi_ha_chiamato(SCONOSCIUTO)
		[doc] = consegna.call_args.args
		self.assertEqual(consegna.call_count, 1)
		self.assertEqual((doc.get("from"), doc.to), (CELLULARE, SCONOSCIUTO))
		self.assertTrue(doc.message.startswith("Aurora: "))
		self.assertIn("/prenota", doc.message)

	def test_mai_un_fisso_un_paese_non_scelto_o_un_numero_a_pagamento(self):
		with patch("crm.api.sms.deliver_via_twilio") as consegna:
			for numero in (STUDIO_NUMBER, "+33612345678", "+39899123456"):
				self.assertFalse(persa.scrivi_a_chi_ha_chiamato(numero))
		consegna.assert_not_called()

	def test_mai_per_la_demo(self):
		with (
			patch("crm.demo.guardie.trattenuto", return_value=True),
			patch("crm.api.sms.deliver_via_twilio") as consegna,
		):
			self.assertFalse(persa.scrivi_a_chi_ha_chiamato(SCONOSCIUTO))
		consegna.assert_not_called()
