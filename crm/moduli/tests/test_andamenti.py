# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Where it hurts, and how a questionnaire goes over time.

A body chart's answer is kept cleaned - its points and strokes to the thousandth
- and the signed PDF draws it; a questionnaire asked every few weeks is owed
again once they pass, and its totals follow on the person's page, for whoever
reads the person's forms, health data only for the care team.
"""

import json

import frappe
from frappe.utils import add_days, now_datetime

from crm.moduli import andamenti, compilazioni, modelli, pdf
from crm.moduli.tests.test_compilazioni import DESK, OTHER, SALES, CompilazioniCase, tratto

CORPO = {
	"sections": [
		{
			"id": "s",
			"title": "Dolore",
			"fields": [
				{"id": "dove", "type": "body_chart", "label": "Dove fa male", "required": True},
				{"id": "sign", "type": "signature", "label": "Firma", "required": True},
			],
		}
	]
}

DIARIO = {
	"sections": [
		{
			"id": "s",
			"title": "Come stai",
			"fields": [
				{"id": "a", "type": "scale", "label": "A riposo"},
				{"id": "b", "type": "scale", "label": "Muovendoti"},
				{
					"id": "totale",
					"type": "score",
					"label": "Dolore",
					"sources": ["a", "b"],
					"bands": [
						{"from": 0, "to": 6, "label": "Lieve"},
						{"from": 7, "to": 20, "label": "Forte"},
					],
				},
				{"id": "sign", "type": "signature", "label": "Firma", "required": True},
			],
		}
	]
}


class IlDisegnoSulCorpo(CompilazioniCase):
	def test_si_firma_pulito_e_va_nel_pdf(self):
		modello = self.pubblica(CORPO, "Dove fa male")
		self.come(DESK)
		nome = compilazioni.start_form(self.giulia.name, modello)["name"]
		risposta = {
			"marks": [{"view": "back", "x": 0.51234, "y": 0.4, "label": " lombare ", "intensity": 7}],
			"strokes": [{"view": "front", "points": [[0.1, 0.2], [0.15, 0.25]]}],
		}
		firmato = self.firma(nome, {"dove": risposta})
		self.assertEqual(
			firmato["answers"]["dove"],
			{
				"marks": [{"view": "back", "x": 0.512, "y": 0.4, "label": "lombare", "intensity": 7}],
				"strokes": [{"view": "front", "points": [[0.1, 0.2], [0.15, 0.25]]}],
			},
		)
		frappe.set_user("Administrator")
		doc = frappe.get_doc(compilazioni.MODULO, nome)
		versione = frappe.get_doc(modelli.VERSIONE, doc.template_version)
		pagina = pdf.html(doc, versione)
		self.assertIn("data:image/svg+xml;base64,", pagina)
		self.assertIn("1. ", pagina)
		self.assertIn("lombare · 7/10", pagina)
		self.assertTrue(firmato["pdf_file"])

	def test_un_punto_fuori_dalla_sagoma_non_si_firma(self):
		modello = self.pubblica(CORPO, "Dove fa male")
		self.come(DESK)
		nome = compilazioni.start_form(self.giulia.name, modello)["name"]
		with self.assertRaises(frappe.ValidationError):
			self.firma(nome, {"dove": {"marks": [{"view": "front", "x": 3, "y": 0.5}]}})
		# nothing marked is nothing answered: required
		with self.assertRaises(frappe.ValidationError):
			self.firma(nome, {"dove": {"marks": [], "strokes": []}})

	def test_sul_sito_non_si_chiede(self):
		problemi = modelli.problemi_dell_uso(CORPO, modelli.SITO)
		self.assertIn("body_chart_on_the_site", [p["code"] for p in problemi])


class OgniQualcheSettimana(CompilazioniCase):
	def test_le_settimane_hanno_un_limite(self):
		with self.assertRaises(frappe.ValidationError):
			modelli.save_template(
				title="Diario", schema=json.dumps(DIARIO), validity="Every few weeks", validity_weeks=0
			)
		fatto = modelli.save_template(
			title="Diario", schema=json.dumps(DIARIO), validity="Every few weeks", validity_weeks=6
		)
		self.assertEqual((fatto["validity"], fatto["validity_weeks"]), ("Every few weeks", 6))


class LAndamento(CompilazioniCase):
	def compila(self, modello, a, b, giorni_fa):
		self.come(DESK)
		nome = compilazioni.start_form(self.giulia.name, modello)["name"]
		self.firma(nome, {"a": a, "b": b})
		frappe.db.set_value(
			compilazioni.MODULO,
			nome,
			"signed_on",
			add_days(now_datetime(), -giorni_fa),
			update_modified=False,
		)
		return nome

	def test_i_totali_nel_tempo(self):
		modello = self.pubblica(DIARIO, "Diario del dolore")
		primo = self.compila(modello, 6, 6, 40)
		secondo = self.compila(modello, 2, 1, 5)
		# a form without a score draws nothing
		self.firma(compilazioni.start_form(self.giulia.name, self.privacy)["name"])
		self.come(SALES)
		[serie] = andamenti.get_trends(self.giulia.name)
		self.assertEqual((serie["title"], serie["label"]), ("Diario del dolore", "Dolore"))
		self.assertEqual([p["name"] for p in serie["points"]], [primo, secondo])
		self.assertEqual([(p["value"], p["band"]) for p in serie["points"]], [(12, "Forte"), (3, "Lieve")])

	def test_solo_chi_legge_la_persona(self):
		modello = self.pubblica(DIARIO, "Diario del dolore")
		self.compila(modello, 1, 1, 3)
		self.come(OTHER)
		with self.assertRaises(frappe.PermissionError):
			andamenti.get_trends(self.giulia.name)

	def test_i_dati_sanitari_solo_alla_cura(self):
		modello = self.pubblica(DIARIO, "Diario del dolore")
		nome = self.compila(modello, 1, 1, 3)
		frappe.db.set_value(compilazioni.MODULO, nome, "clinical", 1)
		self.come(DESK)
		self.assertEqual(andamenti.get_trends(self.giulia.name), [])

	def test_si_chiede_di_nuovo_dopo_le_settimane(self):
		from crm.moduli import dovuti

		modello = modelli.save_template(
			title="Diario",
			schema=json.dumps(DIARIO),
			ask_on="First appointment",
			validity="Every few weeks",
			validity_weeks=4,
		)
		modelli.publish_template(modello["name"])
		self.compila(modello["name"], 1, 1, 30)
		motivi = {
			voce["template"]: voce["reason"]
			for voce in dovuti.dovuti([self.giulia.name], {}, clinici=False)[self.giulia.name]
		}
		self.assertEqual(motivi.get(modello["name"]), "due_again")
