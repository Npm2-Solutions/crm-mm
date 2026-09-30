# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""What a plan is, without a site: who writes which kind, what goes in it, the
patient's day and week."""

from __future__ import annotations

import datetime

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the rules are still testable
	from unittest import TestCase as UnitTestCase

from crm.clinica import piani_regole as p

LUNEDI = datetime.date(2026, 9, 28)


def momento(key="colazione", label="Colazione", day=p.OGNI_GIORNO):
	return {"key": key, "label": label, "day": day}


class ChiScrive(UnitTestCase):
	def test_la_dieta_al_medico_al_biologo_e_al_dietista(self):
		for qualifica in ("medico_chirurgo", "biologo", "dietista"):
			self.assertIn(p.MENU, p.tipi_per(qualifica))
			self.assertIn(p.SCAMBI, p.tipi_per(qualifica))

	def test_il_trainer_allena_e_non_da_diete(self):
		# a personal trainer has no healthcare qualification, or one of its own
		for qualifica in (None, "chinesiologo", "consulente"):
			self.assertEqual(p.tipi_per(qualifica), [p.ALLENAMENTO, p.ABITUDINI])

	def test_la_riabilitazione_al_fisioterapista_e_al_medico(self):
		self.assertIn(p.ESERCIZI, p.tipi_per("fisioterapista"))
		self.assertNotIn(p.MENU, p.tipi_per("fisioterapista"))
		self.assertEqual(p.tipi_per("medico_chirurgo"), list(p.TIPI))
		self.assertNotIn(p.ESERCIZI, p.tipi_per("osteopata"))


class LeRighe(UnitTestCase):
	def test_un_menu_in_regola(self):
		voci = [
			{"moment": "colazione", "kind": p.CIBO, "food": "yogurt"},
			{"moment": "colazione", "kind": p.ABITUDINE, "text": "Un bicchiere d'acqua"},
		]
		self.assertEqual(p.valida(p.MENU, [momento()], voci), [])

	def test_ogni_genere_con_quello_che_gli_serve(self):
		voci = [
			{"moment": "colazione", "kind": p.CIBO},
			{"moment": "colazione", "kind": p.GRUPPO, "food_group": "Cereals", "portions": 0},
			{"moment": "colazione", "kind": p.ABITUDINE, "text": "  "},
		]
		messaggi = [problema.messaggio for problema in p.valida(p.SCAMBI, [momento()], voci)]
		self.assertEqual(
			messaggi, ["Choose the food", "A food group comes with its portions", "Write the habit"]
		)

	def test_un_piano_tiene_solo_i_suoi_generi(self):
		[problema] = p.valida(
			p.ALLENAMENTO, [momento()], [{"moment": "colazione", "kind": p.CIBO, "food": "x"}]
		)
		self.assertEqual(problema.testo(), "A plan of this kind does not hold Food")

	def test_momenti_con_la_loro_chiave_il_nome_e_il_giorno(self):
		momenti = [momento(), momento(label=""), momento(key="cena", day="Someday")]
		messaggi = [problema.testo() for problema in p.valida(p.ABITUDINI, momenti, [])]
		self.assertEqual(
			messaggi,
			["Every moment has its own key (colazione)", "Every moment has a name", "Someday is not a day"],
		)

	def test_una_voce_sta_in_un_momento_e_una_settimana_ha_sette_giorni(self):
		voci = [{"moment": "pranzo", "kind": p.ABITUDINE, "text": "Pesce", "times_per_week": 9}]
		messaggi = [problema.messaggio for problema in p.valida(p.ABITUDINI, [momento()], voci)]
		self.assertEqual(
			messaggi, ["An item belongs to a moment of the plan", "A week has at most seven days"]
		)

	def test_un_tipo_che_non_c_e(self):
		self.assertEqual(p.valida("Horoscope", [], [])[0].testo(), "Horoscope is not a kind of plan")


class IlGiornoELaSettimana(UnitTestCase):
	def test_i_momenti_di_ogni_giorno_e_del_giorno(self):
		momenti = [
			momento(),
			momento("sab", "Pizza del sabato", "Saturday"),
			momento("lun", "Palestra", "Monday"),
		]
		self.assertEqual([m["key"] for m in p.momenti_del_giorno(momenti, LUNEDI)], ["colazione", "lun"])
		sabato = LUNEDI + datetime.timedelta(days=5)
		self.assertEqual([m["key"] for m in p.momenti_del_giorno(momenti, sabato)], ["colazione", "sab"])

	def test_la_settimana_da_lunedi_a_domenica(self):
		mercoledi = LUNEDI + datetime.timedelta(days=2)
		self.assertEqual(p.settimana(mercoledi), (LUNEDI, LUNEDI + datetime.timedelta(days=6)))

	def test_quante_volte_restano(self):
		self.assertEqual(p.restano(3, [p.FATTO, p.IN_PARTE, p.SALTATO]), 1)
		self.assertEqual(p.restano(2, [p.FATTO, p.FATTO, p.FATTO]), 0)
		self.assertIsNone(p.restano(None, [p.FATTO]))

	def test_un_giorno_perso_si_recupera_il_domani_no(self):
		self.assertTrue(p.si_segna(LUNEDI, LUNEDI))
		self.assertTrue(p.si_segna(LUNEDI - datetime.timedelta(days=2), LUNEDI))
		self.assertFalse(p.si_segna(LUNEDI - datetime.timedelta(days=3), LUNEDI))
		self.assertFalse(p.si_segna(LUNEDI + datetime.timedelta(days=1), LUNEDI))

	def test_in_corso_nel_suo_periodo(self):
		self.assertTrue(p.in_corso(None, None, LUNEDI))
		self.assertTrue(p.in_corso(LUNEDI, LUNEDI, LUNEDI))
		self.assertFalse(p.in_corso(LUNEDI + datetime.timedelta(days=1), None, LUNEDI))
		self.assertFalse(p.in_corso(None, LUNEDI - datetime.timedelta(days=1), LUNEDI))

	def test_il_riepilogo_conta_non_giudica(self):
		self.assertEqual(
			p.riepilogo([p.FATTO, p.FATTO, p.SALTATO]), {p.FATTO: 2, p.IN_PARTE: 0, p.SALTATO: 1}
		)

	def test_le_calorie_dalla_tabella(self):
		self.assertEqual(p.calorie(360, 80), 288)
		self.assertIsNone(p.calorie(None, 80))
