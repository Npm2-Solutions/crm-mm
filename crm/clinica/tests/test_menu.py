# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The menu for the nutritionist: targets theirs, nutrients from the tables,
recipes from the assistant.

The dietitian writes Anna's menu with her targets for a day, and asks the
assistant for a lunch. The model reads the meal, the energy, what the dietitian
asks and the library - not Anna. Of its answer the engine keeps the library's
foods and scales their grams to the energy from the tables: a food the library has
not got, or a number of its own, does not come in. Chosen, the recipe goes into the
lunch with its method and the mark; the plan stays a draft. Without Anna's consent,
on somebody else's plan, on a published one or on a training, there are no
recipes.
"""

import json
from unittest import mock

import frappe
import requests

from crm.assistente import modello, regole
from crm.clinica import ASSISTENTE, RICETTE, menu, piani
from crm.clinica import piani_regole as R
from crm.clinica.tests.test_assistente_clinico import risposta
from crm.clinica.tests.test_cartella import DOC1, DOC2
from crm.clinica.tests.test_piani import PianiCase
from crm.moduli import consensi
from crm.permissions import livelli


class MenuCase(PianiCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		frappe.db.set_value(
			piani.CIBO,
			self.pasta.name,
			{"protein_g": 10.9, "carbs_g": 79.1, "fat_g": 1.4, "fibre_g": 2.7},
		)
		self.piselli = frappe.get_doc(
			{
				"doctype": piani.CIBO,
				"food_name": "Piselli surgelati",
				"food_group": "Legumes",
				"kcal": 69,
				"protein_g": 5.5,
				"carbs_g": 9.2,
				"fat_g": 0.4,
				"fibre_g": 6.3,
			}
		).insert(ignore_permissions=True)
		self.olio = frappe.get_doc(
			{
				"doctype": piani.CIBO,
				"food_name": "Olio extravergine",
				"food_group": "Oils and fats",
				"kcal": 899,
				"fat_g": 99.9,
			}
		).insert(ignore_permissions=True)
		piano = frappe.get_single("CRM Plan")
		piano.set(
			"modules",
			[{"module": "clinica", "status": "Active"}, {"module": "assistente", "status": "Active"}],
		)
		piano.save()
		consensi.assicura_tipi()
		self.impostazioni(menus=1)

	def tearDown(self):
		super().tearDown()
		frappe.clear_document_cache(modello.IMPOSTAZIONI, modello.IMPOSTAZIONI)

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
				**valori,
			}
		)
		cfg.save()
		frappe.clear_document_cache(modello.IMPOSTAZIONI, modello.IMPOSTAZIONI)
		livelli.dimentica_cache()

	def consenso(self):
		frappe.set_user("Administrator")
		consensi.registra_risposta(self.anna.name, ASSISTENTE.chiave)

	def proposta(self):
		"""What the model answers: a recipe with a food the library has not got and a
		number of its own, and one of foods nowhere."""
		return json.dumps(
			{
				"recipes": [
					{
						"title": "Pasta e piselli",
						"method": "Cuoci i piselli con l'olio, poi uniscili alla pasta.",
						"kcal": 9999,
						"foods": [
							{"id": self.pasta.name, "grams": 80},
							{"id": self.piselli.name, "grams": 120},
							{"id": self.olio.name, "grams": 10},
							{"id": "burro-inventato", "grams": 20},
						],
					},
					{"title": "Niente", "foods": [{"id": "sale", "grams": 2}]},
				]
			}
		)

	def chiede(self, testo=None, **altro):
		with mock.patch.object(requests, "post", return_value=risposta(testo or self.proposta())) as post:
			fatto = menu.propose_recipes(self.bozza["name"], "pranzo", **altro)
		return fatto, post

	def scrive_bozza(self, **altro):
		self.bozza = self.scrive(dati=self.menu(**altro))
		return self.bozza


class IConti(MenuCase):
	def test_gli_obiettivi_sono_suoi_e_la_nota_arriva_al_paziente(self):
		fatto = self.scrive_bozza(
			targets={"kcal": "1800", "protein_g": 90, "fat_g": "", "fibre_g": -3},
			moments=[{"key": "pranzo", "label": "Pranzo", "day": R.OGNI_GIORNO, "note": " Pasta al dente. "}],
		)
		self.assertEqual(
			fatto["targets"],
			{"kcal": 1800.0, "protein_g": 90.0, "carbs_g": None, "fat_g": None, "fibre_g": None},
		)
		self.assertEqual(fatto["moments"][0]["note"], "Pasta al dente.")
		# the library's values go with each food: the browser counts from them
		[voce] = fatto["items"]
		self.assertEqual(voce["food_detail"]["fibre_g"], 2.7)
		self.assertEqual(R.nutrienti(fatto["items"], {voce["food"]: voce["food_detail"]})["kcal"], 282)

	def test_un_allenamento_non_ha_obiettivi_ne_ricette(self):
		dati = {
			"plan_type": R.ALLENAMENTO,
			"title": "Forza",
			"targets": {"kcal": 1800},
			"moments": [{"key": "s", "label": "Seduta", "day": R.OGNI_GIORNO}],
			"items": [
				{"key": "p", "moment": "s", "kind": R.ESERCIZIO, "exercise": self.ponte.name, "sets": 3}
			],
		}
		fatto = self.scrive(dati=dati)
		self.assertEqual(fatto["targets"]["kcal"], None)
		self.assertEqual(fatto["recipes"], {})
		self.consenso()
		self.come(DOC1)
		with self.assertRaises(frappe.ValidationError):
			menu.propose_recipes(fatto["name"], "s")


class LeRicette(MenuCase):
	def test_senza_consenso_niente_ricette(self):
		fatto = self.scrive_bozza()
		self.assertEqual(fatto["recipes"], {"on": True, "consent": False})
		with self.assertRaises(frappe.ValidationError):
			self.chiede()

	def test_solo_alimenti_della_libreria_scalati_dalle_tabelle(self):
		self.consenso()
		self.scrive_bozza()
		self.assertEqual(piani.get_plan(self.bozza["name"])["recipes"], {"on": True, "consent": True})
		fatto, post = self.chiede(kcal=600, notes="vegetariano")
		[ricetta] = fatto["recipes"]
		self.assertEqual(ricetta["title"], "Pasta e piselli")
		self.assertEqual(
			[v["food"] for v in ricetta["items"]], [self.pasta.name, self.piselli.name, self.olio.name]
		)
		# the proportions are the recipe's, the energy the tables': about 600 kcal
		self.assertLess(abs(ricetta["nutrients"]["kcal"] - 600), 25)
		# the model's own number is not taken
		self.assertNotIn("kcal", ricetta)
		# what the model read: the meal, the energy, the request, the library - not Anna
		inviato = json.dumps(post.call_args.kwargs["json"], ensure_ascii=False)
		self.assertIn("Energy for this meal: about 600 kcal", inviato)
		self.assertIn("vegetariano", inviato)
		self.assertIn(f"{self.piselli.name} | Piselli surgelati | Legumes", inviato)
		self.assertNotIn(self.anna.first_name, inviato)
		evento = frappe.get_doc(modello.EVENTO, fatto["event"])
		self.assertEqual((evento.function, evento.status), (RICETTE.chiave, regole.BOZZA))
		self.assertEqual((evento.reference_doctype, evento.reference_name), (piani.PIANO, self.bozza["name"]))
		self.assertEqual(evento.read_capability, "assistente.registro_clinico")

	def test_scelta_entra_nel_pasto_con_il_segno(self):
		self.consenso()
		self.scrive_bozza()
		fatto, _post = self.chiede()
		[ricetta] = fatto["recipes"]
		# the dietitian changes the grams; a food from elsewhere does not come in
		ricetta["items"][0]["quantity_g"] = 70
		ricetta["items"].append({"food": "burro-inventato", "quantity_g": 20})
		piano = menu.use_recipe(fatto["event"], "pranzo", json.dumps(ricetta))
		self.assertEqual(piano["status"], piani.BOZZA)
		pranzo = [v for v in piano["items"] if v["moment"] == "pranzo"]
		self.assertEqual(
			[(v["food"], v["quantity_g"]) for v in pranzo][1:],
			[(self.pasta.name, 70.0), (self.piselli.name, 120.0), (self.olio.name, 10.0)],
		)
		nota = piano["moments"][0]["note"]
		self.assertIn("Pasta e piselli", nota)
		self.assertIn("Cuoci i piselli", nota)
		self.assertIn("AI draft, checked by", nota)
		evento = frappe.get_doc(modello.EVENTO, fatto["event"])
		self.assertEqual(evento.status, regole.ACCETTATA)
		self.assertIn("Piselli surgelati: 120 g", evento.final)
		self.assertGreater(evento.change_ratio, 0)

	def test_niente_della_libreria_nessuna_ricetta(self):
		self.consenso()
		self.scrive_bozza()
		fatto, _post = self.chiede(
			json.dumps({"recipes": [{"title": "Sale", "foods": [{"id": "sale", "grams": 2}]}]})
		)
		self.assertEqual((fatto["recipes"], fatto["event"]), ([], None))
		self.assertEqual(fatto["error"], "The assistant proposed nothing made of the library's foods")
		self.assertEqual(
			frappe.get_all(modello.EVENTO, filters={"reference_name": self.bozza["name"]}, pluck="status"),
			[regole.SCARTATA],
		)

	def test_solo_sul_proprio_menu_in_bozza(self):
		self.consenso()
		self.scrive_bozza()
		self.come(DOC2)
		with self.assertRaises(frappe.PermissionError):
			self.chiede()
		pubblicato = self.pubblica()
		self.bozza = pubblicato
		with self.assertRaises(frappe.ValidationError):
			self.chiede()

	def test_spenta_nelle_impostazioni(self):
		self.consenso()
		self.impostazioni(menus=0)
		fatto = self.scrive_bozza()
		self.assertEqual(fatto["recipes"], {})
		with self.assertRaises(frappe.ValidationError):
			self.chiede()
