# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Where Telnyx calls DottorCloud, on a real site (doc 65).

Nothing is read before Telnyx's signature is right. A call to one of the centre's
numbers rings everyone who answers it at once - their browsers at their SIP
addresses - showing the number called; nobody picks up, and the answering service
takes it. A call from a browser leaves only after DottorCloud's yes, and shows one
of the centre's numbers or the caller's own line, never one the browser made up.
The SMS arrive in the conversation, STOP stops the automatic ones, and how a
message went is kept, in words.
"""

import json
from unittest.mock import patch
from urllib.parse import urlencode

import frappe
from frappe.utils import set_request

from crm.api import sms as sms_api
from crm.integrations.telnyx import api
from crm.telephony import answering, routing
from crm.telephony.telnyx import collegamento
from crm.telephony.telnyx.tests.test_collegamento import TelnyxCase
from crm.tests.test_documenti_del_core import FRONT_DESK, MANAGER

NUMERO_DEL_CENTRO = "+390212345678"
CHI_CHIAMA = "+393331112233"


def sid() -> str:
	"""A call's id: the webhooks commit, as Twilio's do, so each test has its own."""
	return "v3:" + frappe.generate_hash(length=20)


class WebhookCase(TelnyxCase):
	def setUp(self):
		super().setUp()
		self.telnyx.numero(NUMERO_DEL_CENTRO, sms=True)
		self.collega()
		self.risposte(enabled=0)
		self.addCleanup(self._via_la_richiesta)

	def _via_la_richiesta(self):
		frappe.local.request = None
		if hasattr(frappe.local, "crm_answering_settings"):
			del frappe.local.crm_answering_settings

	def risposte(self, **valori):
		doc = frappe.get_single("CRM Answering Settings")
		doc.update(
			{
				"use_working_hours": 0,
				"callback_hours": 3,
				"greeting_source": answering.SOURCE_TEXT,
				"greeting_text": "La richiamiamo entro {hours} ore",
				"language": "it-IT",
				"voice": "alice",
				"ring_seconds": 20,
				"take_messages": 0,
				**valori,
			}
		)
		doc.save(ignore_permissions=True)
		if hasattr(frappe.local, "crm_answering_settings"):
			del frappe.local.crm_answering_settings

	def modulo(self, funzione, firma=True, **valori):
		"""``funzione`` as Telnyx calls it: a form, signed."""
		corpo = urlencode(valori).encode()
		set_request(
			method="POST",
			path="/api/method/x",
			data=corpo,
			content_type="application/x-www-form-urlencoded",
			headers=self.telnyx.firma(corpo) if firma else {},
		)
		return funzione(**valori)

	def evento(self, tipo, payload):
		corpo = json.dumps(
			{"data": {"id": frappe.generate_hash(), "event_type": tipo, "payload": payload}}
		).encode()
		set_request(
			method="POST",
			path="/api/method/x",
			data=corpo,
			content_type="application/json",
			headers=self.telnyx.firma(corpo),
		)
		return api.sms(**json.loads(corpo))

	def agente(self, utente=MANAGER, dispositivo="Computer"):
		frappe.get_doc(
			{
				"doctype": "CRM Telephony Agent",
				"user": utente,
				"mobile_no": "+393480000000",
				"telnyx_number": NUMERO_DEL_CENTRO,
				"call_receiving_device": dispositivo,
			}
		).insert(ignore_permissions=True)
		return collegamento.credenziale(utente)


class LaFirma(WebhookCase):
	def test_senza_firma_niente(self):
		chiamata = sid()
		with self.assertRaises(frappe.PermissionError):
			self.modulo(
				api.incoming_call, firma=False, CallSid=chiamata, From=CHI_CHIAMA, To=NUMERO_DEL_CENTRO
			)
		self.assertFalse(frappe.db.exists("CRM Call Log", chiamata))

	def test_una_firma_di_un_altro_corpo(self):
		chiamata = sid()
		corpo = urlencode({"CallSid": sid()}).encode()
		set_request(
			method="POST",
			path="/api/method/x",
			data=urlencode({"CallSid": chiamata}).encode(),
			content_type="application/x-www-form-urlencoded",
			headers=self.telnyx.firma(corpo),
		)
		with self.assertRaises(frappe.PermissionError):
			api.incoming_call(CallSid=chiamata, From=CHI_CHIAMA, To=NUMERO_DEL_CENTRO)


class InArrivo(WebhookCase):
	def test_squillano_tutti_alla_scrivania(self):
		propria = self.agente()
		chiamata = sid()
		with patch.object(routing, "logged_in", return_value={MANAGER}):
			risposta = self.modulo(
				api.incoming_call,
				CallSid=chiamata,
				From=CHI_CHIAMA,
				To=NUMERO_DEL_CENTRO,
				CallStatus="ringing",
			)
		xml = risposta.get_data(as_text=True)
		self.assertIn(f">sip:{propria['sip_username']}@sip.telnyx.com</Sip>", xml)
		# a browser sees who calls
		self.assertIn(f'callerId="{CHI_CHIAMA}"', xml)
		self.assertIn("crm.integrations.telnyx.api.ring_ended", xml)
		self.assertEqual(
			frappe.db.get_value("CRM Call Log", chiamata, ["type", "telephony_medium"]),
			("Incoming", "Telnyx"),
		)

	def test_un_cellulare_vede_il_numero_del_centro(self):
		self.agente(dispositivo="Phone")
		xml = self.modulo(api.incoming_call, CallSid=sid(), From=CHI_CHIAMA, To=NUMERO_DEL_CENTRO).get_data(
			as_text=True
		)
		self.assertIn("+393480000000</Number>", xml)
		# Telnyx shows on a phone only a number of its own or a verified one
		self.assertIn(f'callerId="{NUMERO_DEL_CENTRO}"', xml)
		# the browser of whoever is at the desk then asks who it is
		frappe.set_user(MANAGER)
		self.assertEqual(api.who_is_calling(NUMERO_DEL_CENTRO), {"number": CHI_CHIAMA})

	def test_nessuno_risponde_la_segreteria(self):
		self.risposte(enabled=1, answer_mode=answering.MODE_RING_FIRST)
		self.agente()
		chiamata = sid()
		with patch.object(routing, "logged_in", return_value={MANAGER}):
			self.modulo(api.incoming_call, CallSid=chiamata, From=CHI_CHIAMA, To=NUMERO_DEL_CENTRO)
		xml = self.modulo(api.ring_ended, CallSid=chiamata, DialCallStatus="no-answer").get_data(as_text=True)
		self.assertIn("La richiamiamo entro 3 ore", xml)
		# the callback is queued: on this call, or on the caller's one already waiting
		self.assertTrue(frappe.db.exists("CRM Call Log", {"from": CHI_CHIAMA, "callback_status": "Pending"}))

	def test_chi_ha_risposto_e_quanto_e_durata(self):
		propria = self.agente()
		chiamata = sid()
		with patch.object(routing, "logged_in", return_value={MANAGER}):
			self.modulo(api.incoming_call, CallSid=chiamata, From=CHI_CHIAMA, To=NUMERO_DEL_CENTRO)
		indirizzo = f"sip:{propria['sip_username']}@sip.telnyx.com"
		self.modulo(
			api.call_status, CallSid=sid(), ParentCallSid=chiamata, CallStatus="in-progress", To=indirizzo
		)
		# a leg that rang elsewhere and lost does not take the answer back
		self.modulo(
			api.call_status, CallSid=sid(), ParentCallSid=chiamata, CallStatus="canceled", To="+39348"
		)
		self.modulo(api.call_status, CallSid=chiamata, CallStatus="completed", CallDuration="95")
		self.assertEqual(
			frappe.db.get_value("CRM Call Log", chiamata, ["receiver", "status", "duration"]),
			(MANAGER, "Completed", 95),
		)

	def test_la_registrazione_si_scarica_subito(self):
		chiamata = sid()
		self.modulo(api.incoming_call, CallSid=chiamata, From=CHI_CHIAMA, To=NUMERO_DEL_CENTRO)
		with patch("crm.telephony.telnyx.registrazioni.accoda") as accoda:
			self.modulo(
				api.recording_ready,
				CallSid=chiamata,
				RecordingUrl="https://s3.example/r.mp3",
				RecordingStatus="completed",
			)
		accoda.assert_called_once_with(chiamata, "https://s3.example/r.mp3")


class DalBrowser(WebhookCase):
	def setUp(self):
		super().setUp()
		frappe.get_doc(
			{
				"doctype": "CRM Caller ID",
				"phone_number": "+390299999999",
				"provider": "telnyx",
				"source": "Account Number",
				"enabled": 1,
				"voice_capable": 1,
			}
		).insert(ignore_permissions=True)
		self.propria = self.agente()

	def chiama_dal_browser(self, numero, mostra=None, utente=MANAGER):
		frappe.set_user(utente)
		esito = api.prepare_call(numero, mostra)
		frappe.set_user("Administrator")
		if not esito["ok"]:
			return esito, None
		self.chiamata = sid()
		risposta = self.modulo(
			api.voice,
			CallSid=self.chiamata,
			From=f"sip:{self.propria['sip_username']}@sip.telnyx.com",
			To=numero,
			ConnectionId=collegamento._impostazioni().credential_connection_id,
		)
		return esito, risposta.get_data(as_text=True)

	def test_il_numero_scelto_del_centro(self):
		_esito, xml = self.chiama_dal_browser("+390611223344", "+390299999999")
		self.assertIn('callerId="+390299999999"', xml)
		self.assertIn("+390611223344</Number>", xml)
		self.assertEqual(
			frappe.db.get_value("CRM Call Log", self.chiamata, ["type", "caller", "from"]),
			("Outgoing", MANAGER, "+390299999999"),
		)

	def test_mai_un_numero_inventato(self):
		_esito, xml = self.chiama_dal_browser("+390611223344", "+390211111111")
		# not one of the centre's: the person's own line
		self.assertIn(f'callerId="{NUMERO_DEL_CENTRO}"', xml)

	def test_mai_un_numero_a_pagamento_ne_un_paese_non_scelto(self):
		esito, _xml = self.chiama_dal_browser("+39899123456")
		self.assertFalse(esito["ok"])
		# and if the browser called all the same, Telnyx hears no
		chiamata = sid()
		xml = self.modulo(
			api.voice, CallSid=chiamata, From="sip:x@sip.telnyx.com", To="+33612345678"
		).get_data(as_text=True)
		self.assertIn("<Hangup />", xml)
		self.assertNotIn("<Dial", xml)
		self.assertFalse(frappe.db.exists("CRM Call Log", chiamata))

	def test_il_gettone(self):
		frappe.set_user(MANAGER)
		gettone = api.generate_access_token()
		self.assertEqual(gettone, {"token": f"jwt.per.{self.propria['sip_username']}"})
		# without one's own line, no phone in the browser
		frappe.set_user(FRONT_DESK)
		self.assertEqual(api.generate_access_token()["error"], "caller_phone_identity_missing")


class GliSms(WebhookCase):
	def test_ricevuto_e_stop(self):
		persona = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Laura", "last_name": "Bassi", "mobile_no": CHI_CHIAMA}
		).insert(ignore_permissions=True)
		self.evento(
			"message.received",
			{
				"from": {"phone_number": CHI_CHIAMA},
				"to": [{"phone_number": NUMERO_DEL_CENTRO}],
				"text": "Buongiorno",
			},
		)
		self.assertTrue(
			frappe.db.exists(
				"CRM SMS Message", {"type": "Incoming", "message": "Buongiorno", "telephony_medium": "Telnyx"}
			)
		)
		self.evento(
			"message.received",
			{
				"from": {"phone_number": CHI_CHIAMA},
				"to": [{"phone_number": NUMERO_DEL_CENTRO}],
				"text": "BASTA",
			},
		)
		self.assertTrue(frappe.db.get_value("CRM Lead", persona.name, "sms_opt_out"))
		# the answer leaves from the number written to
		(risposta,) = self.telnyx.messaggi
		self.assertEqual((risposta["from"], risposta["to"]), (NUMERO_DEL_CENTRO, CHI_CHIAMA))

	def test_lo_stop_che_telnyx_ha_gia_risposto(self):
		persona = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Marco", "last_name": "Neri", "mobile_no": CHI_CHIAMA}
		).insert(ignore_permissions=True)
		self.evento(
			"message.received",
			{
				"from": {"phone_number": CHI_CHIAMA},
				"to": [{"phone_number": NUMERO_DEL_CENTRO}],
				"text": "STOP",
				"autoresponse_type": "STOP",
			},
		)
		self.assertTrue(frappe.db.get_value("CRM Lead", persona.name, "sms_opt_out"))
		self.assertEqual(self.telnyx.messaggi, [])

	def test_mandato_e_come_e_andato(self):
		doc = sms_api.create_sms(
			type="Outgoing", from_number=NUMERO_DEL_CENTRO, to=CHI_CHIAMA, message="Promemoria"
		)
		self.assertEqual(doc.telephony_medium, "Telnyx")
		sms_api.deliver_sms(doc)
		(mandato,) = self.telnyx.messaggi
		self.assertEqual(mandato["messaging_profile_id"], collegamento._impostazioni().messaging_profile_id)
		self.assertEqual(frappe.db.get_value("CRM SMS Message", doc.name, "status"), "Sent")
		self.evento(
			"message.finalized",
			{
				"id": mandato["id"],
				"to": [{"phone_number": CHI_CHIAMA, "status": "delivery_failed"}],
				"errors": [{"code": "40001", "title": "Not Routable"}],
			},
		)
		self.assertEqual(
			frappe.db.get_value("CRM SMS Message", doc.name, ["status", "error_code"]), ("Undelivered", 40001)
		)
		self.assertIn("landline", frappe.db.get_value("CRM SMS Message", doc.name, "error_message"))

	def test_rifiutato_da_telnyx(self):
		doc = sms_api.create_sms(
			type="Outgoing", from_number=NUMERO_DEL_CENTRO, to=CHI_CHIAMA, message="Ciao"
		)
		self.telnyx.rifiuta = (400, {"errors": [{"code": "40300", "title": "Blocked due to STOP message"}]})
		sms_api.deliver_sms(doc)
		self.assertEqual(
			frappe.db.get_value("CRM SMS Message", doc.name, ["status", "error_code"]), ("Failed", 40300)
		)
		self.assertIn("STOP", frappe.db.get_value("CRM SMS Message", doc.name, "error_message"))

	def test_il_mittente_e_quello_del_centro(self):
		frappe.db.set_single_value(
			collegamento.IMPOSTAZIONI, {"sms_from": "Name", "sms_sender_name": "Aurora"}
		)
		from crm.telephony import sms

		self.assertEqual(sms.mittente(), "Aurora")
		frappe.db.set_single_value(
			collegamento.IMPOSTAZIONI, {"sms_from": "Number", "sms_sender_number": NUMERO_DEL_CENTRO}
		)
		self.assertEqual(sms.mittente(), NUMERO_DEL_CENTRO)
