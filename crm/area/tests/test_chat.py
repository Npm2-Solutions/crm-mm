# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The patient's chat in the area: administration only.

Carla asks about a pain in her chest: 112, before any model. She asks whether she
can come with a fever: the chat does not answer, it offers to pass the question
to the centre; passed on, it is on her board, the desk hears of it without the
words and answers there. She asks when the centre opens on Saturday: the model
answers from the hours and the questions the centre wrote, and does not read who
she is; the register keeps the answer for the medical director. What the model
does not know goes to a person too. With the chat off there is no chat.
"""

import json
from unittest import mock

import frappe
import requests

from crm.assistente import modello, regole
from crm.clinica import CHAT, paziente
from crm.clinica.area import accesso, api, chat, messaggi
from crm.clinica.tests.test_area import CARLA, AreaCase
from crm.clinica.tests.test_assistente_clinico import risposta
from crm.clinica.tests.test_cartella import DESK, DOC1
from crm.permissions import livelli


class ChatCase(AreaCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.carla = frappe.get_doc(
			{"doctype": "CRM Lead", "first_name": "Carla", "last_name": "Bacheca", "email": CARLA}
		).insert(ignore_permissions=True)
		for user in (DESK, DOC1):
			frappe.get_doc(
				{
					"doctype": "ToDo",
					"reference_type": "CRM Lead",
					"reference_name": self.carla.name,
					"allocated_to": user,
					"description": "Carla",
				}
			).insert(ignore_permissions=True)
		frappe.cache.delete_value(accesso._chiave_codice(CARLA))
		self.come(DESK)
		accesso.invite(self.carla.name)
		frappe.set_user("Administrator")
		piano = frappe.get_single("CRM Plan")
		piano.set(
			"modules",
			[{"module": "clinica", "status": "Active"}, {"module": "assistente", "status": "Active"}],
		)
		piano.save()
		orari = frappe.get_single("CRM Scheduling Settings")
		orari.set(
			"default_availability",
			[
				{"workday": "Monday", "start_time": "08:00:00", "end_time": "19:00:00"},
				{"workday": "Saturday", "start_time": "08:30:00", "end_time": "12:30:00"},
			],
		)
		orari.flags.ignore_mandatory = True
		orari.save(ignore_permissions=True)
		self.impostazioni(patient_chat=1)

	def tearDown(self):
		super().tearDown()
		frappe.clear_document_cache(modello.IMPOSTAZIONI, modello.IMPOSTAZIONI)
		frappe.clear_document_cache("CRM Scheduling Settings", "CRM Scheduling Settings")

	def impostazioni(self, **valori):
		frappe.set_user("Administrator")
		cfg = frappe.get_single(modello.IMPOSTAZIONI)
		cfg.update(
			{
				"enabled": 1,
				"provider": regole.ANTHROPIC,
				"base_url": "https://llm.example.eu",
				"model": "claude-prova",
				"api_key": "chiave",
				"region": "EU",
				"no_retention": 1,
				"chat_about": "Siamo in via Roma 12, parcheggio in cortile. Si paga anche con il bancomat.",
				**valori,
			}
		)
		cfg.set(
			"chat_faq",
			[{"question": "Serve l'impegnativa?", "answer": "Per le visite private no."}],
		)
		cfg.save()
		frappe.clear_document_cache(modello.IMPOSTAZIONI, modello.IMPOSTAZIONI)
		livelli.dimentica_cache()

	def chiede(self, domanda, testo=None, history=None):
		with mock.patch.object(requests, "post", return_value=risposta(testo or "{}")) as post:
			fatto = chat.ask(self.carla.name, domanda, json.dumps(history or []))
		return fatto, post


class LaSalute(ChatCase):
	def test_un_emergenza_ha_il_112_prima_di_tutto(self):
		self.entra(CARLA)
		fatto, post = self.chiede("Ho un forte dolore al petto da stamattina")
		self.assertEqual((fatto["kind"], fatto["can_pass"]), ("emergency", False))
		self.assertIn("112", fatto["answer"])
		post.assert_not_called()
		# even with the chat off: an emergency is never left without an answer
		self.impostazioni(patient_chat=0)
		frappe.set_user(CARLA)
		self.assertEqual(self.chiede("Non riesco a respirare")[0]["kind"], "emergency")

	def test_la_salute_si_passa_al_centro_senza_le_parole_nell_avviso(self):
		self.entra(CARLA)
		domanda = "Ho la febbre da ieri, posso venire alla visita di domani?"
		fatto, post = self.chiede(domanda)
		self.assertEqual((fatto["kind"], fatto["can_pass"]), ("health", True))
		post.assert_not_called()
		chat.pass_on(self.carla.name, domanda)
		# not a patient for a question: only what the centre writes about the care makes one
		frappe.set_user("Administrator")
		self.assertFalse(paziente.e_paziente(self.carla.name))
		avvisi = frappe.get_all(
			"CRM Notification",
			filters={"type": "Area", "reference_name": self.carla.name},
			fields=["to_user", "notification_text"],
		)
		self.assertIn(DESK, [a.to_user for a in avvisi])
		self.assertTrue(all("febbre" not in a.notification_text for a in avvisi))
		# the desk reads it on Carla's board, and she sees it was read
		self.come(DESK)
		[letta] = messaggi.get_messages(self.carla.name)["messages"]
		self.assertEqual((letta["kind"], letta["body"]), (messaggi.DOMANDA, domanda))
		self.entra(CARLA)
		self.assertEqual(api.get_me()["people"][0]["unread"], 0)
		[mia] = messaggi.area_messages(self.carla.name)["messages"]
		self.assertTrue(mia["read_on"])


class LAmministrazione(ChatCase):
	def test_risponde_da_quello_che_il_centro_ha_scritto(self):
		self.entra(CARLA)
		self.assertTrue(api.get_me()["chat"])
		fatto, post = self.chiede(
			"A che ora aprite il sabato?",
			json.dumps({"answer": "Il sabato apriamo dalle 8:30 alle 12:30.", "handoff": False}),
			history=[{"role": "patient", "text": "Buongiorno"}, {"role": "assistant", "text": "Buongiorno!"}],
		)
		self.assertEqual(
			fatto, {"kind": "answer", "answer": "Il sabato apriamo dalle 8:30 alle 12:30.", "can_pass": False}
		)
		inviato = post.call_args.kwargs["json"]
		sistema = inviato["system"]
		self.assertIn("an AI, not a person", sistema)
		self.assertIn("Saturday: 08:30-12:30", sistema)
		self.assertIn("parcheggio in cortile", sistema)
		self.assertIn("Q: Serve l'impegnativa?", sistema)
		conversazione = json.dumps(inviato["messages"], ensure_ascii=False)
		self.assertIn("Patient: Buongiorno", conversazione)
		self.assertIn("The patient asks: A che ora aprite il sabato?", conversazione)
		# the model does not read who asks
		for chi in ("Carla", "Bacheca", CARLA):
			self.assertNotIn(chi, json.dumps(inviato, ensure_ascii=False))
		frappe.set_user("Administrator")
		evento = frappe.get_last_doc(modello.EVENTO, filters={"function": CHAT.chiave})
		self.assertEqual((evento.status, evento.reference_name), (regole.CONSEGNATA, self.carla.name))
		self.assertEqual(evento.read_capability, "assistente.registro_clinico")

	def test_quello_che_non_sa_lo_passa_a_una_persona(self):
		self.entra(CARLA)
		fatto, _post = self.chiede(
			"Fate le visite a domicilio?",
			json.dumps({"answer": "Non lo so: può risponderle una persona del centro.", "handoff": True}),
		)
		self.assertEqual((fatto["kind"], fatto["can_pass"]), ("answer", True))
		fatto, _post = self.chiede("Avete il wifi?", "Certo, la password è…")
		self.assertEqual((fatto["kind"], fatto["can_pass"]), ("unavailable", True))

	def test_spenta_non_c_e_chat(self):
		self.impostazioni(patient_chat=0)
		self.entra(CARLA)
		self.assertFalse(api.get_me()["chat"])
		with self.assertRaises(frappe.ValidationError):
			self.chiede("A che ora aprite?")
		with self.assertRaises(frappe.ValidationError):
			chat.pass_on(self.carla.name, "A che ora aprite?")

	def test_senza_l_assistente_nel_piano_non_c_e_chat(self):
		frappe.set_user("Administrator")
		piano = frappe.get_single("CRM Plan")
		piano.set("modules", [{"module": "clinica", "status": "Active"}])
		piano.save()
		livelli.dimentica_cache()
		self.entra(CARLA)
		self.assertFalse(api.get_me()["chat"])
		with self.assertRaises(frappe.ValidationError):
			self.chiede("A che ora aprite?")

	def test_niente_chat_nelle_aree_altrui(self):
		self.entra(CARLA)
		with self.assertRaises(frappe.PermissionError):
			chat.ask(self.anna.name, "A che ora aprite?")
		with self.assertRaises(frappe.PermissionError):
			chat.pass_on(self.anna.name, "A che ora aprite?")
