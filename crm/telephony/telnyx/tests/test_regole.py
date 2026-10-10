# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Connecting the centre's Telnyx account, without a site (doc 64)."""

import base64
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from crm.telephony.telnyx import regole as R
from crm.telephony.telnyx import texml

CHIAVE = "KEY0189A1B2C3D4E5F6071829AB3C4D5E_5FhZonmFvcw8Yq0dME27Bg"


def _coppia():
	privata = Ed25519PrivateKey.generate()
	pubblica = base64.b64encode(privata.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)).decode()
	return privata, pubblica


class IDueCodici(unittest.TestCase):
	def test_una_chiave_come_la_da_il_portale(self):
		self.assertTrue(R.chiave_valida(CHIAVE))
		self.assertTrue(R.chiave_valida(f"  {CHIAVE}\n"))
		self.assertFalse(R.chiave_valida("KEY123"))
		self.assertFalse(R.chiave_valida("AC" + "0" * 32))
		self.assertFalse(R.chiave_valida(""))

	def test_la_chiave_pubblica_e_di_32_byte(self):
		_privata, pubblica = _coppia()
		self.assertEqual(len(R.chiave_pubblica(pubblica)), 32)
		self.assertIsNone(R.chiave_pubblica("non-base64!"))
		self.assertIsNone(R.chiave_pubblica(base64.b64encode(b"corta").decode()))

	def test_cosa_manca_prima_di_chiedere(self):
		_privata, pubblica = _coppia()
		self.assertEqual(R.cosa_manca("", pubblica), "Paste the API key.")
		self.assertIn("starts with KEY", R.cosa_manca("abc", pubblica))
		self.assertEqual(R.cosa_manca(CHIAVE, ""), "Paste the public key.")
		self.assertIn("44 letters", R.cosa_manca(CHIAVE, "abc"))
		self.assertEqual(R.cosa_manca(CHIAVE, pubblica), "")

	def test_la_chiave_mascherata(self):
		self.assertEqual(R.mascherata(CHIAVE), "KEY…7Bg"[:3] + "…" + CHIAVE[-4:])
		self.assertNotIn(CHIAVE[5:20], R.mascherata(CHIAVE))


class LaFirma(unittest.TestCase):
	def setUp(self):
		self.privata, self.pubblica = _coppia()
		self.corpo = b"CallSid=v3%3Aabc&From=%2B393331234567"
		self.adesso = 1_800_000_000

	def firma(self, corpo=None, momento=None):
		momento = momento or self.adesso
		segno = self.privata.sign(str(momento).encode() + b"|" + (corpo or self.corpo))
		return base64.b64encode(segno).decode(), str(momento)

	def test_giusta(self):
		firma, momento = self.firma()
		self.assertTrue(R.firma_valida(self.corpo, firma, momento, self.pubblica, self.adesso + 10))

	def test_un_corpo_cambiato(self):
		firma, momento = self.firma()
		self.assertFalse(R.firma_valida(self.corpo + b"x", firma, momento, self.pubblica, self.adesso))

	def test_troppo_vecchia_o_troppo_avanti(self):
		firma, momento = self.firma()
		self.assertFalse(R.firma_valida(self.corpo, firma, momento, self.pubblica, self.adesso + 301))
		self.assertFalse(R.firma_valida(self.corpo, firma, momento, self.pubblica, self.adesso - 301))
		self.assertTrue(R.firma_valida(self.corpo, firma, momento, self.pubblica, self.adesso + 300))

	def test_un_altra_chiave_o_niente(self):
		firma, momento = self.firma()
		_altra, pubblica = _coppia()
		self.assertFalse(R.firma_valida(self.corpo, firma, momento, pubblica, self.adesso))
		self.assertFalse(R.firma_valida(self.corpo, None, momento, self.pubblica, self.adesso))
		self.assertFalse(R.firma_valida(self.corpo, firma, None, self.pubblica, self.adesso))
		self.assertFalse(R.firma_valida(self.corpo, "@@@", momento, self.pubblica, self.adesso))


