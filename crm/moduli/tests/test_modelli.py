# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Form templates on a site: the draft, the versions, who may touch them.

A draft may be half-written; a published version is right, frozen with its hash
and the words of the consents it records, and never changes.
"""

import json

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, nowdate

from crm.moduli import consensi, modelli
from crm.moduli import schema as S
from crm.permissions import livelli, utenti

SEGRETERIA = "moduli.segreteria@example.com"
MANAGER = "moduli.manager@example.com"

PRIVACY = {
	"sections": [
		{
			"id": "privacy",
			"title": "Privacy",
			"fields": [
				{"id": "notice", "type": "paragraph", "text": "How we use your data."},
				{
					"id": "read",
					"type": "consent",
					"label": "I have read the notice",
					"consent_type": "privacy_notice",
					"must_accept": True,
				},
				{"id": "marketing", "type": "consent", "label": "News", "consent_type": "marketing"},
				{"id": "sign", "type": "signature", "label": "Signature", "required": True},
			],
		}
	]
}


def make_user(email: str, livello: str):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"send_welcome_email": 0,
				"roles": [{"role": "Sales User"}],
			}
		).insert(ignore_permissions=True)
	utenti.assegna_livelli(email, [livello])


class ModelliCase(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		consensi.assicura_tipi()
		utenti.sincronizza()
		make_user(SEGRETERIA, "segreteria")
		make_user(MANAGER, "manager")
		livelli.dimentica_cache()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		livelli.dimentica_cache()

	def bozza(self, schema=PRIVACY, **campi):
		return modelli.save_template(title=campi.pop("title", "Privacy"), schema=json.dumps(schema), **campi)


class LaBozza(ModelliCase):
	def test_si_tiene_anche_a_meta(self):
		"""A draft is work in progress: kept with what is still wrong."""
		mezzo = {"sections": [{"id": "s", "fields": [{"id": "a", "type": "choice", "label": "A"}]}]}
		modello = self.bozza(mezzo)
		self.assertEqual([p["code"] for p in modello["problems"]], ["missing_options"])
		self.assertEqual(modello["schema"], mezzo)
		self.assertTrue(modello["unpublished_changes"])
		self.assertEqual(modello["questions"], 1)

	def test_quello_che_non_e_un_modulo_no(self):
		with self.assertRaises(frappe.ValidationError):
			self.bozza({"fields": []})

	def test_un_uso_sconosciuto_no(self):
		with self.assertRaises(frappe.ValidationError):
			self.bozza(use="Recipe")

	def test_i_servizi_solo_se_chiesto_per_servizio(self):
		servizio = frappe.get_doc(
			{
				"doctype": "CRM Service",
				"service_name": "Onde d'urto",
				"duration": 30,
				"staff": [{"user": MANAGER}],
			}
		).insert(ignore_permissions=True)
		modello = self.bozza(ask_on="Services", services=json.dumps([servizio.name]))
		self.assertEqual(modello["services"], [servizio.name])
		modello = modelli.save_template(name=modello["name"], ask_on="By hand")
		self.assertEqual(modello["services"], [])


class LaPubblicazione(ModelliCase):
	def test_una_versione_congela_schema_impronta_e_testi(self):
		modello = self.bozza()
		versione = modelli.publish_template(modello["name"], notes="First")
		self.assertEqual(versione["version"], 1)
		campi = {c["id"]: c for c in S.campi(versione["schema"])}
		testo = frappe.db.get_value("CRM Consent Type", "marketing", "text")
		self.assertEqual(campi["marketing"]["text"], testo)
		self.assertEqual(campi["marketing"]["text_version"], 1)
		self.assertEqual(versione["schema_hash"], S.impronta(versione["schema"]))
		# the template points at it, and has nothing left to publish
		modello = modelli.get_template(modello["name"])
		self.assertEqual(modello["current_version_number"], 1)
		self.assertFalse(modello["unpublished_changes"])

	def test_una_versione_non_cambia(self):
		versione = modelli.publish_template(self.bozza()["name"])
		doc = frappe.get_doc(modelli.VERSIONE, versione["name"])
		doc.notes = "rewritten"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		with self.assertRaises(frappe.LinkExistsError):
			frappe.delete_doc(modelli.VERSIONE, versione["name"], ignore_permissions=True)

	def test_non_si_pubblica_quel_che_non_e_pronto(self):
		mezzo = {"sections": [{"id": "s", "fields": [{"id": "a", "type": "choice", "label": "A"}]}]}
		with self.assertRaises(frappe.ValidationError):
			modelli.publish_template(self.bozza(mezzo)["name"])
		self.assertFalse(frappe.db.exists(modelli.VERSIONE, {"template": self.bozza(mezzo)["name"]}))

	def test_ne_due_volte_la_stessa(self):
		nome = self.bozza()["name"]
		modelli.publish_template(nome)
		with self.assertRaises(frappe.ValidationError):
			modelli.publish_template(nome)
		# a change is a new version
		cambiato = json.loads(json.dumps(PRIVACY))
		cambiato["sections"][0]["fields"][0]["text"] = "How we use your data, and for how long."
		modelli.save_template(name=nome, schema=json.dumps(cambiato))
		self.assertEqual(modelli.publish_template(nome)["version"], 2)
		self.assertEqual([v["version"] for v in modelli.get_template(nome)["versions"]], [2, 1])

	def test_un_consenso_riscritto_e_da_ripubblicare(self):
		"""The version keeps the words it was published with; the template shows
		that a new consent text is waiting to be published."""
		nome = self.bozza()["name"]
		prima = modelli.publish_template(nome)
		consensi.save_consent_type("marketing", text="Newsletter, offers and recalls: yes, please.")
		self.assertTrue(modelli.get_template(nome)["unpublished_changes"])
		self.assertNotEqual(
			{c["id"]: c for c in S.campi(modelli.get_version(prima["name"])["schema"])}["marketing"]["text"],
			"Newsletter, offers and recalls: yes, please.",
		)
		dopo = modelli.publish_template(nome, asked_from=nowdate())
		marketing = {c["id"]: c for c in S.campi(dopo["schema"])}["marketing"]
		self.assertEqual(marketing["text"], "Newsletter, offers and recalls: yes, please.")
		self.assertEqual(marketing["text_version"], 2)
		self.assertEqual(str(dopo["asked_from"]), nowdate())

	def test_un_consenso_spento_o_sconosciuto_non_si_pubblica(self):
		consensi.save_consent_type("marketing", enabled=0)
		with self.assertRaises(frappe.ValidationError):
			modelli.publish_template(self.bozza()["name"])
		ignoto = json.loads(json.dumps(PRIVACY))
		ignoto["sections"][0]["fields"][2]["consent_type"] = "horoscope"
		with self.assertRaises(frappe.ValidationError):
			modelli.publish_template(self.bozza(ignoto)["name"])

	def test_si_richiede_da_oggi_non_dal_passato(self):
		with self.assertRaises(frappe.ValidationError):
			modelli.publish_template(self.bozza()["name"], asked_from=add_days(nowdate(), -1))

	def test_spento_non_si_pubblica(self):
		nome = self.bozza(enabled=0)["name"]
		with self.assertRaises(frappe.ValidationError):
			modelli.publish_template(nome)


class IlDatoClinico(ModelliCase):
	def test_senza_la_clinica_non_si_segna(self):
		salvati = list(modelli._dato_clinico)
		modelli._dato_clinico.clear()
		self.addCleanup(modelli._dato_clinico.extend, salvati)
		self.assertFalse(modelli.get_template(self.bozza()["name"])["clinical_available"])
		with self.assertRaises(frappe.ValidationError):
			self.bozza(clinical=1)

	def test_con_la_clinica_resta_nella_versione(self):
		modelli.registra_dato_clinico(lambda: True)
		self.addCleanup(lambda: modelli._dato_clinico.pop())
		modello = self.bozza(clinical=1, specialty="Nutrition", title="Anamnesis")
		versione = modelli.publish_template(modello["name"])
		self.assertEqual((versione["clinical"], versione["specialty"]), (1, "Nutrition"))


class ChiLiScrive(ModelliCase):
	def test_la_segreteria_no(self):
		nome = self.bozza()["name"]
		frappe.set_user(SEGRETERIA)
		for chiamata in (
			modelli.get_templates,
			lambda: modelli.get_template(nome),
			lambda: modelli.save_template(title="Mio"),
			lambda: modelli.publish_template(nome),
		):
			with self.assertRaises(frappe.PermissionError):
				chiamata()

	def test_il_manager_si(self):
		frappe.set_user(MANAGER)
		modello = self.bozza()
		self.assertIn(modello["name"], [m["name"] for m in modelli.get_templates()])
		self.assertEqual(modelli.publish_template(modello["name"])["version"], 1)


class LaCancellazione(ModelliCase):
	def test_una_bozza_mai_pubblicata_va(self):
		nome = self.bozza()["name"]
		modelli.delete_template(nome)
		self.assertFalse(frappe.db.exists(modelli.MODELLO, nome))

	def test_una_pubblicata_si_spegne(self):
		nome = self.bozza()["name"]
		modelli.publish_template(nome)
		with self.assertRaises(frappe.LinkExistsError):
			modelli.delete_template(nome)

	def test_la_copia_e_una_bozza(self):
		nome = self.bozza()["name"]
		modelli.publish_template(nome)
		copia = modelli.duplicate_template(nome)
		self.assertEqual(copia["title"], "Copy of Privacy")
		self.assertIsNone(copia["current_version"])
		self.assertEqual(copia["schema"], PRIVACY)
