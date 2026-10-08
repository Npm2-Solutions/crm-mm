# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

import datetime
import unittest
from decimal import Decimal

from crm.convenzioni import regole as R

FONDO = {
	"convention_name": "Salute+",
	"kind": R.FONDO,
	"enabled": 1,
	"direct": 1,
	"indirect": 1,
	"organization": "Salute+ S.p.A.",
	"price_mode": R.LISTINO,
	"price_list": "Salute+",
	"share_mode": R.PERCENTUALE,
	"share_percent": 20,
	"shares": [{"service": "Osteopatia", "patient_share": 15}],
}


class IlPrezzo(unittest.TestCase):
	def test_il_listino_della_convenzione(self):
		self.assertEqual(R.prezzo(FONDO, 70, 42), Decimal("42.00"))

	def test_senza_riga_nel_listino_il_prezzo_del_centro(self):
		self.assertEqual(R.prezzo(FONDO, 70, None), Decimal("70.00"))

	def test_lo_sconto_arrotonda_a_meta_in_su(self):
		azienda = {"price_mode": R.SCONTO, "discount_percent": 15}
		# 33.30 less 15% is 28.305: 28.31
		self.assertEqual(R.prezzo(azienda, "33.30"), Decimal("28.31"))

	def test_i_prezzi_del_centro(self):
		self.assertEqual(R.prezzo({}, 55), Decimal("55.00"))


class LeQuote(unittest.TestCase):
	def test_in_forma_indiretta_paga_tutto_la_persona(self):
		self.assertEqual(R.quote(FONDO, R.INDIRETTA, 42), (Decimal("42.00"), Decimal("0.00")))

	def test_una_percentuale_e_il_resto_al_fondo(self):
		persona, fondo = R.quote(FONDO, R.DIRETTA, "42.25")
		# 20% of 42.25 is 8.45
		self.assertEqual((persona, fondo), (Decimal("8.45"), Decimal("33.80")))
		self.assertEqual(persona + fondo, Decimal("42.25"))

	def test_mezzo_centesimo_in_su(self):
		persona, fondo = R.quote({"share_mode": R.PERCENTUALE, "share_percent": 10}, R.DIRETTA, "0.25")
		self.assertEqual((persona, fondo), (Decimal("0.03"), Decimal("0.22")))

	def test_la_quota_del_servizio_vince(self):
		self.assertEqual(R.quote(FONDO, R.DIRETTA, 60, "Osteopatia"), (Decimal("15.00"), Decimal("45.00")))

	def test_una_franchigia_mai_oltre_il_totale(self):
		franchigia = {"share_mode": R.FISSA, "share_amount": 50}
		self.assertEqual(R.quote(franchigia, R.DIRETTA, 40), (Decimal("40.00"), Decimal("0.00")))
		self.assertEqual(R.quote(franchigia, R.DIRETTA, 80), (Decimal("50.00"), Decimal("30.00")))

	def test_nessuna_quota(self):
		self.assertEqual(R.quote({}, R.DIRETTA, 80), (Decimal("0.00"), Decimal("80.00")))


class LaConvenzione(unittest.TestCase):
	def test_una_buona(self):
		self.assertEqual(R.problemi(FONDO), [])

	def test_in_forma_diretta_serve_chi_paga(self):
		testi = [p.testo() for p in R.problemi({**FONDO, "organization": ""})]
		self.assertIn("In direct form the fund is billed: choose the company that pays", testi)

	def test_almeno_una_forma(self):
		testi = [p.testo() for p in R.problemi({**FONDO, "direct": 0, "indirect": 0})]
		self.assertIn("Choose the direct form, the indirect form or both", testi)

	def test_uno_sconto_fuori_misura(self):
		azienda = {"convention_name": "Tecno", "kind": R.AZIENDA, "indirect": 1, "price_mode": R.SCONTO}
		self.assertEqual(
			[p.testo() for p in R.problemi({**azienda, "discount_percent": 120})],
			["The discount is a percentage between 0 and 100"],
		)
		self.assertEqual(R.problemi({**azienda, "discount_percent": 10}), [])

	def test_le_date(self):
		self.assertTrue(R.valida_il({"valid_from": "2026-01-01"}, "2026-10-08"))
		self.assertFalse(R.valida_il({"valid_upto": "2026-09-30"}, "2026-10-08"))
		self.assertFalse(R.valida_il({"enabled": 0}, "2026-10-08"))
		self.assertEqual(
			[p.testo() for p in R.problemi({**FONDO, "valid_from": "2026-02", "valid_upto": "2026-01"})],
			["It ends before it starts"],
		)

	def test_le_forme(self):
		self.assertEqual(R.forme(FONDO), [R.DIRETTA, R.INDIRETTA])
		self.assertEqual(R.forme({"indirect": 1}), [R.INDIRETTA])


