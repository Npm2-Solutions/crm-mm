# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""News in the area, told outside it: the same words everywhere, only to a number
that wrote to the centre, at most once every two hours.

The centre offers WhatsApp with its approved template. Anna asks for it from her
area only once her number has written to the centre; then a message on her board
reaches her on WhatsApp too, with the template and the centre's name, not with
the message. A second message within two hours does not. SMS say the same, from
the centre's number. A notice that cannot leave does not stop the board. The
channels are chosen by who configures them.
"""

import json
from unittest import mock

import frappe

from crm.clinica.area import api, avvisi, messaggi
from crm.clinica.tests.test_area import ANNA, AreaCase
from crm.clinica.tests.test_cartella import DESK, MANAGER

NUMERO = "+393331234567"
MODELLO = "novita-area-prova"


class AvvisiCase(AreaCase):
	def setUp(self):
		super().setUp()
		self.invita()
		frappe.set_user("Administrator")
		frappe.db.set_value("CRM Lead", self.anna.name, "mobile_no", "+39 333 1234567")
		if not frappe.db.exists("WhatsApp Templates", MODELLO):
			modello = frappe.get_doc(
				{
					"doctype": "WhatsApp Templates",
					"name": MODELLO,
					"template_name": MODELLO,
					"template": "C'è una novità nella tua area di {{1}}.",
					"language": frappe.db.get_value("Language", {}, "name") or "it",
					"category": "UTILITY",
					"status": "APPROVED",
				}
			)
			# as it is after Meta approved it: nothing is asked of Meta here
			modello.db_insert()
		self.offri(whatsapp=MODELLO)
		self.addCleanup(self.pulisci_pause)

	def pulisci_pause(self):
		for canale in avvisi.CANALI:
			frappe.cache.delete_value(avvisi._chiave_pausa(ANNA, canale))

	def offri(self, whatsapp=None, sms=None, twilio=0):
		frappe.db.set_single_value(avvisi.IMPOSTAZIONI, "area_whatsapp_template", whatsapp)
		frappe.db.set_single_value(avvisi.IMPOSTAZIONI, "area_sms_number", sms)
		frappe.db.set_single_value("CRM Twilio Settings", "enabled", twilio)

	def ha_scritto(self, canale=avvisi.WHATSAPP):
		frappe.set_user("Administrator")
		if canale == avvisi.WHATSAPP:
			riga = frappe.get_doc(
				{
					"doctype": "WhatsApp Message",
					"type": "Incoming",
					"from": "393331234567",
					"message": "Buongiorno",
					"content_type": "text",
					"reference_doctype": "CRM Lead",
					"reference_name": self.anna.name,
				}
			)
		else:
			riga = frappe.get_doc(
				{
					"doctype": "CRM SMS Message",
					"type": "Incoming",
					"status": "Received",
					"from": NUMERO,
					"to": "+390212345678",
					"message": "Buongiorno",
					"reference_doctype": "CRM Lead",
					"reference_name": self.anna.name,
				}
			)
		riga.name = frappe.generate_hash(length=10)
		riga.db_insert()

	def sceglie(self, canale=avvisi.WHATSAPP):
		self.entra(ANNA)
		return avvisi.set_notice(canale, 1)

	def scrive(self, testo="Porti la tessera sanitaria"):
		self.come(DESK)
		return messaggi.post_message(self.anna.name, testo)


class LaScelta(AvvisiCase):
	def test_senza_offerta_solo_l_email(self):
		self.offri()
		self.entra(ANNA)
		self.assertFalse(api.get_me()["notices"])
		self.assertEqual(avvisi.notice_options(), {"email": ANNA, "channels": []})

	def test_solo_un_numero_che_ha_scritto_al_centro(self):
		self.entra(ANNA)
		self.assertTrue(api.get_me()["notices"])
		[canale] = avvisi.notice_options()["channels"]
		self.assertEqual((canale["channel"], canale["number"], canale["on"]), ("WhatsApp", None, False))
		with self.assertRaises(frappe.ValidationError):
			avvisi.set_notice("WhatsApp", 1)
		self.ha_scritto()
		[canale] = self.sceglie()["channels"]
		self.assertEqual((canale["number"], canale["on"]), ("•••• 567", True))
		[spento] = avvisi.set_notice("WhatsApp", 0)["channels"]
		self.assertFalse(spento["on"])

	def test_un_canale_che_il_centro_non_offre(self):
		self.ha_scritto(avvisi.SMS)
		self.entra(ANNA)
		with self.assertRaises(frappe.ValidationError):
			avvisi.set_notice("SMS", 1)


class LAvviso(AvvisiCase):
	def test_su_whatsapp_una_volta_ogni_due_ore(self):
		self.ha_scritto()
		self.sceglie()
		with mock.patch.object(avvisi, "_manda_whatsapp") as manda:
			self.scrive()
			self.scrive("Domani alle 9")
		manda.assert_called_once()
		lead, numero, _centro = manda.call_args.args
		self.assertEqual((lead, numero), (self.anna.name, NUMERO))

	def test_il_template_dice_solo_che_c_e_una_novita(self):
		self.ha_scritto()
		frappe.set_user("Administrator")
		with mock.patch("crm.api.whatsapp.insert_and_send") as spedisce:
			avvisi._manda_whatsapp(self.anna.name, NUMERO, "Centro Prova")
		[doc] = spedisce.call_args.args
		self.assertEqual((doc.template, doc.to, doc.use_template), (MODELLO, NUMERO, 1))
		self.assertEqual(json.loads(doc.template_parameters), ["Centro Prova"])
		self.assertEqual((doc.reference_doctype, doc.reference_name), ("CRM Lead", self.anna.name))

	def test_sms_con_le_stesse_parole_dal_numero_del_centro(self):
		self.offri(sms="+390212345678", twilio=1)
		self.ha_scritto(avvisi.SMS)
		self.sceglie(avvisi.SMS)
		with mock.patch("crm.api.sms.deliver_via_twilio") as consegna:
			self.scrive("Il referto è pronto: lo trova nell'area")
		[sms] = consegna.call_args.args
		self.assertEqual((sms.get("from"), sms.to), ("+390212345678", NUMERO))
		self.assertIn("There is news in your area at", sms.message)
		self.assertNotIn("referto", sms.message)

	def test_un_avviso_che_non_parte_non_ferma_la_bacheca(self):
		self.ha_scritto()
		self.sceglie()
		frappe.set_user("Administrator")
		prima = frappe.db.count("Error Log")
		with mock.patch.object(avvisi, "_manda_whatsapp", side_effect=RuntimeError("Meta giù")):
			[messaggio] = self.scrive()["messages"]
		self.assertEqual(messaggio["body"], "Porti la tessera sanitaria")
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.count("Error Log"), prima + 1)


class LeImpostazioni(AvvisiCase):
	def test_le_sceglie_chi_configura_i_canali(self):
		self.come(DESK)
		with self.assertRaises(frappe.PermissionError):
			avvisi.save_notice_settings(MODELLO)
		self.come(MANAGER)
		fatto = avvisi.save_notice_settings(MODELLO, "+39 02 1234 5678")
		self.assertEqual((fatto["whatsapp_template"], fatto["sms_number"]), (MODELLO, "+390212345678"))
		self.assertIn(MODELLO, [t.name for t in fatto["templates"]])
		with self.assertRaises(frappe.ValidationError):
			avvisi.save_notice_settings("un-template-che-non-c-e")
		with self.assertRaises(frappe.ValidationError):
			avvisi.save_notice_settings(None, "non è un numero")
