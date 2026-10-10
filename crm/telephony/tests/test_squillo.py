# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Who answers an incoming call, on a real site (doc 52, third part).

A call to the centre's number rings everyone who answers it at once - at the desk
in the browser, on their mobile - for the seconds the centre chose. Nobody picks up,
and the announcement takes the call and queues the callback; without the answering
service the caller hears the apology. When the centre wants it, after the
announcement the caller leaves a message: it lands on the call, and whoever follows
the person is told.
"""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.integrations.twilio import api
from crm.integrations.twilio.twilio_handler import Twilio
from crm.notifiche import regole as N
from crm.telephony import answering, callbacks, inbound, messaggi, routing
from crm.telephony.providers.base import CallInstruction, Message, ProviderNotSupported, Ring
from crm.telephony.providers.twilio import TwilioProvider
from crm.tests.test_documenti_del_core import FRONT_DESK, MANAGER, CoreTestCase
from crm.tests.test_telephony_providers import CALLER, STUDIO_NUMBER, FakeProvider

SECONDA = "core.second@example.com"


class Squilla(FakeProvider):
	"""A carrier that rings several at once, and records what it was asked."""

	def ring(self, ring):
		self.asked.append(("ring", ring))
		return CallInstruction(body="RING", mimetype="text/plain")

	def take_message(self, announcement, message):
		self.asked.append(("take_message", announcement, message))
		return CallInstruction(body=f"MESSAGE::{announcement.text}", mimetype="text/plain")


class SquilloCase(CoreTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.provider = Squilla()
		self.risposte(enabled=1, answer_mode=answering.MODE_RING_FIRST)
		frappe.db.delete("CRM Telephony Agent", {"twilio_number": STUDIO_NUMBER})

	def tearDown(self):
		super().tearDown()
		if hasattr(frappe.local, "crm_answering_settings"):
			del frappe.local.crm_answering_settings

	def risposte(self, **valori):
		doc = frappe.get_single("CRM Answering Settings")
		doc.update(
			{
				"use_working_hours": 0,
				"callback_hours": 3,
				"dedupe_window_hours": 4,
				"greeting_source": answering.SOURCE_TEXT,
				"greeting_text": "La richiamiamo entro {hours} ore",
				"language": "it-IT",
				"voice": "Polly.Bianca",
				"ring_seconds": 20,
				"take_messages": 0,
				"message_prompt": "",
				**valori,
			}
		)
		doc.save()
		if hasattr(frappe.local, "crm_answering_settings"):
			del frappe.local.crm_answering_settings

	def agente(self, utente, dispositivo, cellulare="+393480000000"):
		return frappe.get_doc(
			{
				"doctype": "CRM Telephony Agent",
				"user": utente,
				"mobile_no": cellulare,
				"twilio_number": STUDIO_NUMBER,
				"call_receiving_device": dispositivo,
			}
		).insert(ignore_permissions=True)

	def chiamata(self, **valori):
		log = frappe.get_doc(
			{
				"doctype": "CRM Call Log",
				"id": "CA" + frappe.generate_hash(length=32),
				"to": STUDIO_NUMBER,
				"type": "Incoming",
				"status": "In Progress",
				"telephony_medium": "Twilio",
				**valori,
			}
		)
		setattr(log, "from", valori.get("from", CALLER))
		return log.insert(ignore_permissions=True)


class SquillanoTutti(SquilloCase):
	def test_tutti_insieme_alla_scrivania_e_al_cellulare(self):
		self.agente(MANAGER, "Computer")
		self.agente(FRONT_DESK, "Phone", "+393471112233")
		with patch.object(routing, "logged_in", return_value={MANAGER}):
			inbound.handle_incoming_call(self.provider, CALLER, STUDIO_NUMBER)
		((tipo, squillo),) = self.provider.asked
		self.assertEqual(tipo, "ring")
		self.assertEqual(
			squillo,
			Ring(
				agents=(MANAGER,),
				phones=("+393471112233",),
				caller_id=CALLER,
				seconds=20,
				called=STUDIO_NUMBER,
			),
		)

	def test_chi_non_c_e_non_squilla(self):
		self.agente(MANAGER, "Computer")
		self.agente(FRONT_DESK, "Computer")
		with patch.object(routing, "logged_in", return_value={FRONT_DESK}):
			inbound.handle_incoming_call(self.provider, CALLER, STUDIO_NUMBER)
		self.assertEqual(self.provider.asked[0][1].agents, (FRONT_DESK,))

	def test_i_secondi_scelti_dal_centro_entro_i_limiti(self):
		self.risposte(enabled=1, answer_mode=answering.MODE_RING_FIRST, ring_seconds=35)
		self.assertEqual(answering.ring_seconds(), 35)
		self.risposte(enabled=1, answer_mode=answering.MODE_RING_FIRST, ring_seconds=2)
		self.assertEqual(answering.ring_seconds(), answering.RING_LEAST)
		self.risposte(enabled=1, answer_mode=answering.MODE_RING_FIRST, ring_seconds=0)
		self.assertEqual(answering.ring_seconds(), answering.RING_SECONDS)

	def test_un_operatore_che_squilla_uno_per_volta(self):
		# a carrier without `ring` rings one person as before; several, it says it cannot
		uno = FakeProvider()
		self.assertEqual(uno.ring(Ring(agents=(MANAGER,))).body, f"AGENT::{MANAGER}")
		self.assertEqual(
			uno.ring(Ring(phones=("+393471112233",), caller_id=CALLER)).body, "PHONE::+393471112233"
		)
		with self.assertRaises(ProviderNotSupported):
			uno.ring(Ring(agents=(MANAGER, FRONT_DESK)))


class NessunoRisponde(SquilloCase):
	def test_la_segreteria_e_la_richiamata(self):
		log = self.chiamata()
		istruzione = inbound.nobody_answered(self.provider, call_log=log)
		self.assertIn("3 ore", istruzione.body)
		self.assertEqual(frappe.db.get_value("CRM Call Log", log.name, "callback_status"), callbacks.PENDING)

	def test_senza_segreteria_le_scuse(self):
		self.risposte(enabled=0)
		istruzione = inbound.nobody_answered(self.provider, call_log=self.chiamata())
		self.assertEqual(self.provider.asked[0][0], "say")
		self.assertNotIn("3 ore", istruzione.body)

	def test_e_un_messaggio_quando_il_centro_lo_vuole(self):
		self.risposte(enabled=1, answer_mode=answering.MODE_RING_FIRST, take_messages=1, message_seconds=90)
		inbound.nobody_answered(self.provider, call_log=self.chiamata())
		((tipo, annuncio, messaggio),) = self.provider.asked
		self.assertEqual(tipo, "take_message")
		self.assertIn("3 ore", annuncio.text)
		self.assertEqual(
			messaggio,
			Message(prompt=answering.message_prompt(), seconds=90, language="it-IT", voice="Polly.Bianca"),
		)
		self.assertIn("tone", answering.message_prompt())

	def test_le_parole_prima_del_segnale_sono_del_centro(self):
		self.risposte(enabled=1, take_messages=1, message_prompt="Lasci un messaggio dopo il segnale.")
		self.assertEqual(answering.message_prompt(), "Lasci un messaggio dopo il segnale.")


class InTwiML(IntegrationTestCase):
	def connettore(self):
		settings = frappe._dict(
			{
				"account_sid": "AC" + "1" * 32,
				"twiml_sid": "AP1",
				"api_key": "SK1",
				"record_calls": 0,
				"recording_notice": "",
				"get_password": lambda *args, **kwargs: "secret",
			}
		)
		with patch.object(Twilio, "get_twilio_client", return_value=None):
			return Twilio(settings=settings)

	def test_un_dial_con_tutti_e_dove_tornare(self):
		xml = (
			self.connettore()
			.generate_ring_response(
				Ring(
					agents=("anna@aurora.example",), phones=("+393471112233",), caller_id=CALLER, seconds=20
				),
				"https://aurora.example/api/method/crm.integrations.twilio.api.ring_ended",
			)
			.to_xml()
		)
		self.assertIn('timeout="20"', xml)
		self.assertIn('answerOnBridge="true"', xml)
		self.assertIn("crm.integrations.twilio.api.ring_ended", xml)
		self.assertIn("<Client", xml)
		self.assertIn("anna(at)aurora.example</Client>", xml)
		self.assertIn("+393471112233</Number>", xml)
		self.assertIn(f'callerId="{CALLER}"', xml)

	def test_il_messaggio_dopo_l_annuncio(self):
		from crm.telephony.providers.base import Announcement

		xml = (
			TwilioProvider()
			.take_message(
				Announcement(text="La richiamiamo entro 3 ore", language="it-IT", voice="Polly.Bianca"),
				Message(
					prompt="Lasci un messaggio dopo il segnale.",
					seconds=90,
					language="it-IT",
					voice="Polly.Bianca",
				),
			)
			.body
		)
		self.assertLess(xml.index("La richiamiamo"), xml.index("Lasci un messaggio"))
		self.assertLess(xml.index("Lasci un messaggio"), xml.index("<Record"))
		self.assertIn('maxLength="90"', xml)
		self.assertIn('playBeep="true"', xml)
		# without its own action Twilio would ask the call's address again, from the start
		self.assertIn("crm.integrations.twilio.api.message_taken", xml)
		self.assertIn("crm.integrations.twilio.api.message_recorded", xml)


class IlMessaggio(SquilloCase):
	"""What Twilio sends back, with its signature checked by `validate_twilio_request`."""

	def setUp(self):
		super().setUp()
		frappe.db.delete("CRM Notification", {"type": "Call"})
		for dove in ("crm.integrations.twilio.api.validate_twilio_request",):
			finto = patch(dove, return_value=None)
			finto.start()
			self.addCleanup(finto.stop)
		finto = patch("crm.telephony.transcription.transcribes_automatically", return_value=False)
		finto.start()
		self.addCleanup(finto.stop)
		# the webhooks commit for Twilio's sake; a test keeps everything to roll back
		finto = patch.object(frappe.db, "commit")
		finto.start()
		self.addCleanup(finto.stop)

	def xml(self, risposta):
		return risposta.get_data(as_text=True)

	def test_risposto_niente_altro(self):
		xml = self.xml(api.ring_ended(CallSid="CA1", DialCallStatus="completed"))
		self.assertIn("<Hangup", xml)
		self.assertNotIn("<Say", xml)

	def test_nessuno_ha_risposto_la_segreteria(self):
		log = self.chiamata()
		xml = self.xml(api.ring_ended(CallSid=log.name, DialCallStatus="no-answer"))
		self.assertIn("La richiamiamo entro 3 ore", xml)
		self.assertEqual(frappe.db.get_value("CRM Call Log", log.name, "callback_status"), callbacks.PENDING)

	def test_lasciato_e_detto_a_chi_segue_la_persona(self):
		persona = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Laura",
				"last_name": "Rossi",
				"mobile_no": CALLER,
				"lead_owner": MANAGER,
			}
		).insert(ignore_permissions=True)
		log = self.chiamata(reference_doctype="CRM Lead", reference_docname=persona.name)
		api.message_recorded(
			CallSid=log.name, RecordingUrl="https://api.twilio.com/rec/RE1", RecordingDuration="12"
		)
		self.assertEqual(
			frappe.db.get_value("CRM Call Log", log.name, ["recording_url", "left_message"]),
			("https://api.twilio.com/rec/RE1", 1),
		)
		avviso = frappe.get_all(
			"CRM Notification",
			{"type": "Call"},
			[
				"to_user",
				"sentence",
				"sentence_args",
				"reference_doctype",
				"reference_name",
				"notification_type_doc",
			],
		)
		self.assertEqual(len(avviso), 1)
		self.assertEqual((avviso[0].to_user, avviso[0].sentence), (MANAGER, N.MESSAGGIO_IN_SEGRETERIA))
		self.assertIn("Laura Rossi", avviso[0].sentence_args)
		self.assertEqual((avviso[0].reference_doctype, avviso[0].reference_name), ("CRM Lead", persona.name))
		self.assertEqual(avviso[0].notification_type_doc, log.name)

	def test_il_segnale_e_poi_niente_non_e_un_messaggio(self):
		log = self.chiamata()
		api.message_recorded(
			CallSid=log.name, RecordingUrl="https://api.twilio.com/rec/RE2", RecordingDuration="0"
		)
		self.assertEqual(frappe.db.get_value("CRM Call Log", log.name, "left_message"), 0)
		self.assertFalse(frappe.db.count("CRM Notification", {"type": "Call"}))

	def test_grazie_solo_a_chi_ha_lasciato_qualcosa(self):
		self.assertIn("<Say", self.xml(api.message_taken(CallSid="CA1", RecordingDuration="8")))
		self.assertNotIn("<Say", self.xml(api.message_taken(CallSid="CA1", RecordingDuration="0")))

	def test_senza_chi_segue_la_persona_chi_risponde_al_numero(self):
		self.agente(FRONT_DESK, "Computer")
		self.assertEqual(messaggi.chi_avvisare("+390699999999", STUDIO_NUMBER), [FRONT_DESK])

	def test_altrimenti_chi_legge_tutte_le_chiamate(self):
		avvisati = messaggi.chi_avvisare("+390699999999", "+390211111111")
		self.assertIn(MANAGER, avvisati)
		self.assertIn(FRONT_DESK, avvisati)
		self.assertNotIn("Administrator", avvisati)
