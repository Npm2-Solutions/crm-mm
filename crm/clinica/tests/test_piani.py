# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Plans: the qualification decides which, the author writes and publishes, the
others read them like a visit, and published they are not rewritten.

The dietitian writes Anna's menu, which a physiotherapist can not, while her
exercises at home are the physiotherapist's. A draft is its author's. Published,
the menu goes to her area (an email that says only that there is news), closes the
menu before it, and is read by the colleagues with the dossier. A new version
starts as a draft; closed, a plan stays in the record. The libraries grow from the
editor.
"""

import json
from unittest import mock

import frappe

from crm.clinica import cartella, paziente, piani
from crm.clinica import piani_regole as R
from crm.clinica.area import messaggi
from crm.clinica.tests.test_cartella import DESK, DIRECTOR, DOC1, DOC2, MANAGER, SALES
from crm.clinica.tests.test_dossier import DossierCase


class PianiCase(DossierCase):
	def setUp(self):
		super().setUp()
		self.disciplina(DOC1, "dietista")
		self.disciplina(DOC2, "fisioterapista")
		frappe.set_user("Administrator")
		self.pasta = frappe.get_doc(
			{
				"doctype": piani.CIBO,
				"food_name": "Pasta di semola",
				"food_group": "Cereals and tubers",
				"portion_g": 80,
				"kcal": 353,
			}
		).insert(ignore_permissions=True)
		self.ponte = frappe.get_doc(
			{"doctype": piani.ESERCIZIO, "exercise_name": "Ponte gluteo", "body_part": "Hips"}
		).insert(ignore_permissions=True)

	def menu(self, **altro):
		return {
			"plan_type": R.MENU,
			"title": "Menù di ottobre",
			"moments": [{"key": "pranzo", "label": "Pranzo", "day": R.OGNI_GIORNO}],
			"items": [
				{
					"key": "pasta",
					"moment": "pranzo",
					"kind": R.CIBO,
					"food": self.pasta.name,
					"quantity_g": 80,
					"alternatives": "oppure riso 80 g",
				}
			],
			**altro,
		}

	def scrive(self, user=DOC1, dati=None, name=None):
		self.come(user)
		return piani.save_plan(self.anna.name, json.dumps(dati or self.menu()), name=name)

	def pubblica(self, user=DOC1, dati=None):
		fatto = self.scrive(user, dati)
		with mock.patch.object(messaggi, "_avvisa"):
			return piani.publish_plan(fatto["name"])


class ChiScrive(PianiCase):
	def test_la_dietista_scrive_il_menu_il_fisioterapista_no(self):
		self.come(DOC1)
		self.assertIn(R.MENU, piani.get_plans(self.anna.name)["kinds"])
		self.come(DOC2)
		tipi = piani.get_plans(self.anna.name)["kinds"]
		self.assertNotIn(R.MENU, tipi)
		self.assertIn(R.ESERCIZI, tipi)
		with self.assertRaises(frappe.PermissionError):
			self.scrive(DOC2)
		fatto = self.scrive(DOC1)
		self.assertEqual((fatto["status"], fatto["plan_type"]), (piani.BOZZA, R.MENU))
		[voce] = fatto["items"]
		self.assertEqual((voce["food_name"], voce["kcal"]), ("Pasta di semola", 282))
		# a plan is health data: Anna is a patient now
		frappe.set_user("Administrator")
		self.assertTrue(paziente.e_paziente(self.anna.name))

	def test_esercizi_a_casa_al_fisioterapista(self):
		dati = {
			"plan_type": R.ESERCIZI,
			"title": "Schiena",
			"moments": [{"key": "sera", "label": "La sera", "day": R.OGNI_GIORNO}],
			"items": [
				{"moment": "sera", "kind": R.ESERCIZIO, "exercise": self.ponte.name, "sets": 3, "reps": "12"}
			],
		}
		fatto = self.scrive(DOC2, dati)
		[voce] = fatto["items"]
		self.assertEqual((voce["exercise_name"], voce["sets"], voce["reps"]), ("Ponte gluteo", 3, "12"))
		self.assertTrue(voce["key"])
		with self.assertRaises(frappe.PermissionError):
			self.scrive(DOC1, dati)

	def test_un_piano_tiene_solo_quello_che_e_suo(self):
		dati = self.menu(items=[{"moment": "pranzo", "kind": R.ESERCIZIO, "exercise": self.ponte.name}])
		with self.assertRaises(frappe.ValidationError):
			self.scrive(DOC1, dati)

	def test_chi_non_scrive_piani(self):
		for user in (DESK, SALES):
			self.come(user)
			with self.assertRaises(frappe.PermissionError, msg=user):
				piani.get_plans(self.anna.name)
			with self.assertRaises(frappe.PermissionError, msg=user):
				piani.save_plan(self.anna.name, json.dumps(self.menu()))


class LaBozza(PianiCase):
	def test_la_bozza_e_del_suo_autore(self):
		fatto = self.scrive()
		self.come(DOC2)
		self.assertEqual(piani.get_plans(self.anna.name)["plans"], [])
		with self.assertRaises(frappe.PermissionError):
			piani.get_plan(fatto["name"])
		# the author goes on writing it, and throws it away
		dopo = self.scrive(DOC1, self.menu(title="Menù di novembre"), name=fatto["name"])
		self.assertEqual(dopo["title"], "Menù di novembre")
		# the item keeps its key: its check-ins stay with it
		self.assertEqual(dopo["items"][0]["key"], "pasta")
		piani.delete_draft(fatto["name"])
		self.assertFalse(frappe.db.exists(piani.PIANO, fatto["name"]))

	def test_vuoto_non_si_pubblica(self):
		fatto = self.scrive(dati=self.menu(items=[]))
		with self.assertRaises(frappe.ValidationError):
			piani.publish_plan(fatto["name"])


class Pubblicato(PianiCase):
	def test_va_nell_area_con_un_avviso_senza_contenuto(self):
		fatto = self.scrive()
		with mock.patch.object(messaggi, "_avvisa") as avvisa:
			pubblicato = piani.publish_plan(fatto["name"])
		avvisa.assert_called_once_with(self.anna.name)
		self.assertEqual(pubblicato["status"], piani.PUBBLICATO)
		self.assertTrue(pubblicato["published_on"])

	def test_non_si_riscrive_e_non_si_cancella(self):
		fatto = self.pubblica()
		with self.assertRaises(frappe.ValidationError):
			self.scrive(DOC1, self.menu(title="Altro"), name=fatto["name"])
		frappe.set_user("Administrator")
		doc = frappe.get_doc(piani.PIANO, fatto["name"])
		doc.title = "Altro"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc(piani.PIANO, fatto["name"], ignore_permissions=True)

	def test_la_nuova_versione_prende_il_suo_posto(self):
		primo = self.pubblica()
		self.come(DOC1)
		bozza = piani.new_version(primo["name"])
		self.assertEqual((bozza["status"], bozza["replaces"]), (piani.BOZZA, primo["name"]))
		self.assertEqual([v["key"] for v in bozza["items"]], ["pasta"])
		with self.assertRaises(frappe.ValidationError):
			piani.new_version(primo["name"])
		with mock.patch.object(messaggi, "_avvisa"):
			piani.publish_plan(bozza["name"])
		vecchio = piani.get_plan(primo["name"])
		self.assertEqual((vecchio["status"], vecchio["replaced_by"]), (piani.CHIUSO, bozza["name"]))

	def test_un_menu_alla_volta(self):
		primo = self.pubblica()
		secondo = self.pubblica(dati=self.menu(title="Menù estivo"))
		self.come(DOC1)
		self.assertEqual(piani.get_plan(primo["name"])["status"], piani.CHIUSO)
		self.assertEqual(piani.get_plan(secondo["name"])["status"], piani.PUBBLICATO)

	def test_chiuso_resta_e_lo_chiude_chi_l_ha_scritto(self):
		fatto = self.pubblica()
		self.consenso()
		self.come(DOC2)
		with self.assertRaises(frappe.PermissionError):
			piani.close_plan(fatto["name"])
		self.come(DOC1)
		chiuso = piani.close_plan(fatto["name"])
		self.assertEqual(chiuso["status"], piani.CHIUSO)
		self.assertIn(fatto["name"], [p["name"] for p in piani.get_plans(self.anna.name)["plans"]])


class ChiLegge(PianiCase):
	def test_i_colleghi_leggono_come_una_visita(self):
		fatto = self.pubblica()
		# without the dossier, each practitioner reads their own
		self.come(DOC2)
		self.assertEqual(piani.get_plans(self.anna.name)["plans"], [])
		self.assertNotIn(fatto["name"], frappe.get_list(piani.PIANO, pluck="name"))
		self.consenso()
		self.come(DOC2)
		self.assertEqual([p["name"] for p in piani.get_plans(self.anna.name)["plans"]], [fatto["name"]])
		self.assertIn(fatto["name"], frappe.get_list(piani.PIANO, pluck="name"))
		self.assertFalse(piani.get_plan(fatto["name"])["can_close"])
		# the medical director reads the centre's
		self.come(DIRECTOR)
		self.assertEqual(piani.get_plan(fatto["name"])["title"], "Menù di ottobre")

	def test_l_apertura_va_nel_registro(self):
		fatto = self.pubblica()
		self.come(DOC1)
		piani.get_plan(fatto["name"])
		self.come(MANAGER)
		registro = cartella.access_log(self.anna.name)
		self.assertIn(("plan", DOC1), [(riga["kind"], riga["viewed_by"]) for riga in registro])


class LeLibrerie(PianiCase):
	def test_crescono_dall_editor(self):
		self.come(DOC1)
		nuovo = piani.add_food("Merluzzo", "Fish", portion_g=150, kcal=82)
		self.assertIn(nuovo["name"], [c["name"] for c in piani.search_foods("merl")])
		# the site may have its own fish: the filter keeps to the group
		pesci = piani.search_foods(group="Fish")
		self.assertIn(nuovo["name"], [c["name"] for c in pesci])
		self.assertEqual({c["food_group"] for c in pesci}, {"Fish"})
		with self.assertRaises(frappe.ValidationError):
			piani.add_exercise("Plank", video_url="https://example.com/plank.mp4")
		esercizio = piani.add_exercise("Plank", "Core", video_url="https://www.youtube.com/watch?v=abc123")
		self.assertIn(esercizio["name"], [e["name"] for e in piani.search_exercises("plank")])

	def test_solo_chi_scrive_piani(self):
		self.come(SALES)
		with self.assertRaises(frappe.PermissionError):
			piani.search_foods("pasta")
		with self.assertRaises(frappe.PermissionError):
			piani.add_food("Pane", "Cereals and tubers")


class LaSpesa(PianiCase):
	def test_la_lista_di_una_settimana_da_dare_al_paziente(self):
		fatto = self.pubblica()
		self.come(DOC1)
		lista = piani.shopping_list(fatto["name"], start="2026-10-05", days=7)
		self.assertEqual((lista["from"], lista["until"], lista["days"]), ("2026-10-05", "2026-10-11", 7))
		[pasta] = lista["foods"]
		self.assertEqual(
			(pasta["food_name"], pasta["grams"], pasta["times"], pasta["each"]),
			("Pasta di semola", 560, 7, 80),
		)
		# opening it is reading the plan
		self.come(MANAGER)
		registro = cartella.access_log(self.anna.name)
		self.assertIn(("plan", DOC1), [(riga["kind"], riga["viewed_by"]) for riga in registro])

	def test_solo_i_giorni_del_piano_e_solo_una_dieta(self):
		fatto = self.pubblica(dati=self.menu(starts_on="2026-10-05", ends_on="2026-10-07"))
		self.come(DOC1)
		lista = piani.shopping_list(fatto["name"], days=14)
		# from the plan's first day, and not after its last
		self.assertEqual((lista["from"], lista["days"]), ("2026-10-05", 3))
		self.assertEqual(lista["foods"][0]["grams"], 240)
		esercizi = {
			"plan_type": R.ESERCIZI,
			"title": "Schiena",
			"moments": [{"key": "sera", "label": "Sera", "day": R.OGNI_GIORNO}],
			"items": [{"key": "ponte", "moment": "sera", "kind": R.ESERCIZIO, "exercise": self.ponte.name}],
		}
		scritto = self.scrive(user=DOC2, dati=esercizi)
		with self.assertRaises(frappe.ValidationError):
			piani.shopping_list(scritto["name"])
		# who does not read the plan does not read its list
		self.come(DOC2)
		with self.assertRaises(frappe.PermissionError):
			piani.shopping_list(fatto["name"])
