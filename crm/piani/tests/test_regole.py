# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What a plan is, without a site: the kinds registered, what goes in a plan, the
person's day and week."""

from __future__ import annotations

import datetime

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the rules are still testable
	from unittest import TestCase as UnitTestCase

from crm.piani import regole as r

LUNEDI = datetime.date(2026, 9, 28)


def momento(key="colazione", label="Colazione", day=r.OGNI_GIORNO):
	return {"key": key, "label": label, "day": day}


class ITipi(UnitTestCase):
	def test_il_crm_scrive_allenamenti_e_abitudini_per_chiunque(self):
		propri = [t for t in r.tipi() if not t.modulo]
		self.assertEqual([t.chiave for t in propri], [r.ALLENAMENTO, r.ABITUDINI])
		for qualifica in (None, "chinesiologo", "consulente"):
			self.assertEqual(r.tipi_per(qualifica, propri), [r.ALLENAMENTO, r.ABITUDINI])
		self.assertFalse(any(t.clinico for t in propri))

	def test_un_tipo_registrato_con_le_sue_qualifiche(self):
		tipo = r.TipoPiano("Test kind", (r.ABITUDINE,), chi_scrive=frozenset({"coach"}), ordine=99)
		r.registra_tipo(tipo)
		try:
			self.assertIn("Test kind", r.tipi_per("coach"))
			self.assertNotIn("Test kind", r.tipi_per("chinesiologo"))
			self.assertEqual(r.tipi()[-1], tipo)
		finally:
			r._tipi.pop("Test kind", None)

	def test_ogni_tipo_si_mostra_con_un_colore_del_sistema(self):
		# the area draws a kind in its category's cloud: never a colour of its own
		self.assertEqual((r.tipo(r.ALLENAMENTO).colore, r.tipo(r.ALLENAMENTO).icona), ("violet", "dumbbell"))
		for tipo in r.tipi():
			self.assertIn(tipo.colore, ("", "amber", "violet", "green", "blue", "rose"), tipo.chiave)

	def test_ogni_genere_porta_i_suoi_campi(self):
		campi = r.campi_voce()
		for campo in ("kind", "times_per_week", "note", "exercise", "sets", "reps", "text"):
			self.assertIn(campo, campi)


class LeRighe(UnitTestCase):
	def test_un_allenamento_in_regola(self):
		voci = [
			{"moment": "colazione", "kind": r.ESERCIZIO, "exercise": "squat", "sets": 3},
			{"moment": "colazione", "kind": r.ABITUDINE, "text": "Un bicchiere d'acqua"},
		]
		self.assertEqual(r.valida(r.ALLENAMENTO, [momento()], voci), [])

	def test_ogni_genere_con_quello_che_gli_serve(self):
		voci = [
			{"moment": "colazione", "kind": r.ESERCIZIO},
			{"moment": "colazione", "kind": r.ABITUDINE, "text": "  "},
		]
		messaggi = [problema.messaggio for problema in r.valida(r.ALLENAMENTO, [momento()], voci)]
		self.assertEqual(messaggi, ["Choose the exercise", "Write the habit"])

	def test_un_piano_tiene_solo_i_suoi_generi(self):
		[problema] = r.valida(
			r.ABITUDINI, [momento()], [{"moment": "colazione", "kind": r.ESERCIZIO, "exercise": "x"}]
		)
		self.assertEqual(problema.testo(), "A plan of this kind does not hold Exercise")
		[problema] = r.valida(r.ABITUDINI, [momento()], [{"moment": "colazione", "kind": "Horoscope"}])
		self.assertEqual(problema.testo(), "A plan of this kind does not hold Horoscope")

	def test_momenti_con_la_loro_chiave_il_nome_e_il_giorno(self):
		momenti = [momento(), momento(label=""), momento(key="cena", day="Someday")]
		messaggi = [problema.testo() for problema in r.valida(r.ABITUDINI, momenti, [])]
		self.assertEqual(
			messaggi,
			["Every moment has its own key (colazione)", "Every moment has a name", "Someday is not a day"],
		)

	def test_una_voce_sta_in_un_momento_e_una_settimana_ha_sette_giorni(self):
		voci = [{"moment": "pranzo", "kind": r.ABITUDINE, "text": "Pesce", "times_per_week": 9}]
		messaggi = [problema.messaggio for problema in r.valida(r.ABITUDINI, [momento()], voci)]
		self.assertEqual(
			messaggi, ["An item belongs to a moment of the plan", "A week has at most seven days"]
		)

	def test_un_tipo_che_non_c_e(self):
		self.assertEqual(r.valida("Horoscope", [], [])[0].testo(), "Horoscope is not a kind of plan")


class IlGiornoELaSettimana(UnitTestCase):
	def test_i_momenti_di_ogni_giorno_e_del_giorno(self):
		momenti = [
			momento(),
			momento("sab", "Pizza del sabato", "Saturday"),
			momento("lun", "Palestra", "Monday"),
		]
		self.assertEqual([m["key"] for m in r.momenti_del_giorno(momenti, LUNEDI)], ["colazione", "lun"])
		sabato = LUNEDI + datetime.timedelta(days=5)
		self.assertEqual([m["key"] for m in r.momenti_del_giorno(momenti, sabato)], ["colazione", "sab"])

	def test_la_settimana_da_lunedi_a_domenica(self):
		mercoledi = LUNEDI + datetime.timedelta(days=2)
		self.assertEqual(r.settimana(mercoledi), (LUNEDI, LUNEDI + datetime.timedelta(days=6)))

	def test_quante_volte_restano(self):
		self.assertEqual(r.restano(3, [r.FATTO, r.IN_PARTE, r.SALTATO]), 1)
		self.assertEqual(r.restano(2, [r.FATTO, r.FATTO, r.FATTO]), 0)
		self.assertIsNone(r.restano(None, [r.FATTO]))

	def test_un_giorno_perso_si_recupera_il_domani_no(self):
		self.assertTrue(r.si_segna(LUNEDI, LUNEDI))
		self.assertTrue(r.si_segna(LUNEDI - datetime.timedelta(days=2), LUNEDI))
		self.assertFalse(r.si_segna(LUNEDI - datetime.timedelta(days=3), LUNEDI))
		self.assertFalse(r.si_segna(LUNEDI + datetime.timedelta(days=1), LUNEDI))

	def test_in_corso_nel_suo_periodo(self):
		self.assertTrue(r.in_corso(None, None, LUNEDI))
		self.assertTrue(r.in_corso(LUNEDI, LUNEDI, LUNEDI))
		self.assertFalse(r.in_corso(LUNEDI + datetime.timedelta(days=1), None, LUNEDI))
		self.assertFalse(r.in_corso(None, LUNEDI - datetime.timedelta(days=1), LUNEDI))

	def test_il_riepilogo_conta_non_giudica(self):
		self.assertEqual(
			r.riepilogo([r.FATTO, r.FATTO, r.SALTATO]), {r.FATTO: 2, r.IN_PARTE: 0, r.SALTATO: 1}
		)
