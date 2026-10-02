# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""Twilio's errors in DottorCloud's words, without a site (doc 52, fifth part)."""

import unittest

from crm.telephony import errori_regole as R


class LeFrasi(unittest.TestCase):
	def test_un_codice_come_arriva(self):
		self.assertEqual(R.codice(30003), 30003)
		self.assertEqual(R.codice("21610"), 21610)
		self.assertIsNone(R.codice(None))
		self.assertIsNone(R.codice(""))
		self.assertIsNone(R.codice("abc"))

	def test_quelli_che_un_centro_incontra(self):
		self.assertIn("off or out of reach", R.frase("30003"))
		self.assertIn("STOP", R.frase(21610))
		self.assertIn("credit", R.frase(10001))
		self.assertIsNone(R.frase(99999))
		# every sentence is whole and ends with its stop
		for numero, testo in R.ERRORI.items():
			self.assertTrue(testo.endswith("."), numero)


class IlRegistro(unittest.TestCase):
	def test_una_riga_per_codice_la_piu_recente_prima(self):
		avvisi = [
			{"error_code": "30003", "alert_text": "Unreachable", "date_created": "2026-10-01T10:00:00"},
			{
				"error_code": "11200",
				"alert_text": "HTTP retrieval failure",
				"date_created": "2026-10-02T09:00:00",
			},
			{
				"error_code": "30003",
				"alert_text": "Unreachable handset",
				"date_created": "2026-10-02T11:00:00",
			},
			{"error_code": "45678", "alert_text": "Something new", "date_created": "2026-09-30T08:00:00"},
		]
		righe = R.raggruppa(avvisi)
		self.assertEqual([riga["code"] for riga in righe], [30003, 11200, 45678])
		self.assertEqual(
			(righe[0]["count"], righe[0]["last"], righe[0]["twilio"]),
			(2, "2026-10-02T11:00:00", "Unreachable handset"),
		)
		self.assertIn("off or out of reach", righe[0]["sentence"])
		# a code DottorCloud does not know keeps Twilio's words
		self.assertIsNone(righe[2]["sentence"])
		self.assertEqual(righe[2]["twilio"], "Something new")

	def test_al_massimo_quanti_ne_servono(self):
		avvisi = [{"error_code": str(30000 + i), "date_created": f"2026-10-0{i % 9 + 1}"} for i in range(20)]
		self.assertEqual(len(R.raggruppa(avvisi, quanti=5)), 5)
