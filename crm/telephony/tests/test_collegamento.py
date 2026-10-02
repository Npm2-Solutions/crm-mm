# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's Twilio account, connected from DottorCloud, on a real site (doc 52).

The manager of Centro Aurora pastes the two codes of the centre's account once.
DottorCloud makes its space there, with its key and its app, and keeps only the
space's codes: the account's token is gone with the request. Connecting again finds
the same space, codes of a subaccount make it the space, and every hour what
somebody changed in the console is put back - never in an account connected by
hand, which may hold other sites' numbers. Disconnected, the key goes and the space
stays. The agency's account is the agency's to connect, and to change.
"""

from unittest.mock import patch

import frappe

from crm import marchio
from crm.permissions import livelli
from crm.telephony import collegamento
from crm.telephony import collegamento_regole as R
from crm.telephony.tests.twilio_finto import Mondo
from crm.tests.test_documenti_del_core import AGENCY, FRONT_DESK, MANAGER, CoreTestCase

VOCE = "/api/method/crm.integrations.twilio.api.twilio_incoming_call_handler"
SMS = "/api/method/crm.integrations.twilio.api.incoming_sms_handler"
APP = "/api/method/crm.integrations.twilio.api.voice"
#: What a connection writes, put back to nothing before each test.
VUOTE = {
	"enabled": 0,
	"account_sid": "",
	"api_key": "",
	"twiml_sid": "",
	"app_name": "",
	"account_owner": "",
	"main_account_sid": "",
	"main_account_name": "",
	"space_sid": "",
	"space_name": "",
	"connected_on": None,
	"connected_by": None,
	"webhook_base_url": "",
}


class TwilioCase(CoreTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		piano = frappe.get_single("CRM Plan")
		piano.set("modules", [{"module": "telefono", "status": "Active"}])
		piano.save()
		livelli.dimentica_cache()
		frappe.db.set_single_value(collegamento.IMPOSTAZIONI, VUOTE)
		frappe.db.delete("CRM Caller ID", {"provider": "twilio"})
		self.mondo = Mondo()
		self.centro = self.mondo.conto("Centro Aurora")
		for dove in (
			"crm.telephony.collegamento.Client",
			"crm.integrations.twilio.twilio_handler.TwilioClient",
		):
			finto = patch(dove, self.mondo.client)
			finto.start()
			self.addCleanup(finto.stop)

	def collega(self, utente=MANAGER, conto=None):
		conto = conto or self.centro
		frappe.set_user(utente)
		stato = collegamento.connect_twilio(conto.sid, conto.auth_token)
		frappe.set_user("Administrator")
		return stato

	def impostazioni(self):
		return frappe.get_single(collegamento.IMPOSTAZIONI)

	def spazio(self):
		(spazio,) = self.mondo.sottoconti(self.centro.sid)
		return spazio


class IlCentroCollegaIlSuoAccount(TwilioCase):
	def test_lo_spazio_le_chiavi_e_niente_altro(self):
		self.mondo.numero(self.centro.sid, "+390212345678", voice_url="https://altro.example/voce")
		stato = self.collega()

		spazio = self.spazio()
		self.assertEqual(spazio.friendly_name, R.nome_dello_spazio(frappe.utils.get_url(), marchio.nome()))
		self.assertTrue(spazio.friendly_name.startswith(f"{marchio.nome()} · "))
		doc = self.impostazioni()
		self.assertEqual(
			(doc.enabled, doc.account_sid, doc.account_owner, doc.main_account_sid, doc.space_sid),
			(1, spazio.sid, R.CENTRO, self.centro.sid, spazio.sid),
		)
		self.assertEqual((doc.main_account_name, doc.space_name), ("Centro Aurora", spazio.friendly_name))
		# the space's token is kept, the account's never
		self.assertEqual(doc.get_password("auth_token"), spazio.auth_token)
		self.assertNotEqual(doc.get_password("auth_token"), self.centro.auth_token)
		# its key and its app, in the space
		(chiave,) = self.mondo.chiavi[spazio.sid]
		(app,) = self.mondo.app[spazio.sid]
		self.assertEqual((doc.api_key, doc.get_password("api_secret")), (chiave.sid, chiave.secret))
		self.assertEqual((doc.twiml_sid, app.friendly_name), (app.sid, "DottorCloud"))
		self.assertTrue(app.voice_url.endswith(APP))
		# the rest of the account is not touched
		self.assertEqual((self.mondo.chiavi[self.centro.sid], self.mondo.app[self.centro.sid]), ([], []))
		self.assertEqual(self.mondo.numeri[self.centro.sid][0].voice_url, "https://altro.example/voce")
		self.assertFalse(
			[c for c in self.mondo.cambi if c[0] == self.centro.sid and c[1] != "create Account"]
		)
		# what the page reads: masked, and whose
		self.assertTrue(stato["connected"])
		self.assertEqual(stato["owner"], R.CENTRO)
		self.assertEqual(
			stato["main_account"], {"sid": R.mascherato(self.centro.sid), "name": "Centro Aurora"}
		)
		self.assertNotIn(self.centro.sid, frappe.as_json(stato))
		self.assertNotIn(spazio.auth_token, frappe.as_json(stato))

	def test_ricollegando_ritrova_lo_spazio(self):
		self.collega()
		prima = self.impostazioni().api_key
		self.collega()
		spazio = self.spazio()
		# one space, one key of DottorCloud's: the one of before is gone
		self.assertEqual([c.sid for c in self.mondo.chiavi[spazio.sid]], [self.impostazioni().api_key])
		self.assertNotEqual(self.impostazioni().api_key, prima)
		self.assertEqual(len(self.mondo.app[spazio.sid]), 1)

	def test_uno_spazio_sospeso_si_risveglia_uno_chiuso_no(self):
		self.collega()
		spazio = self.spazio()
		spazio.status = "suspended"
		self.collega()
		self.assertEqual((self.spazio().status, self.impostazioni().space_sid), ("active", spazio.sid))
		spazio.status = "closed"
		self.collega()
		nuovo = [c for c in self.mondo.sottoconti(self.centro.sid) if c.status == "active"]
		self.assertEqual(len(nuovo), 1)
		self.assertNotEqual(nuovo[0].sid, spazio.sid)
		self.assertEqual(self.impostazioni().space_sid, nuovo[0].sid)

	def test_i_codici_di_un_sottoaccount_ne_fanno_lo_spazio(self):
		fatto_a_mano = self.mondo.conto("Aurora dell'agenzia", padre=self.centro.sid)
		self.mondo.numero(fatto_a_mano.sid, "+393331234567", sms=True)
		stato = self.collega(conto=fatto_a_mano)
		doc = self.impostazioni()
		self.assertEqual((doc.account_sid, doc.space_sid), (fatto_a_mano.sid, fatto_a_mano.sid))
		self.assertEqual((doc.main_account_sid, doc.main_account_name), (self.centro.sid, ""))
		self.assertEqual(doc.get_password("auth_token"), fatto_a_mano.auth_token)
		self.assertEqual(len(self.mondo.sottoconti(self.centro.sid)), 1)
		# its number now reaches DottorCloud, calls and messages
		(numero,) = self.mondo.numeri[fatto_a_mano.sid]
		self.assertTrue(numero.voice_url.endswith(VOCE))
		self.assertTrue(numero.sms_url.endswith(SMS))
		self.assertEqual(stato["repaired"], ["+393331234567"])
		self.assertEqual(
			frappe.db.get_value("CRM Caller ID", "+393331234567", ["routes_to_crm", "sms_capable"]), (1, 1)
		)

	def test_i_codici_sbagliati_non_arrivano_a_twilio(self):
		frappe.set_user(MANAGER)
		for sid, auth_token in (
			("", "x"),
			("AC123", "0" * 32),
			(self.centro.sid, ""),
			(self.centro.sid, "corto"),
		):
			with self.assertRaises(frappe.ValidationError):
				collegamento.connect_twilio(sid, auth_token)
		self.assertEqual(self.mondo.clienti, [])
		# the right shape, the wrong token: Twilio says no, in words
		with self.assertRaises(frappe.ValidationError) as detto:
			collegamento.connect_twilio(self.centro.sid, "f" * 32)
		self.assertIn("Twilio does not recognise these codes", str(detto.exception))
		self.assertFalse(self.impostazioni().enabled)

	def test_spazi_e_a_capo_copiati_non_contano(self):
		frappe.set_user(MANAGER)
		collegamento.connect_twilio(f"  {self.centro.sid}\n", f" {self.centro.auth_token} ")
		self.assertEqual(self.impostazioni().main_account_sid, self.centro.sid)


class OgniOraRimetteAPosto(TwilioCase):
	def test_l_app_e_i_numeri_cambiati_nella_console(self):
		self.collega()
		spazio = self.spazio()
		altro = self.mondo.numero(
			spazio.sid,
			"+390612345678",
			voice_url="https://vecchio.example/voce",
			voice_application_sid="APvecchia",
		)
		messaggi = self.mondo.numero(spazio.sid, "+393339876543", sms=True, sms_method="GET")
		tronco = self.mondo.numero(spazio.sid, "+390287654321", trunk_sid="TKdelcentro", voice_url="sip")
		(app,) = self.mondo.app[spazio.sid]
		app.voice_url = "https://vecchio.example/app"

		collegamento.assicura()
		self.assertTrue(altro.voice_url.endswith(VOCE))
		self.assertEqual((altro.voice_method, altro.voice_application_sid), ("POST", ""))
		self.assertTrue(messaggi.sms_url.endswith(SMS))
		self.assertEqual(messaggi.sms_method, "POST")
		self.assertEqual(tronco.voice_url, "sip")
		self.assertTrue(app.voice_url.endswith(APP))

		# all in place: nothing more is asked
		quanti = len(self.mondo.cambi)
		collegamento.assicura()
		self.assertEqual(len(self.mondo.cambi), quanti)

	def test_un_account_collegato_a_mano_non_si_tocca(self):
		numero = self.mondo.numero(
			self.centro.sid, "+390212345678", voice_url="https://altro-sito.example/voce"
		)
		impostazioni = self.impostazioni()
		impostazioni.update(
			{"enabled": 1, "account_sid": self.centro.sid, "auth_token": self.centro.auth_token}
		)
		impostazioni.flags.dal_collegamento = True
		impostazioni.save(ignore_permissions=True)

		collegamento.assicura()
		frappe.set_user(AGENCY)
		stato = collegamento.check_twilio_connection()
		self.assertTrue(stato["ok"])
		self.assertEqual((stato["owner"], stato["repaired"]), ("Manual", []))
		self.assertEqual(numero.voice_url, "https://altro-sito.example/voce")
		self.assertEqual(self.mondo.cambi, [])

	def test_controlla_dice_com_e_l_account(self):
		self.centro.type = "Trial"
		self.collega()
		frappe.set_user(MANAGER)
		stato = collegamento.check_twilio_connection()
		self.assertTrue(stato["ok"])
		self.assertEqual(stato["type"], "Trial")
		self.assertIn("trial account", stato["note"])
		# a token taken back in the console: said, not thrown
		self.spazio().auth_token = "0" * 32
		stato = collegamento.check_twilio_connection()
		self.assertFalse(stato["ok"])
		self.assertIn("Twilio does not recognise these codes", stato["error"])


class Scollegare(TwilioCase):
	def test_la_chiave_va_lo_spazio_resta(self):
		self.collega()
		spazio = self.spazio()
		frappe.set_user(MANAGER)
		stato = collegamento.disconnect_twilio()
		self.assertFalse(stato["connected"])
		doc = self.impostazioni()
		self.assertEqual((doc.enabled, doc.account_sid, doc.api_key, doc.twiml_sid), (0, "", "", ""))
		self.assertFalse(doc.get_password("auth_token", raise_exception=False))
		self.assertFalse(doc.get_password("api_secret", raise_exception=False))
		self.assertEqual(self.mondo.chiavi[spazio.sid], [])
		self.assertEqual(doc.space_sid, spazio.sid)
		# connecting again: the same space
		self.collega()
		self.assertEqual(self.impostazioni().space_sid, spazio.sid)
		self.assertEqual(len(self.mondo.sottoconti(self.centro.sid)), 1)


class ChiPuo(TwilioCase):
	def test_la_segreteria_no(self):
		frappe.set_user(FRONT_DESK)
		with self.assertRaises(frappe.PermissionError):
			collegamento.get_twilio_connection()
		with self.assertRaises(frappe.PermissionError):
			collegamento.connect_twilio(self.centro.sid, self.centro.auth_token)

	def test_l_account_dell_agenzia_e_dell_agenzia(self):
		agenzia = self.mondo.conto("NPM2 segreteria")
		conf = {"dottorcloud_twilio": {"account_sid": agenzia.sid, "auth_token": agenzia.auth_token}}
		with patch.dict(frappe.conf, conf):
			frappe.set_user(MANAGER)
			self.assertFalse(collegamento.get_twilio_connection()["agency_account"])
			with self.assertRaises(frappe.PermissionError):
				collegamento.connect_agency_twilio()
			frappe.set_user(AGENCY)
			self.assertTrue(collegamento.get_twilio_connection()["agency_account"])
			stato = collegamento.connect_agency_twilio()
		self.assertEqual(stato["owner"], R.AGENZIA)
		self.assertEqual(self.impostazioni().main_account_sid, agenzia.sid)
		self.assertEqual(len(self.mondo.sottoconti(agenzia.sid)), 1)
		# the centre's manager neither replaces it nor disconnects it
		frappe.set_user(MANAGER)
		self.assertFalse(collegamento.get_twilio_connection()["may_change"])
		with self.assertRaises(frappe.PermissionError):
			collegamento.connect_twilio(self.centro.sid, self.centro.auth_token)
		with self.assertRaises(frappe.PermissionError):
			collegamento.disconnect_twilio()

	def test_senza_l_account_dell_agenzia(self):
		frappe.set_user(AGENCY)
		with patch.dict(frappe.conf, {"dottorcloud_twilio": {"account_sid": "", "auth_token": ""}}):
			with self.assertRaises(frappe.ValidationError):
				collegamento.connect_agency_twilio()
