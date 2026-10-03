# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A number of the centre's, verified to be shown on calls (doc 52).

Twilio calls the number and asks for the code the page shows: no document. The
row waits switched off and is switched on when Twilio says the number is verified
- at the end of its call, or when the page or the hourly check asks; whoever asked
hears of it unless the page was watching. A number of the space is not verified
again; one verified in the console is found; one verified is removed from Twilio
here. A verified Italian landline is shown in Italy only as far as the operators
let it: the call warns.
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

import frappe
from frappe.utils import now_datetime

from crm.integrations.twilio import api
from crm.notifiche import api as notifiche
from crm.notifiche import regole as N
from crm.telephony import caller_ids, collegamento, uscita, verificati
from crm.telephony import uscita_regole as U
from crm.telephony import verificati_regole as R
from crm.telephony.tests.test_collegamento import TwilioCase
from crm.tests.test_documenti_del_core import FRONT_DESK, MANAGER

FISSO = "+390212345678"
ROMA = "+390687654321"
CELLULARE = "+393331234567"
LONDRA = "+442079460958"


class LeRegole(unittest.TestCase):
	def test_il_nome_che_twilio_tiene(self):
		self.assertEqual(R.nome_per_twilio(" Reception ", FISSO), "Reception")
		self.assertEqual(R.nome_per_twilio("", FISSO), FISSO)
		self.assertEqual(len(R.nome_per_twilio("x" * 90, FISSO)), 64)

	def test_l_interno_come_twilio_lo_prende(self):
		self.assertEqual(R.interno(" ww 1-0 W2 "), ("ww10w2", ""))
		self.assertEqual(R.interno(None), ("", ""))
		self.assertEqual(R.interno("#1*"), ("#1*", ""))
		self.assertIn("digits", R.interno("interno 3")[1])
		self.assertIn("digits", R.interno("1" * 33)[1])

	def test_l_attesa_da_0_a_60_secondi(self):
		self.assertEqual(R.attesa(None), (0, ""))
		self.assertEqual(R.attesa(""), (0, ""))
		self.assertEqual(R.attesa("30"), (30, ""))
		self.assertEqual(R.attesa(60), (60, ""))
		self.assertIn("60", R.attesa(61)[1])
		self.assertIn("60", R.attesa(-1)[1])
		self.assertIn("60", R.attesa("presto")[1])

	def test_come_e_andata_per_twilio(self):
		self.assertEqual(R.esito("success"), R.VERIFICATO)
		self.assertEqual(R.esito(" FAILED "), R.NON_VERIFICATO)
		self.assertEqual(R.esito(None), "")
		self.assertEqual(R.esito("in-progress"), "")

	def test_un_quarto_d_ora_poi_non_e_avvenuta(self):
		adesso = datetime(2026, 10, 2, 10, 0)
		self.assertFalse(R.scaduta(adesso - timedelta(minutes=10), adesso))
		self.assertTrue(R.scaduta(adesso - timedelta(minutes=16), adesso))
		self.assertTrue(R.scaduta(None, adesso))

	def test_i_rifiuti_di_twilio_in_parole(self):
		self.assertIn("verified already", R.rifiuto(21450))
		self.assertIn("one of the centre's numbers", R.rifiuto("21449"))
		self.assertEqual(R.rifiuto(99999), "")
		self.assertEqual(R.rifiuto(None), "")
		for codice, frase in R.RIFIUTI.items():
			self.assertTrue(frase.endswith("."), codice)

	def test_un_fisso_verificato_in_italia_e_incerto(self):
		self.assertTrue(U.incerta_in_italia(FISSO, ROMA, True))
		self.assertTrue(U.incerta_in_italia(FISSO, CELLULARE, True))
		# a number of Twilio's is shown for certain, abroad nothing is said
		self.assertFalse(U.incerta_in_italia(FISSO, ROMA, False))
		self.assertFalse(U.incerta_in_italia(FISSO, LONDRA, True))
		# an Italian mobile is blocked outright: another warning says so
		self.assertFalse(U.incerta_in_italia(CELLULARE, ROMA, True))


