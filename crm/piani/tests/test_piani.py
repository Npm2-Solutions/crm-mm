# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Plans and programmes on a site without the clinic: a gym's trainer writes them,
the person follows them in their area.

The trainer, with no healthcare qualification, writes Anna's training - and could
not write a diet even with a dietitian's, since the clinic is off. A draft is its
author's; published, the desk reads it (it sees Anna and reads plans), sales do
not; nothing of it is health data: no access log, and Anna is no patient. In her
area she sees today's session, the exercise with its sets, and ticks it done. A
programme at her own pace opens its next stage when she says the first is
finished, with the plan of that stage. The exercises' library is the manager's.
"""

import json
from unittest import mock

import frappe
from frappe.utils import getdate

from crm.area import messaggi
from crm.area.tests.test_area import DESK, MANAGER, OPERATORE, SALES, AreaCase
from crm.piani import api as piani
from crm.piani import area as area_piani
from crm.piani import librerie, programmi
from crm.piani import programmi_regole as P
from crm.piani import regole as r


class PianiCase(AreaCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		self.squat = frappe.get_doc(
			{"doctype": piani.ESERCIZIO, "exercise_name": "Squat", "body_part": "Legs"}
		).insert(ignore_permissions=True)

	def allenamento(self, **altro):
		return {
			"plan_type": r.ALLENAMENTO,
			"title": "Forza di ottobre",
			"moments": [{"key": "seduta", "label": "Seduta A", "day": r.OGNI_GIORNO}],
			"items": [
				{
					"key": "squat",
					"moment": "seduta",
					"kind": r.ESERCIZIO,
					"exercise": self.squat.name,
					"sets": 3,
					"reps": "10",
				},
				{"key": "acqua", "moment": "seduta", "kind": r.ABITUDINE, "text": "Due litri d'acqua"},
			],
			**altro,
		}

	def scrive(self, dati=None, name=None, user=OPERATORE):
		self.come(user)
		return piani.save_plan(self.anna.name, json.dumps(dati or self.allenamento()), name=name)

	def pubblica(self, dati=None):
		fatto = self.scrive(dati)
		with mock.patch.object(messaggi, "_avvisa"):
			return piani.publish_plan(fatto["name"])

	def tipi(self, user):
		self.come(user)
		return [tipo["key"] for tipo in piani.get_plans(self.anna.name)["kinds"]]


class ChiScrive(PianiCase):
	def test_il_trainer_scrive_allenamenti_e_abitudini(self):
		self.assertEqual(self.tipi(OPERATORE), [r.ALLENAMENTO, r.ABITUDINI])
		# the desk reads plans but writes none, sales not even read them
		self.assertEqual(self.tipi(DESK), [])
		self.come(SALES)
		with self.assertRaises(frappe.PermissionError):
			piani.get_plans(self.anna.name)

	def test_senza_la_clinica_nessuna_dieta_anche_con_la_qualifica(self):
		frappe.set_user("Administrator")
		frappe.get_doc(
			{
				"doctype": "CRM Service Provider",
				"provider_name": "Provider trainer",
				"qualification": "dietista",
				"user": OPERATORE,
			}
		).insert(ignore_permissions=True)
		self.assertEqual(self.tipi(OPERATORE), [r.ALLENAMENTO, r.ABITUDINI])
		with self.assertRaises(frappe.PermissionError):
			self.scrive({**self.allenamento(), "plan_type": "Meal plan"})

	def test_quello_che_un_tipo_offre(self):
		self.come(OPERATORE)
		[allenamento, abitudini] = piani.get_plans(self.anna.name)["kinds"]
		self.assertEqual(allenamento["items"], [r.ESERCIZIO, r.ABITUDINE])
		self.assertEqual(abitudini["items"], [r.ABITUDINE])
		self.assertFalse(allenamento["clinical"])
		# each says what it is, for whoever chooses which plan to write
		self.assertTrue(allenamento["description"] and abitudini["description"])

	def test_dice_se_la_persona_lo_vedra(self):
		"""A published plan reaches the person through their area: until somebody
		enters it, the page says so."""
		self.come(OPERATORE)
		self.assertEqual(piani.get_plans(self.anna.name)["area"], {"on": True, "open": False})
		self.invita()
		self.come(OPERATORE)
		self.assertEqual(piani.get_plans(self.anna.name)["area"], {"on": True, "open": True})


class UnAllenamento(PianiCase):
	def test_la_bozza_e_del_suo_autore(self):
		fatto = self.scrive()
		self.assertEqual((fatto["status"], fatto["clinical"]), (piani.BOZZA, 0))
		self.assertEqual(fatto["item_kinds"], [r.ESERCIZIO, r.ABITUDINE])
		[esercizio, abitudine] = fatto["items"]
		self.assertEqual((esercizio["exercise_name"], esercizio["sets"]), ("Squat", 3))
		self.assertEqual(abitudine["text"], "Due litri d'acqua")
		self.come(DESK)
		with self.assertRaises(frappe.PermissionError):
			piani.get_plan(fatto["name"])
		self.assertEqual(piani.get_plans(self.anna.name)["plans"], [])

	def test_pubblicato_lo_legge_chi_legge_i_piani_e_non_e_un_dato_sanitario(self):
		fatto = self.pubblica()
		self.assertEqual(fatto["status"], piani.PUBBLICATO)
		self.come(DESK)
		self.assertEqual(piani.get_plan(fatto["name"])["title"], "Forza di ottobre")
		self.assertEqual([p["name"] for p in piani.get_plans(self.anna.name)["plans"]], [fatto["name"]])
		self.come(SALES)
		with self.assertRaises(frappe.PermissionError):
			piani.get_plan(fatto["name"])
		# the list follows the same rule
		self.assertEqual(frappe.get_list(piani.PIANO, pluck="name"), [])
		self.come(DESK)
		self.assertEqual(frappe.get_list(piani.PIANO, pluck="name"), [fatto["name"]])
		# not health data: no access log, and without the clinic nobody is a patient
		frappe.set_user("Administrator")
		self.assertFalse(frappe.db.exists("View Log", {"reference_name": fatto["name"]}))

	def test_una_nuova_versione_e_la_chiusura(self):
		vecchio = self.pubblica()
		self.come(OPERATORE)
		nuovo = piani.new_version(vecchio["name"])
		self.assertEqual((nuovo["status"], nuovo["replaces"]), (piani.BOZZA, vecchio["name"]))
		with mock.patch.object(messaggi, "_avvisa"):
			piani.publish_plan(nuovo["name"])
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_value(piani.PIANO, vecchio["name"], "status"), piani.CHIUSO)
		self.come(OPERATORE)
		chiuso = piani.close_plan(nuovo["name"])
		self.assertEqual(chiuso["status"], piani.CHIUSO)

	def test_un_esercizio_che_non_c_e_piu(self):
		frappe.set_user("Administrator")
		frappe.db.set_value(piani.ESERCIZIO, self.squat.name, "enabled", 0)
		with self.assertRaises(frappe.ValidationError):
			self.scrive()


class NellArea(PianiCase):
	def test_anna_segna_la_seduta_fatta(self):
		fatto = self.pubblica()
		self.invita()
		self.entra()
		[piano] = area_piani.area_plans(self.anna.name)["plans"]
		self.assertEqual((piano["name"], piano["today"], piano["done_today"]), (fatto["name"], 2, 0))
		giorno = area_piani.area_plan(self.anna.name, fatto["name"])
		[momento] = giorno["moments"]
		esercizio = next(v for v in momento["items"] if v["kind"] == r.ESERCIZIO)
		self.assertEqual(
			(esercizio["exercise_name"], esercizio["sets"], esercizio["reps"]), ("Squat", 3, "10")
		)
		abitudine = next(v for v in momento["items"] if v["kind"] == r.ABITUDINE)
		self.assertEqual(abitudine["text"], "Due litri d'acqua")
		area_piani.log_item(self.anna.name, fatto["name"], "squat", r.FATTO)
		[piano] = area_piani.area_plans(self.anna.name)["plans"]
		self.assertEqual(piano["done_today"], 1)
		# the author reads how it went
		self.come(OPERATORE)
		self.assertEqual(piani.get_plans(self.anna.name)["plans"][0]["summary"][r.FATTO], 1)

	def test_la_sezione_piani_c_e_solo_con_un_piano(self):
		self.assertEqual(area_piani.piani_in_corso(self.anna.name), 0)
		self.pubblica()
		self.assertEqual(area_piani.piani_in_corso(self.anna.name), 1)


class UnProgramma(PianiCase):
	def test_al_suo_ritmo_la_tappa_dopo_si_apre_quando_anna_dice_finita(self):
		self.come(OPERATORE)
		dati = {
			"mode": P.RITMO,
			"title": "Tre settimane",
			"stages": [
				{"key": "uno", "title": "Si comincia"},
				{"key": "due", "title": "Si aumenta"},
			],
		}
		programma = programmi.save_programme(self.anna.name, json.dumps(dati))
		fatto = programmi.stage_plan(programma["name"], "due", r.ALLENAMENTO)
		piani.save_plan(self.anna.name, json.dumps(self.allenamento()), name=fatto["plan"])
		with mock.patch.object(messaggi, "_avvisa"):
			programma = programmi.publish_programme(programma["name"])
		self.assertEqual(programma["status"], programmi.PUBBLICATO)
		self.assertEqual(programma["clinical"], 0)
		self.invita()
		self.entra()
		[visto] = area_piani.area_programmes(self.anna.name)["programmes"]
		self.assertEqual(visto["open_stage"], 0)
		area_piani.finish_stage(self.anna.name, programma["name"], "uno")
		[visto] = area_piani.area_programmes(self.anna.name)["programmes"]
		self.assertEqual(visto["open_stage"], 1)
		# the second stage's plan is published for Anna to follow
		[piano] = area_piani.area_plans(self.anna.name)["plans"]
		self.assertEqual((piano["name"], piano["programme"]), (fatto["plan"], programma["name"]))
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_value(piani.PIANO, fatto["plan"], "starts_on"), getdate())


class LaLibreria(PianiCase):
	def test_gli_esercizi_sono_del_manager(self):
		self.come(MANAGER)
		trovati = librerie.get_exercises(text="Squat", source="Centre")["rows"]
		self.assertIn("Squat", [riga["exercise_name"] for riga in trovati])
		for user in (DESK, OPERATORE):
			self.come(user)
			with self.assertRaises(frappe.PermissionError):
				librerie.get_exercises()

	def test_chi_scrive_piani_aggiunge_un_esercizio(self):
		self.come(OPERATORE)
		fatto = piani.add_exercise("Plank", body_part="Core")
		self.assertEqual(fatto["exercise_name"], "Plank")
		self.assertIn("Plank", [e["exercise_name"] for e in piani.search_exercises("Pla")])
