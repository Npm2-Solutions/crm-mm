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

import json
from datetime import datetime
from unittest.mock import patch

import frappe
from frappe.utils import get_datetime

from crm.api import sms as sms_api
from crm.automation import engine
from crm.integrations.twilio import api as twilio_api
from crm.moduli import consensi, registro
from crm.patches.v1_0 import the_centre_sends_sms_from_one_sender as patch_mittente
from crm.telephony import sms
from crm.telephony.tests.test_collegamento import TwilioCase

CELLULARE = "+393331234567"
FISSO = "+390212345678"
PERSONA = "+393401112233"


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


class IlFermo(TwilioCase):
	"""STOP and START, written to the centre's number: nothing automatic by SMS any
	more, the marketing consent withdrawn - or refused, when it was never asked -
	and an answer that says so, kept in the conversation."""

	def setUp(self):
		super().setUp()
		mittente_di_prova(numero=CELLULARE)
		self.persona = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Sara", "last_name": "Stop", "mobile_no": PERSONA}
		).insert(ignore_permissions=True)
		for finto in (
			patch("crm.integrations.twilio.api.validate_twilio_request", return_value=None),
			patch("crm.moduli.richieste.nome_del_centro", return_value="Aurora"),
			# the webhook commits for Twilio's sake; a test keeps everything to roll back
			patch.object(frappe.db, "commit"),
		):
			finto.start()
			self.addCleanup(finto.stop)

	def scrive(self, testo: str) -> str:
		"""The person writes ``testo`` to the centre's number; what Twilio is told back."""
		frappe.set_user("Guest")
		try:
			risposta = twilio_api.incoming_sms_handler(From=PERSONA, To=CELLULARE, Body=testo)
		finally:
			frappe.set_user("Administrator")
		return risposta.get_data(as_text=True)

	def fermo(self):
		return frappe.db.get_value(
			"CRM Lead", self.persona.name, ["sms_opt_out", "sms_opt_out_on"], as_dict=True
		)

	def test_stop_ferma_e_lo_dice(self):
		xml = self.scrive(" Stop! ")
		self.assertIn("<Message>", xml)
		self.assertIn("START", xml)
		fermo = self.fermo()
		self.assertEqual(fermo.sms_opt_out, 1)
		self.assertTrue(fermo.sms_opt_out_on)
		self.assertTrue(sms.ha_fermato("CRM Lead", self.persona.name))
		# the answer stays in the conversation, from the number written to
		[risposta] = frappe.get_all(
			"CRM SMS Message",
			filters={
				"type": "Outgoing",
				"reference_doctype": "CRM Lead",
				"reference_name": self.persona.name,
			},
			fields=["from", "to", "status"],
		)
		self.assertEqual((risposta["from"], risposta.to, risposta.status), (CELLULARE, PERSONA, "Sent"))
		# never asked about marketing: the register says no, by SMS
		self.assertEqual(consensi.stato(self.persona.name, sms.CONSENSO), registro.RIFIUTATO)
		self.assertEqual(consensi.risposta_attuale(self.persona.name, sms.CONSENSO)["channel"], sms.CANALE)

	def test_stop_revoca_il_consenso_dato(self):
		consensi.registra_risposta(self.persona.name, sms.CONSENSO, stato=registro.DATO)
		self.scrive("STOP")
		attuale = consensi.risposta_attuale(self.persona.name, sms.CONSENSO)
		self.assertEqual(attuale["status"], registro.REVOCATO)
		self.assertEqual(
			frappe.db.get_value(consensi.REGISTRO, attuale["name"], "withdrawal_channel"), sms.CANALE
		)
		# a second STOP writes nothing more
		self.scrive("stop")
		self.assertEqual(len(consensi.risposte(self.persona.name, sms.CONSENSO)), 1)

	def test_start_riprende_ma_non_ridà_il_consenso(self):
		self.scrive("STOP")
		xml = self.scrive("start")
		self.assertIn("STOP", xml)
		self.assertEqual(self.fermo().sms_opt_out, 0)
		self.assertFalse(sms.ha_fermato("CRM Lead", self.persona.name))
		self.assertEqual(consensi.stato(self.persona.name, sms.CONSENSO), registro.RIFIUTATO)

	def test_un_messaggio_resta_un_messaggio(self):
		xml = self.scrive("Stop, mi richiami domani")
		self.assertNotIn("<Message>", xml)
		self.assertEqual(self.fermo().sms_opt_out, 0)

	def test_una_parola_non_muove_le_automazioni(self):
		with patch("crm.automation.engine.process_event") as evento:
			self.scrive("STOP")
			self.scrive("Grazie, a domani")
		[(chiamata, _messaggio)] = [c.args for c in evento.call_args_list]
		self.assertEqual(chiamata, "sms_received")

	def test_chi_scrive_lo_vede_nel_box(self):
		self.assertIsNone(sms_api.get_sms_stop("CRM Lead", self.persona.name))
		self.scrive("STOP")
		self.assertTrue(sms_api.get_sms_stop("CRM Lead", self.persona.name))

	def test_un_automazione_non_lo_manda(self):
		automazione = automazione_sms()
		self.scrive("STOP")
		with patch("crm.api.sms.deliver_via_twilio") as consegna:
			iscrizione = engine.enroll(automazione.name, "CRM Lead", self.persona.name, {})
		consegna.assert_not_called()
		[riga] = frappe.get_doc("CRM Automation Enrollment", iscrizione).logs
		self.assertEqual((riga.action, riga.status), ("send_sms", "Skipped"))


