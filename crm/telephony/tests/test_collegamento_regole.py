# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Connecting the centre's Twilio account, without a site: the two codes, the
space's name, what a number and the app need, Twilio's answers in words."""

import unittest

from crm.telephony import collegamento_regole as R

SID = "AC" + "0123456789abcdef" * 2
TOKEN = "fedcba9876543210" * 2
VOCE = "https://aurora.example/api/method/crm.integrations.twilio.api.twilio_incoming_call_handler"
SMS = "https://aurora.example/api/method/crm.integrations.twilio.api.incoming_sms_handler"


class IDueCodici(unittest.TestCase):
	def test_come_li_da_la_console(self):
		self.assertTrue(R.sid_valido(SID))
		self.assertTrue(R.sid_valido(SID.upper().replace("AC", "AC", 1)))
		self.assertTrue(R.token_valido(TOKEN))
		self.assertEqual(R.cosa_manca(SID, TOKEN), "")

	def test_gli_spazi_copiati_non_contano(self):
		self.assertEqual(R.pulito(f"  {SID}\n"), SID)
		self.assertEqual(R.pulito("fedc ba98\t7654"), "fedcba987654")
		self.assertEqual(R.cosa_manca(f" {SID} ", f"\n{TOKEN} "), "")

	def test_cosa_manca_prima_di_chiedere(self):
		self.assertEqual(R.cosa_manca("", TOKEN), "Paste the Account SID.")
		self.assertIn("starts with AC", R.cosa_manca("SK" + SID[2:], TOKEN))
		self.assertIn("starts with AC", R.cosa_manca(SID[:-1], TOKEN))
		self.assertEqual(R.cosa_manca(SID, None), "Paste the Auth Token.")
		self.assertIn("32 letters and digits", R.cosa_manca(SID, TOKEN + "0"))
		self.assertIn("32 letters and digits", R.cosa_manca(SID, "z" * 32))

	def test_mascherato(self):
		self.assertEqual(R.mascherato(SID), "AC…cdef")
		self.assertEqual(R.mascherato(""), "")
		self.assertEqual(R.mascherato(None), "")


class LoSpazio(unittest.TestCase):
	def test_il_nome_dal_sito(self):
		self.assertEqual(
			R.nome_dello_spazio("https://aurora.dottorcloud.it"), "DottorCloud · aurora.dottorcloud.it"
		)
		self.assertEqual(R.nome_dello_spazio("http://test_site:8000/"), "DottorCloud · test_site")
		self.assertEqual(R.nome_dello_spazio("aurora.example"), "DottorCloud · aurora.example")
		self.assertEqual(R.nome_dello_spazio(""), "DottorCloud")
		# the product's name, the vertical's where one is on
		self.assertEqual(R.nome_dello_spazio("aurora.example", "Altro"), "Altro · aurora.example")

	def test_al_massimo_64_caratteri(self):
		lungo = "https://" + "a" * 80 + ".example"
		self.assertEqual(len(R.nome_dello_spazio(lungo)), 64)


class UnNumero(unittest.TestCase):
	def numero(self, **valori):
		return {"capabilities": {"voice": True, "sms": False}, **valori}

	def test_a_posto_niente(self):
		self.assertEqual(R.da_sistemare(self.numero(voice_url=VOCE, voice_method="POST"), VOCE, SMS), {})
		self.assertEqual(R.da_sistemare(self.numero(voice_url=VOCE), VOCE, SMS), {})

	def test_un_altro_indirizzo_o_un_altro_metodo(self):
		self.assertEqual(
			R.da_sistemare(self.numero(voice_url="https://altro.example"), VOCE, SMS),
			{"voice_url": VOCE, "voice_method": "POST"},
		)
		self.assertEqual(
			R.da_sistemare(self.numero(voice_url=VOCE, voice_method="GET"), VOCE, SMS),
			{"voice_url": VOCE, "voice_method": "POST"},
		)

	def test_un_app_davanti_all_indirizzo_si_toglie(self):
		self.assertEqual(
			R.da_sistemare(self.numero(voice_url=VOCE, voice_application_sid="AP1"), VOCE, SMS),
			{"voice_url": VOCE, "voice_method": "POST", "voice_application_sid": ""},
		)

	def test_gli_sms_solo_dove_ci_sono(self):
		con_sms = {"capabilities": {"voice": True, "sms": True}, "voice_url": VOCE}
		self.assertEqual(R.da_sistemare(con_sms, VOCE, SMS), {"sms_url": SMS, "sms_method": "POST"})
		self.assertEqual(R.da_sistemare({**con_sms, "sms_url": SMS}, VOCE, SMS), {})
		solo_sms = {"capabilities": {"voice": False, "sms": True}, "sms_url": SMS}
		self.assertEqual(R.da_sistemare(solo_sms, VOCE, SMS), {})

	def test_un_trunk_resta_com_e(self):
		self.assertEqual(R.da_sistemare(self.numero(trunk_sid="TK1", voice_url="sip"), VOCE, SMS), {})

	def test_l_app(self):
		self.assertEqual(R.app_da_sistemare({"voice_url": VOCE, "voice_method": "POST"}, VOCE), {})
		self.assertEqual(
			R.app_da_sistemare({"voice_url": "https://vecchio.example", "voice_method": "POST"}, VOCE),
			{"voice_url": VOCE, "voice_method": "POST"},
		)


class InParole(unittest.TestCase):
	def test_gli_errori(self):
		self.assertIn("does not recognise these codes", R.errore_in_parole(401, 20003)[0])
		self.assertIn("does not recognise these codes", R.errore_in_parole(400, 20003)[0])
		self.assertIn("does not find this account", R.errore_in_parole(404)[0])
		self.assertIn("does not answer", R.errore_in_parole(None)[0])
		frase, argomenti = R.errore_in_parole(500, 20500)
		self.assertIn("{0}", frase)
		self.assertEqual(argomenti, [20500])
		self.assertEqual(R.errore_in_parole(503)[1], [503])

	def test_l_account(self):
		self.assertEqual(R.stato_in_parole("active", "Full"), "")
		self.assertIn("trial account", R.stato_in_parole("active", "Trial"))
		self.assertIn("suspended", R.stato_in_parole("suspended", "Full"))
		self.assertIn("closed", R.stato_in_parole("closed", "Full"))
