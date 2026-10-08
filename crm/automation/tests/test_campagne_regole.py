# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A campaign without a site: the ways an automation writes by, who of a list is
left out and why, the counts."""

import unittest

from crm.automation import campagne_regole as R

TUTTO = {"email": "a@b.it", "mobile_no": "+393331234567", "consent": True}


class ICanali(unittest.TestCase):
	def test_nei_rami_e_nei_percorsi(self):
		passi = [
			{"type": "add_tag", "tag": "x"},
			{
				"type": "if_else",
				"branches": [{"steps": [{"type": "send_sms", "message": "ciao"}]}],
				"else_steps": [{"type": "send_email", "subject": "s", "message": "m"}],
			},
			{"type": "split", "paths": [{"steps": [{"type": "send_whatsapp_template", "template": "t"}]}]},
		]
		self.assertEqual(R.canali(passi), {"sms", "email", "whatsapp"})

	def test_un_modulo_per_la_sua_via(self):
		self.assertEqual(R.canali([{"type": "send_form", "via": "sms"}]), {"sms"})
		self.assertEqual(R.canali([{"type": "send_form"}]), {"email"})

	def test_nessuno(self):
		self.assertEqual(R.canali(None), set())
		self.assertEqual(R.canali([{"type": "create_task"}, "x"]), set())


class IlMotivo(unittest.TestCase):
	def test_entra(self):
		self.assertIsNone(R.motivo(TUTTO, marketing=True, vie={"email"}))

	def test_gia_dentro_prima_di_tutto(self):
		persona = {"already": True}
		self.assertEqual(R.motivo(persona, marketing=True, vie={"email"}), R.GIA_DENTRO)

	def test_il_consenso_solo_dove_lo_chiede(self):
		persona = {**TUTTO, "consent": False}
		self.assertEqual(R.motivo(persona, marketing=True, vie={"email"}), R.SENZA_CONSENSO)
		self.assertIsNone(R.motivo(persona, marketing=False, vie={"email"}))

	def test_le_condizioni(self):
		self.assertEqual(R.motivo({**TUTTO, "conditions": False}, marketing=False, vie=set()), R.CONDIZIONI)
		self.assertIsNone(R.motivo({**TUTTO, "conditions": None}, marketing=False, vie=set()))

	def test_stop_dove_scrive_solo_per_sms(self):
		persona = {**TUTTO, "stop": True}
		self.assertEqual(R.motivo(persona, marketing=False, vie={"sms"}), R.STOP)
		# an email still reaches them
		self.assertIsNone(R.motivo(persona, marketing=False, vie={"sms", "email"}))
		# STOP without the email: STOP is what keeps them out
		self.assertEqual(R.motivo({**persona, "email": ""}, marketing=False, vie={"sms", "email"}), R.STOP)
		# WhatsApp is not an SMS
		self.assertIsNone(R.motivo(persona, marketing=False, vie={"whatsapp"}))

	def test_senza_recapito(self):
		self.assertEqual(R.motivo({"consent": True}, marketing=False, vie={"email"}), R.SENZA_RECAPITO)
		self.assertEqual(
			R.motivo({"email": "a@b.it", "stop": True}, marketing=False, vie={"sms"}), R.SENZA_RECAPITO
		)
		self.assertEqual(R.motivo({"email": "  "}, marketing=False, vie={"email"}), R.SENZA_RECAPITO)

	def test_un_automazione_che_non_scrive(self):
		self.assertIsNone(R.motivo({}, marketing=False, vie=set()))


class IConti(unittest.TestCase):
	def test_per_motivo_nel_loro_ordine(self):
		conti = R.conta([None, "stop", None, "already", "stop"])
		self.assertEqual(conti["total"], 5)
		self.assertEqual(conti["enrolled"], 2)
		self.assertEqual(list(conti["skipped"].items()), [("already", 1), ("stop", 2)])

	def test_una_lista_vuota(self):
		self.assertEqual(R.conta([]), {"total": 0, "enrolled": 0, "skipped": {}})
