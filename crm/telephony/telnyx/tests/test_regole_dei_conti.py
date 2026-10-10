# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""What the Telnyx account spends, its errors in words, its Italian numbers'
requirements, without a site (doc 64)."""

import unittest
from decimal import Decimal
from typing import ClassVar

from crm.telephony.telnyx import consumi_regole as C
from crm.telephony.telnyx import errori_regole as E
from crm.telephony.telnyx import numeri_regole as N


class LaSpesa(unittest.TestCase):
	def test_il_mese_per_voce(self):
		mese = C.consumi(
			{
				"call-control": [{"cost": "3.10", "billed_sec": 1800, "connected": 12}],
				"webrtc": [{"cost": "0.40"}],
				"messaging": [{"cost": "1.205", "count": 30}],
				"recording": [{"cost": "0.05"}],
			},
			{"count": 2, "price": Decimal("2.00")},
			"usd",
		)
		voci = {voce["key"]: voce for voce in mese["items"]}
		self.assertEqual([v["key"] for v in mese["items"]], ["calls", "sms", "numbers", "recordings"])
		self.assertEqual(
			(voci["calls"]["price"], voci["calls"]["count"], voci["calls"]["minutes"]), ("3.50", 12, 30)
		)
		self.assertEqual((voci["sms"]["price"], voci["sms"]["count"]), ("1.21", 30))
		self.assertEqual((voci["numbers"]["price"], voci["numbers"]["count"]), ("2.00", 2))
		self.assertEqual((mese["total"], mese["currency"]), ("6.76", "USD"))

	def test_i_numeri_dal_sommario(self):
		sommario = {
			"summary": {
				"lines": [
					{
						"type": "comparative",
						"new_this_month": {"quantity": 1, "mrc": "1.00", "otc": "1.00"},
						"existing_this_month": {"quantity": 2, "mrc": "2.00", "otc": "0"},
					},
					{"type": "simple", "amount": "0.50"},
				]
			}
		}
		self.assertEqual(C.dei_numeri(sommario), {"count": 3, "price": Decimal("4.50")})
		self.assertEqual(C.dei_numeri(None), {"count": 0, "price": Decimal(0)})

	def test_il_bilancio(self):
		self.assertIn("used up", C.bilancio_in_parole("0.00"))
		self.assertIn("used up", C.bilancio_in_parole("10", "-1"))
		self.assertEqual(C.bilancio_in_parole("12.00"), "")
		self.assertEqual(C.bilancio_in_parole(None), "")

	def test_l_avviso_della_spesa_una_volta_al_mese(self):
		self.assertTrue(C.da_avvisare_della_spesa("50.00", 40, "", "2026-10"))
		self.assertFalse(C.da_avvisare_della_spesa("50.00", 40, "2026-10", "2026-10"))
		self.assertTrue(C.da_avvisare_della_spesa("50.00", 40, "2026-09", "2026-10"))
		self.assertFalse(C.da_avvisare_della_spesa("30.00", 40, "", "2026-10"))
		self.assertFalse(C.da_avvisare_della_spesa("30.00", 0, "", "2026-10"))

	def test_l_avviso_del_bilancio_finche_non_si_ricarica(self):
		self.assertEqual(C.cosa_fare_del_bilancio("5.00", 10, False), "tell")
		self.assertEqual(C.cosa_fare_del_bilancio("5.00", 10, True), "")
		self.assertEqual(C.cosa_fare_del_bilancio("50.00", 10, True), "reset")
		self.assertEqual(C.cosa_fare_del_bilancio("50.00", 10, False), "")
		self.assertEqual(C.cosa_fare_del_bilancio("5.00", 0, False), "")


class GliErrori(unittest.TestCase):
	def test_quelli_che_un_centro_incontra(self):
		self.assertIn("STOP", E.frase("40300"))
		self.assertIn("landline", E.frase(40001))
		self.assertIn("balance", E.frase(20100))
		self.assertIsNone(E.frase(99999))
		for numero, testo in E.ERRORI.items():
			self.assertTrue(testo.endswith("."), numero)
		for codice, testo in E.CHIAMATE.items():
			self.assertTrue(testo.endswith("."), codice)

	def test_il_primo_errore(self):
		self.assertEqual(
			E.primo_errore([{"code": "40008", "title": "Undeliverable"}]), (40008, "Undeliverable")
		)
		self.assertEqual(E.primo_errore(["40001"]), (40001, ""))
		self.assertEqual(E.primo_errore([]), (None, ""))

	def test_raggruppati(self):
		righe = E.raggruppa(
			[
				{"code": "40001", "created_at": "2026-10-01T10:00:00Z"},
				{"code": "40008", "created_at": "2026-10-02T10:00:00Z"},
				{"code": "40001", "created_at": "2026-10-03T10:00:00Z"},
			]
		)
		self.assertEqual([(r["code"], r["count"]) for r in righe], [(40001, 2), (40008, 1)])
		self.assertEqual(righe[0]["last"], "2026-10-03T10:00:00Z")


class IRequisiti(unittest.TestCase):
	REQUISITI: ClassVar[list[dict]] = [
		{
			"id": "r-tipo",
			"name": "Customer Type",
			"type": "textual",
			"acceptance_criteria": {
				"acceptable_values": ["natural_person", "legal_entity", "sole_proprietorship"]
			},
		},
		{"id": "r-ragione", "name": "Company Name", "type": "textual"},
		{"id": "r-iva", "name": "VAT Number", "type": "textual"},
		{"id": "r-strano", "name": "Something Telnyx asks", "type": "textual", "description": "Its words"},
		{"id": "r-indirizzo", "name": "Address", "type": "address"},
		{"id": "r-visura", "name": "Local Company Registration Certificate", "type": "document"},
	]

	def test_i_campi_con_i_valori_del_centro(self):
		campi = {
			c["name"]: c
			for c in N.campi(self.REQUISITI, {"business_name": "Aurora srl", "vat_number": "IT1"}, N.AZIENDA)
		}
		self.assertEqual(campi["r-ragione"]["value"], "Aurora srl")
		self.assertEqual(campi["r-iva"]["value"], "IT1")
		self.assertEqual(campi["r-tipo"]["value"], "legal_entity")
		self.assertEqual(
			campi["r-tipo"]["options"], ["natural_person", "legal_entity", "sole_proprietorship"]
		)
		self.assertEqual(
			(campi["r-strano"]["label"], campi["r-strano"]["known"]), ("Something Telnyx asks", False)
		)
		# a professional in their own name
		persona = {c["name"]: c for c in N.campi(self.REQUISITI, {}, N.PERSONA)}
		self.assertEqual(persona["r-tipo"]["value"], "sole_proprietorship")

	def test_i_documenti_e_l_indirizzo(self):
		documenti = {d["requirement"]: d["accepted"][0] for d in N.documenti(self.REQUISITI)}
		self.assertEqual(set(documenti), {"r-indirizzo", "r-visura"})
		self.assertTrue(documenti["r-indirizzo"]["address"])
		self.assertEqual(documenti["r-indirizzo"]["fields"], ["address_sids"])
		self.assertIn("visura", documenti["r-visura"]["label"])

	def test_cosa_manca(self):
		self.assertEqual(
			N.mancanti(
				self.REQUISITI,
				{
					"r-tipo": "legal_entity",
					"r-ragione": "Aurora",
					"r-iva": "IT1",
					"r-strano": "x",
					"r-indirizzo": "9",
				},
			),
			["Local Company Registration Certificate"],
		)

	def test_solo_pdf(self):
		self.assertEqual(N.file_accettato("visura.pdf", 1000), "")
		self.assertIn("PDF", N.file_accettato("visura.jpg", 1000))
		self.assertIn("20 MB", N.file_accettato("visura.pdf", N.MASSIMO + 1))

	def test_gli_stati(self):
		self.assertEqual(N.stato_dell_ordine("success"), N.APPROVATA)
		self.assertEqual(N.stato_dell_ordine("failure"), N.RIFIUTATA)
		self.assertEqual(N.stato_dell_ordine("pending"), N.IN_VERIFICA)
		self.assertEqual(N.stato_del_gruppo("declined"), N.RIFIUTATA)
		self.assertEqual(N.stato_del_gruppo("approved"), N.APPROVATA)

	def test_prezzo_e_prefissi(self):
		self.assertEqual(N.prezzo_al_mese({"monthly_cost": "1.00"}), Decimal("1.00"))
		self.assertIsNone(N.prezzo_al_mese({}))
		self.assertEqual(N.prefissi("+39 02"), ["02", "2"])
		self.assertEqual(N.prefissi("abc"), [])
		# Telnyx sells no Italian mobile
		self.assertNotIn("mobile", N.TIPI)