class LaPratica(unittest.TestCase):
	def test_da_autorizzare(self):
		self.assertEqual(R.stato("Scheduled", "Booked", True, ""), R.DA_AUTORIZZARE)
		self.assertTrue(R.manca_l_autorizzazione(R.DIRETTA, True, "  "))
		self.assertFalse(R.manca_l_autorizzazione(R.INDIRETTA, True, ""))

	def test_autorizzata_poi_eseguita(self):
		self.assertEqual(R.stato("Scheduled", "Booked", True, "A-1"), R.AUTORIZZATA)
		self.assertEqual(R.stato("Scheduled", "Booked", False, ""), R.AUTORIZZATA)
		self.assertEqual(R.stato("Completed", "Attended", True, "A-1"), R.ESEGUITA)

	def test_annullata_o_persa(self):
		self.assertEqual(R.stato("Cancelled", "Booked", True, "A-1"), R.ANNULLATA)
		self.assertEqual(R.stato("No Show", "No Show", True, "A-1"), R.PERSA)

	def test_la_fattura_al_fondo(self):
		self.assertEqual(R.stato("Completed", "Attended", True, "A-1", 0), R.IN_BOZZA)
		self.assertEqual(R.stato("Completed", "Attended", True, "A-1", 1), R.FATTURATA)
		self.assertEqual(R.stato("Completed", "Attended", True, "A-1", 1, True), R.PAGATA)

	def test_cosa_si_fattura(self):
		self.assertTrue(R.da_fatturare({"state": R.ESEGUITA, "fund_share": 30}))
		self.assertFalse(R.da_fatturare({"state": R.ESEGUITA, "fund_share": 0}))
		self.assertFalse(R.da_fatturare({"state": R.DA_AUTORIZZARE, "fund_share": 30}))


class IlMese(unittest.TestCase):
	def test_i_giorni(self):
		self.assertEqual(R.mese("2026-12"), (datetime.date(2026, 12, 1), datetime.date(2026, 12, 31)))
		self.assertEqual(R.mese("2028-02-10"), (datetime.date(2028, 2, 1), datetime.date(2028, 2, 29)))

	def test_i_totali(self):
		pratiche = [
			{"state": R.ESEGUITA, "patient_share": "8.45", "fund_share": "33.80"},
			{"state": R.FATTURATA, "patient_share": 10, "fund_share": 40},
			{"state": R.ANNULLATA, "patient_share": 10, "fund_share": 40},
		]
		t = R.totali(pratiche)
		self.assertEqual(t["fund_share"], 73.8)
		self.assertEqual(t["patient_share"], 18.45)
		self.assertEqual((t["to_bill"], t["to_bill_count"]), (33.8, 1))
		self.assertEqual(t["by_state"][R.ANNULLATA], 1)

	def test_la_riga_al_fondo(self):
		self.assertEqual(
			R.descrizione("Osteopatia", "Anna Neri", "2026-10-02 09:00:00", "UNI-77", "C123"),
			"Osteopatia · Anna Neri · 02/10/2026 · Aut. UNI-77 · Tessera C123",
		)
		self.assertEqual(
			R.descrizione("Visita", "Anna Neri", "2026-10-02", "", None), "Visita · Anna Neri · 02/10/2026"
		)

	def test_il_csv(self):
		testo = R.csv_del_mese(
			[
				{
					"date": "2026-10-02",
					"patient": "Anna Neri",
					"authorisation": "UNI-77",
					"service": "Osteopatia",
					"total": 60,
					"patient_share": 15,
					"fund_share": "45",
					"state": R.ESEGUITA,
				}
			]
		)
		righe = testo.splitlines()
		self.assertTrue(righe[0].startswith("Data;Assistito;Tessera"))
		self.assertEqual(righe[1], "02/10/2026;Anna Neri;;UNI-77;Osteopatia;60,00;15,00;45,00;Eseguita;")

	def test_l_eta(self):
		self.assertEqual([R.fascia(g) for g in (0, 30, 31, 75, 200)], ["30", "30", "60", "90", "older"])


if __name__ == "__main__":
	unittest.main()
