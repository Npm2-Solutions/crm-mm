# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The WhatsApp templates per number: brought in from Meta for every number,
made on the number chosen, offered only where they can be sent.

A template lives on a WhatsApp Business account. frappe_whatsapp's `fetch` read
the first number only, one page of it, and kept one template of each name for
all the accounts: `hello_world`, which Meta puts in every account, was one."""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from crm.tests import serve_whatsapp

CENTRO, BIS, STUDIO = "Prova Centro", "Prova Centro bis", "Prova Studio"


def meta(nome, id_, lingua="it", stato="APPROVED", corpo="Ciao", pulsanti=None):
	"""A template as `GET /<WABA>/message_templates` describes it."""
	parti = [{"type": "BODY", "text": corpo}]
	if pulsanti:
		parti.append({"type": "BUTTONS", "buttons": pulsanti})
	return {
		"id": id_,
		"name": nome,
		"status": stato,
		"category": "UTILITY",
		"language": lingua,
		"components": parti,
	}


class ModelliPerNumero(IntegrationTestCase):
	def setUp(self):
		serve_whatsapp(self)
		for nome, waba in ((CENTRO, "7001"), (BIS, "7001"), (STUDIO, "7002")):
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
		# what Meta answers for each account, by its WABA
		self.su_meta = {"7001": [], "7002": []}
		self.rotti = set()

	def tearDown(self):
		frappe.db.rollback()

	def graph(self, endpoint, token, params=None, max_pages=50, secret=None):
		from crm.integrations.meta.client import MetaAPIError

		waba = endpoint.split("/")[0]
		if waba in self.rotti:
			raise MetaAPIError("Invalid OAuth access token", code=190)
		yield from self.su_meta.get(waba, [])

	def porta_dentro(self):
		from crm.integrations.whatsapp import templates

		with patch("crm.integrations.meta.client.graph_get_paginated", self.graph):
			return templates.porta_dentro()

	def modelli(self, nome):
		return frappe.get_all(
			"WhatsApp Templates",
			filters={"actual_name": nome},
			fields=["name", "whatsapp_account", "status", "id", "language_code", "template_name"],
			order_by="whatsapp_account asc",
		)

	def test_lo_stesso_nome_su_due_account_sono_due_modelli(self):
		self.su_meta["7001"] = [meta("tmw_saluto", "m-1")]
		self.su_meta["7002"] = [meta("tmw_saluto", "m-2")]
		self.assertEqual(self.porta_dentro(), [])
		trovati = self.modelli("tmw_saluto")
		self.assertEqual({(m.whatsapp_account, m.id) for m in trovati}, {(CENTRO, "m-1"), (STUDIO, "m-2")})
		# the second account's took a name of its own
		self.assertEqual(len({m.name for m in trovati}), 2)

	def test_due_numeri_dello_stesso_account_si_leggono_una_volta(self):
		chiesti = []

		def graph(endpoint, token, params=None, max_pages=50, secret=None):
			chiesti.append(endpoint)
			yield from []

		from crm.integrations.whatsapp import templates

		with patch("crm.integrations.meta.client.graph_get_paginated", graph):
			templates.porta_dentro()
		self.assertEqual(chiesti.count("7001/message_templates"), 1)

	def test_riletti_non_si_raddoppiano_e_tengono_il_loro_nome(self):
		self.su_meta["7001"] = [meta("tmw_promemoria", "m-3", stato="PENDING")]
		self.porta_dentro()
		frappe.db.set_value(
			"WhatsApp Templates", self.modelli("tmw_promemoria")[0].name, "template_name", "Promemoria"
		)
		self.su_meta["7001"] = [meta("tmw_promemoria", "m-3", stato="APPROVED", corpo="Ciao {{1}}")]
		self.porta_dentro()
		[modello] = self.modelli("tmw_promemoria")
		self.assertEqual((modello.status, modello.template_name), ("APPROVED", "Promemoria"))
		doc = frappe.get_doc("WhatsApp Templates", modello.name)
		self.assertEqual(doc.template, "Ciao {{1}}")
		# no example from Meta: the variable gets its number, so it is sent
		self.assertEqual(doc.sample_values, "1")

	def test_i_pulsanti_arrivano_come_righe(self):
		self.su_meta["7002"] = [
			meta(
				"tmw_pulsanti",
				"m-4",
				pulsanti=[
					{"type": "QUICK_REPLY", "text": "Confermo"},
					{"type": "PHONE_NUMBER", "text": "Chiama", "phone_number": "+39021234567"},
				],
			)
		]
		self.porta_dentro()
		doc = frappe.get_doc("WhatsApp Templates", self.modelli("tmw_pulsanti")[0].name)
		self.assertEqual(
			[(riga.button_type, riga.button_label) for riga in doc.buttons],
			[("Quick Reply", "Confermo"), ("Call Phone", "Chiama")],
		)

	def test_quello_che_meta_non_ha_piu_resta_segnato(self):
		self.su_meta["7001"] = [meta("tmw_vecchio", "m-5")]
		self.porta_dentro()
		self.su_meta["7001"] = []
		self.porta_dentro()
		self.assertEqual(self.modelli("tmw_vecchio")[0].status, "DELETED")

	def test_un_numero_che_non_risponde_non_ferma_gli_altri(self):
		self.rotti.add("7001")
		self.su_meta["7002"] = [meta("tmw_altro", "m-6")]
		problemi = self.porta_dentro()
		self.assertEqual([problema["number"] for problema in problemi], [CENTRO])
		self.assertIn("reconnect", problemi[0]["error"].lower())
		self.assertEqual(len(self.modelli("tmw_altro")), 1)

	def test_la_pagina_mostra_i_numeri_e_chi_manda_ogni_modello(self):
		from crm.integrations.whatsapp import templates

		self.su_meta["7001"] = [meta("tmw_vista", "m-7")]
		self.porta_dentro()
		with (
			patch("crm.api.whatsapp.sending_account_name", return_value=STUDIO),
			patch("crm.integrations.whatsapp.templates._check_manager"),
		):
			pagina = templates.get_templates()
		numeri = {numero["name"]: numero for numero in pagina["numbers"]}
		# the ids are Meta's names for things: the page has no use for them
		self.assertNotIn("waba", numeri[CENTRO])
		self.assertEqual(numeri[CENTRO]["shares"], [BIS])
		self.assertTrue(numeri[STUDIO]["sends"])
		self.assertEqual(pagina["numbers"][0]["name"], STUDIO)
		[modello] = [m for m in pagina["templates"] if m.template_name == "tmw_vista"]
		self.assertEqual(sorted(modello["numbers"]), sorted([CENTRO, BIS]))

	def test_si_offre_solo_quello_che_il_numero_che_manda_puo_mandare(self):
		from crm.integrations.whatsapp import templates

		self.su_meta["7001"] = [meta("tmw_del_centro", "m-8")]
		self.su_meta["7002"] = [meta("tmw_dello_studio", "m-9")]
		self.porta_dentro()
		with patch("crm.api.whatsapp.sending_account_name", return_value=BIS):
			nomi = {modello.template_name for modello in templates.modelli_inviabili()}
		self.assertIn("tmw_del_centro", nomi)
		self.assertNotIn("tmw_dello_studio", nomi)

	def test_un_numero_dello_stesso_account_puo_mandarlo(self):
		from crm.api.whatsapp import send_whatsapp_template

		self.su_meta["7001"] = [meta("tmw_condiviso", "m-10")]
		self.porta_dentro()
		nome = self.modelli("tmw_condiviso")[0].name
		with (
			patch("crm.api.whatsapp.sending_account_name", return_value=BIS),
			patch("crm.api.whatsapp.validate_access"),
			patch("crm.api.whatsapp.whatsapp_recipient", return_value="+393330000000"),
			patch("crm.api.whatsapp.insert_and_send", return_value="MSG-1") as mandato,
		):
			send_whatsapp_template("CRM Lead", "LEAD-0001", nome, "+393330000000")
		mandato.assert_called_once()

	def test_un_modello_nuovo_va_sul_numero_scelto_con_i_suoi_pulsanti(self):
		from crm.integrations.whatsapp import templates

		mandati = []

		def a_meta(url, headers=None, data=None):
			mandati.append((url, data))
			return {"id": "m-11", "status": "PENDING"}

		percorso = "frappe_whatsapp.frappe_whatsapp.doctype.whatsapp_templates.whatsapp_templates"
		with (
			patch(f"{percorso}.make_post_request", a_meta),
			patch("crm.integrations.whatsapp.templates._check_manager"),
		):
			fatto = templates.save_template(
				{
					"template_name": "tmw_nuovo",
					"category": "UTILITY",
					"language": "it",
					"template": "Ciao",
					"buttons": [
						{"type": "URL", "text": "Apri", "url": "https://example.com"},
						{"type": "QUICK_REPLY", "text": "Confermo"},
					],
				},
				number=STUDIO,
			)
		doc = frappe.get_doc("WhatsApp Templates", fatto["name"])
		self.assertEqual(doc.whatsapp_account, STUDIO)
		# the quick replies first: Meta refuses them mixed
		self.assertEqual([riga.button_type for riga in doc.buttons], ["Quick Reply", "Visit Website"])
		# and it went to the Studio's account
		self.assertIn("/7002/message_templates", mandati[0][0])

	def test_i_pulsanti_sbagliati_si_dicono_prima_di_mandarlo(self):
		from crm.integrations.whatsapp import templates

		with patch("crm.integrations.whatsapp.templates._check_manager"):
			with self.assertRaises(frappe.ValidationError) as preso:
				templates.save_template(
					{
						"template_name": "tmw_sbagliato",
						"category": "UTILITY",
						"language": "it",
						"template": "Ciao",
						"buttons": [{"type": "QUICK_REPLY", "text": ""}],
					},
					number=STUDIO,
				)
		self.assertIn("Button 1", str(preso.exception))
