# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Calls going out from DottorCloud (doc 52, third part).

A call leaves only for the countries the centre chose - Italy to start with - and
never for a premium-rate number; the same countries are Twilio's permissions of
the space. It shows the number chosen for the call when that is one of the
centre's, else the person's own line; an Italian mobile shown on a call to Italy
is blocked since November 2025, and the screen is told.
"""

import unittest
from unittest.mock import patch

import frappe

from crm.integrations.twilio import api
from crm.permissions import livelli, utenti
from crm.permissions.test_org_hierarchy import make_user
from crm.telephony import collegamento, uscita
from crm.telephony import uscita_regole as R
from crm.telephony.tests.test_collegamento import TwilioCase
from crm.tests.test_documenti_del_core import FRONT_DESK, MANAGER

FISSO = "+390212345678"
CELLULARE = "+393331234567"
LONDRA = "+442079460958"
ZURIGO = "+41446681800"
MARKETING = "uscita.marketing@example.com"


def aperto(paese: str, rischiosi: bool = False) -> dict:
	"""A country as Twilio lists it: its ordinary numbers open, maybe its special ones."""
	return {
		"iso_code": paese,
		"low_risk_numbers_enabled": True,
		"high_risk_special_numbers_enabled": rischiosi,
		"high_risk_tollfraud_numbers_enabled": rischiosi,
	}


class DoveSiChiama(unittest.TestCase):
	def test_i_paesi_come_sono_scritti(self):
		self.assertEqual(R.paesi("it, ch"), ["CH", "IT"])
		self.assertEqual(R.paesi('["IT", "FR"]'), ["FR", "IT"])
		self.assertEqual(R.paesi("IT\nSM;VA"), ["IT", "SM", "VA"])
		self.assertEqual(R.paesi(""), ["IT"])
		self.assertEqual(R.paesi(None), ["IT"])
		self.assertEqual(R.paesi("Italia, 39"), ["IT"])

	def test_l_italia_anche_senza_prefisso(self):
		self.assertEqual(R.si_chiama("0212345678", "IT"), "")
		self.assertEqual(R.si_chiama("333 1234567", "IT"), "")
		self.assertEqual(R.si_chiama("0039 02 1234 5678", "IT"), "")
		self.assertEqual(R.paese_di("0212345678"), "IT")

	def test_un_altro_paese_solo_se_il_centro_lo_vuole(self):
		self.assertIn("country", R.si_chiama(LONDRA, "IT"))
		self.assertEqual(R.si_chiama(LONDRA, "IT, GB"), "")
		self.assertEqual(R.si_chiama(ZURIGO, ["IT", "CH"]), "")

	def test_mai_un_numero_a_pagamento(self):
		for numero in ("+39899123456", "+39892123", "+39166123456"):
			self.assertIn("Premium-rate", R.si_chiama(numero, "IT"), numero)

	def test_un_numero_che_non_si_legge(self):
		self.assertIn("cannot be read", R.si_chiama("abc", "IT"))
		self.assertIn("cannot be read", R.si_chiama("", "IT"))

	def test_il_cellulare_italiano_mostrato_in_italia(self):
		self.assertTrue(R.cellulare_italiano(CELLULARE))
		self.assertFalse(R.cellulare_italiano(FISSO))
		self.assertTrue(R.bloccata_in_italia(CELLULARE, FISSO))
		self.assertFalse(R.bloccata_in_italia(FISSO, CELLULARE))
		self.assertFalse(R.bloccata_in_italia(CELLULARE, ZURIGO))

	def test_i_permessi_di_twilio(self):
		cambi = R.cambi_dei_permessi("IT, CH", [aperto("IT"), aperto("US")])
		self.assertEqual([c["iso_code"] for c in cambi], ["CH", "US"])
		self.assertTrue(cambi[0]["low_risk_numbers_enabled"])
		self.assertFalse(cambi[1]["low_risk_numbers_enabled"])
		self.assertFalse(any(c["high_risk_special_numbers_enabled"] for c in cambi))
		self.assertFalse(any(c["high_risk_tollfraud_numbers_enabled"] for c in cambi))

	def test_niente_da_cambiare_niente_si_scrive(self):
		self.assertEqual(R.cambi_dei_permessi("IT", [aperto("IT")]), [])
		# the special numbers of a country chosen are closed, its ordinary ones stay
		(cambio,) = R.cambi_dei_permessi("IT", [aperto("IT", rischiosi=True)])
		self.assertEqual(
			(cambio["low_risk_numbers_enabled"], cambio["high_risk_special_numbers_enabled"]), (True, False)
		)


class NelloSpazio(TwilioCase):
	def setUp(self):
		super().setUp()
		frappe.db.set_single_value(collegamento.IMPOSTAZIONI, "allowed_countries", "IT")
		self.collega()
		self.spazio_sid = self.spazio().sid

	def test_i_paesi_del_centro_anche_in_twilio(self):
		self.assertFalse(self.mondo.eredita[self.spazio_sid])
		self.assertEqual(self.mondo.paesi[self.spazio_sid], {"IT"})
		# the account's own permissions are not touched
		self.assertEqual(self.mondo.paesi[self.centro.sid], {"IT", "US"})

	def test_un_paese_aggiunto_arriva_a_twilio(self):
		impostazioni = frappe.get_single(collegamento.IMPOSTAZIONI)
		impostazioni.allowed_countries = "IT, CH"
		impostazioni.save(ignore_permissions=True)
		self.assertEqual(self.mondo.paesi[self.spazio_sid], {"CH", "IT"})

	def test_un_paese_aperto_nella_console_si_richiude(self):
		self.mondo.paesi[self.spazio_sid].add("CU")
		self.mondo.rischiosi[self.spazio_sid].add("IT")
		collegamento.assicura()
		self.assertEqual(self.mondo.paesi[self.spazio_sid], {"IT"})
		self.assertEqual(self.mondo.rischiosi[self.spazio_sid], set())

	def test_ogni_ora_si_chiede_e_non_si_riscrive(self):
		prima = len(self.mondo.cambi)
		collegamento.assicura()
		self.assertEqual(len(self.mondo.cambi), prima)

	def test_un_account_collegato_a_mano_resta_com_e(self):
		frappe.db.set_single_value(collegamento.IMPOSTAZIONI, "account_owner", "")
		self.mondo.paesi[self.spazio_sid].add("CU")
		self.assertFalse(uscita.allinea_i_paesi())
		self.assertIn("CU", self.mondo.paesi[self.spazio_sid])


class LaChiamata(TwilioCase):
	"""What the browser's call is told, by the TwiML app's webhook."""

	def setUp(self):
		super().setUp()
		frappe.db.set_single_value(collegamento.IMPOSTAZIONI, "allowed_countries", "IT")
		self.collega()
		frappe.db.delete("CRM Telephony Agent", {"user": MANAGER})
		frappe.get_doc(
			{
				"doctype": "CRM Telephony Agent",
				"user": MANAGER,
				"twilio_number": FISSO,
				"call_receiving_device": "Computer",
			}
		).insert(ignore_permissions=True)
		for numero, etichetta in ((FISSO, "Reception"), ("+390687654321", "Roma"), (CELLULARE, "Mobile")):
			if not frappe.db.exists("CRM Caller ID", numero):
				frappe.get_doc(
					{
						"doctype": "CRM Caller ID",
						"phone_number": numero,
						"label": etichetta,
						"provider": "twilio",
						"source": "Account Number",
						"voice_capable": 1,
						"enabled": 1,
					}
				).insert(ignore_permissions=True)
		finto = patch("crm.integrations.twilio.api.create_call_log", return_value=None)
		finto.start()
		self.addCleanup(finto.stop)

	def chiama(self, a, mostra=None):
		from crm.integrations.twilio.twilio_handler import Twilio

		twilio = Twilio.connect()
		with patch("crm.integrations.twilio.api.validate_twilio_request", return_value=twilio):
			risposta = api.voice(Caller=f"client:{Twilio.safe_identity(MANAGER)}", To=a, CallFrom=mostra)
		return risposta.get_data(as_text=True)

	def test_un_paese_che_il_centro_non_chiama(self):
		xml = self.chiama(LONDRA)
		self.assertNotIn("<Dial", xml)
		self.assertIn("<Hangup", xml)

	def test_mai_a_pagamento(self):
		self.assertNotIn("<Dial", self.chiama("+39899123456"))

	def test_dal_numero_scelto_se_e_del_centro(self):
		self.assertIn('callerId="+390687654321"', self.chiama(CELLULARE, "+390687654321"))

	def test_altrimenti_dalla_propria_linea(self):
		self.assertIn(f'callerId="{FISSO}"', self.chiama(CELLULARE, "+390299999999"))
		self.assertIn(f'callerId="{FISSO}"', self.chiama(CELLULARE))

	def test_i_numeri_che_si_possono_mostrare(self):
		frappe.set_user(MANAGER)
		dati = uscita.get_outbound_numbers()
		frappe.set_user("Administrator")
		numeri = {n["number"]: n for n in dati["numbers"]}
		self.assertTrue(numeri[FISSO]["own"])
		self.assertFalse(numeri["+390687654321"]["own"])
		self.assertTrue(numeri[CELLULARE]["mobile"])
		self.assertEqual(dati["countries"], ["IT"])

	def test_prima_di_chiamare(self):
		frappe.set_user(MANAGER)
		self.assertEqual(
			uscita.check_number(FISSO, FISSO),
			{
				"ok": True,
				"reason": "",
				"country": "IT",
				"blocked_in_italy": False,
				"uncertain_in_italy": False,
			},
		)
		self.assertTrue(uscita.check_number(FISSO, CELLULARE)["blocked_in_italy"])
		self.assertFalse(uscita.check_number(LONDRA)["ok"])
		frappe.set_user("Administrator")

	def test_la_segreteria_telefona_il_marketing_no(self):
		make_user(MARKETING)
		utenti.assegna_livelli(MARKETING, ["marketing"])
		livelli.dimentica_cache()
		frappe.set_user(FRONT_DESK)
		self.assertTrue(uscita.get_outbound_numbers()["numbers"])
		frappe.set_user(MARKETING)
		with self.assertRaises(frappe.PermissionError):
			uscita.get_outbound_numbers()
		with self.assertRaises(frappe.PermissionError):
			uscita.check_number(FISSO)
		frappe.set_user("Administrator")
