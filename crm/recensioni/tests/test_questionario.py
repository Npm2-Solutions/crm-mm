# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A satisfaction survey after a visit, on a real site: «Send a form» sends its
link, which opens with no code; sent, its 0 to 10 answer makes the dashboard's
Net Promoter Score. Only to who agreed to be asked; a survey asks no consent,
signature or file."""

import json
from unittest import mock

import frappe
from frappe.utils import add_to_date, nowdate

from crm.automation import engine
from crm.dashboard import registry
from crm.dashboard.context import Context
from crm.moduli import consensi, modelli, richieste
from crm.moduli.tests.test_richieste import LINK, RichiesteCase

NPS = {
	"sections": [
		{
			"id": "visit",
			"title": "La tua visita",
			"fields": [
				{"id": "recommend", "type": "scale", "label": "Ci consiglieresti?", "min": 0, "max": 10},
				{"id": "comment", "type": "text", "label": "Perché?"},
			],
		}
	]
}


class IlQuestionario(RichiesteCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.questionario = self.pubblica(NPS, "Quanto ci consiglieresti?", use="Survey")
		self.auto = frappe.get_doc(
			{
				"doctype": "CRM Automation",
				"title": "Questionario dopo la visita",
				"enabled": 1,
				"trigger_event": "Appointment Completed",
				"steps": json.dumps([{"type": "send_form", "template": self.questionario, "via": "email"}]),
			}
		).insert()

	def acconsente(self):
		consensi.registra_risposta(self.giulia.name, "review_requests", "Given", "At the desk")

	def dopo_la_visita(self, automazione=None):
		frappe.set_user("Administrator")
		with mock.patch.object(richieste, "_segreto", return_value=LINK):
			nome = engine.enroll((automazione or self.auto).name, "CRM Lead", self.giulia.name, {})
		return frappe.get_doc("CRM Automation Enrollment", nome)

	def test_un_questionario_non_chiede_consensi_firme_o_file(self):
		schema = {
			"sections": [
				{
					"id": "s",
					"fields": [
						{"id": "ok", "type": "consent", "label": "Privacy", "consent_type": "marketing"},
						{"id": "firma", "type": "signature", "label": "Firma"},
					],
				}
			]
		}
		codici = [p["code"] for p in modelli.problemi_dell_uso(schema, "Survey")]
		self.assertEqual(codici, ["not_without_a_code", "not_without_a_code"])
		self.assertIn("Survey", modelli.usi_da_mandare())

	def test_senza_consenso_non_parte(self):
		iscrizione = self.dopo_la_visita()
		self.assertEqual(iscrizione.logs[0].status, "Skipped")
		self.assertFalse(frappe.db.exists(richieste.RICHIESTA, {"lead": self.giulia.name}))

	def test_si_apre_col_solo_link_e_si_manda(self):
		self.acconsente()
		iscrizione = self.dopo_la_visita()
		self.assertEqual(iscrizione.logs[0].status, "Success", iscrizione.logs[0].detail)
		richiesta = frappe.get_last_doc(richieste.RICHIESTA, filters={"lead": self.giulia.name})
		self.assertEqual((richiesta.channel, richiesta.template), ("Link", self.questionario))
		posta = frappe.get_last_doc("Email Queue", filters={"reference_name": richiesta.name})
		self.assertIn("giulia.modulo@example.com", [r.recipient for r in posta.recipients])

		# the person: no code, the link opens it
		frappe.set_user("Guest")
		vista = richieste.open_request(LINK)
		self.assertFalse(vista["needs_code"])
		sessione = vista["session"]
		modulo = richieste.get_request_form(LINK, richiesta.name, sessione)
		self.assertFalse(modulo["has_signature"])
		fatto = richieste.sign_request(
			LINK, richiesta.name, json.dumps({"recommend": 9, "comment": "Bene"}), "{}", sessione
		)
		self.assertTrue(fatto["done"])
		# opened again: answered already, the page says thank you (no session to refuse)
		vista = richieste.open_request(LINK)
		self.assertTrue(vista["done"])
		self.assertFalse(vista["needs_code"])
		self.assertNotIn("session", vista)
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_value(richieste.RICHIESTA, richiesta.name, "status"), "Signed")

		# the dashboard: no answer is no score, then one answer, a promoter
		widget = registry.get("satisfaction_nps")
		prima = Context.build(
			add_to_date(nowdate(), days=-400), add_to_date(nowdate(), days=-370), scope=widget.scope
		)
		self.assertIsNone(widget.fn(prima)["value"])
		ctx = Context.build(add_to_date(nowdate(), days=-7), nowdate(), scope=widget.scope)
		numero = widget.fn(ctx)
		self.assertEqual(numero["value"], 100)

	def test_un_modulo_che_non_e_un_questionario_chiede_il_codice(self):
		frappe.set_user("Administrator")
		with mock.patch.object(richieste, "_segreto", return_value=LINK):
			richieste.manda_il_link(
				self.giulia.name,
				[self.privacy],
				richieste.destinatario(self.giulia.name),
				scadenza=add_to_date(nowdate(), days=7),
				dal_centro=True,
			)
		frappe.set_user("Guest")
		vista = richieste.open_request(LINK)
		self.assertTrue(vista["needs_code"])
		self.assertNotIn("session", vista)

	def test_per_sms_il_link_e_nel_messaggio(self):
		self.acconsente()
		frappe.db.set_value("CRM Lead", self.giulia.name, "mobile_no", "+393331234567")
		auto = frappe.get_doc(
			{
				"doctype": "CRM Automation",
				"title": "Questionario per SMS",
				"enabled": 1,
				"trigger_event": "Appointment Completed",
				"steps": json.dumps(
					[
						{
							"type": "send_form",
							"template": self.questionario,
							"via": "sms",
							"message": "Ciao {{ first_name }}: {{ form_link }}",
						}
					]
				),
			}
		).insert()
		with mock.patch("crm.api.sms.send_automation_sms", return_value=True) as manda:
			iscrizione = self.dopo_la_visita(auto)
		self.assertEqual(iscrizione.logs[0].status, "Success", iscrizione.logs[0].detail)
		testo = manda.call_args.kwargs["message"]
		self.assertTrue(testo.startswith("Ciao Giulia: "))
		self.assertIn(f"/modulo/{LINK}", testo)
		self.assertEqual(manda.call_args.kwargs["to"], "+393331234567")
