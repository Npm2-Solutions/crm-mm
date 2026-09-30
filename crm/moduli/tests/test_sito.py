# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The forms on the centre's website (`crm.moduli.sito`), without the clinic.

A beauty centre puts "Richiedi informazioni" on its site: name, email, mobile,
what the visitor is interested in, the newsletter. Whoever sends it is found by
their email or mobile - Giulia, who came last year, is Giulia again - or made; the
answers are kept as a form of theirs with its PDF, the newsletter goes into the
register as given on the website, their deal opens and the automations hear it. A
robot that fills the box nobody sees leaves nothing, a draft is only tried, and
marketing builds these forms without touching the centre's own.
"""

import json
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.api import site_render
from crm.moduli import consensi, modelli, sito
from crm.permissions import livelli, utenti
from crm.permissions.test_org_hierarchy import make_user

MARKETING = "forms.marketing@example.com"
DESK = "forms.site.desk@example.com"

RICHIESTA = {
	"sections": [
		{
			"id": "tu",
			"title": "I tuoi dati",
			"fields": [
				{
					"id": "nome",
					"type": "text",
					"label": "Nome e cognome",
					"person": "full_name",
					"required": True,
				},
				{"id": "email", "type": "text", "label": "Email", "person": "email", "required": True},
				{"id": "cellulare", "type": "text", "label": "Cellulare", "person": "mobile_no"},
				{"id": "azienda", "type": "text", "label": "Azienda", "person": "organization"},
				{
					"id": "interesse",
					"type": "choice",
					"label": "Cosa ti interessa",
					"options": [{"label": "Laser"}, {"label": "Massaggi"}],
					"required": True,
				},
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

RISPOSTE = {
	"nome": "Giulia Sito",
	"email": "Giulia.Sito@Example.com",
	"cellulare": "",
	"azienda": "Studio Giulia",
	"interesse": "Laser",
	"novita": True,
}


#: An old form's rows, as the framework's Web Form kept them.
VECCHI_CAMPI = [
	{"fieldname": "sb1", "fieldtype": "Section Break", "label": "I tuoi dati"},
	{"fieldname": "first_name", "fieldtype": "Data", "label": "Nome", "reqd": 1},
	{"fieldname": "cb1", "fieldtype": "Column Break"},
	{"fieldname": "last_name", "fieldtype": "Data", "label": "Cognome"},
	{"fieldname": "email", "fieldtype": "Data", "options": "Email", "label": "Email", "reqd": 1},
	{"fieldname": "phone", "fieldtype": "Data", "options": "Phone", "label": "Telefono"},
	{"fieldname": "sb2", "fieldtype": "Section Break", "label": "La richiesta"},
	{
		"fieldname": "no_of_employees",
		"fieldtype": "Select",
		"options": "1-10\n11-50\n\n11-50",
		"label": "Dipendenti",
	},
	{"fieldname": "industry", "fieldtype": "Link", "options": "CRM Industry", "label": "Settore"},
	{"fieldname": "has_site", "fieldtype": "Check", "label": "Hai un sito?"},
	{
		"fieldname": "note",
		"fieldtype": "Small Text",
		"label": "Il sito",
		"depends_on": "eval:doc.has_site",
	},
	{
		"fieldname": "job_title",
		"fieldtype": "Data",
		"label": "Ruolo",
		"depends_on": "eval:doc.no_of_employees == '11-50'",
		"mandatory_depends_on": "eval:doc.later",
	},
	{
		"fieldname": "annual_revenue",
		"fieldtype": "Int",
		"label": "Fatturato",
		"depends_on": "eval:doc.x > 3",
	},
	{"fieldname": "1st", "fieldtype": "Datetime", "label": "Quando"},
]


class SitoCase(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		consensi.assicura_tipi()
		utenti.sincronizza()
		for user, livello in ((MARKETING, "marketing"), (DESK, "segreteria")):
			make_user(user)
			utenti.assegna_livelli(user, [livello])
		livelli.dimentica_cache()
		self.modello = self.pubblica(RICHIESTA, "Richiedi informazioni")
		self.route = frappe.db.get_value(modelli.MODELLO, self.modello, "route")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		livelli.dimentica_cache()

	@staticmethod
	def pubblica(schema, titolo, **campi):
		modello = modelli.save_template(
			title=titolo, use=modelli.SITO, schema=json.dumps(schema), enabled=1, **campi
		)
		modelli.publish_template(modello["name"])
		return modello["name"]

	def come(self, user):
		frappe.set_user(user)
		livelli.dimentica_cache()

	def manda(self, risposte=None, **altro):
		self.come("Guest")
		try:
			return sito.submit_site_form(
				self.route, json.dumps(RISPOSTE if risposte is None else risposte), **altro
			)
		finally:
			self.come("Administrator")


class IlModuloDelSito(SitoCase):
	def test_chi_lo_manda_diventa_una_persona_col_suo_modulo(self):
		with patch("crm.automation.engine.process_event") as sentito:
			self.assertEqual(self.manda(), {"sent": True})
		persona = frappe.get_doc("CRM Lead", {"email": "giulia.sito@example.com"})
		self.assertEqual((persona.first_name, persona.last_name), ("Giulia", "Sito"))
		self.assertEqual((persona.source, persona.organization), (sito.FONTE, "Studio Giulia"))

		modulo = frappe.get_doc("CRM Form", {"lead": persona.name})
		self.assertEqual((modulo.channel, modulo.docstatus), (sito.CANALE, 1))
		self.assertEqual(json.loads(modulo.answers)["interesse"], "Laser")
		self.assertTrue(modulo.answers_hash and modulo.signed_on)
		self.assertFalse(modulo.signatures)
		# its PDF, made after the answer went back (at once in the tests)
		self.assertTrue(frappe.db.get_value("CRM Form", modulo.name, "pdf_file"))
		# the newsletter, given on the website
		risposta = consensi.risposta_attuale(persona.name, "marketing")
		self.assertEqual((risposta["status"], risposta["channel"]), ("Given", "Web form"))
		# an inquiry opens a deal
		self.assertTrue(frappe.db.exists("CRM Deal", {"lead": persona.name}))
		# and the automations hear a form was filled
		evento, doc, dati = sentito.call_args.args
		self.assertEqual(
			(evento, doc.name, dati["form_template"]), ("form_submitted", persona.name, self.modello)
		)

	def test_chi_torna_e_la_stessa_persona(self):
		giulia = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Giulia",
				"last_name": "Sito",
				"email": "giulia.sito@example.com",
				"job_title": "Estetista",
			}
		).insert(ignore_permissions=True)
		self.manda()
		self.manda({**RISPOSTE, "azienda": "Un'altra azienda"})
		self.assertEqual(frappe.db.count("CRM Lead", {"email": "giulia.sito@example.com"}), 1)
		self.assertEqual(frappe.db.count("CRM Form", {"lead": giulia.name, "channel": sito.CANALE}), 2)
		# what she left fills what the centre did not know, and never rewrites it
		giulia.reload()
		self.assertEqual((giulia.organization, giulia.job_title), ("Studio Giulia", "Estetista"))
		# one conversation, one deal
		self.assertEqual(frappe.db.count("CRM Deal", {"lead": giulia.name}), 1)

	def test_un_robot_non_lascia_niente(self):
		prima = frappe.db.count("CRM Lead")
		self.assertEqual(self.manda(website="https://spam.example.com"), {"sent": True})
		self.assertEqual(frappe.db.count("CRM Lead"), prima)
		self.assertFalse(frappe.db.exists("CRM Lead", {"email": "giulia.sito@example.com"}))

	def test_senza_un_recapito_non_parte(self):
		with self.assertRaises(frappe.ValidationError):
			self.manda({**RISPOSTE, "email": "non-una-email"})
		# the email optional and nothing left: nobody could answer
		facoltativa = json.loads(json.dumps(RICHIESTA))
		facoltativa["sections"][0]["fields"][1].pop("required")
		self.route = frappe.db.get_value(modelli.MODELLO, self.pubblica(facoltativa, "Contatti"), "route")
		with self.assertRaises(frappe.ValidationError):
			self.manda({**RISPOSTE, "email": ""})
		self.manda({**RISPOSTE, "email": "", "cellulare": "+39 333 111 2222"})
		self.assertTrue(frappe.db.exists("CRM Lead", {"mobile_no": "+393331112222"}))

	def test_mancano_risposte(self):
		with self.assertRaises(frappe.ValidationError):
			self.manda({**RISPOSTE, "interesse": None})
		self.assertFalse(frappe.db.exists("CRM Lead", {"email": "giulia.sito@example.com"}))


class LaBozza(SitoCase):
	def test_una_bozza_non_e_sul_sito_ma_si_prova(self):
		bozza = modelli.save_template(
			title="Prova", use=modelli.SITO, schema=json.dumps(RICHIESTA), enabled=1
		)
		self.route = bozza["route"]
		with self.assertRaises(frappe.DoesNotExistError):
			self.manda()
		self.assertIsNone(sito.modello_del_sito(self.route))
		# whoever builds the website's forms tries it on its page: checked, and not kept
		self.come(MARKETING)
		self.assertEqual(sito.try_site_form(self.route, json.dumps(RISPOSTE)), {"tried": True})
		self.assertFalse(frappe.db.exists("CRM Lead", {"email": "giulia.sito@example.com"}))
		self.come("Guest")
		with self.assertRaises(frappe.PermissionError):
			sito.try_site_form(self.route, json.dumps(RISPOSTE))

	def test_nella_pagina_del_sito(self):
		html = site_render.crm_form_html(self.route)
		self.assertIn("Richiedi informazioni", html)
		self.assertIn("moduli_campi.js", html)
		self.assertIn('"interesse"', html)
		bozza = modelli.save_template(
			title="Bozza", use=modelli.SITO, schema=json.dumps(RICHIESTA), enabled=1
		)
		self.assertIn("not published", site_render.crm_form_html(bozza["route"]))
		self.assertIn("Pick a form", site_render.crm_form_html(""))


class LUso(SitoCase):
	def test_cosa_un_modulo_del_sito_non_fa(self):
		campi = RICHIESTA["sections"][0]["fields"]
		schema = {
			"sections": [
				{
					"id": "s",
					"fields": [
						{"id": "firma", "type": "signature", "label": "Firma"},
						{"id": "file", "type": "attachment", "label": "Foto"},
						{"id": "eta", "type": "number", "label": "Età", "person": "first_name"},
						{"id": "nome", "type": "text", "label": "Nome", "person": "full_name"},
						{"id": "altro", "type": "text", "label": "Nome ancora", "person": "full_name"},
						{"id": "codice", "type": "text", "label": "Codice", "person": "tax_id"},
					],
				}
			]
		}
		codici = {problema["code"] for problema in modelli.problemi_dell_uso(schema, modelli.SITO)}
		self.assertEqual(
			codici,
			{
				"signature_on_the_site",
				"file_on_the_site",
				"person_field_not_text",
				"person_field_twice",
				"person_field_unknown",
				"person_without_contact",
			},
		)
		self.assertEqual(modelli.problemi_dell_uso(RICHIESTA, modelli.SITO), [])
		# the same questions on a form of the desk: nothing to say about the person
		self.assertEqual(
			modelli.problemi_dell_uso({"sections": [{"id": "s", "fields": campi}]}, modelli.FORMA), []
		)

	def test_non_e_un_dato_sanitario_e_non_si_chiede(self):
		modello = frappe.get_doc(modelli.MODELLO, self.modello)
		self.assertEqual((modello.ask_on, modello.send_before), ("By hand", 0))
		modello.clinical = 1
		with self.assertRaises(frappe.ValidationError):
			modello.save()

	def test_l_indirizzo(self):
		self.assertEqual(self.route, "richiedi-informazioni")
		copia = modelli.duplicate_template(self.modello)
		self.assertEqual(copia["route"], "richiedi-informazioni-copy")
		self.assertEqual(modelli.duplicate_template(self.modello)["route"], "richiedi-informazioni-copy-2")
		modello = frappe.get_doc(modelli.MODELLO, copia["name"])
		for sbagliato in ("richiedi-informazioni", "Con spazi e à", "x"):
			modello.route = sbagliato
			with self.assertRaises(frappe.ValidationError):
				modello.save()
		modello.reload()
		modello.success_url = "javascript:alert(1)"
		with self.assertRaises(frappe.ValidationError):
			modello.save()
		# the old forms' addresses still find it
		self.assertEqual(sito.indirizzo("/Richiedi_Informazioni/"), "richiedi-informazioni")
		self.assertEqual(sito.modello_del_sito("Richiedi_Informazioni").name, self.modello)


class ChiLiCostruisce(SitoCase):
	def test_il_marketing_costruisce_solo_quelli_del_sito(self):
		forma = modelli.save_template(title="Privacy", schema=json.dumps({"sections": []}))
		self.come(MARKETING)
		visti = {riga["name"]: riga["use"] for riga in modelli.get_templates()}
		self.assertEqual(visti.get(self.modello), modelli.SITO)
		self.assertNotIn(forma["name"], visti)
		self.assertEqual([uso["value"] for uso in modelli.get_template(self.modello)["uses"]], [modelli.SITO])
		with self.assertRaises(frappe.PermissionError):
			modelli.get_template(forma["name"])
		with self.assertRaises(frappe.PermissionError):
			modelli.save_template(title="Consensi", use=modelli.FORMA, schema=json.dumps({"sections": []}))
		nuovo = modelli.save_template(title="Newsletter", use=modelli.SITO, schema=json.dumps(RICHIESTA))
		self.assertEqual(nuovo["route"], "newsletter")
		# a form of the website does not become one of the centre's
		with self.assertRaises(frappe.PermissionError):
			modelli.save_template(name=nuovo["name"], use=modelli.FORMA)

	def test_la_segreteria_non_li_tocca(self):
		self.come(DESK)
		with self.assertRaises(frappe.PermissionError):
			modelli.get_template(self.modello)
		with self.assertRaises(frappe.PermissionError):
			modelli.save_template(title="Contatti", use=modelli.SITO, schema=json.dumps(RICHIESTA))


class IVecchiModuli(IntegrationTestCase):
	"""The forms built on the framework's Web Form become templates of the website."""

	def tearDown(self):
		frappe.db.rollback()

	def test_i_campi_diventano_domande(self):
		from crm.patches.v1_0.web_forms_are_templates import schema_da_campi

		schema, avvisi = schema_da_campi(VECCHI_CAMPI, lambda doctype: ["Beauty", "Sport"])
		sezioni = schema["sections"]
		self.assertEqual([s["title"] for s in sezioni], ["I tuoi dati", "La richiesta"])
		domande = {d["id"]: d for s in sezioni for d in s["fields"]}
		self.assertEqual(
			{chiave: d.get("person") for chiave, d in domande.items() if d.get("person")},
			{
				"first_name": "first_name",
				"last_name": "last_name",
				"email": "email",
				"phone": "mobile_no",
				"job_title": "job_title",
			},
		)
		self.assertTrue(domande["email"]["required"])
		self.assertEqual([o["label"] for o in domande["no_of_employees"]["options"]], ["1-10", "11-50"])
		self.assertEqual([o["label"] for o in domande["industry"]["options"]], ["Beauty", "Sport"])
		self.assertEqual(domande["has_site"]["type"], "yesno")
		self.assertEqual(
			domande["note"]["show_if"], [[{"field": "has_site", "operator": "equals", "value": "1"}]]
		)
		self.assertEqual(
			domande["job_title"]["show_if"],
			[[{"field": "no_of_employees", "operator": "equals", "value": "11-50"}]],
		)
		self.assertEqual(
			(domande["annual_revenue"]["type"], domande["annual_revenue"]["decimals"]), ("number", 0)
		)
		self.assertNotIn("show_if", domande["annual_revenue"])
		self.assertEqual(domande["q_1st"]["type"], "date")
		self.assertEqual(len(avvisi), 3)
		# what the engine accepts
		self.assertEqual(modelli.problemi(schema, per_pubblicare=True), [])

	def test_un_vecchio_modulo_pubblicato_resta_sul_sito(self):
		from crm.patches.v1_0.web_forms_are_templates import converti

		frappe.set_user("Administrator")
		vecchio = frappe._dict(
			name="contatti",
			title="Contatti",
			route="Contatti_Vecchi_Moduli",
			introduction_text="Scrivici",
			button_label="Invia",
			success_url="javascript:alert(1)",
			crm_published=1,
		)
		nome, avvisi = converti(vecchio, VECCHI_CAMPI)
		modello = frappe.get_doc(modelli.MODELLO, nome)
		self.assertEqual(
			(modello.use, modello.route, modello.description),
			(modelli.SITO, "contatti-vecchi-moduli", "Scrivici"),
		)
		self.assertTrue(modello.current_version)
		self.assertEqual(modello.success_url, "")
		self.assertTrue(any("not a page address" in avviso for avviso in avvisi))
		self.assertEqual(sito.modello_del_sito("Contatti_Vecchi_Moduli").name, nome)

		# a form nobody could be answered from stays a draft, and says why
		nome, avvisi = converti(
			frappe._dict(name="solo", title="Solo nome", route="solo", crm_published=1), VECCHI_CAMPI[1:2]
		)
		self.assertFalse(frappe.db.get_value(modelli.MODELLO, nome, "current_version"))
		self.assertTrue(any("left as a draft" in avviso for avviso in avvisi))

	def test_gli_elenchi_si_richiudono(self):
		from crm.patches.v1_0.web_forms_are_templates import revoca_gli_elenchi

		riga = frappe.get_doc(
			{
				"doctype": "Custom DocPerm",
				"parent": "CRM Industry",
				"parenttype": "DocType",
				"parentfield": "permissions",
				"role": "Guest",
				"permlevel": 0,
				"select": 1,
				"read": 0,
			}
		).insert(ignore_permissions=True)
		revoca_gli_elenchi()
		self.assertFalse(frappe.db.exists("Custom DocPerm", riga.name))
