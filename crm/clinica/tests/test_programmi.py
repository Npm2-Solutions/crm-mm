# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Programmes of stages: written like a plan, published to the area, their stages
opening with time or one after the other.

The dietitian writes Anna a programme of two stages, each with its menu. The
stages' menus are written from the programme and are not published by
themselves. Published, the first stage opens today and its menu with it; Anna says
from her area that she has finished it, and the second opens. By time, the days
open the stages: the daily job finishes the first when its days are over, and the
last one's end completes the programme. A colleague reads it like a visit, with
the dossier; the author closes it, and the open stage's plan with it.
"""

import json
from unittest import mock

import frappe
from frappe.utils import add_days, getdate

from crm.clinica import cartella, piani, programmi
from crm.clinica import piani_regole as R
from crm.clinica import programmi_regole as P
from crm.clinica.area import messaggi
from crm.clinica.tests.test_cartella import DIRECTOR, DOC1, DOC2, MANAGER
from crm.clinica.tests.test_piani import PianiCase


class ProgrammiCase(PianiCase):
	def setUp(self):
		super().setUp()
		patch = mock.patch.object(messaggi, "_avvisa")
		self.avvisi = patch.start()
		self.addCleanup(patch.stop)

	def bozza(self, modo=P.RITMO, starts_on=None, giorni=(None, None)):
		self.come(DOC1)
		return programmi.save_programme(
			self.anna.name,
			json.dumps(
				{
					"title": "Percorso di autunno",
					"mode": modo,
					"starts_on": starts_on,
					"instructions": "Tre mesi per cambiare abitudini.",
					"stages": [
						{
							"key": f"t{n}",
							"title": f"Tappa {n}",
							"description": f"Cosa fare nella tappa {n}",
							"days": g,
						}
						for n, g in enumerate(giorni, 1)
					],
				}
			),
		)

	def menu_della_tappa(self, programma, tappa):
		self.come(DOC1)
		piano = programmi.stage_plan(programma, tappa, R.MENU)["plan"]
		piani.save_plan(self.anna.name, json.dumps(self.menu(title=f"Menù {tappa}")), name=piano)
		return piano

	def pubblica(self, programma):
		self.come(DOC1)
		return programmi.publish_programme(programma)

	def tappe(self, programma):
		self.come(DOC1)
		return {t["key"]: t for t in programmi.get_programme(programma)["stages"]}


class LaScrittura(ProgrammiCase):
	def test_le_tappe_e_i_loro_piani_si_scrivono_dal_programma(self):
		fatto = self.bozza()
		self.assertEqual(fatto["status"], programmi.BOZZA)
		self.assertEqual([t["key"] for t in fatto["stages"]], ["t1", "t2"])
		piano = self.menu_della_tappa(fatto["name"], "t1")
		# the same stage asked again gives its plan back
		self.assertEqual(programmi.stage_plan(fatto["name"], "t1", R.MENU)["plan"], piano)
		tappa = self.tappe(fatto["name"])["t1"]
		self.assertEqual((tappa["plan"], tappa["plan_type"], tappa["plan_title"]), (piano, R.MENU, "Menù t1"))
		# read inside the programme, not among the person's plans; published with its stage
		self.assertNotIn(piano, [p["name"] for p in piani.get_plans(self.anna.name)["plans"]])
		self.assertEqual(piani.get_plan(piano)["programme_title"], "Percorso di autunno")
		with self.assertRaises(frappe.ValidationError):
			piani.publish_plan(piano)

	def test_per_tempo_ogni_tappa_dice_i_suoi_giorni(self):
		with self.assertRaises(frappe.ValidationError):
			self.bozza(modo=P.TEMPO, giorni=(None, 7))
		fatto = self.bozza(modo=P.TEMPO, giorni=(7, None))
		with self.assertRaises(frappe.ValidationError):
			# a programme by time starts on a day
			self.pubblica(fatto["name"])

	def test_il_fisioterapista_non_scrive_il_menu_di_una_tappa(self):
		fatto = self.bozza()
		self.come(DOC2)
		with self.assertRaises(frappe.PermissionError):
			programmi.stage_plan(fatto["name"], "t1", R.MENU)

	def test_la_bozza_si_butta_con_i_piani_delle_tappe(self):
		fatto = self.bozza()
		piano = self.menu_della_tappa(fatto["name"], "t1")
		programmi.delete_programme_draft(fatto["name"])
		self.assertFalse(frappe.db.exists(programmi.PROGRAMMA, fatto["name"]))
		self.assertFalse(frappe.db.exists(piani.PIANO, piano))


class AlProprioRitmo(ProgrammiCase):
	def test_la_prima_tappa_si_apre_oggi_la_seconda_quando_anna_ha_finito(self):
		fatto = self.bozza()
		primo = self.menu_della_tappa(fatto["name"], "t1")
		secondo = self.menu_della_tappa(fatto["name"], "t2")
		pubblicato = self.pubblica(fatto["name"])
		self.assertEqual(pubblicato["status"], programmi.PUBBLICATO)
		self.assertTrue(self.avvisi.called)
		tappe = self.tappe(fatto["name"])
		self.assertEqual((tappe["t1"]["state"], tappe["t2"]["state"]), (P.APERTA, P.CHIUSA))
		self.assertEqual(
			frappe.db.get_value(piani.PIANO, primo, ["status", "starts_on"]), (piani.PUBBLICATO, getdate())
		)
		self.assertEqual(frappe.db.get_value(piani.PIANO, secondo, "status"), piani.BOZZA)
		# in her area: the stage open, what it says, its plan; the next locked
		[nell_area] = programmi.area_dei_programmi(self.anna.name)
		self.assertTrue(nell_area["can_finish"])
		self.assertEqual(
			[(t["state"], t["plan"], t["description"]) for t in nell_area["stages"]],
			[(P.APERTA, primo, "Cosa fare nella tappa 1"), (P.CHIUSA, None, None)],
		)
		# Anna says she has finished it
		frappe.set_user("Administrator")
		with self.assertRaises(frappe.ValidationError):
			programmi.finisce_la_tappa(self.anna.name, fatto["name"], "t2")
		programmi.finisce_la_tappa(self.anna.name, fatto["name"], "t1")
		tappe = self.tappe(fatto["name"])
		self.assertEqual((tappe["t1"]["state"], tappe["t2"]["state"]), (P.FATTA, P.APERTA))
		self.assertEqual(frappe.db.get_value(piani.PIANO, primo, "status"), piani.CHIUSO)
		self.assertEqual(frappe.db.get_value(piani.PIANO, secondo, "status"), piani.PUBBLICATO)
		# the last one finished completes the programme
		programmi.finisce_la_tappa(self.anna.name, fatto["name"], "t2")
		self.come(DOC1)
		self.assertEqual(programmi.get_programme(fatto["name"])["status"], programmi.COMPLETATO)
		self.assertEqual(frappe.db.get_value(piani.PIANO, secondo, "status"), piani.CHIUSO)
		self.assertEqual(programmi.area_dei_programmi(self.anna.name), [])

	def test_l_autore_apre_la_tappa_dopo_o_chiude_il_programma(self):
		fatto = self.bozza()
		primo = self.menu_della_tappa(fatto["name"], "t1")
		self.pubblica(fatto["name"])
		# a stage without a plan is what it says
		aperto = programmi.open_next_stage(fatto["name"])
		self.assertEqual([t["state"] for t in aperto["stages"]], [P.FATTA, P.APERTA])
		self.assertEqual(frappe.db.get_value(piani.PIANO, primo, "status"), piani.CHIUSO)
		chiuso = programmi.close_programme(fatto["name"])
		self.assertEqual((chiuso["status"], chiuso["can_open_next"]), (programmi.CHIUSO, False))
		self.come(DOC2)
		with self.assertRaises(frappe.PermissionError):
			programmi.close_programme(fatto["name"])


class PerTempo(ProgrammiCase):
	def test_i_giorni_aprono_le_tappe_e_la_fine_completa_il_programma(self):
		oggi = getdate()
		fatto = self.bozza(modo=P.TEMPO, starts_on=str(oggi), giorni=(7, 7))
		primo = self.menu_della_tappa(fatto["name"], "t1")
		secondo = self.menu_della_tappa(fatto["name"], "t2")
		self.pubblica(fatto["name"])
		# the first stage's menu is for its seven days
		self.assertEqual(frappe.db.get_value(piani.PIANO, primo, "ends_on"), add_days(oggi, 6))
		self.assertFalse(programmi.area_dei_programmi(self.anna.name)[0]["can_finish"])
		frappe.set_user("Administrator")
		with self.assertRaises(frappe.ValidationError):
			programmi.finisce_la_tappa(self.anna.name, fatto["name"], "t1")
		# the stage ahead says its day
		self.assertEqual(self.tappe(fatto["name"])["t2"]["opens_on"], add_days(oggi, 7))
		doc = frappe.get_doc(programmi.PROGRAMMA, fatto["name"])
		programmi._giorno(doc, add_days(oggi, 3))
		self.assertEqual(self.tappe(fatto["name"])["t2"]["state"], P.CHIUSA)
		programmi._giorno(frappe.get_doc(programmi.PROGRAMMA, fatto["name"]), add_days(oggi, 7))
		tappe = self.tappe(fatto["name"])
		self.assertEqual((tappe["t1"]["state"], tappe["t2"]["state"]), (P.FATTA, P.APERTA))
		self.assertEqual(frappe.db.get_value(piani.PIANO, secondo, "status"), piani.PUBBLICATO)
		programmi._giorno(frappe.get_doc(programmi.PROGRAMMA, fatto["name"]), add_days(oggi, 14))
		self.assertEqual(
			frappe.db.get_value(programmi.PROGRAMMA, fatto["name"], "status"), programmi.COMPLETATO
		)

	def test_un_programma_che_parte_domani_si_apre_domani(self):
		domani = add_days(getdate(), 1)
		fatto = self.bozza(modo=P.TEMPO, starts_on=str(domani), giorni=(7, None))
		self.pubblica(fatto["name"])
		self.assertEqual(self.tappe(fatto["name"])["t1"]["state"], P.CHIUSA)
		with mock.patch.object(programmi, "getdate", return_value=domani):
			programmi.apri_del_giorno()
		self.assertEqual(self.tappe(fatto["name"])["t1"]["state"], P.APERTA)


class ChiLegge(ProgrammiCase):
	def test_come_un_piano(self):
		fatto = self.bozza()
		# a draft is its author's
		self.come(DIRECTOR)
		with self.assertRaises(frappe.PermissionError):
			programmi.get_programme(fatto["name"])
		self.pubblica(fatto["name"])
		self.come(DIRECTOR)
		self.assertEqual(programmi.get_programme(fatto["name"])["title"], "Percorso di autunno")
		self.come(DOC2)
		self.assertEqual(programmi.get_programmes(self.anna.name)["programmes"], [])
		self.consenso()
		self.come(DOC2)
		self.assertEqual(
			[p["name"] for p in programmi.get_programmes(self.anna.name)["programmes"]], [fatto["name"]]
		)
		self.assertFalse(programmi.get_programme(fatto["name"])["can_close"])
		self.come(MANAGER)
		registro = cartella.access_log(self.anna.name)
		self.assertIn(("programme", DOC2), [(riga["kind"], riga["viewed_by"]) for riga in registro])

	def test_pubblicato_non_si_riscrive(self):
		fatto = self.bozza()
		self.pubblica(fatto["name"])
		with self.assertRaises(frappe.ValidationError):
			programmi.save_programme(
				self.anna.name, json.dumps({"title": "Altro", "stages": []}), name=fatto["name"]
			)
		doc = frappe.get_doc(programmi.PROGRAMMA, fatto["name"])
		doc.title = "Riscritto"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
