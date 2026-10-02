# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A number the centre already has in its own Twilio account, moved into DottorCloud's
space (doc 52, sixth part), on a real site with Twilio simulated.

The manager pastes the account's codes again: DottorCloud lists the numbers there,
and moves the one chosen with its approved documents (a bundle clone) and its
address, then points it at DottorCloud. The codes are not kept; a number on a SIP
trunk stays; another account's codes, or the agency's space, move nothing.
"""

from unittest.mock import patch

import frappe

from crm.telephony import collegamento, trasloco
from crm.telephony.tests.test_collegamento import VOCE, TwilioCase
from crm.tests.test_documenti_del_core import FRONT_DESK, MANAGER

FISSO = "+390212345678"


class TraslocoCase(TwilioCase):
	def setUp(self):
		super().setUp()
		self.collega()
		self.space = self.spazio().sid
		self.pacchetto = self.mondo.approvato(self.centro.sid)
		self.indirizzo = self.mondo.indirizzo(self.centro.sid)
		self.numero = self.mondo.numero(
			self.centro.sid,
			FISSO,
			bundle_sid=self.pacchetto.sid,
			address_sid=self.indirizzo.sid,
			voice_url="https://altro.example/voce",
		)

	def come(self, utente=MANAGER):
		frappe.set_user(utente)
		self.addCleanup(frappe.set_user, "Administrator")

	def nello_spazio(self):
		return {numero.phone_number: numero for numero in self.mondo.numeri[self.space]}


class INumeriDelConto(TraslocoCase):
	def test_quelli_che_si_spostano_prima(self):
		self.mondo.numero(self.centro.sid, "+390287654321", trunk_sid="TK0")
		self.come()
		numeri = trasloco.get_account_numbers(self.centro.sid, self.centro.auth_token)
		self.assertEqual([n["number"] for n in numeri], [FISSO, "+390287654321"])
		self.assertEqual(numeri[0]["reason"], "")
		self.assertTrue(numeri[1]["reason"])

	def test_i_codici_di_un_altro_conto(self):
		altro = self.mondo.conto("Altro Centro")
		self.come()
		with self.assertRaises(frappe.ValidationError):
			trasloco.get_account_numbers(altro.sid, altro.auth_token)

	def test_la_reception_no(self):
		self.come(FRONT_DESK)
		with self.assertRaises(frappe.PermissionError):
			trasloco.get_account_numbers(self.centro.sid, self.centro.auth_token)


class LoSpostamento(TraslocoCase):
	def test_con_i_documenti_e_l_indirizzo_e_punta_a_dottorcloud(self):
		self.come()
		esito = trasloco.move_number(self.centro.sid, self.centro.auth_token, self.numero.sid)
		self.assertEqual(esito["number"], FISSO)
		numero = self.nello_spazio()[FISSO]
		self.assertNotIn(numero, self.mondo.numeri[self.centro.sid])
		# its documents approved in the space, a copy of its address there
		pacchetto = self.mondo.pacchetti[numero.bundle_sid]
		self.assertEqual((pacchetto.account, pacchetto.status), (self.space, "twilio-approved"))
		indirizzo = self.mondo.indirizzi[numero.address_sid]
		self.assertEqual((indirizzo.account, indirizzo.street), (self.space, "Via Roma 1"))
		# pointed at DottorCloud (a landline: calls only), and in the list of the centre's numbers
		self.assertTrue(numero.voice_url.endswith(VOCE))
		self.assertTrue(frappe.db.exists("CRM Caller ID", FISSO))

	def test_i_codici_del_conto_non_restano(self):
		self.come()
		trasloco.move_number(self.centro.sid, self.centro.auth_token, self.numero.sid)
		impostazioni = frappe.get_single(collegamento.IMPOSTAZIONI)
		self.assertNotEqual(impostazioni.get_password("auth_token"), self.centro.auth_token)
		self.assertEqual(impostazioni.account_sid, self.space)

	def test_un_numero_su_un_tronco_resta(self):
		self.numero.trunk_sid = "TK0"
		self.come()
		with self.assertRaises(frappe.ValidationError):
			trasloco.move_number(self.centro.sid, self.centro.auth_token, self.numero.sid)
		self.assertNotIn(FISSO, self.nello_spazio())

	def test_twilio_che_non_copia_i_documenti(self):
		self.pacchetto.status = "pending-review"
		self.come()
		with self.assertRaises(frappe.ValidationError):
			trasloco.move_number(self.centro.sid, self.centro.auth_token, self.numero.sid)
		self.assertNotIn(FISSO, self.nello_spazio())

	def test_nello_spazio_dell_agenzia_no(self):
		frappe.db.set_single_value(collegamento.IMPOSTAZIONI, "account_owner", "Agency")
		self.come()
		with self.assertRaises(frappe.ValidationError):
			trasloco.move_number(self.centro.sid, self.centro.auth_token, self.numero.sid)

	def test_un_numero_senza_documenti(self):
		semplice = self.mondo.numero(self.centro.sid, "+14155550100")
		self.come()
		with patch.object(trasloco, "_clona") as clona:
			trasloco.move_number(self.centro.sid, self.centro.auth_token, semplice.sid)
		clona.assert_not_called()
		self.assertIn("+14155550100", self.nello_spazio())
