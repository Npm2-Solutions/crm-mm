# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's Telnyx account, connected from DottorCloud, on a real site (doc 65).

The manager of Centro Aurora pastes the account's API key and public key once.
DottorCloud makes its outbound voice profile, TeXML application, messaging profile
and credential connection there, and points the account's free numbers at itself
- never one on the centre's switchboard, nor one on another application it never
managed. Connecting again finds the same resources; every hour what somebody
changed in the portal is put back. Disconnected, every person's credential goes
and the resources stay. With Twilio connected, Telnyx waits.
"""

from unittest.mock import patch

import frappe

from crm.permissions import livelli
from crm.telephony import operatore
from crm.telephony.telnyx import collegamento
from crm.telephony.telnyx import regole as R
from crm.telephony.telnyx.tests.telnyx_finto import CHIAVE, TelnyxFinto
from crm.tests.test_documenti_del_core import AGENCY, MANAGER, CoreTestCase

VOCE = "/api/method/crm.integrations.telnyx.api.incoming_call"
BROWSER = "/api/method/crm.integrations.telnyx.api.voice"
SMS = "/api/method/crm.integrations.telnyx.api.sms"
#: What a connection writes, put back to nothing before each test.
VUOTE = {
	"enabled": 0,
	"account_owner": "",
	"api_key": "",
	"public_key": "",
	"texml_application_id": "",
	"credential_connection_id": "",
	"outbound_voice_profile_id": "",
	"messaging_profile_id": "",
	"connected_on": None,
	"connected_by": None,
	"allowed_countries": "IT",
	"record_calls": 0,
	"sms_from": "",
	"sms_sender_name": "",
	"sms_sender_number": "",
	"spend_alert": 0,
	"balance_alert": 0,
	"spend_alert_told": "",
	"balance_alert_told": 0,
	"webhook_base_url": "",
	"verify_webhook_signature": 1,
}


class TelnyxCase(CoreTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		piano = frappe.get_single("CRM Plan")
		piano.set("modules", [{"module": "telefono", "status": "Active"}])
		piano.save()
		livelli.dimentica_cache()
		frappe.db.set_single_value(collegamento.IMPOSTAZIONI, VUOTE)
		frappe.db.set_single_value("CRM Twilio Settings", "enabled", 0)
		frappe.db.delete("CRM Caller ID", {"provider": "telnyx"})
		frappe.db.delete("CRM Telephony Agent", {"user": ["in", [MANAGER, AGENCY]]})
		frappe.clear_document_cache(collegamento.IMPOSTAZIONI, collegamento.IMPOSTAZIONI)
		self.telnyx = TelnyxFinto()
		self.telnyx.__enter__()
		self.addCleanup(self.telnyx.__exit__)

	def tearDown(self):
		super().tearDown()
		# the webhooks commit, as Twilio's do: nothing of Telnyx stays on for the next tests
		frappe.db.set_single_value(collegamento.IMPOSTAZIONI, VUOTE)
		frappe.db.delete("CRM Caller ID", {"provider": "telnyx"})
		frappe.db.delete("CRM Telephony Agent", {"user": ["in", [MANAGER, AGENCY]]})
		# a call nobody answered owes a callback: not to the next module's queue
		frappe.db.delete("CRM Call Log", {"telephony_medium": "Telnyx"})
		frappe.db.delete("CRM SMS Message", {"telephony_medium": "Telnyx"})
		frappe.db.commit()  # nosemgrep: frappe-manual-commit — undoes what a webhook committed

	def collega(self, utente=MANAGER):
		frappe.set_user(utente)
		stato = collegamento.connect_telnyx(CHIAVE, self.telnyx.pubblica)
		frappe.set_user("Administrator")
		return stato

	def impostazioni(self):
		frappe.clear_document_cache(collegamento.IMPOSTAZIONI, collegamento.IMPOSTAZIONI)
		return frappe.get_single(collegamento.IMPOSTAZIONI)


class IlCentroCollegaIlSuoAccount(TelnyxCase):
	def test_le_risorse_e_i_numeri(self):
		libero = self.telnyx.numero("+390212345678", sms=True)
		centralino = self.telnyx.connessione("PBX dello studio", "ip_connection")
		sul_centralino = self.telnyx.numero("+390287654321", connection_id=centralino)
		altra_app = self.telnyx.connessione("Altra app", "texml_application")
		sull_altra = self.telnyx.numero("+390611111111", connection_id=altra_app)

		stato = self.collega()

		doc = self.impostazioni()
		self.assertEqual((doc.enabled, doc.account_owner), (1, R.CENTRO))
		self.assertEqual(doc.get_password("api_key"), CHIAVE)
		self.assertEqual(doc.public_key, self.telnyx.pubblica)
		# one of each resource, named after the site, pointing where they should
		(profilo,) = self.telnyx.profili_voce.values()
		(app,) = self.telnyx.applicazioni.values()
		(sms,) = self.telnyx.profili_sms.values()
		(connessione,) = self.telnyx.connessioni.values()
		self.assertEqual(profilo["whitelisted_destinations"], ["IT"])
		self.assertTrue(app["voice_url"].endswith(VOCE))
		self.assertEqual(app["outbound"]["outbound_voice_profile_id"], profilo["id"])
		self.assertTrue(sms["webhook_url"].endswith(SMS))
		self.assertTrue(connessione["webhook_event_url"].endswith(BROWSER))
		self.assertEqual(connessione["webhook_api_version"], "texml")
		self.assertTrue(connessione["outbound"]["call_parking_enabled"])
		self.assertEqual(connessione["sip_uri_calling_preference"], "internal")
		self.assertEqual(
			(doc.texml_application_id, doc.credential_connection_id, doc.messaging_profile_id),
			(app["id"], connessione["id"], sms["id"]),
		)
		# the free number is DottorCloud's now; the others stay where they are
		self.assertEqual(libero["connection_id"], app["id"])
		self.assertIn(collegamento.segno(), libero["tags"])
		self.assertEqual(libero["messaging_profile_id"], sms["id"])
		self.assertEqual(sul_centralino["connection_id"], centralino)
		self.assertEqual(sull_altra["connection_id"], altra_app)
		self.assertEqual(stato["repaired"], ["+390212345678"])
		self.assertEqual(sorted(stato["trunked"]), ["+390287654321", "+390611111111"])
		# the list of numbers, with what reaches DottorCloud
		self.assertEqual(
			frappe.db.get_value(
				"CRM Caller ID", "+390212345678", ["routes_to_crm", "sms_capable", "provider"]
			),
			(1, 1, "telnyx"),
		)
		self.assertEqual(frappe.db.get_value("CRM Caller ID", "+390287654321", "routes_to_crm"), 0)
		self.assertIn(
			"PBX dello studio", frappe.db.get_value("CRM Caller ID", "+390287654321", "routing_note")
		)
		# what the page reads: never the key
		self.assertTrue(stato["connected"])
		self.assertNotIn(CHIAVE, frappe.as_json(stato))
		self.assertEqual(operatore.attivo(), operatore.TELNYX)

	def test_ricollegando_ritrova_le_risorse(self):
		self.collega()
		self.collega()
		self.assertEqual(
			(
				len(self.telnyx.profili_voce),
				len(self.telnyx.applicazioni),
				len(self.telnyx.profili_sms),
				len(self.telnyx.connessioni),
			),
			(1, 1, 1, 1),
		)

	def test_i_codici_sbagliati(self):
		frappe.set_user(MANAGER)
		for chiave, pubblica in (("", self.telnyx.pubblica), ("KEY1", self.telnyx.pubblica), (CHIAVE, "")):
			with self.assertRaises(frappe.ValidationError):
				collegamento.connect_telnyx(chiave, pubblica)
		self.assertEqual(self.telnyx.chiamate, [])
		altra = "KEY0189A1B2C3D4E5F6071829AB3C4D5F_altrachiavealtra"
		with self.assertRaises(frappe.ValidationError) as detto:
			collegamento.connect_telnyx(altra, self.telnyx.pubblica)
		self.assertIn("does not recognise", str(detto.exception))
		self.assertFalse(self.impostazioni().enabled)

	def test_con_twilio_collegato_aspetta(self):
		frappe.db.set_single_value("CRM Twilio Settings", "enabled", 1)
		frappe.set_user(MANAGER)
		with self.assertRaises(frappe.ValidationError) as detto:
			collegamento.connect_telnyx(CHIAVE, self.telnyx.pubblica)
		self.assertIn("Disconnect Twilio first", str(detto.exception))
		self.assertEqual(self.telnyx.chiamate, [])


class OgniOraRimetteAPosto(TelnyxCase):
	def test_quello_che_si_e_cambiato_nel_portale(self):
		self.collega()
		(app,) = self.telnyx.applicazioni.values()
		app["voice_url"] = "https://altro.example/voce"
		(profilo,) = self.telnyx.profili_voce.values()
		profilo["whitelisted_destinations"] = ["US", "CA"]
		nuovo = self.telnyx.numero("+390299999999")
		collegamento.assicura()
		self.assertTrue(app["voice_url"].endswith(VOCE))
		self.assertEqual(profilo["whitelisted_destinations"], ["IT"])
		self.assertEqual(nuovo["connection_id"], app["id"])
		self.assertEqual(frappe.db.get_value("CRM Caller ID", "+390299999999", "routes_to_crm"), 1)

	def test_i_paesi_scelti_vanno_al_profilo(self):
		self.collega()
		frappe.set_user(MANAGER)
		doc = frappe.get_single(collegamento.IMPOSTAZIONI)
		doc.allowed_countries = "IT,FR"
		doc.save()
		frappe.set_user("Administrator")
		(profilo,) = self.telnyx.profili_voce.values()
		(sms,) = self.telnyx.profili_sms.values()
		self.assertEqual(profilo["whitelisted_destinations"], ["FR", "IT"])
		self.assertEqual(sms["whitelisted_destinations"], ["FR", "IT"])


class IlBrowserEScollegare(TelnyxCase):
	def test_una_credenziale_per_persona_e_il_gettone(self):
		self.collega()
		prima = collegamento.credenziale(MANAGER)
		self.assertEqual(collegamento.credenziale(MANAGER), prima)
		self.assertEqual(len(self.telnyx.credenziali), 1)
		self.assertEqual(
			frappe.db.get_value("CRM Telephony Agent", MANAGER, "telnyx_sip_username"), prima["sip_username"]
		)
		self.assertEqual(collegamento.gettone(MANAGER), f"jwt.per.{prima['sip_username']}")
		# removed in the portal: made again
		self.telnyx.credenziali.clear()
		self.assertTrue(collegamento.gettone(MANAGER).startswith("jwt.per.gencred"))
		self.assertEqual(len(self.telnyx.credenziali), 1)

	def test_scollegando_le_credenziali_vanno_le_risorse_restano(self):
		self.collega()
		collegamento.credenziale(MANAGER)
		frappe.set_user(MANAGER)
		stato = collegamento.disconnect_telnyx()
		frappe.set_user("Administrator")
		self.assertFalse(stato["connected"])
		self.assertEqual(self.telnyx.credenziali, {})
		self.assertFalse(frappe.db.get_value("CRM Telephony Agent", MANAGER, "telnyx_credential_id"))
		doc = self.impostazioni()
		self.assertEqual((doc.enabled, doc.get_password("api_key", raise_exception=False)), (0, None))
		self.assertEqual(len(self.telnyx.applicazioni), 1)
		self.assertIsNone(operatore.attivo())


class LAgenzia(TelnyxCase):
	def test_il_conto_dell_agenzia_non_prende_i_numeri_degli_altri(self):
		libero = self.telnyx.numero("+390212345678")
		conf = {"api_key": CHIAVE, "public_key": self.telnyx.pubblica}
		with patch.dict(frappe.conf, {collegamento.CONF: conf}):
			frappe.set_user(AGENCY)
			stato = collegamento.connect_agency_telnyx()
			frappe.set_user("Administrator")
			doc = self.impostazioni()
			self.assertEqual(doc.account_owner, R.AGENZIA)
			# the agency's codes stay in the server's configuration
			self.assertFalse(doc.get_password("api_key", raise_exception=False))
			self.assertEqual(collegamento.chiave(doc), CHIAVE)
		self.assertEqual(libero["connection_id"], "")
		self.assertEqual(stato["repaired"], [])

	def test_il_centro_non_usa_il_conto_dell_agenzia(self):
		with patch.dict(
			frappe.conf, {collegamento.CONF: {"api_key": CHIAVE, "public_key": self.telnyx.pubblica}}
		):
			frappe.set_user(MANAGER)
			with self.assertRaises(frappe.PermissionError):
				collegamento.connect_agency_telnyx()