class INumeri(unittest.TestCase):
	APP, CRED, PROFILO, SEGNO = "app", "cred", "prof", "dottorcloud-aurora.example"

	def fai(self, numero, liberi=True, tipi=None):
		return R.cosa_fare(
			numero,
			self.APP,
			self.PROFILO,
			{self.APP, self.CRED},
			tipi or {},
			self.SEGNO,
			prende_i_liberi=liberi,
		)

	def test_uno_libero_si_prende_nel_conto_del_centro(self):
		azione, cambi = self.fai({"connection_id": "", "tags": [], "sms": True})
		self.assertEqual(azione, "sistema")
		self.assertEqual(
			cambi, {"connection_id": self.APP, "tags": [self.SEGNO], "messaging_profile_id": self.PROFILO}
		)

	def test_nel_conto_dell_agenzia_uno_libero_e_di_un_altro_sito(self):
		self.assertEqual(self.fai({"connection_id": ""}, liberi=False), ("altrove", {}))
		# the site's own, tagged, is taken back
		self.assertEqual(self.fai({"connection_id": "", "tags": [self.SEGNO]}, liberi=False)[0], "sistema")

	def test_su_un_centralino_resta(self):
		tipi = {"pbx": "ip_connection"}
		self.assertEqual(self.fai({"connection_id": "pbx", "tags": [self.SEGNO]}, tipi=tipi), ("altrove", {}))

	def test_su_un_altra_applicazione_resta_se_non_e_nostro(self):
		tipi = {"altra": "texml_application"}
		self.assertEqual(self.fai({"connection_id": "altra"}, tipi=tipi), ("altrove", {}))
		azione, cambi = self.fai({"connection_id": "altra", "tags": [self.SEGNO]}, tipi=tipi)
		self.assertEqual((azione, cambi), ("sistema", {"connection_id": self.APP}))

	def test_a_posto(self):
		numero = {
			"connection_id": self.APP,
			"tags": [self.SEGNO],
			"sms": True,
			"messaging_profile_id": "prof",
		}
		self.assertEqual(self.fai(numero), ("ok", {}))
		# a number that sends no SMS gets no profile
		self.assertEqual(self.fai({"connection_id": self.APP, "tags": [self.SEGNO]}), ("ok", {}))

	def test_l_etichetta_del_sito(self):
		self.assertEqual(R.etichetta("https://aurora.dottorcloud.it"), "dottorcloud-aurora.dottorcloud.it")
		self.assertEqual(R.etichetta(""), "dottorcloud")

	def test_i_paesi(self):
		self.assertEqual(R.paesi_del_profilo(["it", "FR ", "x", ""]), ["FR", "IT"])
		self.assertEqual(R.paesi_del_profilo([]), ["IT"])


class LeRisposte(unittest.TestCase):
	def test_gli_errori_a_parole(self):
		self.assertIn("does not recognise", R.errore_in_parole(401, "10009")[0])
		self.assertIn("does not answer", R.errore_in_parole(None)[0])
		self.assertEqual(R.errore_in_parole(422, "10015", "bad thing"), ("Telnyx says: {0}", ["bad thing"]))
		self.assertEqual(R.errore_in_parole(500, "10007")[1], ["10007"])

	def test_gli_stati(self):
		self.assertEqual(R.stato_sms("delivered"), "Delivered")
		self.assertEqual(R.stato_sms("delivery_failed"), "Undelivered")
		self.assertEqual(R.stato_sms("sending_failed"), "Failed")
		self.assertIsNone(R.stato_sms("read"))
		self.assertEqual(R.stato_chiamata("no-answer"), "No Answer")
		self.assertEqual(R.stato_chiamata("in-progress"), "In Progress")
		self.assertEqual(R.stato_chiamata("canceled"), "Canceled")


class IlTeXML(unittest.TestCase):
	def test_le_parole_del_centro_sono_al_sicuro(self):
		xml = texml.Risposta().say("Studio <Rossi> & figli", voice="alice", language="it-IT").hangup().xml()
		self.assertIn("Studio &lt;Rossi&gt; &amp; figli", xml)
		self.assertTrue(xml.startswith('<?xml version="1.0" encoding="UTF-8"?><Response>'))
		self.assertIn("<Hangup />", xml)

	def test_un_dial_con_tutti(self):
		xml = (
			texml.Risposta()
			.dial(
				numeri=[("+393471112233", {"statusCallback": "https://a/s"})],
				sip=[(texml.indirizzo_sip("gencredAb1"), None)],
				callerId="+390212345678",
				timeout=20,
				answerOnBridge=True,
				record=None,
			)
			.xml()
		)
		self.assertIn('answerOnBridge="true"', xml)
		self.assertIn('timeout="20"', xml)
		self.assertNotIn("record=", xml)
		self.assertIn('<Number statusCallback="https://a/s">+393471112233</Number>', xml)
		self.assertIn("<Sip>sip:gencredAb1@sip.telnyx.com</Sip>", xml)

	def test_record_una_sola_voce(self):
		xml = texml.Risposta().record(maxLength=120, timeout=5).xml()
		self.assertIn('channels="single"', xml)
		self.assertIn('timeout="5"', xml)

	def test_chi_e_dietro_un_indirizzo_sip(self):
		self.assertEqual(texml.utente_sip("sip:gencredAb1@sip.telnyx.com"), "gencredAb1")
		self.assertEqual(texml.utente_sip("gencredAb1"), "gencredAb1")
		self.assertEqual(texml.utente_sip("+390212345678"), "")
		self.assertEqual(texml.utente_sip("sip:+390212345678@sip.telnyx.com"), "")
		self.assertEqual(texml.utente_sip(None), "")