def automazione_sms(**campi):
	"""An automation of one SMS, nothing else."""
	return frappe.get_doc(
		{
			"doctype": "CRM Automation",
			"title": "Un SMS",
			"enabled": 1,
			"trigger_event": "Lead Created",
			"steps": json.dumps([{"type": "send_sms", "message": "Ci vediamo domani"}]),
			**campi,
		}
	).insert(ignore_permissions=True)


class LOrarioDellaPromozione(TwilioCase):
	"""A promotional SMS leaves Monday to Saturday, 8 to 22: written outside those
	hours it waits for them; a reminder of the centre's does not wait."""

	def setUp(self):
		super().setUp()
		mittente_di_prova(numero=CELLULARE)
		self.persona = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Paola", "last_name": "Promo", "mobile_no": PERSONA}
		).insert(ignore_permissions=True)
		consensi.registra_risposta(self.persona.name, sms.CONSENSO, stato=registro.DATO)

	def iscrivi(self, automazione, adesso):
		with (
			patch("crm.automation.engine.now_datetime", return_value=adesso),
			patch("crm.api.sms.deliver_via_twilio") as consegna,
		):
			iscrizione = engine.enroll(automazione.name, "CRM Lead", self.persona.name, {})
		return frappe.get_doc("CRM Automation Enrollment", iscrizione), consegna

	def test_la_domenica_aspetta_il_lunedi_alle_otto(self):
		domenica = datetime(2026, 10, 4, 10, 0)
		iscrizione, consegna = self.iscrivi(automazione_sms(marketing_consent=1), domenica)
		consegna.assert_not_called()
		self.assertEqual(iscrizione.status, "Waiting")
		self.assertEqual(get_datetime(iscrizione.wait_until), datetime(2026, 10, 5, 8, 0))

	def test_un_promemoria_parte_anche_la_domenica(self):
		domenica = datetime(2026, 10, 4, 10, 0)
		_iscrizione, consegna = self.iscrivi(automazione_sms(), domenica)
		consegna.assert_called_once()

	def test_di_giorno_parte(self):
		sabato = datetime(2026, 10, 3, 21, 59)
		_iscrizione, consegna = self.iscrivi(automazione_sms(marketing_consent=1), sabato)
		consegna.assert_called_once()
