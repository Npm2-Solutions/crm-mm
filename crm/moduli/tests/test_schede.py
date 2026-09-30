# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The operator's sheet, without the clinic: a beauty centre's treatment sheet.

The desk writes Giulia's laser session on the "Treatment sheet": the area, the
fluence, how the skin took it, the operator's signature. It is filled at the desk
and only there: never sent by link, never owed at a booking. A sheet records no
consent - that is the person's to give - so one with a consent is not published.
Completed, it is kept like a signed form, with its PDF, on Giulia's Forms tab.
"""

import json

import frappe

from crm.moduli import compilazioni, dovuti, modelli, richieste
from crm.moduli.tests.test_compilazioni import DESK, SALES, CompilazioniCase, tratto

TRATTAMENTO = {
	"sections": [
		{
			"id": "seduta",
			"title": "Seduta",
			"fields": [
				{"id": "zona", "type": "text", "label": "Zona trattata", "required": True},
				{"id": "fluenza", "type": "number", "label": "Fluenza", "unit": "J/cm²"},
				{"id": "arrossamento", "type": "yesno", "label": "Arrossamento"},
				{
					"id": "firma_operatore",
					"type": "signature",
					"label": "Firma dell'operatore",
					"signer": "operator",
					"required": True,
				},
			],
		}
	]
}


class SchedeCase(CompilazioniCase):
	def setUp(self):
		super().setUp()
		self.scheda = self.pubblica(TRATTAMENTO, "Scheda trattamento laser", use=modelli.SCHEDA)


class LaScheda(SchedeCase):
	def test_la_scrive_l_operatore_al_banco(self):
		self.come(DESK)
		offerti = {t["name"]: t["use"] for t in compilazioni.get_person_forms(self.giulia.name)["templates"]}
		self.assertEqual(offerti[self.scheda], modelli.SCHEDA)
		self.assertEqual(offerti[self.privacy], modelli.FORMA)
		scheda = compilazioni.start_form(self.giulia.name, self.scheda, channel="Link")
		# the operator's, written at the desk whatever was asked
		self.assertEqual((scheda["use"], scheda["channel"]), (modelli.SCHEDA, "At the desk"))
		chiusa = compilazioni.sign_form(
			scheda["name"],
			json.dumps({"zona": "Gambe", "fluenza": "12,5", "arrossamento": False}),
			json.dumps({"firma_operatore": tratto()}),
		)
		self.assertEqual(chiusa["docstatus"], 1)
		self.assertEqual(chiusa["answers"]["fluenza"], 12.5)
		self.assertTrue(chiusa["pdf_file"])
		firma = chiusa["signatures"][0]
		self.assertEqual((firma["field"], firma["signer"]), ("firma_operatore", "operator"))
		self.assertEqual(
			frappe.db.get_value("CRM Signature", {"parent": scheda["name"]}, "signer_user"), DESK
		)
		# on Giulia's Forms tab, among what she signed
		self.assertIn(
			(scheda["name"], modelli.SCHEDA),
			[(f["name"], f["use"]) for f in compilazioni.get_person_forms(self.giulia.name)["forms"]],
		)
		# and nothing in the register of consents
		self.assertFalse(frappe.db.exists("CRM Consent", {"source_name": scheda["name"]}))

	def test_non_si_manda_e_non_si_deve(self):
		self.come(DESK)
		mandabili = [t["name"] for t in richieste.get_send_options(self.giulia.name)["templates"]]
		self.assertIn(self.privacy, mandabili)
		self.assertNotIn(self.scheda, mandabili)
		with self.assertRaises(frappe.ValidationError):
			richieste.hand_over_tablet(self.giulia.name, json.dumps([self.scheda]))
		# nobody owes a sheet: asked on a booking, it is asked by hand
		frappe.set_user("Administrator")
		modello = frappe.get_doc(modelli.MODELLO, self.scheda)
		modello.ask_on = "First appointment"
		modello.send_before = 1
		modello.save()
		self.assertEqual((modello.ask_on, modello.send_before), ("By hand", 0))
		self.assertNotIn(self.scheda, [t["name"] for t in dovuti.modelli_che_si_chiedono()])

	def test_un_consenso_e_della_persona(self):
		frappe.set_user("Administrator")
		con_consenso = {
			"sections": [
				{
					"id": "s",
					"title": "S",
					"fields": [
						{"id": "zona", "type": "text", "label": "Zona"},
						{
							"id": "novita",
							"type": "consent",
							"label": "Novità",
							"consent_type": "marketing",
						},
					],
				}
			]
		}
		modello = modelli.save_template(
			title="Scheda con consenso", schema=json.dumps(con_consenso), use=modelli.SCHEDA
		)
		self.assertIn("consent_on_a_sheet", [p["code"] for p in modello["problems"]])
		with self.assertRaises(frappe.ValidationError):
			modelli.publish_template(modello["name"])
		# the same questions, as a form the person fills, are fine
		forma = modelli.save_template(title="Modulo con consenso", schema=json.dumps(con_consenso))
		self.assertNotIn("consent_on_a_sheet", [p["code"] for p in forma["problems"]])

	def test_lo_legge_chi_vede_la_persona(self):
		self.come(DESK)
		scheda = compilazioni.start_form(self.giulia.name, self.scheda)
		# sales works on Giulia: it reads her forms, sheets included
		self.come(SALES)
		self.assertIn(
			scheda["name"], [f["name"] for f in compilazioni.get_person_forms(self.giulia.name)["forms"]]
		)

	def test_gli_usi_del_crm(self):
		usi = {uso.chiave: uso for uso in modelli.usi()}
		self.assertTrue(usi[modelli.FORMA].della_persona)
		self.assertFalse(usi[modelli.SCHEDA].della_persona)
		# the person fills a form, at the desk or on the website; the operator a sheet
		self.assertEqual(modelli.usi_della_persona(), [modelli.FORMA, modelli.SITO])
		# an old template without a use is a form
		self.assertEqual(modelli.uso(None).chiave, modelli.FORMA)
