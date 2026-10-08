# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Asking how a visit went: the rules, without a site."""

from __future__ import annotations

from datetime import datetime

try:
	from frappe.tests import UnitTestCase
except ImportError:  # no bench: the rules are still testable
	from unittest import TestCase as UnitTestCase

from crm.recensioni import regole as r


class ChiSiPuoChiedere(UnitTestCase):
	def test_un_si_a_queste_richieste_basta(self):
		self.assertTrue(r.puo_chiedere("Given", None))

	def test_il_marketing_le_comprende(self):
		self.assertTrue(r.puo_chiedere(None, "Given"))

	def test_il_no_piu_stretto_vince_sul_si_al_marketing(self):
		self.assertFalse(r.puo_chiedere("Refused", "Given"))
		self.assertFalse(r.puo_chiedere("Withdrawn", "Given"))

	def test_chi_non_ha_mai_risposto_non_riceve_niente(self):
		self.assertFalse(r.puo_chiedere(None, None))
		self.assertFalse(r.puo_chiedere(None, "Withdrawn"))


class OgniQuanto(UnitTestCase):
	adesso = datetime(2026, 10, 8, 12, 0)

	def test_mai_chiesto(self):
		self.assertFalse(r.troppo_presto(None, self.adesso, 12))

	def test_meno_di_dodici_mesi_fa(self):
		self.assertTrue(r.troppo_presto(datetime(2026, 1, 5), self.adesso, 12))

	def test_piu_di_dodici_mesi_fa(self):
		self.assertFalse(r.troppo_presto(datetime(2025, 10, 7), self.adesso, 12))

	def test_i_mesi_vuoti_o_sbagliati_sono_dodici(self):
		self.assertEqual(r.mesi_tra(None), 12)
		self.assertEqual(r.mesi_tra(0), 12)
		self.assertEqual(r.mesi_tra("x"), 12)
		self.assertEqual(r.mesi_tra(6), 6)
		self.assertEqual(r.mesi_tra(500), r.MESI_MASSIMI)

	def test_mesi_scritti_da_1_a_60(self):
		for buoni in (None, "", 1, "12", 60):
			self.assertTrue(r.mesi_validi(buoni), buoni)
		for sbagliati in (0, -3, 61, 1.5, "x"):
			self.assertFalse(r.mesi_validi(sbagliati), sbagliati)


class IlServizioEIlLink(UnitTestCase):
	def test_servizi_esclusi_uno_per_riga(self):
		self.assertEqual(r.servizi("Prelievo\n\n Certificato \nPrelievo"), ["Prelievo", "Certificato"])
		self.assertTrue(r.escluso("Certificato", "Prelievo\nCertificato"))
		self.assertFalse(r.escluso("Visita", "Prelievo"))
		self.assertFalse(r.escluso(None, "Prelievo"))

	def test_il_link_del_centro_prima_del_place_id(self):
		self.assertEqual(
			r.link_di_google(" https://g.page/r/abc/review ", "ChIJ123"), "https://g.page/r/abc/review"
		)
		self.assertEqual(
			r.link_di_google("", "ChIJN1t_tDeuEmsRUsoyG83frY4"),
			"https://search.google.com/local/writereview?placeid=ChIJN1t_tDeuEmsRUsoyG83frY4",
		)
		self.assertIsNone(r.link_di_google(None, None))

	def test_un_link_e_https(self):
		self.assertTrue(r.link_valido("https://g.page/r/abc/review"))
		self.assertFalse(r.link_valido("http://g.page/r/abc"))
		self.assertFalse(r.link_valido("javascript:alert(1)"))
		self.assertFalse(r.link_valido("https://g.page/r/a b"))

	def test_un_place_id(self):
		self.assertTrue(r.place_id_valido("ChIJN1t_tDeuEmsRUsoyG83frY4"))
		self.assertFalse(r.place_id_valido("<script>"))

	def test_un_messaggio_chiede_una_recensione_se_ha_il_segnaposto(self):
		self.assertTrue(r.chiede_una_recensione(None, "Ciao, {{review_link}}"))
		self.assertTrue(r.chiede_una_recensione("", ["{{ first_name }}", "{{ review_link }}"]))
		self.assertFalse(r.chiede_una_recensione("Ciao {{ first_name }}", "{{ booking_link }}"))


class IlNetPromoterScore(UnitTestCase):
	def test_promotori_meno_detrattori(self):
		# 3 promoters, 1 passive, 1 detractor out of 5: 60% - 20%
		self.assertEqual(
			r.nps([10, 9, 9, 7, 3]),
			{"answers": 5, "promoters": 3, "passives": 1, "detractors": 1, "score": 40},
		)

	def test_tutti_detrattori(self):
		self.assertEqual(r.nps([0, 6, "5"])["score"], -100)

	def test_senza_risposte_nessun_punteggio(self):
		self.assertIsNone(r.nps([])["score"])
		self.assertEqual(r.nps([None, "", 11, -1, 7.5, True])["answers"], 0)

	def test_arrotondato_per_eccesso_a_meta(self):
		# 5 promoters and 3 detractors of 8 make 25; 1 promoter of 8 makes 12.5, which is 13
		self.assertEqual(r.nps([10, 10, 10, 10, 10, 0, 0, 0])["score"], 25)
		self.assertEqual(r.nps([10, 8, 8, 8, 8, 8, 8, 8])["score"], 13)

	def test_la_domanda_e_la_prima_scala_da_0_a_10(self):
		schema = {
			"sections": [
				{
					"fields": [
						{"id": "dolore", "type": "scale", "min": 1, "max": 5},
						{"id": "consiglio", "type": "scale", "min": 0, "max": 10},
						{"id": "altro", "type": "scale", "min": "0", "max": "10"},
					]
				}
			]
		}
		self.assertEqual(r.domanda_nps(schema), "consiglio")
		self.assertIsNone(r.domanda_nps({"sections": []}))
		self.assertIsNone(r.domanda_nps(None))
