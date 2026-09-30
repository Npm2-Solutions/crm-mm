# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The plans in the patient area: what to do on a day, one tap an item.

The dietitian publishes Anna's menu; in her area Anna sees today's moments - every
day's and today's weekday's, not tomorrow's - and taps each item: done, partly,
skipped, changed with another tap, taken back. A missed day is made up within two
days, never ahead. An item asked three times a week says how many are left; the
calories show only if the dietitian wants them; an exchange diet lists the foods
to choose from. A draft, a closed plan and somebody else's are not hers to see.
"""

import json
from unittest import mock

import frappe
from frappe.utils import add_days, getdate

from crm.clinica import piani
from crm.clinica import piani_regole as R
from crm.area import api, messaggi
from crm.clinica.area import piani as area_piani
from crm.clinica.tests.test_area import AreaCase
from crm.clinica.tests.test_cartella import DOC1


class AreaPianiCase(AreaCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		frappe.get_doc(
			{
				"doctype": "CRM Service Provider",
				"provider_name": "Dietista dell'area",
				"qualification": "dietista",
				"user": DOC1,
			}
		).insert(ignore_permissions=True)
		self.pasta = frappe.get_doc(
			{
				"doctype": piani.CIBO,
				"food_name": "Pasta di semola",
				"food_group": "Cereals and tubers",
				"portion_g": 80,
				"kcal": 353,
			}
		).insert(ignore_permissions=True)
		oggi = getdate()
		self.oggi = R.GIORNI[oggi.weekday()]
		self.domani = R.GIORNI[(oggi.weekday() + 1) % 7]
		self.invita()

	def menu(self, **altro):
		return {
			"plan_type": R.MENU,
			"title": "Menù di Anna",
			"moments": [
				{"key": "pranzo", "label": "Pranzo", "day": R.OGNI_GIORNO},
				{"key": "oggi", "label": "Solo oggi", "day": self.oggi},
				{"key": "domani", "label": "Solo domani", "day": self.domani},
			],
			"items": [
				{
					"key": "pasta",
					"moment": "pranzo",
					"kind": R.CIBO,
					"food": self.pasta.name,
					"quantity_g": 80,
				},
				{"key": "acqua", "moment": "oggi", "kind": R.ABITUDINE, "text": "Due litri d'acqua"},
				{"key": "passeggiata", "moment": "domani", "kind": R.ABITUDINE, "text": "Camminare"},
				{
					"key": "pesce",
					"moment": "pranzo",
					"kind": R.ABITUDINE,
					"text": "Pesce",
					"times_per_week": 3,
				},
			],
			**altro,
		}

	def pubblica(self, dati=None):
		self.come(DOC1)
		fatto = piani.save_plan(self.anna.name, json.dumps(dati or self.menu()))
		with mock.patch.object(messaggi, "_avvisa"):
			return piani.publish_plan(fatto["name"])["name"]

	def giorno(self, piano, day=None):
		return area_piani.area_plan(self.anna.name, piano, day=day)

	def voci(self, fatto):
		return {voce["key"]: voce for momento in fatto["moments"] for voce in momento["items"]}

	def segna(self, piano, voce, esito, day=None):
		return area_piani.log_item(self.anna.name, piano, voce, esito, day=day)


class IlGiorno(AreaPianiCase):
	def test_i_momenti_di_oggi_non_quelli_di_domani(self):
		piano = self.pubblica()
		self.entra()
		[riga] = area_piani.area_plans(self.anna.name)["plans"]
		self.assertEqual((riga["name"], riga["today"], riga["done_today"]), (piano, 3, 0))
		self.assertEqual(api.get_me()["people"][0]["sections"]["plans"], 1)
		fatto = self.giorno(piano)
		self.assertEqual([m["label"] for m in fatto["moments"]], ["Pranzo", "Solo oggi"])
		self.assertTrue(fatto["can_log"])
		pasta = self.voci(fatto)["pasta"]
		self.assertEqual((pasta["food_name"], pasta["quantity_g"]), ("Pasta di semola", 80))
		# the calories only if the dietitian wants them shown
		self.assertNotIn("kcal", pasta)

	def test_le_calorie_se_l_operatore_le_mostra(self):
		piano = self.pubblica(self.menu(show_calories=1))
		self.entra()
		self.assertEqual(self.voci(self.giorno(piano))["pasta"]["kcal"], 282)

	def test_domani_si_guarda_e_non_si_segna(self):
		piano = self.pubblica()
		self.entra()
		domani = str(add_days(getdate(), 1))
		fatto = self.giorno(piano, domani)
		self.assertIn("passeggiata", self.voci(fatto))
		self.assertFalse(fatto["can_log"])
		with self.assertRaises(frappe.ValidationError):
			self.segna(piano, "passeggiata", R.FATTO, day=domani)

	def test_la_dieta_a_scambi_dice_tra_cosa_scegliere(self):
		dati = {
			"plan_type": R.SCAMBI,
			"title": "Scambi",
			"moments": [{"key": "pranzo", "label": "Pranzo", "day": R.OGNI_GIORNO}],
			"items": [
				{
					"key": "cereali",
					"moment": "pranzo",
					"kind": R.GRUPPO,
					"food_group": "Cereals and tubers",
					"portions": 1,
				}
			],
		}
		piano = self.pubblica(dati)
		self.entra()
		cereali = self.voci(self.giorno(piano))["cereali"]
		# the library's cereals, the site's own ones too, a portion each
		self.assertIn({"food_name": "Pasta di semola", "portion_g": 80}, cereali["choices"])


class LaSpesa(AreaPianiCase):
	def test_cosa_comprare_per_i_prossimi_giorni(self):
		piano = self.pubblica()
		self.entra()
		lista = area_piani.area_shopping_list(self.anna.name, piano, days=14)
		self.assertEqual((lista["from"], lista["days"]), (str(getdate()), 14))
		# the pasta every day; the fish three times a week is a habit, not a food
		self.assertEqual(
			[(r["food_name"], r["grams"], r["times"]) for r in lista["foods"]],
			[("Pasta di semola", 1120, 14)],
		)
		self.assertNotIn("kcal", lista["foods"][0])
		with self.assertRaises(frappe.ValidationError):
			area_piani.area_shopping_list(self.anna.name, piano, start=str(add_days(getdate(), 40)))

	def test_la_dieta_a_scambi_per_porzioni(self):
		dati = {
			"plan_type": R.SCAMBI,
			"title": "Scambi",
			"moments": [{"key": "pranzo", "label": "Pranzo", "day": R.OGNI_GIORNO}],
			"items": [
				{
					"key": "cereali",
					"moment": "pranzo",
					"kind": R.GRUPPO,
					"food_group": "Cereals and tubers",
					"portions": 2,
				}
			],
		}
		piano = self.pubblica(dati)
		self.entra()
		[cereali] = area_piani.area_shopping_list(self.anna.name, piano)["groups"]
		self.assertEqual((cereali["food_group"], cereali["portions"]), ("Cereals and tubers", 14))
		self.assertIn({"food_name": "Pasta di semola", "portion_g": 80}, cereali["choices"])


class IProgrammi(AreaPianiCase):
	def test_anna_finisce_la_tappa_e_si_apre_la_dopo(self):
		from crm.clinica import programmi
		from crm.clinica import programmi_regole as P

		self.come(DOC1)
		fatto = programmi.save_programme(
			self.anna.name,
			json.dumps(
				{
					"title": "Percorso",
					"mode": P.RITMO,
					"stages": [{"key": "a", "title": "Prima"}, {"key": "b", "title": "Seconda"}],
				}
			),
		)
		piano = programmi.stage_plan(fatto["name"], "a", R.MENU)["plan"]
		piani.save_plan(self.anna.name, json.dumps(self.menu()), name=piano)
		with mock.patch.object(messaggi, "_avvisa"):
			programmi.publish_programme(fatto["name"])
		self.entra()
		# the Plans entry of the area counts the programme too
		self.assertEqual(api.get_me()["people"][0]["sections"]["plans"], 2)
		[nell_area] = area_piani.area_programmes(self.anna.name)["programmes"]
		self.assertEqual([t["state"] for t in nell_area["stages"]], [P.APERTA, P.CHIUSA])
		self.assertIn(piano, [p["name"] for p in area_piani.area_plans(self.anna.name)["plans"]])
		fatto = area_piani.finish_stage(self.anna.name, fatto["name"], "a")
		self.assertEqual([t["state"] for t in fatto["programmes"][0]["stages"]], [P.FATTA, P.APERTA])
		self.assertEqual(area_piani.area_plans(self.anna.name)["plans"], [])


class UnTocco(AreaPianiCase):
	def test_si_segna_si_cambia_si_ritira(self):
		piano = self.pubblica()
		self.entra()
		self.segna(piano, "pasta", R.FATTO)
		self.segna(piano, "pasta", R.IN_PARTE)
		frappe.set_user("Administrator")
		[riga] = frappe.get_all(
			piani.REGISTRO, filters={"plan": piano, "item_key": "pasta"}, fields=["outcome", "logged_by"]
		)
		self.assertEqual((riga.outcome, riga.logged_by), (R.IN_PARTE, "anna.referto@example.com"))
		# the dietitian sees it on the plan
		self.come(DOC1)
		self.assertEqual([r.outcome for r in piani.get_plan(piano)["logs"]], [R.IN_PARTE])
		frappe.set_user("anna.referto@example.com")
		self.segna(piano, "pasta", None)
		self.assertEqual(frappe.db.count(piani.REGISTRO, {"plan": piano}), 0)
		self.assertEqual(area_piani.area_plans(self.anna.name)["plans"][0]["done_today"], 0)

	def test_un_giorno_perso_si_recupera_entro_due_giorni(self):
		piano = self.pubblica()
		self.entra()
		self.segna(piano, "pasta", R.SALTATO, day=str(add_days(getdate(), -2)))
		with self.assertRaises(frappe.ValidationError):
			self.segna(piano, "pasta", R.FATTO, day=str(add_days(getdate(), -3)))
		with self.assertRaises(frappe.ValidationError):
			self.segna(piano, "nessuna", R.FATTO)
		with self.assertRaises(frappe.ValidationError):
			self.segna(piano, "pasta", "Excellent")

	def test_quante_volte_restano_questa_settimana(self):
		piano = self.pubblica()
		self.entra()
		self.assertEqual(self.voci(self.giorno(piano))["pesce"]["left_this_week"], 3)
		self.segna(piano, "pesce", R.FATTO)
		self.assertEqual(self.voci(self.giorno(piano))["pesce"]["left_this_week"], 2)
		self.assertIsNone(self.voci(self.giorno(piano))["pasta"]["left_this_week"])


class SoloIlSuo(AreaPianiCase):
	def test_la_bozza_e_il_piano_chiuso_non_si_vedono(self):
		self.come(DOC1)
		bozza = piani.save_plan(self.anna.name, json.dumps(self.menu()))["name"]
		self.entra()
		self.assertEqual(area_piani.area_plans(self.anna.name)["plans"], [])
		with self.assertRaises(frappe.PermissionError):
			self.giorno(bozza)
		piano = self.pubblica()
		self.come(DOC1)
		piani.close_plan(piano)
		frappe.set_user("anna.referto@example.com")
		with self.assertRaises(frappe.PermissionError):
			self.segna(piano, "pasta", R.FATTO)

	def test_un_piano_che_non_e_ancora_cominciato(self):
		piano = self.pubblica(self.menu(starts_on=str(add_days(getdate(), 3))))
		self.entra()
		self.assertEqual(area_piani.area_plans(self.anna.name)["plans"], [])
		with self.assertRaises(frappe.PermissionError):
			self.giorno(piano)

	def test_niente_piani_di_altri(self):
		self.entra()
		frappe.set_user("Administrator")
		altro = frappe.get_doc({"doctype": "CRM Lead", "first_name": "Bruno", "last_name": "Piano"}).insert(
			ignore_permissions=True
		)
		frappe.set_user("anna.referto@example.com")
		with self.assertRaises(frappe.PermissionError):
			area_piani.area_plans(altro.name)
