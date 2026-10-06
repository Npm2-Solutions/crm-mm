# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The reminders of the appointments, on a real site (docs/progetto-ghl/59).

Anna has a visit the day after tomorrow at half past nine. Tomorrow at ten the
round finds it, and the reminder leaves - by email, with the booking page's link,
where she says «I'll be there»; by SMS, where she answers «Sì» or «No»; by
WhatsApp with three buttons, where a tap confirms, cancels or asks to move it.
Her «no» cancels the visit and frees the time, or only tells the desk; in a class
it frees her seat alone. A visit moved is reminded again, one just booked is not,
nor the demo's, nor a platform's. A WhatsApp Meta could not deliver goes by email.
"""

import datetime
import json
import re
from unittest import mock

import frappe
from frappe.utils import add_to_date, now_datetime

from crm.api import appointments as agenda_api
from crm.api import service_booking as SB
from crm.notifiche import regole as N
from crm.scheduling import promemoria as P
from crm.scheduling import promemoria_regole as R
from crm.scheduling.timeutils import to_system_naive
from crm.telephony.tests.test_sms import mittente_di_prova
from crm.tests import serve_whatsapp
from crm.tests import test_scheduling as agenda

UTC = datetime.UTC
CHIARA = "promemoria.chiara@example.com"
MODELLO = "promemoria-prova"
LINK = re.compile(r"/prenota\?token=([A-Za-z0-9_-]+)")


class PromemoriaCase(agenda.SchedulingCase):
	def setUp(self):
		super().setUp()
		self.make_user(CHIARA)
		self.impostazioni(
			enabled=1,
			hours_before=24,
			cancel_on_reply=1,
			whatsapp_template=None,
			use_sms=0,
			use_email=1,
		)
		oggi = datetime.datetime.now(UTC).date()
		# the site's own appointments of these days are set aside: the round here is
		# about these tests' alone (rolled back after each one)
		frappe.db.sql(
			"""update `tabCRM Appointment` set status = 'Cancelled' where starts_on between %s and %s""",
			(oggi - datetime.timedelta(days=1), oggi + datetime.timedelta(days=6)),
		)
		# the words the person reads, in English here whatever the site's language
		lingua = mock.patch("crm.lingue.del_centro", return_value="en")
		lingua.start()
		self.addCleanup(lingua.stop)
		# tomorrow at ten, the centre's clock (UTC in these tests): the round's now
		self.adesso = datetime.datetime.combine(oggi + datetime.timedelta(days=1), datetime.time(10))
		self.inizio = datetime.datetime.combine(
			oggi + datetime.timedelta(days=2), datetime.time(9, 30), tzinfo=UTC
		)
		self.visita = self.make_service("Visita promemoria", [CHIARA], bookable_online=1)
		self.anna = self.persona("Anna", "anna.promemoria@example.com", "+393331110001")
		self.appuntamento = self.prenota(self.anna, self.inizio)
		orologio = mock.patch("crm.scheduling.promemoria._adesso", return_value=self.adesso)
		orologio.start()
		self.addCleanup(orologio.stop)
		posta = mock.patch("frappe.sendmail")
		self.sendmail = posta.start()
		self.addCleanup(posta.stop)

	# ---- the centre and its people

	def impostazioni(self, **campi):
		doc = frappe.get_doc(P.IMPOSTAZIONI)
		doc.update(campi)
		doc.save(ignore_permissions=True)

	def persona(self, nome, email=None, cellulare=None):
		return frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": nome,
				"last_name": "Promemoria",
				"email": email or "",
				"mobile_no": cellulare or "",
			}
		).insert(ignore_permissions=True)

	def riga(self, persona):
		return {
			"party_type": "CRM Lead",
			"party": persona.name,
			"participant_name": persona.lead_name,
			"email": persona.email,
			"phone": persona.mobile_no,
			"status": "Booked",
		}

	def prenota(self, *persone_e_inizio, servizio=None, **altro):
		*persone, inizio = persone_e_inizio
		doc = self.make_appointment(
			(servizio or self.visita).name,
			inizio,
			[CHIARA],
			status="Confirmed",
			participants=[self.riga(persona) for persona in persone],
			**altro,
		)
		# booked a week ago: its reminder is not the booking's own
		frappe.db.set_value("CRM Appointment", doc.name, "creation", add_to_date(now_datetime(), days=-7))
		return frappe.get_doc("CRM Appointment", doc.name)

	def giro(self):
		P.ogni_quarto_d_ora()

	def registri(self, appuntamento=None):
		return frappe.get_all(
			P.PROMEMORIA,
			filters={"appointment": (appuntamento or self.appuntamento).name},
			fields=["*"],
			order_by="creation asc",
		)

	def registro(self, appuntamento=None):
		[riga] = self.registri(appuntamento)
		return riga

	def avvisi(self, frase):
		return frappe.get_all(
			"CRM Notification",
			filters={"to_user": CHIARA, "sentence": frase, "notification_type_doc": self.appuntamento.name},
			pluck="name",
		)


class QuandoParte(PromemoriaCase):
	def test_per_email_il_giorno_prima_una_volta(self):
		self.giro()
		[chiamata] = self.sendmail.call_args_list
		self.assertEqual(chiamata.kwargs["recipients"], ["anna.promemoria@example.com"])
		self.assertIn("Visita promemoria", chiamata.kwargs["subject"])
		token = LINK.search(chiamata.kwargs["message"]).group(1)
		self.assertEqual(
			frappe.db.get_value(
				"CRM Appointment Participant", {"parent": self.appuntamento.name}, "access_token"
			),
			token,
		)
		registro = self.registro()
		self.assertEqual((registro.channel, registro.status), (R.EMAIL, R.INVIATO))
		# the next round finds it done
		self.giro()
		self.assertEqual(len(self.sendmail.call_args_list), 1)
		self.assertEqual(len(self.registri()), 1)

	def test_non_prima_del_suo_momento(self):
		with mock.patch("crm.scheduling.promemoria._adesso", return_value=self.adesso.replace(hour=9)):
			self.giro()
		self.sendmail.assert_not_called()
		self.assertEqual(self.registri(), [])

	def test_spostato_si_ricorda_dell_ora_nuova(self):
		self.giro()
		doc = frappe.get_doc("CRM Appointment", self.appuntamento.name)
		doc.starts_on = to_system_naive(self.inizio + datetime.timedelta(hours=2))
		doc.ends_on = to_system_naive(self.inizio + datetime.timedelta(hours=3))
		doc.save()
		with mock.patch("crm.scheduling.promemoria._adesso", return_value=self.adesso.replace(hour=12)):
			self.giro()
		self.assertEqual(len(self.registri()), 2)

	def test_appena_prenotato_no(self):
		# booked an hour ago: the reminder's moment, half past nine, was half an hour later
		appena = to_system_naive((self.adesso - datetime.timedelta(hours=1)).replace(tzinfo=UTC))
		frappe.db.set_value("CRM Appointment", self.appuntamento.name, "creation", appena)
		self.giro()
		self.sendmail.assert_not_called()

	def test_ne_la_demo_ne_le_piattaforme(self):
		frappe.db.set_value("CRM Appointment", self.appuntamento.name, "source", "External")
		self.giro()
		frappe.db.set_value("CRM Appointment", self.appuntamento.name, "source", "Internal")
		with mock.patch("crm.demo.guardie.mai_fuori", return_value=True):
			self.giro()
		self.sendmail.assert_not_called()
		self.assertEqual(self.registri(), [])

	def test_spenti_non_parte_niente(self):
		self.impostazioni(enabled=0)
		self.giro()
		self.sendmail.assert_not_called()

	def test_senza_recapiti_lo_dice(self):
		nessuno = self.persona("Nessuno")
		altro = self.prenota(nessuno, self.inizio + datetime.timedelta(hours=1))
		with mock.patch("crm.scheduling.promemoria._adesso", return_value=self.adesso.replace(hour=11)):
			self.giro()
		registro = self.registro(altro)
		self.assertEqual(registro.status, R.NON_INVIATO)
		self.assertIn("call them", registro.reason)


class PerSms(PromemoriaCase):
	def setUp(self):
		super().setUp()
		# the centre's SMS leave from a number: the person can answer it
		mittente_di_prova(numero="+390212345678")
		self.impostazioni(use_sms=1, use_email=0)
		consegna = mock.patch("crm.api.sms.deliver_via_twilio")
		self.consegna = consegna.start()
		self.addCleanup(consegna.stop)

	def risponde(self, testo, numero="+393331110001"):
		return P.alla_risposta_sms(frappe._dict({"message": testo, "from": numero}))

	def test_parte_e_il_si_conferma(self):
		self.giro()
		[sms] = self.consegna.call_args.args
		self.assertEqual((sms.get("from"), sms.to), ("+390212345678", "+393331110001"))
		self.assertIn("YES", sms.message)
		self.assertRegex(sms.message, LINK)
		self.assertEqual(self.registro().channel, R.SMS)
		self.assertEqual(self.risponde("Sì, grazie"), "")
		registro = self.registro()
		self.assertEqual((registro.answer, registro.answered_by), (R.CONFERMA, R.SMS))

	def test_il_no_disdice_e_libera_l_ora(self):
		self.giro()
		risposta = self.risponde("NO")
		self.assertIn("cancelled", risposta)
		doc = frappe.get_doc("CRM Appointment", self.appuntamento.name)
		self.assertEqual(doc.status, "Cancelled")
		self.assertIn("reminder", doc.cancellation_reason)
		self.assertTrue(self.registro().cancelled)
		# whoever the visit was with is told, and the notification opens the agenda on it
		self.assertTrue(self.avvisi(N.PROMEMORIA_DISDETTO))
		# the same «no» again does nothing more
		self.assertEqual(self.risponde("no"), "")

	def test_senza_disdire_avvisa_soltanto(self):
		self.impostazioni(cancel_on_reply=0)
		self.giro()
		self.assertIn("the centre will cancel it", self.risponde("no"))
		self.assertEqual(
			frappe.db.get_value("CRM Appointment", self.appuntamento.name, "status"), "Confirmed"
		)
		self.assertTrue(self.avvisi(N.PROMEMORIA_NON_VIENE))

	def test_un_altro_numero_o_un_messaggio_non_rispondono(self):
		self.giro()
		self.assertEqual(self.risponde("SI", numero="+393339999999"), "")
		self.assertEqual(self.risponde("Arrivo dieci minuti in ritardo"), "")
		self.assertFalse(self.registro().answer)

	def test_sposta_manda_il_link_della_pagina(self):
		self.giro()
		risposta = self.risponde("sposta")
		self.assertRegex(risposta, LINK)
		self.assertEqual(self.registro().answer, R.SPOSTA)
		self.assertTrue(self.avvisi(N.PROMEMORIA_SPOSTA))

	def test_chi_ha_scritto_stop_non_riceve_sms(self):
		frappe.db.set_value("CRM Lead", self.anna.name, "sms_opt_out", 1)
		self.giro()
		self.consegna.assert_not_called()
		self.assertEqual(self.registro().status, R.NON_INVIATO)

	def test_in_una_lezione_libera_solo_il_suo_posto(self):
		marco = self.persona("Marco", "marco.promemoria@example.com", "+393331110002")
		lezione = self.make_service("Pilates promemoria", [CHIARA], max_participants=6)
		classe = self.prenota(self.anna, marco, self.inizio + datetime.timedelta(hours=1), servizio=lezione)
		with mock.patch("crm.scheduling.promemoria._adesso", return_value=self.adesso.replace(hour=11)):
			self.giro()
			# the two visits of Anna's: the class's is the latest reminder sent
			self.risponde("no")
		doc = frappe.get_doc("CRM Appointment", classe.name)
		stati = {riga.party: riga.status for riga in doc.participants}
		self.assertEqual(doc.status, "Confirmed")
		self.assertEqual(stati, {self.anna.name: "Cancelled", marco.name: "Booked"})


class PerWhatsApp(PromemoriaCase):
	def setUp(self):
		# skipped before anything is made: a setUp that stops gets no tearDown, and
		# what it made would stay for the next test
		serve_whatsapp(self)
		super().setUp()
		self.modello()
		self.impostazioni(whatsapp_template=MODELLO, use_email=1)
		self.mandati = []
		spedisce = mock.patch("crm.api.whatsapp.insert_and_send", side_effect=self._spedisce)
		spedisce.start()
		self.addCleanup(spedisce.stop)

	def modello(self):
		if frappe.db.exists("WhatsApp Templates", MODELLO):
			return
		modello = frappe.get_doc(
			{
				"doctype": "WhatsApp Templates",
				"name": MODELLO,
				"template_name": MODELLO,
				"template": R.modello("it")["template"],
				"language": frappe.db.get_value("Language", {}, "name") or "it",
				"category": "UTILITY",
				"status": "APPROVED",
			}
		)
		# as it is after Meta approved it: nothing is asked of Meta here
		modello.db_insert()
		for i, testo in enumerate(R.modello("it")["buttons"], start=1):
			frappe.get_doc(
				{
					"doctype": "WhatsApp Button",
					"parent": MODELLO,
					"parenttype": "WhatsApp Templates",
					"parentfield": "buttons",
					"idx": i,
					"button_type": "Quick Reply",
					"button_label": testo,
				}
			).db_insert()

	def _spedisce(self, doc):
		# the message as Meta's answer leaves it: written, with its id
		doc.name = frappe.generate_hash(length=10)
		doc.message_id = f"wamid.{doc.name}"
		doc.type = doc.type or "Outgoing"
		doc.db_insert()
		self.mandati.append(doc)
		return doc.name

	def tocca(self, testo, numero="393331110001"):
		[promemoria] = [m for m in self.mandati if m.message_type == "Template"]
		return frappe.get_doc(
			{
				"doctype": "WhatsApp Message",
				"type": "Incoming",
				"from": numero,
				"message": testo,
				"message_id": f"wamid.risposta.{frappe.generate_hash(length=6)}",
				"content_type": "button",
				"is_reply": 1,
				"reply_to_message_id": promemoria.message_id,
			}
		).insert(ignore_permissions=True)

	def test_il_modello_con_le_sue_variabili(self):
		self.giro()
		[promemoria] = self.mandati
		variabili = list(json.loads(promemoria.body_param).values())
		self.assertEqual(variabili[:2], ["Anna", "Visita promemoria"])
		self.assertEqual(len(variabili), 4)
		self.assertEqual((promemoria.to, promemoria.reference_name), ("+393331110001", self.anna.name))
		registro = self.registro()
		self.assertEqual((registro.channel, registro.message_name), (R.WHATSAPP, promemoria.name))
		self.sendmail.assert_not_called()

	def test_il_modello_dei_promemoria_e_dell_account_che_invia(self):
		# two WhatsApp Business accounts: ours made on the first is not the second's
		uno, due = "Promemoria uno", "Promemoria due"
		for nome, waba in ((uno, "8801"), (due, "8802")):
			if not frappe.db.exists("WhatsApp Account", nome):
				frappe.get_doc(
					{
						"doctype": "WhatsApp Account",
						"account_name": nome,
						"business_id": waba,
						"phone_id": f"ph-{nome}",
						"token": "finto",
						"status": "Active",
					}
				).insert(ignore_permissions=True)
		nostro = R.modello("en")["template_name"]
		frappe.get_doc(
			{
				"doctype": "WhatsApp Templates",
				"name": f"{nostro}-prova",
				"template_name": nostro,
				"actual_name": nostro,
				"template": R.modello("en")["template"],
				"language": frappe.db.get_value("Language", {}, "name") or "en",
				"category": "UTILITY",
				"status": "PENDING",
				"whatsapp_account": uno,
			}
		).db_insert()
		with mock.patch("crm.api.whatsapp.sending_account_name", return_value=due):
			self.assertIsNone(P._il_nostro())
			# Meta's names are per account, the site's one for all: made there it is «_2»
			self.assertEqual(P._nome_libero(nostro), f"{nostro}_2")
		with mock.patch("crm.api.whatsapp.sending_account_name", return_value=uno):
			self.assertEqual(P._il_nostro(), {"name": f"{nostro}-prova", "status": "PENDING"})
		# the template's words stay the rules' own, whatever a caller changes
		R.modello("en")["template_name"] = "altro"
		self.assertEqual(R.modello("en")["template_name"], nostro)

	def test_un_tocco_conferma_e_risponde(self):
		self.giro()
		self.tocca("Confermo")
		registro = self.registro()
		self.assertEqual((registro.answer, registro.answered_by), (R.CONFERMA, R.WHATSAPP))
		[grazie] = [m for m in self.mandati if m.message_type != "Template"]
		self.assertIn("Anna", grazie.message)
		self.assertEqual(grazie.to, "393331110001")

	def test_devo_disdire_libera_l_ora(self):
		self.giro()
		self.tocca("Devo disdire")
		self.assertEqual(
			frappe.db.get_value("CRM Appointment", self.appuntamento.name, "status"), "Cancelled"
		)

	def test_da_un_altro_numero_niente(self):
		self.giro()
		self.tocca("Devo disdire", numero="393339999999")
		self.assertFalse(self.registro().answer)
		self.assertEqual(
			frappe.db.get_value("CRM Appointment", self.appuntamento.name, "status"), "Confirmed"
		)

	def test_non_arrivato_va_per_email(self):
		self.giro()
		[promemoria] = self.mandati
		frappe.db.set_value("WhatsApp Message", promemoria.name, "status", "failed")
		self.giro()
		registro = self.registro()
		self.assertEqual((registro.channel, registro.status), (R.EMAIL, R.INVIATO))
		self.assertIn("WhatsApp", registro.reason)
		self.sendmail.assert_called_once()

	def test_un_modello_senza_i_pulsanti_non_si_sceglie(self):
		frappe.db.delete("WhatsApp Button", {"parent": MODELLO})
		with self.assertRaises(frappe.ValidationError):
			P.save_settings({"whatsapp_template": MODELLO})


class DallaPagina(PromemoriaCase):
	def ospite(self, funzione, *args):
		frappe.set_user("Guest")
		try:
			return funzione(*args)
		finally:
			frappe.set_user("Administrator")

	def test_ci_saro(self):
		self.giro()
		token = LINK.search(self.sendmail.call_args.kwargs["message"]).group(1)
		vista = self.ospite(SB.get_booking, token)
		self.assertTrue(vista["can_confirm"])
		# booked at the desk: booked, not waiting for anybody's yes
		self.assertFalse(vista["pending_approval"])
		vista = self.ospite(SB.confirm, token)
		self.assertTrue(vista["confirmed"])
		self.assertFalse(vista["can_confirm"])
		self.assertEqual(self.registro().answered_by, R.DALLA_PAGINA)

	def test_disdetto_sulla_pagina_e_la_sua_risposta(self):
		self.giro()
		token = LINK.search(self.sendmail.call_args.kwargs["message"]).group(1)
		self.ospite(SB.cancel, token, "")
		registro = self.registro()
		self.assertEqual(
			(registro.answer, registro.answered_by, registro.cancelled), (R.NON_VIENE, R.DALLA_PAGINA, 1)
		)
		self.assertEqual(
			frappe.db.get_value("CRM Appointment", self.appuntamento.name, "status"), "Cancelled"
		)

	def test_la_reception_vede_la_risposta(self):
		from crm.api import oggi

		self.giro()
		token = LINK.search(self.sendmail.call_args.kwargs["message"]).group(1)
		self.ospite(SB.confirm, token)
		giorno = oggi.get_day(self.inizio.date().isoformat())
		[appuntamento] = [a for a in giorno["appointments"] if a["name"] == self.appuntamento.name]
		self.assertEqual(appuntamento["participants"][0]["reminder"]["answer"], R.CONFERMA)

	def test_senza_promemoria_niente_da_confermare(self):
		token = P._link(frappe.get_doc("CRM Appointment", self.appuntamento.name).participants[0])
		vista = self.ospite(SB.get_booking, LINK.search(token).group(1))
		self.assertFalse(vista["can_confirm"])

	def test_l_agenda_vede_la_risposta(self):
		self.giro()
		token = LINK.search(self.sendmail.call_args.kwargs["message"]).group(1)
		self.ospite(SB.confirm, token)
		giorno = self.inizio.date().isoformat()
		feed = agenda_api.get_calendar(giorno, giorno)
		[appuntamento] = [a for a in feed["appointments"] if a["name"] == self.appuntamento.name]
		self.assertEqual(appuntamento["participants"][0]["reminder"]["answer"], R.CONFERMA)