class LaVerifica(TwilioCase):
	def setUp(self):
		super().setUp()
		frappe.db.set_single_value(collegamento.IMPOSTAZIONI, "allowed_countries", "IT")
		self.collega()
		self.spazio_sid = self.spazio().sid
		frappe.db.delete("CRM Notification", {"notification_type_doctype": "CRM Caller ID"})
		for numero in (FISSO, ROMA, CELLULARE):
			frappe.cache.delete_value(verificati._GUARDA.format(numero))
		self.addCleanup(frappe.set_user, "Administrator")

	def chiedi(self, numero=FISSO, **valori):
		frappe.set_user(MANAGER)
		esito = verificati.verify_number(numero, **valori)
		frappe.set_user("Administrator")
		return esito

	def risponde(self, verifica, esito="success", sid=None, **altro):
		"""Twilio's StatusCallback at the end of its call."""
		from crm.integrations.twilio.twilio_handler import Twilio

		with patch("crm.integrations.twilio.api.validate_twilio_request", return_value=Twilio.connect()):
			return api.caller_id_verified(
				AccountSid=verifica.account_sid,
				CallSid=verifica.call_sid,
				To=verifica.phone_number,
				CallStatus="completed",
				VerificationStatus=esito,
				OutgoingCallerIdSid=sid,
				**altro,
			)

	def avvisi(self):
		return frappe.get_all(
			"CRM Notification",
			filters={"notification_type_doctype": "CRM Caller ID"},
			fields=["to_user", "type", "sentence", "notification_type_doc"],
		)

	def test_twilio_chiama_e_il_numero_aspetta_spento(self):
		esito = self.chiedi("02 1234 5678", label="Reception", extension="ww 1", call_delay="5")

		(verifica,) = self.mondo.verifiche
		# in the space, never in the centre's own account
		self.assertEqual(verifica.account_sid, self.spazio_sid)
		self.assertEqual((verifica.phone_number, verifica.friendly_name), (FISSO, "Reception"))
		self.assertEqual((verifica.extension, verifica.call_delay), ("ww1", 5))
		self.assertTrue(verifica.status_callback.endswith(verificati.ESITO))
		self.assertEqual(verifica.status_callback_method, "POST")
		# the code goes to the page, which shows it
		self.assertEqual(esito["validation_code"], verifica.validation_code)
		self.assertEqual(esito["status"], R.IN_ATTESA)
		self.assertTrue(esito["uncertain_in_italy"])

		riga = frappe.get_doc("CRM Caller ID", FISSO)
		self.assertEqual(
			(riga.enabled, riga.source, riga.verification_status, riga.verification_requested_by),
			(0, caller_ids.SOURCE_VERIFIED, R.IN_ATTESA, MANAGER),
		)
		self.assertEqual(riga.verification_call_sid, verifica.call_sid)
		self.assertNotIn(FISSO, caller_ids.usable_for_outbound())

	def test_il_codice_digitato_e_twilio_lo_dice(self):
		self.chiedi()
		(verifica,) = self.mondo.verifiche
		verificato = self.mondo.codice_digitato(verifica)
		self.risponde(verifica, sid=verificato.sid)

		riga = frappe.get_doc("CRM Caller ID", FISSO)
		self.assertEqual((riga.enabled, riga.verification_status), (1, R.VERIFICATO))
		self.assertEqual(riga.provider_sid, verificato.sid)
		self.assertTrue(riga.verified_on)
		self.assertIn(FISSO, caller_ids.usable_for_outbound())
		# whoever asked hears of it, once
		self.risponde(verifica, sid=verificato.sid)
		self.assertEqual(
			self.avvisi(),
			[
				{
					"to_user": MANAGER,
					"type": "Phone",
					"sentence": N.NUMERO_VERIFICATO,
					"notification_type_doc": FISSO,
				}
			],
		)

	def test_l_avviso_apre_i_numeri(self):
		self.chiedi()
		(verifica,) = self.mondo.verifiche
		self.risponde(verifica, sid=self.mondo.codice_digitato(verifica).sid)
		frappe.set_user(MANAGER)
		(riga,) = [r for r in notifiche.get_notifications()["rows"] if r["kind"] == "phone"]
		self.assertEqual(riga["settings"], {"page": "Telephony", "step": "caller-id-settings"})

	def test_nessuno_risponde(self):
		self.chiedi()
		(verifica,) = self.mondo.verifiche
		self.mondo.codice_digitato(verifica, giusto=False)
		self.risponde(verifica, esito="failed")

		riga = frappe.get_doc("CRM Caller ID", FISSO)
		self.assertEqual((riga.enabled, riga.verification_status), (0, R.NON_VERIFICATO))
		self.assertEqual([a.sentence for a in self.avvisi()], [N.NUMERO_NON_VERIFICATO])
		# and it cannot be switched on by hand: Twilio would refuse the call
		frappe.set_user(MANAGER)
		with self.assertRaises(frappe.ValidationError):
			caller_ids.set_enabled(FISSO, True)

	def test_senza_la_firma_di_twilio_niente(self):
		self.chiedi()
		(verifica,) = self.mondo.verifiche
		with self.assertRaises(frappe.PermissionError):
			api.caller_id_verified(
				AccountSid=self.spazio_sid,
				CallSid=verifica.call_sid,
				To=FISSO,
				VerificationStatus="success",
				OutgoingCallerIdSid="PN" + "0" * 32,
			)
		self.assertEqual(frappe.db.get_value("CRM Caller ID", FISSO, "verification_status"), R.IN_ATTESA)

	def test_la_pagina_che_aspetta_lo_chiede_a_twilio(self):
		self.chiedi()
		(verifica,) = self.mondo.verifiche
		frappe.set_user(MANAGER)
		self.assertEqual(verificati.verification_state(FISSO)["status"], R.IN_ATTESA)
		verificato = self.mondo.codice_digitato(verifica)
		# Twilio could not reach the site: the page finds it all the same
		stato = verificati.verification_state(FISSO)
		self.assertEqual((stato["status"], stato["enabled"]), (R.VERIFICATO, True))
		self.assertEqual(frappe.db.get_value("CRM Caller ID", FISSO, "provider_sid"), verificato.sid)
		frappe.set_user("Administrator")
		# the page was watching: nobody needs a notification, not even when Twilio
		# says it later
		self.risponde(verifica, sid=verificato.sid)
		self.assertEqual(self.avvisi(), [])

	def test_la_pagina_guardava_twilio_lo_dice(self):
		self.chiedi()
		(verifica,) = self.mondo.verifiche
		frappe.set_user(MANAGER)
		verificati.verification_state(FISSO)
		frappe.set_user("Administrator")
		self.risponde(verifica, sid=self.mondo.codice_digitato(verifica).sid)
		self.assertEqual(frappe.db.get_value("CRM Caller ID", FISSO, "verification_status"), R.VERIFICATO)
		self.assertEqual(self.avvisi(), [])

	def test_dopo_un_quarto_d_ora_non_e_avvenuta(self):
		self.chiedi()
		frappe.db.set_value(
			"CRM Caller ID", FISSO, "verification_requested_on", now_datetime() - timedelta(minutes=20)
		)
		frappe.set_user(MANAGER)
		self.assertEqual(verificati.verification_state(FISSO)["status"], R.NON_VERIFICATO)

	def test_ogni_ora_si_ritrova(self):
		self.chiedi()
		(verifica,) = self.mondo.verifiche
		self.mondo.codice_digitato(verifica)
		# nobody told DottorCloud, nobody was looking: the hourly check finds it
		collegamento.assicura()
		riga = frappe.get_doc("CRM Caller ID", FISSO)
		self.assertEqual((riga.enabled, riga.verification_status), (1, R.VERIFICATO))
		self.assertEqual([a.sentence for a in self.avvisi()], [N.NUMERO_VERIFICATO])

	def test_ogni_ora_una_verifica_dimenticata_finisce(self):
		self.chiedi(ROMA)
		frappe.db.set_value(
			"CRM Caller ID", ROMA, "verification_requested_on", now_datetime() - timedelta(hours=2)
		)
		collegamento.assicura()
		self.assertEqual(frappe.db.get_value("CRM Caller ID", ROMA, "verification_status"), R.NON_VERIFICATO)

	def test_un_numero_dello_spazio_non_si_verifica(self):
		self.mondo.numero(self.spazio_sid, FISSO)
		caller_ids.sync("twilio")
		with self.assertRaises(frappe.ValidationError) as errore:
			self.chiedi()
		self.assertIn("one of the centre's numbers", str(errore.exception))
		self.assertEqual(self.mondo.verifiche, [])

	def test_gia_verificato_nella_console(self):
		verificato = self.mondo.verificato(self.spazio_sid, FISSO, "Reception")
		esito = self.chiedi()
		self.assertEqual(esito["status"], R.VERIFICATO)
		self.assertNotIn("validation_code", esito)
		riga = frappe.get_doc("CRM Caller ID", FISSO)
		self.assertEqual((riga.enabled, riga.provider_sid, riga.label), (1, verificato.sid, "Reception"))
		# verified already here: asked again, it is said
		with self.assertRaises(frappe.ValidationError):
			self.chiedi()

	def test_dove_e_cosa_non_si_verifica(self):
		for numero in (LONDRA, "+39899123456", "telefono"):
			with self.assertRaises(frappe.ValidationError, msg=numero):
				self.chiedi(numero)
		with self.assertRaises(frappe.ValidationError):
			self.chiedi(extension="interno 3")
		with self.assertRaises(frappe.ValidationError):
			self.chiedi(call_delay=90)
		self.assertEqual(self.mondo.verifiche, [])

	def test_solo_chi_configura_il_telefono(self):
		frappe.set_user(FRONT_DESK)
		for chiamata in (
			lambda: verificati.verify_number(FISSO),
			lambda: verificati.verification_state(FISSO),
			lambda: verificati.remove_verified(FISSO),
		):
			with self.assertRaises(frappe.PermissionError):
				chiamata()

	def test_togliere_un_numero_verificato(self):
		self.mondo.verificato(self.spazio_sid, FISSO)
		caller_ids.sync("twilio")
		frappe.db.delete("CRM Telephony Agent", {"user": MANAGER})
		frappe.get_doc(
			{
				"doctype": "CRM Telephony Agent",
				"user": MANAGER,
				"twilio_number": FISSO,
				"call_receiving_device": "Computer",
			}
		).insert(ignore_permissions=True)

		frappe.set_user(MANAGER)
		esito = verificati.remove_verified(FISSO)
		frappe.set_user("Administrator")
		self.assertEqual(self.mondo.verificati[self.spazio_sid], [])
		self.assertEqual(esito["lines"], 1)
		riga = frappe.get_doc("CRM Caller ID", FISSO)
		self.assertEqual((riga.enabled, riga.verification_status, riga.provider_sid), (0, "", None))
		self.assertNotIn(FISSO, caller_ids.usable_for_outbound())

	def test_un_numero_dello_spazio_non_si_toglie_qui(self):
		self.mondo.numero(self.spazio_sid, ROMA)
		caller_ids.sync("twilio")
		frappe.set_user(MANAGER)
		with self.assertRaises(frappe.ValidationError):
			verificati.remove_verified(ROMA)

	def test_dello_spazio_e_verificato_resta_dello_spazio(self):
		self.mondo.numero(self.spazio_sid, FISSO)
		self.mondo.verificato(self.spazio_sid, FISSO)
		caller_ids.sync("twilio")
		self.assertEqual(frappe.db.get_value("CRM Caller ID", FISSO, "source"), caller_ids.SOURCE_ACCOUNT)

	def test_la_lista_tiene_i_sid_e_non_si_riscrive(self):
		numero = self.mondo.numero(self.spazio_sid, ROMA)
		caller_ids.sync("twilio")
		self.assertEqual(frappe.db.get_value("CRM Caller ID", ROMA, "provider_sid"), numero.sid)
		prima = frappe.db.get_value("CRM Caller ID", ROMA, "modified")
		caller_ids.sync("twilio")
		self.assertEqual(frappe.db.get_value("CRM Caller ID", ROMA, "modified"), prima)

	def test_una_riga_scritta_a_mano_non_si_mostra(self):
		frappe.get_doc(
			{
				"doctype": "CRM Caller ID",
				"phone_number": ROMA,
				"provider": "twilio",
				"source": caller_ids.SOURCE_MANUAL,
				"voice_capable": 1,
				"enabled": 1,
			}
		).insert(ignore_permissions=True)
		self.assertNotIn(ROMA, caller_ids.usable_for_outbound())

	def test_la_chiamata_in_italia_avvisa(self):
		self.mondo.verificato(self.spazio_sid, FISSO)
		self.mondo.numero(self.spazio_sid, ROMA)
		caller_ids.sync("twilio")
		frappe.set_user(MANAGER)
		numeri = {n["number"]: n for n in uscita.get_outbound_numbers()["numbers"]}
		self.assertTrue(numeri[FISSO]["verified"])
		self.assertFalse(numeri[ROMA]["verified"])
		self.assertTrue(uscita.check_number(CELLULARE, FISSO)["uncertain_in_italy"])
		self.assertFalse(uscita.check_number(CELLULARE, ROMA)["uncertain_in_italy"])
