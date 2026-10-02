# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Every SMS of the centre from one sender (doc 52, fourth part).

The manager chooses on Twilio's page: the centre's name, which nobody can answer,
or one of its numbers that can send SMS, when the answers must come back. With
nothing chosen, the first such number, else a name made from the centre's. The
SMS written by hand, the automations', the waiting list's and the client area's
all leave from it; somebody's own line - an Italian landline cannot send SMS -
never again.
"""

from unittest.mock import patch

import frappe

from crm.api import sms as sms_api
from crm.patches.v1_0 import the_centre_sends_sms_from_one_sender as patch_mittente
from crm.telephony import sms
from crm.telephony.tests.test_collegamento import TwilioCase

CELLULARE = "+393331234567"
FISSO = "+390212345678"


def numero_sms(numero: str, sms_capable: int = 1) -> None:
	"""One of the space's numbers in DottorCloud's list, as the sync writes it."""
	if frappe.db.exists("CRM Caller ID", numero):
		frappe.db.set_value("CRM Caller ID", numero, {"sms_capable": sms_capable, "enabled": 1})
		return
	frappe.get_doc(
		{
			"doctype": "CRM Caller ID",
			"phone_number": numero,
			"provider": "twilio",
			"source": "Account Number",
			"voice_capable": 1,
			"sms_capable": sms_capable,
			"enabled": 1,
		}
	).insert(ignore_permissions=True)


def mittente_di_prova(numero: str | None = None, nome: str | None = None, acceso: int = 1) -> None:
	"""Twilio on, and the centre's SMS from ``numero`` (one of its numbers that can
	send SMS) or ``nome``; neither: nothing chosen."""
	frappe.db.set_single_value(sms.IMPOSTAZIONI, "enabled", acceso)
	if numero:
		numero_sms(numero)
	frappe.db.set_single_value(
		sms.IMPOSTAZIONI,
		{
			"sms_from": sms.NUMERO if numero else sms.NOME if nome else "",
			"sms_sender_number": numero or "",
			"sms_sender_name": nome or "",
		},
	)


class IlMittente(TwilioCase):
	def test_quello_scelto(self):
		mittente_di_prova(nome="Aurora")
		self.assertEqual(sms.mittente(), "Aurora")
		mittente_di_prova(numero=CELLULARE)
		self.assertEqual(sms.mittente(), CELLULARE)
		self.assertTrue(sms.si_risponde(sms.mittente()))
		self.assertFalse(sms.si_risponde("Aurora"))

	def test_senza_scelta_il_primo_numero_poi_il_nome_del_centro(self):
		mittente_di_prova()
		with patch("crm.moduli.richieste.nome_del_centro", return_value="Centro Medico Aurora"):
			self.assertEqual(sms.mittente(), "Aurora")
			numero_sms(CELLULARE)
			self.assertEqual(sms.mittente(), CELLULARE)

	def test_un_numero_che_non_manda_piu_sms(self):
		mittente_di_prova(numero=CELLULARE)
		numero_sms(CELLULARE, sms_capable=0)
		with patch("crm.moduli.richieste.nome_del_centro", return_value="Aurora"):
			self.assertEqual(sms.mittente(), "Aurora")

	def test_twilio_spento_niente(self):
		mittente_di_prova(numero=CELLULARE, acceso=0)
		self.assertIsNone(sms.mittente())


class LaScelta(TwilioCase):
	def setUp(self):
		super().setUp()
		# a space of DottorCloud's: saving the page asks Twilio nothing
		self.collega()

	def salva(self, **campi):
		impostazioni = frappe.get_single(sms.IMPOSTAZIONI)
		impostazioni.update(campi)
		impostazioni.save(ignore_permissions=True)

	def test_un_nome_che_twilio_prende(self):
		self.salva(sms_from="Name", sms_sender_name="  Aurora ")
		self.assertEqual(frappe.db.get_single_value(sms.IMPOSTAZIONI, "sms_sender_name"), "Aurora")
		with self.assertRaises(frappe.ValidationError):
			self.salva(sms_from="Name", sms_sender_name="Centro Aurora Milano")
		with self.assertRaises(frappe.ValidationError):
			self.salva(sms_from="Name", sms_sender_name="Città")

	def test_solo_un_numero_che_manda_sms(self):
		numero_sms(CELLULARE)
		numero_sms(FISSO, sms_capable=0)
		self.salva(sms_from="Number", sms_sender_number=CELLULARE)
		with self.assertRaises(frappe.ValidationError):
			self.salva(sms_from="Number", sms_sender_number=FISSO)

	def test_le_opzioni_della_pagina(self):
		numero_sms(CELLULARE)
		frappe.db.set_single_value(sms.IMPOSTAZIONI, "enabled", 1)
		with patch("crm.moduli.richieste.nome_del_centro", return_value="Studio Più"):
			opzioni = sms.get_sms_sender_options()
		self.assertEqual([n["number"] for n in opzioni["numbers"]], [CELLULARE])
		self.assertEqual((opzioni["name"], opzioni["sender"]), ("Studio Piu", CELLULARE))


class DaDovePartono(TwilioCase):
	def setUp(self):
		super().setUp()
		mittente_di_prova(numero=CELLULARE)
		self.persona = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Marta",
				"last_name": "Mittente",
				"mobile_no": "+393401112233",
			}
		).insert(ignore_permissions=True)

	def test_scritto_a_mano(self):
		# somebody's own line - a landline here - is not where an SMS leaves from
		if not frappe.db.exists("CRM Telephony Agent", "Administrator"):
			frappe.get_doc(
				{"doctype": "CRM Telephony Agent", "user": "Administrator", "twilio_number": FISSO}
			).insert(ignore_permissions=True)
		with patch("crm.api.sms.deliver_via_twilio") as consegna:
			sms_api.send_sms("CRM Lead", self.persona.name, "+393401112233", "Ci vediamo domani")
		[doc] = consegna.call_args.args
		self.assertEqual((doc.get("from"), doc.to), (CELLULARE, "+393401112233"))

	def test_di_un_automazione(self):
		with patch("crm.api.sms.deliver_via_twilio") as consegna:
			sms_api.send_automation_sms("+393401112233", "Promemoria", "CRM Lead", self.persona.name)
		[doc] = consegna.call_args.args
		self.assertEqual(doc.get("from"), CELLULARE)

	def test_senza_mittente_non_parte(self):
		mittente_di_prova(acceso=0)
		with self.assertRaises(frappe.ValidationError):
			sms_api.send_sms("CRM Lead", self.persona.name, "+393401112233", "Ci vediamo domani")
		self.assertFalse(sms_api.send_automation_sms("+393401112233", "Promemoria"))


class IlNumeroDiPrima(TwilioCase):
	def test_quello_dell_area_diventa_il_mittente(self):
		frappe.db.set_single_value(sms.IMPOSTAZIONI, {"sms_from": "", "sms_sender_number": ""})
		for doctype, valore in (("CRM Area Settings", "+390299999999"), ("CRM Waiting List Settings", FISSO)):
			frappe.db.delete("Singles", {"doctype": doctype, "field": "sms_number"})
			frappe.db.sql(
				"insert into `tabSingles` (doctype, field, value) values (%s, %s, %s)",
				(doctype, "sms_number", valore),
			)
		patch_mittente.execute()
		scelta = frappe.db.get_singles_dict(sms.IMPOSTAZIONI)
		self.assertEqual((scelta.sms_from, scelta.sms_sender_number), ("Number", "+390299999999"))

	def test_una_scelta_fatta_resta(self):
		frappe.db.set_single_value(sms.IMPOSTAZIONI, {"sms_from": "Name", "sms_sender_name": "Aurora"})
		patch_mittente.execute()
		self.assertEqual(frappe.db.get_single_value(sms.IMPOSTAZIONI, "sms_from"), "Name")
